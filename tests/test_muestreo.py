"""«Ajuste a datos» con un muestreo real: V1 (Vazante cargado = camino validado, a 1e-12), la
validación de la entrada, el sin-sólidos, el molino y la pestaña en los dos idiomas. Los errores
plantados (V2/V3) están en `test_muestreo_error_plantado.py`."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from scipy import stats  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
sys.path.insert(0, str(ROOT / "app"))

import i18n  # noqa: E402
import muestreo_tab as mt  # noqa: E402
from carga import ErrorCarga, leer_tabla, mensaje_error  # noqa: E402
from controles import KNOT_RD, KNOT_SIZES  # noqa: E402
from muestreo_datos import (  # noqa: E402
    COLUMNAS_TABLA,
    analizar,
    retenidos,
    solidos_de_archivo,
    tabla_de_levantamiento,
    validar,
)

from conminucion.fitting import fit_cyclone_partition  # noqa: E402
from conminucion.fracture import Fracture  # noqa: E402
from conminucion.mill import BallMill, KnotSelection  # noqa: E402
from conminucion.plantas_reales import VAZANTE_C1, evaluar_ciclon  # noqa: E402
from conminucion.reconcile import reconcile_node  # noqa: E402
from conminucion.sizes import SizeGrid, rosin_rammler  # noqa: E402

SOL = VAZANTE_C1.solidos_pct
TABLA = tabla_de_levantamiento(VAZANTE_C1)


def csv_vazante(sep: str = ";", coma: bool = True) -> bytes:
    filas = [sep.join(c.es for c in COLUMNAS_TABLA)]
    for _, r in TABLA.iterrows():
        celdas = ["" if pd.isna(r[c.clave]) else f"{r[c.clave]:g}" for c in COLUMNAS_TABLA]
        filas.append(sep.join(x.replace(".", ",") if coma else x for x in celdas))
    return ("\r\n".join(filas) + "\r\n").encode()


# ------------------------------------------------------------------ V1
def test_v1_vazante_pegado_da_exactamente_lo_mismo_que_evaluar_ciclon():
    ref = evaluar_ciclon(VAZANTE_C1)
    r = analizar(TABLA, SOL)
    assert r.metodo == "rf_fijo"
    assert r.d50c == ref.d50c_um and r.alpha == ref.alpha  # EXACTO, no aproximado
    assert r.r == ref.theta
    assert r.rf == pytest.approx(ref.agua_a_gruesos_pct / 100.0, abs=0, rel=1e-15)
    assert np.array_equal(r.part_pct[r.usadas], ref.particion_pct[ref.superior_um <= 350.0])
    assert r.libre.as_dict() == ref.ajuste_libre.as_dict()


@pytest.mark.parametrize(("sep", "coma"), [(";", True), (",", False)])
def test_v1_vazante_como_csv_da_exactamente_lo_mismo(sep, coma):
    leida = leer_tabla("v.csv", csv_vazante(sep, coma), COLUMNAS_TABLA)
    ref, r = analizar(TABLA, SOL), analizar(leida, SOL)
    assert (r.d50c, r.alpha, r.r, r.chi2) == (ref.d50c, ref.alpha, ref.r, ref.chi2)
    assert r.carga_circulante == ref.carga_circulante


def test_vazante_reproduce_la_validacion_publicada():
    r = analizar(TABLA, SOL)
    assert 100 * (r.d50c / VAZANTE_C1.d50c_um - 1) == pytest.approx(-1.4, abs=0.1)
    assert abs(100 * (r.alpha / VAZANTE_C1.alpha - 1)) < 0.5  # docs: alpha 0,0 %


def test_madneuli_no_cabe_en_este_formato():
    """Madneuli solo publica el % bajo 74 µm de cada corriente (2 clases, sin la serie de
    tamices): una tabla así se rechaza por tener menos de 4 mallas."""
    madneuli = pd.DataFrame({"tamiz": [74.0, 37.0], "alim": [63.2, 0.0], "uf": [92.5, 0.0],
                             "of": [54.5, 0.0]})  # fmt: skip
    assert clave(madneuli, None).clave == "mu.err.menos"


# ------------------------------------------------------------------ las definiciones
def test_chi2_grados_de_libertad_cierre_y_z_son_los_de_la_definicion():
    r = analizar(TABLA, SOL)
    n = len(TABLA)
    assert r.grados_libertad == n + 2
    assert r.chi2_critico == stats.chi2.ppf(0.95, n + 2)
    rc = reconcile_node(retenidos(TABLA["alim"]), retenidos(TABLA["uf"]), retenidos(TABLA["of"]))
    assert r.chi2 == rc.chi2
    chi2 = sum(float(np.sum(z**2)) for z in r.z.values())
    assert chi2 == pytest.approx(r.chi2, rel=1e-9)
    assert r.cierre_despues < 1e-12 < r.cierre_antes
    assert r.mayor_ajuste.z == max((z[np.argmax(abs(z))] for z in r.z.values()), key=abs)
    assert r.ancho_ic_d50c > 0


def test_sin_solidos_rf_se_ajusta_libre_y_lo_dice():
    r = analizar(TABLA, None)
    assert r.metodo == "rf_libre"
    ref = fit_cyclone_partition(r.part_x_um[r.usadas], r.part_pct[r.usadas] / 100.0)
    # (la partición viaja en % y vuelve a fracción: ruido de 1e-16 que el optimizador amplifica)
    assert (r.d50c, r.alpha, r.rf) == pytest.approx(tuple(ref.values), rel=1e-6)
    assert r.libre.ci_low == pytest.approx(ref.ci_low, rel=1e-5)


def test_las_clases_del_ajuste_son_las_de_la_validacion():
    r = analizar(TABLA, SOL)
    ref = evaluar_ciclon(VAZANTE_C1)
    assert int(r.usadas.sum()) == int((ref.superior_um <= 350.0).sum()) == 6


# ------------------------------------------------------------------ la validación de la entrada
def clave(t: pd.DataFrame, solidos=SOL) -> ErrorCarga:
    with pytest.raises(ErrorCarga) as e:
        analizar(t, solidos)
    return e.value


def test_rechaza_un_acumulado_que_sube():
    e = clave(TABLA.assign(uf=TABLA["uf"].where(TABLA.index != 8, 50.0)))
    assert e.clave == "mu.err.monotono" and e.campos["tamiz"] == "149"
    assert e.campos["col"].clave == "uf"


@pytest.mark.parametrize("valor", [-0.1, 100.1])
def test_rechaza_porcentajes_fuera_de_0_100(valor):
    e = clave(TABLA.assign(of=TABLA["of"].where(TABLA.index != 12, valor)))
    assert e.clave == "mu.err.rango" and e.campos["col"].clave == "of"


def test_rechaza_tamices_no_decrecientes_o_no_positivos():
    assert clave(TABLA.assign(tamiz=TABLA["tamiz"].where(TABLA.index != 5, 3000.0))).clave == (
        "mu.err.tamices"
    )
    assert clave(TABLA.assign(tamiz=TABLA["tamiz"].where(TABLA.index != 12, 0.0))).clave == (
        "mu.err.tamices"
    )


def test_rechaza_distinto_numero_de_filas():
    e = clave(TABLA.assign(uf=TABLA["uf"].where(TABLA.index != 12, np.nan)))
    assert e.clave == "mu.err.filas"
    assert (e.campos["tamiz"], e.campos["alim"], e.campos["uf"], e.campos["of"]) == (13, 13, 12, 13)


def test_rechaza_datos_de_molino_incompletos():
    assert clave(TABLA.assign(molino_alim=100.0)).clave == "mu.err.filas_molino"
    parcial = TABLA.assign(molino_alim=100.0, molino_desc=np.where(TABLA.index < 5, 100.0, np.nan))
    assert clave(parcial).clave == "mu.err.filas_molino"


def test_rechaza_menos_de_4_mallas_utiles():
    assert clave(TABLA.iloc[:3]).clave == "mu.err.menos"
    assert clave(TABLA.iloc[:0]).clave == "mu.err.menos"
    solo_gruesas = TABLA.iloc[:6]  # todas con tamiz superior > 350 µm: no hay clases que ajustar
    e = clave(solo_gruesas)
    assert e.clave == "mu.err.utiles" and e.campos["n"] < 4


@pytest.mark.parametrize("solidos", [(0.0, 84.1, 31.1), (60.5, 100.0, 31.1), (60.5, 84.1, -1.0)])
def test_rechaza_solidos_fuera_de_0_100(solidos):
    assert clave(TABLA, solidos).clave == "mu.err.solidos"


def test_ignora_filas_vacias_y_valores_no_finitos_son_filas_incompletas():
    con_vacia = pd.concat([TABLA, pd.DataFrame([{c: np.nan for c in TABLA.columns}])])
    assert analizar(con_vacia, SOL).d50c == analizar(TABLA, SOL).d50c
    e = clave(TABLA.assign(alim=TABLA["alim"].where(TABLA.index != 3, np.inf)))
    assert e.clave == "mu.err.filas"
    assert validar(TABLA).shape == (13, 6)


def test_todos_los_errores_tienen_texto_en_los_dos_idiomas():
    for lang in ("es", "en"):
        for e in (clave(TABLA.iloc[:3]), clave(TABLA, (0, 1, 2))):
            with i18n.use(lang):
                assert mensaje_error(e)


def test_los_solidos_de_un_archivo_son_el_primer_valor_de_cada_columna():
    t = TABLA.assign(solidos_alim=np.nan, solidos_uf=np.nan, solidos_of=np.nan)
    assert solidos_de_archivo(t) is None
    t.loc[0, ["solidos_alim", "solidos_uf", "solidos_of"]] = SOL
    t.loc[5, "solidos_alim"] = 1.0
    assert solidos_de_archivo(t) == SOL
    assert solidos_de_archivo(TABLA) is None


# ------------------------------------------------------------------ el molino
def _con_molino(ruido: float = 0.0) -> pd.DataFrame:
    grid = SizeGrid(TABLA["tamiz"].to_numpy())
    alim = rosin_rammler(grid, 3000.0, 1.0)
    alim = alim / alim.sum()
    desc = BallMill(KnotSelection(KNOT_SIZES, KNOT_RD), Fracture(), 1).discharge_solids(grid, alim)

    def pasante(x):
        return 100.0 * np.cumsum(x[::-1])[::-1]

    return TABLA.assign(molino_alim=pasante(alim), molino_desc=pasante(desc))


def test_el_molino_recupera_los_rd_de_los_que_salen_los_datos():
    r = analizar(_con_molino(), SOL, (KNOT_SIZES, Fracture(), 1))
    assert r.molino is not None and r.molino_error is None
    assert r.molino.values == pytest.approx(KNOT_RD, rel=1e-6)
    assert r.molino.rmse < 1e-6


def test_sin_datos_de_molino_no_hay_ajuste_y_con_pocos_datos_hay_aviso():
    assert analizar(TABLA, SOL, (KNOT_SIZES, Fracture(), 1)).molino is None
    corto = _con_molino().iloc[6:11]  # 5 mallas: faltan datos para 4 nudos
    r = analizar(corto, SOL, (KNOT_SIZES, Fracture(), 1))
    assert r.molino is None and r.molino_error == "mu.err.molino"


# ------------------------------------------------------------------ la pestaña
def run(lang: str, fuente: str | None = None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["lang"] = lang
    at.run()
    if fuente is not None:
        with i18n.use(lang):
            at.radio(key="fit_fuente").set_value(i18n.t("mu.fuente." + fuente)).run()
    return at


def test_con_el_muestreo_sintetico_la_pestana_sigue_igual_que_antes():
    at = run("es")
    assert not at.exception and len(at.metric) == 12
    assert any("sintético" in m.value for m in at.markdown)
    assert at.radio(key="fit_fuente").value == "sintetico"
    assert not any(m.label == "R (sólidos al underflow)" for m in at.metric)


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("fuente", ["tus", "vazante"])
def test_las_fuentes_reales_dan_los_numeros_de_vazante_en_los_dos_idiomas(lang, fuente):
    at = run(lang, fuente)
    assert not at.exception and not at.error and not at.warning
    ref = evaluar_ciclon(VAZANTE_C1)
    m = {x.label: x.value for x in at.metric}
    r = [v for k, v in m.items() if k.startswith("R (")][0]
    assert r == (f"{ref.theta:.4f}".replace(".", ",") if lang == "es" else f"{ref.theta:.4f}")
    if fuente == "vazante":
        txt = " ".join(c.value for c in at.caption)
        assert ("Publicado" in txt) if lang == "es" else ("Published" in txt)
    assert len(at.metric) == 18  # 12 de siempre + 6 del estado del muestreo


def test_un_error_en_la_tabla_editada_se_muestra_traducido_y_sin_traza():
    at = run("es", "tus")
    tabla = mt.KEY_TABLA
    at.session_state[tabla] = {
        "edited_rows": {8: {"uf": 50.0}},
        "added_rows": [],
        "deleted_rows": [],
    }
    at.run()
    assert not at.exception
    assert any("no es un acumulado" in w.value and "149" in w.value for w in at.warning)
    at.session_state[tabla] = {
        "edited_rows": {3: {"alim": 120.0}},
        "added_rows": [],
        "deleted_rows": [],
    }
    at.run()
    assert any("fuera de 0–100 %" in w.value for w in at.warning)


def test_editar_el_underflow_en_la_tabla_cambia_el_chi2():
    at = run("es", "tus")
    base = next(m.value for m in at.metric if m.label == "χ² ponderado")
    tabla = mt.KEY_TABLA
    at.session_state[tabla] = {
        "edited_rows": {8: {"uf": 30.4}},
        "added_rows": [],
        "deleted_rows": [],
    }
    at.run()
    despues = next(m.value for m in at.metric if m.label == "χ² ponderado")
    assert base == "0,04" and despues == "27,28"
    assert any("supera el crítico" in m.value for m in at.markdown)


def test_la_pestana_no_ofrece_que_mejorar_porque_la_prueba_con_error_plantado_fallo():
    at = run("es", "tus")
    textos = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "Qué mejorar" not in textos and "What to improve" not in textos
    assert "no qué corriente está mal" in textos


def test_con_datos_de_molino_en_la_tabla_la_pestana_muestra_los_rd_por_nudos():
    at = run("es", "tus")
    datos = _con_molino()
    editadas = {
        i: {"molino_alim": float(r.molino_alim), "molino_desc": float(r.molino_desc)}
        for i, r in datos.iterrows()
    }
    at.session_state[mt.KEY_TABLA] = {
        "edited_rows": editadas, "added_rows": [], "deleted_rows": []
    }  # fmt: skip
    at.run()
    assert not at.exception and not at.error
    assert any(h.value == "Molino: r/d por nudos" for h in at.subheader)
    assert any("nudos (4750, 1187, 297, 74 µm)" in c.value for c in at.caption)
    rd = next(d.value for d in at.dataframe if "r/d estimado" in d.value.columns)
    assert rd["r/d estimado"].tolist() == pytest.approx(list(KNOT_RD), abs=1e-4)
