"""Pestaña «Guía»: qué se simula, cómo se calcula, qué datos necesita y cómo leer el resultado.
Las ecuaciones y autores son los de docs/teoria.md."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from controles import data_table

TEORIA = "https://github.com/Laxionx/simulador-conminucion/blob/main/docs/teoria.md"

CIRCUITS = {
    "abierto": "El mineral pasa una sola vez por el molino. Simple, pero el producto sale con "
    "gruesos: no hay nada que los devuelva.",
    "cerrado_directo": "El mineral fresco entra al molino junto con los gruesos que devuelve el "
    "ciclón. La descarga del molino va al cajón, se diluye y se bombea al ciclón: los finos "
    "salen por el rebalse como producto y los gruesos vuelven al molino.",
    "cerrado_inverso": "El mineral fresco entra primero al ciclón: si ya trae finos, salen "
    "directo al producto sin pasar por el molino. Solo los gruesos van al molino, y su descarga "
    "vuelve al cajón del ciclón.",
}

STEPS = (
    ("Alimentación", "La granulometría del mineral fresco se describe con una ecuación de dos "
     "parámetros, Rosin-Rammler o Gaudin-Schuhmann (King, 2001).",
     r"P(x) = 1 - e^{-(x/x_{63})^{m}} \qquad P(x) = \min\left[1, (x/k)^{\alpha}\right]"),
    ("Molino de bolas", "Cada clase de tamaño se rompe a una velocidad propia (selección de "
     "Austin) y sus fragmentos caen a clases más finas según la función de fractura. El molino "
     "es uno o varios tanques de mezcla perfecta en serie (Whiten, 1974; Austin, Klimpel y "
     "Luckie, 1984).",
     r"p_i = \frac{f_i + \sum_{j<i} (r/d)_j\, a_{ij}\, p_j}{1 + (r/d)_i}"
     r"\qquad S_i = \frac{A\,(x_i/1000)^{\alpha}}{1 + (x_i/\mu)^{\Lambda}}"),
    ("Cajón", "Agrega el agua justa para que la pulpa llegue al ciclón con el % de sólidos "
     "pedido.", r"W = \sum m \cdot \frac{100 - \%s}{\%s}"),
    ("Hidrociclón", "Cada tamaño se reparte entre la descarga (gruesos) y el rebalse (finos) "
     "según la curva de Whiten; una parte del agua, Rf, arrastra finos sin clasificar a la "
     "descarga (Lynch y Rao, 1975; Kelsall, 1953).",
     r"E_a(x) = R_f + (1 - R_f)\,\frac{e^{\alpha x/d_{50c}} - 1}"
     r"{e^{\alpha x/d_{50c}} + e^{\alpha} - 2}"),
    ("Reciclo", "Los gruesos que vuelven dependen de lo que sale del molino, que depende de "
     "los gruesos que vuelven: se itera hasta que la corriente devuelta no cambie más de una "
     "parte en mil millones. Wegstein acelera la iteración.",
     r"x_{k+1} = q\,x_k + (1 - q)\,g(x_k) \qquad q = s/(s - 1)"),
    ("Energía y potencia", "Bond (1952) estima la energía para llevar el mineral de F80 a P80. "
     "La potencia del molino sale de su tamaño, su llenado y su giro (Bond, con las correcciones "
     "de Rowland y Kjos, 1980). La velocidad crítica es la que pega las bolas a la pared.",
     r"W = 10\,W_i\left(\frac{1}{\sqrt{P_{80}}} - \frac{1}{\sqrt{F_{80}}}\right)"
     r"\qquad N_c = \frac{42{,}3}{\sqrt{D - d}}\ \text{rpm}"),
)  # fmt: skip

OUTPUTS = (
    ("P80 del producto", "Tamaño bajo el que pasa el 80 % del producto. Es lo que la planta "
     "controla: define la liberación del mineral para la flotación."),
    ("Carga circulante", "Toneladas que vuelven al molino por cada tonelada fresca. Alta = el "
     "ciclón devuelve mucho; el molino trabaja con más carga."),
    ("Energía de Bond", "kWh por tonelada fresca que pide la reducción de tamaño según Bond. "
     "Se compara con la energía que entrega el molino (potencia ÷ t/h): si es menor, el "
     "molino no alcanza ese P80 según Bond. Es un chequeo grueso: no lleva los factores de "
     "eficiencia de Rowland."),
    ("Iteraciones", "Cuántas vueltas dio el cálculo del reciclo hasta converger."),
    ("Balance", "Sólidos que entran contra sólidos que salen: debe cerrar casi a cero."),
)  # fmt: skip

LIMITS = (
    "Estado estacionario: no simula arranques, paradas ni cambios en el tiempo.",
    "El ciclón usa una curva de eficiencia con parámetros dados; no calcula el d50c desde la "
    "geometría del equipo (eso es Plitt, disponible en la librería, no en esta app).",
    "La velocidad de fractura no cambia con la potencia del molino: tiempo de residencia y "
    "potencia se dan por separado.",
    "Pestaña de ajuste: datos sintéticos generados con parámetros conocidos, para mostrar que "
    "el método los recupera; no son datos de una planta.",
)


def markdown_table(df: pd.DataFrame) -> str:
    """Tabla en Markdown: el texto largo se ajusta a la columna en vez de cortarse."""

    def cell(v: object) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ")

    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(cell(v) for v in row) + " |" for row in df.values)


def guide_tab(kind: str, flowsheet: str | None) -> None:
    st.markdown("### Qué simula")
    st.markdown(
        "Un **circuito de molienda y clasificación**: el mineral chancado entra a un molino de "
        "bolas que lo muele y un hidrociclón separa lo que ya está fino (producto) de lo que "
        "todavía está grueso. El simulador calcula, para cada corriente, cuántas toneladas de "
        "sólidos y de agua lleva y qué tan fino es el mineral, a partir de ecuaciones "
        "publicadas."
    )
    st.markdown(f"**Circuito elegido.** {CIRCUITS[kind]}")
    if flowsheet:
        st.html(flowsheet)
    st.markdown("### Cómo lo calcula, paso a paso")
    for i, (title, text, latex) in enumerate(STEPS, start=1):
        left, right = st.columns([2, 3])
        left.markdown(f"**{i}. {title}**  \n{text}")
        right.latex(latex)
    st.caption(f"Cada ecuación, con su derivación y referencia, en [docs/teoria.md]({TEORIA}).")
    st.markdown("### Qué datos necesita")
    st.markdown(
        "Cada dato tiene una ayuda (**?**) en la barra lateral. Para empezar, el botón "
        "**Cargar ejemplo típico** pone todos los valores de la columna «Ejemplo»."
    )
    for group, rows in data_table().groupby("Equipo", sort=False):
        st.markdown(f"**{group}**")
        st.markdown(markdown_table(rows.drop(columns="Equipo")))
    st.markdown("### Qué devuelve y cómo leerlo")
    for name, text in OUTPUTS:
        st.markdown(f"- **{name}.** {text}")
    st.markdown("### Lo que no hace")
    for text in LIMITS:
        st.markdown(f"- {text}")
