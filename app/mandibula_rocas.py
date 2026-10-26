"""Las rocas del esquema del chancador: cuantiles de masa, clase de tamaño, forma irregular
determinista y colocación sin encimarse. Todo sale del cálculo; no hay azar.

Una roca de tamaño x (mm) se dibuja con diámetro 0,85·x·escala, en la altura de la cámara donde la
abertura local (CSS + (G − CSS)·y/D) iguala a x. Las rocas se recorren de mayor a menor y se salta
la que se cruzaría con una ya dibujada: por eso se dibujan n ≤ 120 de los 120 cuantiles.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from equipos import INK
from mandibula_datos import MM, Calculo

from conminucion.datos_mandibula import COLPA_FRACCION_BOCA
from conminucion.mandibula import pasante_en
from conminucion.sizes import size_at_passing
from conminucion.stream import Stream

ROCAS, PRODUCTO, FINOS = 120, 30, 12  # cuantiles de la carga, del producto y de los finos
AJUSTE = 0.85  # diámetro de la roca / abertura local
CLASS_COLORS = ("#56B4E9", "#E69F00", "#009E73", "#D55E00")  # Okabe-Ito
CLASS_KEYS = ("fino", "css_oss", "grueso", "colpa")
VERTICES = (4, 5, 6, 8)  # la clase también se distingue por su forma y su borde
BORDES = ("3 2", "", "", "")  # trazos del borde: la clase fina va a trazos
GROSOR = (1.0, 1.0, 1.0, 3.0)
MARGEN = 1.5  # px entre las cajas de dos rocas


def clase_de(size_mm: float, css_eff_mm: float, oss_mm: float, gape_mm: float) -> int:
    """0 ≤ CSS · 1 entre CSS y OSS · 2 mayor que el OSS · 3 colpa (> 0,8·boca)."""
    if size_mm > COLPA_FRACCION_BOCA * gape_mm:
        return 3
    return 0 if size_mm <= css_eff_mm else 1 if size_mm <= oss_mm else 2


def cuantiles(s: Stream, n: int) -> list[float]:
    """Tamaños (mm) de n rocas: los cuantiles de masa (i+½)/n de la corriente, de menor a mayor."""
    if s.total_solids <= 0:
        return []
    return [size_at_passing(s.grid, s.solids, (i + 0.5) / n) / MM for i in range(n)]


def fracciones_clases(c: Calculo, s: Stream | None = None) -> list[float]:
    """Fracción de la masa de la corriente `s` (por defecto, la que llega al chancador) en cada
    clase (suma 1)."""
    j, f = c.jaw, c.carga if s is None else s
    p = [pasante_en(f, x * MM) for x in (j.css_eff_mm, j.oss_mm, COLPA_FRACCION_BOCA * j.gape_mm)]
    return [p[0], p[1] - p[0], p[2] - p[1], 1.0 - p[2]]


def _azar(i: int, j: int) -> float:
    """Número determinista en [0, 1) a partir de dos enteros."""
    x = math.sin(i * 12.9898 + j * 78.233) * 43758.5453
    return x - math.floor(x)


def puntos(k: int, cx: float, cy: float, r: float, semilla: int,
           irregular: float = 0.2) -> list[tuple[float, float]]:  # fmt: skip
    """Polígono de VERTICES[k] vértices, con radios entre (1 − irregular)·r y r."""
    n = VERTICES[k]
    giro = _azar(semilla, 0) * 2.0 * math.pi
    return [
        (
            cx
            + r
            * (1 - irregular + irregular * _azar(semilla, i + 1))
            * math.cos(giro + 2 * math.pi * i / n),
            cy
            + r
            * (1 - irregular + irregular * _azar(semilla, i + 1))
            * math.sin(giro + 2 * math.pi * i / n),
        )
        for i in range(n)
    ]


def forma(k: int, cx: float, cy: float, r: float, semilla: int, clase: str, mm: float,
          marca: bool = False) -> str:  # fmt: skip
    """Una roca: polígono irregular con el color, los vértices y el borde de su clase."""
    pts = puntos(k, cx, cy, r, semilla, 0.0 if marca else 0.2)  # las marcas son regulares
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    trazo = f' stroke-dasharray="{BORDES[k]}"' if BORDES[k] else ""
    return (
        f'<polygon class="{clase} {clase}-{k}" data-mm="{mm:.2f}" points="{p}" '
        f'fill="{CLASS_COLORS[k]}" fill-opacity="{1 if marca else 0.8}" stroke="{INK}" '
        f'stroke-width="{GROSOR[k]}"{trazo}/>'
    )


@dataclass(frozen=True)
class Roca:
    size_mm: float
    clase: int
    cx: float
    cy: float
    r: float


def _cruza(a: Roca, b: Roca) -> bool:
    return (
        abs(a.cx - b.cx) < a.r + b.r + MARGEN and abs(a.cy - b.cy) < a.r + b.r + MARGEN
    )  # cajas (cuadrados de lado 2r) que se tocan


def sin_encimar(candidatas: list[Roca], ocupadas: list[Roca] | None = None) -> list[Roca]:
    """Las candidatas, en el orden dado, que no se cruzan con una aceptada ni con `ocupadas`."""
    aceptadas = list(ocupadas or [])
    nuevas = []
    for r in candidatas:
        if not any(_cruza(r, o) for o in aceptadas):
            aceptadas.append(r)
            nuevas.append(r)
    return nuevas


def rocas_de_camara(c: Calculo, xf: float, yb: float, s: float,
                    reservadas: tuple[Roca, ...] = ()) -> list[Roca]:  # fmt: skip
    """Las rocas de la carga que caben sin encimarse, de mayor a menor. Las que pasan por la
    abertura (≤ CSS) se dibujan cayendo bajo ella, en fila."""
    j = c.jaw
    cands = []
    caen = 0
    for x in sorted(cuantiles(c.carga, ROCAS), reverse=True):
        k = clase_de(x, j.css_eff_mm, j.oss_mm, j.gape_mm)
        r = max(AJUSTE * x * s / 2.0, 1.5)
        if x <= j.css_eff_mm:
            caen += 1
            cx = xf + max(j.css_eff_mm * s, 2 * r) / 2.0
            cands.append(Roca(x, k, cx, yb + 8.0 + 2 * r * caen, r))
        else:
            cy = yb - j.height * (x - j.css_eff_mm) / (j.gape_mm - j.css_eff_mm) * s
            cands.append(Roca(x, k, xf + x * s / 2.0, cy, r))
    return sin_encimar(cands, list(reservadas))


MARCA_R = (4.5, 6.5)  # radio (px) de las marcas de la correa: mínimo 4,5 ⇒ cajas de ≥ 6 px
MARCA_PASO = 14.5  # px entre marcas
POR_FILA = 15


def marcas_de_correa(c: Calculo, s: Stream, n: int, x0: float, y_correa: float) -> list[Roca]:
    """TODAS las n marcas de la corriente `s` (cuantiles de masa), de menor a mayor, en filas
    ordenadas sobre la correa a partir de x0. NO van a escala (cada marca vale 1/n de la masa; el
    radio crece de 4,5 a 6,5 px con el orden) y no se descarta ninguna."""
    j = c.jaw
    out = []
    xs = cuantiles(s, n)
    for i, x in enumerate(xs):
        fila, col = divmod(i, POR_FILA)
        r = MARCA_R[0] + (MARCA_R[1] - MARCA_R[0]) * i / max(n - 1, 1)
        cy = y_correa - MARCA_R[1] - 1.0 - fila * (2 * MARCA_R[1] + 2.0)
        out.append(
            Roca(x, clase_de(x, j.css_eff_mm, j.oss_mm, j.gape_mm), x0 + col * MARCA_PASO, cy, r)
        )
    return out


def dibujar_marcas(marcas: list[Roca], clase: str) -> str:
    """El SVG de las marcas de la correa: regulares y con relleno sólido en todas las clases."""
    return "".join(
        forma(r.clase, r.cx, r.cy, r.r, i, clase, r.size_mm, marca=True)
        for i, r in enumerate(marcas)
    )


def dibujar(rocas: list[Roca], clase: str) -> str:
    """El SVG de las rocas (las grandes atrás); `clase` es el prefijo de su clase CSS."""
    return "".join(
        forma(r.clase, r.cx, r.cy, r.r, i, clase, r.size_mm)
        for i, r in enumerate(sorted(rocas, key=lambda r: -r.r))
    )
