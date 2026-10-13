"""La presentación de la app: cada animación sale del cálculo, cada dato tiene su ayuda y la
tabla «Qué datos necesita» no se puede desfasar de la barra lateral."""

import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))
APP = str(APP_DIR / "streamlit_app.py")

from animaciones import (  # noqa: E402
    MAX_FRAMES,
    convergence_figure,
    frame_iterations,
    journey,
    journey_figure,
)
from controles import CHOICES, DATOS, DISTRIBUTIONS, SELECTIONS, data_table  # noqa: E402
from equipos import (  # noqa: E402
    MOTION_CSS,
    as_images,
    charge_angle,
    cyclone_svg,
    dash_period_s,
    flowsheet_svg,
    line_width,
    mill_svg,
    rotation_period_s,
)
from guia import markdown_table  # noqa: E402

from conminucion.circuits import FRESH, CircuitConfig, simulate  # noqa: E402
from conminucion.classifier import EfficiencyCurve  # noqa: E402
from conminucion.mill import AustinSelection, BallMill  # noqa: E402
from conminucion.power import critical_speed_rpm  # noqa: E402
from conminucion.sizes import SizeGrid, rosin_rammler  # noqa: E402
from conminucion.stream import Stream  # noqa: E402

KINDS = ("abierto", "cerrado_directo", "cerrado_inverso")


def _cfg(n_mixers: int = 3) -> CircuitConfig:
    grid = SizeGrid.geometric(9500.0, 17)
    fresh = Stream.from_fractions(grid, rosin_rammler(grid, 3200.0, 1.0), 100.0, 0.0, 2.7)
    return CircuitConfig(fresh, BallMill(AustinSelection(), n_mixers=n_mixers), EfficiencyCurve())


# ------------------------------------------------------------------ datos y ayudas
def test_cada_dato_tiene_rango_ejemplo_y_ayuda():
    assert len({d.key for d in DATOS}) == len(DATOS)
    for d in DATOS:
        assert d.lo <= d.default <= d.hi, d.key
        assert d.meaning and d.source, d.key
        assert d.meaning in d.help and d.source in d.help


def test_la_tabla_sale_de_las_mismas_definiciones():
    table = data_table()
    assert len(table) == len(CHOICES) + len(DATOS)
    assert set(table["Equipo"]) == {d.group for d in DATOS} | {c[1] for c in CHOICES}
    assert table["Qué es"].str.len().min() > 0
    assert table["Cómo se obtiene"].str.len().min() > 0


def test_la_tabla_en_markdown_escapa_las_barras():
    import pandas as pd

    md = markdown_table(pd.DataFrame({"a": ["x|y"], "b": ["z"]}))
    assert "x\\|y" in md and md.count("\n") == 2


@pytest.mark.parametrize("dist", DISTRIBUTIONS)
@pytest.mark.parametrize("param", SELECTIONS)
def test_todos_los_controles_tienen_ayuda_y_estan_en_la_tabla(dist, param):
    at = AppTest.from_file(APP, default_timeout=180).run()
    at.sidebar.radio[0].set_value(dist)
    at.sidebar.radio[1].set_value(param)
    at.run()
    assert not at.exception
    widgets = [*at.sidebar.number_input, *at.sidebar.slider, *at.sidebar.radio,
               *at.sidebar.selectbox, *at.sidebar.checkbox]  # fmt: skip
    for w in widgets:
        assert w.help, w.label
    asked = {d.key for d in DATOS if not d.when or d.when in (dist, param)}
    shown = {w.label for w in [*at.sidebar.number_input, *at.sidebar.slider]}
    expected = {f"{d.label} ({d.unit})" if d.unit else d.label for d in DATOS if d.key in asked}
    assert shown == expected


def test_cargar_ejemplo_tipico_vuelve_a_los_valores_de_la_tabla():
    def solids(at):
        return next(w for w in at.sidebar.number_input if w.label == "Sólidos frescos (t/h)")

    at = AppTest.from_file(APP, default_timeout=180).run()
    solids(at).set_value(250.0).run()
    assert solids(at).value == 250.0
    at.sidebar.button[0].click().run()
    assert solids(at).value == 100.0
    assert not at.exception


# ------------------------------------------------------------------ esquemas de los equipos
@pytest.mark.parametrize("filling", [0.30, 0.38, 0.45, 0.5])
def test_area_de_la_carga_es_el_llenado(filling):
    theta = charge_angle(filling)
    assert (theta - math.sin(theta)) / (2 * math.pi) == pytest.approx(filling, abs=1e-12)


def test_el_tambor_gira_a_las_rpm_reales():
    period = rotation_period_s(4.0, 0.75, 75.0)
    assert period == pytest.approx(60.0 / (0.75 * critical_speed_rpm(4.0, 75.0)))
    svg = mill_svg(4.0, 6.0, 0.38, 0.75, 75.0, 1500.0, 130.0)
    assert f"animation-duration:{period:.3f}s" in svg


