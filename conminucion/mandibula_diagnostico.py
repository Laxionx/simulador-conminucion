"""Diagnóstico estructurado del chancador de mandíbula (sin textos de interfaz).

Solo chequeos que tienen fuente o son una definición; cada uno devuelve un `Chequeo` con
código, nivel ("ok", "aviso", "mal"), los valores medidos y la clave de su fuente en
`datos_mandibula.FUENTES`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .datos_mandibula import (
    CARRERA_RANGO_CM,
    COLPA_FRACCION_BOCA,
    RAZON_REDUCCION_RANGO,
    RPM_RANGO,
)
from .mandibula import JawCrusher, pasante_en
from .stream import Stream

NIVELES = ("ok", "aviso", "mal")


@dataclass(frozen=True)
class Chequeo:
    codigo: str
    nivel: str
    valores: dict[str, float] = field(default_factory=dict)
    fuente: str = "definicion"


def _en_rango(x: float, rango: tuple[float, float]) -> bool:
    return rango[0] <= x <= rango[1]


def diagnostico(crusher: JawCrusher, feed: Stream, hopper_t: float = 0.0) -> list[Chequeo]:
    """Chequeos de la máquina con la alimentación dada. `hopper_t` es la tolva (t) para el
    tiempo a rebalse."""
    product = crusher(feed)
    tph = feed.total_solids
    nc = crusher.critical_rpm
    colpas = 1.0 - pasante_en(feed, COLPA_FRACCION_BOCA * crusher.gape_mm * 1000.0)
    razon = feed.f80 / product.p80
    util = crusher.utilization(feed)
    potencia = crusher.power_draw_kw(feed, product)
    carrera_cm = crusher.stroke / 10.0

    def nivel(malo: bool, gravedad: str = "aviso") -> str:
        return gravedad if malo else "ok"

    checks = [
        Chequeo(
            "no_muerde",
            nivel(not crusher.bites, "mal"),
            {"theta_deg": crusher.bite_angle_deg, "limite_deg": crusher.bite_limit_deg},
            "rose_english",
        ),
        Chequeo(
            "velocidad_critica",
            nivel(crusher.rpm > nc),
            {"rpm": crusher.rpm, "rpm_critica": nc, "factor": crusher.speed_factor},
            "king_tn5",
        ),
        Chequeo(
            "rpm_fuera_de_rango",
            nivel(not _en_rango(crusher.rpm, RPM_RANGO)),
            {"rpm": crusher.rpm, "min": RPM_RANGO[0], "max": RPM_RANGO[1]},
            "amit135",
        ),
        Chequeo(
            "carrera_fuera_de_rango",
            nivel(not _en_rango(carrera_cm, CARRERA_RANGO_CM)),
            {"carrera_cm": carrera_cm, "min": CARRERA_RANGO_CM[0], "max": CARRERA_RANGO_CM[1]},
            "amit135",
        ),
        Chequeo(
            "colpas",
            nivel(colpas > 0.0),
            {"fraccion": colpas, "tamano_um": COLPA_FRACCION_BOCA * crusher.gape_mm * 1000.0},
            "king_tn5",
        ),
        Chequeo(
            "razon_reduccion",
            nivel(not _en_rango(razon, RAZON_REDUCCION_RANGO)),
            {"razon": razon, "min": RAZON_REDUCCION_RANGO[0], "max": RAZON_REDUCCION_RANGO[1]},
            "king_tn5",
        ),
        Chequeo(
            "sobrecarga",
            nivel(util > 1.0, "mal"),
            {
                "utilizacion": util,
                "alimentacion_tph": tph,
                "capacidad_tph": crusher.effective_capacity_tph(feed),
                "minutos_a_rebalse": crusher.overflow_minutes(feed, hopper_t),
            },
            "definicion",
        ),
    ]
    if crusher.power_kw is not None:
        checks.append(
            Chequeo(
                "potencia",
                nivel(potencia > crusher.power_kw, "mal"),
                {"requerida_kw": potencia, "instalada_kw": crusher.power_kw},
                "bond_1952",
            )
        )
    return checks
