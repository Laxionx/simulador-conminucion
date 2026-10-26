"""La pestaña «Chancado primario» y el patrón «estado + prueba esto» de la pestaña Simulación:
humo en los dos idiomas, equipos de la Tabla 3.1, cada afirmación de «Prueba esto», valores
manipulados y un fuzz de 30 combinaciones por idioma (30 % extremas, con el tiempo por corrida)."""

import json
import math
import random
import re
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
sys.path.insert(0, str(ROOT / "app"))

import estado  # noqa: E402
import i18n  # noqa: E402
import mandibula_datos as md  # noqa: E402
import mandibula_graficos as mg  # noqa: E402
import mandibula_tab as mt  # noqa: E402
from equipos import es  # noqa: E402

from conminucion.datos_mandibula import K_CAL, TABLA_KING  # noqa: E402

SEED, N_FUZZ, EXTREME_SHARE = 20261026, 30, 0.30
CHECKS = {
    "no_muerde", "velocidad_critica", "rpm_fuera_de_rango", "carrera_fuera_de_rango", "colpas",
    "razon_reduccion", "sobrecarga", "potencia",
}  # fmt: skip


def run(lang: str = "es") -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["lang"] = lang
    return at.run()


def field(at: AppTest, key: str):
    return next(w for w in at.number_input if w.key == md.PREFIX + key)


def lines(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown]


def vals(**cambios) -> dict:
    return {**md.valores_por_defecto(), **cambios}


# ------------------------------------------------------------------ datos y cálculo
def test_el_estado_de_ejemplo_esta_en_rango_y_es_el_de_la_tabla_de_king():
    c = md.ejemplo()
    assert {ch.codigo for ch in c.checks} == CHECKS
    assert all(ch.nivel == "ok" for ch in c.checks)
    maq, oss, q = md.punto_king(c)
    assert (maq.nombre, oss, q) == ("24x36", 51, 70)
    assert c.jaw.oss_mm == pytest.approx(51.0, abs=1e-6) and c.jaw.k == pytest.approx(K_CAL)
    assert c.jaw.product_model == "nordberg"


def test_los_controles_se_definen_una_vez_y_el_ejemplo_esta_dentro_de_su_rango():
    assert len({c.key for c in md.CAMPOS}) == len(md.CAMPOS)
    for c in md.CAMPOS:
        assert c.lo <= c.default < c.hi and c.step > 0, c.key
        assert c.source in {"king_tn5", "amit135", "karra_king", "definicion", "supuesto"}
    assert md.validar(md.valores_por_defecto()) is None
    assert {r for r in mt.datos_table().columns} == {
        i18n.TEXTS["es"][k] for k in ("jaw.col.campo", "jaw.col.unit", "jaw.col.range",
                                      "jaw.col.example", "jaw.col.what", "jaw.col.how")
    }  # fmt: skip
    with i18n.use("es"):
        assert len(mt.datos_table()) == len(md.CAMPOS) + 2  # + modelo del producto y parrilla


@pytest.mark.parametrize("maq", TABLA_KING, ids=lambda m: m.nombre)
def test_cada_equipo_de_la_tabla_con_cada_oss_es_un_caso_valido_y_coincide_con_la_tabla(maq):
    for oss in maq.capacidad_tph:
        v = vals(**md.valores_de_equipo(maq, oss))
        assert md.validar(v) is None, (maq.nombre, oss, md.validar(v))
        c = md.calcular(v)
        assert c.jaw.oss_mm == pytest.approx(oss, abs=0.01)
        assert (c.jaw.gape_mm, c.jaw.width_mm, c.jaw.rpm, c.jaw.power_kw) == pytest.approx(
            (round(maq.boca_mm, 1), round(maq.largo_mm, 1), maq.rpm, maq.kw)
        )
        assert c.jaw.height == pytest.approx(2.0 * c.jaw.gape_mm)
        assert md.punto_king(c)[1:] == (oss, maq.capacidad_tph[oss])
        assert c.cierre() < 1e-12


