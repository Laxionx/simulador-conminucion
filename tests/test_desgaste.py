"""Desgaste de bolas. Tolerancias fijadas ANTES de correr:

- Teoría de Davis (1919, ley de volumen, Δ = 3), Tablas 19, 20 y 21: ±0,05 puntos de % en
  peso (las tablas redondean a 1 o 2 decimales).
- Cargas MEDIDAS en Miami Copper (Tabla 19) y Golden Cycle (Tabla 20) con Δ = 3: ±3 puntos por
  intervalo.
- Ley lineal (Δ = 2) contra la curva empírica de Bond (d/D)^3,8: ±3 puntos en el acumulado.
- Simulación por cohortes contra la solución analítica: 1e-6.
- Correlaciones de Bond (1964) contra la Tabla 6 del informe GM71739 (Quebec): ±1 %.
"""

import numpy as np
import pytest

from conminucion.desgaste import (
    bond_wear_kg_per_kwh,
    charge_balance,
    cohort_charge,
    fit_wear_exponent,
    seasoned_charge,
)

INCH = 25.4

# ---------------------------------------------------- Davis (1919), vía 911Metallurgist
# Tabla 21 (teoría, % en peso por intervalo de 1/4"): recarga (pulg), descarte (pulg) -> valores
DAVIS_T21 = {
    (5, 0): [
        14.26,
        12.83,
        11.49,
        10.22,
        9.02,
        7.88,
        6.84,
        5.86,
        4.96,
        4.14,
        3.39,
        2.71,
        2.11,
        1.58,
        1.14,
        0.76,
        0.46,
        0.24,
        0.09,
        0.02,
    ],
    (5, 3): [18.19, 16.36, 14.65, 13.04, 11.51, 10.05, 8.73, 7.47],
    (4, 1): [17.89, 15.63, 13.57, 11.63, 9.84, 8.21, 6.73, 5.38, 4.20, 3.14, 2.27, 1.51],
    (3, 2.5): [54.52, 45.48],
    (2, 0.5): [33.54, 25.16, 18.16, 12.07, 7.38, 3.69],
}


# Hallazgo: en la columna (2", 0,5") Davis publicó 18,16 y 3,69; la fórmula exacta da 18,06 y 3,77
# (errores aritméticos de 1919). Queda como fallo esperado y estricto.
ERRATA_DAVIS = (2, 0.5)


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(c, marks=pytest.mark.xfail(strict=True, reason="aritmética de la fuente"))
        if c == ERRATA_DAVIS
        else c
        for c in DAVIS_T21
    ],
)
def test_teoria_de_davis_tabla_21(case):
    makeup, discard = case
    expected = DAVIS_T21[case]
    sieves = [(makeup - 0.25 * i) * INCH for i in range(len(expected))]
    ours = 100 * seasoned_charge(sieves, {makeup * INCH: 1.0}, discard * INCH, exponent=3.0)
    np.testing.assert_allclose(ours, expected, atol=0.05)


# Tabla 19: Miami Copper, molino Hardinge de 8 pies, un año con recarga diaria de bolas de 2".
MIAMI_SIEVES_IN = [2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 0.8, 0.6, 0.4]
MIAMI_MEDIDO = [27.46, 21.00, 17.70, 12.84, 9.04, 5.75, 3.36, 1.91, 0.94]
MIAMI_CALCULADO = [27.10, 21.70, 16.90, 12.70, 9.10, 6.10, 3.70, 1.90, 0.80]
# Tabla 20: Golden Cycle, bolas de 5,5", se descartan bajo 2,9".
GOLDEN_SIEVES_IN = [5.5 - 0.2 * i for i in range(13)]
GOLDEN_MEDIDO = [12.83, 12.54, 13.18, 8.55, 8.59, 8.44, 6.78, 5.55, 4.23, 5.36, 5.25, 4.52, 4.18]
GOLDEN_CALCULADO = [12.32, 11.43, 10.57, 9.74, 8.94, 8.18, 7.46, 6.76, 6.10, 5.48, 4.89, 4.33, 3.80]


def _miami():
    s = [x * INCH for x in MIAMI_SIEVES_IN]
    return 100 * seasoned_charge(s, {2.0 * INCH: 1.0}, 0.0, exponent=3.0)


def _golden():
    s = [x * INCH for x in GOLDEN_SIEVES_IN]
    return 100 * seasoned_charge(s, {5.5 * INCH: 1.0}, 2.9 * INCH, exponent=3.0)


