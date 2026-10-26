"""Curvas (Plotly) de la pestaña «Chancado primario»: la granulometría de cada corriente del
circuito y la capacidad del chancador según las rpm o según el CSS. Todo sale del cálculo; el
único dato externo son los puntos de la Tabla 3.1 de King (en `datos_mandibula`)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from animaciones import _layout
from equipos import INK, STEEL, STREAM_COLORS
from i18n import t
from mandibula_datos import MM, Calculo, maquina_king

from conminucion.mandibula import taggart_tph
from conminucion.stream import Stream

PUNTOS = 60
EJES = ("rpm", "css")
RPM_DESDE, RPM_HASTA = 0.4, 1.7  # × N
NARANJA, VERDE, AZUL = "#D55E00", "#009E73", "#0072B2"


def _curva(fig: go.Figure, s: Stream, nombre: str, color: str, dash: str = "solid") -> None:
    if s.total_solids <= 0:
        return
    fig.add_scatter(
        x=(s.grid.sieves / MM).tolist(), y=(100.0 * s.cumulative_passing).tolist(), name=nombre,
        mode="lines+markers", marker=dict(size=4), line=dict(color=color, width=2.4, dash=dash),
    )  # fmt: skip


def granulometria_fig(c: Calculo) -> go.Figure:
    """Pasante acumulado (%) de cada corriente (eje logarítmico) y el CSS y OSS efectivos."""
    fig = go.Figure()
    _curva(fig, c.mina, t("jaw.plot.mina"), STREAM_COLORS["alimentacion_fresca"])
    if c.pasante is not None:
        _curva(fig, c.pasante, t("jaw.plot.pasante"), VERDE, "dot")
    _curva(fig, c.carga, t("jaw.plot.carga"), STREAM_COLORS["alim_molino"], "dash")
    _curva(fig, c.prod_chancador, t("jaw.plot.prod"), STEEL)
    _curva(fig, c.producto, t("jaw.plot.total"), INK)
    for x, name in ((c.jaw.css_eff_mm, "css"), (c.jaw.oss_mm, "oss")):
        fig.add_vline(x=x, line=dict(color=NARANJA, width=1.6, dash="dashdot"),
                      annotation_text=t(f"jaw.plot.{name}"), annotation_position="top",
                      annotation_font=dict(size=12, color=NARANJA))  # fmt: skip
    _layout(fig, t("jaw.plot.gran.title"),
            dict(type="log", title=t("jaw.plot.gran.x")),
            dict(title=t("jaw.plot.gran.y"), range=[0, 102]))  # fmt: skip
    return fig


def _capacidad_rpm(c: Calculo) -> tuple[list[float], list[float]]:
    j = c.jaw
    xs = np.linspace(RPM_DESDE * j.rpm, RPM_HASTA * j.rpm, PUNTOS)
    return xs.tolist(), [j.with_(rpm=float(r)).capacity_tph() for r in xs]


def _capacidad_css(c: Calculo) -> tuple[list[float], list[float]]:
    j = c.jaw
    tope = j.gape_mm - j.stroke - j.wear_mm - 2.0  # el OSS debe quedar bajo la boca
    xs = np.linspace(min(5.0, tope / 2.0), tope, PUNTOS)
    return xs.tolist(), [j.with_(css_mm=float(x)).capacity_tph() for x in xs]


def capacidad_fig(c: Calculo, eje: str) -> go.Figure:
    """Capacidad volumétrica del modelo según las rpm o según el CSS, con el punto de operación, la
    alimentación que llega y el límite por potencia. En el eje CSS agrega los puntos de la Tabla 3.1
    de King (si el equipo es uno de los 12) y la fórmula de Taggart."""
    if eje not in EJES:
        raise ValueError(f"Eje desconocido {eje!r}")
    j = c.jaw
    fig = go.Figure()
    por_rpm = eje == "rpm"
    xs, ys = _capacidad_rpm(c) if por_rpm else _capacidad_css(c)
    fig.add_scatter(x=xs, y=ys, mode="lines", name=t("jaw.plot.cap.modelo"),
                    line=dict(color=INK, width=2.6))  # fmt: skip
    x0 = j.rpm if por_rpm else j.css_mm
    fig.add_scatter(x=[x0], y=[j.capacity_tph()], mode="markers", name=t("jaw.plot.cap.punto"),
                    marker=dict(size=13, color=NARANJA, symbol="diamond",
                                line=dict(color=INK, width=1.5)))  # fmt: skip
    fig.add_hline(y=c.carga.total_solids, line=dict(color=STREAM_COLORS["underflow"], width=1.8,
                  dash="dash"), annotation_text=t("jaw.plot.cap.llega"),
                  annotation_position="top left")  # fmt: skip
    limite = j.motor_limit_tph(c.carga, c.prod_chancador)
    if np.isfinite(limite):
        fig.add_hline(y=limite, line=dict(color=VERDE, width=1.8, dash="dot"),
                      annotation_text=t("jaw.plot.cap.potencia"),
                      annotation_position="bottom right")  # fmt: skip
    if por_rpm:
        fig.add_vline(x=j.critical_rpm, line=dict(color=NARANJA, width=1.6, dash="dashdot"),
                      annotation_text=t("jaw.plot.cap.nc"),
                      annotation_position="top right")  # fmt: skip
        x_title = t("jaw.plot.cap.x.rpm")
    else:
        fig.add_scatter(
            x=xs, y=[taggart_tph(j.width_mm, x + j.wear_mm + j.stroke) for x in xs], mode="lines",
            name=t("jaw.plot.cap.taggart"), line=dict(color=AZUL, width=2, dash="dash"),
        )  # fmt: skip
        maq = maquina_king(c.v)
        if maq is not None:
            pts = sorted(maq.capacidad_tph.items())
            fig.add_scatter(
                x=[oss - j.stroke - j.wear_mm for oss, _ in pts], y=[q for _, q in pts],
                mode="markers", name=t("jaw.plot.cap.king"),
                marker=dict(size=10, color=VERDE, symbol="square", line=dict(color=INK, width=1)),
            )  # fmt: skip
        x_title = t("jaw.plot.cap.x.css")
    _layout(fig, t("jaw.plot.cap.title"), dict(title=x_title),
            dict(title=t("jaw.plot.cap.y"), rangemode="tozero"))  # fmt: skip
    return fig
