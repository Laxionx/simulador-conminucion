"""Presets de circuito: molino abierto, cerrado directo y cerrado inverso."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .bond import bond_energy
from .classifier import EfficiencyCurve, SharpnessCurve
from .flowsheet import Flowsheet, Solution, Unit
from .mill import BallMill, EnergyBallMill
from .stream import Stream
from .units import ClassifierOp, MillOp, SumpOp

KINDS = ("abierto", "cerrado_directo", "cerrado_inverso")
FRESH = "alimentacion_fresca"


@dataclass(frozen=True)
class CircuitConfig:
    fresh: Stream
    mill: BallMill | EnergyBallMill
    classifier: EfficiencyCurve | SharpnessCurve
    cyclone_feed_pct_solids: float = 45.0
    bond_wi: float = 14.0  # kWh/t


@dataclass
class CircuitResult:
    kind: str
    solution: Solution
    product: str
    circulating_load: float | None
    bond_kwh_t: float
    balance: dict[str, float]

    @property
    def streams(self) -> dict[str, Stream]:
        return self.solution.streams

    def table(self) -> pd.DataFrame:
        rows = [
            {
                "corriente": name,
                "solidos_t_h": s.total_solids,
                "agua_t_h": s.water,
                "pct_solidos": s.pct_solids,
                "P80_um": s.p80,
            }
            for name, s in self.streams.items()
        ]
        return pd.DataFrame(rows)

    def passing_table(self) -> pd.DataFrame:
        """Pasante acumulado (%) por tamiz y corriente."""
        any_stream = next(iter(self.streams.values()))
        data = {"tamiz_um": any_stream.grid.sieves}
        data.update({n: 100 * s.cumulative_passing for n, s in self.streams.items()})
        return pd.DataFrame(data)


def build_flowsheet(kind: str, cfg: CircuitConfig) -> Flowsheet:
    feeds = {FRESH: cfg.fresh}
    mill, cls = MillOp(cfg.mill), ClassifierOp(cfg.classifier)
    sump = SumpOp(cfg.cyclone_feed_pct_solids)
    if kind == "abierto":
        return Flowsheet([Unit("molino", (FRESH,), ("producto",), mill)], feeds)
    if kind == "cerrado_directo":
        units = [
            Unit("mezcla", (FRESH, "underflow"), ("alim_molino",), SumpOp()),
            Unit("molino", ("alim_molino",), ("descarga_molino",), mill),
            Unit("cajon", ("descarga_molino",), ("alim_ciclon",), sump),
            Unit("ciclon", ("alim_ciclon",), ("underflow", "overflow"), cls),
        ]
        return Flowsheet(units, feeds, tears=["underflow"])
    if kind == "cerrado_inverso":
        units = [
            Unit("cajon", (FRESH, "descarga_molino"), ("alim_ciclon",), sump),
            Unit("ciclon", ("alim_ciclon",), ("underflow", "overflow"), cls),
            Unit("molino", ("underflow",), ("descarga_molino",), mill),
        ]
        return Flowsheet(units, feeds, tears=["descarga_molino"])
    raise ValueError(f"Preset desconocido: {kind}. Opciones: {KINDS}")


def simulate(kind: str, cfg: CircuitConfig, wegstein: bool = False, **solver_kw) -> CircuitResult:
    sol = build_flowsheet(kind, cfg).solve(wegstein=wegstein, **solver_kw)
    product = "producto" if kind == "abierto" else "overflow"
    s = sol.streams
    fresh, prod = s[FRESH], s[product]
    circ = None if kind == "abierto" else s["underflow"].total_solids / fresh.total_solids
    balance = {
        "solidos_in": fresh.total_solids,
        "solidos_out": prod.total_solids,
        "error_solidos": fresh.total_solids - prod.total_solids,
        "agua_in": fresh.water,
        "agua_out": prod.water,
        "agua_agregada": prod.water - fresh.water,
    }
    wi = bond_energy(cfg.bond_wi, fresh.p80, prod.p80)
    return CircuitResult(kind, sol, product, circ, wi, balance)
