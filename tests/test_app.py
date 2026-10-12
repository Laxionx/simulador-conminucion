from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


@pytest.mark.parametrize("kind", ["abierto", "cerrado_directo", "cerrado_inverso"])
def test_app_runs_without_exceptions(kind):
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.sidebar.selectbox[0].set_value(kind).run()
    assert not at.exception
    assert not at.error
    labels = [m.label for m in at.metric]
    assert "P80 del producto (µm)" in labels


def test_app_no_se_cae_si_el_circuito_no_converge(monkeypatch):
    # Con entradas extremas el circuito cerrado puede no converger en 500 iteraciones: la app debe
    # avisar en ambas pestañas, no caerse (lo encontró un fuzz de los controles antes de publicar).
    import conminucion.circuits as circuits
    from conminucion.flowsheet import ConvergenceError

    def no_converge(*args, **kwargs):
        raise ConvergenceError("No convergió en 500 iteraciones")

    monkeypatch.setattr(circuits, "simulate", no_converge)
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert len(at.error) == 1  # la pestaña de simulación
    assert any("no convergió" in w.value.lower() for w in at.warning)  # la de ajuste


@pytest.mark.parametrize("value", [10_000_000, -5, float("inf"), float("nan")])
def test_el_servidor_rechaza_valores_fuera_de_rango(value):
    # Un cliente puede mandar valores sin pasar por el navegador: Streamlit (versión fijada en
    # requirements.txt) los devuelve al valor por defecto en el servidor.
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.sidebar.slider[0].set_value(value).run()  # número de tamices, 8 a 24
    assert not at.exception
    assert at.sidebar.slider[0].value == 17
