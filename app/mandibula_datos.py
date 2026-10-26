"""Datos y cálculo de la pestaña «Chancado primario»: la definición ÚNICA de los controles (de ella
salen los campos de la pestaña y la tabla de datos de su guía), los equipos de la Tabla 3.1 de King,
la validación en el servidor, el cálculo del circuito (parrilla + chancador de mandíbula) y los
experimentos de «Prueba esto». Los textos están en `textos_es_mandibula.py` y
`textos_en_mandibula.py` (claves `jaw.*`)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from scipy.optimize import brentq

from conminucion.datos_mandibula import (
    K_CAL,
    MU_DEFECTO,
    RHO_S_REF,
    TABLA_KING,
    WI_MANDIBULA_DEFECTO,
    MaquinaKing,
)
from conminucion.mandibula import Grizzly, JawCrusher, carrera_amit_mm, pasante_en
from conminucion.mandibula_diagnostico import Chequeo, diagnostico
from conminucion.sizes import SizeGrid, rosin_rammler
from conminucion.stream import Stream

PREFIX = "jaw_"
MM = 1000.0  # µm por mm
CLASES, RAZON = 60, 2.0**0.25  # rejilla de la alimentación: 60 clases, razón 2^(1/4)
TOP_SOBRE_BOCA = 0.75  # el equipo predefinido fija el tamaño máximo en 0,75·boca
F80_SOBRE_TOP = 0.6  # ... y el F80 en 0,6 de ese tamaño máximo
CARGA_SOBRE_TABLA = 0.9  # ... y la alimentación en 90 % de la capacidad de la tabla
MODELOS = ("nordberg", "whiten")
PERSONALIZADO = "personalizado"
OSS_COINCIDE_MM = 0.5  # el OSS «coincide» con un punto de la tabla si difiere menos de esto


@dataclass(frozen=True)
class Campo:
    """Un control numérico. Sus textos son `jaw.campo.<key>.label|meaning|source`; `source` es la
    clave de `datos_mandibula.FUENTES` o «supuesto»."""

    key: str
    group: str
    unit: str
    lo: float
    hi: float
    default: float
    step: float
    source: str

    @property
    def label_k(self) -> str:
        return f"jaw.campo.{self.key}.label"

    @property
    def meaning_k(self) -> str:
        return f"jaw.campo.{self.key}.meaning"

    @property
    def source_k(self) -> str:
        return f"jaw.src.{self.source}"


G_MAQ, G_ALIM, G_PARR = "maquina", "alimentacion", "parrilla"


def valores_de_equipo(maq: MaquinaKing, oss_mm: float) -> dict[str, float]:
    """Los valores de los controles para un equipo de la tabla de King a un OSS de la tabla:
    boca, ancho, rpm y kW de la tabla; altura = 2·boca y carrera = regla AMIT 135; CSS = OSS −
    carrera; y una alimentación coherente con el tamaño (SUPUESTOS rotulados)."""
    gape, stroke = round(maq.boca_mm, 1), round(carrera_amit_mm(maq.boca_mm), 2)
    top = TOP_SOBRE_BOCA * gape
    return {
        "gape": gape, "width": round(maq.largo_mm, 1), "height": round(2.0 * gape, 1),
        "stroke": stroke, "css": round(oss_mm - stroke, 2), "rpm": float(maq.rpm),
        "power": float(maq.kw),
        "tph": round(CARGA_SOBRE_TABLA * maq.capacidad_tph[int(oss_mm)]),
        "top": round(top), "f80": round(F80_SOBRE_TOP * top), "grz_ap": float(oss_mm),
    }  # fmt: skip


EJEMPLO_EQUIPO, EJEMPLO_OSS = "24x36", 51
POR_NOMBRE = {m.nombre: m for m in TABLA_KING}
_EJ = valores_de_equipo(POR_NOMBRE[EJEMPLO_EQUIPO], EJEMPLO_OSS)

CAMPOS: tuple[Campo, ...] = (
    Campo("gape", G_MAQ, "mm", 150, 1800, _EJ["gape"], 10, "king_tn5"),
    Campo("width", G_MAQ, "mm", 200, 2200, _EJ["width"], 10, "king_tn5"),
    Campo("height", G_MAQ, "mm", 300, 3600, _EJ["height"], 10, "amit135"),
    Campo("stroke", G_MAQ, "mm", 5, 120, _EJ["stroke"], 1, "amit135"),
    Campo("css", G_MAQ, "mm", 5, 700, _EJ["css"], 1, "king_tn5"),
    Campo("wear", G_MAQ, "mm", 0, 60, 0.0, 1, "definicion"),
    Campo("rpm", G_MAQ, "rpm", 60, 450, _EJ["rpm"], 5, "amit135"),
    Campo("mu", G_MAQ, "", 0.1, 0.6, MU_DEFECTO, 0.01, "supuesto"),
    Campo("power", G_MAQ, "kW", 5, 800, _EJ["power"], 1, "king_tn5"),
    Campo("tph", G_ALIM, "t/h", 1, 5000, _EJ["tph"], 5, "definicion"),
    Campo("rho", G_ALIM, "t/m³", 1.5, 5.0, RHO_S_REF, 0.1, "supuesto"),
    Campo("top", G_ALIM, "mm", 20, 1800, _EJ["top"], 10, "definicion"),
    Campo("f80", G_ALIM, "mm", 5, 1500, _EJ["f80"], 5, "definicion"),
    Campo("n", G_ALIM, "", 0.3, 5.0, 1.2, 0.1, "definicion"),
    Campo("wi", G_ALIM, "kWh/t", 3, 40, WI_MANDIBULA_DEFECTO, 0.5, "supuesto"),
    Campo("grz_ap", G_PARR, "mm", 5, 600, _EJ["grz_ap"], 5, "karra_king"),
    Campo("hopper", G_PARR, "t", 0, 500, 20.0, 5, "definicion"),
)
BY_KEY = {c.key: c for c in CAMPOS}
EJEMPLO = {c.key: c.default for c in CAMPOS}
EJEMPLO_PARRILLA, EJEMPLO_MODELO = True, MODELOS[0]


def valores_por_defecto() -> dict[str, object]:
    return {**EJEMPLO, "grizzly": EJEMPLO_PARRILLA, "model": EJEMPLO_MODELO}


def validar(v: dict[str, object]) -> str | None:
    """La clave del texto del primer problema de los datos, o None si están bien. Se comprueba en
    el servidor aunque los controles ya limiten el rango."""
    for c in CAMPOS:
        x = v.get(c.key)
        if isinstance(x, bool) or not isinstance(x, int | float) or not math.isfinite(x):
            return "jaw.err.numero"
        if not c.lo <= x <= c.hi:
            return "jaw.err.rango"
    if v.get("model") not in MODELOS or not isinstance(v.get("grizzly"), bool):
        return "jaw.err.numero"
    if v["gape"] <= v["css"] + v["wear"] + v["stroke"]:  # type: ignore[operator]
        return "jaw.err.boca"
    if v["f80"] >= v["top"]:  # type: ignore[operator]
        return "jaw.err.f80"
    if _x63(float(v["f80"]), float(v["top"]), float(v["n"])) is None:  # type: ignore[arg-type]
        return "jaw.err.rr"
    return None


def _x63(f80: float, top: float, n: float) -> float | None:
    """x63 de la Rosin-Rammler cuya versión truncada en `top` tiene su P80 en `f80`; None si
    esa n no lo permite (el mínimo de F(f80) es (f80/top)^n, límite x63 → ∞)."""

    def f(x63: float) -> float:
        den = -math.expm1(-((top / x63) ** n))
        if den <= 0.0:  # x63 enorme: tiende al límite (f80/top)^n
            return (f80 / top) ** n - 0.8
        return -math.expm1(-((f80 / x63) ** n)) / den - 0.8

    lo, hi = f80 / 60.0, f80 * 1e4
    return None if f(lo) * f(hi) > 0 else float(brentq(f, lo, hi))


def alimentacion(v: dict[str, object]) -> Stream:
    """Alimentación de mina: Rosin-Rammler truncada en el tamaño máximo, con P80 = F80."""
    top = float(v["top"]) * MM  # type: ignore[arg-type]
    x63 = _x63(float(v["f80"]), float(v["top"]), float(v["n"]))  # type: ignore[arg-type]
    grid = SizeGrid.geometric(top, CLASES, RAZON)
    return Stream.from_fractions(
        grid, rosin_rammler(grid, x63 * MM, float(v["n"])), float(v["tph"]), 0.0, float(v["rho"])  # type: ignore[arg-type]
    )  # fmt: skip


def maquina(v: dict[str, object]) -> JawCrusher:
    """El chancador. k = K_CAL·ρs/2,7: la densidad aparente efectiva escala con la del sólido
    (SUPUESTO; con ρs = 2,7 es exactamente K_CAL)."""
    return JawCrusher(
        float(v["gape"]), float(v["width"]), float(v["css"]), float(v["rpm"]),  # type: ignore[arg-type]
        height_mm=float(v["height"]), stroke_mm=float(v["stroke"]), wear_mm=float(v["wear"]),  # type: ignore[arg-type]
        mu=float(v["mu"]), power_kw=float(v["power"]), wi=float(v["wi"]),  # type: ignore[arg-type]
        k=K_CAL * float(v["rho"]) / RHO_S_REF, product_model=str(v["model"]),  # type: ignore[arg-type]
    )  # fmt: skip


@dataclass(frozen=True)
class Calculo:
    v: dict[str, object]
    jaw: JawCrusher
    parrilla: Grizzly | None
    mina: Stream
    pasante: Stream | None  # lo que pasa la parrilla (va directo a la correa)
    carga: Stream  # alimentación al chancador (lo retenido, o toda la mina sin parrilla)
    prod_chancador: Stream
    producto: Stream  # producto total: pasante de la parrilla + producto del chancador
    checks: list[Chequeo]

    @property
    def capacidad(self) -> float:
        return self.jaw.effective_capacity_tph(self.carga)

    @property
    def utilizacion(self) -> float:
        return self.jaw.utilization(self.carga)

    @property
    def potencia(self) -> float:
        return self.jaw.power_draw_kw(self.carga, self.prod_chancador)

    @property
    def p80(self) -> float:
        return self.producto.p80 / MM

    def nivel(self, codigo: str) -> str:
        return next(c.nivel for c in self.checks if c.codigo == codigo)

    def cierre(self) -> float:
        """Error relativo del balance de sólidos: mina contra producto total."""
        return abs(self.mina.total_solids - self.producto.total_solids) / self.mina.total_solids

    def bajo_css(self, s: Stream) -> float:
        """Fracción de la corriente bajo el CSS efectivo."""
        return pasante_en(s, self.jaw.css_eff_mm * MM) if s.total_solids > 0 else 0.0


def calcular(v: dict[str, object]) -> Calculo:
    """El circuito completo con datos ya validados. Lanza ValueError si el modelo los rechaza."""
    jaw, mina = maquina(v), alimentacion(v)
    if v["grizzly"]:
        parrilla = Grizzly(float(v["grz_ap"]))  # type: ignore[arg-type]
        pasante, carga = parrilla.split(mina)
    else:
        parrilla, pasante, carga = None, None, mina
    prod = jaw(carga)
    total = prod if pasante is None else Stream.mix([pasante, prod])
    checks = diagnostico(jaw, carga, float(v["hopper"]))  # type: ignore[arg-type]
    return Calculo(dict(v), jaw, parrilla, mina, pasante, carga, prod, total, checks)


@lru_cache(maxsize=1)
def ejemplo() -> Calculo:
    return calcular(valores_por_defecto())


def con_cambios(base: dict[str, object], **cambios: object) -> Calculo:
    return calcular({**base, **cambios})


def maquina_king(v: dict[str, object]) -> MaquinaKing | None:
    """La fila de la Tabla 3.1 cuya boca y ancho son los de los controles (o None)."""
    for m in TABLA_KING:
        if abs(m.boca_mm - float(v["gape"])) < 0.5 and abs(m.largo_mm - float(v["width"])) < 0.5:  # type: ignore[arg-type]
            return m
    return None


def punto_king(c: Calculo) -> tuple[MaquinaKing, int, float] | None:
    """(equipo, OSS de la tabla, t/h de la tabla) si el equipo es uno de la tabla y el OSS coincide
    con uno de sus puntos."""
    m = maquina_king(c.v)
    if m is None:
        return None
    for oss, q in m.capacidad_tph.items():
        if abs(oss - c.jaw.oss_mm) < OSS_COINCIDE_MM:
            return m, oss, q
    return None


# ---------------------------------------------------------------- experimentos de «Prueba esto»
@dataclass(frozen=True)
class Experimento:
    """Un cambio al estado de ejemplo. `direcciones` (magnitud → +1 sube / −1 baja) y `niveles`
    (código del chequeo → nivel nuevo) son lo que afirma su texto; las pruebas lo verifican."""

    clave: str
    cambios: dict[str, object]
    direcciones: dict[str, int]
    niveles: dict[str, str]


EXPERIMENTOS: tuple[Experimento, ...] = (
    Experimento("css", {"css": 10.0},
                {"capacidad": -1, "p80": -1, "utilizacion": +1}, {"sobrecarga": "mal"}),
    Experimento("rpm", {"rpm": 330.0},
                {"capacidad": -1, "utilizacion": +1},
                {"velocidad_critica": "aviso", "sobrecarga": "mal"}),
    Experimento("parrilla", {"grizzly": False},
                {"alimentacion": +1, "utilizacion": +1}, {"sobrecarga": "mal"}),
    Experimento("desgaste", {"wear": 25.0},
                {"capacidad": +1, "p80": +1, "utilizacion": -1},
                {"razon_reduccion": "aviso", "velocidad_critica": "aviso"}),
    Experimento("colpas", {"top": 580.0}, {"colpas": +1}, {"colpas": "aviso"}),
    Experimento("motor", {"power": 25.0, "wi": 22.0},
                {"capacidad": -1, "utilizacion": +1},
                {"potencia": "mal", "sobrecarga": "mal"}),
)  # fmt: skip
