"""Esquemas animados de los equipos, en SVG. Se arman solo con números del cálculo y textos
fijos: nada que escriba el visitante entra al dibujo. Se muestran como imagen (<img>), así que el
navegador no ejecuta nada de ellos. Con «reducir movimiento» en el sistema se ve la versión quieta.

Lo que sale del cálculo: el giro del tambor (rpm reales: % de la crítica × velocidad crítica),
el área de la carga de bolas (= llenado J), el grosor y la velocidad de cada corriente (sólidos
t/h). Lo ilustrativo, y así se rotula: la inclinación de la carga y el remolino del ciclón.
"""

from __future__ import annotations

import base64
import math
from html import escape

from conminucion.power import critical_speed_rpm
from conminucion.stream import Stream

INK, PAPER, STEEL, STEEL_LIGHT, WATER = "#1F2A30", "#F5F1E8", "#4F5F69", "#A7B3BA", "#3B82A6"
STREAM_COLORS = {
    "alimentacion_fresca": "#B7791F",  # mineral grueso
    "alim_molino": "#8C5A2B",
    "descarga_molino": "#8C5A2B",  # pulpa en molienda
    "alim_ciclon": "#6B5B8C",  # pulpa diluida
    "underflow": "#C0462B",  # gruesos que vuelven
    "overflow": "#1F7A6F",  # producto fino
    "producto": "#1F7A6F",
}
STREAM_NAMES = {
    "alimentacion_fresca": "Alimentación fresca",
    "alim_molino": "Alimentación al molino",
    "descarga_molino": "Descarga del molino",
    "alim_ciclon": "Alimentación al ciclón",
    "underflow": "Descarga del ciclón (gruesos)",
    "overflow": "Rebalse (producto)",
    "producto": "Producto",
}
SANS = "Segoe UI, Helvetica, Arial, sans-serif"
R = ".cm-svg "  # todo el CSS del esquema queda dentro de su raíz
SERIF = "Georgia, 'Times New Roman', serif"
CHARGE_TILT_DEG = 35.0  # ilustrativo
DASH = 36.0  # px que avanza el trazo en un ciclo
LIFTERS = 12  # filas de levantadores por vuelta, en el corte y en el diagrama
STRIPE = 22  # px entre franjas del tambor en el diagrama


def es(x: float, decimals: int = 1) -> str:
    """Número con coma decimal y espacio de miles."""
    return f"{x:,.{decimals}f}".replace(",", " ").replace(".", ",")


def _css(paused: bool) -> str:
    base = (
        f"{R}text{{font-family:{SANS};fill:{INK}}} {R}.cm-t{{font-family:{SERIF};font-weight:700}}"
        f"{R}.cm-flow{{fill:none;stroke-linecap:round}}"
        f"{R}.cm-lbl{{paint-order:stroke;stroke:{PAPER};stroke-width:4px;stroke-linejoin:round}}"
        f"{R}.cm-dash{{fill:none;stroke:#fff;stroke-opacity:.55;stroke-linecap:round}}"
    )
    if paused:
        return base
    return base + (
        "@keyframes cm-spin{to{transform:rotate(360deg)}}"
        f"@keyframes cm-run{{to{{stroke-dashoffset:-{DASH:g}}}}}"
        "@keyframes cm-roll{from{offset-distance:0%}to{offset-distance:100%}}"
        f"@keyframes cm-slide{{to{{transform:translateX({STRIPE}px)}}}}"
        f"{R}.cm-spin{{transform-box:view-box;animation:cm-spin linear infinite}}"
        f"{R}.cm-slide{{animation:cm-slide linear infinite}}"
        f"{R}.cm-dash{{animation:cm-run linear infinite}}"
        f"{R}.cm-ball{{animation:cm-roll ease-in infinite}}"
        f"@media (prefers-reduced-motion: reduce){{{R}*{{animation:none!important}}}}"
    )


