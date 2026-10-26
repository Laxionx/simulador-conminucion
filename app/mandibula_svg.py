"""Esquema animado del chancador de mandíbula (corte lateral, toggle simple) y mini gráfico de la
abertura de descarga, en SVG. Se arman solo con números del cálculo y textos fijos: nada que escriba
el visitante entra al dibujo. Se muestran como imagen (<img>), así que el navegador no ejecuta nada.

Sale del cálculo: la cámara a escala (boca G, altura D, CSS y OSS efectivos, ángulo θ), el período
del vaivén y del volante (60/N s, dividido por la velocidad de la vista), la parrilla (abertura a
escala) y las rocas: 120 cuantiles de masa de la granulometría que llega al chancador (cada una vale
1/120 de la masa), cada una a la altura de la cámara donde su tamaño iguala la abertura local, con
la forma y el color de su clase de tamaño. Ilustrativo, y así se rotula: la amplificación de la
carrera, la velocidad de la animación y la vibración de la parrilla.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from html import escape

from equipos import (
    INK,
    PAPER,
    STEEL,
    STEEL_LIGHT,
    _css,
    _lines,
    _stream,
    _text,
    es,
)
from i18n import t
from mandibula_datos import Calculo
from mandibula_rocas import (
    CLASS_KEYS,
    FINOS,
    PRODUCTO,
    ROCAS,
    Roca,
    dibujar,
    dibujar_marcas,
    forma,
    fracciones_clases,
    marcas_de_correa,
    rocas_de_camara,
)

W, H = 900, 650
MAX_H_PX, MAX_W_PX = 300.0, 200.0  # espacio de la cámara en el dibujo
XF, Y0, Y_CORREA = 340.0, 200.0, 590.0
JAW_W, JAW_EXT, FLY_R = 40.0, 36.0, 44.0
VIEW_FULL, VIEW_DETAIL = "completo", "detalle"
VIEWS = (VIEW_FULL, VIEW_DETAIL)
AMP_RANGE, SPEED_RANGE = (1.0, 8.0), (5, 100)
IDS = ("jw-boca", "jw-altura", "jw-css", "jw-oss")
ARCO_R = 34.0  # radio del arco del ángulo de mordida; la θ va a ARCO_R + 10
SOLO = "#8A3B12"  # color de la nota «solo cambia el dibujo»


@dataclass(frozen=True)
class Geometria:
    """La cámara en píxeles. Cerrada: la mandíbula móvil en el CSS efectivo (a escala)."""

    s: float  # px por mm
    xf: float
    y0: float
    yb: float
    xm: float  # boca arriba (x de la mandíbula móvil, cerrada)
    xc: float  # abertura de abajo, cerrada
    apex_y: float  # donde se cortan las dos caras de la cámara
    phi_deg: float  # giro de la mandíbula móvil hacia abierto (carrera × amplificación)
    pivot: tuple[float, float]


def escala(gape_mm: float, height_mm: float) -> float:
    return min(MAX_H_PX / height_mm, MAX_W_PX / gape_mm)


def periodo_s(rpm: float, speed_pct: float) -> float:
    """Segundos por ciclo en el dibujo: 60/N dividido por el factor de velocidad de la vista."""
    return 60.0 / rpm / (speed_pct / 100.0)


def _giro_deg(pivot: tuple[float, float], p: tuple[float, float], dx: float) -> float:
    """Ángulo (SVG, grados) que desplaza dx en x al punto p al girar en torno a pivot."""
    rx, ry = p[0] - pivot[0], p[1] - pivot[1]
    nx = max(-math.hypot(rx, ry) + 1e-9, min(math.hypot(rx, ry) - 1e-9, rx + dx))
    ny = math.copysign(math.sqrt(max(rx * rx + ry * ry - nx * nx, 0.0)), ry)
    return math.degrees(math.atan2(ny, nx) - math.atan2(ry, rx))


def geometria(c: Calculo, amp: float) -> Geometria:
    j = c.jaw
    s = escala(j.gape_mm, j.height)
    yb = Y0 + j.height * s
    xm, xc = XF + j.gape_mm * s, XF + j.css_eff_mm * s
    yt = Y0 - JAW_EXT
    xt = xm + (xm - xc) * JAW_EXT / (yb - Y0)
    pivot = (xt + JAW_W / 2.0, yt + 12.0)
    phi = _giro_deg(pivot, (xc, yb), amp * j.stroke * s)
    apex = yb + j.css_eff_mm * j.height / (j.gape_mm - j.css_eff_mm) * s
    return Geometria(s, XF, Y0, yb, xm, xc, apex, phi, pivot)


# ------------------------------------------------------------------ piezas
def _poly(pts: list[tuple[float, float]], fill: str, extra: str = "") -> str:
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{p}" fill="{fill}" stroke="{STEEL}" stroke-width="2.5" {extra}/>'


def _jaw_pts(g: Geometria) -> list[tuple[float, float]]:
    yt = g.y0 - JAW_EXT
    xt = g.xm + (g.xm - g.xc) * JAW_EXT / (g.yb - g.y0)
    return [(xt, yt), (g.xc, g.yb), (g.xc + JAW_W, g.yb), (xt + JAW_W, yt)]


def _zigzag(x0: float, x1: float, y: float, turns: int = 8, amp: float = 7.0) -> str:
    step = (x1 - x0) / (2 * turns)
    pts = [(x0, y)] + [(x0 + step * (2 * i + 1), y + (-amp if i % 2 else amp))
                       for i in range(2 * turns - 1)] + [(x1, y)]  # fmt: skip
    return "M " + " L ".join(f"{x:.1f} {yy:.1f}" for x, yy in pts)


def _linea(x1: float, y1: float, x2: float, y2: float, extra: str = "") -> str:
    return f'<line {extra}x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{INK}"/>'


def _dim(x1: float, y1: float, x2: float, y2: float, ident: str) -> str:
    """Cota con topes: horizontal si y1 = y2, y si no, vertical."""
    d = (0.0, 4.0) if abs(y1 - y2) < 1e-9 else (4.0, 0.0)  # topes perpendiculares a la cota
    return (
        _linea(x1, y1, x2, y2, f'id="{ident}" stroke-width="1.6" ')
        + _linea(x1 - d[0], y1 - d[1], x1 + d[0], y1 + d[1])
        + _linea(x2 - d[0], y2 - d[1], x2 + d[0], y2 + d[1])
    )


def _animacion(g: Geometria, period: float, sx: dict[str, float]) -> str:
    """Reglas CSS propias del esquema (dentro de .cm-svg): vaivén, toggle y resorte."""
    ox, oy = g.pivot
    out = (
        f".cm-svg .jw-swing{{transform-box:view-box;transform-origin:{ox:.1f}px {oy:.1f}px;"
        f"animation:jw-swing {period:.3f}s ease-in-out infinite}}"
        f"@keyframes jw-swing{{0%,100%{{transform:rotate(0deg)}}"
        f"50%{{transform:rotate({g.phi_deg:.3f}deg)}}}}"
        f".cm-svg .jw-vib{{animation:jw-vib {min(period / 6.0, 0.25):.3f}s linear infinite}}"
        "@keyframes jw-vib{0%,100%{transform:translateY(0)}50%{transform:translateY(1.6px)}}"
    )
    for name, factor in sx.items():
        out += (
            f".cm-svg .jw-{name}{{transform-box:view-box;animation:jw-{name} {period:.3f}s "
            f"ease-in-out infinite}}@keyframes jw-{name}{{0%,100%{{transform:scaleX(1)}}"
            f"50%{{transform:scaleX({factor:.4f})}}}}"
        )
    return f"<style>{out}</style>"


def _punto_girado(
    pivot: tuple[float, float], p: tuple[float, float], deg: float
) -> tuple[float, float]:
    a = math.radians(deg)
    rx, ry = p[0] - pivot[0], p[1] - pivot[1]
    return pivot[0] + rx * math.cos(a) - ry * math.sin(a), pivot[1] + rx * math.sin(
        a
    ) + ry * math.cos(a)


def _vista(g: Geometria, view: str) -> tuple[float, float, float, float]:
    if view == VIEW_FULL:
        return 0.0, 0.0, float(W), float(H)
    return g.xc - 150.0, g.yb - 160.0, 490.0, 372.0  # el detalle incluye una franja de leyenda


def jaw_svg(c: Calculo, amp: float, speed_pct: float, view: str = VIEW_FULL,
            paused: bool = False) -> str:  # fmt: skip
    """Corte del chancador. `amp` (1–8): la carrera se dibuja ×amp; `speed_pct` (5–100): velocidad
    de la animación. Los dos solo cambian el dibujo (se rotula en él)."""
    if view not in VIEWS:
        raise ValueError(f"Vista desconocida {view!r}")
    j, g = c.jaw, geometria(c, amp)
    period = periodo_s(j.rpm, speed_pct)
    px, py = g.pivot
    jaw = _jaw_pts(g)
    openg = [_punto_girado(g.pivot, p, g.phi_deg) for p in jaw]
    # toggle (abajo) y barra tensora con resorte (más arriba), anclados en la pared trasera
    qy_t, qy_r = g.yb - 14.0, g.yb - 14.0 - 0.26 * (g.yb - g.y0)
    face = lambda y: g.xc + JAW_W + (g.xm - g.xc) * (g.yb - y) / (g.yb - g.y0)  # noqa: E731
    wall = g.xc + JAW_W + 118.0
    ant = {"tog": (face(qy_t), qy_t), "rod": (face(qy_r), qy_r)}
    sx = {}
    for name, q in ant.items():
        dx = _punto_girado(g.pivot, q, g.phi_deg)[0] - q[0]
        sx[name] = max((wall - q[0] - dx) / (wall - q[0]), 0.2)
    body = [
        _animacion(g, period, sx) if not paused else "",
        # pared trasera y bastidor
        f'<rect x="{wall:.1f}" y="{g.yb - 0.4 * (g.yb - g.y0) - 30:.1f}" width="34" '
        f'height="{0.4 * (g.yb - g.y0) + 60:.1f}" fill="{STEEL}"/>',
        _poly(
            [
                (g.xf - 70, g.y0 - 40),
                (g.xf - 34, g.y0 - 40),
                (g.xf - 34, g.yb + 24),
                (g.xf - 70, g.yb + 24),
            ],
            STEEL_LIGHT,
        ),  # fmt: skip
        _poly(
            [(g.xf - 34, g.y0 - 40), (g.xf, g.y0), (g.xf, g.yb), (g.xf - 34, g.yb + 24)], STEEL
        ),  # fmt: skip
        # cámara: contorno de la mandíbula móvil cerrada (a escala) y abierta (carrera × amp)
        _poly(openg, "none", 'stroke-dasharray="5 4" stroke-opacity=".6"'),
        # toggle, barra tensora y resorte (se estiran con el vaivén)
        f'<g class="jw-tog" style="transform-origin:{wall:.1f}px {qy_t:.1f}px">'
        f'<rect x="{ant["tog"][0]:.1f}" y="{qy_t - 6:.1f}" width="{wall - ant["tog"][0]:.1f}" '
        f'height="12" rx="3" fill="{INK}"/></g>',
        f'<g class="jw-rod" style="transform-origin:{wall:.1f}px {qy_r:.1f}px">'
        f'<path d="{_zigzag(ant["rod"][0] + 12, wall - 12, qy_r)}" fill="none" stroke="{INK}" '
        f'stroke-width="2.5"/><line x1="{ant["rod"][0]:.1f}" y1="{qy_r:.1f}" '
        f'x2="{ant["rod"][0] + 12:.1f}" y2="{qy_r:.1f}" stroke="{INK}" stroke-width="3"/>'
        f'<line x1="{wall - 12:.1f}" y1="{qy_r:.1f}" x2="{wall:.1f}" y2="{qy_r:.1f}" '
        f'stroke="{INK}" stroke-width="3"/></g>',
        # mandíbula móvil colgada del eje excéntrico, con el volante
        f'<g class="jw-swing">{_poly(jaw, "#C9C1B0")}'
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{FLY_R}" fill="#E4DED2" stroke="{STEEL}" '
        f'stroke-width="3"/></g>',
        f'<g class="cm-spin" style="transform-origin:{px:.1f}px {py:.1f}px;'
        f'animation-duration:{period:.3f}s">'
        + "".join(
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px + FLY_R * math.cos(a):.1f}" '
            f'y2="{py + FLY_R * math.sin(a):.1f}" stroke="{STEEL}" stroke-width="4"/>'
            for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)
        )
        + f'<circle cx="{px + FLY_R * 0.62:.1f}" cy="{py:.1f}" r="7" fill="{INK}"/></g>'
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="{INK}"/>',
    ]
    body += _parrilla_y_flujos(c, g, paused)
    body.append(dibujar(rocas_de_camara(c, g.xf, g.yb, g.s, reservadas(c, g)), "rock"))
    body += _rocas_correa(c, g)
    body.append(_cotas(c, g))
    body.append(_textos(c, g, amp, speed_pct, period, wall, qy_t, qy_r, view == VIEW_FULL))
    x, y, w, h = _vista(g, view)
    if view == VIEW_DETAIL:  # una franja propia, tapa la parte baja, con la leyenda y la nota
        sy = g.yb + 92.0  # la franja tapa lo que hay bajo la descarga
        body.append(
            f'<rect x="{x:.1f}" y="{sy:.1f}" width="{w:.1f}" height="{y + h - sy:.1f}" '
            f'fill="{PAPER}"/>'
        )
        body.append(_leyenda(c, x + 14.0, sy + 16.0, horizontal=True, ancho=235.0))
        solo = t("jaw.svg.solo", a=es(amp, 0), v=es(speed_pct, 0)) + " " + t("jaw.svg.solo2")
        body.append(_text(x + 14.0, y + h - 10.0, solo, 11, "start", "lbl", SOLO))
    css = _css(paused)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="cm-svg" viewBox="{x:.1f} {y:.1f} {w:.1f} '
        f'{h:.1f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{t("jaw.svg.label")}">'
        f"<style>{css}</style>"
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PAPER}"/>{"".join(body)}</svg>'
    )


def _rocas_correa(c: Calculo, g: Geometria) -> list[str]:
    """Sobre la correa, TODAS las marcas: los finos de la parrilla (aguas arriba) y el producto del
    chancador (bajo la descarga), en filas ordenadas, sin escala ni descarte."""
    xg, mid = g.xf - 140.0, g.xf + (g.xc - g.xf) / 2.0
    fin = []
    if c.pasante is not None:
        fin = marcas_de_correa(c, c.pasante, FINOS, xg - 62.0, Y_CORREA)
    prod = marcas_de_correa(c, c.prod_chancador, PRODUCTO, mid + 14.0, Y_CORREA)
    return [dibujar_marcas(fin, "fin"), dibujar_marcas(prod, "prod")]


def reservadas(c: Calculo, g: Geometria) -> tuple[Roca, ...]:
    """La caja del arco y de la θ: ninguna roca de la cámara se dibuja encima."""
    return (Roca(0.0, 0, g.xf, g.apex_y - ARCO_R * 0.95, ARCO_R * 0.95),)


def _parrilla(c: Calculo, g: Geometria, xg: float, top: float, paused: bool) -> list[str]:
    """Tolva, parrilla (plataforma inclinada de barras sobre su bastidor), chute de finos."""
    x0, y_a = g.xf - 230.0, g.y0 - 112.0
    xs, y_s = g.xf - 80.0, g.y0 - 82.0  # fin de la zona con abertura
    xb, y_b = g.xf + 6.0, g.y0 - 56.0  # borde que entrega a la boca
    ap = c.parrilla.aperture_mm * g.s  # abertura a escala
    pitch = 8.0 + ap

    def riel(x: float) -> float:
        return y_a + (y_s - y_a) * (x - x0) / (xs - x0)

    n = max(int((xs - x0) / pitch), 2)
    barras = "".join(
        f'<rect x="{x0 + i * pitch:.1f}" y="{riel(x0 + i * pitch) - 13:.1f}" width="8" '
        f'height="13" fill="{INK}"/>'
        for i in range(n)
    )
    deck = (
        f'<g id="jw-parrilla" class="{"" if paused else "jw-vib"}">{barras}'
        f'<line x1="{x0}" y1="{y_a}" x2="{xs}" y2="{y_s}" stroke="{INK}" stroke-width="5"/>'
        f'<line x1="{x0}" y1="{y_a + 10}" x2="{xs}" y2="{y_s + 10}" stroke="{STEEL}" '
        f'stroke-width="4"/>'
        f'<line x1="{xs}" y1="{y_s}" x2="{xb}" y2="{y_b}" stroke="{INK}" stroke-width="5"/>'
        f"</g>"
    )
    fall = "".join(
        f'<line x1="{x:.1f}" y1="{riel(x) + 12:.1f}" x2="{x:.1f}" y2="{riel(x) + 34:.1f}" '
        f'stroke="#1F7A6F" stroke-width="2" stroke-dasharray="3 4"/>'
        for x in (x0 + 25.0, x0 + 80.0, x0 + 130.0)
    )
    yf = y_a + 96.0  # fondo del embudo
    chute = (
        f'<polyline points="{x0},{y_a + 38} {xg - 9},{yf} {xg - 9},{Y_CORREA - 6}" fill="none" '
        f'stroke="{STEEL}" stroke-width="4"/>'
        f'<polyline points="{xs},{y_s + 40} {xg + 9},{yf} {xg + 9},{Y_CORREA - 6}" fill="none" '
        f'stroke="{STEEL}" stroke-width="4"/>'
    )
    tolva = (
        f'<polygon points="{x0 - 46},{y_a - 78} {x0 + 46},{y_a - 78} {x0 + 18},{y_a - 24} '
        f'{x0 - 18},{y_a - 24}" fill="#E4DED2" stroke="{STEEL}" stroke-width="3"/>'
    )
    out = [tolva, chute, deck, fall]
    mina, carga = c.mina.total_solids, c.carga.total_solids
    out.append(_stream([(x0, y_a - 86), (x0, y_a - 50)], "alimentacion_fresca", mina, top, paused))
    out.append(_stream([(x0, y_a - 26), (x0 + 12, y_a - 4)], "alimentacion_fresca", mina, top,
                       paused))  # fmt: skip
    out.append(_stream([(xb - 6, y_b + 2), (g.xf + 14, g.y0 - 16), (g.xf + 14, g.y0 - 4)],
                       "alimentacion_fresca", carga, top, paused))  # fmt: skip
    if c.pasante is not None:
        out.append(_stream([(xg, yf - 14), (xg, Y_CORREA - 8)], "producto",
                           c.pasante.total_solids, top, paused))  # fmt: skip
    return out


def _parrilla_y_flujos(c: Calculo, g: Geometria, paused: bool) -> list[str]:
    top = max(c.mina.total_solids, 1e-9)
    xg = g.xf - 140.0
    mid = g.xf + (g.xc - g.xf) / 2.0
    if c.parrilla is None:
        out = [_stream([(g.xf - 60, g.y0 - 110), (g.xf + 14, g.y0 - 30), (g.xf + 14, g.y0 - 6)],
                       "alimentacion_fresca", c.mina.total_solids, top, paused)]  # fmt: skip
    else:
        out = _parrilla(c, g, xg, top, paused)
    out.append(_stream([(mid, g.yb + 2), (mid, Y_CORREA - 8)], "producto",
                       c.prod_chancador.total_solids, top, paused))  # fmt: skip
    out.append(
        f'<rect x="{xg - 70:.0f}" y="{Y_CORREA}" width="{620 - xg + 70:.0f}" height="16" '
        f'rx="8" fill="{STEEL}"/>'
    )
    return out


def _text_rot(x: float, y: float, s: str, color: str = INK) -> str:
    """Texto vertical (girado −90°), centrado en (x, y)."""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" text-anchor="middle" class="cm-lbl" '
        f'style="fill:{color}" transform="rotate(-90 {x:.1f} {y:.1f})">{escape(s)}</text>'
    )


def _guia(x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{STEEL}" '
        f'stroke-width="1" stroke-dasharray="3 3"/>'
    )


def _cotas(c: Calculo, g: Geometria) -> str:
    j = c.jaw
    oss = g.xf + (j.css_eff_mm + j.stroke) * g.s
    r = ARCO_R
    ang = math.atan2(g.xc - g.xm, g.yb - g.y0)  # inclinación de la cara móvil
    ax, ay = g.xf, g.apex_y
    p1, p2 = (ax, ay - r), (ax - r * math.sin(ang), ay - r * math.cos(ang))
    arc = f"M {p1[0]:.1f} {p1[1]:.1f} A {r} {r} 0 0 0 {p2[0]:.1f} {p2[1]:.1f}"
    xl = g.xf + 64.0  # los rótulos de CSS y OSS van a un lado, con su línea guía
    tx, ty = ax - (r + 10) * math.sin(ang / 2), ay - (r + 10) * math.cos(ang / 2)
    return (
        _dim(g.xf, g.y0 - 8, g.xm, g.y0 - 8, IDS[0])
        + _dim(g.xf - 96, g.y0, g.xf - 96, g.yb, IDS[1])
        + _dim(g.xf, g.yb + 18, g.xc, g.yb + 18, IDS[2])
        + _dim(g.xf, g.yb + 34, oss, g.yb + 34, IDS[3])
        + _guia(g.xc + 3, g.yb + 18, xl - 3, g.yb + 18)
        + _guia(oss + 3, g.yb + 34, xl - 3, g.yb + 34)
        + f'<path d="{arc}" fill="none" stroke="{INK}" stroke-width="1.4"/>'
        + _text(
            g.xf + (g.xm - g.xf) / 2,
            g.y0 - 14,
            t("jaw.svg.g", v=es(j.gape_mm, 0)),
            13,
            "middle",
            "lbl",
        )  # fmt: skip
        + _text_rot(g.xf - 102, (g.y0 + g.yb) / 2, t("jaw.svg.d", v=es(j.height, 0)))
        + _text(xl, g.yb + 22, t("jaw.svg.css", v=es(j.css_eff_mm, 1)), 12, "start", "lbl")
        + _text(xl, g.yb + 38, t("jaw.svg.oss", v=es(j.oss_mm, 1)), 12, "start", "lbl")
        + _text(tx, ty, "θ", 13, "middle", "lbl")
    )


def _bloque(c: Calculo, s, titulo: str, x: float, y: float, size: int, paso: float) -> str:
    """Un bloque de la leyenda: título y una línea por clase (forma y color en la marca; el texto,
    en tinta, para que se lea sobre el fondo) con el % de la masa de esa corriente."""
    frac = fracciones_clases(c, s)
    out = [_text(x, y, t(titulo), size, "start", "t", INK)]
    for i, k in enumerate(CLASS_KEYS):
        cy = y + (i + 1) * paso
        out.append(forma(i, x + 6.0, cy - 4.0, 6.0, 0, "leg", 0.0, marca=True))
        out.append(_text(x + 20.0, cy, t(f"jaw.svg.leg.{k}", p=es(100 * frac[i], 1)), size,
                         "start", "", INK))  # fmt: skip
    return "".join(out)


def _leyenda(c: Calculo, x: float, y: float, horizontal: bool = False, ancho: float = 0.0,
             size: int = 12, paso: float = 17.0) -> str:  # fmt: skip
    """La ÚNICA leyenda, en dos bloques: la alimentación a la cámara y el producto en la correa."""
    x2, y2 = (x + ancho, y) if horizontal else (x, y + 5 * paso + 8.0)
    return _bloque(c, c.carga, "jaw.svg.leg.camara", x, y, size, paso) + _bloque(
        c, c.prod_chancador, "jaw.svg.leg.correa", x2, y2, size, paso
    )


def _textos(c: Calculo, g: Geometria, amp: float, speed_pct: float, period: float,
            wall: float, qy_t: float, qy_r: float, info: bool) -> str:  # fmt: skip
    j = c.jaw
    x0, y_a, xg = g.xf - 230.0, g.y0 - 112.0, g.xf - 140.0
    lx = wall + 46.0  # los rótulos de la pared trasera van a la derecha, con su guía
    ap_y = g.y0 + 110.0
    abertura = j.css_eff_mm + (j.gape_mm - j.css_eff_mm) * (g.yb - ap_y) / (j.height * g.s)
    x_in = g.xf + abertura * g.s / 2.0
    names = [
        (g.pivot[0] + 12, g.pivot[1] + FLY_R + 18, "jaw.svg.volante", "start"),
        (lx, qy_t + 4, "jaw.svg.toggle", "start"),
        (lx, qy_r + 4, "jaw.svg.barra", "start"),
        (lx, ap_y + 4, "jaw.svg.camara", "start"),
        (x0 + 60, y_a - 14, "jaw.svg.parrilla", "start"),
        (xg - 16, y_a + 170, "jaw.svg.finos", "end"),
        (g.xf - 195, Y_CORREA + 32, "jaw.svg.correa", "start"),
    ]
    out = "".join(_text(x, y, t(k), 12, a, "lbl", STEEL) for x, y, k, a in names)
    out += _guia(wall + 36, qy_t, lx - 4, qy_t) + _guia(wall + 36, qy_r, lx - 4, qy_r)
    out += _guia(x_in, ap_y, lx - 4, ap_y)
    out += _text_rot(g.xf - 52, (g.y0 + g.yb) / 2, t("jaw.svg.fija"), INK)
    bloque = ""
    if info:  # el bloque de información y la leyenda solo van en el corte completo
        bloque = _lines(650, 40, [
            (t("jaw.svg.title"), 18, "t", INK),
            (t("jaw.svg.dims", g=es(j.gape_mm, 0), w=es(j.width_mm, 0)), 14, "", INK),
            (t("jaw.svg.rpm", rpm=es(j.rpm, 0), p=es(60.0 / j.rpm, 3)), 14, "", INK),
            (t("jaw.svg.view", p=es(period, 2), v=es(speed_pct, 0)), 14, "", INK),
            (t("jaw.svg.stroke", l=es(j.stroke, 1), a=es(amp, 0)), 14, "", INK),
            (t("jaw.svg.theta", v=es(j.bite_angle_deg, 1)), 14, "", INK),
            (t("jaw.svg.solo", a=es(amp, 0), v=es(speed_pct, 0)), 12, "", SOLO),
            (t("jaw.svg.solo2"), 12, "", SOLO),
        ])  # fmt: skip
        n = len(rocas_de_camara(c, g.xf, g.yb, g.s, reservadas(c, g)))
        fin = FINOS if c.pasante is not None else 0
        bloque += _leyenda(c, 706.0, 236.0)
        bloque += _lines(650, 535, [
            (t("jaw.svg.note1", n=n, m=ROCAS), 12, "", STEEL),
            (t("jaw.svg.note2"), 12, "", STEEL),
            (t("jaw.svg.note3", a=PRODUCTO), 12, "", STEEL),
            (t("jaw.svg.note4", b=fin), 12, "", STEEL),
        ])  # fmt: skip
    prod = t("jaw.svg.prodtot", t=es(c.producto.total_solids, 0), p=es(c.p80, 1))
    return out + bloque + _text(350, Y_CORREA + 32, prod, 12, "start", "lbl", INK)


# ------------------------------------------------------------------ abertura en el tiempo
def abertura_svg(css_mm: float, oss_mm: float, rpm: float, speed_pct: float,
                 paused: bool = False) -> str:  # fmt: skip
    """Abertura de descarga en 2 ciclos: oscila entre el CSS efectivo y el OSS (a escala)."""
    w, h, x0, x1, ytop, ybot = 480, 170, 110.0, 460.0, 36.0, 118.0
    period = periodo_s(rpm, speed_pct)

    def y_of(mm: float) -> float:
        return ybot - (mm - css_mm) / max(oss_mm - css_mm, 1e-9) * (ybot - ytop)

    pts = [(x0 + (x1 - x0) * i / 80.0,
            y_of(css_mm + (oss_mm - css_mm) * (1 - math.cos(2 * math.pi * 2 * i / 80.0)) / 2.0))
           for i in range(81)]  # fmt: skip
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    dot = (
        ""
        if paused
        else (
            f'<circle r="5" fill="#D55E00" stroke="{INK}" class="cm-ball" style="offset-path:'
            f"path('{d}');animation-duration:{2 * period:.3f}s;animation-timing-function:linear\"/>"
        )
    )
    body = (
        f'<line x1="{x0}" y1="{ytop}" x2="{x1}" y2="{ytop}" stroke="{STEEL}" '
        f'stroke-dasharray="4 4"/>'
        f'<line x1="{x0}" y1="{ybot}" x2="{x1}" y2="{ybot}" stroke="{STEEL}" '
        f'stroke-dasharray="4 4"/>'
        f'<path id="jw-curva" d="{d}" fill="none" stroke="{INK}" stroke-width="2.4"/>{dot}'
        + _text(x0 - 6, ytop + 4, t("jaw.svg.oss", v=es(oss_mm, 1)), 11, "end")
        + _text(x0 - 6, ybot + 4, t("jaw.svg.css", v=es(css_mm, 1)), 11, "end")
        + _text((x0 + x1) / 2, 18, t("jaw.svg.ab.title"), 14, "middle", "t")
        + _text(
            (x0 + x1) / 2,
            152,
            t("jaw.svg.ab.x", s=es(2 * 60.0 / rpm, 2), n=es(rpm, 0)),
            12,
            "middle",
            color=STEEL,
        )  # fmt: skip
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="cm-svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{t("jaw.svg.ab.label")}">'
        f'<style>{_css(paused)}</style><rect width="{w}" height="{h}" fill="{PAPER}"/>{body}</svg>'
    )
