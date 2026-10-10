"""Hidrociclón de Plitt en la forma de MODSIM (modelo CYCL) contra el ejercicio 2-2 del curso que
trae MODSIM 3.6.24 Academic (DOCS/Modsim Training/Module2). Tolerancias fijadas ANTES de correr:

- d50c: 90,9 µm con el ápex estándar (11,6 % de Dc) y 75,8 µm con ápex de 15 %: ±0,1 µm. No es
  ciega: al leer CLASMODS.FOR se comprobó a mano que da 90,94 y 75,76 µm.
- % de sólidos: descarga 70,9 % y rebalse 13,7 % (ápex estándar); descarga 55,1 % (ápex 15 %):
  ±0,1 puntos.
- d80 del rebalse 81,6 µm y de la descarga 516 µm (ápex estándar), interpolados como MODSIM: ±1 %.
- Ápex mínimo de Mular y Jull con el ápex estándar: 7,4 cm, ±0,05 cm. Ambos casos avisan embanque.
- Conservación de sólidos y de agua: 1e-12 relativo.
"""

from __future__ import annotations

import numpy as np
import pytest

from conminucion.modsim import alimentacion_modsim, lista_modsim
from conminucion.plantas_reales import tamano_estilo_modsim
from conminucion.plitt import PlittCyclone

# Ejercicio 2-1: sílice de densidad 2,7; 50 t/h al 40 % de sólidos; tamaño mayor 2 mm, 25 clases
TAMICES_UM = (850, 600, 425, 300, 212, 150, 106, 75, 53, 38)
PASANTE_PCT = (95.7, 88.3, 77.0, 63.3, 49.6, 37.4, 27.3, 19.6, 13.8, 10.2)
LISTA_UM = lista_modsim(2000.0, 25)


def _feed():
    return alimentacion_modsim(2000.0, 25, TAMICES_UM, PASANTE_PCT, tph=50.0, water=75.0, rho_s=2.7)


def _cyclone(spigot: float = 0.116) -> PlittCyclone:
    # 60 cm, geometría "estándar" y los demás valores por defecto del formulario de MODSIM
    return PlittCyclone(diameter_m=0.6, spigot=spigot, size_basis="tamiz_inferior")


def _pct_solids(stream) -> float:
    return 100.0 * stream.total_solids / (stream.total_solids + stream.water)


@pytest.mark.parametrize(("spigot", "d50c"), [(0.116, 90.9), (0.15, 75.8)])
def test_d50c_igual_al_de_modsim(spigot, d50c):
    assert _cyclone(spigot).performance(_feed()).d50c_um == pytest.approx(d50c, abs=0.1)


@pytest.mark.parametrize(
    ("spigot", "underflow", "overflow"), [(0.116, 70.9, 13.7), (0.15, 55.1, None)]
)
def test_porcentaje_de_solidos(spigot, underflow, overflow):
    coarse, fine = _cyclone(spigot).split(_feed())
    assert _pct_solids(coarse) == pytest.approx(underflow, abs=0.1)
    if overflow is not None:
        assert _pct_solids(fine) == pytest.approx(overflow, abs=0.1)


def test_d80_del_rebalse_y_de_la_descarga():
    coarse, fine = _cyclone().split(_feed())
    assert tamano_estilo_modsim(fine, 0.8, LISTA_UM) == pytest.approx(81.6, rel=0.01)
    assert tamano_estilo_modsim(coarse, 0.8, LISTA_UM) == pytest.approx(516.0, rel=0.01)


def test_embanque_de_mular_y_jull():
    cyclone = _cyclone()
    coarse, _ = cyclone.split(_feed())
    assert cyclone.min_spigot_m(coarse) == pytest.approx(0.074, abs=0.0005)
    assert cyclone.ropes(coarse)
    wide = _cyclone(0.15)
    assert wide.ropes(wide.split(_feed())[0])  # «el criterio de Mular-Judd sigue avisando»


@pytest.mark.parametrize("spigot", [0.116, 0.15])
def test_conserva_solidos_y_agua(spigot):
    feed = _feed()
    coarse, fine = _cyclone(spigot).split(feed)
    np.testing.assert_allclose(coarse.solids + fine.solids, feed.solids, rtol=1e-12)
    assert coarse.water + fine.water == pytest.approx(feed.water, rel=1e-12)


def test_alimentacion_interpolada_como_modsim():
    feed = _feed()
    assert feed.total_solids == pytest.approx(50.0)
    # en los tamices de los datos la interpolación devuelve el dato (localmente Rosin-Rammler)
    from conminucion.modsim import pasante_frpass

    for size, pct in zip(TAMICES_UM, PASANTE_PCT, strict=True):
        assert pasante_frpass(TAMICES_UM, PASANTE_PCT, size) == pytest.approx(pct, abs=1e-9)
    assert pasante_frpass(TAMICES_UM, PASANTE_PCT, 5000.0) == pytest.approx(100.0, abs=0.2)
    assert 0.0 < pasante_frpass(TAMICES_UM, PASANTE_PCT, 10.0) < 10.2  # ley de potencia


def test_ciclon_menor_corta_mas_fino_y_repartir_el_caudal_mas_grueso():
    feed = _feed()
    base = _cyclone().performance(feed).d50c_um
    assert PlittCyclone(diameter_m=0.38).performance(feed).d50c_um < base
    assert PlittCyclone(diameter_m=0.6, n_cyclones=2).performance(feed).d50c_um > base


def test_errores():
    with pytest.raises(ValueError):
        PlittCyclone(diameter_m=0.0)
    with pytest.raises(ValueError):
        PlittCyclone(diameter_m=0.5, n_cyclones=0)
    with pytest.raises(ValueError):
        PlittCyclone(diameter_m=0.5, slurry_density_factor=1.0)


def test_bordes_de_la_interpolacion_de_modsim():
    from conminucion.modsim import pasante_frpass

    top = ((1000.0, 500.0, 250.0), (100.0, 60.0, 20.0))  # el primer tamiz ya deja pasar todo
    # Rareza de MODSIM, replicada: sobre ese tamiz extrapola desde el par siguiente y no da 100.
    # A mano: ξ = ln(1200/250)/ln 2 = 2,263; η = (ln(1/0,4)/ln(1/0,8))^ξ = 24,45; 1 - 0,8^η
    assert pasante_frpass(*top, 1200.0) == pytest.approx(99.573, abs=0.001)
    assert 60.0 < pasante_frpass(*top, 700.0) < 100.0
    bottom = ((1000.0, 500.0, 250.0), (80.0, 30.0, 0.0))  # el último tamiz no deja pasar nada
    assert 0.0 < pasante_frpass(*bottom, 300.0) < 30.0
    assert pasante_frpass(*bottom, 100.0) == 0.0
    assert pasante_frpass(*bottom, 0.0) == 0.0
    full = ((1000.0, 500.0, 250.0), (100.0, 100.0, 50.0))
    assert pasante_frpass(*full, 800.0) == 100.0
    assert pasante_frpass(*full, 1200.0) == 100.0
    assert pasante_frpass((1000.0, 500.0, 250.0), (0.0, 0.0, 0.0), 1200.0) == 0.0
