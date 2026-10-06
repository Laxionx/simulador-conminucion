"""Corriente de proceso: sólidos por clase (t/h), agua (t/h) y densidad de sólidos."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .sizes import SizeGrid, cumulative_passing, size_at_passing

NEG_TOL = 1e-9


@dataclass(frozen=True, eq=False)
class Stream:
    grid: SizeGrid
    solids: NDArray[np.float64]  # t/h por clase
    water: float = 0.0  # t/h
    rho_s: float = 2.7  # t/m3

    def __post_init__(self) -> None:
        s = np.array(self.solids, dtype=float)
        if s.shape != (self.grid.n,):
            raise ValueError("solids debe tener una entrada por clase")
        if np.any(s < -NEG_TOL) or self.water < -NEG_TOL:
            raise ValueError("Flujos negativos")
        if self.rho_s <= 0:
            raise ValueError("rho_s debe ser positiva")
        s = np.clip(s, 0.0, None)
        s.setflags(write=False)
        object.__setattr__(self, "solids", s)
        object.__setattr__(self, "water", max(float(self.water), 0.0))

    @classmethod
    def from_fractions(
        cls, grid: SizeGrid, fractions, tph: float, water: float = 0.0, rho_s: float = 2.7
    ) -> Stream:
        f = np.asarray(fractions, dtype=float)
        return cls(grid, f / f.sum() * tph, water, rho_s)

    @classmethod
    def empty(cls, grid: SizeGrid, rho_s: float = 2.7) -> Stream:
        return cls(grid, np.zeros(grid.n), 0.0, rho_s)

    @classmethod
    def mix(cls, streams: Sequence[Stream]) -> Stream:
        """Suma de corrientes (densidad de sólidos ponderada por volumen)."""
        first = streams[0]
        solids = np.sum([s.solids for s in streams], axis=0)
        water = float(sum(s.water for s in streams))
        vol = sum(s.total_solids / s.rho_s for s in streams)
        rho = solids.sum() / vol if vol > 0 else first.rho_s
        return cls(first.grid, solids, water, rho)

    @property
    def total_solids(self) -> float:
        return float(self.solids.sum())

    @property
    def total_mass(self) -> float:
        return self.total_solids + self.water

    @property
    def pct_solids(self) -> float:
        m = self.total_mass
        return 100.0 * self.total_solids / m if m > 0 else 0.0

    @property
    def volume_flow(self) -> float:
        """Caudal de pulpa (m3/h)."""
        return self.total_solids / self.rho_s + self.water

    @property
    def fractions(self) -> NDArray[np.float64]:
        t = self.total_solids
        return self.solids / t if t > 0 else np.zeros(self.grid.n)

    @property
    def cumulative_passing(self) -> NDArray[np.float64]:
        return cumulative_passing(self.solids)

    def size_at(self, p: float) -> float:
        return size_at_passing(self.grid, self.solids, p)

    @property
    def p80(self) -> float:
        return self.size_at(0.8)

    @property
    def f80(self) -> float:
        """Alias: F80 es el P80 de la alimentación."""
        return self.p80

    def with_water(self, water: float) -> Stream:
        return Stream(self.grid, self.solids, water, self.rho_s)

    def scaled(self, factor: float) -> Stream:
        return Stream(self.grid, self.solids * factor, self.water * factor, self.rho_s)
