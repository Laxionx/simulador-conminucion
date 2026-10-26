"""El esquema del chancador de mandíbula: SVG válido y sin código, dos versiones como imagen, y cada
magnitud del dibujo sale del cálculo (cámara a escala, período, rocas por clase). La carrera
amplificada y la velocidad de la animación solo cambian el dibujo."""

import base64
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytest.importorskip("streamlit")

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

import i18n  # noqa: E402
import mandibula_datos as md  # noqa: E402
import mandibula_svg as ms  # noqa: E402
from equipos import as_images, es  # noqa: E402

from conminucion.mandibula import pasante_en  # noqa: E402

NS = "{http://www.w3.org/2000/svg}"
SPANISH = re.compile(
    r"[áéíóúñ¿¡]|\b(de|del|la|las|los|el|con|para|por|una|sin|que|se|más|muy)\b", re.IGNORECASE
)


def calc(**cambios) -> md.Calculo:
    return md.calcular({**md.valores_por_defecto(), **cambios})


CASOS = {
    "ejemplo": {},
    "css_cerrado": {"css": 8.0},
    "desgaste": {"wear": 20.0},
    "sin_parrilla": {"grizzly": False},
    "colpas": {"top": 580.0},
    "rpm_alta": {"rpm": 330.0},
    "grande": md.valores_de_equipo(md.POR_NOMBRE["42x48"], 152),
}


def svg(c, amp=3.0, vel=10, view="completo", paused=True, lang="es") -> str:
    with i18n.use(lang):
        return ms.jaw_svg(c, amp, vel, view, paused)


def tree(text: str) -> ET.Element:
    return ET.fromstring(text)


def by_id(root: ET.Element, ident: str) -> ET.Element:
    return next(e for e in root.iter() if e.get("id") == ident)


def length(e: ET.Element) -> float:
    return math.hypot(
        float(e.get("x2")) - float(e.get("x1")), float(e.get("y2")) - float(e.get("y1"))
    )


# ------------------------------------------------------------------ válido y sin código
@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("view", ms.VIEWS)
@pytest.mark.parametrize("paused", [True, False])
def test_el_svg_es_xml_valido_y_no_lleva_codigo_ni_enlaces(lang, view, paused):
    for cambios in CASOS.values():
        c = md.calcular({**md.valores_por_defecto(), **cambios})
        text = svg(c, view=view, paused=paused, lang=lang)
        root = tree(text)
        assert "<script" not in text.lower() and "foreignobject" not in text.lower()
        assert "javascript:" not in text.lower() and "<image" not in text.lower()
        for e in root.iter():
            assert not any(a.lower().startswith("on") for a in e.attrib), e.tag
            assert not any("href" in a.lower() for a in e.attrib), e.tag
        assert text.count("http") == 1  # solo el espacio de nombres xmlns


def test_las_dos_versiones_van_como_imagen_y_la_quieta_no_se_anima():
    c = calc()
    with i18n.use("es"):
        html = as_images(ms.jaw_svg(c, 3, 10, paused=False), ms.jaw_svg(c, 3, 10, paused=True), "x")
    assert html.count("<img") == 2 and "<svg" not in html
    assert 'class="cm-anim"' in html and 'class="cm-still"' in html
    anim, still = (
        base64.b64decode(s).decode()
        for s in re.findall(r'src="data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)"', html)
    )
    assert "@keyframes jw-swing" in anim and "animation:jw-swing" in anim
    assert "@keyframes jw-" not in still and "jw-swing{" not in still
    tree(anim), tree(still)
    # con la animación apagada, la misma versión quieta sirve para las dos
    with i18n.use("es"):
        quieta = ms.jaw_svg(c, 3, 10, paused=True)
        assert as_images(quieta, quieta, "x").count("<img") == 1


def test_una_vista_desconocida_se_rechaza():
    with pytest.raises(ValueError, match="Vista"), i18n.use("es"):
        ms.jaw_svg(calc(), 3, 10, "otra")