def _svg(width: int, height: int, body: str, paused: bool, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="cm-svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(label)}">'
        f"<style>{_css(paused)}</style>"
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>{body}</svg>'
    )


# Una regla de la página elige qué versión se ve: la quieta si el sistema pide reducir movimiento.
MOTION_CSS = (
    "<style>.cm-still{display:none}"
    "@media (prefers-reduced-motion: reduce){.cm-anim{display:none}.cm-still{display:block}}"
    "</style>"
)


def as_images(animated: str, still: str, alt: str) -> str:
    """Las dos versiones del esquema como <img> (data URL): el navegador no ejecuta nada de una
    imagen. Si la animación está apagada, `animated` ya es la versión quieta."""

    def tag(svg: str, cls: str) -> str:
        data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return (
            f'<img class="{cls}" alt="{escape(alt)}" style="width:100%;height:auto" '
            f'src="data:image/svg+xml;base64,{data}">'
        )

    if animated == still:
        return tag(still, "cm-plain")
    return tag(animated, "cm-anim") + tag(still, "cm-still")


def _text(x: float, y: float, s: str, size: int = 13, anchor: str = "start", cls: str = "",
          color: str = INK) -> str:  # fmt: skip
    c = f' class="cm-{cls}"' if cls else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
        f'style="fill:{color}"{c}>{escape(s)}</text>'
    )


def _lines(x: float, y: float, rows: list[tuple[str, int, str, str]]) -> str:
    """Renglones de texto (texto, tamaño, clase, color) uno debajo del otro."""
    out = []
    for text, size, cls, color in rows:
        out.append(_text(x, y, text, size, cls=cls, color=color))
        y += size * 1.45
    return "".join(out)


# ------------------------------------------------------------------ corrientes
def line_width(solids: float, max_solids: float) -> float:
    """Grosor (px) proporcional a los sólidos de la corriente."""
    return 3.0 + 13.0 * (solids / max_solids if max_solids > 0 else 0.0)


def dash_period_s(solids: float, max_solids: float) -> float:
    """Segundos por ciclo del trazo: a más caudal, más rápido."""
    speed = 12.0 + 88.0 * (solids / max_solids if max_solids > 0 else 0.0)  # px/s
    return DASH / speed


def _stream(points: list[tuple[float, float]], name: str, solids: float, max_solids: float,
            paused: bool) -> str:  # fmt: skip
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    w, color = line_width(solids, max_solids), STREAM_COLORS[name]
    dur = "" if paused else f' style="animation-duration:{dash_period_s(solids, max_solids):.3f}s"'
    return (
        f'<path class="cm-flow" d="{d}" stroke="{color}" stroke-width="{w:.2f}" '
        f'stroke-linejoin="round"/>'
        f'<path class="cm-dash" d="{d}" stroke-width="{max(w / 3, 1.5):.2f}" '
        f'stroke-dasharray="6 {DASH - 6:g}"{dur}/>'
    )


# ------------------------------------------------------------------ molino (corte)
def charge_angle(filling: float) -> float:
    """Ángulo central θ (rad) del segmento circular cuya área es la fracción J del círculo:
    θ − sen θ = 2πJ (bisección)."""
    if not 0.0 < filling < 1.0:
        raise ValueError("El llenado debe estar entre 0 y 1")
    lo, hi = 0.0, 2.0 * math.pi
    for _ in range(80):
        mid = (lo + hi) / 2
        if mid - math.sin(mid) < 2.0 * math.pi * filling:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def rotation_period_s(diameter_m: float, speed_frac: float, top_ball_mm: float) -> float:
    """Segundos por vuelta del tambor a la velocidad real."""
    return 60.0 / (speed_frac * critical_speed_rpm(diameter_m, top_ball_mm))


