"""«Comparar con tu planta» en «Chancado primario»: la calibración de k con una capacidad medida
(k·f × modelo = medido), la inversa de Nordberg para el P80, el caso limitado por el motor, la
guarda de plausibilidad y los botones en la app (AppTest)."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
sys.path.insert(0, str(ROOT / "app"))

import i18n  # noqa: E402
import mandibula_datos as md  # noqa: E402
import planta_datos as pd_  # noqa: E402

from conminucion.datos_mandibula import K_CAL, TABLA_KING  # noqa: E402
from conminucion.mandibula_producto import nordberg_cumulative, nordberg_p80_over_oss  # noqa: E402

EJEMPLO = md.ejemplo()
Q_EJ = EJEMPLO.jaw.capacity_tph()  # volumétrica con k de King; el motor del ejemplo no limita
LIMITADO = md.calcular({**md.valores_por_defecto(), "power": 12.0})  # motor chico: limita


def calibrar(c: md.Calculo, q: float) -> md.Calculo:
    cap = pd_.comparar_capacidad(c, q)
    return md.calcular({**c.v, "kf": cap.f})


# ------------------------------------------------------------------ capacidad
def test_el_ejemplo_no_esta_limitado_por_el_motor():
    assert Q_EJ <= EJEMPLO.jaw.motor_limit_tph(EJEMPLO.carga, EJEMPLO.prod_chancador)
    assert pd_.factor_k(EJEMPLO) == 1.0


@pytest.mark.parametrize("q", [20.0, 40.0, 58.4, 70.0, 90.0])
def test_k_por_f_por_el_modelo_da_exactamente_lo_medido(q):
    cap = pd_.comparar_capacidad(EJEMPLO, q)
    assert cap.estado == "ok" and cap.calibrable
    assert cap.f == pytest.approx(q / Q_EJ, rel=1e-15)
    assert cap.k_planta == pytest.approx(EJEMPLO.jaw.k * cap.f, rel=1e-15)
    cal = calibrar(EJEMPLO, q)
    assert cal.jaw.capacity_tph() == pytest.approx(q, rel=1e-9)
    assert cal.capacidad == pytest.approx(q, rel=1e-9)  # la efectiva, la de los indicadores
    assert cal.jaw.k == pytest.approx(cap.k_planta, rel=1e-12)
    assert cap.delta_pct == pytest.approx(100 * (q / EJEMPLO.capacidad - 1), rel=1e-12)


def test_calibrar_dos_veces_no_acumula_el_factor():
    cal = calibrar(EJEMPLO, 40.0)
    cap = pd_.comparar_capacidad(
        cal, 40.0
    )  # se compara contra el k de King, no contra el ya calibrado
    assert cap.f == pytest.approx(40.0 / Q_EJ, rel=1e-12) and cap.k_king == pytest.approx(
        EJEMPLO.jaw.k, rel=1e-12
    )
    assert pd_.comparar_capacidad(cal, 55.0).f == pytest.approx(55.0 / Q_EJ, rel=1e-12)


def test_un_punto_de_king_como_medido_devuelve_el_k_propio_de_ese_punto():
    ok = 0
    for m in TABLA_KING:
        for oss, q_tabla in m.capacidad_tph.items():
            c = md.calcular({**md.valores_por_defecto(), **md.valores_de_equipo(m, oss)})
            cap = pd_.comparar_capacidad(c, q_tabla)
            if cap.estado != "ok":
                continue  # limitado por el motor o fuera del rango de f: no calibra
            ok += 1
            k_propio = q_tabla / c.jaw.with_(k=1.0).capacity_tph()  # k que da exacto ese punto
            assert cap.k_planta == pytest.approx(k_propio, rel=1e-12)
            assert md.calcular({**c.v, "kf": cap.f}).jaw.capacity_tph() == pytest.approx(
                q_tabla, rel=1e-9
            )
    assert ok >= 20  # la mayoría de los 60 puntos de la tabla se puede calibrar
    assert 1.0 < K_CAL < 3.0  # el k de King por defecto, como referencia


def test_el_caso_limitado_por_el_motor_no_se_puede_calibrar():
    assert LIMITADO.capacidad < LIMITADO.jaw.capacity_tph()  # el motor manda
    cap = pd_.comparar_capacidad(LIMITADO, 30.0)
    assert cap.estado == "motor" and not cap.calibrable
    assert cap.q_motor == pytest.approx(LIMITADO.capacidad)
    # con motor limitante, k no cambia la capacidad efectiva: no hay nada que calibrar
    otro = md.calcular({**LIMITADO.v, "kf": 1.3})
    assert otro.capacidad == pytest.approx(LIMITADO.capacidad)


def test_lo_medido_sobre_lo_que_permite_el_motor_no_calibra():
    motor = EJEMPLO.jaw.motor_limit_tph(EJEMPLO.carga, EJEMPLO.prod_chancador)
    assert Q_EJ < motor < 5 * Q_EJ  # f queda en rango: lo único que falla es el motor
    cap = pd_.comparar_capacidad(EJEMPLO, motor * 1.01)
    assert cap.estado == "motor_medido" and not cap.calibrable
    assert pd_.comparar_capacidad(EJEMPLO, motor * 0.99).estado == "ok"


@pytest.mark.parametrize("q", [Q_EJ * 0.19, Q_EJ * 5.01, 0.1, 5000.0])
def test_guarda_de_plausibilidad_f_fuera_de_0_2_a_5(q):
    cap = pd_.comparar_capacidad(EJEMPLO, q)
    assert cap.estado in ("rango", "motor_medido") and not cap.calibrable
    assert not 0.2 <= cap.f <= 5.0 or cap.estado == "motor_medido"


def test_el_factor_se_valida_en_el_servidor_y_el_valor_por_defecto_no_cambia_nada():
    for kf in (0.19, 5.01, float("nan"), float("inf"), "x", True):
        assert md.validar({**md.valores_por_defecto(), "kf": kf}) is not None
    assert md.validar({**md.valores_por_defecto(), "kf": 2.5}) is None
    con_uno = md.calcular({**md.valores_por_defecto(), "kf": 1.0})
    assert con_uno.capacidad == EJEMPLO.capacidad and con_uno.jaw.k == EJEMPLO.jaw.k


def test_una_medicion_invalida_se_rechaza():
    for q in (0.0, -1.0, float("nan")):
        with pytest.raises(ValueError, match="positiva"):
            pd_.comparar_capacidad(EJEMPLO, q)
        with pytest.raises(ValueError, match="positivo"):
            pd_.comparar_p80(EJEMPLO, q)


# ------------------------------------------------------------------ P80
def test_la_inversa_de_nordberg_es_exacta():
    razon = nordberg_p80_over_oss()
    assert nordberg_cumulative(razon) == pytest.approx(0.8, abs=1e-12)
    for oss in (20.0, 76.2, 150.0):
        r = pd_.comparar_p80(EJEMPLO, razon * oss)
        assert r.oss_implicito == pytest.approx(oss, rel=1e-13)
    assert razon == pytest.approx(0.905, abs=0.001)


def test_p80_desgaste_estimado_y_casos():
    razon = nordberg_p80_over_oss()
    nominal = EJEMPLO.jaw.oss_mm
    igual = pd_.comparar_p80(EJEMPLO, razon * nominal)
    assert igual.estado == "ok" and igual.diferencia == pytest.approx(0, abs=1e-12)
    gastado = pd_.comparar_p80(EJEMPLO, razon * (nominal + 8.0))
    assert gastado.estado == "ok" and gastado.desgaste == pytest.approx(8.0, rel=1e-12)
    # aplicar ese desgaste mueve el OSS nominal al implícito
    con_desgaste = md.calcular({**EJEMPLO.v, "wear": gastado.desgaste})
    assert con_desgaste.jaw.oss_mm == pytest.approx(gastado.oss_implicito, rel=1e-12)
    fino = pd_.comparar_p80(EJEMPLO, razon * (nominal - 3.0))
    assert fino.estado == "neg" and not fino.aplicable
    fuera = pd_.comparar_p80(EJEMPLO, razon * (nominal + 61.0))
    assert fuera.estado == "fuera" and not fuera.aplicable


def test_con_desgaste_previo_el_control_recibe_el_desgaste_total():
    previo = md.calcular({**md.valores_por_defecto(), "wear": 10.0})
    razon = nordberg_p80_over_oss()
    r = pd_.comparar_p80(previo, razon * (previo.jaw.oss_mm + 5.0))
    assert r.oss_nominal == pytest.approx(previo.jaw.oss_mm)  # el nominal ya incluye los 10 mm
    assert r.diferencia == pytest.approx(5.0) and r.desgaste == pytest.approx(15.0)


# ------------------------------------------------------------------ la app
def run(lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["lang"] = lang
    return at.run()


def boton(at: AppTest, texto: str):
    return next((b for b in at.button if b.label == texto), None)


def capacidad(at: AppTest) -> str:
    return next(
        m.value for m in at.metric if m.label.startswith(("Capacidad (t/h)", "Capacity (t/h)"))
    )


def test_sin_medidas_la_seccion_solo_muestra_los_campos_y_nada_cambia():
    at = run()
    assert not at.exception and len(at.metric) == 12
    assert at.number_input(key="jaw_q_med").value is None
    assert boton(at, "Usar mi calibración") is None and boton(at, "Volver al k de King") is None
    assert capacidad(at) == "58,4"


def test_los_botones_calibran_y_vuelven_al_k_de_king_en_es():
    at = run()
    at.number_input(key="jaw_q_med").set_value(40.0).run()
    assert any("Factor de planta f" in m.value and "0,685" in m.value for m in at.markdown)
    boton(at, "Usar mi calibración").click().run()
    assert at.session_state["jaw_kf"] == pytest.approx(40.0 / Q_EJ, rel=1e-12)
    assert capacidad(at) == "40,0"
    assert any("Calibrado con tu planta (f = 0,685)" in c.value for c in at.caption)
    assert (
        sum("Calibrado con tu planta" in c.value for c in at.caption) == 2
    )  # indicadores y curvas
    assert boton(at, "Volver al k de King") is not None
    boton(at, "Volver al k de King").click().run()
    assert at.session_state["jaw_kf"] == 1.0 and capacidad(at) == "58,4"
    assert not any("Calibrado con tu planta" in c.value for c in at.caption)


def test_los_botones_en_ingles():
    with i18n.use("en"):  # el radio de la fuente de datos formatea sus opciones con t()
        at = run("en")
        at.number_input(key="jaw_q_med").set_value(40.0).run()
        boton(at, "Use my calibration").click().run()
        assert capacidad(at) == "40.0"
        assert any("Calibrated with your plant (f = 0.685)" in c.value for c in at.caption)
        boton(at, "Back to King's k").click().run()
        assert capacidad(at) == "58.4"


def test_con_el_motor_limitando_avisa_y_no_ofrece_el_boton():
    at = run()
    at.number_input(key="jaw_power").set_value(12.0).run()
    at.number_input(key="jaw_q_med").set_value(30.0).run()
    assert any("el motor limita" in w.value for w in at.warning)
    assert boton(at, "Usar mi calibración") is None


def test_f_implausible_avisa_y_no_se_aplica():
    at = run()
    at.number_input(key="jaw_q_med").set_value(2.0).run()
    assert any("revisa unidades o condiciones" in w.value for w in at.warning)
    assert boton(at, "Usar mi calibración") is None
    assert "jaw_kf" not in at.session_state or at.session_state["jaw_kf"] == 1.0


def test_el_p80_pone_el_desgaste_en_el_control():
    at = run()
    razon = nordberg_p80_over_oss()
    at.number_input(key="jaw_p80_med").set_value(round(razon * (EJEMPLO.jaw.oss_mm + 6.0), 3)).run()
    boton(at, "Poner ese desgaste en el control").click().run()
    assert at.number_input(key="jaw_wear").value == pytest.approx(6.0, abs=0.01)


def test_p80_mas_fino_que_nordberg_avisa_sin_boton():
    at = run()
    at.number_input(key="jaw_p80_med").set_value(5.0).run()
    assert any("más fino que la curva de Nordberg" in w.value for w in at.warning)
    assert boton(at, "Poner ese desgaste en el control") is None
