"""App Streamlit del simulador de conminución: guía, simulación con equipos animados y ajuste."""

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
    STREAM_NAMES,
    as_images,
    cyclone_svg,
    es,
    flowsheet_svg,
    mill_svg,
    rotation_period_s,
)
from guia import guide_tab  # noqa: E402

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

st.set_page_config(page_title="Simulador de conminución", layout="wide")
METHODS = {True: "Wegstein", False: "Sustitución sucesiva"}


def _metrics(res: CircuitResult) -> None:
    s = res.streams
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("P80 del producto (µm)", f"{s[res.product].p80:.1f}")
    c2.metric(
        "Carga circulante", "-" if res.circulating_load is None else f"{res.circulating_load:.3f}"
    )
    c3.metric("Energía de Bond (kWh/t)", f"{res.bond_kwh_t:.2f}")
    c4.metric("Iteraciones", res.solution.iterations)


def _energy(res: CircuitResult, geom: MillGeometry) -> tuple[float, float]:
    """(kW en el piñón, toneladas de bolas) y la comparación con Bond."""
    power = bond_mill_power(geom.diameter_m, geom.length_m, geom.filling, geom.speed,
                            geom.top_ball_mm)  # fmt: skip
    available = power.kw / res.streams[FRESH].total_solids
    need = res.bond_kwh_t
    c1, c2 = st.columns(2)
    c1.metric("Energía que entrega el molino (kWh/t)", es(available, 2),
              help="Potencia de Bond-Rowland dividida por las t/h frescas.")  # fmt: skip
    c2.metric(
        "Energía que pide Bond para este P80 (kWh/t)",
        es(need, 2),
        help="W = 10 Wi (1/√P80 − 1/√F80), sin factores de eficiencia de Rowland.",
    )
    verdict = "alcanza" if available >= need else "no alcanza"
    st.caption(
        f"Según Bond, el molino **{verdict}** para moler hasta este P80 "
        f"({es(available / need if need else float('nan'), 2)} veces lo pedido). Chequeo grueso: "
        "la cinética del molino (τ, selección) no depende de su potencia en este modelo."
    )
    return power.kw, power.balls_t


def _convergence(kind: str, cfg: CircuitConfig, res: CircuitResult, wegstein: bool) -> None:
    histories = {METHODS[wegstein]: res.solution.tear_history}
    try:
        other = simulate(kind, cfg, wegstein=not wegstein)
        histories[METHODS[not wegstein]] = other.solution.tear_history
    except ConvergenceError:
        st.caption(f"{METHODS[not wegstein]} no converge en 500 iteraciones con estos datos.")
    fresh = res.streams[FRESH].total_solids
    st.plotly_chart(convergence_figure(fresh, histories), width="stretch")
    st.caption(
        "El reciclo arranca vacío. Cada iteración pasa el mineral por el molino y el ciclón y "
        "devuelve más gruesos, hasta que lo que vuelve ya no cambia: eso es la carga "
        "circulante final."
    )


def simulation_tab(kind: str, cfg: CircuitConfig, wegstein: bool, geom: MillGeometry,
                   res: CircuitResult, flowsheet: str, animate: bool) -> None:  # fmt: skip
    s = res.streams
    _metrics(res)
    st.html(flowsheet)
    st.markdown("#### Energía del molino")
    kw, balls = _energy(res, geom)
    st.markdown("#### Los equipos por dentro")
    left, right = st.columns(2)
    args = (geom.diameter_m, geom.length_m, geom.filling, geom.speed, geom.top_ball_mm, kw, balls)
    left.html(as_images(mill_svg(*args, paused=not animate), mill_svg(*args, paused=True),
                        "Molino de bolas en corte"))  # fmt: skip
    if kind != "abierto":
        flows = (s["alim_ciclon"], s["underflow"], s["overflow"])
        right.html(as_images(cyclone_svg(*flows, not animate), cyclone_svg(*flows, True),
                             "Hidrociclón"))  # fmt: skip
    st.plotly_chart(journey_figure(journey(kind, res, cfg), s[FRESH].grid.sieves),
                    width="stretch")  # fmt: skip
    st.caption("Aprieta «Reproducir»: cada paso agrega una etapa del recorrido, incluida la "
               "salida de cada mezclador del molino.")  # fmt: skip
    if kind != "abierto":
        _convergence(kind, cfg, res, wegstein)
    st.markdown("#### Corrientes")
    left, right = st.columns([3, 2])
    left.plotly_chart(passing_figure(s), width="stretch")
    table = res.table()
    shown = table.assign(corriente=table["corriente"].map(lambda n: STREAM_NAMES.get(n, n)))
    right.dataframe(shown.round(3), hide_index=True)
    bal = res.balance
    right.caption(
        f"Balance: sólidos in {bal['solidos_in']:.3f} / out {bal['solidos_out']:.3f} t/h "
        f"(error {bal['error_solidos']:.1e}); agua agregada {bal['agua_agregada']:.2f} t/h."
    )
    d1, d2 = st.columns(2)
    d1.download_button("Exportar corrientes (CSV)", table.to_csv(index=False), "corrientes.csv")
    d2.download_button(
        "Exportar pasantes (CSV)", res.passing_table().to_csv(index=False), "pasantes.csv"
    )


