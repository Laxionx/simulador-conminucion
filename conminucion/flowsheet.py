"""Solucionador secuencial-modular con corrientes de corte (sustitución sucesiva / Wegstein)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np

from .stream import Stream


class ConvergenceError(RuntimeError):
    """El reciclo no convergió dentro del máximo de iteraciones."""


@dataclass(frozen=True)
class Unit:
    name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    op: Callable[[list[Stream]], tuple[Stream, ...]]


@dataclass
class Solution:
    streams: dict[str, Stream]
    iterations: int
    converged: bool
    residuals: list[float] = field(default_factory=list)
    # Sólidos (t/h) en las corrientes de corte que produce cada iteración: muestra cómo se
    # llena el reciclo hasta converger. Vacía si no hay reciclo.
    tear_history: list[float] = field(default_factory=list)


class Flowsheet:
    def __init__(
        self,
        units: Sequence[Unit],
        feeds: Mapping[str, Stream],
        tears: Sequence[str] = (),
    ) -> None:
        self.units = list(units)
        self.feeds = dict(feeds)
        self.tears = list(tears)
        produced = [o for u in self.units for o in u.outputs]
        if len(set(produced)) != len(produced) or set(produced) & set(self.feeds):
            raise ValueError("Cada corriente debe tener un único origen")
        unknown = set(self.tears) - set(produced)
        if unknown:
            raise ValueError(f"Corrientes de corte que ninguna unidad produce: {sorted(unknown)}")
        known = set(produced) | set(self.feeds)
        for u in self.units:
            missing = set(u.inputs) - known
            if missing:
                raise ValueError(
                    f"La unidad {u.name} usa corrientes inexistentes: {sorted(missing)}"
                )
        self.order = self._topological_order()
        ref = next(iter(self.feeds.values()))
        self._grid, self._rho = ref.grid, ref.rho_s

    def _topological_order(self) -> list[Unit]:
        available = set(self.feeds) | set(self.tears)
        pending, order = list(self.units), []
        while pending:
            ready = [u for u in pending if set(u.inputs) <= available]
            if not ready:
                names = [u.name for u in pending]
                raise ValueError(f"Ciclo sin corriente de corte; unidades atascadas: {names}")
            for u in ready:
                order.append(u)
                pending.remove(u)
                available |= {o for o in u.outputs if o not in self.tears}
        return order

    # --- codificación de las corrientes de corte como vector ---
    def _encode(self, streams: Mapping[str, Stream]) -> np.ndarray:
        return np.concatenate([np.append(streams[t].solids, streams[t].water) for t in self.tears])

    def _decode(self, x: np.ndarray) -> dict[str, Stream]:
        m = self._grid.n + 1
        return {
            t: Stream(self._grid, x[i * m : i * m + m - 1], x[i * m + m - 1], self._rho)
            for i, t in enumerate(self.tears)
        }

    def _pass(self, x: np.ndarray) -> tuple[dict[str, Stream], dict[str, Stream]]:
        streams: dict[str, Stream] = dict(self.feeds)
        streams.update(self._decode(x))
        produced: dict[str, Stream] = {}
        for u in self.order:
            outs = u.op([streams[n] for n in u.inputs])
            for name, s in zip(u.outputs, outs, strict=True):
                if name in self.tears:
                    produced[name] = s
                else:
                    streams[name] = s
        return streams, produced

    def solve(
        self,
        tear_guess: Mapping[str, Stream] | None = None,
        wegstein: bool = False,
        tol: float = 1e-9,
        max_iter: int = 500,
    ) -> Solution:
        if not self.tears:
            streams, _ = self._pass(np.zeros(0))
            return Solution(streams, 1, True, [0.0])
        guess = {t: Stream.empty(self._grid, self._rho) for t in self.tears}
        guess.update(tear_guess or {})
        x = self._encode(guess)
        x_prev = g_prev = None
        residuals: list[float] = []
        history: list[float] = []
        for it in range(1, max_iter + 1):
            streams, produced = self._pass(x)
            g = self._encode(produced)
            err = float(np.max(np.abs(g - x)) / max(np.max(np.abs(g)), 1e-300))
            residuals.append(err)
            history.append(float(sum(produced[t].total_solids for t in self.tears)))
            if err <= tol:
                streams.update(produced)
                return Solution(streams, it, True, residuals, history)
            if wegstein and g_prev is not None:
                dx = x - x_prev
                safe = np.where(np.abs(dx) > 1e-14, dx, 1.0)
                slope = np.where(np.abs(dx) > 1e-14, (g - g_prev) / safe, 0.0)
                q = np.clip(slope / (slope - 1.0), -5.0, 0.0)
                x_new = q * x + (1.0 - q) * g
            else:
                x_new = g
            x_prev, g_prev, x = x, g, np.clip(x_new, 0.0, None)
        raise ConvergenceError(
            f"No convergió en {max_iter} iteraciones (error relativo {residuals[-1]:.3e} > {tol:g})"
        )
