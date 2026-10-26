"""Cada dato de entrada se define una sola vez: arma la barra lateral y la tabla «Qué datos
necesita» de la guía, así las dos no se pueden desfasar. Sus textos están en `textos_es_datos.py`
y `textos_en_datos.py`, con las claves `dato.<clave>.label|meaning` y `src.*`."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st
from i18n import current, int_num, num_g, opt, t, use

from conminucion.circuits import KINDS, CircuitConfig
from conminucion.classifier import EfficiencyCurve
from conminucion.fracture import Fracture
from conminucion.mill import AustinSelection, BallMill, KnotSelection
from conminucion.sizes import SizeGrid, gaudin_schuhmann, rosin_rammler
from conminucion.stream import Stream

KNOT_SIZES = (4750.0, 1187.0, 297.0, 74.0)
KNOT_RD = (0.9, 1.6, 1.0, 0.35)
DISTRIBUTIONS = ("Rosin-Rammler", "Gaudin-Schuhmann")
SELECTIONS = ("Austin (S, τ)", "Nudos r/d")
PREFIX = "dato_"


def _tx(text: str) -> str:
    """El texto de una clave de `textos_*`; si no es una clave, el propio texto."""
    try:
        return t(text)
    except KeyError:
        return text


@dataclass(frozen=True)
class Dato:
    key: str
    label_k: str
    unit_k: str
    lo: float
    hi: float
    default: float
    step: float | None
    group: str
    meaning_k: str
    source_k: str
    widget: str = "number"  # number | slider
    when: str = ""  # solo se pide con esta opción
    size: float | None = None  # tamaño (µm) del nudo r/d: lo lleva el rótulo

    @property
    def label(self) -> str:
        if self.size is not None:
            return t(self.label_k, size=num_g(self.size))
        return _tx(self.label_k)

    @property
    def unit(self) -> str:
        return _tx(self.unit_k)

    @property
    def meaning(self) -> str:
        return _tx(self.meaning_k)

    @property
    def source(self) -> str:
        return _tx(self.source_k)

    @property
    def help(self) -> str:
        unit = f" ({self.unit})" if self.unit else ""
        return t("dato.help", meaning=self.meaning, unit=unit, lo=_num(self.lo), hi=_num(self.hi),
                 source=self.source)  # fmt: skip


def _num(x: float) -> str:
    """Número en el formato del idioma: «1 000», «2,7» (es) o «1,000», «2.7» (en)."""
    return int_num(x) if float(x).is_integer() else num_g(x)


CIRC, ALIM, CIN, POT, CIC, ENE = (
    "Circuito",
    "Alimentación",
    "Molino: cinética de molienda",
    "Molino: tamaño y potencia",
    "Hidrociclón y cajón",
    "Energía",
)


def _d(key: str, unit: str, lo: float, hi: float, default: float, step: float | None,
       group: str, source: str | None = None, **kw) -> Dato:  # fmt: skip
    """Un dato: sus textos son las claves `dato.<clave>.label|meaning|source` (o `src.*`)."""
    return Dato(key, f"dato.{key}.label", unit, lo, hi, default, step, group,
                f"dato.{key}.meaning", source or f"dato.{key}.source", **kw)  # fmt: skip


DATOS: tuple[Dato, ...] = (
    _d("top", "µm", 1000, 50000, 9500, 500, ALIM, "src.sieves"),
    _d("n", "", 8, 24, 17, 1, ALIM, "src.sieves", widget="slider"),
    _d("tph", "t/h", 1, 5000, 100, None, ALIM),
    _d("rho", "t/m³", 1, 8, 2.7, 0.1, ALIM),
    _d("water", "t/h", 0, 5000, 0, None, ALIM),
    _d("x63", "µm", 100, 40000, 3200, None, ALIM, "src.lab", when=DISTRIBUTIONS[0]),
    _d("m", "", 0.2, 5, 1.0, 0.1, ALIM, "src.lab", when=DISTRIBUTIONS[0]),
    _d("k", "µm", 100, 60000, 12000, None, ALIM, "src.lab", when=DISTRIBUTIONS[1]),
    _d("a", "", 0.2, 3, 0.8, 0.05, ALIM, "src.lab", when=DISTRIBUTIONS[1]),
    _d("A", "1/min", 0.01, 10, 0.8, 0.1, CIN, "src.mol", when=SELECTIONS[0]),
    _d("alpha_s", "", 0.1, 3, 0.9, 0.1, CIN, "src.mol", when=SELECTIONS[0]),
    _d("mu", "µm", 100, 20000, 2500, 100, CIN, "src.mol", when=SELECTIONS[0]),
    _d("lam", "", 0.5, 10, 3.0, 0.5, CIN, "src.mol", when=SELECTIONS[0]),
    _d("tau", "min", 0.1, 60, 3.0, 0.5, CIN, when=SELECTIONS[0]),
    *(
        Dato(f"rd{i}", "dato.rd.label", "", 0.001, 20, v, None, CIN, "dato.rd.meaning",
             "dato.rd.source", when=SELECTIONS[1], size=s)
        for i, (s, v) in enumerate(zip(KNOT_SIZES, KNOT_RD, strict=True))
    ),
    _d("phi", "", 0, 1, 0.6, 0.05, CIN, "src.fra", widget="slider"),
    _d("gamma", "", 0.2, 2, 0.8, 0.05, CIN, "src.fra", widget="slider"),
    _d("beta", "", 1, 6, 3.5, 0.1, CIN, "src.fra", widget="slider"),
    _d("mixers", "", 1, 8, 1, 1, CIN, widget="slider"),
    _d("mill_water", "t/h", 0, 1000, 0, None, CIN),
    _d("diameter", "m", 1, 8, 4.0, 0.1, POT, "src.plano"),
    _d("length", "m", 1, 15, 6.0, 0.5, POT, "src.plano"),
    _d("filling", "%", 30, 45, 38, 1, POT, widget="slider"),
    _d("speed", "unit.crit", 60, 85, 75, 1, POT, widget="slider"),
    _d("top_ball", "mm", 25, 125, 75, 5, POT),
    _d("d50c", "µm", 5, 5000, 100, 10, CIC, "src.cyc"),
    _d("alpha_c", "", 0.5, 10, 3.0, 0.5, CIC, "src.cyc"),
    _d("rf", "", 0, 0.9, 0.2, 0.05, CIC, widget="slider"),
    _d("pct", "%", 20, 70, 45, 1, CIC, widget="slider"),
    _d("wi", "kWh/t", 5, 30, 14, 0.5, ENE),
)  # fmt: skip
BY_KEY = {d.key: d for d in DATOS}
CHOICES = (  # (clave de sus textos, grupo de la tabla)
    ("kind", CIRC),
    ("dist", ALIM),
    ("param", CIN),
)


def kind_labels() -> list[str]:
    return [opt(k) for k in KINDS]


def param_labels() -> list[str]:
    return [opt(p) for p in SELECTIONS]


def choice_options(name: str) -> str:
    """Las opciones de una elección, en el idioma actual, para la tabla de datos."""
    if name == "kind":
        return ", ".join(kind_labels())
    return ", ".join(DISTRIBUTIONS) if name == "dist" else ", ".join(param_labels())


@dataclass(frozen=True)
class MillGeometry:
    diameter_m: float
    length_m: float
    filling: float  # fracción
    speed: float  # fracción de la crítica
    top_ball_mm: float


def _ask(d: Dato) -> float:
    sb, key = st.sidebar, PREFIX + d.key
    label = f"{d.label} ({d.unit})" if d.unit else d.label
    if d.widget == "slider":
        if float(d.default).is_integer() and float(d.step or 1).is_integer():
            lo, hi, v = int(d.lo), int(d.hi), int(d.default)
            return sb.slider(label, lo, hi, v, int(d.step or 1), help=d.help, key=key)
    step = None if d.step is None else float(d.step)  # Streamlit pide todos del mismo tipo
    if d.widget == "slider":
        return sb.slider(label, float(d.lo), float(d.hi), float(d.default), step,
                         help=d.help, key=key)  # fmt: skip
    return sb.number_input(label, float(d.lo), float(d.hi), float(d.default), step,
                           help=d.help, key=key)  # fmt: skip


def _relabel_selects(previous: str) -> None:
    """Al cambiar de idioma, el circuito y la parametrización conservan su elección: se pasa del
    rótulo del idioma anterior al del actual (el valor guardado en la sesión es el rótulo)."""
    for key, raws in ((PREFIX + "kind", KINDS), (PREFIX + "param", SELECTIONS)):
        if key not in st.session_state:
            continue
        for raw in raws:
            with use(previous):
                old = opt(raw)
            if old == st.session_state[key]:
                st.session_state[key] = opt(raw)
                break


def reset_to_example() -> None:
    """Vuelve todos los datos al ejemplo típico."""
    for k in [k for k in st.session_state if str(k).startswith(PREFIX)]:
        del st.session_state[k]


def build_config(v: dict[str, float], dist: str, param: str) -> tuple[CircuitConfig, MillGeometry]:
    """El circuito y la geometría del molino a partir de los valores de los datos (`v`, con las
    claves de `DATOS`), la distribución de la alimentación y la parametrización del molino. La
    barra lateral y los experimentos de «Prueba esto» arman el circuito con esta misma función."""
    grid = SizeGrid.geometric(v["top"], int(v["n"]))
    if dist == DISTRIBUTIONS[0]:
        fractions = rosin_rammler(grid, v["x63"], v["m"])
    else:
        fractions = gaudin_schuhmann(grid, v["k"], v["a"])
    fresh = Stream.from_fractions(grid, fractions, v["tph"], v["water"], v["rho"])
    if param == SELECTIONS[0]:
        sel = AustinSelection(v["A"], v["alpha_s"], v["mu"], v["lam"], v["tau"])
    else:
        sel = KnotSelection(KNOT_SIZES, tuple(v[f"rd{i}"] for i in range(len(KNOT_SIZES))))
    frac = Fracture(v["phi"], v["gamma"], v["beta"])
    mill = BallMill(sel, frac, int(v["mixers"]), v["mill_water"])
    geometry = MillGeometry(v["diameter"], v["length"], v["filling"] / 100.0,
                            v["speed"] / 100.0, v["top_ball"])  # fmt: skip
    cls = EfficiencyCurve(v["d50c"], v["alpha_c"], v["rf"])
    return CircuitConfig(fresh, mill, cls, float(v["pct"]), v["wi"]), geometry


def sidebar_config() -> tuple[str, CircuitConfig, bool, MillGeometry]:
    """Lee la barra lateral y arma el circuito y la geometría del molino."""
    sb = st.sidebar
    seen = st.session_state.get("_lang_seen")
    if seen and seen != current():
        _relabel_selects(seen)
    st.session_state["_lang_seen"] = current()
    labels = kind_labels()
    chosen = sb.selectbox(t("choice.kind.label"), labels, index=1,
                          help=t("choice.kind.meaning"), key=PREFIX + "kind")  # fmt: skip
    kind = KINDS[labels.index(chosen)]
    sb.button(t("sidebar.example"), on_click=reset_to_example, width="stretch")
    v: dict[str, float] = {}
    sb.subheader(t("group." + ALIM))
    for key in ("top", "n", "tph", "rho", "water"):
        v[key] = _ask(BY_KEY[key])
    dist = sb.radio(t("choice.dist.label"), DISTRIBUTIONS, horizontal=True,
                    help=t("choice.dist.meaning"), key=PREFIX + "dist")  # fmt: skip
    for d in DATOS:
        if d.when == dist:
            v[d.key] = _ask(d)

    sb.subheader(t("group." + CIN))
    plabels = param_labels()
    pchosen = sb.radio(t("choice.param.label"), plabels, horizontal=True,
                       help=t("choice.param.meaning"), key=PREFIX + "param")  # fmt: skip
    param = SELECTIONS[plabels.index(pchosen)]
    for d in DATOS:
        if d.when == param or (d.group == CIN and not d.when):
            v[d.key] = _ask(d)

    sb.subheader(t("group." + POT))
    for key in ("diameter", "length", "filling", "speed", "top_ball"):
        v[key] = _ask(BY_KEY[key])

    sb.subheader(t("group." + CIC))
    for key in ("d50c", "alpha_c", "rf", "pct"):
        v[key] = _ask(BY_KEY[key])
    sb.subheader(t("group." + ENE))
    v["wi"] = _ask(BY_KEY["wi"])
    wegstein = sb.checkbox(
        t("sidebar.wegstein"), value=True, key=PREFIX + "wegstein", help=t("sidebar.wegstein.help")
    )
    cfg, geometry = build_config(v, dist, param)
    return kind, cfg, wegstein, geometry


def data_table() -> pd.DataFrame:
    """La tabla «Qué datos necesita», hecha de las mismas definiciones que la barra lateral."""
    rows = [
        {t("col.equipo"): t("group." + g), t("col.dato"): t(f"choice.{name}.label"),
         t("col.unit"): "", t("col.range"): choice_options(name), t("col.example"): "",
         t("col.what"): t(f"choice.{name}.meaning"), t("col.how"): t("choice.how")}
        for name, g in CHOICES
    ]  # fmt: skip
    rows += [
        {
            t("col.equipo"): t("group." + d.group),
            t("col.dato"): d.label + (t("dato.with", when=opt(d.when)) if d.when else ""),
            t("col.unit"): d.unit,
            t("col.range"): t("dato.range", lo=_num(d.lo), hi=_num(d.hi)),
            t("col.example"): _num(d.default),
            t("col.what"): d.meaning,
            t("col.how"): d.source[0].upper() + d.source[1:],
        }
        for d in DATOS
    ]
    return pd.DataFrame(rows)
