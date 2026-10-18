"""Ensayo de Bond: la contabilidad contra la Tabla 2 de Liang et al. (2016), la molienda por lotes
contra soluciones exactas y la simulación del ensayo contra lo medido. Los cortes se fijaron antes
de correr."""

import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from conminucion.ensayo_bond import (
    CARGA_CIRCULANTE,
    ajustar_a_alpha,
    alimentacion_dos_puntos,
    contabilidad,
    indice_trabajo,
    ipp,
    matriz_generadora,
    moler_lote,
    nuevos_primeros_ciclos,
    seleccion_lotes,
    siguientes_revoluciones,
    simular_ensayo,
)
from conminucion.fracture import Fracture
from conminucion.mill import AustinSelection
from conminucion.sizes import SizeGrid, size_at_passing

# Liang, Wei, Xu, Xia y Li (2016), Minerals 6(2), 39, Tabla 2 (magnetita de Hebei oriental)
CARGA, FINOS_CARGA, TAMIZ, F80, P80, REV1 = 1365.0, 414.8, 150.0, 1450.0, 119.6, 100
FINOS = [583.9, 464.5, 379.6, 406.8, 409.0, 383.2, 397.9, 398.1, 394.2, 390.8, 382.5]
PUB_REV = [100, 126, 109, 106, 115, 107, 113, 108, 105, 104, 104]
PUB_DE_ALIM = [414.8, 177.4, 141.1, 115.3, 123.6, 124.3, 116.4, 120.9, 121.0, 119.8, 118.8]
PUB_NUEVOS = [169.1, 287.1, 238.5, 291.5, 285.4, 258.9, 281.5, 277.2, 273.2, 271.0, 263.7]
PUB_GBP = [1.6910, 2.2786, 2.1881, 2.3135, 2.4817, 2.4196, 2.4912, 2.5667, 2.6019, 2.6058, 2.5356]
GBP_FINAL, WI_PUB = 2.5811, 10.93
# La fila 4 publica 106 rev, pero su Gbp (2.3135 = 291.5 / 126) y la regla de GMG dan 126.
FILA_REV_ERRATA = 4
# Filas cuyo «de la alimentación» publicado difiere 0,1 g del que sale de 414,8/1365 (borde del
# redondeo): arrastran menos de 0,001 al Gbp.
FILAS_BORDE = {3, 4}


@pytest.fixture(scope="module")
def calc():
    return contabilidad(CARGA, FINOS_CARGA, FINOS, REV1, TAMIZ, F80, P80)


# ------------------------------------------------------------------ contabilidad de GMG
def test_ipp_y_la_regla_de_revoluciones_de_gmg():
    assert CARGA_CIRCULANTE == 2.5
    assert ipp(CARGA) == pytest.approx(390.0)
    assert siguientes_revoluciones(390.0, 177.4, 1.6910) == 126  # (390 - 177,4) / 1,691 = 125,7
    assert siguientes_revoluciones(390.0, 141.1, 2.2786) == 109  # 109,2


def test_las_11_filas_de_la_tabla_2_se_reproducen(calc):
    assert len(calc.ciclos) == 11
    for c, rev, de_alim, nuevos, gbp in zip(
        calc.ciclos, PUB_REV, PUB_DE_ALIM, PUB_NUEVOS, PUB_GBP, strict=True
    ):
        if c.ciclo != FILA_REV_ERRATA:
            assert c.revoluciones == rev, c.ciclo  # revoluciones, al entero
        assert abs(c.finos_de_alimentacion_g - de_alim) <= 0.1 + 1e-9, c.ciclo  # a 0,1 g
        assert abs(c.finos_nuevos_g - nuevos) <= 0.1 + 1e-9, c.ciclo
        if c.ciclo in FILAS_BORDE:
            assert abs(c.gbp - gbp) < 1e-3, c.ciclo
        else:
            assert round(c.gbp, 4) == gbp, c.ciclo  # Gbp, a 4 decimales


def test_la_fila_4_publica_una_errata_de_revoluciones(calc):
    # 291,5 g / 126 rev = 2,3135 (el Gbp publicado); con las 106 rev publicadas daría 2,7500
    assert round(PUB_NUEVOS[3] / 126, 4) == PUB_GBP[3]
    assert round(PUB_NUEVOS[3] / 106, 4) != PUB_GBP[3]
    assert calc.ciclos[3].revoluciones == 126
    # las otras 10 filas cuadran: Gbp publicado = nuevos publicados / revoluciones publicadas
    for i in range(11):
        if i + 1 != FILA_REV_ERRATA:
            assert PUB_NUEVOS[i] / PUB_REV[i] == pytest.approx(PUB_GBP[i], abs=6e-4)


def test_gbp_final_y_wi_de_la_tabla_3(calc):
    assert round(calc.gbp_final, 4) == GBP_FINAL  # media de los 3 últimos ciclos
    assert calc.wi == pytest.approx(WI_PUB, abs=0.05)
    assert calc.ipp_g == pytest.approx(390.0)


