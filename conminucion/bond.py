"""Energía específica de Bond (1952)."""

from __future__ import annotations

import numpy as np


def bond_energy(wi: float, f80: float, p80: float) -> float:
    """W (kWh/t) = 10 Wi (1/sqrt(P80) - 1/sqrt(F80)), con F80 y P80 en µm."""
    if wi <= 0 or f80 <= 0 or p80 <= 0:
        raise ValueError("wi, f80 y p80 deben ser positivos")
    return float(10.0 * wi * (1.0 / np.sqrt(p80) - 1.0 / np.sqrt(f80)))
