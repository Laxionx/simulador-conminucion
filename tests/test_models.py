import numpy as np
import pytest

from conminucion.classifier import EfficiencyCurve, corrected_efficiency
from conminucion.fracture import Fracture
from conminucion.mill import AustinSelection, BallMill, KnotSelection
from conminucion.stream import Stream
from conminucion.units import ClassifierOp, MillOp, SumpOp


def test_appearance_columns_sum_one(grid):
    a = Fracture().appearance(grid)
    n = grid.n
    np.testing.assert_allclose(a[:, : n - 1].sum(axis=0), 1.0, atol=1e-14)
    assert a[:, n - 1].sum() == 0
    assert np.all(np.triu(a) == 0) and np.all(a >= 0)  # solo a clases más finas


@pytest.mark.parametrize("phi,gamma,beta", [(0.0, 1.0, 2.0), (1.0, 0.5, 4.0), (0.3, 1.2, 5.0)])
def test_appearance_sum_other_params(grid, phi, gamma, beta):
    a = Fracture(phi, gamma, beta).appearance(grid)
    np.testing.assert_allclose(a[:, : grid.n - 1].sum(axis=0), 1.0, atol=1e-13)


def test_fracture_invalid():
    for kw in ({"phi": 1.5}, {"gamma": 0}, {"beta": -1}):
        with pytest.raises(ValueError):
            Fracture(**kw)


def test_mill_limit_rd_zero(fresh):
    mill = BallMill(KnotSelection((1000.0,), (1e-300,)))
    out = mill(fresh)
    np.testing.assert_allclose(out.solids, fresh.solids, atol=1e-12)  # r/d = 0: sin molienda


def test_mill_mass_conservation(fresh):
    for sel in (AustinSelection(), KnotSelection((4000, 500, 100), (1.0, 2.0, 0.5))):
        for nmix in (1, 3):
            m = BallMill(sel, n_mixers=nmix, added_water=2.0)
            o = m(fresh)
            assert abs(o.total_solids - fresh.total_solids) < 1e-10
            assert o.water == pytest.approx(fresh.water + 2.0)
            assert o.p80 < fresh.p80


def test_mill_more_mixers_less_short_circuit(fresh):
    one = BallMill(AustinSelection(), n_mixers=1)(fresh).p80
    many = BallMill(AustinSelection(), n_mixers=6)(fresh).p80
    assert many < one  # menos cortocircuito: más molienda


def test_knot_selection_interpolation_and_extrapolation(grid):
    sel = KnotSelection((1000.0, 100.0), (4.0, 1.0))  # desordenados a propósito
    rd = sel.rd_vector(grid)
    x = grid.sizes
    assert rd[-1] == 0.0
    big = x > 1000
    small = (x < 100) & (np.arange(grid.n) < grid.n - 1)
    np.testing.assert_allclose(rd[big], 4.0)
    np.testing.assert_allclose(rd[small], 1.0)
    mid = (x < 1000) & (x > 100)
    expect = np.exp((np.log(x[mid]) - np.log(100)) / (np.log(1000) - np.log(100)) * np.log(4))
    np.testing.assert_allclose(rd[mid], expect)
    for bad in (lambda: KnotSelection((1.0,), (1.0, 2.0)), lambda: KnotSelection((1.0,), (0.0,))):
        with pytest.raises(ValueError):
            bad()


def test_austin_and_mill_validation():
    with pytest.raises(ValueError):
        AustinSelection(A=0)
    with pytest.raises(ValueError):
        BallMill(n_mixers=0)


def test_efficiency_at_d50c_half_and_limits():
    assert float(corrected_efficiency(100.0, 100.0, 3.0)) == pytest.approx(0.5)
    assert float(corrected_efficiency(1e12, 100.0, 3.0)) == pytest.approx(1.0)
    assert float(corrected_efficiency(0.0, 100.0, 3.0)) == 0.0
    ea = EfficiencyCurve(100.0, 3.0, 0.2).efficiency(np.array([0.0, 100.0, 1e9]))
    np.testing.assert_allclose(ea, [0.2, 0.6, 1.0])


def test_classifier_limits_and_conservation(grid):
    feed = Stream.from_fractions(grid, np.ones(grid.n), 100.0, 80.0)
    c, f = EfficiencyCurve(100.0, 3.0, 0.2).split(feed)
    np.testing.assert_allclose(c.solids + f.solids, feed.solids, atol=1e-12)
    assert c.water + f.water == pytest.approx(feed.water)
    # d50c -> infinito: todo al overflow salvo el bypass Rf
    c, f = EfficiencyCurve(1e15, 3.0, 0.2).split(feed)
    np.testing.assert_allclose(c.solids, 0.2 * feed.solids, rtol=1e-9)
    # Rf = 1: todo al underflow
    c, f = EfficiencyCurve(100.0, 3.0, 1.0).split(feed)
    np.testing.assert_allclose(c.solids, feed.solids)
    assert f.total_solids == 0 and f.water == pytest.approx(0)
    for kw in ({"d50c": 0}, {"alpha": 0}, {"rf": 1.5}):
        with pytest.raises(ValueError):
            EfficiencyCurve(**kw)


def test_screen_use_rf_zero(grid):
    feed = Stream.from_fractions(grid, np.ones(grid.n), 10.0, 5.0)
    over, under = EfficiencyCurve(1000.0, 4.0, 0.0).split(feed)
    assert over.water == 0 and under.water == pytest.approx(5.0)
    assert over.p80 > under.p80


def test_unit_ops_conservation(fresh):
    outs = MillOp(BallMill())([fresh])
    assert abs(outs[0].total_solids - fresh.total_solids) < 1e-10
    c, f = ClassifierOp(EfficiencyCurve())([fresh, fresh])
    assert abs(c.total_solids + f.total_solids - 2 * fresh.total_solids) < 1e-10
    (s,) = SumpOp(40.0)([fresh])
    assert s.pct_solids == pytest.approx(40.0) and s.total_solids == pytest.approx(100.0)
    (same,) = SumpOp(None)([fresh])
    assert same.water == fresh.water
    wet = fresh.with_water(1000.0)
    (kept,) = SumpOp(40.0)([wet])
    assert kept.water == 1000.0  # no quita agua
    with pytest.raises(ValueError):
        SumpOp(100.0)
