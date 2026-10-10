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
    CONSTANCIA,
    CONSTANCIA_FACTOR_PROMEDIO,
    MADNEULI_CLASIFICADORES,
    MADNEULI_NODOS,
    VAZANTE_C1,
    VAZANTE_C2,
    carga_circulante_por_granulometria,
    cierre_nodo,
    energia_bond_constancia,
    evaluar_ciclon,
)

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
