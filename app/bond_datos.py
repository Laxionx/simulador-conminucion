"""Datos del «Ensayo de Bond»: la definición ÚNICA de los controles de la calculadora (de ella salen
los campos de la pestaña y la tabla «datos que necesita» de su ficha), su validación en el servidor
y el caso de Hebei (Liang et al., 2016) que precarga la calculadora y alimenta la simulación.
Los textos están en `textos_es_bond.py` y `textos_en_bond.py` (claves `bond.*`)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd
from carga import Columna

from conminucion.ensayo_bond import (
    MOLINO_DIAMETRO_M,
    MOLINO_RPM,
    Alimentacion,
    EnsayoSimulado,
    ResultadoBond,
    ajustar_a_alpha,
    alimentacion_dos_puntos,
    contabilidad,
    simular_ensayo,
)
from conminucion.fracture import Fracture
from conminucion.mill import AustinSelection
from conminucion.power import ball_charge_t, critical_speed_rpm

PREFIX = "bond_"
TABLE_KEY = PREFIX + "tabla"
MAX_CICLOS, MIN_CICLOS = 30, 1
FINOS_MAX = 5000.0  # g
CORTE_PCT = 10.0  # la simulación «acierta» si queda a ±10 % de lo medido
# Molino de Bond (GMG 2021): 305 x 305 mm, 285 bolas de 20,125 kg, la mayor de 36,8 mm.
MOLINO_LARGO_M, BOLAS_N, BOLAS_KG, BOLA_MAX_MM = 0.305, 285, 20.125, 36.8

# Hebei oriental, magnetita (Liang, Wei, Xu, Xia y Li, 2016, Minerals 6(2), 39), Tablas 2 y 3.
HEBEI_FINOS = (583.9, 464.5, 379.6, 406.8, 409.0, 383.2, 397.9, 398.1, 394.2, 390.8, 382.5)
HEBEI_GBP_FINAL, HEBEI_WI = 2.5811, 10.93


@dataclass(frozen=True)
class Campo:
    key: str
    unit: str
    lo: float
    hi: float
    default: float
    step: float
    integer: bool = False

    @property
    def label_k(self) -> str:
        return f"bond.campo.{self.key}.label"

    @property
    def meaning_k(self) -> str:
        return f"bond.campo.{self.key}.meaning"

    @property
    def source_k(self) -> str:
        return f"bond.campo.{self.key}.source"


CAMPOS: tuple[Campo, ...] = (
    Campo("carga", "g", 100, 5000, 1365.0, 0.1),
    Campo("finos_carga", "g", 0, 5000, 414.8, 0.1),
    Campo("rev1", "", 1, 2000, 100, 1, integer=True),
    Campo("tamiz", "µm", 45, 4750, 150.0, 1.0),
    Campo("f80", "µm", 50, 20000, 1450.0, 10.0),
    Campo("p80", "µm", 10, 4000, 119.6, 0.1),
)
BY_KEY = {c.key: c for c in CAMPOS}
# La columna de la tabla de ciclos: la misma definición lee el CSV/XLSX y escribe la plantilla.
COLUMNAS_CICLOS = (Columna("finos", "Finos totales (g)", "Total fines (g)"),)
Valores = dict[str, float]


def valores_por_defecto() -> Valores:
    return {c.key: c.default for c in CAMPOS}


def tabla_inicial() -> pd.DataFrame:
    return pd.DataFrame({"finos": list(HEBEI_FINOS)})


def _finito(x: object) -> bool:
    return isinstance(x, int | float) and not isinstance(x, bool) and math.isfinite(x)


def validar(valores: Valores, finos: list) -> str | None:
    """La clave del texto del primer problema de los datos, o None si están bien. Se vuelve a
    comprobar en el servidor aunque los controles ya limiten el rango: un cliente puede mandar
    cualquier valor."""
    for c in CAMPOS:
        v = valores.get(c.key)
        if not _finito(v):
            return "bond.err.numero"
        if not c.lo <= v <= c.hi or (c.integer and not float(v).is_integer()):
            return "bond.err.rango"
    if not MIN_CICLOS <= len(finos) <= MAX_CICLOS:
        return "bond.err.filas"
    if not all(_finito(x) for x in finos):
        return "bond.err.vacio"
    if not all(0 <= x <= min(FINOS_MAX, valores["carga"]) for x in finos):
        return "bond.err.finos"
    if not valores["finos_carga"] < valores["carga"]:
        return "bond.err.carga"
    if not valores["p80"] < valores["tamiz"] < valores["f80"]:
        return "bond.err.tamaños"
    return None


def calcular(valores: Valores, finos: list[float]) -> ResultadoBond | None:
    """La contabilidad del ensayo con datos ya validados; None si los datos no cuadran (un ciclo
    sin finos nuevos)."""
    try:
        return contabilidad(
            valores["carga"], valores["finos_carga"], finos, int(valores["rev1"]),
            valores["tamiz"], valores["f80"], valores["p80"],
        )  # fmt: skip
    except ValueError:
        return None


@dataclass(frozen=True)
class CasoHebei:
    medido: ResultadoBond
    simulado: EnsayoSimulado
    seleccion: AustinSelection
    alimentacion: Alimentacion
    llenado: float  # fracción del volumen del molino ocupada por las bolas
    rpm_critica: float


def llenado_bolas() -> float:
    """Fracción del volumen del molino que ocupa la carga de bolas: 20,125 kg de acero con la
    densidad (7,8 t/m³) y los huecos (0,4) que usa el repo en `ball_charge_t`."""
    lleno_t = ball_charge_t(MOLINO_DIAMETRO_M, MOLINO_LARGO_M, 1.0)
    return BOLAS_KG / 1000.0 / lleno_t


def caso_hebei() -> CasoHebei:
    """El ensayo medido y su simulación: se ajustan solo A y α de Austin a los finos nuevos de los
    ciclos 1 y 2 con las revoluciones publicadas (100 y 126), y se predicen los 11 ciclos."""
    v = valores_por_defecto()
    medido = contabilidad(v["carga"], v["finos_carga"], HEBEI_FINOS, int(v["rev1"]), v["tamiz"],
                          v["f80"], v["p80"])  # fmt: skip
    alim = alimentacion_dos_puntos(v["tamiz"], v["f80"], v["finos_carga"] / v["carga"])
    fractura = Fracture()
    nuevos = (medido.ciclos[0].finos_nuevos_g, medido.ciclos[1].finos_nuevos_g)
    revs = (medido.ciclos[0].revoluciones, medido.ciclos[1].revoluciones)
    sel = ajustar_a_alpha(alim, fractura, v["carga"], nuevos, revs)
    sim = simular_ensayo(
        alim, sel, fractura, v["carga"], len(HEBEI_FINOS), int(v["rev1"]), v["f80"]
    )
    return CasoHebei(medido, sim, sel, alim, llenado_bolas(),
                     critical_speed_rpm(MOLINO_DIAMETRO_M, BOLA_MAX_MM))  # fmt: skip


def velocidad_critica_frac(rpm_critica: float) -> float:
    """Los 70 rpm del molino de Bond como fracción de su velocidad crítica."""
    return MOLINO_RPM / rpm_critica
