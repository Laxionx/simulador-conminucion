"""Gráficos de la app con Plotly. Las animaciones se arman con datos del cálculo (la historia
del reciclo y la granulometría a la salida de cada mezclador del molino) y solo corren cuando el
visitante aprieta «Reproducir»: Plotly las anima en el navegador, no en el servidor."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
from equipos import INK, PAPER, STEEL, STREAM_COLORS, STREAM_NAMES, es

from conminucion.circuits import FRESH, CircuitConfig, CircuitResult
from conminucion.stream import Stream

MAX_FRAMES = 150
FONT = dict(family="Segoe UI, Helvetica, Arial, sans-serif", color=INK, size=13)


def _layout(fig: go.Figure, title: str, xaxis: dict, yaxis: dict, frames: int = 0) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(family="Georgia, serif", size=17)),
        paper_bgcolor=PAPER, plot_bgcolor="#FBF9F4", font=FONT, height=430,
        margin=dict(l=60, r=20, t=60, b=50 if not frames else 140),
        xaxis=dict(gridcolor="#E4DED2", linecolor=STEEL, **xaxis),
        yaxis=dict(gridcolor="#E4DED2", linecolor=STEEL, **yaxis),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )  # fmt: skip
    return fig


def _note(text: str) -> dict:
    return dict(annotations=[dict(
        text=text, x=0.99, y=0.04, xref="paper", yref="paper", showarrow=False, xanchor="right",
        yanchor="bottom",
        font=dict(family="Georgia, serif", size=15, color=INK), bgcolor="rgba(251,249,244,.85)",
    )])  # fmt: skip


def _player(fig: go.Figure, names: list[str], ms: int) -> go.Figure:
    """Botones y deslizador en español. Arranca mostrando el estado final; «Reproducir» lo
    recorre desde el principio. Nada arranca solo."""
    play = dict(frame=dict(duration=ms, redraw=True), fromcurrent=False, mode="immediate",
                transition=dict(duration=0))  # fmt: skip
    pause = dict(frame=dict(duration=0, redraw=False), mode="immediate")
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", direction="left", x=0.0, y=-0.27, xanchor="left", yanchor="top",
            buttons=[dict(label="▶ Reproducir", method="animate", args=[None, play]),
                     dict(label="⏸ Pausa", method="animate", args=[[None], pause])],
        )],
        sliders=[dict(
            x=0.22, y=-0.24, len=0.78, active=len(names) - 1, currentvalue=dict(visible=False),
            steps=[dict(label=n, method="animate",
                        args=[[n], dict(mode="immediate", frame=dict(duration=0, redraw=True))])
                   for n in names],
        )],
    )  # fmt: skip
    return fig


# ------------------------------------------------------------------ convergencia del reciclo
def frame_iterations(n: int) -> list[int]:
    """Iteraciones que se dibujan (1-based): todas si son pocas; si no, salteadas y siempre la
    última, para no mandar cientos de cuadros al navegador."""
    step = max(1, math.ceil(n / MAX_FRAMES))
    its = list(range(1, n + 1, step))
    return its if its[-1] == n else [*its, n]


def convergence_figure(fresh_solids: float, histories: dict[str, list[float]]) -> go.Figure:
    """Carga circulante (underflow / fresca) por iteración, un trazo por método."""
    loads = {k: np.asarray(h) / fresh_solids for k, h in histories.items()}
    n = max(len(v) for v in loads.values())
    colors = {0: STREAM_COLORS["underflow"], 1: STEEL}
    its = frame_iterations(n)

    def traces(k: int) -> list[go.Scatter]:
        out = []
        for i, (label, v) in enumerate(loads.items()):
            m = min(k, len(v))
            out.append(go.Scatter(
                x=list(range(1, m + 1)), y=v[:m].tolist(), mode="lines+markers",
                name=f"{label} ({len(v)} iteraciones)", marker=dict(size=4),
                line=dict(color=colors.get(i, INK), width=2.5),
            ))  # fmt: skip
        return out

    def note(k: int) -> dict:
        return _note(f"Iteración {k}: " + " · ".join(
            f"{label} {es(float(v[min(k, len(v)) - 1]), 3)}" for label, v in loads.items()
        ))  # fmt: skip

    frames = [go.Frame(data=traces(k), name=str(k), layout=note(k)) for k in its]
    fig = go.Figure(data=traces(its[-1]), frames=frames, layout=note(its[-1]))
    ymax = max(float(v.max()) for v in loads.values())
    _layout(fig, "Cómo se llena el reciclo, iteración por iteración",
            dict(title="Iteración", range=[0, n + 1]),
            dict(title="Carga circulante (underflow / fresca)", range=[0, ymax * 1.08]),
            frames=len(frames))  # fmt: skip
    return _player(fig, [str(k) for k in its], ms=60)


# ------------------------------------------------------------------ granulometría por etapa
@dataclass(frozen=True)
class Stage:
    label: str
    stream: str  # para el color
    passing: np.ndarray  # % pasante acumulado por tamiz


def _passing(grid, solids: np.ndarray) -> np.ndarray:
    return 100.0 * Stream(grid, solids, 0.0, 2.7).cumulative_passing


def journey(kind: str, res: CircuitResult, cfg: CircuitConfig) -> list[Stage]:
    """Etapas en el orden en que las recorre el mineral, con la salida de cada mezclador."""
    s = res.streams
    grid = s[FRESH].grid
    mill_in = {"abierto": FRESH, "cerrado_directo": "alim_molino",
               "cerrado_inverso": "underflow"}[kind]  # fmt: skip
    profiles = cfg.mill.mixer_profiles(grid, s[mill_in].solids)
    n = len(profiles)
    mixers = [
        Stage(f"Molino: mezclador {i + 1} de {n}" if n > 1 else "Molino", "descarga_molino",
              _passing(grid, p))
        for i, p in enumerate(profiles)
    ]  # fmt: skip

    def st_(name: str, label: str | None = None) -> Stage:
        return Stage(label or STREAM_NAMES[name], name, 100.0 * s[name].cumulative_passing)

    if kind == "abierto":
        return [st_(FRESH), *mixers[:-1], st_("producto", "Producto (descarga del molino)")]
    if kind == "cerrado_directo":
        return [st_(FRESH), st_("alim_molino"), *mixers[:-1], st_("descarga_molino"),
                st_("underflow"), st_("overflow")]  # fmt: skip
    return [st_(FRESH), st_("alim_ciclon"), st_("underflow"), *mixers[:-1],
            st_("descarga_molino"), st_("overflow")]  # fmt: skip


def journey_figure(stages: list[Stage], sieves: np.ndarray) -> go.Figure:
    """Cada cuadro agrega la etapa siguiente; las anteriores quedan tenues."""
    x = sieves.tolist()

    def traces(k: int) -> list[go.Scatter]:
        """Todas las etapas en cada cuadro (Plotly solo anima trazos que ya existen); las que
        el mineral aún no recorre van vacías."""
        out = []
        for i, stg in enumerate(stages):
            current, reached = i == k, i <= k
            out.append(go.Scatter(
                x=x if reached else [], y=stg.passing.tolist() if reached else [],
                mode="lines+markers", name=stg.label, showlegend=reached,
                line=dict(color=STREAM_COLORS[stg.stream], width=3.5 if current else 1.5),
                marker=dict(size=5 if current else 3), opacity=1.0 if current else 0.35,
            ))  # fmt: skip
        return out

    names = [f"{i + 1}" for i in range(len(stages))]
    notes = [_note(f"Etapa {i + 1} de {len(stages)}: {stg.label}") for i, stg in enumerate(stages)]
    frames = [go.Frame(data=traces(k), name=names[k], layout=notes[k]) for k in range(len(stages))]
    fig = go.Figure(data=traces(len(stages) - 1), frames=frames, layout=notes[-1])
    _layout(fig, "El mineral a lo largo del circuito",
            dict(title="Tamaño (µm)", type="log"),
            dict(title="Pasante acumulado (%)", range=[0, 102]), frames=len(frames))  # fmt: skip
    return _player(fig, names, ms=900)


def passing_figure(streams: dict[str, Stream]) -> go.Figure:
    """Curvas de pasante de todas las corrientes, con los colores de su tipo."""
    fig = go.Figure()
    for name, s in streams.items():
        if s.total_solids > 0:
            fig.add_trace(go.Scatter(
                x=s.grid.sieves.tolist(), y=(100 * s.cumulative_passing).tolist(),
                mode="lines+markers", name=STREAM_NAMES.get(name, name), marker=dict(size=4),
                line=dict(color=STREAM_COLORS.get(name, INK), width=2.5,
                          dash="dot" if name in ("alim_molino", "alim_ciclon") else "solid"),
            ))  # fmt: skip
    return _layout(fig, "Granulometría de cada corriente", dict(title="Tamaño (µm)", type="log"),
                   dict(title="Pasante acumulado (%)", range=[0, 102]))  # fmt: skip
