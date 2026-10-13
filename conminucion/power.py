"""Potencia de un molino de bolas por la fórmula de Bond con las correcciones de Rowland.

    kW/t de bolas = 4,879 D^0,3 (3,2 - 3 J) Cs (1 - 0,1 / 2^(9 - 10 Cs)) + Ss

D: diámetro interior entre revestimientos (m); J: fracción del volumen ocupada por la carga
de bolas; Cs: fracción de la velocidad crítica. Para D > 3,3 m, el factor de tamaño de bola es
Ss = 1,102 (B - 12,5 D) / 50,8, con B el tamaño máximo de bola (mm).

La potencia del molino es esa cifra por las toneladas de bolas: J * (pi/4) D^2 L * densidad
aparente de la carga, que es la densidad del acero por (1 - huecos), con huecos = 0,4.
Fuentes: Rowland y Kjos (1980); Austin, Klimpel y Luckie (1984), p. 236; Gupta y Yan (2016).
Es potencia en el piñón y vale para cargas normales (J entre 0,3 y 0,45 aproximadamente).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MILL_TYPE_FACTORS = {"rebalse": 1.0, "parrilla_humedo": 1.16, "parrilla_seco": 1.08}
BALL_SIZE_FACTOR_MIN_DIAMETER = 3.3  # m
G = 9.80665  # m/s²


def critical_speed_rpm(diameter_m: float, ball_mm: float = 0.0) -> float:
    """Velocidad crítica (rpm): la bola en lo alto del tambor no cae porque la fuerza
    centrífuga iguala a su peso, ω² (D - d)/2 = g. Da N = 42,3/√(D - d) con D y d en m, la
    forma usual de los textos de procesamiento de minerales."""
    gap = diameter_m - ball_mm / 1000.0
    if gap <= 0:
        raise ValueError("El diámetro del molino debe ser mayor que el de la bola")
    return 60.0 / (2.0 * np.pi) * float(np.sqrt(2.0 * G / gap))


@dataclass(frozen=True)
class BallMillPower:
    """Potencia en el piñón (kW) y su desglose."""

    kw_per_t_balls: float
    balls_t: float
    kw: float


def bond_kw_per_t_balls(
    diameter_m: float,
    ball_filling: float,
    critical_speed: float,
    top_ball_mm: float | None = None,
    mill_type: str = "rebalse",
) -> float:
    """kW por tonelada de bolas (Bond-Rowland)."""
    if diameter_m <= 0 or not 0 < ball_filling < 1 or not 0 < critical_speed < 1:
        raise ValueError("Se requiere D > 0, 0 < J < 1 y 0 < Cs < 1")
    if mill_type not in MILL_TYPE_FACTORS:
        raise ValueError(
            f"Tipo de molino desconocido {mill_type!r}; use {tuple(MILL_TYPE_FACTORS)}"
        )
    speed = critical_speed * (1.0 - 0.1 / 2.0 ** (9.0 - 10.0 * critical_speed))
    kwb = 4.879 * diameter_m**0.3 * (3.2 - 3.0 * ball_filling) * speed
    if top_ball_mm is not None and diameter_m > BALL_SIZE_FACTOR_MIN_DIAMETER:
        kwb += 1.102 * (top_ball_mm - 12.5 * diameter_m) / 50.8
    return float(kwb * MILL_TYPE_FACTORS[mill_type])


def ball_charge_t(
    diameter_m: float,
    length_m: float,
    ball_filling: float,
    media_density: float = 7.8,
    voidage: float = 0.4,
) -> float:
    """Toneladas de bolas: J * volumen interior * densidad del acero * (1 - huecos)."""
    if length_m <= 0 or media_density <= 0 or not 0 <= voidage < 1:
        raise ValueError("Se requiere L > 0, densidad > 0 y 0 <= huecos < 1")
    volume = np.pi / 4.0 * diameter_m**2 * length_m
    return float(ball_filling * volume * media_density * (1.0 - voidage))


def bond_mill_power(
    diameter_m: float,
    length_m: float,
    ball_filling: float,
    critical_speed: float,
    top_ball_mm: float | None = None,
    mill_type: str = "rebalse",
    media_density: float = 7.8,
    voidage: float = 0.4,
) -> BallMillPower:
    """Potencia del molino en el piñón (kW), lista para `EnergyBallMill(power_kw=...)`."""
    kwb = bond_kw_per_t_balls(diameter_m, ball_filling, critical_speed, top_ball_mm, mill_type)
    balls = ball_charge_t(diameter_m, length_m, ball_filling, media_density, voidage)
    return BallMillPower(kwb, balls, kwb * balls)
