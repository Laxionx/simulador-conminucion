"""Chancador de mandíbula (capacidad cinemática, mordida, potencia, producto) y parrilla.

Geometría (mm de entrada, m internos): boca G, ancho W, altura de la cámara D (2·G por
defecto), carrera L_T (regla AMIT 135) y ajuste CSS (lado cerrado). Con el desgaste δ,
CSS_e = CSS + δ y OSS = CSS_e + L_T. Fórmulas de la referencia R (ver docs/chancado.md):

    tan θ = (G - CSS_e)/D;  muerde si θ <= 2·arctan μ
    h = L_T/tan θ;  s = ½·g·(30/N)²;  Nc = 30·√(g·tan θ/(2·L_T))
    V = W·h·(CSS_e + L_T/2);  Q = 60·N·V·f_N·k,  f_N = 1 si N <= Nc, si no (Nc/N)²

k [t/m³] es la densidad aparente efectiva (ρ_s·φ en R); aquí es un parámetro calibrable.
SUPUESTOS declarados: μ, k, la fracción de potencia en vacío y el Wi de impacto no salen de
una fuente; ver `datos_mandibula`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from .bond import bond_energy
from .chancadora import ConeCrusher
from .datos_mandibula import (
    ALTURA_SOBRE_BOCA,
    CARRERA_COEF,
    CARRERA_EXP,
    G_GRAVEDAD,
    K_REF,
    KARRA_EXPONENTE,
    KARRA_LN2,
    MU_DEFECTO,
    R_ETA_PARRILLA,
    TAGGART_RHO_B,
    VACIO_DEFECTO,
    WI_MANDIBULA_DEFECTO,
)
from .mandibula_producto import MM, nordberg_product
from .stream import Stream

MODELOS_PRODUCTO = ("whiten", "nordberg")
MODOS_PARRILLA = ("karra", "constante")


def carrera_amit_mm(gape_mm: float) -> float:
    """Carrera por la regla de AMIT 135: L_T = 0,0502·boca^0,85 (metros), devuelta en mm."""
    if gape_mm <= 0:
        raise ValueError("La boca debe ser positiva")
    return CARRERA_COEF * (gape_mm / MM) ** CARRERA_EXP * MM


def rose_english_tph(
    css_mm: float, stroke_mm: float, gape_mm: float, width_mm: float, rpm: float, k: float
) -> float:
    """Forma de baja frecuencia de Rose y English (1967): Q = 60·L_T·N·W·(2·CSS + L_T)·R/(R-1)·k,
    con R = G/CSS (Gupta y Yan 2016, cap. 4). Es la identidad de la cinemática con D = 2G."""
    if min(css_mm, stroke_mm, width_mm, rpm, k) <= 0 or gape_mm <= css_mm:
        raise ValueError("Se requieren valores positivos y boca > CSS")
    ratio = gape_mm / css_mm
    lt, css, w = stroke_mm / MM, css_mm / MM, width_mm / MM
    return 60.0 * lt * rpm * w * (2.0 * css + lt) * ratio / (ratio - 1.0) * k


def taggart_tph(width_mm: float, oss_mm: float, rho_b: float = TAGGART_RHO_B) -> float:
    """Taggart: Q = 0,093·W[cm]·OSS[cm]·(ρ_b/1,6) (t/h)."""
    if min(width_mm, oss_mm, rho_b) <= 0:
        raise ValueError("width, OSS y ρ_b deben ser positivos")
    return 0.093 * (width_mm / 10.0) * (oss_mm / 10.0) * (rho_b / TAGGART_RHO_B)


def pasante_en(feed: Stream, size_um: float) -> float:
    """Fracción de la corriente bajo size_um (interpolación log-lineal del acumulado, con un
    nodo virtual de 0 bajo el tamiz más fino, como `size_at_passing`)."""
    if size_um <= 0:
        raise ValueError("El tamaño debe ser positivo")
    s = feed.grid.sieves
    x = np.log(np.concatenate(([s[-1] * s[-1] / s[-2]], s[::-1])))
    y = np.concatenate(([0.0], feed.cumulative_passing[::-1]))
    return float(np.interp(np.log(size_um), x, y, left=0.0, right=1.0))


@dataclass(frozen=True)
class JawCrusher:
    """Chancador de mandíbula. Longitudes en mm, velocidad en rpm, potencia en kW."""

    gape_mm: float
    width_mm: float
    css_mm: float
    rpm: float
    height_mm: float | None = None  # D; por defecto 2·boca (AMIT 135)
    stroke_mm: float | None = None  # L_T; por defecto la regla AMIT 135
    wear_mm: float = 0.0  # δ
    mu: float = MU_DEFECTO  # SUPUESTO
    power_kw: float | None = None
    idle_fraction: float = VACIO_DEFECTO  # SUPUESTO: fracción de power_kw gastada en vacío
    wi: float = WI_MANDIBULA_DEFECTO  # SUPUESTO: Wi de impacto, kWh/t
    k: float = K_REF  # t/m³, densidad aparente efectiva (calibrable)
    product_model: str = "whiten"
    fines: float = 0.2  # whiten: K, n1, n2 como el cono de MODSIM
    alpha1: float = 0.653  # whiten: d1 = α1·OSS (SUPUESTO: valor del cono)
    alpha2: float = 1.6  # whiten: d2 = α2·OSS + d*
    exponent: float = 1.0
    n1: float = 0.5
    n2: float = 4.5
    d_star_mm: float = 0.0

    def __post_init__(self) -> None:
        if min(self.gape_mm, self.width_mm, self.css_mm, self.rpm, self.k, self.wi) <= 0:
            raise ValueError("boca, ancho, CSS, rpm, k y Wi deben ser positivos")
        if self.wear_mm < 0 or not 0.0 <= self.idle_fraction < 1.0:
            raise ValueError("Se requiere desgaste >= 0 y 0 <= fracción en vacío < 1")
        for name in ("height_mm", "stroke_mm", "power_kw"):
            v = getattr(self, name)
            if v is not None and v <= 0:
                raise ValueError(f"{name} debe ser positivo")
        if self.mu <= 0:
            raise ValueError("μ debe ser positivo")
        if self.product_model not in MODELOS_PRODUCTO:
            raise ValueError(f"Modelo de producto desconocido {self.product_model!r}")
        if self.gape_mm <= self.oss_mm:
            raise ValueError("La boca debe ser mayor que el OSS (geometría inválida)")
        self._cone()  # valida los parámetros de la fractura con la misma regla que el cono

    # --- geometría ---
    @property
    def stroke(self) -> float:
        """Carrera L_T efectiva (mm)."""
        return self.stroke_mm if self.stroke_mm is not None else carrera_amit_mm(self.gape_mm)

    @property
    def height(self) -> float:
        """Altura de la cámara D efectiva (mm)."""
        return self.height_mm if self.height_mm is not None else ALTURA_SOBRE_BOCA * self.gape_mm

    @property
    def css_eff_mm(self) -> float:
        return self.css_mm + self.wear_mm

    @property
    def oss_mm(self) -> float:
        return self.css_eff_mm + self.stroke

    @property
    def tan_theta(self) -> float:
        return (self.gape_mm - self.css_eff_mm) / self.height

    @property
    def bite_angle_deg(self) -> float:
        return float(np.degrees(np.arctan(self.tan_theta)))

    @property
    def bite_limit_deg(self) -> float:
        return float(np.degrees(2.0 * np.arctan(self.mu)))

    @property
    def bites(self) -> bool:
        return self.bite_angle_deg <= self.bite_limit_deg

    # --- cinemática ---
    @property
    def advance_m(self) -> float:
        """h = L_T/tan θ: avance geométrico por golpe."""
        return self.stroke / MM / self.tan_theta

    @property
    def free_fall_m(self) -> float:
        """s = ½·g·(30/N)²: caída libre en medio ciclo."""
        return 0.5 * G_GRAVEDAD * (30.0 / self.rpm) ** 2

    @property
    def critical_rpm(self) -> float:
        return 30.0 * float(np.sqrt(G_GRAVEDAD * self.tan_theta / (2.0 * self.stroke / MM)))

    @property
    def speed_factor(self) -> float:
        nc = self.critical_rpm
        return 1.0 if self.rpm <= nc else (nc / self.rpm) ** 2

    @property
    def volume_per_cycle_m3(self) -> float:
        return self.width_mm / MM * self.advance_m * (self.css_eff_mm + self.stroke / 2.0) / MM

    # --- capacidad ---
    def capacity_tph(self) -> float:
        """Capacidad volumétrica: 60·N·V·f_N·k."""
        return 60.0 * self.rpm * self.volume_per_cycle_m3 * self.speed_factor * self.k

    def taggart_tph(self, rho_b: float = TAGGART_RHO_B) -> float:
        return taggart_tph(self.width_mm, self.oss_mm, rho_b)

    @property
    def chamber_volume_m3(self) -> float:
        """Trapecio W·D·(G + CSS_e + L_T/2)/2: boca G arriba y abertura media abajo."""
        bottom = self.css_eff_mm + self.stroke / 2.0
        return self.width_mm * self.height * (self.gape_mm + bottom) / 2.0 / MM**3

    @property
    def holdup_t(self) -> float:
        """Masa retenida en la cámara llena (volumen × k)."""
        return self.chamber_volume_m3 * self.k

    @property
    def strokes_to_exit(self) -> float:
        """Golpes de una partícula: D/mín(h, s)."""
        return self.height / MM / min(self.advance_m, self.free_fall_m)

    @property
    def residence_s(self) -> float:
        return self.strokes_to_exit * 60.0 / self.rpm

    # --- producto ---
    def _cone(self) -> ConeCrusher:
        return ConeCrusher(
            self.oss_mm, self.fines, self.alpha1, self.alpha2, self.exponent,
            self.n1, self.n2, self.d_star_mm, "modsim",
        )  # fmt: skip

    def __call__(self, feed: Stream) -> Stream:
        """Producto. "whiten": ciclo de King con el ajuste = OSS; "nordberg": curva estándar."""
        if self.product_model == "nordberg":
            return nordberg_product(feed, self.oss_mm)
        return self._cone()(feed)

    def with_(self, **changes: float | str | None) -> JawCrusher:
        return replace(self, **changes)  # type: ignore[arg-type]

    # --- potencia y carga ---
    def _bond_kwh_t(self, feed: Stream, product: Stream) -> float:
        p80 = product.p80
        return bond_energy(self.wi, feed.f80, p80) if p80 < feed.f80 else 0.0

    def power_draw_kw(self, feed: Stream, product: Stream | None = None) -> float:
        """Bond (Wi de impacto) a la alimentación actual, más el vacío (fracción de power_kw)."""
        product = self(feed) if product is None else product
        vacio = self.idle_fraction * (self.power_kw or 0.0)
        return feed.total_solids * self._bond_kwh_t(feed, product) + vacio

    def motor_limit_tph(self, feed: Stream, product: Stream | None = None) -> float:
        """Alimentación que permite el motor: (1 - vacío)·kW / (kWh/t de Bond)."""
        if self.power_kw is None:
            return float("inf")
        w = self._bond_kwh_t(feed, self(feed) if product is None else product)
        return float("inf") if w <= 0 else (1.0 - self.idle_fraction) * self.power_kw / w

    def effective_capacity_tph(self, feed: Stream) -> float:
        return min(self.capacity_tph(), self.motor_limit_tph(feed))

    def utilization(self, feed: Stream) -> float:
        """Alimentación a la cámara / capacidad efectiva (mín. volumétrica y motor)."""
        return feed.total_solids / self.effective_capacity_tph(feed)

    def overflow_minutes(self, feed: Stream, hopper_t: float) -> float:
        """Minutos hasta llenar una tolva de hopper_t toneladas (inf si no hay exceso)."""
        if hopper_t < 0:
            raise ValueError("La tolva no puede ser negativa")
        excess = feed.total_solids - self.effective_capacity_tph(feed)
        return float("inf") if excess <= 0 else hopper_t / excess * 60.0


@dataclass(frozen=True)
class Grizzly:
    """Parrilla (grizzly) de abertura entre barras `aperture_mm`.

    "karra": partición c(d) = 1 - exp(-0,693·(d/d50)^5,9) a sobretamaño, con d50 = abertura
    (SUPUESTO: la abertura hace de d50). "constante": pasa eta·f(x) si x < abertura (R)."""

    aperture_mm: float
    mode: str = "karra"
    eta: float = R_ETA_PARRILLA
    sharpness: float = KARRA_EXPONENTE

    def __post_init__(self) -> None:
        if self.aperture_mm <= 0 or self.sharpness <= 0 or not 0.0 < self.eta <= 1.0:
            raise ValueError("Se requiere abertura > 0, agudeza > 0 y 0 < eta <= 1")
        if self.mode not in MODOS_PARRILLA:
            raise ValueError(f"Modo de parrilla desconocido {self.mode!r}; use {MODOS_PARRILLA}")

    def passing_fraction(self, sizes) -> NDArray[np.float64]:
        """Fracción de cada clase (tamaños en µm) que pasa por la parrilla."""
        d = np.asarray(sizes, dtype=float)
        a = self.aperture_mm * MM
        if self.mode == "constante":
            return np.where(d < a, self.eta, 0.0)
        return np.exp(-KARRA_LN2 * (d / a) ** self.sharpness)

    def split(self, feed: Stream) -> tuple[Stream, Stream]:
        """(pasante, retenido). Conserva sólidos; el agua se reparte como los sólidos."""
        p = self.passing_fraction(feed.grid.sizes)
        total = feed.total_solids
        share = float((feed.solids * p).sum() / total) if total > 0 else 0.0
        passed = Stream(feed.grid, feed.solids * p, feed.water * share, feed.rho_s)
        kept = Stream(feed.grid, feed.solids * (1.0 - p), feed.water * (1.0 - share), feed.rho_s)
        return passed, kept
