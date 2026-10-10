"""Validación contra plantas reales publicadas. Tolerancias fijadas ANTES de correr.

C2 Vazante (ciclones):
  - partición recalculada desde granulometrías balanceadas vs la publicada: ±1,5 puntos;
  - agua a gruesos desde el balance de agua: ±0,5 puntos;
  - Whiten con Rf = agua a gruesos (método del artículo): d50c ±10 %, alpha ±15 %.
C4 Constancia (Bond):
  - energía de Bond del simulador vs la columna «modelo» del reporte: ±5 % por muestreo;
  - promedio planta/modelo recalculado vs el publicado (1,12): ±0,01;
  - cada factor publicado dentro del intervalo que permite el redondeo de la tabla.
"""

import numpy as np
import pytest

from conminucion.plantas_reales import (
    BOUGAINVILLE_ALIM_TPH,
    CONSTANCIA,
    CONSTANCIA_FACTOR_PROMEDIO,
    MADNEULI_CLASIFICADORES,
    MADNEULI_NODOS,
    MODSIM_ALIM_MOLINO_PASANTE,
    MODSIM_BOUGAINVILLE,
    MODSIM_DESCARGA_PASANTE,
    MODSIM_PRODUCTO_PASANTE,
    MODSIM_UNDERFLOW_PASANTE,
    VAZANTE_C1,
    VAZANTE_C2,
    bougainville_config,
    carga_circulante_por_granulometria,
    cierre_nodo,
    energia_bond_constancia,
    evaluar_ciclon,
    pasante_estilo_modsim,
    simular_bougainville,
    tamano_estilo_modsim,
)
from conminucion.stream import Stream

VAZANTE = [VAZANTE_C1, VAZANTE_C2]


@pytest.mark.parametrize("survey", VAZANTE, ids=["campana1", "campana2"])
def test_vazante_particion_reproduce_la_tabla_publicada(survey):
    res = evaluar_ciclon(survey)
    calculada = dict(zip(res.inferior_um, res.particion_pct, strict=True))
    for inferior, publicada in survey.particion_publicada.items():
        assert calculada[inferior] == pytest.approx(publicada, abs=1.5), inferior


@pytest.mark.parametrize("survey", VAZANTE, ids=["campana1", "campana2"])
def test_vazante_agua_a_gruesos(survey):
    res = evaluar_ciclon(survey)
    assert res.agua_a_gruesos_pct == pytest.approx(survey.agua_a_gruesos_pct, abs=0.5)


@pytest.mark.parametrize("survey", VAZANTE, ids=["campana1", "campana2"])
def test_vazante_whiten_reproduce_d50c_y_alpha(survey):
    res = evaluar_ciclon(survey)
    assert res.d50c_um == pytest.approx(survey.d50c_um, rel=0.10)
    assert res.alpha == pytest.approx(survey.alpha, rel=0.15)


def test_constancia_bond_reproduce_la_columna_modelo():
    for m, energia in energia_bond_constancia():
        assert energia == pytest.approx(m.energia_modelo, rel=0.05), m.numero


def test_constancia_factor_promedio_publicado():
    factores = [m.energia_planta / m.energia_modelo for m in CONSTANCIA]
    assert np.mean(factores) == pytest.approx(CONSTANCIA_FACTOR_PROMEDIO, abs=0.01)
    # Coherencia interna de la fuente: las energías vienen con un decimal (±0,05), así que
    # el factor publicado debe caer en el intervalo que permite ese redondeo.
    for m in CONSTANCIA:
        bajo = (m.energia_planta - 0.05) / (m.energia_modelo + 0.05) - 0.005
        alto = (m.energia_planta + 0.05) / (m.energia_modelo - 0.05) + 0.005
        assert bajo <= m.factor_publicado <= alto, m.numero


# C3 Madneuli — tolerancias fijadas antes de correr:
#   - cierre de sólidos en cada nodo del diagrama balanceado: ±2 %;
#   - cierre de -74 µm en los nodos SIN molienda (un molino fabrica finos): ±2 %;
#   - carga circulante desde el % -74 µm (reconciliación) vs la de los flujos: ±10 % relativo.

NODOS_SIN_MOLIENDA = [n for n in MADNEULI_NODOS if not n.startswith("molino")]


@pytest.mark.parametrize("nodo", list(MADNEULI_NODOS))
def test_madneuli_solidos_cierran_en_cada_nodo(nodo):
    assert abs(cierre_nodo(nodo, "solidos")) <= 0.02


@pytest.mark.parametrize("nodo", NODOS_SIN_MOLIENDA)
def test_madneuli_menos74_cierra_donde_no_hay_molienda(nodo):
    assert abs(cierre_nodo(nodo, "menos74")) <= 0.02


