"""V2 y V3, escritas ANTES de ver el resultado y sin ajustarlas después: se planta un error de
+4 puntos de % pasante en una corriente y una malla de Vazante (campaña 1) y el diagnóstico
«ajuste estandarizado más grande» debe señalar esa corriente y una clase que tenga esa malla por
límite (el acumulado → retenido reparte el error entre las dos clases vecinas de la malla), con |z|
> 3, y el χ² debe empeorar. Las mallas finas ya siguen en orden tras sumar 4 puntos (la malla vecina
más gruesa queda 9 a 24 puntos por encima), así que no hay que corregir nada más."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from muestreo_datos import analizar, tabla_de_levantamiento  # noqa: E402

from conminucion.plantas_reales import VAZANTE_C1  # noqa: E402

CASOS = [("uf", 149.0), ("of", 74.0), ("alim", 298.0)]


def _con_error(corriente: str, malla: float):
    t = tabla_de_levantamiento(VAZANTE_C1).copy()
    fila = t.index[t["tamiz"] == malla][0]
    t.loc[fila, corriente] += 4.0
    return t


def test_vazante_sin_error_no_marca_nada():
    base = analizar(tabla_de_levantamiento(VAZANTE_C1), VAZANTE_C1.solidos_pct)
    assert abs(base.mayor_ajuste.z) < 3.0


@pytest.mark.xfail(
    strict=True,
    reason="RESULTADO NEGATIVO de V2/V3: el balance reparte el error entre las tres corrientes, el "
    "mayor |z| cae en la alimentación y no pasa de 3; por eso la app NO ofrece «qué mejorar»",
)
@pytest.mark.parametrize(("corriente", "malla"), CASOS)
def test_el_error_plantado_es_el_mayor_ajuste_y_el_chi2_empeora(corriente, malla):
    base = analizar(tabla_de_levantamiento(VAZANTE_C1), VAZANTE_C1.solidos_pct)
    mala = analizar(_con_error(corriente, malla), VAZANTE_C1.solidos_pct)
    m = mala.mayor_ajuste
    assert m.corriente == corriente
    assert malla in (m.inferior_um, m.superior_um)
    assert abs(m.z) > 3.0
    assert mala.chi2 > base.chi2


@pytest.mark.parametrize(("corriente", "malla"), CASOS)
def test_observacion_el_mayor_ajuste_cae_en_la_malla_plantada_pero_en_otra_corriente(
    corriente, malla
):
    """Lo que SÍ se observa (descripción posterior al resultado, no un diagnóstico): el mayor ajuste
    cae en una clase vecina de la malla plantada, siempre en la alimentación, con |z| < 3, y el χ²
    empeora; solo en uf@149 el χ² pasa el crítico al 95 %."""
    base = analizar(tabla_de_levantamiento(VAZANTE_C1), VAZANTE_C1.solidos_pct)
    mala = analizar(_con_error(corriente, malla), VAZANTE_C1.solidos_pct)
    m = mala.mayor_ajuste
    assert malla in (m.inferior_um, m.superior_um)
    assert m.corriente == "alim" and abs(m.z) < 3.0
    assert mala.chi2 > base.chi2
    assert (mala.chi2 > mala.chi2_critico) == (corriente == "uf")


def test_un_ic_imposible_se_muestra_como_no_fiable():
    """Con el error plantado en el underflow, el IC lineal del ajuste libre da un d50c y un α
    negativos: la tabla no muestra esos números sino «no fiable» (guarda de número imposible)."""
    from muestreo_tab import limite_ic, tabla_parametros

    mala = analizar(_con_error("uf", 149.0), VAZANTE_C1.solidos_pct)
    lo = {n: v[1] for n, v in mala.libre.as_dict().items()}
    assert lo["d50c"] < 0 and lo["alpha"] < 0  # el caso que motivó la guarda
    tabla = tabla_parametros(mala)
    columna_lo = tabla.iloc[:, 3].tolist()
    assert columna_lo[0] == columna_lo[1] == "no fiable"
    assert not any(str(x).startswith("-") for x in tabla.iloc[:, 3:].to_numpy().ravel())
    assert limite_ic(0.5, (0.0, 1.0)) != "no fiable" and limite_ic(1.2, (0.0, 1.0)) == "no fiable"
    assert limite_ic(0.0) == "no fiable" and limite_ic(float("nan")) == "no fiable"