def _segment(cx: float, cy: float, r: float, theta: float, tilt: float) -> tuple[str, tuple]:
    """Camino del segmento de carga (abajo, girado `tilt` rad hacia la izquierda) y los
    extremos de su cuerda (hombro, pie)."""
    half = theta / 2
    a1, a2 = math.pi / 2 + tilt - half, math.pi / 2 + tilt + half  # ángulos en y hacia abajo
    p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    p2 = (cx + r * math.cos(a2), cy + r * math.sin(a2))
    large = 1 if theta > math.pi else 0
    d = f"M {p1[0]:.2f} {p1[1]:.2f} A {r} {r} 0 {large} 1 {p2[0]:.2f} {p2[1]:.2f} Z"
    shoulder, toe = (p2, p1) if p2[1] < p1[1] else (p1, p2)
    return d, (shoulder, toe)


def mill_svg(
    diameter_m: float,
    length_m: float,
    filling: float,
    speed_frac: float,
    top_ball_mm: float,
    power_kw: float,
    balls_t: float,
    paused: bool = False,
) -> str:
    cx, cy, r = 210.0, 205.0, 150.0
    period = rotation_period_s(diameter_m, speed_frac, top_ball_mm)
    rpm = 60.0 / period
    theta = charge_angle(filling)
    seg, (shoulder, toe) = _segment(cx, cy, r - 10, theta, math.radians(CHARGE_TILT_DEG))
    lifters = "".join(
        f'<rect x="{cx - 5:.1f}" y="{cy - r + 2:.1f}" width="10" height="16" fill="{STEEL}" '
        f'transform="rotate({k * 360 / LIFTERS:g} {cx} {cy})"/>'
        for k in range(LIFTERS)
    )
    spin = (
        ""
        if paused
        else f' style="transform-origin:{cx}px {cy}px;animation-duration:{period:.3f}s"'
    )
    balls = "".join(
        f'<circle cx="{x}" cy="{y}" r="7" fill="{STEEL_LIGHT}" stroke="{STEEL}" stroke-width="1"/>'
        for x in range(int(cx - r), int(cx + r), 16)
        for y in range(int(cy - r), int(cy + r), 15)
    )
    path = f"M {shoulder[0]:.1f} {shoulder[1]:.1f} L {toe[0]:.1f} {toe[1]:.1f}"
    falling = "".join(
        f'<circle class="cm-ball" r="7" fill="{STEEL_LIGHT}" stroke="{STEEL}" '
        f"style=\"offset-path:path('{path}');animation-duration:{period / 2:.3f}s;"
        f'animation-delay:-{k * period / 8:.3f}s"/>'
        for k in range(4)
    ) if not paused else ""  # fmt: skip
    body = (
        f'<defs><clipPath id="cm-carga"><path d="{seg}"/></clipPath></defs>'
        f'<circle cx="{cx}" cy="{cy}" r="{r + 12}" fill="{STEEL}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#E4DED2"/>'
        f'<path d="{seg}" fill="#8C5A2B" fill-opacity=".35"/>'
        f'<g clip-path="url(#cm-carga)">{balls}</g>{falling}'
        f'<g class="cm-spin"{spin}>{lifters}'
        f'<circle cx="{cx}" cy="{cy - r - 6}" r="4" fill="{PAPER}"/></g>'
        + _lines(390, 44, [
            ("Molino de bolas, en corte", 28, "t", INK),
            (f"Ø {es(diameter_m)} m × {es(length_m)} m", 21, "", INK),
            (f"Llenado de bolas: {es(100 * filling, 0)} %", 21, "", INK),
            (f"Giro: {es(100 * speed_frac, 0)} % de la crítica", 21, "", INK),
            (f"= {es(rpm)} rpm, una vuelta cada {es(period, 2)} s", 21, "", INK),
            (f"Potencia en el piñón: {es(power_kw, 0)} kW", 23, "t", INK),
            (f"Carga de bolas: {es(balls_t, 0)} t (Bond-Rowland)", 21, "", INK),
        ])
        + _lines(390, 362, [
            ("Esquema, no a escala. Giro y área de la carga:", 16, "", STEEL),
            ("del cálculo. Inclinación y caída: ilustrativas.", 16, "", STEEL),
        ])
    )  # fmt: skip
    return _svg(820, 410, body, paused, "Esquema animado del molino de bolas en corte")


