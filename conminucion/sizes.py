"""Clases de tamaño, interpolación de pasantes y generadores de alimentación."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

SQRT2 = float(np.sqrt(2.0))


@dataclass(frozen=True, eq=False)
class SizeGrid:
    """Tamices s_1 > ... > s_n (µm). Clase k = [s_{k+1}, s_k); la última es el fondo [0, s_n)."""

    sieves: NDArray[np.float64]

    def __post_init__(self) -> None:
        s = np.array(self.sieves, dtype=float)
        if s.ndim != 1 or len(s) < 3:
            raise ValueError("Se necesitan al menos 3 tamices")
        if np.any(s <= 0) or np.any(np.diff(s) >= 0):
            raise ValueError("Los tamices deben ser positivos y estrictamente decrecientes")
        s.setflags(write=False)
        object.__setattr__(self, "sieves", s)

    @classmethod
    def geometric(cls, top: float = 9500.0, n: int = 17, ratio: float = SQRT2) -> SizeGrid:
        """Serie geométrica de razón `ratio` (√2 por defecto)."""
        return cls(top / ratio ** np.arange(n))

    @property
    def n(self) -> int:
        return len(self.sieves)

    def representative(self, basis: str = "medio") -> NDArray[np.float64]:
        """Tamaño de cada clase: "medio" (media geométrica) o "tamiz_superior" (convención de
        MODSIM para clasificadores y selección; el fondo usa s_n)."""
        if basis == "medio":
            return self.sizes
        if basis == "tamiz_superior":
            return self.sieves
        raise ValueError(f"Base de tamaño desconocida {basis!r}; use 'medio' o 'tamiz_superior'")

    @property
    def sizes(self) -> NDArray[np.float64]:
        """Tamaño representativo: media geométrica de los límites (fondo: s_n/√2)."""
        s = self.sieves
        return np.append(np.sqrt(s[:-1] * s[1:]), s[-1] / SQRT2)


def cumulative_passing(mass: NDArray[np.float64]) -> NDArray[np.float64]:
    """Fracción pasante en cada tamiz s_k = suma de las clases k..n (relativa al total)."""
    total = mass.sum()
    if total <= 0:
        return np.full(len(mass), np.nan)
    return np.cumsum(mass[::-1])[::-1] / total


def size_at_passing(grid: SizeGrid, mass: NDArray[np.float64], p: float) -> float:
    """Tamaño (µm) al que pasa la fracción p, con interpolación log-lineal del pasante."""
    if not 0.0 < p < 1.0:
        raise ValueError("p debe estar en (0, 1)")
    cum = cumulative_passing(np.asarray(mass, dtype=float))
    if np.isnan(cum[0]):
        return float("nan")
    s = grid.sieves
    # Nodos ascendentes en tamaño; bajo el fondo se extrapola con un nodo virtual de P = 0
    x = np.log(np.concatenate(([s[-1] * s[-1] / s[-2]], s[::-1])))
    pc = np.concatenate(([0.0], cum[::-1]))
    idx = int(np.searchsorted(pc, p, side="left"))
    idx = min(max(idx, 1), len(pc) - 1)
    p0, p1 = pc[idx - 1], pc[idx]
    if p1 == p0:
        return float(np.exp(x[idx]))
    return float(np.exp(x[idx - 1] + (p - p0) / (p1 - p0) * (x[idx] - x[idx - 1])))


def _from_cumulative(
    grid: SizeGrid, cdf: Callable[[NDArray[np.float64]], NDArray[np.float64]]
) -> NDArray[np.float64]:
    """Fracciones por clase desde un pasante acumulado, truncado en el tamiz superior."""
    cum = np.asarray(cdf(grid.sieves), dtype=float)
    mass = cum - np.append(cum[1:], 0.0)
    return mass / cum[0]


def rosin_rammler(grid: SizeGrid, x63: float, m: float) -> NDArray[np.float64]:
    """Fracciones por clase de P(x) = 1 - exp(-(x/x63)^m), renormalizada sobre s_1."""
    if x63 <= 0 or m <= 0:
        raise ValueError("x63 y m deben ser positivos")
    return _from_cumulative(grid, lambda x: 1.0 - np.exp(-((x / x63) ** m)))


def gaudin_schuhmann(grid: SizeGrid, k: float, alpha: float) -> NDArray[np.float64]:
    """Fracciones por clase de P(x) = min(1, (x/k)^alpha), renormalizada sobre s_1."""
    if k <= 0 or alpha <= 0:
        raise ValueError("k y alpha deben ser positivos")
    return _from_cumulative(grid, lambda x: np.minimum(1.0, (x / k) ** alpha))
