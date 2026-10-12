"""App Streamlit del simulador de conminución: simulación de circuitos y ajuste a datos."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Streamlit Community Cloud instala solo requirements.txt: el paquete se importa desde la raíz.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conminucion.circuits import KINDS, CircuitConfig, simulate  # noqa: E402
from conminucion.classifier import EfficiencyCurve
from conminucion.fitting import fit_cyclone_partition, fit_mill_knots
from conminucion.flowsheet import ConvergenceError
from conminucion.fracture import Fracture
from conminucion.mill import AustinSelection, BallMill, KnotSelection
from conminucion.reconcile import reconcile_node
from conminucion.sizes import SizeGrid, gaudin_schuhmann, rosin_rammler
from conminucion.stream import Stream
from conminucion.synthetic import (
    synthetic_cyclone_survey,
    synthetic_mill_survey,
    synthetic_partition_curve,
)

st.set_page_config(page_title="Simulador de conminución", layout="wide")

LABELS = {
    "abierto": "Molino en circuito abierto",
    "cerrado_directo": "Circuito cerrado directo",
    "cerrado_inverso": "Circuito cerrado inverso",
}
KNOT_SIZES = (4750.0, 1187.0, 297.0, 74.0)
KNOT_RD = (0.9, 1.6, 1.0, 0.35)


def sidebar_config() -> tuple[str, CircuitConfig, bool]:
    """Lee los controles de la barra lateral y arma la configuración del circuito."""
    sb = st.sidebar
    kind = sb.selectbox("Preset de circuito", KINDS, index=1, format_func=LABELS.get)
    sb.subheader("Tamices y alimentación")
    top = sb.number_input("Tamiz superior (µm)", 1000.0, 50000.0, 9500.0, 500.0)
    n = sb.slider("Número de tamices", 8, 24, 17)
    grid = SizeGrid.geometric(top, n)
    tph = sb.number_input("Sólidos frescos (t/h)", 1.0, 5000.0, 100.0)
    rho = sb.number_input("Densidad de sólidos (t/m³)", 1.0, 8.0, 2.7, 0.1)
    water = sb.number_input("Agua en la alimentación (t/h)", 0.0, 5000.0, 0.0)
    dist = sb.radio("Distribución", ["Rosin-Rammler", "Gaudin-Schuhmann"], horizontal=True)
    if dist == "Rosin-Rammler":
        x63 = sb.number_input("x63 (µm)", 100.0, 40000.0, 3200.0)
        m = sb.number_input("m", 0.2, 5.0, 1.0, 0.1)
        fr = rosin_rammler(grid, x63, m)
    else:
        k = sb.number_input("k (µm)", 100.0, 60000.0, 12000.0)
        a = sb.number_input("α", 0.2, 3.0, 0.8, 0.05)
        fr = gaudin_schuhmann(grid, k, a)
    fresh = Stream.from_fractions(grid, fr, tph, water, rho)

    sb.subheader("Molino de bolas")
    param = sb.radio("Parametrización de r/d", ["Austin (S, τ)", "Nudos r/d"], horizontal=True)
    if param.startswith("Austin"):
        sel = AustinSelection(
            sb.number_input("A (1/min)", 0.01, 10.0, 0.8, 0.1),
            sb.number_input("α (selección)", 0.1, 3.0, 0.9, 0.1),
            sb.number_input("μ (µm)", 100.0, 20000.0, 2500.0, 100.0),
            sb.number_input("Λ", 0.5, 10.0, 3.0, 0.5),
            sb.number_input("τ (min)", 0.1, 60.0, 3.0, 0.5),
        )
    else:
        rds = [
            sb.number_input(f"r/d @ {s:g} µm", 0.001, 20.0, v)
            for s, v in zip(KNOT_SIZES, KNOT_RD, strict=True)
        ]
        sel = KnotSelection(KNOT_SIZES, tuple(rds))
    frac = Fracture(
        sb.slider("φ (fractura)", 0.0, 1.0, 0.6, 0.05),
        sb.slider("γ", 0.2, 2.0, 0.8, 0.05),
        sb.slider("β", 1.0, 6.0, 3.5, 0.1),
    )
    mill = BallMill(
        sel,
        frac,
        sb.slider("Mezcladores en serie", 1, 8, 1),
        sb.number_input("Agua de adición al molino (t/h)", 0.0, 1000.0, 0.0),
    )

    sb.subheader("Clasificador (hidrociclón)")
    cls = EfficiencyCurve(
        sb.number_input("d50c (µm)", 5.0, 5000.0, 100.0, 10.0),
        sb.number_input("α (nitidez)", 0.5, 10.0, 3.0, 0.5),
        sb.slider("Rf (bypass de agua)", 0.0, 0.9, 0.2, 0.05),
    )
    pct = sb.slider("% sólidos alimentación al ciclón", 20, 70, 45)
    wi = sb.number_input("Wi de Bond (kWh/t)", 5.0, 30.0, 14.0, 0.5)
    wegstein = sb.checkbox("Aceleración de Wegstein", value=True)
    return kind, CircuitConfig(fresh, mill, cls, float(pct), wi), wegstein


def passing_plot(streams: dict[str, Stream]) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for name, s in streams.items():
        if s.total_solids > 0:
            ax.plot(s.grid.sieves, 100 * s.cumulative_passing, marker="o", ms=3, label=name)
    ax.set(xscale="log", xlabel="Tamaño (µm)", ylabel="Pasante acumulado (%)", ylim=(0, 102))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def simulation_tab(kind: str, cfg: CircuitConfig, wegstein: bool) -> None:
    try:
        res = simulate(kind, cfg, wegstein=wegstein)
    except ConvergenceError as exc:
        st.error(str(exc))
        return
    s = res.streams
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("P80 del producto (µm)", f"{s[res.product].p80:.1f}")
    c2.metric(
        "Carga circulante", "-" if res.circulating_load is None else f"{res.circulating_load:.3f}"
    )
    c3.metric("Energía de Bond (kWh/t)", f"{res.bond_kwh_t:.2f}")
    c4.metric("Iteraciones", res.solution.iterations)
    left, right = st.columns([3, 2])
    left.pyplot(passing_plot(s))
    table = res.table()
    right.dataframe(table.round(3), hide_index=True)
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
    st.caption("Construido desde ecuaciones publicadas (Whiten, Austin, Lynch-Rao, Bond).")
    kind, cfg, wegstein = sidebar_config()
    tab_sim, tab_fit = st.tabs(["Simulación", "Ajuste a datos (muestreo sintético)"])
    with tab_sim:
        simulation_tab(kind, cfg, wegstein)
    with tab_fit:
        fitting_tab(cfg)


main()
