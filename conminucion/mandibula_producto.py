"""Producto del chancador de mandíbula: curva estándar de Nordberg y modelo de referencia R.

Los tamaños de las corrientes van en µm; los parámetros del chancador, en mm.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .chancadora import resolver_ciclo
from .datos_mandibula import (
    NORDBERG_FINO,
    NORDBERG_GRUESO,
    NORDBERG_R_CORTE,
    R_K1,
    R_K2,
    R_K3,
)
from .stream import Stream

MM = 1000.0  # µm por mm


def nordberg_cumulative(r) -> NDArray[np.float64]:
    """Fracción acumulada pasante P(x) = 1 - exp(-(r/k)^n), r = x/OSS (Nordberg, 1976)."""
    r = np.asarray(r, dtype=float)
    if np.any(r < 0):
        raise ValueError("r = x/OSS no puede ser negativo")
    n = np.where(r <= NORDBERG_R_CORTE, NORDBERG_FINO[0], NORDBERG_GRUESO[0])
    k = np.where(r <= NORDBERG_R_CORTE, NORDBERG_FINO[1], NORDBERG_GRUESO[1])
    return 1.0 - np.exp(-((r / k) ** n))


def nordberg_p80_over_oss() -> float:
    """P80/OSS de la curva estándar (rama gruesa, r > 0,4073)."""
    n, k = NORDBERG_GRUESO
    return float(k * np.log(5.0) ** (1.0 / n))


def nordberg_product(feed: Stream, oss_mm: float) -> Stream:
    """Producto de la curva de Nordberg evaluada en la media geométrica de cada clase, sin
    permitir un producto más grueso que la alimentación (acumulado ≥ el de la alimentación en
    cada clase; se desacumula). Conserva la masa de sólidos."""
    if oss_mm <= 0:
        raise ValueError("OSS debe ser positivo")
    total = feed.total_solids
    if total <= 0:
        return feed
    cum = np.maximum(nordberg_cumulative(feed.grid.sizes / (oss_mm * MM)), feed.cumulative_passing)
    mass = np.clip(cum - np.append(cum[1:], 0.0), 0.0, None)
    return Stream(feed.grid, mass / mass.sum() * total, feed.water, feed.rho_s)


def referencia_clasificacion(sizes, css_eff_mm: float, oss_mm: float) -> NDArray[np.float64]:
    """C(x) de la referencia R: 0 bajo K1·CSS_e, 1 sobre K2·OSS y 1 - ((K2-x)/(K2-K1))^K3
    entre ambos (x en µm)."""
    x = np.asarray(sizes, dtype=float)
    k1, k2 = R_K1 * css_eff_mm * MM, R_K2 * oss_mm * MM
    if k2 <= k1:
        raise ValueError("Se requiere K2·OSS > K1·CSS_e")
    mid = 1.0 - np.clip((k2 - x) / (k2 - k1), 0.0, 1.0) ** R_K3
    return np.where(x <= k1, 0.0, np.where(x >= k2, 1.0, mid))


def broadbent_callcott(ratio) -> NDArray[np.float64]:
    """B(x, y) = (1 - e^(-x/y))/(1 - e^(-1)), acotada a 1 para x >= y."""
    r = np.asarray(ratio, dtype=float)
    return np.minimum((1.0 - np.exp(-r)) / (1.0 - np.exp(-1.0)), 1.0)


def referencia_producto(feed: Stream, css_eff_mm: float, oss_mm: float) -> Stream:
    """Producto de la referencia R: x = f + B·C·x, p = (I - C)·x, con B de Broadbent-Callcott
    por clase (límites de la clase hija sobre el tamaño medio de la madre)."""
    grid = feed.grid
    parent = grid.sizes
    top, bottom = grid.sieves, np.append(grid.sieves[1:], 0.0)
    b = np.tril(
        broadbent_callcott(top[:, None] / parent[None, :])
        - broadbent_callcott(bottom[:, None] / parent[None, :]),
        k=-1,
    )
    np.fill_diagonal(b, 1.0 - broadbent_callcott(bottom / parent))
    c = referencia_clasificacion(parent, css_eff_mm, oss_mm)
    return Stream(grid, resolver_ciclo(feed.solids, b, c), feed.water, feed.rho_s)
