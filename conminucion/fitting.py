"""Ajuste de parámetros con scipy.optimize.least_squares e IC al 95 % por covarianza del jacobiano.

IC: cov = s^2 (J^T J)^-1 con s^2 = SSR/(m-p); intervalo theta +/- t_{0,975; m-p} * se.
Es una aproximación lineal (asintótica); cerca de una cota (p. ej. Rf = 0) es optimista.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats
from scipy.optimize import least_squares

from .classifier import actual_efficiency
from .fracture import Fracture
from .mill import BallMill, KnotSelection
from .sizes import SizeGrid


@dataclass(frozen=True)
class FitResult:
    names: tuple[str, ...]
    values: NDArray[np.float64]
    ci_low: NDArray[np.float64]
    ci_high: NDArray[np.float64]
    rmse: float
    dof: int

    def as_dict(self) -> dict[str, tuple[float, float, float]]:
        return {
            n: (float(v), float(lo), float(hi))
            for n, v, lo, hi in zip(self.names, self.values, self.ci_low, self.ci_high, strict=True)
        }

    def contains(self, truth: Sequence[float]) -> list[bool]:
        t = np.asarray(truth, dtype=float)
        return list((self.ci_low <= t) & (t <= self.ci_high))


def _jacobian_ci(sol, m: int) -> tuple[NDArray, NDArray, int]:
    """Error estándar y semiancho t del IC 95 % desde el jacobiano de la solución."""
    p = len(sol.x)
    dof = m - p
    if dof <= 0:
        raise ValueError("Faltan datos: observaciones <= parámetros")
    s2 = 2.0 * sol.cost / dof
    cov = s2 * np.linalg.pinv(sol.jac.T @ sol.jac)
    se = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    return se, stats.t.ppf(0.975, dof) * se, dof


def fit_cyclone_partition(
    sizes: NDArray, partition: NDArray, sigma: NDArray | None = None
) -> FitResult:
    """Ajusta (d50c, alpha, Rf) a una curva de partición real medida (a la descarga gruesa)."""
    x, y = np.asarray(sizes, float), np.asarray(partition, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    w = np.ones_like(y) if sigma is None else 1.0 / np.asarray(sigma, float)[ok]
    mid = 0.5 * (y.min() + y.max())
    d0 = float(np.exp(np.interp(mid, y[np.argsort(y)], np.log(x[np.argsort(y)]))))

    def resid(th: NDArray) -> NDArray:
        return (actual_efficiency(x, th[0], th[1], th[2]) - y) * w

    sol = least_squares(
        resid,
        x0=[d0, 3.0, min(max(y.min(), 0.0), 0.9)],
        bounds=([1e-3, 0.1, 0.0], [1e7, 30.0, 1.0]),
        x_scale="jac",
    )
    se, half, dof = _jacobian_ci(sol, len(y))
    lo, hi = sol.x - half, sol.x + half
    lo[2], hi[2] = max(lo[2], 0.0), min(hi[2], 1.0)  # Rf es una fracción
    rmse = float(np.sqrt(np.mean(resid(sol.x) ** 2)))
    return FitResult(("d50c", "alpha", "Rf"), sol.x, lo, hi, rmse, dof)


def fit_mill_knots(
    grid: SizeGrid,
    feed: NDArray,
    discharge: NDArray,
    knot_sizes: Sequence[float],
    fracture: Fracture | None = None,
    n_mixers: int = 1,
) -> FitResult:
    """Ajusta los r/d de los nudos (parámetro ln r/d) a la alimentación y descarga medidas."""
    frac = fracture or Fracture()
    f = np.asarray(feed, float) / np.sum(feed)
    p = np.asarray(discharge, float) / np.sum(discharge)
    sizes = tuple(float(s) for s in knot_sizes)

    def model(theta: NDArray) -> NDArray:
        mill = BallMill(KnotSelection(sizes, tuple(np.exp(theta))), frac, n_mixers)
        return mill.discharge_solids(grid, f)

    sol = least_squares(
        lambda th: model(th) - p,
        x0=np.zeros(len(sizes)),
        bounds=(-8.0, 5.0),
        x_scale="jac",
    )
    se, half, dof = _jacobian_ci(sol, len(p) - 1)  # la suma de p es 1: una clase redundante
    names = tuple(f"rd@{s:g}um" for s in sizes)
    rmse = float(np.sqrt(np.mean((model(sol.x) - p) ** 2)))
    return FitResult(names, np.exp(sol.x), np.exp(sol.x - half), np.exp(sol.x + half), rmse, dof)
