"""App Streamlit del simulador de conminución: guía, simulación con equipos animados y ajuste, en
español e inglés (`?lang=en`)."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Streamlit Community Cloud instala solo requirements.txt: el paquete se importa desde la raíz,
# y los módulos de la app, desde esta carpeta.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from animaciones import (  # noqa: E402
    convergence_figure,
    journey,
    journey_figure,
    passing_figure,
)
from controles import KNOT_RD, KNOT_SIZES, MillGeometry, sidebar_config  # noqa: E402
from equipos import (  # noqa: E402
    MOTION_CSS,
    as_images,
    cyclone_svg,
    es,
    flowsheet_svg,
    mill_svg,
    rotation_period_s,
    stream_name,
)
from guia import guide_tab  # noqa: E402
from i18n import activate, current, sidebar_selector, t, tr_error  # noqa: E402
from tablas import passing_table, stream_table  # noqa: E402

from conminucion.circuits import FRESH, CircuitConfig, CircuitResult, simulate  # noqa: E402
from conminucion.classifier import EfficiencyCurve  # noqa: E402
from conminucion.fitting import fit_cyclone_partition, fit_mill_knots  # noqa: E402
from conminucion.flowsheet import ConvergenceError  # noqa: E402
from conminucion.mill import BallMill, KnotSelection  # noqa: E402
from conminucion.power import bond_mill_power  # noqa: E402
from conminucion.reconcile import reconcile_node  # noqa: E402
from conminucion.synthetic import (  # noqa: E402
    synthetic_cyclone_survey,
    synthetic_mill_survey,
    synthetic_partition_curve,
)

activate()  # idioma de esta corrida: la sesión o `?lang=` (solo es o en)
st.set_page_config(page_title=t("page.title"), layout="wide")


def _methods() -> dict[bool, str]:
    return {True: t("method.wegstein"), False: t("method.succ")}


def _sci(x: float) -> str:
    """Notación científica con el separador decimal del idioma."""
    out = f"{x:.1e}"
    return out.replace(".", ",") if current() == "es" else out


def _metrics(res: CircuitResult) -> None:
    s = res.streams
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("m.p80"), es(s[res.product].p80, 1))
    c2.metric(t("m.cl"), "-" if res.circulating_load is None else es(res.circulating_load, 3))
    c3.metric(t("m.bond"), es(res.bond_kwh_t, 2))
    c4.metric(t("m.iter"), res.solution.iterations)


def _energy(res: CircuitResult, geom: MillGeometry) -> tuple[float, float]:
    """(kW en el piñón, toneladas de bolas) y la comparación con Bond."""
    power = bond_mill_power(geom.diameter_m, geom.length_m, geom.filling, geom.speed,
                            geom.top_ball_mm)  # fmt: skip
    available = power.kw / res.streams[FRESH].total_solids
    need = res.bond_kwh_t
    c1, c2 = st.columns(2)
    c1.metric(t("e.avail"), es(available, 2), help=t("e.avail.help"))
    c2.metric(t("e.need"), es(need, 2), help=t("e.need.help"))
    verdict = t("e.yes") if available >= need else t("e.no")
    ratio = es(available / need if need else float("nan"), 2)
    st.caption(t("e.caption", verdict=verdict, ratio=ratio))
    return power.kw, power.balls_t


def _convergence(kind: str, cfg: CircuitConfig, res: CircuitResult, wegstein: bool) -> None:
    methods = _methods()
    histories = {methods[wegstein]: res.solution.tear_history}
    try:
        other = simulate(kind, cfg, wegstein=not wegstein)
        histories[methods[not wegstein]] = other.solution.tear_history
    except ConvergenceError:
        st.caption(t("conv.noconv", method=methods[not wegstein]))
    fresh = res.streams[FRESH].total_solids
    st.plotly_chart(convergence_figure(fresh, histories), width="stretch")
    st.caption(t("conv.caption"))


def simulation_tab(kind: str, cfg: CircuitConfig, wegstein: bool, geom: MillGeometry,
                   res: CircuitResult, flowsheet: str, animate: bool) -> None:  # fmt: skip
    s = res.streams
    _metrics(res)
    st.html(flowsheet)
    st.markdown(t("sim.h.energy"))
    kw, balls = _energy(res, geom)
    st.markdown(t("sim.h.equip"))
    left, right = st.columns(2)
    args = (geom.diameter_m, geom.length_m, geom.filling, geom.speed, geom.top_ball_mm, kw, balls)
    left.html(as_images(mill_svg(*args, paused=not animate), mill_svg(*args, paused=True),
                        t("sim.alt.mill")))  # fmt: skip
    if kind != "abierto":
        flows = (s["alim_ciclon"], s["underflow"], s["overflow"])
        right.html(as_images(cyclone_svg(*flows, not animate), cyclone_svg(*flows, True),
                             t("sim.alt.cyclone")))  # fmt: skip
    st.plotly_chart(journey_figure(journey(kind, res, cfg), s[FRESH].grid.sieves),
                    width="stretch")  # fmt: skip
    st.caption(t("sim.journey"))
    if kind != "abierto":
        _convergence(kind, cfg, res, wegstein)
    st.markdown(t("sim.h.streams"))
    left, right = st.columns([3, 2])
    left.plotly_chart(passing_figure(s), width="stretch")
    table = res.table()
    shown = table.assign(corriente=table["corriente"].map(stream_name))
    right.dataframe(stream_table(shown).round(3), hide_index=True)
    bal = res.balance
    right.caption(
        t("sim.balance", in_=es(bal["solidos_in"], 3), out=es(bal["solidos_out"], 3),
          err=_sci(bal["error_solidos"]), water=es(bal["agua_agregada"], 2))
    )  # fmt: skip
    d1, d2 = st.columns(2)
    d1.download_button(
        t("sim.dl.streams"), stream_table(table).to_csv(index=False), "corrientes.csv"
    )
    d2.download_button(
        t("sim.dl.passing"), passing_table(res.passing_table()).to_csv(index=False), "pasantes.csv"
    )


def ci_table(fit, truth) -> pd.DataFrame:
    rows = [
        {
            t("ci.param"): n,
            t("ci.true"): truth_value,
            t("ci.est"): v,
            t("ci.lo"): lo,
            t("ci.hi"): hi,
            t("ci.in"): ok,
        }
        for (n, (v, lo, hi)), truth_value, ok in zip(
            fit.as_dict().items(), truth, fit.contains(truth), strict=True
        )
    ]
    return pd.DataFrame(rows).round(4)


def fitting_tab(cfg: CircuitConfig) -> None:
    st.markdown(t("fit.intro"))
    c1, c2, c3 = st.columns(3)
    seed = int(c1.number_input(t("fit.seed"), 0, 10_000, 1))
    sigma = c2.number_input(t("fit.sigma"), 0.001, 0.1, 0.02, 0.005)
    rel = c3.number_input(t("fit.rel"), 0.0, 0.2, 0.05, 0.01)
    grid = cfg.fresh.grid
    truth = (cfg.classifier.d50c, cfg.classifier.alpha, cfg.classifier.rf)

    st.subheader(t("fit.h1"))
    x, y = synthetic_partition_curve(grid, cfg.classifier, sigma, seed)
    fit = fit_cyclone_partition(x, y)
    st.dataframe(ci_table(fit, truth), hide_index=True)
    fig, ax = plt.subplots(figsize=(6, 3.6))
    xs = np.geomspace(grid.sizes[-1], grid.sizes[0], 200)
    ax.scatter(x, y, s=18, label=t("fit.measured"))
    ax.plot(xs, EfficiencyCurve(*fit.values).efficiency(xs), label=t("fit.fitted"))
    ax.plot(xs, cfg.classifier.efficiency(xs), "--", label=t("fit.true"))
    ax.set(xscale="log", xlabel=t("fit.xlabel"), ylabel=t("fit.ylabel"))
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

    st.subheader(t("fit.h2"))
    try:
        sim = simulate("cerrado_directo", cfg, wegstein=True)
    except ConvergenceError as exc:
        st.warning(t("fit.warn", exc=tr_error(str(exc))))
    else:
        sv = synthetic_cyclone_survey(sim.streams["alim_ciclon"], cfg.classifier, rel, seed=seed)
        rc = reconcile_node(sv.feed, sv.underflow, sv.overflow)
        true_cl = sim.circulating_load
        st.write(
            t("fit.write", true_r=es(sv.true_r, 4), rec_r=es(rc.r_underflow, 4),
              true_cl=es(true_cl, 3), rec_cl=es(rc.circulating_load, 3), chi2=es(rc.chi2, 2))
        )  # fmt: skip
        st.caption(t("fit.cap"))

    st.subheader(t("fit.h3"))
    true_mill = BallMill(KnotSelection(KNOT_SIZES, KNOT_RD), cfg.mill.fracture, cfg.mill.n_mixers)
    fm, pm = synthetic_mill_survey(grid, cfg.fresh.fractions, true_mill, rel_noise=rel, seed=seed)
    mfit = fit_mill_knots(grid, fm, pm, KNOT_SIZES, cfg.mill.fracture, cfg.mill.n_mixers)
    st.dataframe(ci_table(mfit, KNOT_RD), hide_index=True)


def main() -> None:
    sidebar_selector()
    st.title(t("app.title"))
    st.caption(t("app.caption"))
    st.html(MOTION_CSS)
    kind, cfg, wegstein, geom = sidebar_config()
    animate = st.toggle(t("toggle.label"), value=True, help=t("toggle.help"))
    try:
        res, error = simulate(kind, cfg, wegstein=wegstein), None
    except ConvergenceError as exc:
        res, error = None, exc
    sheets: dict[str, str | None] = {"guia": None, "sim": None}
    if res is not None:
        period = rotation_period_s(geom.diameter_m, geom.speed, geom.top_ball_mm)
        still = flowsheet_svg(kind, res.streams, period, True)
        moving = flowsheet_svg(kind, res.streams, period, not animate)
        sheets = {tag: as_images(moving, still, t("sim.alt.flow")) for tag in sheets}
    tab_guide, tab_sim, tab_fit = st.tabs([t("tab.guide"), t("tab.sim"), t("tab.fit")])
    with tab_guide:
        guide_tab(kind, sheets["guia"])
    with tab_sim:
        if res is None:
            st.error(tr_error(str(error)))
        else:
            simulation_tab(kind, cfg, wegstein, geom, res, sheets["sim"], animate)
    with tab_fit:
        fitting_tab(cfg)


main()
