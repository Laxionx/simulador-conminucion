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
