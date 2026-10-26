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
import mandibula_rocas as mr  # noqa: E402
import mandibula_svg as ms  # noqa: E402
from equipos import INK, PAPER, as_images, es  # noqa: E402

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


def _rocas(root: ET.Element, prefijo: str = "rock") -> dict[int, list[ET.Element]]:
    out: dict[int, list[ET.Element]] = {0: [], 1: [], 2: [], 3: []}
    for e in root.iter():
        m = re.search(rf"\b{prefijo}-(\d)\b", e.get("class", ""))
        if m:
            out[int(m.group(1))].append(e)
    return out


def _todas(root: ET.Element, prefijo: str) -> list[ET.Element]:
    return [e for k in _rocas(root, prefijo).values() for e in k]


def _caja(e: ET.Element) -> tuple[float, float, float, float]:
    pts = [tuple(map(float, p.split(","))) for p in e.get("points").split()]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _se_cruzan(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _sin_cruces(elementos: list[ET.Element]) -> bool:
    cajas = [_caja(e) for e in elementos]
    return not any(
        _se_cruzan(cajas[i], cajas[j]) for i in range(len(cajas)) for j in range(i + 1, len(cajas))
    )


def _dibujadas(c: md.Calculo) -> dict[str, list[ET.Element]]:
    root = tree(svg(c))
    return {p: _todas(root, p) for p in ("rock", "prod", "fin")}


@pytest.mark.parametrize("nombre", CASOS)
def test_las_rocas_no_se_encriman_y_son_cuantiles_de_la_carga(nombre):
    c = md.calcular({**md.valores_por_defecto(), **CASOS[nombre]})
    d = _dibujadas(c)
    cuantiles = {round(x, 2) for x in mr.cuantiles(c.carga, mr.ROCAS)}
    assert 3 <= len(d["rock"]) <= mr.ROCAS
    assert {float(e.get("data-mm")) for e in d["rock"]} <= cuantiles
    for grupo in d.values():
        assert _sin_cruces(grupo), (nombre, len(grupo))  # cajas que no se cruzan
    assert _sin_cruces(d["prod"] + d["fin"])  # y las de la correa tampoco entre sí


@pytest.mark.parametrize("nombre", CASOS)
def test_cada_roca_esta_a_la_altura_de_la_regla_de_la_abertura(nombre):
    c = md.calcular({**md.valores_por_defecto(), **CASOS[nombre]})
    j, g = c.jaw, ms.geometria(c, 3.0)
    rocas = mr.rocas_de_camara(c, g.xf, g.yb, g.s, ms.reservadas(c, g))
    for r in rocas:
        assert r.clase == mr.clase_de(r.size_mm, j.css_eff_mm, j.oss_mm, j.gape_mm)
        assert r.r == pytest.approx(max(0.85 * r.size_mm * g.s / 2.0, 1.5))  # 0,85 × la abertura
        if r.size_mm > j.css_eff_mm:
            abertura = j.css_eff_mm + (j.gape_mm - j.css_eff_mm) * (g.yb - r.cy) / (j.height * g.s)
            assert abertura == pytest.approx(r.size_mm, rel=1e-9)  # su tamaño = la abertura local
            assert r.cx == pytest.approx(g.xf + r.size_mm * g.s / 2.0)
    assert len(_dibujadas(c)["rock"]) == len(rocas)  # lo dibujado sale de esas rocas


def test_la_regla_no_deja_que_dos_rocas_se_crucen_aunque_sus_alturas_coincidan():
    a, b = mr.Roca(100.0, 2, 50.0, 50.0, 20.0), mr.Roca(90.0, 2, 60.0, 60.0, 20.0)
    c = mr.Roca(30.0, 1, 200.0, 50.0, 5.0)
    assert mr.sin_encimar([a, b, c]) == [a, c]  # b se cruza con a y se salta
    assert mr.sin_encimar([b, a]) == [b]


def test_la_clase_depende_del_tamano_y_las_formas_y_colores_son_los_de_la_clase():
    j = md.ejemplo().jaw
    css, oss, g = j.css_eff_mm, j.oss_mm, j.gape_mm
    tamanos = (css, css + 0.1, oss, oss + 0.1, 0.8 * g + 1)
    assert [mr.clase_de(x, css, oss, g) for x in tamanos] == [0, 1, 1, 2, 3]
    c = md.calcular({**md.valores_por_defecto(), "top": 580.0, "grizzly": False})
    root = tree(svg(c))
    vistas = set()
    for prefijo in ("rock", "prod", "fin"):
        for k, items in _rocas(root, prefijo).items():
            for e in items:
                vistas.add(k)
                assert e.tag == NS + "polygon" and e.get("fill") == mr.CLASS_COLORS[k]
                assert len(e.get("points").split()) == mr.VERTICES[k]
                assert mr.clase_de(float(e.get("data-mm")), css, oss, g) == k
    assert vistas == {0, 1, 2, 3}
    grueso = [e for e in _rocas(root)[3]]
    assert grueso and float(grueso[0].get("stroke-width")) > 2.5  # la colpa lleva borde grueso
    fino = _rocas(root, "prod")[0] + _rocas(root, "rock")[0]
    assert not fino or all(e.get("stroke-dasharray") for e in fino)  # y la fina, borde a trazos
    assert len(set(mr.CLASS_COLORS)) == 4 and len(set(mr.VERTICES)) == 4


def _clases_dibujadas(elementos: list[ET.Element]) -> list[int]:
    n = [0, 0, 0, 0]
    for e in elementos:
        n[int(re.search(r"-(\d)\b", e.get("class").split()[1]).group(1))] += 1
    return n


@pytest.mark.parametrize("nombre", CASOS)
def test_la_correa_dibuja_todas_las_marcas_y_las_clases_son_las_del_modelo(nombre):
    """Sin escala ni descarte: 30 cuantiles del producto y 12 de los finos, todos visibles."""
    c = md.calcular({**md.valores_por_defecto(), **CASOS[nombre]})
    d = _dibujadas(c)
    assert len(d["prod"]) == mr.PRODUCTO
    assert len(d["fin"]) == (mr.FINOS if c.pasante is not None else 0)
    prod = [round(x, 2) for x in mr.cuantiles(c.prod_chancador, mr.PRODUCTO)]
    assert sorted(float(e.get("data-mm")) for e in d["prod"]) == sorted(prod)
    esperado = [mr.PRODUCTO * f for f in mr.fracciones_clases(c, c.prod_chancador)]
    for dibujadas, esp in zip(_clases_dibujadas(d["prod"]), esperado, strict=True):
        assert abs(dibujadas - esp) <= 1.0 + 1e-9, (nombre, dibujadas, esp)
    if c.pasante is not None:
        esperado = [mr.FINOS * f for f in mr.fracciones_clases(c, c.pasante)]
        for dibujadas, esp in zip(_clases_dibujadas(d["fin"]), esperado, strict=True):
            assert abs(dibujadas - esp) <= 1.0 + 1e-9, (nombre, dibujadas, esp)
    for e in d["prod"] + d["fin"]:  # tamaño mínimo visible y relleno sólido en todas las clases
        x0, y0, x1, y1 = _caja(e)
        assert min(x1 - x0, y1 - y0) >= 6.0 and e.get("fill-opacity") == "1"
        assert ms.Y_CORREA - 40 <= y0 and y1 <= ms.Y_CORREA
    assert _sin_cruces(d["prod"] + d["fin"])


def test_las_marcas_del_producto_estan_bajo_la_descarga_y_los_finos_aguas_arriba():
    c = calc()
    d = _dibujadas(c)
    g = ms.geometria(c, 3.0)
    xs_prod = [(_caja(e)[0] + _caja(e)[2]) / 2 for e in d["prod"]]
    xs_fin = [(_caja(e)[0] + _caja(e)[2]) / 2 for e in d["fin"]]
    assert min(xs_prod) > g.xc and max(xs_fin) < min(xs_prod)  # la correa avanza hacia la derecha
    assert _dibujadas(calc(grizzly=False))["fin"] == []  # sin parrilla no hay finos
    cerrado = calc(css=8.0)  # un OSS más cerrado da un producto más fino
    assert max(mr.cuantiles(cerrado.prod_chancador, 30)) < max(mr.cuantiles(c.prod_chancador, 30))
    textos = [e.text for e in tree(svg(c)).iter(NS + "text")]
    assert "Correa: marca = 1/30 del producto" in textos
    assert "(tamaño no a escala; finos: 1/12)" in textos


def _luminancia(hexa: str) -> float:
    canales = [int(hexa[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in canales]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contraste(a: str, b: str) -> float:
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("view", ms.VIEWS)
def test_la_leyenda_es_unica_en_dos_bloques_con_texto_en_tinta_y_contraste(view):
    c = md.calcular({**md.valores_por_defecto(), "top": 580.0, "grizzly": False})
    root = tree(svg(c, view=view))
    textos = [e.text for e in root.iter(NS + "text")]
    fa, fp = (mr.fracciones_clases(c, s_) for s_ in (c.carga, c.prod_chancador))
    plantillas = ["≤ CSS: {} % de la masa", "entre CSS y OSS: {} %", "mayor que el OSS: {} %",
                  "colpa (> 0,8·boca): {} %"]  # fmt: skip
    pares = [zip(plantillas, fr, strict=True) for fr in (fa, fp)]
    lineas = [p.format(es(100 * f, 1)) for par in pares for p, f in par]
    en_leyenda = [x for x in textos if x in set(lineas)]
    assert en_leyenda == lineas  # los dos bloques, en orden: primero la cámara y luego la correa
    assert (
        textos.count("Alimentación a la cámara") == 1 and textos.count("Producto en la correa") == 1
    )
    assert sum(f > 0 for f in fa) >= 2 and fa != fp  # los dos bloques dicen cosas distintas
    for e in root.iter(NS + "text"):
        if e.text in lineas or e.text in ("Alimentación a la cámara", "Producto en la correa"):
            assert INK in e.get("style")  # el texto va en tinta; el color, solo en la forma
    assert _contraste(INK, PAPER) >= 4.5
    assert not any("Producto:" in (x or "") for x in textos)  # ya no hay un % suelto ambiguo


def test_la_nota_solo_cambia_el_dibujo_esta_en_el_bloque_de_informacion():
    root = tree(svg(calc(), amp=3.0, vel=10))
    textos = {e.text: float(e.get("x")) for e in root.iter(NS + "text")}
    assert textos["solo cambia el dibujo"] == 650.0 and "Carrera ×3, velocidad 10 %:" in textos
    assert not any(e.text and "Carrera ×3 y velocidad" in e.text for e in root.iter(NS + "text"))


def test_los_rotulos_van_a_un_lado_con_linea_guia():
    c = calc()
    root = tree(svg(c))
    g = ms.geometria(c, 3.0)
    x = {e.text: float(e.get("x")) for e in root.iter(NS + "text")}
    # los rótulos de CSS y OSS van a un lado de la corriente de descarga y no encima de ella
    assert x["CSS = 18,0 mm"] > g.xf + 40 and x["OSS = 51,0 mm"] > g.xf + 40
    guias = [e for e in root.iter(NS + "line") if e.get("stroke-dasharray") == "3 3"]
    assert len(guias) >= 5
    assert "θ" in x  # el ángulo se rotula con el símbolo; su valor va en el bloque de información


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
    assert paso == pytest.approx(8.0 + c.parrilla.aperture_mm * g.s, abs=0.15)
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


def test_la_theta_y_su_arco_no_los_pisa_ninguna_roca():
    for nombre in CASOS:
        c = md.calcular({**md.valores_por_defecto(), **CASOS[nombre]})
        root = tree(svg(c))
        g = ms.geometria(c, 3.0)
        th = next(e for e in root.iter(NS + "text") if e.text == "θ")
        x, y = float(th.get("x")), float(th.get("y"))
        caja_theta = (x - 8.0, y - 13.0, x + 8.0, y + 4.0)
        arco = (g.xf - ms.ARCO_R, g.apex_y - ms.ARCO_R, g.xf + 4.0, g.apex_y)
        for e in _todas(root, "rock"):
            assert not _se_cruzan(_caja(e), caja_theta), nombre
            assert not _se_cruzan(_caja(e), arco), nombre
        res = ms.reservadas(c, g)[0]
        assert res.cx - res.r <= caja_theta[0] and caja_theta[2] <= res.cx + res.r
        assert res.cy - res.r <= caja_theta[1] and caja_theta[3] <= res.cy + res.r


@pytest.mark.parametrize("lang", ["es", "en"])
def test_ningun_texto_del_esquema_se_sale_del_lienzo(lang):
    """Estima el ancho de cada texto (0,52 × el cuerpo por carácter) y exige que quepa."""
    for cambios in CASOS.values():
        c = md.calcular({**md.valores_por_defecto(), **cambios})
        for e in tree(svg(c, lang=lang)).iter(NS + "text"):
            if not e.text or e.get("transform"):
                continue
            ancho = 0.52 * float(e.get("font-size")) * len(e.text)
            x, ancla = float(e.get("x")), e.get("text-anchor")
            izq = x if ancla == "start" else x - ancho if ancla == "end" else x - ancho / 2
            assert izq >= 0 and izq + ancho <= ms.W - 4, (lang, e.text, izq, ancho)
