"""Español e inglés: mismas claves, mismas cifras, sin restos de un idioma en el otro, y el
parámetro `?lang=` validado."""

import ast
import json
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
sys.path.insert(0, str(ROOT / "app"))

import animaciones  # noqa: E402
import controles  # noqa: E402
import equipos  # noqa: E402
import guia  # noqa: E402
import i18n  # noqa: E402
import modelo_en  # noqa: E402
import tablas  # noqa: E402
from i18n import TEXTS  # noqa: E402

from conminucion.circuits import CircuitConfig, simulate  # noqa: E402
from conminucion.classifier import EfficiencyCurve  # noqa: E402
from conminucion.mill import AustinSelection, BallMill  # noqa: E402
from conminucion.sizes import SizeGrid, rosin_rammler  # noqa: E402
from conminucion.stream import Stream  # noqa: E402

ES, EN = TEXTS["es"], TEXTS["en"]
KINDS = ("abierto", "cerrado_directo", "cerrado_inverso")
# restos de español que no deben aparecer en un texto en inglés
SPANISH = re.compile(
    r"[áéíóúñ¿¡]|\b(de|del|la|las|los|el|con|para|por|una|sin|que|se|más|muy)\b", re.IGNORECASE
)


def spanish_left(text: str) -> bool:
    return bool(SPANISH.search(re.sub(r"\{[^}]*\}|`[^`]*`", "", text)))


def run(lang: str | None = None, **values) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    if lang is not None:
        at.query_params["lang"] = lang
    at.run()
    for key, value in values.items():
        for w in [*at.sidebar.number_input, *at.sidebar.slider, *at.sidebar.selectbox,
                  *at.sidebar.radio]:  # fmt: skip
            if w.key == "dato_" + key:
                if key == "kind" or key == "param":
                    with i18n.use(lang or "es"):
                        value = i18n.opt(value)  # las listas muestran el rótulo del idioma
                w.set_value(value)
    if values:
        at.run()
    return at


def _cfg() -> CircuitConfig:
    grid = SizeGrid.geometric(9500.0, 17)
    fresh = Stream.from_fractions(grid, rosin_rammler(grid, 3200.0, 1.0), 100.0, 0.0, 2.7)
    return CircuitConfig(fresh, BallMill(AustinSelection(), n_mixers=3), EfficiencyCurve())


# ------------------------------------------------------------------ las claves
def test_los_dos_idiomas_tienen_las_mismas_claves():
    assert set(ES) == set(EN), sorted(set(ES) ^ set(EN))


def test_cada_texto_tiene_los_mismos_campos_en_los_dos_idiomas():
    for key in ES:
        assert i18n.fields(ES[key]) == i18n.fields(EN[key]), key


def test_ningun_texto_esta_vacio_y_solo_los_cognados_son_iguales_en_los_dos_idiomas():
    assert not {k for k in ES if not ES[k].strip() or not EN[k].strip()}
    same = {k for k in ES if ES[k] == EN[k]}
    # símbolos (α, μ, d50c...), fórmulas, unidades, «Balance», «Wegstein» y textos de solo campos
    assert same == {
        "dato.A.label", "dato.a.label", "dato.beta.label", "dato.d50c.label", "dato.gamma.label",
        "dato.k.label", "dato.lam.label", "dato.m.label", "dato.mu.label", "dato.x63.label",
        "method.wegstein", "opt.Austin (S, τ)", "out.5.name", "step.1.latex", "step.2.latex",
        "step.3.latex", "step.4.latex", "step.5.latex", "svg.flow.stream", "svg.mill.dims",
        "tcol.P80_um", "tid.overflow", "tid.underflow",
    }  # fmt: skip


def _literals_and_prefixes() -> tuple[set[str], set[str]]:
    literals, prefixes = set(), set()
    for path in (ROOT / "app").glob("*.py"):
        if path.name.startswith("textos_"):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.add(node.value)
            if isinstance(node, ast.JoinedStr) and node.values:
                first = node.values[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    prefixes.add(first.value)
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Add)
                and isinstance(node.left, ast.Constant)
                and isinstance(node.left.value, str)
            ):
                prefixes.add(node.left.value)
    return literals, {p for p in prefixes if "." in p and len(p) >= 3}


def test_no_hay_claves_sin_usar():
    literals, prefixes = _literals_and_prefixes()
    unused = [k for k in ES if k not in literals and not any(k.startswith(p) for p in prefixes)]
    assert not unused, unused


