"""Muestreo de planta sintético: parámetros conocidos + ruido gaussiano."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .classifier import EfficiencyCurve
from .mill import BallMill
from .sizes import SizeGrid
from .stream import Stream


@dataclass(frozen=True)
class CycloneSurvey:
    """Tres granulometrías medidas (fracciones másicas) y la verdad conocida."""

    feed: NDArray[np.float64]
    underflow: NDArray[np.float64]
    overflow: NDArray[np.float64]
    true_r: float
    true_feed: NDArray[np.float64]
    true_curve: EfficiencyCurve


def _noisy(x: NDArray, rel: float, abs_sd: float, rng: np.random.Generator) -> NDArray:
    """Ruido gaussiano multiplicativo + piso absoluto (sin renormalizar)."""
    sd = np.sqrt((rel * x) ** 2 + abs_sd**2)
    return np.clip(x + rng.normal(0.0, 1.0, len(x)) * sd, 0.0, None)


def synthetic_cyclone_survey(
    feed: Stream,
    curve: EfficiencyCurve,
    rel_noise: float = 0.05,
    abs_noise: float = 0.002,
    seed: int | None = 0,
) -> CycloneSurvey:
    rng = np.random.default_rng(seed)
    uf, of = curve.split(feed)
    r = uf.total_solids / feed.total_solids
    return CycloneSurvey(
        _noisy(feed.fractions, rel_noise, abs_noise, rng),
        _noisy(uf.fractions, rel_noise, abs_noise, rng),
        _noisy(of.fractions, rel_noise, abs_noise, rng),
        r,
        feed.fractions,
        curve,
    )


def synthetic_partition_curve(
    grid: SizeGrid, curve: EfficiencyCurve, sigma: float = 0.02, seed: int | None = 0
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Curva de partición real con ruido gaussiano absoluto `sigma` (tamaños, eficiencia)."""
    rng = np.random.default_rng(seed)
    ea = curve.efficiency(grid.sizes)
    return grid.sizes.copy(), ea + rng.normal(0.0, sigma, grid.n)


def synthetic_mill_survey(
    grid: SizeGrid,
    feed_fractions: NDArray,
    mill: BallMill,
    abs_noise: float = 0.002,
    rel_noise: float = 0.03,
    seed: int | None = 0,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Alimentación y descarga de molino medidas (fracciones másicas con ruido)."""
    rng = np.random.default_rng(seed)
    p = mill.discharge_solids(grid, feed_fractions)
    return (
        _noisy(np.asarray(feed_fractions, float), rel_noise, abs_noise, rng),
        _noisy(p, rel_noise, abs_noise, rng),
    )
