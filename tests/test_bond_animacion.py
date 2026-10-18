"""«Ensayo de Bond» en la app (sin levantar Streamlit): la animación sale del cálculo, los controles
se definen una sola vez y la validación del servidor rechaza valores manipulados."""

import base64
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

import bond_datos as bd  # noqa: E402
import bond_tab  # noqa: E402
import i18n  # noqa: E402
from bond_grafico import bond_figure, series  # noqa: E402
from equipos import rotation_period_s  # noqa: E402

from conminucion.ensayo_bond import MOLINO_DIAMETRO_M, MOLINO_RPM  # noqa: E402
from conminucion.power import critical_speed_rpm  # noqa: E402


@pytest.fixture(scope="module")
def caso():
    return bd.caso_hebei()


def _svgs(html: str) -> list[str]:
    return [
        base64.b64decode(b).decode("utf-8")
        for b in re.findall(r'src="data:image/svg\+xml;base64,([^"]+)"', html)
    ]


# ------------------------------------------------------------------ el molino
def test_el_molino_gira_a_las_rpm_reales_del_ensayo(caso):
    # 70 rpm es una fracción de la velocidad crítica del molino de 305 mm con bolas de 36,8 mm
    frac = bd.velocidad_critica_frac(caso.rpm_critica)
    assert caso.rpm_critica == pytest.approx(critical_speed_rpm(0.305, bd.BOLA_MAX_MM))
    assert frac * caso.rpm_critica == pytest.approx(MOLINO_RPM)
    assert 0.8 < frac < 0.95
    animado, quieto = _svgs(bond_tab.mill_image(caso, True))
    assert "animation-duration:0.857s" in animado  # 60 / 70 s por vuelta
    assert "animation-duration" not in quieto.split("</style>")[1]
    period = rotation_period_s(MOLINO_DIAMETRO_M, frac, bd.BOLA_MAX_MM)
    assert period == pytest.approx(60.0 / 70.0)
    assert "70,0 rpm" in animado and "una vuelta cada 0,86 s" in animado


def test_el_llenado_del_molino_sale_de_las_bolas_declaradas(caso):
    from conminucion.power import ball_charge_t

    j = caso.llenado
    assert 0.15 < j < 0.25
    assert ball_charge_t(0.305, 0.305, j) == pytest.approx(20.125 / 1000.0)
    animado = _svgs(bond_tab.mill_image(caso, True))[0]
    assert f"{round(100 * j)} %" in animado
    assert "285 bolas, 20,125 kg" in animado
    assert "kW" not in animado  # la potencia de Bond-Rowland no vale a esta escala


def test_con_el_interruptor_apagado_solo_hay_una_version_quieta(caso):
    html = bond_tab.mill_image(caso, False)
    assert len(_svgs(html)) == 1 and "animation-duration" not in _svgs(html)[0].split("</style>")[1]


def test_los_esquemas_son_xml_valido_en_los_dos_idiomas(caso):
    for lang in ("es", "en"):
        with i18n.use(lang):
            for svg in _svgs(bond_tab.mill_image(caso, True)):
                ET.fromstring(svg)


def test_el_molino_no_cambio_para_los_otros_usos():
    from equipos import mill_svg

    base = mill_svg(4.0, 6.0, 0.38, 0.75, 75.0, 2500.0, 120.0)
    assert "Potencia en el piñón: 2 500 kW" in base and "Carga de bolas: 120 t" in base
    assert "Ø 4,0 m × 6,0 m" in base


# ------------------------------------------------------------------ el gráfico
def test_cada_cuadro_del_grafico_es_el_gbp_calculado_de_ese_ciclo(caso):
    fig = bond_figure(caso.medido, caso.simulado)
    s = series(caso.medido, caso.simulado)
    n = len(caso.medido.ciclos)
    assert len(fig.frames) == n == 11
    for k, frame in enumerate(fig.frames, start=1):
        assert frame.name == str(k)
        gm, gs, cm, cs = (np.asarray(tr.y) for tr in frame.data)
        assert len(gm) == k
        np.testing.assert_allclose(gm, s["gbp_med"][:k])
        np.testing.assert_allclose(gs, s["gbp_sim"][:k])
        np.testing.assert_allclose(cm, s["cl_med"][:k])
        np.testing.assert_allclose(cs, s["cl_sim"][:k])
    final = [np.asarray(tr.y) for tr in fig.data]
    np.testing.assert_allclose(final[0], [c.gbp for c in caso.medido.ciclos])
    np.testing.assert_allclose(final[1], [c.gbp for c in caso.simulado.ciclos])


def test_el_contador_del_grafico_dice_el_ciclo_de_cada_cuadro(caso):
    fig = bond_figure(caso.medido, caso.simulado)
    for k, frame in enumerate(fig.frames, start=1):
        textos = " ".join(a["text"] for a in frame.layout.annotations)
        assert f"Ciclo {k} de 11" in textos
    assert "Reproducir" in str(fig.layout.updatemenus)  # nada arranca solo