def test_errata_de_davis_con_la_formula_exacta():
    b = [2.0, 1.75, 1.5, 1.25, 1.0, 0.75]
    exact = [100 * (b[i] ** 3 - (b[i + 1] if i < 5 else 0.5) ** 3) / (8 - 0.125) for i in range(6)]
    ours = 100 * seasoned_charge([x * INCH for x in b], {2 * INCH: 1.0}, 0.5 * INCH, exponent=3.0)
    np.testing.assert_allclose(ours, exact, rtol=1e-12)
    assert exact[2] == pytest.approx(18.06, abs=0.005) and exact[5] == pytest.approx(
        3.77, abs=0.005
    )


def test_davis_columnas_calculadas():
    np.testing.assert_allclose(_miami(), MIAMI_CALCULADO, atol=0.05)
    np.testing.assert_allclose(_golden(), GOLDEN_CALCULADO, atol=0.05)


def test_cargas_medidas_en_planta():
    np.testing.assert_allclose(_miami(), MIAMI_MEDIDO, atol=3.0)
    np.testing.assert_allclose(_golden(), GOLDEN_MEDIDO, atol=3.0)


# ------------------------------------------------------------------ Bond y las leyes de desgaste
def test_bond_3_8_es_delta_2_2_y_la_ley_lineal_queda_cerca():
    sieves = list(np.linspace(80.0, 4.0, 20))
    d_top = sieves[0]
    lower = np.append(sieves[1:], 0.0)
    bond_cum = (lower / d_top) ** 3.8  # % que pasa el límite inferior de cada clase
    for exponent, tol in ((2.2, 1e-9), (2.0, 0.03)):
        fr = seasoned_charge(sieves, {d_top: 1.0}, 0.0, exponent)
        passing = 1.0 - np.cumsum(fr)
        np.testing.assert_allclose(passing, bond_cum, atol=tol)


@pytest.mark.parametrize(
    ("exponent", "discard"), [(2.0, 0.0), (2.0, 15.0), (2.2, 10.0), (3.0, 12.0), (2.5, 0.0)]
)
def test_cohortes_reproducen_la_solucion_analitica(exponent, discard):
    sieves = [60.0, 50.0, 40.0, 30.0, 20.0, 10.0]
    analytic = seasoned_charge(sieves, {60.0: 1.0}, discard, exponent)
    # el error del control es proporcional a 1/N: 5,7e-6 con 400 mil, 4,6e-7 con 4 millones
    numeric = cohort_charge(sieves, 60.0, discard, exponent, cohorts=4_000_000)
    np.testing.assert_allclose(numeric, analytic, atol=1e-6)


def test_varias_medidas_de_recarga_se_superponen():
    sieves = [80.0, 60.0, 40.0, 20.0]
    a = seasoned_charge(sieves, {80.0: 1.0}, 10.0, 2.0)
    b = seasoned_charge(sieves, {60.0: 1.0}, 10.0, 2.0)
    mix = seasoned_charge(sieves, {80.0: 0.5, 60.0: 0.5}, 10.0, 2.0)
    # pesos: masa de la carga que aporta cada recarga, por kg recargado
    w_a = (80.0**4 - 10.0**4) / 80.0**3
    w_b = (60.0**4 - 10.0**4) / 60.0**3
    np.testing.assert_allclose(mix, (w_a * a + w_b * b) / (w_a + w_b), rtol=1e-12)


# ------------------------------------------------------------------ consumo (Bond 1964)
# GM71739 (Sirios Resources, proyecto Cheechoo), Tabla 6, kg/kWh
QUEBEC = {
    0.457: {
        "barras_molino_barras": 0.1347,
        "bolas_molino_bolas_humedo": 0.1211,
        "revestimiento_chancadoras": 0.0278,
        "rodillos_chancadora": 0.0581,
    },
    0.352: {
        "barras_molino_barras": 0.1276,
        "bolas_molino_bolas_humedo": 0.1107,
        "revestimiento_chancadoras": 0.0235,
        "rodillos_chancadora": 0.0489,
    },
    0.229: {
        "barras_molino_barras": 0.1162,
        "bolas_molino_bolas_humedo": 0.0951,
        "revestimiento_chancadoras": 0.0184,
        "rodillos_chancadora": 0.0366,
    },
}
# Revestimientos (kg/kWh): molino de barras y molino de bolas en húmedo
QUEBEC_REVESTIMIENTOS = {0.457: (0.0125, 0.0094), 0.352: (0.0115, 0.0086), 0.229: (0.0101, 0.0075)}


