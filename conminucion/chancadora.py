"""Chancadora de cono: clasificación interna y fractura de Whiten (1973), en la forma de King
(2001, Technical Notes 5).

En cada ciclo una fracción c_i de la clase i queda retenida y se rompe; el resto sale. Por clase,
de la más gruesa a la más fina:

    M m_i / W = (p_i^F + Σ_{j<i} c_j (M m_j / W) b_ij) / (1 - c_i b_ii)
    producto_i = (1 - c_i) M m_i / W

Clasificación interna: c(d) = 0 bajo d1 = α1·CSS, 1 sobre d2 = α2·CSS + d*, y
1 - ((d - d2)/(d1 - d2))^n entre ambos. Fractura: B(x; y) = K (x/y)^n1 + (1 - K)(x/y)^n2,
con K la fracción de finos.

Dos convenciones para el tamaño de cada clase (los tamaños de la grilla van en µm):
- "modsim": como CRSHMODS.FOR de MODSIM 3.6. c se evalúa en el límite inferior de la clase, la
  madre se rompe desde su límite inferior y B se evalúa en los tamaños medios de las clases hijas.
- "literal": las notas de King tal cual. c y la madre van en el tamaño medio, y B en los límites.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from .sizes import SizeGrid
from .stream import Stream

CONVENCIONES = ("modsim", "literal")
MM = 1000.0  # µm por mm


def resolver_ciclo(solids, b, c) -> NDArray[np.float64]:
    """Producto (t/h) del ciclo clasificación-fractura, de la clase más gruesa a la más fina.

    `b` es la matriz de fractura (b[i, j] = fracción de la madre j que cae en la clase i) y `c`
    la fracción de cada clase que queda retenida y se rompe en cada ciclo."""
    held = np.zeros(len(c))  # M m_i (en t/h de alimentación)
    for i in range(len(c)):
        inflow = solids[i] + b[i, :i] @ (c[:i] * held[:i])
        held[i] = inflow / (1.0 - c[i] * b[i, i])
    return (1.0 - c) * held


@dataclass(frozen=True)
class ConeCrusher:
    """Chancadora de cono. Por defecto, la estándar de MODSIM (CRSH)."""

    css_mm: float
    fines: float = 0.2  # K: fracción de finos de la fractura
    alpha1: float = 0.653  # d1 = α1·CSS
    alpha2: float = 1.6  # d2 = α2·CSS + d*
    exponent: float = 1.0  # n de la clasificación interna
    n1: float = 0.5
    n2: float = 4.5
    d_star_mm: float = 0.0
    convention: str = "modsim"

    def __post_init__(self) -> None:
        if self.css_mm <= 0 or not 0.0 <= self.fines <= 1.0:
            raise ValueError("Se requiere CSS > 0 y 0 <= fracción de finos <= 1")
        if not 0 < self.alpha1 < self.alpha2 or self.exponent <= 0 or self.d_star_mm < 0:
            raise ValueError("Se requiere 0 < α1 < α2, exponente > 0 y d* >= 0")
        if self.n1 <= 0 or self.n2 <= 0:
            raise ValueError("Los exponentes de la fractura deben ser positivos")
        if self.convention not in CONVENCIONES:
            raise ValueError(f"Convención desconocida {self.convention!r}; use {CONVENCIONES}")

    @classmethod
    def standard(cls, css_mm: float, **kwargs: float | str) -> ConeCrusher:
        """Cono estándar, valores por defecto de MODSIM (CRSH)."""
        return cls(css_mm, **kwargs)  # type: ignore[arg-type]

    @classmethod
    def short_head(cls, css_mm: float, **kwargs: float | str) -> ConeCrusher:
        """Cono de cabeza corta, valores por defecto de MODSIM (SHHD, según Karra 1982)."""
        defaults: dict[str, float | str] = {
            "alpha2": 2.0, "exponent": 2.0, "n1": 0.518, "n2": 2.475, "d_star_mm": 4.826
        }  # fmt: skip
        return cls(css_mm, **(defaults | kwargs))  # type: ignore[arg-type]

    def with_convention(self, convention: str) -> ConeCrusher:
        return replace(self, convention=convention)

    def classification(self, sizes) -> NDArray[np.float64]:
        """c(d), con d en µm."""
        d = np.asarray(sizes, dtype=float)
        d1 = self.alpha1 * self.css_mm * MM
        d2 = (self.alpha2 * self.css_mm + self.d_star_mm) * MM
        mid = 1.0 - np.clip((d - d2) / (d1 - d2), 0.0, 1.0) ** self.exponent
        return np.where(d < d1, 0.0, np.where(d >= d2, 1.0, mid))

    def _cumulative(self, ratio) -> NDArray[np.float64]:
        r = np.asarray(ratio, dtype=float)
        return self.fines * r**self.n1 + (1.0 - self.fines) * r**self.n2

    def breakage(self, grid: SizeGrid) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """(b, c): b[i, j] fracción de la madre j que cae en la clase i (b[j, j] = la que se
        queda en su clase; cada columna suma 1) y c, la clasificación de cada clase."""
        lower = grid.representative("tamiz_inferior")
        middle = np.sqrt(grid.sieves * lower)
        if self.convention == "modsim":  # B entre los medios de la clase hija y de la siguiente
            parent, top, bottom = lower, middle, np.append(middle[1:], 0.0)
        else:  # B entre los límites de la clase hija; el fondo llega a 0
            parent, top, bottom = middle, grid.sieves, np.append(lower[:-1], 0.0)
        ratio_top = top[:, None] / parent[None, :]
        ratio_bottom = bottom[:, None] / parent[None, :]
        b = np.tril(self._cumulative(ratio_top) - self._cumulative(ratio_bottom), k=-1)
        np.fill_diagonal(b, 1.0 - self._cumulative(bottom / parent))
        return b, self.classification(parent)

    def __call__(self, feed: Stream) -> Stream:
        b, c = self.breakage(feed.grid)
        return Stream(feed.grid, resolver_ciclo(feed.solids, b, c), feed.water, feed.rho_s)