def test_los_textos_del_esquema_en_ingles_no_llevan_espanol():
    c = calc()
    for text in (svg(c, lang="en"), svg(c, lang="en", paused=False)):
        texts = re.findall(r">([^<]+)</text>", text) + re.findall(r'aria-label="([^"]+)"', text)
        assert texts and not [x for x in texts if SPANISH.search(x)], texts
    with i18n.use("en"):
        ab = ms.abertura_svg(18.0, 51.0, 250.0, 10)
    assert not [x for x in re.findall(r">([^<]+)</text>", ab) if SPANISH.search(x)]


# ------------------------------------------------------------------ sale del cálculo
@pytest.mark.parametrize("nombre", CASOS)
def test_la_camara_esta_a_escala_con_boca_altura_css_y_oss_del_calculo(nombre):
    c = md.calcular({**md.valores_por_defecto(), **CASOS[nombre]})
    j = c.jaw
    root = tree(svg(c))
    s = ms.escala(j.gape_mm, j.height)
    assert length(by_id(root, "jw-boca")) == pytest.approx(j.gape_mm * s, abs=0.02)
    assert length(by_id(root, "jw-altura")) == pytest.approx(j.height * s, abs=0.02)
    assert length(by_id(root, "jw-css")) == pytest.approx(j.css_eff_mm * s, abs=0.02)
    assert length(by_id(root, "jw-oss")) == pytest.approx((j.css_eff_mm + j.stroke) * s, abs=0.02)
    texts = " ".join(e.text or "" for e in root.iter(NS + "text"))
    assert f"CSS = {es(j.css_eff_mm, 1)} mm" in texts and f"OSS = {es(j.oss_mm, 1)} mm" in texts
    assert f"G = {es(j.gape_mm, 0)} mm" in texts and f"D = {es(j.height, 0)} mm" in texts
    assert f"θ = {es(j.bite_angle_deg, 1)}°" in texts


def test_la_mandibula_abierta_esta_a_la_carrera_real_con_amplificacion_1():
    c = calc()
    j, g = c.jaw, ms.geometria(c, 1.0)
    root = tree(svg(c, amp=1.0))
    ghost = next(e for e in root.iter(NS + "polygon") if e.get("stroke-dasharray") == "5 4")
    pts = [tuple(map(float, p.split(","))) for p in ghost.get("points").split()]
    abierta = pts[1][0] - (g.xf + j.css_eff_mm * g.s)  # esquina de abajo, cara de la cámara
    assert abierta == pytest.approx(j.stroke * g.s, rel=0.03, abs=0.3)


@pytest.mark.parametrize(("rpm", "vel"), [(250.0, 10), (180.0, 100), (330.0, 5), (90.0, 50)])
def test_el_periodo_es_60_sobre_n_dividido_por_la_velocidad(rpm, vel):
    text = svg(calc(rpm=rpm), vel=vel, paused=False)
    esperado = 60.0 / rpm / (vel / 100.0)
    assert ms.periodo_s(rpm, vel) == pytest.approx(esperado)
    swing = float(re.search(r"animation:jw-swing ([0-9.]+)s", text).group(1))
    spin = float(re.search(r'cm-spin" style="[^"]*animation-duration:([0-9.]+)s', text).group(1))
    assert swing == pytest.approx(esperado, abs=0.0006) and spin == pytest.approx(
        esperado, abs=0.0006
    )
    assert f"{es(rpm, 0)} rpm" in text


