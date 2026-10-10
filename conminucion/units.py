"""Operaciones unitarias: cada una recibe una lista de corrientes y devuelve una tupla."""

from __future__ import annotations

from dataclasses import dataclass

from .classifier import EfficiencyCurve, SharpnessCurve
from .mill import BallMill, EnergyBallMill
from .stream import Stream


@dataclass(frozen=True)
class MillOp:
    """Molino: mezcla las entradas y las muele."""

    mill: BallMill | EnergyBallMill

    def __call__(self, ins: list[Stream]) -> tuple[Stream, ...]:
        return (self.mill(Stream.mix(ins)),)


@dataclass(frozen=True)
class ClassifierOp:
    """Hidrociclón o harnero: salidas (descarga gruesa, descarga fina)."""

    curve: EfficiencyCurve | SharpnessCurve

    def __call__(self, ins: list[Stream]) -> tuple[Stream, ...]:
        return self.curve.split(Stream.mix(ins))


@dataclass(frozen=True)
class SumpOp:
    """Cajón: mezcla y agrega agua de dilución para fijar el % de sólidos (si hay objetivo)."""

    target_pct_solids: float | None = None

    def __post_init__(self) -> None:
        if self.target_pct_solids is not None and not 0 < self.target_pct_solids < 100:
            raise ValueError("target_pct_solids debe estar en (0, 100)")

    def __call__(self, ins: list[Stream]) -> tuple[Stream, ...]:
        mixed = Stream.mix(ins)
        if self.target_pct_solids is None:
            return (mixed,)
        needed = mixed.total_solids * (100.0 - self.target_pct_solids) / self.target_pct_solids
        return (mixed.with_water(max(needed, mixed.water)),)
