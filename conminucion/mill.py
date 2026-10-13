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

    def mixer_profiles(self, grid: SizeGrid, feed: NDArray) -> list[NDArray[np.float64]]:
        """Sólidos (t/h por clase) a la salida de cada mezclador; el último es la descarga."""
        rd = self.selection.rd_vector(grid) / self.n_mixers
        a = self.fracture.appearance(grid)
        p = np.asarray(feed, dtype=float)
        profiles = []
        for _ in range(self.n_mixers):
            p = solve_mixer(p, rd, a)
            profiles.append(p)
        return profiles

    def discharge_solids(self, grid: SizeGrid, feed: NDArray) -> NDArray[np.float64]:
        """N mezcladores en serie, cada uno con (r/d)/N (equivale a tau/N)."""
        return self.mixer_profiles(grid, feed)[-1]

    def __call__(self, feed: Stream) -> Stream:
        p = self.discharge_solids(feed.grid, feed.solids)
        return Stream(feed.grid, p, feed.water + self.added_water, feed.rho_s)


@dataclass(frozen=True)
class EnergySelection:
    """Selección específica de energía de Herbst y Fuerstenau (1980), en t/kWh:
    ln(S^E / S^E_1) = zeta1 ln d + zeta2 (ln d)^2, con d en mm (tamaño medio de la clase)."""

    s1e: float  # S^E a 1 mm, t/kWh
    zeta1: float = 0.0
    zeta2: float = 0.0
    size_basis: str = "medio"  # o "tamiz_superior", como MODSIM

    def __post_init__(self) -> None:
        if self.s1e <= 0:
            raise ValueError("s1e debe ser positivo")

    def specific(self, grid: SizeGrid) -> NDArray[np.float64]:
        ln_d = np.log(grid.representative(self.size_basis) / 1000.0)
        se = self.s1e * np.exp(self.zeta1 * ln_d + self.zeta2 * ln_d**2)
        se[-1] = 0.0  # el fondo no fractura
        return se


@dataclass(frozen=True)
class EnergyBallMill:
    """Molino de bolas con escalamiento por potencia (modelo HFSU de MODSIM; King 2001, 5.9).

    En cada región de mezcla perfecta, (r/d)_i = S^E_i * P / W * fracción de tiempo, con P la
    potencia neta (kW) y W los sólidos que entran (t/h): no hace falta el tiempo de residencia.
    """

    selection: EnergySelection
    fracture: Fracture = field(default_factory=Fracture)
    power_kw: float = 1000.0
    region_fractions: tuple[float, ...] = (1.0,)
    discharge_pct_solids: float | None = None  # agua que se agrega para fijar la descarga

    def __post_init__(self) -> None:
        fr = self.region_fractions
        if self.power_kw <= 0 or not fr or min(fr) < 0 or abs(sum(fr) - 1.0) > 1e-9:
            raise ValueError("power_kw>0 y fracciones de región >=0 que sumen 1")
        if self.discharge_pct_solids is not None and not 0 < self.discharge_pct_solids < 100:
            raise ValueError("discharge_pct_solids debe estar en (0, 100)")

    def discharge_solids(self, grid: SizeGrid, feed: NDArray) -> NDArray[np.float64]:
        p = np.asarray(feed, dtype=float)
        if p.sum() <= 0:
            return p
        specific_energy = self.power_kw / p.sum()  # kWh/t
        se, a = self.selection.specific(grid), self.fracture.appearance(grid)
        for fraction in self.region_fractions:
            if fraction > 0:
                p = solve_mixer(p, se * specific_energy * fraction, a)
        return p

    def __call__(self, feed: Stream) -> Stream:
        p = self.discharge_solids(feed.grid, feed.solids)
        water = feed.water
        if self.discharge_pct_solids is not None:
            x = self.discharge_pct_solids
            water = max(water, p.sum() * (100.0 - x) / x)
        return Stream(feed.grid, p, water, feed.rho_s)