def test_las_familias_dinamicas_estan_completas():
    for d in controles.DATOS:
        assert d.label_k in ES and d.meaning_k in ES and d.source_k in ES, d.key
        assert "group." + d.group in ES
    for name, group in controles.CHOICES:
        for part in ("label", "meaning"):
            assert f"choice.{name}.{part}" in ES
        assert "group." + group in ES
    for kind in KINDS:
        assert f"circuit.{kind}" in ES and f"opt.{kind}" in ES
    for sel in controles.SELECTIONS:
        assert "opt." + sel in ES
    for i in range(1, guia.N_STEPS + 1):
        assert all(f"step.{i}.{p}" in ES for p in ("title", "text", "latex"))
    assert f"step.{guia.N_STEPS + 1}.title" not in ES
    for i in range(1, guia.N_OUTPUTS + 1):
        assert f"out.{i}.name" in ES and f"out.{i}.text" in ES
    assert f"out.{guia.N_OUTPUTS + 1}.name" not in ES
    assert all(f"limit.{i}" in ES for i in range(1, guia.N_LIMITS + 1))
    assert f"limit.{guia.N_LIMITS + 1}" not in ES
    for stream in equipos.STREAM_COLORS:
        assert "stream." + stream in ES and "tid." + stream in ES
    cfg = _cfg()
    for kind in KINDS:
        res = simulate(kind, cfg)
        assert all("tcol." + c in ES for c in res.table().columns)
        assert all(c == "tamiz_um" or "tid." + c in ES for c in res.passing_table().columns)


def test_los_textos_en_ingles_no_llevan_palabras_en_espanol():
    bad = {k: v[:80] for k, v in EN.items() if spanish_left(v)}
    assert not bad, bad


# ------------------------------------------------------------------ el idioma y la URL
@pytest.mark.parametrize("value", ["fr", "EN", "es ", "", "en;alert(1)", "<script>", "../en"])
def test_un_parametro_lang_invalido_es_espanol_sin_error(value):
    at = run(value)
    assert not at.exception
    assert at.tabs[0].label == "Guía"
    assert at.sidebar.radio[0].value == "es"
    assert at.query_params["lang"] in (["es"], "es")


def test_parse_lang_solo_acepta_es_y_en():
    assert [i18n.parse_lang(v) for v in ("es", "en")] == ["es", "en"]
    assert {i18n.parse_lang(v) for v in ("fr", None, 3, ["en"], "EN", " en")} == {"es"}


def test_lang_en_en_la_url_abre_en_ingles_y_el_selector_cambia_el_idioma():
    en = run("en")
    assert [t.label for t in en.tabs] == [
        "Guide", "Simulation", "Fitting to data (synthetic survey)"
    ]  # fmt: skip
    assert en.sidebar.radio[0].value == "en"
    en.sidebar.radio[0].set_value("es").run()
    assert en.tabs[0].label == "Guía"
    assert en.query_params["lang"] in (["es"], "es")
    es_ = run()
    es_.sidebar.radio[0].set_value("en").run()
    assert es_.tabs[0].label == "Guide" and not es_.exception


def test_el_valor_de_lang_nunca_llega_al_html_ni_al_svg():
    at = run("en<script>alert(1)</script>")
    blob = json.dumps([m.value for m in at.markdown] + [c.value for c in at.caption])
    assert "alert(1)" not in blob and "<script" not in blob.lower()


def test_los_datos_y_las_listas_se_conservan_al_cambiar_de_idioma():
    at = run("es", tph=250.0, kind="cerrado_inverso", param="Nudos r/d")
    at.sidebar.radio[0].set_value("en").run()
    tph = next(w for w in at.sidebar.number_input if w.key == "dato_tph")
    kind = next(w for w in at.sidebar.selectbox if w.key == "dato_kind")
    param = next(w for w in at.sidebar.radio if w.key == "dato_param")
    assert tph.value == 250.0
    assert kind.value == "Reverse closed circuit" and param.value == "Knots r/d"
    at.sidebar.radio[0].set_value("es").run()
    kind = next(w for w in at.sidebar.selectbox if w.key == "dato_kind")
    assert kind.value == "Circuito cerrado inverso" and not at.exception


# ------------------------------------------------------------------ humo de todas las pestañas
@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("lang", ["es", "en"])
def test_humo_de_todas_las_pestanas(lang, kind):
    at = run(lang, kind=kind)
    assert not at.exception and not at.error
    assert len(at.tabs) == 3 and len(at.metric) == 6
    assert at.sidebar.selectbox[0].value == i18n_opt(lang, kind)


def i18n_opt(lang: str, raw: str) -> str:
    with i18n.use(lang):
        return i18n.opt(raw)