def test_grosor_y_velocidad_crecen_con_el_caudal():
    flows = [0.0, 10.0, 50.0, 100.0]
    widths = [line_width(f, 100.0) for f in flows]
    periods = [dash_period_s(f, 100.0) for f in flows]
    assert widths == sorted(widths) and periods == sorted(periods, reverse=True)
    assert (widths[3] - widths[0]) == pytest.approx(2 * (widths[2] - widths[0]))


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("paused", [False, True])
def test_los_esquemas_son_svg_validos_y_sin_codigo(kind, paused):
    res = simulate(kind, _cfg(), wegstein=True)
    s = res.streams
    svgs = [flowsheet_svg(kind, s, 3.75, paused), mill_svg(4.0, 6.0, 0.38, 0.75, 75.0, 1.0, 1.0,
                                                            paused)]  # fmt: skip
    if kind != "abierto":
        svgs.append(cyclone_svg(s["alim_ciclon"], s["underflow"], s["overflow"], paused))
    for svg in svgs:
        ET.fromstring(svg)  # XML bien formado
        low = svg.lower()
        assert "<script" not in low and "javascript:" not in low and "href" not in low
        assert ("prefers-reduced-motion" in svg) is (not paused)
        assert ("@keyframes" in svg) is (not paused)
    p80 = f"{s[res.product].p80:,.0f}".replace(",", " ")
    assert p80 in svgs[0]  # el diagrama rotula el P80 del producto calculado


def test_las_dos_versiones_van_como_imagen():
    import base64
    import re

    moving = mill_svg(4.0, 6.0, 0.38, 0.75, 75.0, 1.0, 1.0)
    still = mill_svg(4.0, 6.0, 0.38, 0.75, 75.0, 1.0, 1.0, paused=True)
    html = as_images(moving, still, "Molino")
    srcs = re.findall(r'src="data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)"', html)
    assert [base64.b64decode(x).decode("utf-8") for x in srcs] == [moving, still]
    assert "<svg" not in html  # el SVG viaja codificado, no como marcado de la página
    assert 'class="cm-anim"' in html and 'class="cm-still"' in html
    assert html.count("<img") == 2
    assert as_images(still, still, "x").count("<img") == 1  # sin animación, una sola
    assert "prefers-reduced-motion: reduce" in MOTION_CSS


# ------------------------------------------------------------------ animaciones
def test_cuadros_de_la_convergencia():
    assert frame_iterations(19) == list(range(1, 20))
    many = frame_iterations(500)
    assert many[-1] == 500 and len(many) <= MAX_FRAMES + 1


@pytest.mark.parametrize("kind", ["cerrado_directo", "cerrado_inverso"])
def test_la_convergencia_termina_en_la_carga_circulante(kind):
    weg, sub = simulate(kind, _cfg(), wegstein=True), simulate(kind, _cfg(), wegstein=False)
    fresh = weg.streams[FRESH].total_solids
    fig = convergence_figure(fresh, {"W": weg.solution.tear_history,
                                     "S": sub.solution.tear_history})  # fmt: skip
    assert len(fig.frames) == len(frame_iterations(max(weg.solution.iterations,
                                                       sub.solution.iterations)))  # fmt: skip
    last = fig.frames[-1].data
    assert last[0].y[-1] == pytest.approx(weg.circulating_load, rel=1e-9)
    assert last[1].y[-1] == pytest.approx(sub.circulating_load, rel=1e-6)
    assert fig.data[0].y == last[0].y  # arranca mostrando el estado final


@pytest.mark.parametrize("kind", KINDS)
def test_el_recorrido_termina_en_la_descarga_del_molino(kind):
    cfg = _cfg(n_mixers=3)
    res = simulate(kind, cfg, wegstein=True)
    stages = journey(kind, res, cfg)
    out = "producto" if kind == "abierto" else "descarga_molino"
    mill_out = [st for st in stages if st.stream == out][-1]
    np.testing.assert_allclose(mill_out.passing, 100 * res.streams[out].cumulative_passing)
    assert sum("mezclador" in st.label for st in stages) == 2  # los 2 intermedios de 3
    fig = journey_figure(stages, res.streams[FRESH].grid.sieves)
    assert len(fig.frames) == len(stages)
    assert all(len(f.data) == len(stages) for f in fig.frames)  # Plotly anima trazos fijos
    assert len(fig.frames[0].data[1].y) == 0  # al inicio, la etapa 2 aún vacía


def test_la_app_muestra_las_tres_pestanas_y_la_energia():
    at = AppTest.from_file(APP, default_timeout=180).run()
    assert not at.exception
    assert [t.label for t in at.tabs] == [
        "Guía",
        "Simulación",
        "Ajuste a datos (muestreo sintético)",
    ]
    labels = [m.label for m in at.metric]
    assert "Energía que entrega el molino (kWh/t)" in labels
    at.toggle[0].set_value(False).run()  # sin animaciones
    assert not at.exception