@pytest.mark.parametrize(
    ("cambio", "problema"),
    [
        ({"gape": float("nan")}, "jaw.err.numero"),
        ({"css": float("inf")}, "jaw.err.numero"),
        ({"rpm": True}, "jaw.err.numero"),
        ({"tph": "100"}, "jaw.err.numero"),
        ({"model": "otro"}, "jaw.err.numero"),
        ({"grizzly": 1}, "jaw.err.numero"),
        ({"wear": -1.0}, "jaw.err.rango"),
        ({"gape": 1e9}, "jaw.err.rango"),
        ({"css": 600.0}, "jaw.err.boca"),
        ({"wear": 60.0, "css": 540.0}, "jaw.err.boca"),
        ({"f80": 500.0}, "jaw.err.f80"),
        ({"n": 5.0, "f80": 450.0}, "jaw.err.rr"),
    ],
)
def test_los_datos_invalidos_se_rechazan_con_su_mensaje(cambio, problema):
    assert md.validar(vals(**cambio)) == problema


def test_la_alimentacion_de_mina_tiene_el_f80_y_el_tamano_maximo_pedidos():
    for n in (0.4, 1.2, 3.0):
        for f80 in (100.0, 274.0, 400.0):
            v = vals(n=n, f80=f80)
            if md.validar(v) is not None:
                continue
            s = md.alimentacion(v)
            assert s.total_solids == pytest.approx(v["tph"])
            assert s.grid.sieves[0] == pytest.approx(v["top"] * md.MM)
            assert s.p80 / md.MM == pytest.approx(f80, rel=0.06)


def test_la_densidad_escala_k_y_el_balance_de_masa_cierra():
    a, b = md.calcular(vals(rho=2.7)), md.calcular(vals(rho=3.6))
    assert b.jaw.k == pytest.approx(a.jaw.k * 3.6 / 2.7)
    for c in (a, b, md.calcular(vals(grizzly=False)), md.calcular(vals(model="whiten"))):
        assert c.cierre() < 1e-12
        if c.pasante is not None:
            assert c.pasante.total_solids + c.carga.total_solids == pytest.approx(
                c.mina.total_solids
            )
        assert c.producto.total_solids == pytest.approx(c.mina.total_solids)
    assert md.calcular(vals(grizzly=False)).carga is not None


def test_el_calculo_de_la_pestana_cuesta_menos_de_0_3_s_por_corrida():
    md.calcular(md.valores_por_defecto())  # calienta
    t0 = time.perf_counter()
    n = 20
    for _ in range(n):
        c = md.calcular(md.valores_por_defecto())
        mg.granulometria_fig(c), mg.capacidad_fig(c, "rpm"), mg.capacidad_fig(c, "css")
        mt.balance_table(c)
    presupuesto = 0.3 if sys.gettrace() is None else 1.5  # con cobertura todo corre más lento
    assert (time.perf_counter() - t0) / n < presupuesto


@pytest.mark.parametrize("eje", mg.EJES)
def test_las_curvas_usan_los_datos_del_calculo_y_la_tabla_de_king(eje):
    c = md.ejemplo()
    with i18n.use("es"):
        fig = mg.capacidad_fig(c, eje)
        gran = mg.granulometria_fig(c)
    names = [tr.name for tr in fig.data]
    assert "Modelo (cinemática)" in names and "Punto de operación" in names
    punto = next(tr for tr in fig.data if tr.name == "Punto de operación")
    assert punto.y[0] == pytest.approx(c.jaw.capacity_tph())
    assert ("Tabla de King" in names) == (eje == "css") and ("Taggart" in names) == (eje == "css")
    if eje == "css":
        king = next(tr for tr in fig.data if tr.name == "Tabla de King")
        assert list(king.y) == [q for _, q in sorted(TABLA_KING[4].capacidad_tph.items())]
        assert list(king.x) == pytest.approx([o - c.jaw.stroke for o in (51, 63, 76, 102)])
    assert {s.name for s in gran.data if s.mode != "lines+text"} == {
        "Alimentación de mina", "Pasante de la parrilla", "Alimentación al chancador",
        "Producto del chancador", "Producto total",
    }  # fmt: skip
    assert not gran.layout.shapes  # el CSS y el OSS son dos trazos, no formas en log10
    assert {tr.name for tr in gran.data if tr.mode == "lines+text"} == {"CSS", "OSS"}
    with pytest.raises(ValueError, match="Eje"):
        mg.capacidad_fig(c, "otro")


def test_sin_equipo_de_la_tabla_no_hay_puntos_de_king_en_la_curva():
    c = md.calcular(vals(gape=700.0))
    assert md.punto_king(c) is None
    with i18n.use("es"):
        assert "Tabla de King" not in [tr.name for tr in mg.capacidad_fig(c, "css").data]