def test_la_amplificacion_y_la_velocidad_solo_cambian_el_dibujo():
    c = calc()
    antes = (c.capacidad, c.p80, c.utilizacion, c.jaw.stroke, c.jaw.oss_mm, c.potencia)
    cotas = {}
    angulos = {}
    for amp in (1.0, 4.0, 8.0):
        for vel in (5, 100):
            text = svg(c, amp=amp, vel=vel, paused=False)
            root = tree(text)
            cotas[(amp, vel)] = tuple(
                length(by_id(root, i)) for i in ("jw-boca", "jw-altura", "jw-css", "jw-oss")
            )
            angulos[(amp, vel)] = float(
                re.search(
                    r"jw-swing\{0%,100%\{transform:rotate\(0deg\)\}50%\{transform:rotate\((-?[0-9.]+)deg",
                    text,
                ).group(1)
            )
    assert len(set(cotas.values())) == 1  # las cotas no dependen de ninguno de los dos
    assert (c.capacidad, c.p80, c.utilizacion, c.jaw.stroke, c.jaw.oss_mm, c.potencia) == antes
    a1, a4, a8 = (abs(angulos[(a, 5)]) for a in (1.0, 4.0, 8.0))
    assert a1 < a4 < a8 and a8 == pytest.approx(8 * a1, rel=0.05)
    assert angulos[(4.0, 5)] == angulos[(4.0, 100)]  # la velocidad no cambia la carrera dibujada
    assert "solo cambia el dibujo" in svg(c, amp=4.0, vel=25) and "×4" in svg(c, amp=4.0)


def _rocas(root: ET.Element) -> dict[int, list[ET.Element]]:
    out: dict[int, list[ET.Element]] = {0: [], 1: [], 2: [], 3: []}
    for e in root.iter():
        m = re.search(r"\brock-(\d)\b", e.get("class", ""))
        if m:
            out[int(m.group(1))].append(e)
    return out


def _fracciones(c: md.Calculo) -> list[float]:
    j, f = c.jaw, c.carga
    p = [pasante_en(f, x * md.MM) for x in (j.css_eff_mm, j.oss_mm, 0.8 * j.gape_mm)]
    return [p[0], p[1] - p[0], p[2] - p[1], 1.0 - p[2]]


@pytest.mark.parametrize("nombre", CASOS)
def test_hay_120_rocas_y_cada_clase_tiene_su_fraccion_de_la_masa(nombre):
    c = md.calcular({**md.valores_por_defecto(), **CASOS[nombre]})
    rocas = _rocas(tree(svg(c)))
    n = [len(rocas[k]) for k in range(4)]
    assert sum(n) == ms.ROCAS == 120
    for k, frac in enumerate(_fracciones(c)):
        assert abs(n[k] - ms.ROCAS * frac) <= 1.0 + 1e-9, (nombre, k, n[k], ms.ROCAS * frac)
    assert n == ms.conteo_clases(c)


def test_los_casos_cubren_las_cuatro_clases():
    vistos = {
        k
        for nombre in CASOS
        for k, v in enumerate(
            ms.conteo_clases(md.calcular({**md.valores_por_defecto(), **CASOS[nombre]}))
        )
        if v
    }
    assert vistos == {0, 1, 2, 3}


def test_cada_clase_tiene_su_color_y_su_forma_y_la_leyenda_dice_cuantas_son():
    c = md.calcular({**md.valores_por_defecto(), "top": 580.0, "grizzly": False})
    root = tree(svg(c))
    rocas = _rocas(root)
    formas = {0: NS + "circle", 1: NS + "rect", 2: NS + "polygon", 3: NS + "polygon"}
    vertices = {2: 3, 3: 6}
    assert len(set(ms.CLASS_COLORS)) == 4
    for k, items in rocas.items():
        assert items, k
        for e in items:
            assert e.tag == formas[k] and e.get("fill") == ms.CLASS_COLORS[k]
            if k in vertices:
                assert len(e.get("points").split()) == vertices[k]
    assert float(rocas[3][0].get("stroke-width")) > float(rocas[0][0].get("stroke-width"))
    texts = [e.text for e in root.iter(NS + "text")]
    n = ms.conteo_clases(c)
    assert f"≤ CSS: {n[0]} rocas" in texts and f"colpa (> 0,8·boca): {n[3]}" in texts


def _centro(e: ET.Element) -> tuple[float, float]:
    if e.tag == NS + "rect":
        return float(e.get("x")) + float(e.get("width")) / 2, float(e.get("y")) + float(
            e.get("height")
        ) / 2
    pts = [tuple(map(float, p.split(","))) for p in e.get("points").split()]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)


