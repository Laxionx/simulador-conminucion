"""Clasificación por curva de eficiencia (Whiten; Lynch y Rao 1975; bypass de Kelsall 1953)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

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