def test_wi_con_la_constante_del_enunciado_y_la_de_la_guia():
    # 1,1 x 44,5 en vez de 1,1023 x 44,5 (la guía usa 1,1023): 10,90 frente al 10,93 publicado
    gap = 10 / np.sqrt(P80) - 10 / np.sqrt(F80)
    assert 1.1 * 44.5 / (TAMIZ**0.23 * GBP_FINAL**0.82 * gap) == pytest.approx(10.90, abs=0.01)
    assert indice_trabajo(TAMIZ, GBP_FINAL, P80, F80) == pytest.approx(WI_PUB, abs=0.05)


def test_la_carga_circulante_se_acerca_a_250_por_ciento(calc):
    assert calc.ciclos[-1].carga_circulante_pct == pytest.approx(250.0, abs=10.0)


def test_el_criterio_de_termino_pide_cinco_ciclos_y_una_inversion(calc):
    assert [c.ciclo for c in calc.ciclos if c.invierte] == [3, 4, 6, 7, 11]
    assert calc.termina_en == 6  # primer ciclo >= 5 en que el Gbp invierte su dirección
    corto = contabilidad(CARGA, FINOS_CARGA, FINOS[:4], REV1, TAMIZ)
    assert corto.termina_en is None and corto.wi is None


@pytest.mark.parametrize(
    "args",
    [
        (0.0, 100.0, [500.0], 100, 150.0),  # carga 0
        (CARGA, CARGA, [500.0], 100, 150.0),  # todo es fino
        (CARGA, 100.0, [], 100, 150.0),  # sin ciclos
        (CARGA, 100.0, [-5.0], 100, 150.0),
        (CARGA, 100.0, [CARGA + 1], 100, 150.0),
        (CARGA, 100.0, [500.0], 0, 150.0),  # sin revoluciones
        (CARGA, 414.8, [400.0], 100, 150.0),  # no produjo finos nuevos
    ],
)
def test_la_contabilidad_rechaza_datos_imposibles(args):
    with pytest.raises(ValueError):
        contabilidad(*args)


def test_wi_rechaza_p80_mayor_que_f80():
    with pytest.raises(ValueError):
        indice_trabajo(150.0, 2.5, 2000.0, 1450.0)
    with pytest.raises(ValueError):
        indice_trabajo(150.0, 0.0, 100.0, 1450.0)


# ------------------------------------------------------------------ molienda por lotes
def _grid():
    return SizeGrid.geometric(3350.0, 12, (3350.0 / 150.0) ** (1 / 9))


def test_la_molienda_por_lotes_conserva_la_masa():
    grid, sel, fr = _grid(), AustinSelection(), Fracture()
    w0 = np.linspace(1.0, 2.0, grid.n)
    w0 /= w0.sum()
    for minutos in (0.0, 0.3, 1.43, 20.0):
        w = moler_lote(grid, w0, minutos, sel, fr)
        assert abs(w.sum() - 1.0) < 1e-12 and w.min() > -1e-15
    m = matriz_generadora(seleccion_lotes(grid, sel), fr.appearance(grid))
    assert np.abs(m.sum(axis=0)).max() < 1e-12  # cada columna suma cero


def test_una_sola_clase_coincide_con_la_exponencial_analitica():
    s, t, w0 = 0.7, 1.43, 3.0
    m = matriz_generadora(np.array([s]), np.array([[0.0]]))
    assert (expm(m * t) @ np.array([w0]))[0] == pytest.approx(w0 * np.exp(-s * t), rel=1e-13)


def test_dos_clases_coinciden_con_la_solucion_exacta():
    s, t = 0.9, 2.0
    a = np.array([[0.0, 0.0], [1.0, 0.0]])  # todo lo que se rompe pasa a la clase fina
    m = matriz_generadora(np.array([s, 0.0]), a)
    out = expm(m * t) @ np.array([1.0, 0.0])
    assert out == pytest.approx([np.exp(-s * t), 1 - np.exp(-s * t)], rel=1e-13)


def test_la_exponencial_de_matriz_coincide_con_un_integrador_ode():
    grid, sel, fr = _grid(), AustinSelection(), Fracture()
    w0 = np.exp(-np.arange(grid.n) / 3.0)
    w0 /= w0.sum()
    m = matriz_generadora(seleccion_lotes(grid, sel), fr.appearance(grid))
    t = 100 / 70.0
    ode = solve_ivp(lambda _t, w: m @ w, (0, t), w0, method="DOP853", rtol=1e-13, atol=1e-15)
    assert np.abs(ode.y[:, -1] - moler_lote(grid, w0, t, sel, fr)).max() < 1e-8


def test_el_tiempo_negativo_se_rechaza():
    with pytest.raises(ValueError):
        moler_lote(_grid(), np.ones(12), -1.0, AustinSelection(), Fracture())


# ------------------------------------------------------------------ simulación del ensayo
@pytest.fixture(scope="module")
def caso():
    alim = alimentacion_dos_puntos(TAMIZ, F80, FINOS_CARGA / CARGA)
    fr = Fracture()
    sel = ajustar_a_alpha(alim, fr, CARGA, (PUB_NUEVOS[0], PUB_NUEVOS[1]), (100, 126))
    return alim, fr, sel, simular_ensayo(alim, sel, fr, CARGA, 11, REV1, F80)