def test_cada_roca_esta_a_la_altura_donde_su_tamano_iguala_la_abertura_local():
    c = md.calcular({**md.valores_por_defecto(), "top": 580.0})
    j, g = c.jaw, ms.geometria(c, 3.0)
    rocas = _rocas(tree(svg(c)))
    for k in (1, 2, 3):
        for e in rocas[k]:
            cx, cy = _centro(e)
            tamano = 2.0 * (cx - g.xf) / g.s  # entre las dos mandíbulas: ancho = tamaño
            assert j.css_eff_mm < tamano
            abertura_local = j.css_eff_mm + (j.gape_mm - j.css_eff_mm) * (g.yb - cy) / (
                j.height * g.s
            )
            assert abertura_local == pytest.approx(tamano, rel=0.02, abs=1.5)
            assert ms.clase_de(tamano, j.css_eff_mm, j.oss_mm, j.gape_mm) == k


def test_los_tamanos_de_las_rocas_son_deterministas_y_crecientes():
    c = calc()
    a, b = ms.tamanos_rocas(c), ms.tamanos_rocas(c)
    assert a == b and a == sorted(a) and len(a) == 120
    assert svg(c) == svg(c) and svg(c, paused=False) == svg(c, paused=False)  # sin azar


def test_la_vista_de_detalle_es_el_mismo_dibujo_con_otro_viewbox():
    c = calc()
    full, detail = tree(svg(c)), tree(svg(c, view="detalle"))
    assert full.get("viewBox") != detail.get("viewBox")
    x, y, w, h = map(float, detail.get("viewBox").split())
    assert w < 900 and h < 580
    for ident in ("jw-boca", "jw-altura", "jw-css", "jw-oss"):
        assert length(by_id(full, ident)) == length(by_id(detail, ident))
    g = ms.geometria(c, 3.0)
    assert x < g.xc < x + w and y < g.yb < y + h  # la descarga queda dentro del detalle


def test_la_parrilla_se_dibuja_con_su_abertura_a_escala_y_se_apaga():
    c = calc()
    g = ms.geometria(c, 3.0)
    root = tree(svg(c))
    barras = [e for e in by_id(root, "jw-parrilla") if e.tag == NS + "rect"]
    paso = float(barras[1].get("x")) - float(barras[0].get("x"))
    assert paso == pytest.approx(9.0 + c.parrilla.aperture_mm * g.s, abs=0.15)
    assert not any(e.get("id") == "jw-parrilla" for e in tree(svg(calc(grizzly=False))).iter())


# ------------------------------------------------------------------ abertura en el tiempo
def test_la_abertura_oscila_entre_el_css_y_el_oss_y_el_punto_tarda_dos_ciclos():
    c = calc()
    j = c.jaw
    with i18n.use("es"):
        text = ms.abertura_svg(j.css_eff_mm, j.oss_mm, j.rpm, 20, paused=False)
    root = tree(text)
    d = by_id(root, "jw-curva").get("d")
    ys = [float(p.split()[-1]) for p in d.removeprefix("M ").split(" L ")]
    assert len(ys) == 81 and ys[0] == max(ys) and min(ys) == pytest.approx(36.0, abs=0.1)
    assert max(ys) == pytest.approx(118.0, abs=0.1)  # CSS abajo, OSS arriba
    assert ys[40] == pytest.approx(ys[0], abs=0.1)  # a la mitad de la curva, un ciclo completo
    dur = float(re.search(r"animation-duration:([0-9.]+)s", text).group(1))
    assert dur == pytest.approx(2 * ms.periodo_s(j.rpm, 20), abs=0.001)
    texts = " ".join(e.text for e in root.iter(NS + "text"))
    assert es(j.css_eff_mm, 1) in texts and es(j.oss_mm, 1) in texts
    with i18n.use("es"):
        assert "animation" not in ms.abertura_svg(j.css_eff_mm, j.oss_mm, j.rpm, 20, paused=True)