def test_madneuli_los_molinos_generan_finos():
    for nodo in MADNEULI_NODOS:
        if nodo.startswith("molino"):
            assert cierre_nodo(nodo, "menos74") > 0.5


@pytest.mark.parametrize("clasificador", list(MADNEULI_CLASIFICADORES))
def test_madneuli_carga_circulante(clasificador):
    simulada, publicada = carga_circulante_por_granulometria(clasificador)
    assert simulada == pytest.approx(publicada, rel=0.10)


# C1 Bougainville vs MODSIM 3.6.24 — tolerancias declaradas ANTES de correr:
#   - carga circulante y alimentación al molino: ±5 %;
#   - P80, P50 y P20 del producto (convención de MODSIM): ±5 %;
#   - cada punto de la granulometría del producto: ±3 puntos;
#   - agua del cajón y % de sólidos del rebose: ±2 %.
# Supuesto declarado: una sola región de mezcla perfecta (fracciones 1 y 2 = 0 en el .cur).


@pytest.fixture(scope="module")
def bougainville():
    return simular_bougainville()


def test_bougainville_carga_circulante_y_alimentacion(bougainville):
    s = bougainville.streams
    ref = MODSIM_BOUGAINVILLE
    assert bougainville.circulating_load == pytest.approx(
        ref["underflow_tph"] / BOUGAINVILLE_ALIM_TPH, rel=0.05
    )
    assert s["alim_molino"].total_solids == pytest.approx(ref["alim_molino_tph"], rel=0.05)


# Hallazgo: el P20 queda en -5,2 % (fuera del ±5 %). El residuo viene del molino, cuya
# discretización exacta en MODSIM no se pudo identificar (ver docs/VALIDACION_PLANTAS_REALES.md).
@pytest.mark.parametrize(
    ("p", "key"),
    [
        (0.8, "p80_um"),
        (0.5, "p50_um"),
        pytest.param(0.2, "p20_um", marks=pytest.mark.xfail(strict=True, reason="molino")),
    ],
)
def test_bougainville_tamanos_del_producto(bougainville, p, key):
    prod = bougainville.streams["overflow"]
    assert tamano_estilo_modsim(prod, p) == pytest.approx(MODSIM_BOUGAINVILLE[key], rel=0.05)


def test_bougainville_granulometria_del_producto(bougainville):
    ours = pasante_estilo_modsim(bougainville.streams["overflow"])
    np.testing.assert_allclose(ours, MODSIM_PRODUCTO_PASANTE, atol=3.0)


def test_bougainville_agua(bougainville):
    s = bougainville.streams
    sump_water = s["alim_ciclon"].water - s["descarga_molino"].water
    assert sump_water == pytest.approx(MODSIM_BOUGAINVILLE["agua_cajon_m3h"], rel=0.02)
    assert s["overflow"].pct_solids == pytest.approx(
        MODSIM_BOUGAINVILLE["overflow_pct_solidos"], rel=0.02
    )


# Comparación por equipo, alimentando cada uno con la corriente que calculó MODSIM. Son guardas
# de regresión: los valores se conocían al escribirlas.
def _masas_desde_pasante(pasante) -> np.ndarray:
    p = np.asarray(pasante) / 100.0
    return -np.diff(np.concatenate(([1.0], p, [0.0])))


def test_bougainville_ciclon_solo_reproduce_modsim():
    cfg = bougainville_config()
    feed = Stream(
        cfg.fresh.grid,
        _masas_desde_pasante(MODSIM_DESCARGA_PASANTE) * MODSIM_BOUGAINVILLE["alim_molino_tph"],
        431.28,
    )
    coarse, fine = cfg.classifier.split(feed)
    assert coarse.total_solids == pytest.approx(MODSIM_BOUGAINVILLE["underflow_tph"], rel=1e-3)
    np.testing.assert_allclose(pasante_estilo_modsim(fine), MODSIM_PRODUCTO_PASANTE, atol=0.01)
    np.testing.assert_allclose(pasante_estilo_modsim(coarse), MODSIM_UNDERFLOW_PASANTE, atol=0.05)


def test_bougainville_molino_solo_cerca_de_modsim():
    cfg = bougainville_config()
    feed = Stream(
        cfg.fresh.grid,
        _masas_desde_pasante(MODSIM_ALIM_MOLINO_PASANTE) * MODSIM_BOUGAINVILLE["alim_molino_tph"],
        86.33,
    )
    out = cfg.mill(feed)
    np.testing.assert_allclose(pasante_estilo_modsim(out), MODSIM_DESCARGA_PASANTE, atol=1.2)
    assert out.water == pytest.approx(209.34, rel=1e-3)