# ------------------------------------------------------------------ «Prueba esto» de la pestaña
def _magnitudes(c: md.Calculo) -> dict[str, float]:
    return {
        "capacidad": c.capacidad, "p80": c.p80, "utilizacion": c.utilizacion,
        "alimentacion": c.carga.total_solids,
        "colpas": next(ch.valores["fraccion"] for ch in c.checks if ch.codigo == "colpas"),
    }  # fmt: skip


@pytest.mark.parametrize("exp", md.EXPERIMENTOS, ids=lambda e: e.clave)
def test_cada_experimento_hace_lo_que_dice_su_texto(exp):
    antes = md.ejemplo()
    despues = md.con_cambios(md.valores_por_defecto(), **exp.cambios)
    a, b = _magnitudes(antes), _magnitudes(despues)
    for nombre, signo in exp.direcciones.items():
        assert (b[nombre] - a[nombre]) * signo > 0, (exp.clave, nombre, a[nombre], b[nombre])
    assert {ch.codigo: ch.nivel for ch in antes.checks} == dict.fromkeys(CHECKS, "ok")
    nuevos = {ch.codigo: ch.nivel for ch in despues.checks}
    for codigo, nivel in exp.niveles.items():
        assert nuevos[codigo] == nivel, (exp.clave, codigo)
    # y no cambia lo que el texto no dice: los demás chequeos siguen en rango
    assert {k for k, v in nuevos.items() if v != "ok"} == set(exp.niveles)


def test_las_afirmaciones_con_numeros_de_los_textos_son_ciertas():
    pares = {e.clave: (a, b) for e, a, b in mt.pares_de_experimentos()}
    a, b = pares["css"]
    assert a.jaw.css_eff_mm > b.jaw.css_eff_mm == 10.0 and b.utilizacion > 1.0
    a, b = pares["rpm"]
    assert a.jaw.rpm < a.jaw.critical_rpm < b.jaw.rpm  # «trabaja bajo Nc» y luego sobre Nc
    a, b = pares["parrilla"]
    assert b.capacidad == pytest.approx(a.capacidad, rel=1e-9) and b.pasante is None
    a, b = pares["desgaste"]
    assert b.jaw.oss_mm > a.jaw.oss_mm and b.carga.f80 / b.prod_chancador.p80 < 4.0
    assert b.jaw.critical_rpm < b.jaw.rpm  # Nc baja bajo las rpm
    a, b = pares["colpas"]
    assert _magnitudes(a)["colpas"] == 0.0 < _magnitudes(b)["colpas"]
    assert b.capacidad == pytest.approx(a.capacidad, rel=1e-9)
    assert float(a.v["top"]) < 0.8 * a.jaw.gape_mm < float(b.v["top"])
    a, b = pares["motor"]
    assert b.potencia > b.jaw.power_kw > a.potencia and b.jaw.power_kw < a.jaw.power_kw


@pytest.mark.parametrize("lang", ["es", "en"])
def test_los_textos_de_prueba_esto_llevan_los_numeros_del_modelo_en_vivo(lang):
    with i18n.use(lang):
        items = mt.pruebas_de_ejemplo()
        assert [p.clave for p in items] == [e.clave for e in md.EXPERIMENTOS]
        for p, (e, a, _b) in zip(items, mt.pares_de_experimentos(), strict=True):
            assert "{" not in p.texto and p.titulo and p.cambios
            assert set(p.cambios) == {md.PREFIX + k for k in e.cambios}
            assert es(a.capacidad, 0) in p.texto  # la capacidad de antes está en todos los textos
        css = items[0].texto
        pares = mt.pares_de_experimentos()[0]
        assert es(pares[1].capacidad, 0) in css and es(100 * pares[2].utilizacion, 0) in css


