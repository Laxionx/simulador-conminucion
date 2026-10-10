"""Clasificación por curva de eficiencia (Whiten; Lynch y Rao 1975; bypass de Kelsall 1953)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq

from .stream import Stream


def corrected_efficiency(x, d50c: float, alpha: float) -> NDArray[np.float64]:
    """Ec = (e^u - 1)/(e^u + e^alpha - 2), u = alpha x/d50c (forma estable, Ec(d50c)=0,5)."""
    u = alpha * np.asarray(x, dtype=float) / d50c
    decay = np.exp(-u)
    return (1.0 - decay) / (1.0 + (np.exp(alpha) - 2.0) * decay)


def actual_efficiency(x, d50c: float, alpha: float, rf: float = 0.0) -> NDArray[np.float64]:
    """Ea = Rf + (1 - Rf) Ec: fracción de cada clase que va a la descarga gruesa."""
    return rf + (1.0 - rf) * corrected_efficiency(x, d50c, alpha)


@dataclass(frozen=True)
class EfficiencyCurve:
    """Hidrociclón (gruesa = underflow) o harnero (gruesa = sobretamaño, rf ~ 0)."""

    d50c: float = 100.0  # µm
    alpha: float = 3.0
    rf: float = 0.2  # fracción del agua de alimentación a la descarga gruesa

    def __post_init__(self) -> None:
        if self.d50c <= 0 or self.alpha <= 0 or not 0.0 <= self.rf <= 1.0:
            raise ValueError("Se requiere d50c>0, alpha>0 y 0<=rf<=1")

    def efficiency(self, sizes) -> NDArray[np.float64]:
        return actual_efficiency(sizes, self.d50c, self.alpha, self.rf)

    def split(self, feed: Stream) -> tuple[Stream, Stream]:
        """Devuelve (descarga gruesa, descarga fina)."""
        ea = self.efficiency(feed.grid.sizes)
        coarse = Stream(feed.grid, feed.solids * ea, feed.water * self.rf, feed.rho_s)
        fine = Stream(feed.grid, feed.solids * (1.0 - ea), feed.water * (1.0 - self.rf), feed.rho_s)
        return coarse, fine


SHARPNESS_MODELS = ("logistico", "rosin_rammler", "suma_exponencial")
LN3 = float(np.log(3.0))


def _whiten_reduced_size(p: float, alpha: float) -> float:
    """x = d/d50c donde la curva de Whiten vale p (forma cerrada)."""
    return float(np.log((1.0 + p * (np.exp(alpha) - 2.0)) / (1.0 - p)) / alpha)


def whiten_alpha_from_sharpness(si: float) -> float:
    """alpha de Whiten cuyo índice de nitidez d25/d75 vale si."""
    return float(
        brentq(
            lambda a: _whiten_reduced_size(0.25, a) / _whiten_reduced_size(0.75, a) - si,
            1e-4,
            60.0,
            xtol=1e-12,
        )
    )


@dataclass(frozen=True)
class SharpnessCurve:
    """Clasificador empírico de Austin, Klimpel y Luckie (1984, p. 305); modelo CYCA de MODSIM.

    La curva corregida se fija con d50c y el índice de nitidez SI = d25/d75 (0 a 1). El bypass
    manda esa fracción de sólidos y de agua a la descarga gruesa. El d50c dado es para densidad
    rho_ref y se escala como ((rho_ref - 1)/(rho_s - 1))^n (n = 0,5 Stokes, 1 Newton).
    """

    d50c: float  # µm, para densidad rho_ref
    sharpness: float
    bypass: float = 0.0
    model: str = "logistico"
    density_exponent: float = 0.5
    rho_ref: float = 2.67
    size_basis: str = "medio"  # o "tamiz_superior", como MODSIM

    def __post_init__(self) -> None:
        if self.d50c <= 0 or not 0.0 < self.sharpness < 1.0 or not 0.0 <= self.bypass < 1.0:
            raise ValueError("Se requiere d50c>0, 0<SI<1 y 0<=bypass<1")
        if self.model not in SHARPNESS_MODELS:
            raise ValueError(f"Modelo desconocido {self.model!r}; use uno de {SHARPNESS_MODELS}")
        if self.rho_ref <= 1.0:
            raise ValueError("rho_ref debe ser mayor que la del agua")

    def d50_for(self, rho_s: float) -> float:
        return self.d50c * ((self.rho_ref - 1.0) / (rho_s - 1.0)) ** self.density_exponent

    def corrected(self, sizes, rho_s: float = 2.67) -> NDArray[np.float64]:
        x = np.asarray(sizes, dtype=float) / self.d50_for(rho_s)
        si = self.sharpness
        if self.model == "logistico":
            lam = -2.0 * LN3 / np.log(si)
            return 1.0 / (1.0 + x ** (-lam))
        if self.model == "rosin_rammler":
            m = np.log(np.log(4.0 / 3.0) / np.log(4.0)) / np.log(si)
            return 1.0 - np.exp(-np.log(2.0) * x**m)
        return corrected_efficiency(x, 1.0, whiten_alpha_from_sharpness(si))

    def efficiency(self, sizes, rho_s: float = 2.67) -> NDArray[np.float64]:
        return self.bypass + (1.0 - self.bypass) * self.corrected(sizes, rho_s)

    def split(self, feed: Stream) -> tuple[Stream, Stream]:
        """Devuelve (descarga gruesa, descarga fina)."""
        ea = self.efficiency(feed.grid.representative(self.size_basis), feed.rho_s)
        coarse = Stream(feed.grid, feed.solids * ea, feed.water * self.bypass, feed.rho_s)
        fine = Stream(
            feed.grid, feed.solids * (1.0 - ea), feed.water * (1.0 - self.bypass), feed.rho_s
        )
        return coarse, fine
