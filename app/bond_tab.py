"""Pestaña «Ensayo de Bond»: ficha, calculadora del procedimiento de GMG y simulación ciclo a ciclo
del ensayo de Hebei. Los controles se definen una sola vez en `bond_datos.CAMPOS`; de ahí salen los
campos de la calculadora y la tabla de datos de la ficha. Nada de lo que escribe el visitante entra
al SVG ni al HTML: la tabla y los campos solo alimentan números del cálculo."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from bond_datos import (
    BOLA_MAX_MM,
    BOLAS_KG,
    BOLAS_N,
    BY_KEY,
    CAMPOS,
    COLUMNAS_CICLOS,
    CORTE_PCT,
    FINOS_MAX,
    HEBEI_GBP_FINAL,
    HEBEI_WI,
    MAX_CICLOS,
    MIN_CICLOS,
    MOLINO_LARGO_M,
    PREFIX,
    TABLE_KEY,
    Campo,
    CasoHebei,
    calcular,
    caso_hebei,
    tabla_inicial,
    validar,
    velocidad_critica_frac,
)
from bond_grafico import bond_figure
from carga import cargador
from equipos import as_images, es, mill_svg
from guia import markdown_table
from i18n import int_num, num_g, t

from conminucion.ensayo_bond import MOLINO_DIAMETRO_M, MOLINO_RPM, ResultadoBond

CYCLE_KEY = PREFIX + "ciclo"
BASE_KEY, VER_KEY = PREFIX + "base", PREFIX + "ver"  # la tabla cargada y cuántas veces se cargó
ROW_PX = 35  # alto de una fila de st.dataframe, para que la tabla se vea entera


def _num(x: float) -> str:
    return int_num(x) if float(x).is_integer() else num_g(x)


def datos_table() -> pd.DataFrame:
    """La tabla «datos que necesita» de la ficha, de las mismas definiciones que los campos."""
    rows = [
        {
            t("bond.col.campo"): t(c.label_k),
            t("bond.col.unit"): c.unit,
            t("bond.col.range"): f"{_num(c.lo)}–{_num(c.hi)}".replace(" ", " "),
            t("bond.col.example"): _num(c.default),
            t("bond.col.what"): t(c.meaning_k),
            t("bond.col.how"): t(c.source_k)[0].upper() + t(c.source_k)[1:],
        }
        for c in CAMPOS
    ]
    return pd.DataFrame(rows)


def ficha() -> None:
    st.markdown(t("bond.h.ficha"))
    st.markdown(t("bond.ficha.que"))
    st.markdown(t("bond.ficha.datos"))
    st.markdown(markdown_table(datos_table()))
    st.markdown(t("bond.ficha.ciclos", max=_num(FINOS_MAX), n=MAX_CICLOS))
    st.markdown(t("bond.ficha.devuelve"))
    st.markdown(t("bond.ficha.fuentes"))
    st.markdown(t("bond.ficha.supuestos"))


def _ask(c: Campo, container) -> float:
    label = f"{t(c.label_k)} ({c.unit})" if c.unit else t(c.label_k)
    help_ = f"{t(c.meaning_k)} {t(c.source_k)}. [{_num(c.lo)}–{_num(c.hi)}]"
    key = PREFIX + c.key
    # Un campo entero también es un número decimal para Streamlit: con un número_input entero, un
    # NaN o un infinito mandados por un cliente rompen su deserializador antes de llegar aquí.
    return container.number_input(label, float(c.lo), float(c.hi), float(c.default),
                                  float(c.step), format="%.0f" if c.integer else None, help=help_,
                                  key=key)  # fmt: skip


def _reset() -> None:
    for k in [k for k in st.session_state if str(k).startswith(PREFIX)]:
        del st.session_state[k]


def cycle_frame(res: ResultadoBond) -> pd.DataFrame:
    """La tabla calculada, con encabezados del idioma; los números quedan como números."""
    si, no = t("bond.yes"), t("bond.no")
    return pd.DataFrame({
        t("bond.t.ciclo"): res.columna("ciclo"),
        t("bond.t.alim"): [round(x, 1) for x in res.columna("alimentacion_nueva_g")],
        t("bond.t.rev"): res.columna("revoluciones"),
        t("bond.t.total"): [round(x, 1) for x in res.columna("finos_total_g")],
        t("bond.t.dealim"): [round(x, 1) for x in res.columna("finos_de_alimentacion_g")],
        t("bond.t.nuevos"): [round(x, 1) for x in res.columna("finos_nuevos_g")],
        t("bond.t.gbp"): [round(x, 4) for x in res.columna("gbp")],
        t("bond.t.cl"): [round(x, 1) for x in res.columna("carga_circulante_pct")],
        t("bond.t.inv"): [si if x else no for x in res.columna("invierte")],
    })  # fmt: skip


def calculator() -> None:
    st.markdown(t("bond.h.calc"))
    st.markdown(t("bond.calc.intro"))
    cols = st.columns(3)
    valores = {c.key: _ask(c, cols[i % 3]) for i, c in enumerate(CAMPOS)}
    column = st.column_config.NumberColumn(
        t("bond.edit.finos"), help=t("bond.edit.help"), min_value=0.0, max_value=FINOS_MAX,
        step=0.1, format="%.1f", required=True,
    )  # fmt: skip
    nueva = cargador("bond", COLUMNAS_CICLOS, tabla_inicial())
    if nueva is not None:  # el archivo entra a la tabla editable (clave nueva = tabla nueva)
        st.session_state[BASE_KEY] = nueva
        st.session_state[VER_KEY] = st.session_state.get(VER_KEY, 0) + 1
    ver = st.session_state.get(VER_KEY, 0)
    edited = st.data_editor(st.session_state.get(BASE_KEY, tabla_inicial()),
                            key=TABLE_KEY if ver == 0 else f"{TABLE_KEY}_{ver}",
                            num_rows="dynamic", hide_index=True, column_config={"finos": column},
                            width="stretch")  # fmt: skip
    st.button(t("bond.calc.example"), on_click=_reset)
    finos = [None if pd.isna(x) else float(x) for x in edited["finos"].tolist()]
    problem = validar(valores, finos)
    if problem:
        st.warning(t(problem, lo=MIN_CICLOS, hi=MAX_CICLOS))
        return
    res = calcular(valores, finos)
    if res is None or res.wi is None:
        st.warning(t("bond.err.calculo"))
        return
    frame = cycle_frame(res)
    formats = {1: "%.1f", 2: "%d", 3: "%.1f", 4: "%.1f", 5: "%.1f", 6: "%.4f", 7: "%.1f"}
    config = {frame.columns[i]: st.column_config.NumberColumn(format=f) for i, f in formats.items()}
    st.dataframe(frame, hide_index=True, width="stretch", column_config=config,
                 height=ROW_PX * (len(frame) + 1) + 3)  # fmt: skip
    st.markdown(
        t("bond.calc.res", gbp=es(res.gbp_final, 4), ipp=es(res.ipp_g, 1), wi=es(res.wi, 2))
    )
    if res.termina_en is not None:
        st.markdown(t("bond.calc.fin.si", k=res.termina_en))
    else:
        st.markdown(t("bond.calc.fin.no"))
    st.caption(t("bond.calc.ref", gbp=es(HEBEI_GBP_FINAL, 4), wi=es(HEBEI_WI, 2)))


@st.cache_data(show_spinner=False)
def _caso() -> CasoHebei:
    return caso_hebei()


def mill_image(case: CasoHebei, animate: bool) -> str:
    """El molino de Bond girando a sus rpm reales: 70 rpm = su fracción de la velocidad crítica."""
    frac = velocidad_critica_frac(case.rpm_critica)
    args = (MOLINO_DIAMETRO_M, MOLINO_LARGO_M, case.llenado, frac, BOLA_MAX_MM, 0.0, 0.0)
    lab = (BOLAS_N, BOLAS_KG)
    return as_images(mill_svg(*args, paused=not animate, lab_balls=lab),
                     mill_svg(*args, paused=True, lab_balls=lab), t("bond.sim.alt"))  # fmt: skip


def _row(name_k: str, sim: float, med: float, decimals: int) -> str:
    err = 100.0 * (sim - med) / med
    verdict = t("bond.res.in") if abs(err) <= CORTE_PCT else t("bond.res.out")
    return t("bond.res.row", name=t(name_k), sim=es(sim, decimals), med=es(med, decimals),
             err=es(err, 1), verdict=verdict)  # fmt: skip


def results(case: CasoHebei) -> None:
    sim = case.simulado
    st.markdown(t("bond.h.res", cut=_num(CORTE_PCT)))
    st.markdown("\n".join(f"- {r}" for r in (
        _row("bond.res.gbp", sim.gbp_final, HEBEI_GBP_FINAL, 4),
        _row("bond.res.p80", sim.p80_um, BY_KEY["p80"].default, 1),
        _row("bond.res.wi", sim.wi, HEBEI_WI, 2),
    )))  # fmt: skip
    st.caption(t("bond.res.nota"))


def simulation(animate: bool) -> None:
    case = _caso()
    st.markdown(t("bond.h.sim"))
    st.markdown(t("bond.sim.intro", a=es(case.seleccion.A, 3), alpha=es(case.seleccion.alpha, 3)))
    n = len(case.simulado.ciclos)
    left, right = st.columns(2)
    k = int(
        right.slider(t("bond.sim.cycle"), 1, n, n, help=t("bond.sim.cycle.help"), key=CYCLE_KEY)
    )
    cyc, real = case.simulado.ciclos[k - 1], case.medido.ciclos[k - 1]
    right.markdown(t("bond.sim.cap", k=k, n=n, rev=cyc.revoluciones, rpm=es(MOLINO_RPM, 0),
                     s=es(cyc.revoluciones * 60.0 / MOLINO_RPM, 1), gm=es(real.gbp, 4),
                     gs=es(cyc.gbp, 4), cl=es(cyc.carga_circulante_pct, 1)))  # fmt: skip
    with right:
        results(case)
    left.html(mill_image(case, animate))
    left.caption(t("bond.sim.legend"))
    st.plotly_chart(bond_figure(case.medido, case.simulado), width="stretch")


def bond_tab(animate: bool) -> None:
    ficha()
    calculator()
    simulation(animate)