def ci_table(fit, truth) -> pd.DataFrame:
    rows = [
        {
            "parámetro": n,
            "verdadero": t,
            "estimado": v,
            "IC95 inf": lo,
            "IC95 sup": hi,
            "dentro del IC": ok,
        }
        for (n, (v, lo, hi)), t, ok in zip(
            fit.as_dict().items(), truth, fit.contains(truth), strict=True
        )
    ]
    return pd.DataFrame(rows).round(4)


def fitting_tab(cfg: CircuitConfig) -> None:
    st.markdown(
        "Muestreo de planta **sintético**: se generan datos con parámetros conocidos más ruido "
        "gaussiano y se comprueba que el ajuste los recupera dentro de su IC al 95 % "
        "(covarianza del jacobiano de `least_squares`)."
    )
    c1, c2, c3 = st.columns(3)
    seed = int(c1.number_input("Semilla", 0, 10_000, 1))
    sigma = c2.number_input("Ruido de la partición (σ absoluta)", 0.001, 0.1, 0.02, 0.005)
    rel = c3.number_input("Ruido relativo de granulometrías", 0.0, 0.2, 0.05, 0.01)
    grid = cfg.fresh.grid
    truth = (cfg.classifier.d50c, cfg.classifier.alpha, cfg.classifier.rf)

    st.subheader("1. Ciclón: curva de partición medida")
    x, y = synthetic_partition_curve(grid, cfg.classifier, sigma, seed)
    fit = fit_cyclone_partition(x, y)
    st.dataframe(ci_table(fit, truth), hide_index=True)
    fig, ax = plt.subplots(figsize=(6, 3.6))
    xs = np.geomspace(grid.sizes[-1], grid.sizes[0], 200)
    ax.scatter(x, y, s=18, label="medido (sintético)")
    ax.plot(xs, EfficiencyCurve(*fit.values).efficiency(xs), label="ajustado")
    ax.plot(xs, cfg.classifier.efficiency(xs), "--", label="verdadero")
    ax.set(xscale="log", xlabel="Tamaño (µm)", ylabel="Partición al underflow")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("2. Reconciliación del nodo del ciclón")
    try:
        sim = simulate("cerrado_directo", cfg, wegstein=True)
    except ConvergenceError as exc:
        st.warning(f"El circuito cerrado directo no se puede reconciliar con estos datos: {exc}")
    else:
        sv = synthetic_cyclone_survey(sim.streams["alim_ciclon"], cfg.classifier, rel, seed=seed)
        rc = reconcile_node(sv.feed, sv.underflow, sv.overflow)
        true_cl = sim.circulating_load
        st.write(
            f"Fracción de sólidos al underflow: verdadera {sv.true_r:.4f}, reconciliada "
            f"{rc.r_underflow:.4f}. Carga circulante: verdadera {true_cl:.3f}, "
            f"reconciliada {rc.circulating_load:.3f} (χ² ponderado {rc.chi2:.2f})."
        )
        st.caption(
            "La partición derivada de datos reconciliados tiene errores heterocedásticos; "
            "sus IC por jacobiano pueden ser optimistas (ver README)."
        )

    st.subheader("3. Molino: r/d por nudos desde alimentación y descarga")
    true_mill = BallMill(KnotSelection(KNOT_SIZES, KNOT_RD), cfg.mill.fracture, cfg.mill.n_mixers)
    fm, pm = synthetic_mill_survey(grid, cfg.fresh.fractions, true_mill, rel_noise=rel, seed=seed)
    mfit = fit_mill_knots(grid, fm, pm, KNOT_SIZES, cfg.mill.fracture, cfg.mill.n_mixers)
    st.dataframe(ci_table(mfit, KNOT_RD), hide_index=True)


def main() -> None:
    st.title("Simulador de circuitos de molienda y clasificación")
    st.caption(
        "Construido desde ecuaciones publicadas (Whiten, Austin, Lynch-Rao, Bond). Empieza por "
        "la **Guía**; los datos se cambian en la barra lateral."
    )
    st.html(MOTION_CSS)
    kind, cfg, wegstein, geom = sidebar_config()
    animate = st.toggle(
        "Mover los equipos", value=True,
        help="Apaga las animaciones de los esquemas. También se apagan solas si el sistema "
        "tiene activado «reducir movimiento».",
    )  # fmt: skip
    try:
        res, error = simulate(kind, cfg, wegstein=wegstein), None
    except ConvergenceError as exc:
        res, error = None, exc
    sheets: dict[str, str | None] = {"guia": None, "sim": None}
    if res is not None:
        period = rotation_period_s(geom.diameter_m, geom.speed, geom.top_ball_mm)
        still = flowsheet_svg(kind, res.streams, period, True)
        moving = flowsheet_svg(kind, res.streams, period, not animate)
        sheets = {tag: as_images(moving, still, "Diagrama de flujo del circuito") for tag in sheets}
    tab_guide, tab_sim, tab_fit = st.tabs(
        ["Guía", "Simulación", "Ajuste a datos (muestreo sintético)"]
    )
    with tab_guide:
        guide_tab(kind, sheets["guia"])
    with tab_sim:
        if res is None:
            st.error(str(error))
        else:
            simulation_tab(kind, cfg, wegstein, geom, res, sheets["sim"], animate)
    with tab_fit:
        fitting_tab(cfg)


main()
