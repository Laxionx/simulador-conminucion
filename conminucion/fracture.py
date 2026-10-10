"""Función de fractura de Austin, Klimpel y Luckie (1984), forma acumulada normalizada."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .sizes import SizeGrid


@dataclass(frozen=True)
class Fracture:
    """B(x; y) = phi (x/y)^gamma + (1-phi) (x/y)^beta: fracción de los fragmentos de una
    partícula de tamaño y que queda bajo x.

    `parent_size` fija el tamaño de la partícula madre de cada clase:
    - "tamiz_superior" (por defecto): y = tamiz superior; los fragmentos que quedarían en la
      misma clase se reparten de nuevo (normalización por B(s_j+1|s_j)).
    - "tamiz_inferior": y = límite inferior, como MODSIM (King 2001); todos los fragmentos caen
      en clases más finas y no hace falta normalizar.
    """

    phi: float = 0.6
    gamma: float = 0.8
    beta: float = 3.5
    parent_size: str = "tamiz_superior"

    def __post_init__(self) -> None:
        if not 0.0 <= self.phi <= 1.0 or self.gamma <= 0 or self.beta <= 0:
            raise ValueError("Se requiere 0<=phi<=1, gamma>0 y beta>0")
        if self.parent_size not in ("tamiz_superior", "tamiz_inferior"):
            raise ValueError("parent_size debe ser 'tamiz_superior' o 'tamiz_inferior'")

    def cumulative(self, ratio) -> NDArray[np.float64]:
        r = np.asarray(ratio, dtype=float)
        return self.phi * r**self.gamma + (1 - self.phi) * r**self.beta

    def appearance(self, grid: SizeGrid) -> NDArray[np.float64]:
        """Matriz a[k, j] (k fila, j columna); cada columna j<n-1 suma 1; el fondo no fractura."""
        if self.parent_size == "tamiz_inferior":
            return self._appearance_lower(grid)
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

    def _appearance_lower(self, grid: SizeGrid) -> NDArray[np.float64]:
        """a[k, j] = B(s_k / s_j+1) - B(s_k+1 / s_j+1), con s_j+1 el límite inferior de la clase
        madre y B(0) = 0 para el fondo."""
        n, s = grid.n, grid.sieves
        a = np.zeros((n, n))
        for j in range(n - 1):
            parent = s[j + 1]
            upper = self.cumulative(s[j + 1 :] / parent)
            lower = np.append(upper[1:], 0.0)
            a[j + 1 :, j] = upper - lower
        return a
