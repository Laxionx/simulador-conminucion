"""Gráfico animado del «Ensayo de Bond»: el Gbp y la carga circulante de cada ciclo, medidos frente
a simulados. Cada cuadro agrega un ciclo; los datos son los del cálculo (nada se dibuja aparte) y
solo corre cuando el visitante aprieta «Reproducir»."""

from __future__ import annotations

import plotly.graph_objects as go
from animaciones import _layout, _note, _player
from equipos import INK, STEEL, STREAM_COLORS, es
from i18n import t
from plotly.subplots import make_subplots

from conminucion.ensayo_bond import EnsayoSimulado, ResultadoBond

MEDIDO, SIMULADO = STREAM_COLORS["underflow"], STEEL
HEIGHT = 600


def series(medido: ResultadoBond, sim: EnsayoSimulado) -> dict[str, list[float]]:
    """Las cuatro curvas del gráfico, tal como salen del cálculo."""
    return {
        "gbp_med": medido.columna("gbp"),
        "gbp_sim": sim.columna("gbp"),
        "cl_med": medido.columna("carga_circulante_pct"),
        "cl_sim": sim.columna("carga_circulante_pct"),
    }


def _rango(valores: list[float]) -> list[float]:
    lo, hi = min(valores), max(valores)
    pad = 0.08 * (hi - lo or 1.0)
    return [lo - pad, hi + pad]


def bond_figure(medido: ResultadoBond, sim: EnsayoSimulado) -> go.Figure:
    s = series(medido, sim)
    n = len(s["gbp_med"])
    names = {"med": t("bond.plot.med"), "sim": t("bond.plot.sim")}

    def traces(k: int) -> list[go.Scatter]:
        x = list(range(1, k + 1))
        spec = [
            ("gbp_med", "med", MEDIDO, "solid", "y"),
            ("gbp_sim", "sim", SIMULADO, "dash", "y"),
            ("cl_med", "med", MEDIDO, "solid", "y2"),
            ("cl_sim", "sim", SIMULADO, "dash", "y2"),
        ]
        return [
            go.Scatter(
                x=x, y=s[key][:k], mode="lines+markers", name=names[who], marker=dict(size=6),
                line=dict(color=color, width=2.5, dash=dash), xaxis="x" if axis == "y" else "x2",
                yaxis=axis, showlegend=axis == "y", legendgroup=who,
            )
            for key, who, color, dash, axis in spec
        ]  # fmt: skip

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=(t("bond.plot.y1"), t("bond.plot.y2")))  # fmt: skip
    for ann in fig.layout.annotations:  # los títulos de los dos paneles
        ann.update(font=dict(size=13, color=INK), x=0.0, xanchor="left")
    titles = [a.to_plotly_json() for a in fig.layout.annotations]

    def note(k: int) -> dict:
        """Títulos de los paneles y contador de ciclos (un cuadro reemplaza las anotaciones)."""
        text = t("bond.plot.note", k=k, n=n, gm=es(s["gbp_med"][k - 1], 4),
                 gs=es(s["gbp_sim"][k - 1], 4))  # fmt: skip
        return dict(annotations=[*titles, *_note(text)["annotations"]])

    fig.add_traces(traces(n), rows=[1, 1, 2, 2], cols=[1, 1, 1, 1])
    fig.frames = [go.Frame(data=traces(k), traces=[0, 1, 2, 3], name=str(k), layout=note(k))
                  for k in range(1, n + 1)]  # fmt: skip
    _layout(fig, t("bond.plot.title"), dict(range=[0.5, n + 0.5], dtick=1),
            dict(range=_rango(s["gbp_med"] + s["gbp_sim"])), frames=n)  # fmt: skip
    fig.update_layout(height=HEIGHT, margin=dict(l=60, r=20, t=70, b=140),
                      yaxis2=dict(range=_rango(s["cl_med"] + s["cl_sim"]), gridcolor="#E4DED2",
                                  linecolor=STEEL),
                      xaxis2=dict(gridcolor="#E4DED2", linecolor=STEEL, dtick=1,
                                  title=t("bond.plot.x")), **note(n))  # fmt: skip
    return _player(fig, [str(k) for k in range(1, n + 1)], ms=450)
