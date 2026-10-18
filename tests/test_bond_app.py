"""La pestaña «Ensayo de Bond» dentro de la app: humo en los dos idiomas, edición de la tabla,
valores manipulados y un fuzz de 30 combinaciones por idioma (30 % extremas)."""

import json
import random
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
sys.path.insert(0, str(ROOT / "app"))

import bond_datos as bd  # noqa: E402

TABLE = bd.TABLE_KEY
SEED, N_FUZZ, EXTREME_SHARE = 20261018, 30, 0.30


def run(lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["lang"] = lang
    return at.run()


def edit(at: AppTest, edited: dict | None = None, added: list | None = None, deleted=None):
    at.session_state[TABLE] = {
        "edited_rows": edited or {},
        "added_rows": added or [],
        "deleted_rows": deleted or [],
    }
    return at.run()


def md(at: AppTest, needle: str) -> str:
    return next((m.value for m in at.markdown if needle in m.value), "")


def number_input(at: AppTest, key: str):
    return next(w for w in at.number_input if w.key == bd.PREFIX + key)


# ------------------------------------------------------------------ humo
@pytest.mark.parametrize(
    ("lang", "tab", "wi", "gbp"),
    [("es", "Ensayo de Bond", "10,92", "2,5811"), ("en", "Bond test", "10.92", "2.5811")],
)
def test_humo_de_la_pestana_en_cada_idioma(lang, tab, wi, gbp):
    at = run(lang)
    assert not at.exception and not at.error
    assert [t.label for t in at.tabs][-1] == tab
    calc = md(at, "Gbp**" if lang == "en" else "Gbp final**")
    assert f"Wi = {wi} kWh/t" in calc and gbp in calc
    assert len(at.metric) == 6  # la pestaña no agrega métricas a las de siempre
    n_cycles = max(len(d.value) for d in at.dataframe)
    assert n_cycles == 11  # la tabla calculada tiene un renglón por ciclo


def test_los_campos_de_la_pestana_son_los_de_la_definicion_unica():
    at = run()
    keys = {w.key for w in at.number_input if str(w.key).startswith(bd.PREFIX)}
    assert keys == {bd.PREFIX + c.key for c in bd.CAMPOS}
    for c in bd.CAMPOS:
        w = number_input(at, c.key)
        assert (w.min, w.max, w.value) == (c.lo, c.hi, c.default)


def test_el_resultado_negativo_se_informa_tal_cual_en_la_app():
    at = run()
    res = md(at, "Wi (kWh/t): simulado")
    assert "fuera del corte" in res and "dentro del corte" in res  # Gbp pasa; P80 y Wi no
    assert "9,59" in res and "2,7439" in res


def test_el_selector_de_ciclo_cambia_el_texto_del_molino():
    at = run()
    base = md(at, "Ciclo 11 de 11")
    assert "99 revoluciones a 70 rpm = 84,9 s" in base
    sl = next(w for w in at.slider if w.key == "bond_ciclo")
    sl.set_value(1).run()
    assert not at.exception
    assert "Ciclo 1 de 11: 100 revoluciones a 70 rpm = 85,7 s" in md(at, "Ciclo 1 de 11")


def test_apagar_el_movimiento_no_rompe_la_pestana():
    at = run()
    at.toggle[0].set_value(False).run()
    assert not at.exception


# ------------------------------------------------------------------ la tabla editable
def test_editar_la_tabla_cambia_la_calculadora():
    at = run()
    antes = md(at, "Gbp final**")
    at = edit(at, {10: {"finos": 395.0}})  # el último ciclo, de 382,5 a 395,0 g
    assert not at.exception and not at.warning
    despues = md(at, "Gbp final**")
    assert despues != antes and "Wi =" in despues


def test_agregar_y_quitar_ciclos():
    at = run()
    at = edit(at, added=[{"finos": 390.0}, {"finos": 391.0}])
    assert not at.exception and max(len(d.value) for d in at.dataframe) == 13
    at = edit(at, deleted=[0, 1, 2, 3, 4, 5, 6])
    assert not at.exception


@pytest.mark.parametrize(
    "malo", [None, float("nan"), float("inf"), -5.0, 1e12, "texto", "<script>x</script>"]
)
def test_una_celda_manipulada_avisa_sin_caerse_ni_llegar_al_html(malo):
    at = edit(run(), {3: {"finos": malo}})
    assert not at.exception
    blob = json.dumps([m.value for m in at.markdown] + [w.value for w in at.warning])
    assert "<script" not in blob.lower()
    assert at.warning or md(at, "Gbp final**")  # o avisa, o Streamlit la dejó en su valor


def test_una_tabla_sin_ciclos_avisa():
    at = edit(run(), deleted=list(range(11)))
    assert not at.exception and any("entre 1 y 30" in w.value for w in at.warning)


def test_un_ciclo_sin_finos_nuevos_avisa():
    at = edit(run(), {0: {"finos": 300.0}})
    assert not at.exception and any("no cuadran" in w.value for w in at.warning)


FUERA_DE_RANGO = [(c.key, 1e12) for c in bd.CAMPOS] + [
    ("rev1", float("nan")),  # el entero que rompía el deserializador de Streamlit
    ("rev1", float("inf")),
    ("carga", float("nan")),
    ("carga", -5),
]


@pytest.mark.parametrize(("key", "value"), FUERA_DE_RANGO)
def test_el_servidor_devuelve_al_valor_por_defecto_un_campo_fuera_de_rango(key, value):
    at = run()
    number_input(at, key).set_value(value).run()
    assert not at.exception
    assert number_input(at, key).value == next(c.default for c in bd.CAMPOS if c.key == key)


def test_volver_al_ejemplo_restaura_la_tabla_y_los_campos():
    at = run()
    number_input(at, "carga").set_value(2000.0).run()
    at = edit(at, {0: {"finos": 500.0}})
    next(b for b in at.button if "Hebei" in b.label).click().run()
    assert not at.exception and number_input(at, "carga").value == 1365.0
    assert "Wi = 10,92" in md(at, "Gbp final**")


def test_al_cambiar_de_idioma_se_conservan_los_datos_de_la_pestana():
    at = run()
    number_input(at, "carga").set_value(1400.0).run()
    at.sidebar.radio[0].set_value("en").run()
    assert not at.exception and number_input(at, "carga").value == 1400.0


# ------------------------------------------------------------------ fuzz
def _fuzz_cases(rng: random.Random):
    """30 combinaciones: ~30 % extremas (límites, fuera de rango, celdas rotas, 30 ciclos)."""
    cases = []
    for i in range(N_FUZZ):
        extreme = i < round(N_FUZZ * EXTREME_SHARE)
        campos = {}
        for c in bd.CAMPOS:
            if extreme and rng.random() < 0.5:
                campos[c.key] = rng.choice([c.lo, c.hi, c.hi * 10, -1.0, float("nan")])
            else:
                v = rng.uniform(c.lo, c.hi)
                campos[c.key] = int(v) if c.integer else round(v, 1)
        n = rng.choice([0, 1, 30, 31]) if extreme else rng.randint(2, 15)
        added = [{"finos": rng.uniform(0, 600)} for _ in range(max(n - 11, 0))]
        deleted = list(range(11 - n)) if n < 11 else []
        edited = {j: {"finos": rng.choice([None, float("nan"), 0.0, bd.FINOS_MAX, 1e12])}
                  for j in rng.sample(range(11), 3)} if extreme else {}  # fmt: skip
        cases.append((campos, edited, added, deleted, rng.random() < 0.5, rng.randint(1, 11)))
    rng.shuffle(cases)
    return cases


@pytest.mark.parametrize("lang", ["es", "en"])
def test_fuzz_de_30_combinaciones_no_tira_excepciones(lang):
    at = run(lang)
    for campos, edited, added, deleted, mover, ciclo in _fuzz_cases(random.Random(SEED)):
        for key, value in campos.items():
            number_input(at, key).set_value(value)
        next(w for w in at.slider if w.key == "bond_ciclo").set_value(ciclo)
        at.toggle[0].set_value(mover)
        at.session_state[TABLE] = {"edited_rows": edited, "added_rows": added,
                                   "deleted_rows": deleted}  # fmt: skip
        at.run()
        assert not at.exception, (campos, edited, added, deleted)
        assert not at.error
        blob = json.dumps([m.value for m in at.markdown] + [w.value for w in at.warning])
        assert not re.search(r"Traceback|nan kWh|inf kWh", blob)
