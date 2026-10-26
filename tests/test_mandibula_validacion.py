"""Validación del chancador de mandíbula contra la Tabla 3.1 de King y la curva de Nordberg.

Los listones se fijaron ANTES de mirar los resultados y no se cambian:
- capacidad: >= 80 % de los 56 puntos dentro de ±30 % (M2 y M4, fuera de muestra);
- producto: |Δ| <= 5 puntos porcentuales en todos los r y las 9 alimentaciones.
Un modelo que no pasa queda como xfail estricto con los números medidos.
"""

import numpy as np
import pytest

from conminucion.datos_mandibula import TABLA_KING
from conminucion.mandibula_validacion import (
    ALIMENTACIONES,
    R_PRODUCTO,
    ajustar_whiten,
    deltas_referencia,
    deltas_whiten,
    desglose_por_tamano,
    error_pct,
    guarda_potencia,
    maquina_producto,
    max_abs_por_alimentacion,
    modelo_m1,
    modelo_m2_cv,
    modelo_m3,
    modelo_m4_cv,
    puntos_king,
    razones_n_nc,
    resumen_errores,
)

BANDA_PCT = 30.0
LISTON_FRACCION = 0.80
LISTON_PP = 5.0

PUNTOS = puntos_king()
OBS = np.array([p.q_tph for p in PUNTOS])


def test_tabla_king_tiene_56_puntos():
    assert len(PUNTOS) == 56
    assert len(TABLA_KING) == 12
    assert not any(p.nombre == "30x42" and p.oss_mm == 102 for p in PUNTOS)  # errata excluida


def _fraccion(pred):
    return resumen_errores(error_pct(pred, OBS), PUNTOS, BANDA_PCT)["frac_banda"]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "M1 (referencia R, k = 1,485): 40/56 = 71,4 % dentro de ±30 % (liston 80 %); mediana "
        "|error| 19,3 %; peor 36x48 OSS 76: -47,5 %; sesgo bajo en 10 de 12 tamanos"
    ),
)
def test_m1_referencia_r_capacidad():
    assert _fraccion(modelo_m1(PUNTOS)) >= LISTON_FRACCION


def test_m2_cinematica_con_k_fuera_de_muestra():
    pred, k_pliegue, k_global = modelo_m2_cv(PUNTOS)
    assert len(k_pliegue) == 12 and k_global > 0
    assert _fraccion(pred) >= LISTON_FRACCION


@pytest.mark.xfail(
    strict=True,
    reason=(
        "M3 (Taggart, rho_b 1,6): 20/56 = 35,7 % dentro de ±30 %; mediana |error| 40,7 %; "
        "peor 42x48 OSS 127: -58,3 %; subestima sistematicamente las maquinas grandes (24x36 "
        "en adelante, -31 a -52 %)"
    ),
)
def test_m3_taggart():
    assert _fraccion(modelo_m3(PUNTOS)) >= LISTON_FRACCION


def test_m4_control_empirico_fuera_de_muestra():
    assert _fraccion(modelo_m4_cv(PUNTOS)) >= LISTON_FRACCION


def test_desglose_cubre_los_12_tamanos():
    d = desglose_por_tamano(error_pct(modelo_m1(PUNTOS), OBS), PUNTOS)
    assert len(d) == 12 and sum(v[2] for v in d.values()) == 56


def test_razones_n_nc_positivas():
    r = razones_n_nc(PUNTOS)
    assert len(r) == 12 and all(0 < lo <= hi for lo, hi in r.values())


def test_guarda_de_potencia_es_finita_y_positiva():
    g = guarda_potencia(PUNTOS)
    assert g.shape == (56,) and np.all(g > 0) and np.all(np.isfinite(g))


# ------------------------------------------------------------ producto
JAW = maquina_producto()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "P1 (referencia R sin ajuste): max |delta| 17,2 a 20,8 pp segun la alimentacion "
        "(liston 5 pp); el producto de R es mas fino que la curva de Nordberg en r = 0,3-1,0"
    ),
)
def test_p1_referencia_r_producto():
    peor = max(max_abs_por_alimentacion(deltas_referencia(JAW)).values())
    assert peor <= LISTON_PP


@pytest.mark.xfail(
    strict=True,
    reason=(
        "P2 (whiten ajustado con n = 1,2 y F80/OSS = 5; alpha1 0,350, alpha2 4,350 (en el "
        "limite superior de la brecha), exponente 7,80): ajuste RMS 1,5 pp; fuera de muestra "
        "max |delta| 2,0 a 9,4 pp, peor n = 0,8 y F80/OSS = 3; 4 de las 8 pasan el liston de "
        "5 pp y 4 no"
    ),
)
def test_p2_whiten_ajustado_fuera_de_muestra():
    ajustada, _ = ajustar_whiten(JAW)
    deltas = deltas_whiten(ajustada)
    fuera = {k: v for k, v in max_abs_por_alimentacion(deltas).items() if k != (1.2, 5.0)}
    assert len(fuera) == 8 and len(ALIMENTACIONES) == 9 and len(R_PRODUCTO) == 7
    assert max(fuera.values()) <= LISTON_PP


def test_k_cal_es_el_ajuste_global_contra_king():
    """K_CAL se recalcula con los 56 puntos de la Tabla 3.1 (media geométrica del cociente)."""
    from conminucion.datos_mandibula import K_CAL
    from conminucion.mandibula_validacion import modelo_m2_cv, puntos_king

    assert modelo_m2_cv(puntos_king())[2] == pytest.approx(K_CAL, abs=0.001)
