"""Molino de bolas de mezcla perfecta (Whiten 1974; Napier-Munn et al. 1996)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from .fracture import Fracture
from .sizes import SizeGrid
from .stream import Stream


@dataclass(frozen=True)
class KnotSelection:
    """(r/d) por nudos (tamaño µm, valor): interpolación lineal de ln(r/d) vs ln(tamaño)."""

    sizes: tuple[float, ...]
    rd: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.sizes) != len(self.rd) or len(self.sizes) < 1:
            raise ValueError("sizes y rd deben tener igual longitud (>=1)")
        if min(self.sizes) <= 0 or min(self.rd) <= 0:
            raise ValueError("Tamaños y r/d deben ser positivos")

    def rd_vector(self, grid: SizeGrid) -> NDArray[np.float64]:
        order = np.argsort(self.sizes)
        xs = np.log(np.asarray(self.sizes, dtype=float)[order])
        ys = np.log(np.asarray(self.rd, dtype=float)[order])
        rd = np.exp(np.interp(np.log(grid.sizes), xs, ys))  # extrapolación constante
        rd[-1] = 0.0
        return rd


@dataclass(frozen=True)
class AustinSelection:
    """S_i = A (x/1000)^alpha / (1 + (x/mu)^Lambda) [1/min]; (r/d)_i = S_i tau."""

    A: float = 0.8
    alpha: float = 0.9
    mu: float = 2500.0
    lam: float = 3.0
    tau: float = 3.0  # min

    def __post_init__(self) -> None:
        if min(self.A, self.alpha, self.mu, self.lam, self.tau) <= 0:
            raise ValueError("Todos los parámetros de Austin deben ser positivos")

    def selection(self, grid: SizeGrid) -> NDArray[np.float64]:
        x = grid.sizes
        return self.A * (x / 1000.0) ** self.alpha / (1.0 + (x / self.mu) ** self.lam)

    def rd_vector(self, grid: SizeGrid) -> NDArray[np.float64]:
        rd = self.selection(grid) * self.tau
        rd[-1] = 0.0
        return rd


def solve_mixer(f: NDArray, rd: NDArray, a: NDArray) -> NDArray:
    """p_i = [f_i + sum_{j<i} rd_j a_ij p_j] / (1 + rd_i), de la clase gruesa a la fina."""
    p = np.zeros(len(f), dtype=float)
    for i in range(len(f)):
        p[i] = (f[i] + (a[i, :i] * rd[:i]) @ p[:i]) / (1.0 + rd[i])
    return p


@dataclass(frozen=True)
class BallMill:
    selection: KnotSelection | AustinSelection = field(default_factory=AustinSelection)
    fracture: Fracture = field(default_factory=Fracture)
    n_mixers: int = 1
    added_water: float = 0.0  # t/h

    def __post_init__(self) -> None:
        if self.n_mixers < 1 or self.added_water < 0:
            raise ValueError("n_mixers>=1 y added_water>=0")

    def discharge_solids(self, grid: SizeGrid, feed: NDArray) -> NDArray[np.float64]:
        """N mezcladores en serie, cada uno con (r/d)/N (equivale a tau/N)."""
        rd = self.selection.rd_vector(grid) / self.n_mixers
        a = self.fracture.appearance(grid)
        p = np.asarray(feed, dtype=float)
        for _ in range(self.n_mixers):
            p = solve_mixer(p, rd, a)
        return p

    def __call__(self, feed: Stream) -> Stream:
        p = self.discharge_solids(feed.grid, feed.solids)
        return Stream(feed.grid, p, feed.water + self.added_water, feed.rho_s)
