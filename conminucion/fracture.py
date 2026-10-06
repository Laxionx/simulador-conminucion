"""Función de fractura de Austin, Klimpel y Luckie (1984), forma acumulada normalizada."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .sizes import SizeGrid


@dataclass(frozen=True)
class Fracture:
    """B(k|j) = phi (s_k/s_j)^gamma + (1-phi) (s_k/s_j)^beta para k > j."""

    phi: float = 0.6
    gamma: float = 0.8
    beta: float = 3.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.phi <= 1.0 or self.gamma <= 0 or self.beta <= 0:
            raise ValueError("Se requiere 0<=phi<=1, gamma>0 y beta>0")

    def appearance(self, grid: SizeGrid) -> NDArray[np.float64]:
        """Matriz a[k, j] (k fila, j columna); cada columna j<n-1 suma 1; el fondo no fractura."""
        n = grid.n
        s = grid.sieves
        ratio = s[:, None] / s[None, :]
        below = np.arange(n)[:, None] > np.arange(n)[None, :]
        b = self.phi * ratio**self.gamma + (1 - self.phi) * ratio**self.beta
        cum = np.vstack([np.where(below, b, 0.0), np.zeros((1, n))])  # B(n+1|j) := 0
        a = np.where(below, cum[:-1] - cum[1:], 0.0)
        denom = cum[np.arange(1, n), np.arange(n - 1)]  # B(j+1|j)
        a[:, : n - 1] /= denom
        a[:, n - 1] = 0.0
        return a
