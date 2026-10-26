"""«Estado de la operación» y «Prueba esto» de la pestaña Simulación. Solo chequeos de definición o
con fuente ya citada en el repo: la potencia del molino (Bond-Rowland, `power.py`) frente a la
energía de Bond, la convergencia del reciclo y el cierre del balance de masa (la tolerancia del
solver, `Flowsheet.solve`, tol = 1e-9). Los experimentos parten del ejemplo de la barra lateral
(los valores por defecto de `controles.DATOS`) y llevan números calculados en vivo."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from controles import DATOS, DISTRIBUTIONS, SELECTIONS, MillGeometry, build_config
from equipos import es
from estado import Fila, Prueba, cientifico
from i18n import num_g, opt, t

from conminucion.circuits import FRESH, CircuitResult, simulate
from conminucion.power import BallMillPower, bond_mill_power

KIND0 = "cerrado_directo"  # el circuito con el que abre la barra lateral
TOL_BALANCE = 1e-9  # tolerancia relativa del solver (`Flowsheet.solve`)
PREFIJO = "dato_"  # claves de la barra lateral


def potencia_molino(geom: MillGeometry) -> BallMillPower:
    return bond_mill_power(geom.diameter_m, geom.length_m, geom.filling, geom.speed,
                           geom.top_ball_mm)  # fmt: skip


def disponible_kwh_t(res: CircuitResult, power: BallMillPower) -> float:
    """Energía del molino por tonelada fresca (kWh/t): potencia del piñón / sólidos frescos."""
    return power.kw / res.streams[FRESH].total_solids


def filas_estado(kind: str, res: CircuitResult, power: BallMillPower, wegstein: bool) -> list[Fila]:
    """Los chequeos del panel de la pestaña Simulación."""
    avail, need = disponible_kwh_t(res, power), res.bond_kwh_t
    fresh = res.streams[FRESH].total_solids
    err = abs(res.balance["error_solidos"]) / fresh
    sol = res.solution
    method = t("method.wegstein") if wegstein else t("method.succ")
    if kind == "abierto":
        reciclo = Fila("ok", t("sim.chk.abierto"), t("sim.crit.reciclo"))
    else:
        text = t("sim.chk.reciclo", it=sol.iterations, method=method,
                 cl=es(res.circulating_load or 0.0, 2))  # fmt: skip
        reciclo = Fila("ok" if sol.converged else "mal", text, t("sim.crit.reciclo"))
    return [
        Fila(
            "ok" if avail >= need else "mal",
            t(
                "sim.chk.potencia",
                avail=es(avail, 2),
                need=es(need, 2),
                ratio=es(avail / need if need else float("nan"), 2),
            ),
            t("sim.crit.potencia"),
        ),  # fmt: skip
        reciclo,
        Fila(
            "ok" if err <= TOL_BALANCE else "aviso",
            t("sim.chk.balance", err=cientifico(err), tol=cientifico(TOL_BALANCE)),
            t("sim.crit.balance"),
        ),
    ]


# ---------------------------------------------------------------- Prueba esto
@dataclass(frozen=True)
class ExperimentoSim:
    """Un cambio al ejemplo. `direcciones`: magnitud → +1 sube / −1 baja; `potencia_ok`: lo que
    afirma el texto sobre si la potencia alcanza tras el cambio (None: no lo afirma)."""

    clave: str
    cambios: dict[str, float]
    direcciones: dict[str, int]
    kind: str = KIND0
    potencia_ok: bool | None = None


EXPERIMENTOS_SIM: tuple[ExperimentoSim, ...] = (
    ExperimentoSim("d50c", {"d50c": 200.0},
                   {"p80": +1, "carga": -1, "bond": -1}, potencia_ok=True),
    ExperimentoSim("tph", {"tph": 150.0}, {"disp": -1}, potencia_ok=False),
    ExperimentoSim("abierto", {}, {"p80": +1, "bond": -1}, kind="abierto", potencia_ok=True),
)  # fmt: skip


@dataclass(frozen=True)
class Resultado:
    kind: str
    res: CircuitResult
    disp: float  # kWh/t disponibles

    @property
    def p80(self) -> float:
        return self.res.streams[self.res.product].p80

    @property
    def carga(self) -> float | None:
        return self.res.circulating_load

    @property
    def bond(self) -> float:
        return self.res.bond_kwh_t


def valores_ejemplo() -> dict[str, float]:
    return {d.key: d.default for d in DATOS}


def evaluar(kind: str = KIND0, **cambios: float) -> Resultado:
    cfg, geom = build_config({**valores_ejemplo(), **cambios}, DISTRIBUTIONS[0], SELECTIONS[0])
    res = simulate(kind, cfg, wegstein=True)
    return Resultado(kind, res, disponible_kwh_t(res, potencia_molino(geom)))


@lru_cache(maxsize=1)
def pares() -> tuple:
    """(experimento, ejemplo, tras el cambio) de cada experimento."""
    base = evaluar()
    return tuple((e, base, evaluar(e.kind, **e.cambios)) for e in EXPERIMENTOS_SIM)


@lru_cache(maxsize=1)
def _mas_rapido() -> Resultado:
    """El caso de la alimentación de 150 t/h con el molino a 85 % de la velocidad crítica."""
    return evaluar(KIND0, tph=150.0, speed=85.0)


def numeros(a: Resultado, b: Resultado) -> dict[str, str]:
    mas_rapido = _mas_rapido()
    return {
        "p0": es(a.p80, 0), "p1": es(b.p80, 0), "need0": es(a.bond, 2), "need1": es(b.bond, 2),
        "cl0": es(a.carga or 0.0, 2), "cl1": es(b.carga or 0.0, 2), "disp0": es(a.disp, 2),
        "disp1": es(b.disp, 2), "disp2": es(mas_rapido.disp, 2),
        "d0": num_g(valores_ejemplo()["d50c"]), "d1": num_g(200.0),
        "tph0": num_g(valores_ejemplo()["tph"]), "tph1": num_g(150.0),
        "abierto": opt("abierto"), "cerrado": opt(KIND0),
    }  # fmt: skip


def pruebas_sim() -> list[Prueba]:
    """Los tres experimentos, con los números del modelo y los valores que fija su botón."""
    out = []
    for e, a, b in pares():
        cambios: dict[str, object] = {PREFIJO + k: v for k, v in e.cambios.items()}
        if e.kind != KIND0:
            cambios[PREFIJO + "kind"] = opt(e.kind)
        out.append(Prueba(e.clave, t(f"sim.exp.{e.clave}.titulo"),
                          t(f"sim.exp.{e.clave}.texto", **numeros(a, b)), cambios))  # fmt: skip
    return out
