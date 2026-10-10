"""Modelos HFSU (molino con selección específica de energía) y CYCA (clasificador por nitidez)."""

import numpy as np
import pytest

from conminucion.classifier import SharpnessCurve, whiten_alpha_from_sharpness
from conminucion.fracture import Fracture
from conminucion.mill import BallMill, EnergyBallMill, EnergySelection, KnotSelection
from conminucion.stream import Stream


def test_seleccion_especifica_vale_s1e_a_1_mm(grid):
    sel = EnergySelection(s1e=0.62, zeta1=0.551, zeta2=-0.331)
    se = sel.specific(grid)
    d = grid.sizes / 1000.0
    expected = 0.62 * np.exp(0.551 * np.log(d) - 0.331 * np.log(d) ** 2)
    np.testing.assert_allclose(se[:-1], expected[:-1], rtol=1e-12)
    assert se[-1] == 0.0
    flat = EnergySelection(s1e=0.5).specific(grid)
    np.testing.assert_allclose(flat[:-1], 0.5)
    top = EnergySelection(s1e=0.5, zeta1=1.0, size_basis="tamiz_superior").specific(grid)
    np.testing.assert_allclose(top[:-1], 0.5 * grid.sieves[:-1] / 1000.0)


def test_molino_de_energia_equivale_a_rd_igual_a_se_por_energia(fresh):
    sel = EnergySelection(s1e=0.4, zeta1=0.6)
    mill = EnergyBallMill(sel, Fracture(), power_kw=1500.0)
    grid = fresh.grid
    rd = sel.specific(grid) * 1500.0 / fresh.total_solids
    knots = KnotSelection(tuple(grid.sizes[:-1]), tuple(rd[:-1]))
    expected = BallMill(knots, Fracture()).discharge_solids(grid, fresh.solids)
    np.testing.assert_allclose(mill.discharge_solids(grid, fresh.solids), expected, rtol=1e-9)
    out = mill(fresh)
    assert out.total_solids == pytest.approx(fresh.total_solids, rel=1e-12)


def test_molino_de_energia_mas_potencia_mas_fino_y_agua(fresh):
    sel = EnergySelection(s1e=0.4, zeta1=0.6)
    low = EnergyBallMill(sel, power_kw=500.0)(fresh)
    high = EnergyBallMill(sel, power_kw=2000.0, discharge_pct_solids=75.0)(fresh)
    assert high.p80 < low.p80
    assert high.pct_solids == pytest.approx(75.0)
    two = EnergyBallMill(sel, power_kw=2000.0, region_fractions=(0.5, 0.5))(fresh)
    assert two.total_solids == pytest.approx(fresh.total_solids)
    empty = Stream.empty(fresh.grid)
    assert EnergyBallMill(sel)(empty).total_solids == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"power_kw": 0.0},
        {"region_fractions": (0.5, 0.4)},
        {"region_fractions": ()},
        {"region_fractions": (1.2, -0.2)},
        {"discharge_pct_solids": 100.0},
    ],
)
def test_molino_de_energia_valida_parametros(kwargs):
    with pytest.raises(ValueError):
        EnergyBallMill(EnergySelection(0.5), **kwargs)
    with pytest.raises(ValueError):
        EnergySelection(0.0)


@pytest.mark.parametrize("model", ["logistico", "rosin_rammler", "suma_exponencial"])
@pytest.mark.parametrize("si", [0.3, 0.6, 0.8])
def test_curva_de_nitidez_cumple_d50_y_d25_d75(model, si):
    curve = SharpnessCurve(d50c=100.0, sharpness=si, model=model, rho_ref=2.67)
    assert curve.corrected([100.0], rho_s=2.67)[0] == pytest.approx(0.5, abs=1e-12)
    from scipy.optimize import brentq

    def size_at(p: float) -> float:
        return brentq(lambda d: curve.corrected([d], 2.67)[0] - p, 1e-3, 1e5, xtol=1e-12)

    assert size_at(0.25) / size_at(0.75) == pytest.approx(si, rel=1e-8)


def test_curva_de_nitidez_bypass_densidad_y_division(fresh):
    curve = SharpnessCurve(d50c=100.0, sharpness=0.5, bypass=0.2, density_exponent=0.5)
    assert curve.d50_for(2.67) == pytest.approx(100.0)
    assert curve.d50_for(5.0) == pytest.approx(100.0 * (1.67 / 4.0) ** 0.5)
    ea = curve.efficiency([1e-3, 1e6], rho_s=2.67)
    np.testing.assert_allclose(ea, [0.2, 1.0], atol=1e-9)
    coarse, fine = curve.split(fresh.with_water(50.0))
    np.testing.assert_allclose(coarse.solids + fine.solids, fresh.solids, rtol=1e-12)
    assert coarse.water == pytest.approx(10.0) and fine.water == pytest.approx(40.0)
    top = SharpnessCurve(d50c=100.0, sharpness=0.5, size_basis="tamiz_superior")
    assert (
        top.split(fresh)[0].total_solids > SharpnessCurve(100.0, 0.5).split(fresh)[0].total_solids
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"d50c": 0.0, "sharpness": 0.5},
        {"d50c": 1.0, "sharpness": 1.0},
        {"d50c": 1.0, "sharpness": 0.5, "bypass": 1.0},
        {"d50c": 1.0, "sharpness": 0.5, "model": "otro"},
        {"d50c": 1.0, "sharpness": 0.5, "rho_ref": 1.0},
    ],
)
def test_curva_de_nitidez_valida_parametros(kwargs):
    with pytest.raises(ValueError):
        SharpnessCurve(**kwargs)


def test_alpha_de_whiten_desde_nitidez_y_base_de_tamano_invalida(grid):
    for si in (0.2, 0.5, 0.9):
        alpha = whiten_alpha_from_sharpness(si)
        assert alpha > 0
    assert whiten_alpha_from_sharpness(0.8) > whiten_alpha_from_sharpness(0.5)
    with pytest.raises(ValueError):
        grid.representative("otro")


def test_fractura_con_madre_en_el_limite_inferior(grid):
    fr = Fracture(phi=0.79, gamma=0.696, beta=2.17, parent_size="tamiz_inferior")
    a = fr.appearance(grid)
    n = grid.n
    np.testing.assert_allclose(a[:, : n - 1].sum(axis=0), 1.0, atol=1e-14)
    assert np.all(np.triu(a) == 0) and np.all(a >= 0) and a[:, n - 1].sum() == 0
    s = grid.sieves
    # primera clase hija: todo lo que queda entre el límite inferior de la madre y el siguiente
    assert a[1, 0] == pytest.approx(1.0 - fr.cumulative(s[2] / s[1]))
    assert a[n - 1, 0] == pytest.approx(fr.cumulative(s[n - 1] / s[1]))
    with pytest.raises(ValueError):
        Fracture(parent_size="medio")


def test_tamano_representativo_en_el_limite_inferior(grid):
    low = grid.representative("tamiz_inferior")
    np.testing.assert_allclose(low[:-1], grid.sieves[1:])
    assert low[-1] == pytest.approx(grid.sieves[-1] / np.sqrt(2.0))