# ------------------------------------------------------------------ mismas cifras
_NUMBER = {
    "es": re.compile(r"-?\d+(?: \d{3})*(?:[.,]\d+)?(?:e-?\d+)?"),
    "en": re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:e-?\d+)?"),
}


def _numbers(text: str, lang: str) -> list[float]:
    """Los números de un texto, leídos con el formato de su idioma."""
    out = []
    for item in _NUMBER[lang].findall(text.replace("\xa0", " ")):
        item = item.replace(",", "") if lang == "en" else item.replace(" ", "").replace(",", ".")
        out.append(float(item))
    return out


def _figures(at: AppTest, lang: str) -> list:
    parts = [str(m.value) for m in at.metric] + [m.delta for m in at.metric]
    out = [_numbers(p or "", lang) for p in parts]
    for df in at.dataframe:
        for row in df.value.values.tolist():
            out.append([x for x in row if isinstance(x, int | float)])
    for md in at.markdown:
        if md.value.startswith("| "):
            for line in md.value.splitlines()[2:]:
                out.append([_numbers(c, lang) for c in line.strip("| ").split(" | ")])
    return out


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"tph": 250.0, "d50c": 150.0, "pct": 55},
        {"kind": "abierto", "top": 12000.0, "n": 14},
        {"kind": "cerrado_inverso", "diameter": 5.0, "filling": 40, "speed": 70, "wi": 18.0},
        {"dist": "Gaudin-Schuhmann", "param": "Nudos r/d"},
    ],
)
def test_las_cifras_son_identicas_en_los_dos_idiomas(values):
    es_, en = run("es", **values), run("en", **values)
    assert not es_.exception and not en.exception
    a, b = _figures(es_, "es"), _figures(en, "en")
    assert len(a) == len(b) > 20 and a == b
    assert len(es_.metric) == len(en.metric) == 6


# ------------------------------------------------------------------ los gráficos y los esquemas
def _fig_text(fig) -> str:
    return json.dumps(fig.to_plotly_json(), ensure_ascii=False)


def test_los_graficos_en_ingles_no_llevan_espanol_y_en_espanol_siguen_igual():
    cfg = _cfg()
    res = simulate("cerrado_directo", cfg)
    other = simulate("cerrado_directo", cfg, wegstein=False)
    histories = {"A": res.solution.tear_history, "B": other.solution.tear_history}
    sieves = res.streams["alimentacion_fresca"].grid.sieves
    for lang in ("es", "en"):
        with i18n.use(lang):
            figs = [
                animaciones.convergence_figure(100.0, histories),
                animaciones.journey_figure(
                    animaciones.journey("cerrado_directo", res, cfg), sieves
                ),
                animaciones.passing_figure(res.streams),
            ]  # fmt: skip
            blob = " ".join(_fig_text(f) for f in figs)
        texts = re.findall(r'"(?:text|title|name|label)": "([^"]+)"', blob)
        texts += re.findall(r'"title": \{"text": "([^"]+)"', blob)
        if lang == "en":
            assert not [x for x in texts if spanish_left(x)], [x for x in texts if spanish_left(x)]
            assert "Play" in blob and "Pause" in blob and "Cyclone feed" in blob
        else:
            assert "Reproducir" in blob and "Pausa" in blob and "Alimentación al ciclón" in blob


def test_los_esquemas_en_ingles_no_llevan_espanol():
    cfg = _cfg()
    for lang in ("es", "en"):
        svgs = []
        with i18n.use(lang):
            for kind in KINDS:
                res = simulate(kind, cfg)
                svgs.append(equipos.flowsheet_svg(kind, res.streams, 3.0))
                svgs.append(equipos.flowsheet_svg(kind, res.streams, 3.0, True))
            s = res.streams
            svgs.append(equipos.mill_svg(4.0, 6.0, 0.38, 0.75, 75.0, 2500.0, 120.0))
            svgs.append(equipos.cyclone_svg(s["alim_ciclon"], s["underflow"], s["overflow"]))
        blob = " ".join(svgs)
        texts = re.findall(r">([^<]+)</text>", blob) + re.findall(r'aria-label="([^"]+)"', blob)
        if lang == "en":
            assert not [x for x in texts if spanish_left(x)], [x for x in texts if spanish_left(x)]
            for expected in ("Ball mill", "Hydrocyclone", "Sump and pump", "Power at the pinion"):
                assert any(expected in x for x in texts), expected
        else:
            for expected in ("Molino de bolas", "Hidrociclón", "Cajón y bomba", "Potencia"):
                assert any(expected in x for x in texts), expected