@pytest.mark.parametrize("ai", list(QUEBEC))
def test_bond_1964_contra_el_informe_de_quebec(ai):
    for element, published in QUEBEC[ai].items():
        assert bond_wear_kg_per_kwh(ai, element) == pytest.approx(published, rel=0.01), element


@pytest.mark.xfail(strict=True, reason="el informe redondeó los coeficientes de Bond")
def test_revestimientos_con_la_tolerancia_declarada():
    for ai, (rod, ball) in QUEBEC_REVESTIMIENTOS.items():
        assert bond_wear_kg_per_kwh(ai, "revestimiento_molino_barras") == pytest.approx(
            rod, rel=0.01
        )
        assert bond_wear_kg_per_kwh(ai, "revestimiento_molino_bolas_humedo") == pytest.approx(
            ball, rel=0.01
        )


def test_hallazgo_coeficientes_del_informe():
    """Bond: 0,035 y 0,026 lb/kWh, con (Ai - 0,015). El informe usa 0,016 y 0,012 kg/kWh y, en
    el de bolas, (Ai - 0,020): con SUS fórmulas se reproduce SU tabla; las de Bond quedan
    entre 0,4 y 2 % abajo."""
    for ai, (rod, ball) in QUEBEC_REVESTIMIENTOS.items():
        assert 0.016 * (ai - 0.015) ** 0.30 == pytest.approx(rod, rel=0.006)
        assert 0.012 * (ai - 0.020) ** 0.30 == pytest.approx(ball, rel=0.006)
        for element, value in (
            ("revestimiento_molino_barras", rod),
            ("revestimiento_molino_bolas_humedo", ball),
        ):
            ours = bond_wear_kg_per_kwh(ai, element)
            assert ours < value and ours == pytest.approx(value, rel=0.025)


def test_balance_de_la_carga_a_mano():
    # Ley lineal, una sola bola de 76,2 mm, descarte a 25,4 mm: M = ρπ/6 · Q (D⁴ - d0⁴)/(4k)
    charge_t, makeup_kg_h = 250.0, 300.0
    rho, d, d0 = 7800.0, 76.2, 25.4
    m_ball = rho * np.pi / 6 * (d / 1000) ** 3
    q = makeup_kg_h / m_ball
    k = rho * np.pi / 6 * 1e-9 * q * (d**4 - d0**4) / 4 / (charge_t * 1000)
    res = charge_balance(charge_t, makeup_kg_h, {d: 1.0}, d0, exponent=2.0)
    assert res.wear_constant == pytest.approx(k, rel=1e-12)
    assert res.balls_per_hour == pytest.approx(q, rel=1e-12)
    assert res.ball_life_h == pytest.approx((d - d0) / k, rel=1e-12)
    assert res.balls_in_charge == pytest.approx(q * (d - d0) / k, rel=1e-12)
    assert res.discard_kg_h + res.worn_kg_h == pytest.approx(makeup_kg_h)
    vol = charge_balance(charge_t, makeup_kg_h, {d: 1.0}, 0.0, exponent=3.0)
    assert vol.balls_in_charge is None and vol.ball_life_h == float("inf")


@pytest.mark.parametrize(
    "call",
    [
        lambda: seasoned_charge([50, 40], {60.0: 1.0}),
        lambda: seasoned_charge([50, 60], {40.0: 1.0}),
        lambda: seasoned_charge([50, 40], {40.0: 1.0}, discard_mm=45.0),
        lambda: seasoned_charge([50, 40], {40.0: 1.0}, exponent=6.5),
        lambda: charge_balance(0.0, 10.0, {50.0: 1.0}),
        lambda: bond_wear_kg_per_kwh(0.01),
        lambda: bond_wear_kg_per_kwh(0.3, "otro"),
    ],
)
def test_validaciones(call):
    with pytest.raises(ValueError):
        call()


def test_ajuste_del_exponente():
    sieves = [80.0, 70.0, 60.0, 50.0, 40.0, 30.0]
    synthetic = 100 * seasoned_charge(sieves, {80.0: 1.0}, 25.0, exponent=2.37)
    exponent, rms = fit_wear_exponent(sieves, {80.0: 1.0}, synthetic, 25.0)
    assert exponent == pytest.approx(2.37, abs=1e-4) and rms < 1e-6
    # Miami (Davis 1919): la carga medida favorece la ley de volumen
    miami, _ = fit_wear_exponent([x * INCH for x in MIAMI_SIEVES_IN], {2 * INCH: 1.0}, MIAMI_MEDIDO)
    assert miami == pytest.approx(3.0, abs=0.1)
