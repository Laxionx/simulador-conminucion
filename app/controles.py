"""Cada dato de entrada se define una sola vez: arma la barra lateral y la tabla «Qué datos
necesita» de la guía, así las dos no se pueden desfasar."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from conminucion.circuits import KINDS, CircuitConfig
from conminucion.classifier import EfficiencyCurve
from conminucion.fracture import Fracture
from conminucion.mill import AustinSelection, BallMill, KnotSelection
from conminucion.sizes import SizeGrid, gaudin_schuhmann, rosin_rammler
from conminucion.stream import Stream

LABELS = {
    "abierto": "Molino en circuito abierto",
    "cerrado_directo": "Circuito cerrado directo",
    "cerrado_inverso": "Circuito cerrado inverso",
}
KNOT_SIZES = (4750.0, 1187.0, 297.0, 74.0)
KNOT_RD = (0.9, 1.6, 1.0, 0.35)
DISTRIBUTIONS = ("Rosin-Rammler", "Gaudin-Schuhmann")
SELECTIONS = ("Austin (S, τ)", "Nudos r/d")
PREFIX = "dato_"


@dataclass(frozen=True)
class Dato:
    key: str
    label: str
    unit: str
    lo: float
    hi: float
    default: float
    step: float | None
    group: str
    meaning: str
    source: str
    widget: str = "number"  # number | slider
    when: str = ""  # solo se pide con esta opción

    @property
    def help(self) -> str:
        unit = f" ({self.unit})" if self.unit else ""
        return (
            f"{self.meaning} Rango{unit}: {_num(self.lo)} a {_num(self.hi)}. "
            f"En planta: {self.source}"
        )


def _num(x: float) -> str:
    """Número en español: «1 000», «2,7»."""
    if float(x).is_integer():
        return f"{int(x):,}".replace(",", " ")
    return f"{x:g}".replace(".", ",")


CIRC, ALIM, CIN, POT, CIC, ENE = (
    "Circuito",
    "Alimentación",
    "Molino: cinética de molienda",
    "Molino: tamaño y potencia",
    "Hidrociclón y cajón",
    "Energía",
)
LAB = "se ajusta al análisis granulométrico (tamizado) de la alimentación."
MOL = "se ajusta a pruebas de molienda en un molino de laboratorio."
FRA = "prueba de fractura de una sola clase de tamaño en el laboratorio."
CYC = "se ajusta a un muestreo del ciclón (curva de partición)."
DATOS: tuple[Dato, ...] = (
    Dato("top", "Tamiz superior", "µm", 1000, 50000, 9500, 500, ALIM,
         "El tamiz más grueso de la serie; cada tamiz siguiente es √2 veces más fino.",
         "la serie de tamices que usa el laboratorio."),
    Dato("n", "Número de tamices", "", 8, 24, 17, 1, ALIM,
         "Cuántos tamices tiene la serie; el último cierra en el fondo.",
         "la serie de tamices que usa el laboratorio.", widget="slider"),
    Dato("tph", "Sólidos frescos", "t/h", 1, 5000, 100, None, ALIM,
         "Mineral seco que entra al circuito por hora.",
         "balanza de la faja que alimenta al molino."),
    Dato("rho", "Densidad de sólidos", "t/m³", 1, 8, 2.7, 0.1, ALIM,
         "Densidad del mineral, sin poros ni agua; fija el volumen de pulpa.",
         "picnómetro en el laboratorio."),
    Dato("water", "Agua en la alimentación", "t/h", 0, 5000, 0, None, ALIM,
         "Agua que entra junto con el mineral fresco.",
         "caudalímetro del agua de alimentación y humedad del mineral."),
    Dato("x63", "x63", "µm", 100, 40000, 3200, None, ALIM,
         "Tamaño bajo el que pasa el 63,2 % de la alimentación.", LAB, when=DISTRIBUTIONS[0]),
    Dato("m", "m", "", 0.2, 5, 1.0, 0.1, ALIM,
         "Pendiente de Rosin-Rammler: más alta, distribución más estrecha.", LAB,
         when=DISTRIBUTIONS[0]),
    Dato("k", "k", "µm", 100, 60000, 12000, None, ALIM,
         "Tamaño máximo de la distribución de Gaudin-Schuhmann.", LAB, when=DISTRIBUTIONS[1]),
    Dato("a", "α", "", 0.2, 3, 0.8, 0.05, ALIM,
         "Pendiente de Gaudin-Schuhmann.", LAB, when=DISTRIBUTIONS[1]),
    Dato("A", "A", "1/min", 0.01, 10, 0.8, 0.1, CIN,
         "Velocidad de fractura de las partículas de 1 mm.", MOL, when=SELECTIONS[0]),
    Dato("alpha_s", "α (selección)", "", 0.1, 3, 0.9, 0.1, CIN,
         "Cuánto sube la velocidad de fractura con el tamaño.", MOL, when=SELECTIONS[0]),
    Dato("mu", "μ", "µm", 100, 20000, 2500, 100, CIN,
         "Sobre este tamaño las partículas son grandes para las bolas y se rompen más lento.",
         MOL, when=SELECTIONS[0]),
    Dato("lam", "Λ", "", 0.5, 10, 3.0, 0.5, CIN,
         "Qué tan rápido cae la velocidad de fractura por encima de μ.", MOL,
         when=SELECTIONS[0]),
    Dato("tau", "τ, tiempo de residencia", "min", 0.1, 60, 3.0, 0.5, CIN,
         "Tiempo medio que la pulpa pasa dentro del molino.",
         "volumen de pulpa en el molino entre el caudal de pulpa, o una prueba con trazador.",
         when=SELECTIONS[0]),
    *(
        Dato(f"rd{i}", f"r/d a {s:g} µm", "", 0.001, 20, v, None, CIN,
             "Velocidad de fractura entre velocidad de descarga para ese tamaño.",
             "se ajusta a un muestreo de la alimentación y la descarga del molino.",
             when=SELECTIONS[1])
        for i, (s, v) in enumerate(zip(KNOT_SIZES, KNOT_RD, strict=True))
    ),
    Dato("phi", "φ (fractura)", "", 0, 1, 0.6, 0.05, CIN,
         "Parte de los fragmentos que sigue la rama fina de la función de fractura.", FRA,
         widget="slider"),
    Dato("gamma", "γ", "", 0.2, 2, 0.8, 0.05, CIN,
         "Pendiente de la rama fina de la función de fractura.", FRA, widget="slider"),
    Dato("beta", "β", "", 1, 6, 3.5, 0.1, CIN,
         "Pendiente de la rama gruesa de la función de fractura.", FRA, widget="slider"),
    Dato("mixers", "Mezcladores en serie", "", 1, 8, 1, 1, CIN,
         "Tanques de mezcla perfecta que representan el molino; más tanques, flujo más "
         "parecido a un pistón.",
         "distribución de tiempos de residencia medida con un trazador.", widget="slider"),
    Dato("mill_water", "Agua de adición al molino", "t/h", 0, 1000, 0, None, CIN,
         "Agua que se agrega en la entrada del molino.", "caudalímetro de esa línea."),
    Dato("diameter", "Diámetro del molino", "m", 1, 8, 4.0, 0.1, POT,
         "Diámetro interior entre revestimientos.", "plano del molino."),
    Dato("length", "Largo del molino", "m", 1, 15, 6.0, 0.5, POT,
         "Largo interior efectivo.", "plano del molino."),
    Dato("filling", "Llenado de bolas", "%", 30, 45, 38, 1, POT,
         "Parte del volumen interior que ocupa la carga de bolas, con sus huecos.",
         "altura libre sobre la carga, medida con el molino detenido.", widget="slider"),
    Dato("speed", "Velocidad de giro", "% de la crítica", 60, 85, 75, 1, POT,
         "Giro como porcentaje de la velocidad que pega las bolas a la pared.",
         "rpm del molino (motor y reductor) dividido por la velocidad crítica.",
         widget="slider"),
    Dato("top_ball", "Bola más grande de la recarga", "mm", 25, 125, 75, 5, POT,
         "Solo cambia la potencia en molinos de más de 3,3 m.",
         "programa de recarga de bolas."),
    Dato("d50c", "d50c", "µm", 5, 5000, 100, 10, CIC,
         "Tamaño corregido que se reparte mitad a la descarga y mitad al rebalse.", CYC),
    Dato("alpha_c", "α (nitidez)", "", 0.5, 10, 3.0, 0.5, CIC,
         "Nitidez del corte: más alta, separación más limpia.", CYC),
    Dato("rf", "Rf (bypass de agua)", "", 0, 0.9, 0.2, 0.05, CIC,
         "Parte del agua de alimentación que sale por la descarga y arrastra finos sin "
         "clasificar.",
         "se ajusta a un muestreo del ciclón (agua en la descarga y la alimentación).",
         widget="slider"),
    Dato("pct", "% de sólidos de la alimentación al ciclón", "%", 20, 70, 45, 1, CIC,
         "El cajón agrega agua hasta este porcentaje de sólidos.",
         "densímetro en la alimentación al ciclón o balanza Marcy.", widget="slider"),
    Dato("wi", "Wi de Bond", "kWh/t", 5, 30, 14, 0.5, ENE,
         "Energía para moler de un tamaño muy grande a un P80 de 100 µm.",
         "prueba estándar de Bond en el laboratorio."),
)  # fmt: skip
BY_KEY = {d.key: d for d in DATOS}
CHOICES = (
    ("Preset de circuito", CIRC, "Qué circuito se simula.", ", ".join(LABELS.values())),
    ("Distribución", ALIM, "Ecuación que describe la alimentación.", ", ".join(DISTRIBUTIONS)),
    ("Parametrización de r/d", CIN, "Cómo se describe la velocidad de fractura.",
     ", ".join(SELECTIONS)),
)  # fmt: skip


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


def reset_to_example() -> None:
    """Vuelve todos los datos al ejemplo típico."""
    for k in [k for k in st.session_state if str(k).startswith(PREFIX)]:
        del st.session_state[k]


def sidebar_config() -> tuple[str, CircuitConfig, bool, MillGeometry]:
    """Lee la barra lateral y arma el circuito y la geometría del molino."""
    sb = st.sidebar
    kind = sb.selectbox("Preset de circuito", KINDS, index=1, format_func=LABELS.get,
                        help=CHOICES[0][2], key=PREFIX + "kind")  # fmt: skip
    sb.button("Cargar ejemplo típico", on_click=reset_to_example, width="stretch")
    v: dict[str, float] = {}
    sb.subheader(ALIM)
    for key in ("top", "n", "tph", "rho", "water"):
        v[key] = _ask(BY_KEY[key])
    dist = sb.radio("Distribución", DISTRIBUTIONS, horizontal=True, help=CHOICES[1][2],
                    key=PREFIX + "dist")  # fmt: skip
    for d in DATOS:
        if d.when == dist:
            v[d.key] = _ask(d)
    grid = SizeGrid.geometric(v["top"], int(v["n"]))
    if dist == DISTRIBUTIONS[0]:
        fractions = rosin_rammler(grid, v["x63"], v["m"])
    else:
        fractions = gaudin_schuhmann(grid, v["k"], v["a"])
    fresh = Stream.from_fractions(grid, fractions, v["tph"], v["water"], v["rho"])

    sb.subheader(CIN)
    param = sb.radio("Parametrización de r/d", SELECTIONS, horizontal=True, help=CHOICES[2][2],
                     key=PREFIX + "param")  # fmt: skip
    for d in DATOS:
        if d.when == param or (d.group == CIN and not d.when):
            v[d.key] = _ask(d)
    if param == SELECTIONS[0]:
        sel = AustinSelection(v["A"], v["alpha_s"], v["mu"], v["lam"], v["tau"])
    else:
        sel = KnotSelection(KNOT_SIZES, tuple(v[f"rd{i}"] for i in range(len(KNOT_SIZES))))
    frac = Fracture(v["phi"], v["gamma"], v["beta"])
    mill = BallMill(sel, frac, int(v["mixers"]), v["mill_water"])

    sb.subheader(POT)
    for key in ("diameter", "length", "filling", "speed", "top_ball"):
        v[key] = _ask(BY_KEY[key])
    geometry = MillGeometry(v["diameter"], v["length"], v["filling"] / 100.0,
                            v["speed"] / 100.0, v["top_ball"])  # fmt: skip

    sb.subheader(CIC)
    cls = EfficiencyCurve(_ask(BY_KEY["d50c"]), _ask(BY_KEY["alpha_c"]), _ask(BY_KEY["rf"]))
    pct = _ask(BY_KEY["pct"])
    sb.subheader(ENE)
    wi = _ask(BY_KEY["wi"])
    wegstein = sb.checkbox(
        "Aceleración de Wegstein", value=True, key=PREFIX + "wegstein",
        help="Acelera la convergencia del reciclo; sin ella se usa sustitución sucesiva.",
    )  # fmt: skip
    return kind, CircuitConfig(fresh, mill, cls, float(pct), wi), wegstein, geometry


def data_table() -> pd.DataFrame:
    """La tabla «Qué datos necesita», hecha de las mismas definiciones que la barra lateral."""
    rows = [
        {"Equipo": g, "Dato": label, "Unidad": "", "Rango": options, "Ejemplo": "",
         "Qué es": meaning, "Cómo se obtiene": "Elección del usuario"}
        for label, g, meaning, options in CHOICES
    ]  # fmt: skip
    rows += [
        {
            "Equipo": d.group,
            "Dato": d.label + (f" (con {d.when})" if d.when else ""),
            "Unidad": d.unit,
            "Rango": f"{_num(d.lo)} a {_num(d.hi)}",
            "Ejemplo": _num(d.default),
            "Qué es": d.meaning,
            "Cómo se obtiene": d.source[0].upper() + d.source[1:],
        }
        for d in DATOS
    ]
    return pd.DataFrame(rows)