def test_los_numeros_de_los_esquemas_cambian_de_formato_pero_no_de_valor():
    cfg = _cfg()
    res = simulate("cerrado_directo", cfg)
    with i18n.use("es"):
        es_svg = equipos.flowsheet_svg("cerrado_directo", res.streams, 3.0)
    with i18n.use("en"):
        en_svg = equipos.flowsheet_svg("cerrado_directo", res.streams, 3.0)
    solids = f"{res.streams['alimentacion_fresca'].total_solids:.1f}"
    assert f"{solids.replace('.', ',')} t/h" in es_svg and f"{solids} t/h" in en_svg


def test_formato_de_numeros_por_idioma():
    with i18n.use("es"):
        assert i18n.num(1234.5, 1) == "1 234,5" and i18n.num(0.5, 2) == "0,50"
        assert i18n.int_num(20000) == "20 000" and i18n.num_g(2.5) == "2,5"
    with i18n.use("en"):
        assert i18n.num(1234.5, 1) == "1,234.5" and i18n.num(0.5, 2) == "0.50"
        assert i18n.int_num(20000) == "20,000" and i18n.num_g(2.5) == "2.5"


# ---------------------------------------------------- tablas, CSV y errores del modelo
def test_las_tablas_y_el_csv_llevan_los_encabezados_del_idioma():
    res = simulate("cerrado_directo", _cfg())
    with i18n.use("en"):
        stream = tablas.stream_table(res.table())
        passing = tablas.passing_table(res.passing_table())
        assert list(stream.columns) == ["stream", "solids_t_h", "water_t_h", "pct_solids", "P80_um"]
        assert list(passing.columns)[:3] == ["sieve_um", "fresh_feed", "underflow"]
        assert stream["solids_t_h"].tolist() == res.table()["solidos_t_h"].tolist()
        assert not spanish_left(stream.to_csv(index=False) + passing.to_csv(index=False))
    with i18n.use("es"):
        assert list(tablas.stream_table(res.table()).columns) == list(res.table().columns)
        assert list(tablas.passing_table(res.passing_table()).columns) == list(
            res.passing_table().columns
        )


def test_los_errores_del_modelo_se_traducen():
    msg = "No convergió en 500 iteraciones (error relativo 1,234e-03 > 1e-09)"
    with i18n.use("en"):
        assert i18n.tr_error(msg) == (
            "It did not converge in 500 iterations (relative error 1.234e-03 > 1e-09)"
        )
        assert i18n.tr_error("No convergió en 500 iteraciones") == (
            "It did not converge in 500 iterations"
        )
        assert i18n.tr_error("algo desconocido") == "algo desconocido"
    with i18n.use("es"):
        assert i18n.tr_error(msg) == msg
    assert all(re.compile(p) for p, _ in modelo_en.ERRORS)


@pytest.mark.parametrize("lang", ["es", "en"])
def test_si_el_circuito_no_converge_se_avisa_en_cada_idioma_sin_traza(monkeypatch, lang):
    import conminucion.circuits as circuits
    from conminucion.flowsheet import ConvergenceError

    def no_converge(*args, **kwargs):
        raise ConvergenceError("No convergió en 500 iteraciones (error relativo 2e-03 > 1e-09)")

    monkeypatch.setattr(circuits, "simulate", no_converge)
    at = run(lang)
    assert not at.exception
    assert len(at.error) == 1
    expected = "It did not converge in 500 iterations" if lang == "en" else "No convergió"
    assert expected in at.error[0].value
    assert any(expected in w.value or "reconcil" in w.value.lower() for w in at.warning)


# ------------------------------------------------------------------ README y GIF
def test_los_readme_se_enlazan_entre_si_y_los_gif_existen_y_pesan_menos_de_3_mb():
    es_, en = (ROOT / "README.md").read_text("utf-8"), (ROOT / "README.en.md").read_text("utf-8")
    assert es_.splitlines()[0] == "[English version](README.en.md)"
    assert en.splitlines()[0] == "[Versión en español](README.md)"
    assert "?lang=en" in en
    for readme, name in ((es_, "molino-ciclon.es.gif"), (en, "mill-cyclone.en.gif")):
        assert f"docs/img/{name}" in readme
        gif = ROOT / "docs" / "img" / name
        assert gif.read_bytes()[:6] in (b"GIF89a", b"GIF87a")
        assert 0 < gif.stat().st_size < 3_000_000


def test_el_ingles_usa_comillas_inglesas_y_no_las_espanolas():
    bad = [k for k, v in EN.items() if "«" in v or "»" in v]
    assert not bad, bad