def test_la_alimentacion_pasa_por_los_dos_puntos(caso):
    alim = caso[0]
    assert alim.tamiz_um == pytest.approx(150.0)
    assert alim.fraccion_bajo_tamiz == pytest.approx(FINOS_CARGA / CARGA, abs=1e-6)
    assert size_at_passing(alim.grid, alim.fracciones, 0.8) == pytest.approx(F80, rel=0.005)
    assert alim.fracciones.sum() == pytest.approx(1.0)


def test_el_ajuste_mueve_solo_a_y_alpha(caso):
    sel, base = caso[2], AustinSelection()
    assert (sel.mu, sel.lam, sel.tau) == (base.mu, base.lam, base.tau)
    assert (sel.A, sel.alpha) != (base.A, base.alpha)


def test_el_ajuste_reproduce_los_finos_nuevos_de_los_ciclos_1_y_2(caso):
    alim, fr, sel, _ = caso
    nuevos = nuevos_primeros_ciclos(alim, sel, fr, CARGA, (100, 126))  # las revoluciones del ajuste
    # dos datos, dos parámetros: no hay raíz exacta, el mejor ajuste queda a ~1 %
    assert nuevos == pytest.approx(PUB_NUEVOS[:2], rel=0.02)
    assert abs(nuevos[0] / PUB_NUEVOS[0] - 1) > 1e-4  # y no es exacto: se informa


def test_la_simulacion_respeta_el_procedimiento(caso):
    sim, fraccion = caso[3], FINOS_CARGA / CARGA
    assert [c.ciclo for c in sim.ciclos] == list(range(1, 12))
    assert sim.ciclos[0].revoluciones == REV1
    for prev, c in zip(sim.ciclos, sim.ciclos[1:], strict=False):
        esperado = siguientes_revoluciones(390.0, prev.finos_total_g * fraccion, prev.gbp)
        assert c.revoluciones == esperado
    assert sim.ciclos[-1].carga_circulante_pct == pytest.approx(250.0, abs=10.0)


def test_corte_gbp_final_simulado_a_10_por_ciento_de_lo_medido(caso):
    assert caso[3].gbp_final == pytest.approx(GBP_FINAL, rel=0.10)


@pytest.mark.xfail(
    strict=True,
    reason="Resultado negativo: el Wi simulado queda ~12 % bajo el medido porque el producto "
    "simulado es más fino (P80 ~107 µm frente a 119,6) y el Gbp, 6 % más alto. Coincide con la "
    "revisión de 2023 «The truth about population balance modeling»: un ensayo por lotes ajustado "
    "a los primeros ciclos no predice el de ciclo cerrado con exactitud.",
)
def test_corte_wi_simulado_a_10_por_ciento_de_lo_medido(caso):
    assert caso[3].wi == pytest.approx(WI_PUB, rel=0.10)


def test_el_resultado_negativo_del_wi_queda_fijado(caso):
    # si el modelo cambia, este valor cambia y el cambio no pasa desapercibido
    assert caso[3].wi == pytest.approx(9.59, abs=0.05)
    assert caso[3].p80_um == pytest.approx(106.5, abs=1.0)


def test_la_regla_de_revoluciones_rechaza_un_gbp_no_positivo():
    for gbp in (0.0, -1.0):
        with pytest.raises(ValueError):
            siguientes_revoluciones(390.0, 100.0, gbp)


def test_la_simulacion_coincide_con_una_reimplementacion_independiente(caso):
    """Oráculo: el mismo ensayo con solo exponencial de matriz y tamizado a mano, sin las
    funciones del módulo que se prueba (salvo la selección y la fractura)."""
    alim, fr, sel, sim = caso
    grid, i0 = alim.grid, alim.idx_tamiz
    m = matriz_generadora(seleccion_lotes(grid, sel), fr.appearance(grid))
    w = CARGA * alim.fracciones
    fraccion = FINOS_CARGA / CARGA
    rev, gbps, finos_ciclos = REV1, [], []
    for _ in range(11):
        salida = expm(m * rev / 70.0) @ w
        finos = salida[i0:].sum()
        gbps.append((finos - w[i0:].sum()) / rev)
        finos_ciclos.append(salida.copy())
        finos_ciclos[-1][:i0] = 0.0
        w = salida.copy()
        w[i0:] = 0.0
        w += finos * alim.fracciones
        rev = round((CARGA / 3.5 - fraccion * finos) / gbps[-1])
    assert [c.gbp for c in sim.ciclos] == pytest.approx(gbps, rel=1e-9)
    assert sim.gbp_final == pytest.approx(np.mean(gbps[-3:]), rel=1e-12)
    producto = np.sum(finos_ciclos[-3:], axis=0)
    assert sim.p80_um == pytest.approx(size_at_passing(alim.grid, producto, 0.8), rel=1e-9)
    assert abs(sim.p80_um - size_at_passing(alim.grid, finos_ciclos[-1], 0.8)) > 1e-3  # 3 ciclos