# ------------------------------------------------------------------ hidrociclón
def cyclone_svg(feed: Stream, under: Stream, over: Stream, paused: bool = False) -> str:
    top = max(feed.total_solids, 1e-9)
    swirl = "M 175 80 Q 210 100 245 80 Q 210 120 180 130 Q 210 160 236 170 Q 210 205 196 230 " \
            "Q 210 260 222 280 Q 210 305 204 325"  # fmt: skip
    body = (
        f'<polygon points="160,65 260,65 260,135 160,135" fill="#E4DED2" stroke="{STEEL}" '
        f'stroke-width="4"/>'
        f'<polygon points="160,135 260,135 218,330 202,330" fill="#E4DED2" stroke="{STEEL}" '
        f'stroke-width="4"/>'
        + _stream([(20, 82), (160, 82)], "alim_ciclon", feed.total_solids, top, paused)
        + f'<path d="{swirl}" fill="none" stroke="{STREAM_COLORS["underflow"]}" '
        f'stroke-opacity=".5" stroke-width="3"/>'
        + _stream([(210, 300), (210, 50), (210, 20)], "overflow", over.total_solids, top, paused)
        + _stream([(210, 330), (210, 400)], "underflow", under.total_solids, top, paused)
        + f'<rect x="195" y="40" width="30" height="60" fill="none" stroke="{STEEL}" '
        f'stroke-width="4"/>'
        + _lines(390, 44, [
            ("Hidrociclón", 28, "t", INK),
            (f"Entra: {es(feed.total_solids)} t/h de sólidos", 21, "", INK),
            (f"al {es(feed.pct_solids, 0)} % de sólidos", 21, "", INK),
            (f"Rebalse: {es(over.total_solids)} t/h · P80 {es(over.p80, 0)} µm", 21, "",
             STREAM_COLORS["overflow"]),
            (f"Descarga: {es(under.total_solids)} t/h · P80 {es(under.p80, 0)} µm", 21, "",
             STREAM_COLORS["underflow"]),
            ("Los gruesos bajan por la pared y", 19, "", INK),
            ("salen por el ápice; los finos suben", 19, "", INK),
            ("por el centro y salen por el rebalse.", 19, "", INK),
        ])
        + _lines(390, 362, [
            ("Esquema, no a escala. Grosor y velocidad", 16, "", STEEL),
            ("de las corrientes: t/h. Remolino: ilustrativo.", 16, "", STEEL),
        ])
    )  # fmt: skip
    return _svg(820, 410, body, paused, "Esquema animado del hidrociclón")


# ------------------------------------------------------------------ diagrama de flujo
W, H = 1000, 440
MILL_BOX = (200, 110, 420, 180)  # x0, y0, x1, y1
SUMP_BOX = (480, 280, 560, 360)
CYCLONE = "740,80 830,80 830,130 793,250 777,250 740,130"


def _layout(kind: str) -> dict[str, list[tuple[float, float]]]:
    if kind == "abierto":
        return {"alimentacion_fresca": [(20, 145), (200, 145)],
                "producto": [(420, 145), (980, 145)]}  # fmt: skip
    common = {
        "descarga_molino": [(420, 145), (520, 145), (520, 280)],
        "alim_ciclon": [(560, 340), (680, 340), (680, 105), (740, 105)],
        "overflow": [(785, 80), (785, 40), (985, 40)],
    }
    if kind == "cerrado_directo":
        return common | {
            "alimentacion_fresca": [(20, 145), (170, 145)],
            "alim_molino": [(170, 145), (200, 145)],
            "underflow": [(785, 250), (785, 400), (170, 400), (170, 145)],
        }
    if kind == "cerrado_inverso":
        return common | {
            "alimentacion_fresca": [(20, 320), (480, 320)],
            "underflow": [(785, 250), (785, 400), (130, 400), (130, 145), (200, 145)],
        }
    raise ValueError(f"Circuito desconocido: {kind}")


