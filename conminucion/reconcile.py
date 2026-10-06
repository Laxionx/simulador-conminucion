"""Reconciliación de balance en un nodo (alimentación = underflow + overflow) por clase.

Se minimiza la suma ponderada (x_aj - x_med)^2 / sigma^2 sobre las tres granulometrías
(fracciones másicas) sujeta a: f_i = R u_i + (1-R) o_i para cada clase y suma 1 en cada corriente.
Para un R dado el problema es lineal con solución cerrada (multiplicadores de Lagrange);
R (fracción de sólidos al underflow) se obtiene minimizando el objetivo con un buscador escalar.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize_scalar


@dataclass(frozen=True)
class Reconciliation:
    r_underflow: float  # fracción de los sólidos de la alimentación que va al underflow
    feed: NDArray[np.float64]
    underflow: NDArray[np.float64]
    overflow: NDArray[np.float64]
    chi2: float
    circulating_load: float  # sólidos underflow / sólidos overflow (= / alimentación fresca)

    def partition(self, min_feed_fraction: float = 0.005) -> NDArray[np.float64]:
        """Eficiencia real por clase R u_i / f_i (NaN donde la alimentación es casi nula)."""
        with np.errstate(divide="ignore", invalid="ignore"):
            ea = self.r_underflow * self.underflow / self.feed
        return np.where(self.feed >= min_feed_fraction, ea, np.nan)


def _constraints(r: float, n: int) -> tuple[NDArray, NDArray]:
    """A x = b con x = (f, u, o)."""
    a_cls = np.hstack([np.eye(n), -r * np.eye(n), -(1 - r) * np.eye(n)])
    a_sum = np.zeros((3, 3 * n))
    for k in range(3):
        a_sum[k, k * n : (k + 1) * n] = 1.0
    return np.vstack([a_cls, a_sum]), np.concatenate([np.zeros(n), np.ones(3)])


def _solve_for_r(r: float, meas: NDArray, var: NDArray) -> tuple[NDArray, float]:
    """Solución para R fijo; lo que sale negativo se fija en 0 y se resuelve de nuevo."""
    n = len(meas) // 3
    a, b = _constraints(r, n)
    m, v = meas.copy(), var.copy()
    for _ in range(3 * n):
        wa = a * v
        lam = np.linalg.pinv(wa @ a.T) @ (a @ m - b)
        x = m - wa.T @ lam
        neg = x < -1e-12
        if not neg.any():
            break
        m[neg], v[neg] = 0.0, 1e-24  # fija en cero (cota de no negatividad)
    x = np.clip(x, 0.0, None)
    return x, float(np.sum((x - meas) ** 2 / var))


def reconcile_node(
    feed: NDArray,
    underflow: NDArray,
    overflow: NDArray,
    rel_sigma: float = 0.05,
    abs_sigma: float = 0.002,
) -> Reconciliation:
    """Ajusta las tres granulometrías medidas y estima R; sigma_i = max(rel*x, abs)."""
    meas = np.concatenate([feed, underflow, overflow]).astype(float)
    n = len(feed)
    if len(underflow) != n or len(overflow) != n:
        raise ValueError("Las tres granulometrías deben tener igual número de clases")
    sigma = np.maximum(rel_sigma * np.abs(meas), abs_sigma)
    var = sigma**2
    res = minimize_scalar(
        lambda r: _solve_for_r(r, meas, var)[1],
        bounds=(1e-6, 1 - 1e-6),
        method="bounded",
        options={"xatol": 1e-12},
    )
    r = float(res.x)
    x, chi2 = _solve_for_r(r, meas, var)
    return Reconciliation(r, x[:n], x[n : 2 * n], x[2 * n :], chi2, r / (1.0 - r))