@pytest.mark.parametrize("exp", md.EXPERIMENTOS, ids=lambda e: e.clave)
def test_el_boton_de_prueba_esto_pone_el_cambio_y_el_panel_dice_lo_que_dice_el_texto(exp):
    at = run()
    next(b for b in at.button if b.key == f"jaw_prueba_{exp.clave}").click().run()
    assert not at.exception and not at.error
    c = md.con_cambios(md.valores_por_defecto(), **exp.cambios)
    shown = lines(at)
    for ch in c.checks:
        if ch.codigo in exp.niveles:  # cada línea con su nivel escrito y en color
            assert estado.linea(mt._fila(ch)) in shown, (exp.clave, ch.codigo)
    colores = {n: estado.COLORES[n] for n in exp.niveles.values()}
    assert all(f":{col}-badge[" in " ".join(shown) for col in colores.values())
    assert any(estado.linea(mt._fila(ch)) in shown for ch in c.checks if ch.nivel != "ok")
    assert "Operación dentro de rango." in " ".join(shown)  # el de la pestaña de simulación
    # el restablecer vuelve al ejemplo
    next(b for b in at.button if b.key == "jaw_prueba_reset").click().run()
    assert field(at, "css").value == md.EJEMPLO["css"] and not at.exception
    assert sum(m.startswith(":green-badge[En rango] Operación") for m in lines(at)) == 2


# ------------------------------------------------------------------ la pestaña en la app
@pytest.mark.parametrize(
    ("lang", "tab", "ok", "king"),
    [
        ("es", "Chancado primario", "Operación dentro de rango.", "Tabla de King (24x36 pulgadas"),
        ("en", "Primary crushing", "Operation within range.", "King's table (24x36 inches"),
    ],
)
def test_humo_de_la_pestana_en_cada_idioma(lang, tab, ok, king):
    at = run(lang)
    assert not at.exception and not at.error
    assert len(at.tabs) == 5 and at.tabs[4].label == tab
    assert len(at.metric) == 12  # 6 de simulación y 6 de chancado
    jaw = at.metric[6:]
    assert [m.label for m in jaw][:3] == (
        ["Capacidad (t/h)", "Utilización", "P80 producto (mm)"]
        if lang == "es"
        else ["Capacity (t/h)", "Utilization", "Product P80 (mm)"]
    )
    c = md.ejemplo()
    with i18n.use(lang):
        assert jaw[0].value == es(c.capacidad, 1) and jaw[2].value == es(c.p80, 1)
        assert jaw[3].value == f"{es(c.potencia, 1)} / {es(56, 0)}"
        assert jaw[4].value == es(c.jaw.rpm / c.jaw.critical_rpm, 2)
    assert sum(ok in m for m in lines(at)) == 2  # el panel de chancado y el de simulación
    assert any(king in c_.value for c_ in at.caption)
    assert not any("de la masa" in c_.value or "of the mass" in c_.value for c_ in at.caption)
    assert len(at.get("plotly_chart")) >= 2 + 1 + 3  # curvas del chancado y gráficos de simulación
    assert len(at.latex) == 12 and any(w.key == "jaw_prueba_css" for w in at.button)
    html = " ".join(h.value for h in at.get("html"))
    alts = (
        ("Corte lateral", "Abertura de descarga") if lang == "es" else ("Side section", "Discharge")
    )
    assert all(alt in html for alt in alts)  # el esquema y el mini gráfico, como imagen
    assert at.dataframe  # el balance de masa


def test_el_balance_y_la_descarga_salen_del_calculo():
    at = run()
    c = md.ejemplo()
    bal = next(d.value for d in at.dataframe if "Sólidos (t/h)" in d.value.columns)
    assert len(bal) == 5
    assert bal["Sólidos (t/h)"].tolist()[0] == pytest.approx(c.mina.total_solids, abs=0.01)
    assert bal["Sólidos (t/h)"].tolist()[-1] == pytest.approx(c.producto.total_solids, abs=0.01)
    assert any("error relativo de sólidos" in x.value for x in at.caption)


