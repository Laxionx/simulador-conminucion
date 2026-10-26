"""«Estado de la operación» y «Prueba esto» de la pestaña Simulación: el ejemplo está en rango, cada
experimento hace lo que dice su texto y sus botones ponen el cambio en la barra lateral."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
sys.path.insert(0, str(ROOT / "app"))

import i18n  # noqa: E402
import sim_estado as se  # noqa: E402
from equipos import es  # noqa: E402


def run(lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["lang"] = lang
    return at.run()


def lines(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown]


def test_el_ejemplo_de_la_simulacion_esta_en_rango_y_es_el_de_la_barra_lateral():
    base = se.evaluar()
    at = run()
    p80 = next(m for m in at.metric if m.label == "P80 del producto (µm)")
    assert p80.value == es(base.p80, 1)
    cl = next(m for m in at.metric if m.label == "Carga circulante")
    assert cl.value == es(base.carga, 3)
    disp = next(m for m in at.metric if m.label == "Energía que entrega el molino (kWh/t)")
    assert disp.value == es(base.disp, 2)
    with i18n.use("es"):
        filas = se.filas_estado(
            se.KIND0,
            base.res,
            se.potencia_molino(
                se.build_config(se.valores_ejemplo(), se.DISTRIBUTIONS[0], se.SELECTIONS[0])[1]
            ),
            True,
        )
    assert [f.nivel for f in filas] == ["ok", "ok", "ok"]


@pytest.mark.parametrize("exp", se.EXPERIMENTOS_SIM, ids=lambda e: e.clave)
def test_cada_experimento_de_simulacion_hace_lo_que_dice_su_texto(exp):
    base = se.evaluar()
    nuevo = se.evaluar(exp.kind, **exp.cambios)
    mag = {
        "p80": lambda r: r.p80, "bond": lambda r: r.bond, "disp": lambda r: r.disp,
        "carga": lambda r: r.carga or 0.0,
    }  # fmt: skip
    for nombre, signo in exp.direcciones.items():
        assert (mag[nombre](nuevo) - mag[nombre](base)) * signo > 0, (exp.clave, nombre)
    suficiente = nuevo.disp >= nuevo.bond
    assert exp.potencia_ok is None or suficiente == exp.potencia_ok


def test_los_numeros_de_los_experimentos_de_simulacion_y_el_caso_de_mas_velocidad():
    pares = {e.clave: (a, b) for e, a, b in se.pares()}
    a, b = pares["tph"]
    assert b.disp < b.bond < a.disp and b.bond == pytest.approx(a.bond, rel=1e-6)
    rapido = se._mas_rapido()
    assert b.disp < rapido.disp < rapido.bond  # subir la velocidad ayuda, pero no alcanza
    a, b = pares["abierto"]
    assert b.res.circulating_load is None and a.res.circulating_load > 0
    a, b = pares["d50c"]
    assert a.disp == b.disp and b.disp > b.bond  # el panel sigue en rango


@pytest.mark.parametrize("lang", ["es", "en"])
def test_los_botones_de_simulacion_ponen_el_cambio_y_el_panel_lo_refleja(lang):
    at = run(lang)
    next(b for b in at.button if b.key == "sim_prueba_tph").click().run()
    assert not at.exception and not at.error
    tph = next(w for w in at.sidebar.number_input if w.key == "dato_tph")
    assert tph.value == 150.0
    malas = [m for m in lines(at) if m.startswith(":red-badge[")]
    assert len(malas) == 1 and ("Potencia del molino" in malas[0] or "Mill power" in malas[0])
    next(b for b in at.button if b.key == "sim_prueba_abierto").click().run()
    assert not at.exception and not at.error
    kind = next(w for w in at.sidebar.selectbox if w.key == "dato_kind")
    with i18n.use(lang):
        assert kind.value == i18n.opt("abierto")
    assert any("no hay reciclo" in m or "no recycle" in m for m in lines(at))
    next(b for b in at.button if b.key == "sim_prueba_reset").click().run()
    kind = next(w for w in at.sidebar.selectbox if w.key == "dato_kind")
    with i18n.use(lang):
        assert kind.value == i18n.opt(se.KIND0) and not at.exception
