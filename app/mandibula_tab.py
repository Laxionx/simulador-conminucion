"""Pestaña «Chancado primario»: parrilla + chancador de mandíbula con indicadores, estado de la
operación, esquema animado, equipos predefinidos de la Tabla 3.1 de King, curvas, balance de masa,
«Prueba esto» y la guía de la pestaña. Los controles se definen una vez en `mandibula_datos.CAMPOS`;
de ahí salen los campos y la tabla de datos de la guía. Nada de lo que escribe el visitante entra
al SVG ni al HTML: solo números del cálculo y textos de diccionarios fijos."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
import streamlit as st
from equipos import as_images, es
from estado import Fila, Prueba, cientifico, panel, pruebas
from guia import markdown_table
from i18n import int_num, num_g, t, tr_error
from mandibula_datos import (
    CAMPOS,
    EJEMPLO_EQUIPO,
    EXPERIMENTOS,
    G_ALIM,
    G_MAQ,
    G_PARR,
    MM,
    MODELOS,
    PERSONALIZADO,
    POR_NOMBRE,
    PREFIX,
    Calculo,
    calcular,
    con_cambios,
    ejemplo,
    punto_king,
    validar,
    valores_de_equipo,
    valores_por_defecto,
)
from mandibula_graficos import EJES, capacidad_fig, granulometria_fig
from mandibula_svg import (
    AMP_RANGE,
    SPEED_RANGE,
    VIEW_FULL,
    VIEWS,
    abertura_svg,
    jaw_svg,
)
from planta_tab import comparar_con_planta, factor_aplicado, nota_calibracion

KEY_EQUIPO, KEY_PARRILLA, KEY_MODELO = PREFIX + "equipo", PREFIX + "grizzly", PREFIX + "model"
KEY_VISTA, KEY_AMP, KEY_VEL, KEY_EJE = (PREFIX + k for k in ("vista", "amp", "vel", "eje"))
AMP_DEFECTO, VEL_DEFECTO = 3.0, 10
NIVEL_PEOR = {"ok": 0, "aviso": 1, "mal": 2}


def _num(x: float) -> str:
    return int_num(x) if float(x).is_integer() else num_g(x)


# ------------------------------------------------------------------ equipos predefinidos
def _nombre_equipo(name: str) -> str:
    if name == PERSONALIZADO:
        return t("jaw.equipo.personalizado")
    m = POR_NOMBRE[name]
    return t("jaw.equipo.item", name=name, kw=num_g(m.kw), rpm=num_g(m.rpm))


def _oss_de_tabla(name: str) -> list[int]:
    return sorted(POR_NOMBRE[name].capacidad_tph)


def _aplicar_valores(vals: dict[str, float]) -> None:
    for k, v in vals.items():
        st.session_state[PREFIX + k] = v


def _equipo_cb() -> None:
    """Al elegir un equipo de la tabla: sus datos y un OSS de la tabla (el del medio)."""
    name = st.session_state[KEY_EQUIPO]
    if name == PERSONALIZADO or name not in POR_NOMBRE:
        return
    osss = _oss_de_tabla(name)
    oss = osss[len(osss) // 2]
    _aplicar_valores(valores_de_equipo(POR_NOMBRE[name], oss))
    st.session_state[f"{PREFIX}oss_{name}"] = oss


def _oss_cb(name: str) -> None:
    oss = st.session_state[f"{PREFIX}oss_{name}"]
    vals = valores_de_equipo(POR_NOMBRE[name], oss)
    stroke = st.session_state.get(PREFIX + "stroke", vals["stroke"])
    _aplicar_valores({"css": round(oss - stroke, 2), "tph": vals["tph"], "grz_ap": vals["grz_ap"]})


def _restablecer() -> None:
    for k in [k for k in st.session_state if str(k).startswith(PREFIX)]:
        del st.session_state[k]


def _ask(c, container) -> float:
    label = f"{t(c.label_k)} ({c.unit})" if c.unit else t(c.label_k)
    help_ = f"{t(c.meaning_k)} {t(c.source_k)}. [{_num(c.lo)}–{_num(c.hi)}]"
    return container.number_input(
        label, float(c.lo), float(c.hi), float(c.default), float(c.step), format="%g",
        help=help_, key=PREFIX + c.key,
    )  # fmt: skip


def _controles() -> dict[str, object]:
    st.subheader(t("jaw.h.equipos"))
    st.caption(t("jaw.equipos.intro"))
    left, right = st.columns(2)
    opciones = [*POR_NOMBRE, PERSONALIZADO]
    rotulos = {n: _nombre_equipo(n) for n in opciones}
    left.selectbox(t("jaw.equipo.label"), opciones, index=opciones.index(EJEMPLO_EQUIPO),
                   format_func=rotulos.__getitem__, key=KEY_EQUIPO, on_change=_equipo_cb,
                   help=t("jaw.equipo.help"))  # fmt: skip
    name = st.session_state.get(KEY_EQUIPO, EJEMPLO_EQUIPO)
    if name in POR_NOMBRE:
        right.selectbox(t("jaw.oss.label"), _oss_de_tabla(name), key=f"{PREFIX}oss_{name}",
                        on_change=_oss_cb, args=(name,), help=t("jaw.oss.help"))  # fmt: skip
    st.subheader(t("jaw.h.controles"))
    values: dict[str, object] = {}
    for group in (G_MAQ, G_ALIM, G_PARR):
        st.markdown(f"**{t('jaw.group.' + group)}**")
        cols = st.columns(3)
        fields = [c for c in CAMPOS if c.group == group]
        for i, c in enumerate(fields):
            values[c.key] = _ask(c, cols[i % 3])
        if group == G_ALIM:
            values["model"] = cols[len(fields) % 3].selectbox(
                t("jaw.campo.model.label"), MODELOS, key=KEY_MODELO,
                format_func={m: t("jaw.model." + m) for m in MODELOS}.__getitem__,
                help=t("jaw.campo.model.meaning"))  # fmt: skip
        if group == G_PARR:
            values["grizzly"] = cols[len(fields) % 3].toggle(
                t("jaw.campo.grizzly.label"), value=True, key=KEY_PARRILLA,
                help=t("jaw.campo.grizzly.meaning"))  # fmt: skip
    st.button(t("jaw.reset"), on_click=_restablecer)
    return values


# ------------------------------------------------------------------ indicadores y estado
def _indicadores(c: Calculo) -> None:
    """Seis indicadores en dos filas de tres: rótulos cortos (el nombre completo va en la ayuda)."""
    j = c.jaw
    fila1, fila2 = st.columns(3), st.columns(3)
    fila1[0].metric(t("jaw.m.cap"), es(c.capacidad, 1), help=t("jaw.m.cap.help"))
    fila1[1].metric(t("jaw.m.util"), es(100 * c.utilizacion, 0) + " %", help=t("jaw.m.util.help"))
    fila1[2].metric(t("jaw.m.p80"), es(c.p80, 1), help=t("jaw.m.p80.help"))
    fila2[0].metric(t("jaw.m.pot"), f"{es(c.potencia, 1)} / {es(j.power_kw or 0.0, 0)}",
                    help=t("jaw.m.pot.help"))  # fmt: skip
    fila2[1].metric(t("jaw.m.nnc"), es(j.rpm / j.critical_rpm, 2), help=t("jaw.m.nnc.help"))
    fila2[2].metric(t("jaw.m.ang"), f"{es(j.bite_angle_deg, 1)} / {es(j.bite_limit_deg, 1)}",
                    help=t("jaw.m.ang.help"))  # fmt: skip


def _valor(v: float, d: int = 1) -> str:
    return es(v, d)


def _fila(ch) -> Fila:
    """Un `Chequeo` de la librería, con su texto (números del cálculo) y su fuente."""
    v = ch.valores
    campos = dict(
        theta=_valor(v.get("theta_deg", 0.0)), limite=_valor(v.get("limite_deg", 0.0)),
        rpm=_valor(v.get("rpm", 0.0), 0), nc=_valor(v.get("rpm_critica", 0.0), 0),
        min=_num(v.get("min", 0.0)), max=_num(v.get("max", 0.0)),
        carrera=_valor(v.get("carrera_cm", 0.0)), pct=_valor(100 * v.get("fraccion", 0.0)),
        tam=_valor(v.get("tamano_um", 0.0) / MM, 0), razon=_valor(v.get("razon", 0.0)),
        alim=_valor(v.get("alimentacion_tph", 0.0)), cap=_valor(v.get("capacidad_tph", 0.0)),
        util=_valor(100 * v.get("utilizacion", 0.0), 0), req=_valor(v.get("requerida_kw", 0.0)),
        inst=_valor(v.get("instalada_kw", 0.0), 0), f=_valor(v.get("factor", 1.0), 2),
    )  # fmt: skip
    texto = t(f"jaw.chk.{ch.codigo}", **campos)
    rebalse = v.get("minutos_a_rebalse", float("inf"))
    if ch.codigo == "sobrecarga" and ch.nivel == "mal" and rebalse != float("inf"):
        texto += " " + t("jaw.chk.rebalse", min=_valor(rebalse, 0))
    ayuda = t(f"jaw.crit.{ch.codigo}") + " " + t("jaw.fuente", fuente=t(f"jaw.fuente.{ch.fuente}"))
    return Fila(ch.nivel, texto, ayuda)


def _estado(c: Calculo) -> None:
    st.subheader(t("jaw.h.estado"))
    panel([_fila(ch) for ch in c.checks])


def _king(c: Calculo) -> None:
    hit = punto_king(c)
    if hit is None:
        return
    m, oss, q = hit
    mod = c.jaw.capacity_tph()
    st.caption(t("jaw.king", name=m.nombre, oss=_num(oss), q=_num(q), m=es(mod, 0),
                 d=es(100 * (mod / q - 1), 0)))  # fmt: skip


# ------------------------------------------------------------------ esquema
def _vista_controles() -> tuple[str, float, float]:
    """Los tres controles de la vista (solo cambian el dibujo); no dependen del cálculo."""
    st.subheader(t("jaw.h.esquema"))
    a, b, d = st.columns(3)
    view = a.radio(t("jaw.vista.label"), VIEWS, horizontal=True, key=KEY_VISTA,
                   format_func={v: t("jaw.vista." + v) for v in VIEWS}.__getitem__,
                   help=t("jaw.vista.help"))  # fmt: skip
    amp = b.slider(t("jaw.amp.label"), AMP_RANGE[0], AMP_RANGE[1], AMP_DEFECTO, 0.5, key=KEY_AMP,
                   help=t("jaw.amp.help"))  # fmt: skip
    vel = d.slider(t("jaw.vel.label"), SPEED_RANGE[0], SPEED_RANGE[1], VEL_DEFECTO, 5, key=KEY_VEL,
                   help=t("jaw.vel.help"))  # fmt: skip
    return (view if view in VIEWS else VIEW_FULL), amp, vel


def _vista(c: Calculo, animate: bool, view: str, amp: float, vel: float) -> None:
    st.html(as_images(jaw_svg(c, amp, vel, view, paused=not animate),
                      jaw_svg(c, amp, vel, view, paused=True), t("jaw.svg.label")))  # fmt: skip
    j = c.jaw
    left, right = st.columns(2)
    left.html(as_images(abertura_svg(j.css_eff_mm, j.oss_mm, j.rpm, vel, not animate),
                        abertura_svg(j.css_eff_mm, j.oss_mm, j.rpm, vel, True),
                        t("jaw.svg.ab.label")))  # fmt: skip
    right.markdown(t("jaw.ab.texto", css=es(j.css_eff_mm, 1), oss=es(j.oss_mm, 1),
                     l=es(j.stroke, 1), s=es(60.0 / j.rpm, 3)))  # fmt: skip


# ------------------------------------------------------------------ curvas y balance
def _curvas_controles() -> str:
    st.subheader(t("jaw.h.curvas"))
    eje = st.radio(t("jaw.eje.label"), EJES, horizontal=True, key=KEY_EJE,
                   format_func={v: t("jaw.eje." + v) for v in EJES}.__getitem__,
                   help=t("jaw.eje.help"))  # fmt: skip
    return eje if eje in EJES else EJES[0]


def _curvas(c: Calculo, eje: str) -> None:
    st.plotly_chart(granulometria_fig(c), width="stretch")
    st.plotly_chart(capacidad_fig(c, eje), width="stretch")
    st.caption(t("jaw.curvas.nota"))
    nota_calibracion(c, curvas=True)


def balance_table(c: Calculo) -> pd.DataFrame:
    """Las corrientes del circuito: t/h, P80, P50 (mm) y % bajo el CSS efectivo."""
    streams = [("mina", c.mina), ("pasante", c.pasante), ("carga", c.carga),
               ("prod", c.prod_chancador), ("total", c.producto)]  # fmt: skip
    rows = []
    for key, s in streams:
        if s is None:
            continue
        ok = s.total_solids > 0
        rows.append({
            t("jaw.bal.corriente"): t("jaw.bal." + key),
            t("jaw.bal.tph"): round(s.total_solids, 2),
            t("jaw.bal.p80"): round(s.p80 / MM, 2) if ok else None,
            t("jaw.bal.p50"): round(s.size_at(0.5) / MM, 2) if ok else None,
            t("jaw.bal.css"): round(100 * c.bajo_css(s), 1),
        })  # fmt: skip
    return pd.DataFrame(rows)


def _balance(c: Calculo) -> None:
    st.subheader(t("jaw.h.balance"))
    df = balance_table(c)
    st.dataframe(df, hide_index=True, width="stretch")
    st.caption(t("jaw.balance", in_=es(c.mina.total_solids, 3), out=es(c.producto.total_solids, 3),
                 err=cientifico(c.cierre())))  # fmt: skip
    st.download_button(t("jaw.dl"), df.to_csv(index=False), "chancado_primario.csv")


# ------------------------------------------------------------------ prueba esto
@lru_cache(maxsize=1)
def pares_de_experimentos() -> tuple:
    """(experimento, estado de ejemplo, estado tras el cambio) de cada experimento."""
    base = valores_por_defecto()
    return tuple((e, ejemplo(), con_cambios(base, **e.cambios)) for e in EXPERIMENTOS)


def _colpas_pct(c: Calculo) -> float:
    return 100 * next(ch.valores["fraccion"] for ch in c.checks if ch.codigo == "colpas")


def numeros(a: Calculo, b: Calculo) -> dict[str, str]:
    """Las cifras que llevan los textos de «Prueba esto»: antes (0) y después (1)."""
    out: dict[str, str] = {}
    for i, c in enumerate((a, b)):
        j = c.jaw
        out.update({
            f"css{i}": es(j.css_eff_mm, 1), f"oss{i}": es(j.oss_mm, 1),
            f"q{i}": es(c.capacidad, 0), f"u{i}": es(100 * c.utilizacion, 0),
            f"p{i}": es(c.p80, 0), f"feed{i}": es(c.carga.total_solids, 0),
            f"nc{i}": es(j.critical_rpm, 0), f"rpm{i}": es(j.rpm, 0),
            f"ratio{i}": es(c.carga.f80 / c.prod_chancador.p80, 1),
            f"pot{i}": es(c.potencia, 0), f"inst{i}": es(j.power_kw or 0.0, 0),
            f"wi{i}": es(j.wi, 1), f"top{i}": es(float(c.v["top"]), 0),  # type: ignore[arg-type]
            f"colpas{i}": es(_colpas_pct(c), 1), f"lim{i}": es(0.8 * j.gape_mm, 0),
            f"wear{i}": es(j.wear_mm, 0),
        })  # fmt: skip
    return out


def pruebas_de_ejemplo() -> list[Prueba]:
    return [
        Prueba(
            e.clave,
            t(f"jaw.exp.{e.clave}.titulo"),
            t(f"jaw.exp.{e.clave}.texto", **numeros(a, b)),
            {PREFIX + k: v for k, v in e.cambios.items()},
        )  # fmt: skip
        for e, a, b in pares_de_experimentos()
    ]


def _prueba_esto() -> None:
    st.subheader(t("jaw.h.prueba"))
    st.markdown(t("jaw.prueba.intro"))
    pruebas(pruebas_de_ejemplo(), PREFIX, _restablecer)


# ------------------------------------------------------------------ guía de la pestaña
def datos_table() -> pd.DataFrame:
    """La tabla de datos de la guía, de las mismas definiciones que los controles."""
    rows = [
        {
            t("jaw.col.campo"): t(c.label_k),
            t("jaw.col.unit"): c.unit,
            t("jaw.col.range"): f"{_num(c.lo)}–{_num(c.hi)}",
            t("jaw.col.example"): _num(c.default),
            t("jaw.col.what"): t(c.meaning_k),
            t("jaw.col.how"): t(c.source_k)[0].upper() + t(c.source_k)[1:],
        }
        for c in CAMPOS
    ]
    opciones = ", ".join(t("jaw.model." + m) for m in MODELOS)
    como = t("jaw.src.definicion")[0].upper() + t("jaw.src.definicion")[1:]
    for key, rng, ex in (("model", opciones, t("jaw.model.nordberg")),
                         ("grizzly", t("jaw.si_no"), t("jaw.si"))):  # fmt: skip
        rows.append({
            t("jaw.col.campo"): t(f"jaw.campo.{key}.label"),
            t("jaw.col.unit"): "",
            t("jaw.col.range"): rng,
            t("jaw.col.example"): ex,
            t("jaw.col.what"): t(f"jaw.campo.{key}.meaning"),
            t("jaw.col.how"): como,
        })  # fmt: skip
    return pd.DataFrame(rows)


def _guia() -> None:
    with st.expander(t("jaw.guia.titulo")):
        st.markdown(t("jaw.guia.como"))
        st.markdown(t("jaw.guia.ecuaciones"))
        for i in range(1, 7):
            st.latex(t(f"jaw.guia.eq{i}"))
        st.markdown(t("jaw.guia.supuestos"))
        st.markdown(t("jaw.guia.validacion"))
        st.markdown(t("jaw.guia.datos"))
        st.markdown(markdown_table(datos_table()))
        st.markdown(t("jaw.guia.fuentes"))


# ------------------------------------------------------------------ la pestaña
def mandibula_tab(animate: bool) -> None:
    top = st.container()
    controls = st.container()
    with controls:
        values = _controles()
    values["kf"] = factor_aplicado()  # factor de planta (1 = k de King); ver planta_datos
    problem = validar(values)
    calc, error = None, None
    if problem is None:
        try:
            calc = calcular(values)
        except ValueError as exc:
            error = t("jaw.err.modelo", msg=tr_error(str(exc)))
    else:
        error = t(problem)
    with top:
        if calc is None:
            st.error(error)
        else:
            _indicadores(calc)
            nota_calibracion(calc)
            _estado(calc)
        view, amp, vel = _vista_controles()
        if calc is not None:
            _vista(calc, animate, view, amp, vel)
    with controls:
        if calc is not None:
            _king(calc)
    eje = _curvas_controles()
    if calc is not None:
        _curvas(calc, eje)
        _balance(calc)
        comparar_con_planta(calc)
    _prueba_esto()
    _guia()