def test_cambiar_de_equipo_fija_los_valores_de_la_tabla():
    at = run()
    sel = next(w for w in at.selectbox if w.key == "jaw_equipo")
    sel.set_value("42x48").run()
    assert not at.exception and not at.error
    maq = next(m for m in TABLA_KING if m.nombre == "42x48")
    oss = sorted(maq.capacidad_tph)[len(maq.capacidad_tph) // 2]
    esperado = md.valores_de_equipo(maq, oss)
    for k, v in esperado.items():
        assert field(at, k).value == pytest.approx(v), k
    assert (field(at, "gape").value, field(at, "width").value) == (1066.8, 1219.2)
    assert (field(at, "rpm").value, field(at, "power").value) == (180.0, 110.0)
    oss_sel = next(w for w in at.selectbox if w.key == "jaw_oss_42x48")
    assert oss_sel.value == oss
    assert any(f"42x48 pulgadas, OSS {oss} mm" in c.value for c in at.caption)
    oss_sel.set_value(sorted(maq.capacidad_tph)[0]).run()  # otro punto de la tabla
    oss0 = sorted(maq.capacidad_tph)[0]
    assert field(at, "css").value == pytest.approx(oss0 - field(at, "stroke").value, abs=0.01)
    assert any(f"OSS {oss0} mm" in c.value for c in at.caption)
    # con otro CSS ya no coincide con ningún punto de la tabla: la línea desaparece
    field(at, "css").set_value(80.0).run()
    assert not any("pulgadas, OSS" in c.value for c in at.caption) and not at.exception


def test_personalizado_no_cambia_los_valores():
    at = run()
    sel = next(w for w in at.selectbox if w.key == "jaw_equipo")
    sel.set_value("personalizado").run()
    assert not at.exception and field(at, "gape").value == md.EJEMPLO["gape"]
    assert not any(w.key.startswith("jaw_oss_") for w in at.selectbox)


def test_apagar_la_parrilla_o_el_movimiento_o_cambiar_el_modelo_no_rompe_la_pestana():
    at = run()
    next(w for w in at.toggle if w.key == "jaw_grizzly").set_value(False).run()
    assert not at.exception and not at.error
    at.toggle[0].set_value(False).run()
    next(w for w in at.selectbox if w.key == "jaw_model").set_value("whiten").run()
    assert not at.exception and not at.error
    next(w for w in at.radio if w.key == "jaw_vista").set_value("detalle").run()
    next(w for w in at.radio if w.key == "jaw_eje").set_value("css").run()
    assert not at.exception and not at.error


@pytest.mark.parametrize(
    ("cambio", "texto"),
    [
        ({"css": 600.0}, "La boca debe ser mayor que el OSS"),
        ({"f80": 450.0, "top": 400.0}, "El F80 debe ser menor"),
        ({"n": 5.0, "f80": 450.0, "top": 457.0}, "demasiado cerca"),
    ],
)
def test_los_datos_incoherentes_avisan_sin_traza(cambio, texto):
    at = run()
    for k, v in cambio.items():
        field(at, k).set_value(v)
    at.run()
    assert not at.exception
    assert any(texto in e.value for e in at.error), [e.value for e in at.error]
    assert not re.search(r"Traceback|nan|inf ", json.dumps([e.value for e in at.error]))


@pytest.mark.parametrize("key", ["gape", "css", "n"])  # una muestra de los 17 controles
@pytest.mark.parametrize("value", [1e12, -5.0, float("nan"), float("inf")])
def test_el_servidor_devuelve_al_valor_de_ejemplo_lo_que_manda_un_cliente_manipulado(key, value):
    at = run()
    field(at, key).set_value(value).run()
    assert not at.exception and not at.error
    assert field(at, key).value == md.EJEMPLO[key]


def test_la_pestana_en_ingles_no_deja_textos_en_espanol_ni_cambia_las_cifras():
    es_, en = run("es"), run("en")
    a, b = (_numeros_de_la_pestana(x, lg) for x, lg in ((es_, "es"), (en, "en")))
    assert len(a) == len(b) > 40 and a == b


_NUMBER = {
    "es": re.compile(r"-?\d+(?: \d{3})*(?:[.,]\d+)?(?:e-?\d+)?"),
    "en": re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:e-?\d+)?"),
}


def _numeros(text: str, lang: str) -> list[float]:
    out = []
    for item in _NUMBER[lang].findall(text.replace("\xa0", " ")):
        item = item.replace(",", "") if lang == "en" else item.replace(" ", "").replace(",", ".")
        out.append(float(item))
    return out


def _numeros_de_la_pestana(at: AppTest, lang: str) -> list[list[float]]:
    """Las cifras de textos, métricas y tablas de las pestañas Simulación y Chancado primario."""
    out = []
    for tab in (at.tabs[1], at.tabs[4]):
        textos = [m.value for m in tab.markdown] + [c.value for c in tab.caption]
        textos += [str(m.value) for m in tab.metric]
        out += [_numeros(x, lang) for x in textos]
        for df in tab.dataframe:
            celdas = [x for row in df.value.values.tolist() for x in row]
            out.append([x for x in celdas if isinstance(x, int | float) and not math.isnan(x)])
    return out


