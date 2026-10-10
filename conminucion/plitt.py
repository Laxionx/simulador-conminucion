"""Hidrociclón de Plitt (1976) en la forma SI de King: modelo CYCL de MODSIM 3.6.

Predice, desde la geometría y la alimentación (largos en m, caudal por ciclón Q en m³/s, φ la
fracción volumétrica de sólidos):

    d50c = F1·85,07·Dc^0,46·Di^0,6·Do^1,21·e^(6,3φ) / (Du^0,71·h^0,38·Q^0,45)   [µm]
           × (μ/0,001)^0,35 / (ρs - ρ_pulpa)^n
    S    = F3·3,79·(Du/Do)^3,31·h^0,54·(Du² + Do²)^0,36·e^(0,54φ) / (H^0,24·Dc^1,11)
    Rv   = S/(S + 1)          (fracción del caudal de pulpa a la descarga)
    m    = F2·2,96·e^(-1,58·Rv)·(Dc²·h/Q)^0,15

La curva corregida es c(d) = 1 - exp(-0,693 (d/d50c)^m). El agua que va a la descarga es
Rf = (Rv - φ·T)/(1 - φ·T), con T la fracción de sólidos según la curva corregida, y la curva
real es c + Rf(1 - c). La constante 85,07 = 2690/√1000 es la del código de MODSIM. Las versiones
publicadas de Plitt usan otras unidades y no coinciden entre sí (ver docs/plitt.md).

Embanque (roping): Mular y Jull (1978), como en MODSIM. El ápex mínimo es
0,145 - 0,417/(2,65 - ρs + ρs/w) + 0,0279·ln(Ms/ρs), con w la fracción de sólidos de la descarga
y Ms sus sólidos por ciclón en kg/s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .stream import Stream

TPH_TO_KG_S = 1.0 / 3.6
WATER_VISCOSITY = 0.001  # Pa·s
D50_CONSTANT = 2690.0 / math.sqrt(1000.0)
LN2 = math.log(2.0)  # 0,693 en el código


@dataclass(frozen=True)
class PlittResult:
    d50c_um: float
    sharpness: float  # m
    flow_split: float  # S = caudal de pulpa a la descarga / al rebalse
    rv: float  # fracción del caudal de pulpa a la descarga
    rf: float  # fracción del agua a la descarga
    phi: float  # fracción volumétrica de sólidos en la alimentación
    q_m3_s: float  # caudal de pulpa por ciclón


@dataclass(frozen=True)
class PlittCyclone:
    """Geometría como fracción del diámetro, igual que el formulario de MODSIM; los valores por
    defecto son su geometría «estándar»."""

    diameter_m: float
    vortex_spigot: float = 3.0  # h/Dc
    inlet: float = 0.2  # Di/Dc
    vortex_finder: float = 0.167  # Do/Dc
    spigot: float = 0.116  # Du/Dc
    head_m: float = 3.0  # altura de la pulpa de alimentación
    n_cyclones: int = 1
    f_d50: float = 1.0
    f_sharpness: float = 1.0
    f_split: float = 1.0
    viscosity_pa_s: float = 0.0012
    density_exponent: float = 0.5
    slurry_density_factor: float = 0.0  # ρ_pulpa = 1 + f(ρs - 1), con 0 <= f < 1
    size_basis: str = "medio"  # "tamiz_inferior" como MODSIM

    def __post_init__(self) -> None:
        dims = (self.diameter_m, self.vortex_spigot, self.inlet, self.vortex_finder, self.spigot)
        if min(dims) <= 0 or self.head_m <= 0 or self.n_cyclones < 1:
            raise ValueError("Dimensiones, altura y número de ciclones deben ser positivos")
        if min(self.f_d50, self.f_sharpness, self.f_split, self.viscosity_pa_s) <= 0:
            raise ValueError("Los factores de calibración y la viscosidad deben ser positivos")
        if not 0.0 <= self.slurry_density_factor < 1.0:
            raise ValueError("El factor de densidad de la pulpa debe estar en [0, 1)")

    def performance(self, feed: Stream) -> PlittResult:
        dc = self.diameter_m
        h, di = self.vortex_spigot * dc, self.inlet * dc
        do, du = self.vortex_finder * dc, self.spigot * dc
        solids_m3_s = feed.total_solids * TPH_TO_KG_S / feed.rho_s / 1000.0
        q_total = feed.water * TPH_TO_KG_S / 1000.0 + solids_m3_s
        phi = solids_m3_s / q_total
        q = q_total / self.n_cyclones
        d50 = (
            self.f_d50 * D50_CONSTANT * dc**0.46 * di**0.6 * do**1.21 * math.exp(6.3 * phi)
            / (du**0.71 * h**0.38 * q**0.45)
        )  # fmt: skip
        d50 *= (self.viscosity_pa_s / WATER_VISCOSITY) ** 0.35
        rho_slurry = 1.0 + self.slurry_density_factor * (feed.rho_s - 1.0)
        d50 /= abs(feed.rho_s - rho_slurry) ** self.density_exponent
        split = (
            self.f_split * 3.79 * (du / do) ** 3.31 * h**0.54 * (du**2 + do**2) ** 0.36
            * math.exp(0.54 * phi) / (self.head_m**0.24 * dc**1.11)
        )  # fmt: skip
        rv = split / (split + 1.0)
        m = self.f_sharpness * 2.96 * math.exp(-1.58 * rv) * (dc**2 * h / q) ** 0.15
        corrected = self._corrected(feed, d50, m)
        t = float(feed.solids @ corrected) / feed.total_solids
        rf = max((rv - phi * t) / (1.0 - phi * t), 0.0)
        return PlittResult(d50, m, split, rv, rf, phi, q)

    def _corrected(self, feed: Stream, d50: float, m: float) -> NDArray[np.float64]:
        sizes = feed.grid.representative(self.size_basis)
        return 1.0 - np.exp(-LN2 * (sizes / d50) ** m)

    def split(self, feed: Stream) -> tuple[Stream, Stream]:
        """Devuelve (descarga, rebalse)."""
        result = self.performance(feed)
        c = self._corrected(feed, result.d50c_um, result.sharpness)
        actual = c + result.rf * (1.0 - c)
        coarse = Stream(feed.grid, feed.solids * actual, feed.water * result.rf, feed.rho_s)
        fine = Stream(
            feed.grid, feed.solids * (1.0 - actual), feed.water * (1.0 - result.rf), feed.rho_s
        )
        return coarse, fine

    def min_spigot_m(self, underflow: Stream) -> float:
        """Ápex mínimo para no embancar, según Mular y Jull (1978)."""
        w = underflow.total_solids / (underflow.total_solids + underflow.water)
        sg = underflow.rho_s
        per_cyclone = underflow.total_solids * TPH_TO_KG_S / self.n_cyclones
        return 0.145 - 0.417 / (2.65 - sg + sg / w) + 0.0279 * math.log(per_cyclone / sg)

    def ropes(self, underflow: Stream) -> bool:
        return self.spigot * self.diameter_m < self.min_spigot_m(underflow)
