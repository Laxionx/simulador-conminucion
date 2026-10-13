"""Los datos que alimentan las animaciones de la app salen del cálculo, no de un dibujo aparte."""

import math

import numpy as np
import pytest

from conminucion.circuits import FRESH, CircuitConfig, simulate
from conminucion.classifier import EfficiencyCurve
from conminucion.mill import AustinSelection, BallMill
from conminucion.power import critical_speed_rpm
from conminucion.sizes import SizeGrid, rosin_rammler
from conminucion.stream import Stream


def _cfg(n_mixers: int = 3) -> CircuitConfig:
    grid = SizeGrid.geometric(9500.0, 17)
    fresh = Stream.from_fractions(grid, rosin_rammler(grid, 3200.0, 1.0), 100.0, 0.0, 2.7)
    return CircuitConfig(fresh, BallMill(AustinSelection(), n_mixers=n_mixers), EfficiencyCurve())


@pytest.mark.parametrize("kind", ["cerrado_directo", "cerrado_inverso"])
@pytest.mark.parametrize("wegstein", [True, False])
def test_historia_del_reciclo_termina_en_la_carga_circulante(kind, wegstein):
    res = simulate(kind, _cfg(), wegstein=wegstein)
    history = res.solution.tear_history
    assert len(history) == res.solution.iterations
    fresh = res.streams[FRESH].total_solids
    assert history[-1] / fresh == pytest.approx(res.circulating_load, rel=1e-9)
    assert history[0] < history[-1]  # arranca vacío y se llena


def test_circuito_abierto_no_tiene_historia_de_reciclo():
    assert simulate("abierto", _cfg()).solution.tear_history == []


def test_perfiles_por_mezclador_terminan_en_la_descarga():
    cfg = _cfg(n_mixers=4)
    feed = cfg.fresh
    profiles = cfg.mill.mixer_profiles(feed.grid, feed.solids)
    assert len(profiles) == 4
    np.testing.assert_allclose(profiles[-1], cfg.mill.discharge_solids(feed.grid, feed.solids))
    for p in profiles:
        assert p.sum() == pytest.approx(feed.solids.sum())  # el molino no crea ni pierde sólidos
    finer = [float(np.cumsum(p[::-1])[-5]) for p in profiles]  # masa bajo el 5.º tamiz más fino
    assert finer == sorted(finer)  # cada mezclador muele más


def test_velocidad_critica_desde_la_fisica():
    # En la velocidad crítica, en lo alto del tambor la fuerza centrífuga iguala al peso:
    # ω² (D - d)/2 = g  ⇒  N = 60/(2π) · sqrt(2 g / (D - d)) rpm.
    for d_m, ball_mm in ((4.0, 0.0), (5.5, 75.0), (1.0, 25.0)):
        expected = 60.0 / (2 * math.pi) * math.sqrt(2 * 9.80665 / (d_m - ball_mm / 1000.0))
        assert critical_speed_rpm(d_m, ball_mm) == pytest.approx(expected, rel=1e-12)
    assert critical_speed_rpm(4.0) == pytest.approx(42.3 / 2.0, rel=2e-3)  # la forma de manual
    with pytest.raises(ValueError):
        critical_speed_rpm(0.05, 60.0)