# ------------------------------------------------------------------ fuzz de los controles nuevos
def _fuzz_cases(rng: random.Random):
    keys = [c.key for c in md.CAMPOS]
    for _ in range(N_FUZZ):
        elegidos = rng.sample(keys, rng.randint(3, 8))
        valores = {}
        for k in elegidos:
            c = md.BY_KEY[k]
            if rng.random() < EXTREME_SHARE:
                valores[k] = rng.choice([c.lo, c.hi])
            else:
                valores[k] = round(rng.uniform(c.lo, c.hi), 2)
        yield (
            valores, rng.random() < 0.5, rng.choice(md.MODELOS),
            rng.choice(["completo", "detalle"]),
            rng.choice(["rpm", "css"]), rng.choice([1.0, 4.5, 8.0]), rng.choice([5, 40, 100]),
            rng.random() < 0.5,
        )  # fmt: skip


@pytest.mark.parametrize("lang", ["es", "en"])
def test_fuzz_de_30_combinaciones_no_tira_excepciones(lang):
    at = run(lang)
    tiempos = []
    for valores, parrilla, modelo, vista, eje, amp, vel, mover in _fuzz_cases(random.Random(SEED)):
        for k, v in valores.items():
            field(at, k).set_value(v)
        next(w for w in at.toggle if w.key == "jaw_grizzly").set_value(parrilla)
        next(w for w in at.selectbox if w.key == "jaw_model").set_value(modelo)
        next(w for w in at.radio if w.key == "jaw_vista").set_value(vista)
        next(w for w in at.radio if w.key == "jaw_eje").set_value(eje)
        next(w for w in at.slider if w.key == "jaw_amp").set_value(amp)
        next(w for w in at.slider if w.key == "jaw_vel").set_value(vel)
        at.toggle[0].set_value(mover)
        t0 = time.perf_counter()
        at.run()
        tiempos.append(time.perf_counter() - t0)
        assert not at.exception, (valores, parrilla, modelo)
        blob = json.dumps([m.value for m in at.markdown] + [e.value for e in at.error])
        assert not re.search(r"Traceback|nan %|inf t/h|nan kW", blob), valores
        if at.error:  # un caso incoherente se avisa con un texto de diccionario, sin traza
            keys = {i18n.TEXTS[lang][k] for k in ("jaw.err.boca", "jaw.err.f80", "jaw.err.rr")}
            assert all(e.value in keys or "rechazó" in e.value or "rejected" in e.value
                       for e in at.error), [e.value for e in at.error]  # fmt: skip
    print(f"fuzz {lang}: {sum(tiempos) / len(tiempos):.2f} s por corrida de la app completa")


@pytest.mark.parametrize("cambios", [{}, {"css": 8.0}, {"wear": 20.0}, {"gape": 1066.8}])
def test_el_grafico_de_granulometria_tiene_el_eje_y_las_lineas_dentro_del_rango_de_los_datos(
    cambios,
):
    """Regresión: en un eje log de Plotly las líneas de `add_vline` van en log10(x), y el CSS = 18
    caía en 10^18. Nada puede salir del rango de tamaños de los datos."""
    import numpy as np

    c = md.calcular(vals(**cambios))
    with i18n.use("es"):
        fig = mg.granulometria_fig(c)
    lo, hi = c.mina.grid.sieves.min() / md.MM, c.mina.grid.sieves.max() / md.MM
    for tr in fig.data:
        xs = np.asarray(tr.x, dtype=float)
        assert lo <= xs.min() and xs.max() <= hi, tr.name
    assert not fig.layout.shapes and not fig.layout.annotations  # nada en coordenadas de log10
    rango = fig.layout.xaxis.range
    assert 10 ** rango[0] == pytest.approx(lo, rel=1e-6) and hi <= 10 ** rango[1] <= 1.2 * hi
    lineas = {tr.name: tr.x[0] for tr in fig.data if tr.mode == "lines+text"}
    assert lineas == {"CSS": c.jaw.css_eff_mm, "OSS": c.jaw.oss_mm}
    assert lo < c.jaw.css_eff_mm < c.jaw.oss_mm < hi


def test_los_seis_indicadores_van_en_dos_filas_de_tres_con_rotulos_cortos():
    at = run()
    jaw = at.metric[6:]
    assert len(jaw) == 6 and all(len(m.label) <= 24 for m in jaw)
    assert all(m.help for m in jaw)  # el nombre completo va en la ayuda
    assert len(at.tabs[4].columns) >= 6  # dos filas de 3 columnas
