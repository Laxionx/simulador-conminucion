"""Desgaste de medios de molienda: carga estacionaria («sazonada») y consumo de acero.

Ley de desgaste: una bola de diámetro d pierde masa a razón proporcional a d^Δ
(Austin, Klimpel y Luckie 1984). Como su masa va con d³, el diámetro baja como
dd/dt = -k d^(Δ-2). Casos clásicos:
- Δ = 3, «volumen» (Davis 1919): la bola pierde masa en proporción a su peso;
- Δ = 2, «superficie» o desgaste lineal (Prentice 1943; Bond 1958): dd/dt constante.

En estado estacionario, el número de bolas en cada diámetro es el caudal de recarga por el
tiempo que pasan en él, así que la masa acumulada bajo d es proporcional a d^(6-Δ):
d³ con Δ = 3, d⁴ con Δ = 2, y la curva empírica de Bond, (d/D)^3,8, equivale a Δ = 2,2.

Consumo: correlaciones de Bond (1964) con el índice de abrasión Ai, en lb/kWh pasadas a kg/kWh.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

LB_TO_KG = 0.45359237
STEEL_DENSITY = 7800.0  # kg/m3

# Bond (1964): (coeficiente lb/kWh, resta a Ai, exponente). Formas publicadas en lb/kWh.
BOND_WEAR = {
    "barras_molino_barras": (0.35, 0.020, 0.20),
    "revestimiento_molino_barras": (0.035, 0.015, 0.30),
    "bolas_molino_bolas_humedo": (0.35, 0.015, 0.33),
    "revestimiento_molino_bolas_humedo": (0.026, 0.015, 0.30),
    "bolas_molino_bolas_seco": (0.05, 0.0, 0.5),
    "revestimiento_molino_bolas_seco": (0.005, 0.0, 0.5),
}


def bond_wear_kg_per_kwh(ai: float, element: str = "bolas_molino_bolas_humedo") -> float:
    """Consumo de acero según Bond (1964), en kg por kWh de molienda. Ai en gramos.

    Varias operaciones reportan consumos reales cercanos a la mitad de esta predicción
    (ver docs/desgaste.md): úsese como cota de diseño, no como dato de planta."""
    if element == "revestimiento_chancadoras":
        return (ai + 0.22) / 11.0 * LB_TO_KG
    if element == "rodillos_chancadora":
        return (0.1 * ai) ** 0.667 * LB_TO_KG
    if element not in BOND_WEAR:
        options = (*BOND_WEAR, "revestimiento_chancadoras", "rodillos_chancadora")
        raise ValueError(f"Elemento desconocido {element!r}; use uno de {options}")
    coefficient, offset, exponent = BOND_WEAR[element]
    if ai <= offset:
        raise ValueError(f"Ai debe ser mayor que {offset} g para {element}")
    return coefficient * (ai - offset) ** exponent * LB_TO_KG


def _check_law(exponent: float) -> None:
    if not 0.0 < exponent < 6.0:
        raise ValueError("El exponente de desgaste debe estar entre 0 y 6")


def _mass_integral(a: float, b: float, exponent: float) -> float:
    """∫ d^(5-Δ) dd entre a y b: masa (sin constantes) de las bolas de diámetro en [a, b]."""
    p = 6.0 - exponent
    return (b**p - a**p) / p


def seasoned_charge(
    sieves_mm: Sequence[float],
    makeup: Mapping[float, float],
    discard_mm: float = 0.0,
    exponent: float = 2.0,
) -> NDArray[np.float64]:
    """Fracción en masa de la carga estacionaria en cada intervalo [s_k+1, s_k).

    `makeup`: diámetro de recarga (mm) -> fracción EN MASA de la recarga. Las bolas salen del
    molino al llegar a `discard_mm` (0 = se gastan del todo). Los tamices van de mayor a menor;
    la última clase es [0, s_n)."""
    _check_law(exponent)
    s = np.asarray(sieves_mm, dtype=float)
    if s.ndim != 1 or len(s) < 1 or np.any(np.diff(s) >= 0) or np.any(s <= 0):
        raise ValueError("Los tamices deben ser positivos y estrictamente decrecientes")
    total = sum(makeup.values())
    if not makeup or total <= 0 or min(makeup.values()) < 0 or min(makeup) <= discard_mm:
        raise ValueError("La recarga necesita fracciones positivas y tamaños sobre el descarte")
    if max(makeup) > s[0] + 1e-9:
        raise ValueError("El tamiz superior debe cubrir la bola de recarga más grande")
    upper = s
    lower = np.append(s[1:], 0.0)
    mass = np.zeros(len(s))
    for size, fraction in makeup.items():
        rate = fraction / total / size**3  # número de bolas por unidad de masa recargada
        for k, (hi, lo) in enumerate(zip(upper, lower, strict=True)):
            a, b = max(lo, discard_mm), min(hi, size)
            if b > a:
                mass[k] += rate * _mass_integral(a, b, exponent)
    return mass / mass.sum()


def cohort_charge(
    sieves_mm: Sequence[float],
    makeup_mm: float,
    discard_mm: float = 0.0,
    exponent: float = 2.0,
    cohorts: int = 200_000,
) -> NDArray[np.float64]:
    """Control numérico independiente: sigue cohortes de bolas recargadas a intervalos iguales
    de tiempo, con la solución de dd/dt = -k d^(Δ-2), y suma su masa por intervalo."""
    _check_law(exponent)
    s = np.asarray(sieves_mm, dtype=float)
    q = 3.0 - exponent
    if abs(q) < 1e-12:
        life = np.log(makeup_mm / max(discard_mm, makeup_mm * 1e-9))
        ages = (np.arange(cohorts) + 0.5) / cohorts * life
        d = makeup_mm * np.exp(-ages)
    else:
        life = (makeup_mm**q - discard_mm**q) / q
        ages = (np.arange(cohorts) + 0.5) / cohorts * life
        d = np.clip(makeup_mm**q - q * ages, 0.0, None) ** (1.0 / q)
    index = np.searchsorted(-s, -d, side="right") - 1  # clase [s_k+1, s_k)
    index = np.clip(index, 0, len(s) - 1)
    mass = np.bincount(index, weights=d**3, minlength=len(s))
    return mass / mass.sum()


@dataclass(frozen=True)
class ChargeBalance:
    """Balance de la carga de bolas en estado estacionario."""

    wear_constant: float  # k en mm^(3-Δ)/h
    balls_per_hour: float  # bolas recargadas por hora
    discard_kg_h: float  # acero que sale como bolas descartadas
    worn_kg_h: float  # acero que se gasta y sale con la pulpa
    ball_life_h: float  # vida de una bola de la recarga más grande, de D al descarte
    balls_in_charge: float | None  # número de bolas en el molino (None si diverge)


def charge_balance(
    charge_t: float,
    makeup_kg_h: float,
    makeup: Mapping[float, float],
    discard_mm: float = 0.0,
    exponent: float = 2.0,
    density: float = STEEL_DENSITY,
) -> ChargeBalance:
    """Con la masa de la carga y la recarga (kg/h), deduce la velocidad de desgaste y el
    resto del balance. Masa de una bola: densidad · π d³/6 (d en m)."""
    _check_law(exponent)
    if charge_t <= 0 or makeup_kg_h <= 0:
        raise ValueError("La carga y la recarga deben ser positivas")
    total = sum(makeup.values())

    def ball_kg(d_mm: float) -> float:
        return density * np.pi / 6.0 * (d_mm / 1000.0) ** 3

    rates = {d: makeup_kg_h * f / total / ball_kg(d) for d, f in makeup.items()}  # bolas/h
    mass_integral = sum(q * _mass_integral(discard_mm, d, exponent) for d, q in rates.items())
    k = density * np.pi / 6.0 * 1e-9 * mass_integral / (charge_t * 1000.0)
    q3 = 3.0 - exponent
    if abs(q3) < 1e-12:
        count = (
            None
            if discard_mm == 0
            else sum(q / k * np.log(d / discard_mm) for d, q in rates.items())
        )
        life = None if discard_mm == 0 else np.log(max(makeup) / discard_mm) / k
    else:
        diverges = q3 < 0 and discard_mm == 0
        count = (
            None
            if diverges
            else sum(q / k * (d**q3 - discard_mm**q3) / q3 for d, q in rates.items())
        )
        life = None if diverges else (max(makeup) ** q3 - discard_mm**q3) / (q3 * k)
    discard = sum(rates.values()) * ball_kg(discard_mm)
    return ChargeBalance(
        float(k),
        float(sum(rates.values())),
        float(discard),
        float(makeup_kg_h - discard),
        float("inf") if life is None else float(life),
        None if count is None else float(count),
    )


def fit_wear_exponent(
    sieves_mm: Sequence[float],
    makeup: Mapping[float, float],
    measured_pct: Sequence[float],
    discard_mm: float = 0.0,
    bounds: tuple[float, float] = (1.0, 4.5),
) -> tuple[float, float]:
    """Exponente Δ que mejor reproduce una carga tamizada en planta (mínimos cuadrados).
    Devuelve (Δ, error cuadrático medio en puntos de %)."""
    from scipy.optimize import minimize_scalar

    target = np.asarray(measured_pct, dtype=float)

    def sse(exponent: float) -> float:
        model = 100.0 * seasoned_charge(sieves_mm, makeup, discard_mm, exponent)
        return float(np.sum((model - target) ** 2))

    best = minimize_scalar(sse, bounds=bounds, method="bounded", options={"xatol": 1e-6})
    return float(best.x), float(np.sqrt(best.fun / len(target)))