def test_el_grafico_en_ingles_no_lleva_espanol(caso):
    with i18n.use("en"):
        fig = bond_figure(caso.medido, caso.simulado)
    blob = str(fig.to_plotly_json())
    assert "Cycle 3 of 11" in blob and "Play" in blob and "Ciclo" not in blob


# ------------------------------------------------------------------ una sola definición
def test_los_campos_de_la_calculadora_se_definen_una_vez():
    assert len({c.key for c in bd.CAMPOS}) == len(bd.CAMPOS)
    tabla = bond_tab.datos_table()
    assert len(tabla) == len(bd.CAMPOS)
    for c, (_, row) in zip(bd.CAMPOS, tabla.iterrows(), strict=True):
        assert c.lo <= c.default <= c.hi
        assert row.iloc[0] == i18n.TEXTS["es"][c.label_k]
        assert i18n.TEXTS["es"][c.meaning_k] in row.iloc[4]
    assert bd.valores_por_defecto() == {c.key: c.default for c in bd.CAMPOS}


def test_el_caso_de_hebei_precargado_da_el_wi_publicado(caso):
    assert caso.medido.wi == pytest.approx(bd.HEBEI_WI, abs=0.05)
    assert bd.validar(bd.valores_por_defecto(), list(bd.HEBEI_FINOS)) is None


# ------------------------------------------------------------------ valores manipulados
OK = bd.valores_por_defecto()


@pytest.mark.parametrize("campo", [c.key for c in bd.CAMPOS])
@pytest.mark.parametrize("malo", [float("nan"), float("inf"), -float("inf"), "x", None, True, 1e12])
def test_el_servidor_rechaza_valores_manipulados_de_los_campos(campo, malo):
    assert bd.validar({**OK, campo: malo}, list(bd.HEBEI_FINOS)) is not None


@pytest.mark.parametrize(
    "finos",
    [
        [],
        [None],
        [float("nan")] * 3,
        [100.0, float("inf")],
        [100.0, -1.0],
        [100.0, 1e9],
        ["12"],
        [True],
        [100.0] * (bd.MAX_CICLOS + 1),
    ],
)
def test_el_servidor_rechaza_tablas_manipuladas(finos):
    assert bd.validar(OK, finos) is not None


def test_relaciones_entre_datos():
    assert bd.validar({**OK, "finos_carga": OK["carga"]}, [100.0]) == "bond.err.carga"
    assert bd.validar({**OK, "p80": 160.0}, [100.0]) == "bond.err.tamaños"  # P80 > tamiz
    assert bd.validar({**OK, "f80": 100.0}, [100.0]) == "bond.err.tamaños"  # F80 < tamiz
    assert bd.validar(OK, [OK["carga"] + 1]) == "bond.err.finos"
    assert bd.calcular(OK, [100.0, 100.0]) is None  # un ciclo sin finos nuevos
    assert bd.calcular(OK, list(bd.HEBEI_FINOS)).wi == pytest.approx(10.92, abs=0.01)


def test_todo_texto_de_error_existe_en_los_dos_idiomas():
    for key in ("numero", "rango", "filas", "vacio", "finos", "carga", "tamaños", "calculo"):
        assert f"bond.err.{key}" in i18n.TEXTS["es"] and f"bond.err.{key}" in i18n.TEXTS["en"]


def test_cualquier_numero_valido_da_un_resultado_finito_o_un_aviso():
    rng = np.random.default_rng(7)
    for _ in range(200):
        v = {c.key: float(rng.uniform(c.lo, c.hi)) for c in bd.CAMPOS}
        v["rev1"] = float(int(v["rev1"]))
        finos = [
            float(x) for x in rng.uniform(0, min(v["carga"], bd.FINOS_MAX), rng.integers(1, 31))
        ]
        if bd.validar(v, finos) is None:
            res = bd.calcular(v, finos)
            assert res is None or all(math.isfinite(c.gbp) for c in res.ciclos)


def test_un_numero_de_revoluciones_con_decimales_se_rechaza():
    assert bd.validar({**OK, "rev1": 100.5}, list(bd.HEBEI_FINOS)) == "bond.err.rango"
    assert bd.validar({**OK, "rev1": 100.0}, list(bd.HEBEI_FINOS)) is None


def test_las_constantes_del_molino_son_las_de_la_guia_de_gmg():
    # GMG (2021): molino de 305 x 305 mm a 70 rpm; 285 bolas de 20,125 kg, la mayor de 36,8 mm
    assert (MOLINO_DIAMETRO_M, bd.MOLINO_LARGO_M, MOLINO_RPM) == (0.305, 0.305, 70.0)
    assert (bd.BOLAS_N, bd.BOLAS_KG, bd.BOLA_MAX_MM) == (285, 20.125, 36.8)
    assert bd.CORTE_PCT == 10.0