# Dónde va cada rótulo (x, y de la primera línea, alineación): en zonas libres de cañerías.
LABEL_AT = {
    "alimentacion_fresca": (20, 92, "start"),
    "descarga_molino": (430, 118, "start"),
    "alim_ciclon": (664, 205, "end"),
    "overflow": (845, 66, "start"),
    "underflow": (200, 370, "start"),
    "producto": (440, 118, "start"),
}
LABEL_AT_INVERSO = {"alimentacion_fresca": (220, 290, "start")}


def flowsheet_svg(kind: str, streams: dict[str, Stream], mill_period_s: float,
                  paused: bool = False) -> str:  # fmt: skip
    layout = _layout(kind)
    top = max(s.total_solids for name, s in streams.items() if name in layout)
    x0, y0, x1, y1 = MILL_BOX
    stripes = "".join(
        f'<line x1="{x}" y1="{y0 + 4}" x2="{x}" y2="{y1 - 4}" stroke="{STEEL}" stroke-width="3"/>'
        for x in range(x0 - STRIPE, x1 + STRIPE, STRIPE)
    )
    # Cada franja es una fila de levantadores: pasan LIFTERS por vuelta, al ritmo real.
    slide = "" if paused else (
        f' class="cm-slide" style="animation-duration:{mill_period_s / LIFTERS:.3f}s"'
    )  # fmt: skip
    parts = [
        f'<defs><clipPath id="cm-tambor"><rect x="{x0}" y="{y0}" width="{x1 - x0}" '
        f'height="{y1 - y0}" rx="16"/></clipPath></defs>',
        f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="16" fill="#E4DED2" '
        f'stroke="{STEEL}" stroke-width="4"/>',
        f'<g clip-path="url(#cm-tambor)"><g{slide}>{stripes}</g></g>',
        _text((x0 + x1) / 2, y1 + 22, "Molino de bolas", 14, "middle", "t"),
    ]
    if kind != "abierto":
        sx0, sy0, sx1, sy1 = SUMP_BOX
        parts += [
            f'<rect x="{sx0}" y="{sy0}" width="{sx1 - sx0}" height="{sy1 - sy0}" '
            f'fill="#E4DED2" stroke="{STEEL}" stroke-width="4"/>'
            f'<rect x="{sx0 + 4}" y="{sy0 + 32}" width="{sx1 - sx0 - 8}" height="{sy1 - sy0 - 36}" '
            f'fill="{WATER}" fill-opacity=".35"/>',
            _text((sx0 + sx1) / 2, sy1 + 20, "Cajón y bomba", 14, "middle", "t"),
            f'<polygon points="{CYCLONE}" fill="#E4DED2" stroke="{STEEL}" stroke-width="4"/>',
            _text(845, 170, "Hidrociclón", 14, "start", "t"),
        ]
    for name, points in layout.items():
        parts.append(_stream(points, name, streams[name].total_solids, top, paused))
    labels = LABEL_AT | (LABEL_AT_INVERSO if kind == "cerrado_inverso" else {})
    for name, (x, y, anchor) in labels.items():
        if name in layout:
            s, color = streams[name], STREAM_COLORS[name]
            parts.append(_text(x, y, STREAM_NAMES[name], 13, anchor, "lbl", color))
            parts.append(_text(x, y + 16, f"{es(s.total_solids)} t/h · P80 {es(s.p80, 0)} µm",
                               12, anchor, "lbl", color))  # fmt: skip
    note = (
        "Grosor y velocidad de cada línea: sólidos que lleva (t/h). El tambor gira al ritmo real."
    )
    height = 240 if kind == "abierto" else H  # el abierto no tiene la mitad de abajo
    parts.append(_text(20, height - 8, note, 11, color=STEEL))
    return _svg(W, height, "".join(parts), paused, f"Diagrama de flujo animado: {kind}")
