"""Pestaña «Guía»: qué se simula, cómo se calcula, qué datos necesita y cómo leer el resultado.
Las ecuaciones y autores son los de docs/teoria.md. Los textos están en `textos_es_guia.py` y
`textos_en_guia.py`."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from controles import data_table
from i18n import t

TEORIA = "https://github.com/Laxionx/simulador-conminucion/blob/main/docs/teoria.md"
N_STEPS, N_OUTPUTS, N_LIMITS = 6, 5, 4


def markdown_table(df: pd.DataFrame) -> str:
    """Tabla en Markdown: el texto largo se ajusta a la columna en vez de cortarse."""

    def cell(v: object) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ")

    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(cell(v) for v in row) + " |" for row in df.values)


def guide_tab(kind: str, flowsheet: str | None) -> None:
    st.markdown(t("guide.h.simula"))
    st.markdown(t("guide.simula"))
    st.markdown(t("guide.circuit", text=t(f"circuit.{kind}")))
    if flowsheet:
        st.html(flowsheet)
    st.markdown(t("guide.h.pasos"))
    for i in range(1, N_STEPS + 1):
        left, right = st.columns([2, 3])
        left.markdown(f"**{i}. {t(f'step.{i}.title')}**  \n{t(f'step.{i}.text')}")
        right.latex(t(f"step.{i}.latex"))
    st.caption(t("guide.teoria", url=TEORIA))
    st.markdown(t("guide.h.datos"))
    st.markdown(t("guide.datos"))
    group_col = t("col.equipo")
    for group, rows in data_table().groupby(group_col, sort=False):
        st.markdown(f"**{group}**")
        st.markdown(markdown_table(rows.drop(columns=group_col)))
    st.markdown(t("guide.h.salidas"))
    for i in range(1, N_OUTPUTS + 1):
        st.markdown(f"- **{t(f'out.{i}.name')}.** {t(f'out.{i}.text')}")
    st.markdown(t("guide.h.limites"))
    for i in range(1, N_LIMITS + 1):
        st.markdown(f"- {t(f'limit.{i}')}")
