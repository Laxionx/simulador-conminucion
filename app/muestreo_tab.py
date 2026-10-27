"""«Ajuste a datos» con un muestreo real de molienda: elegir la fuente (tus datos o el muestreo
publicado de Vazante), cargar la tabla (pegada o desde CSV/XLSX), y ver el estado del muestreo, las
granulometrías reconciliadas, la partición ajustada y los r/d del molino. El cálculo está en
`muestreo_datos.py`. Nada de lo que escribe o sube el visitante entra al HTML: solo números."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from carga import ErrorCarga, cargador, mensaje_error
from controles import KNOT_SIZES
from equipos import es
from estado import Fila, panel
from i18n import current, t
from muestreo_datos import (
    CLAVES_TABLA,
    COLUMNAS_ARCHIVO,
    COLUMNAS_TABLA,
    CORRIENTES,
    Z_CORTE,
    Resultado,
    analizar,
    solidos_de_archivo,
    tabla_de_levantamiento,
)

from conminucion.circuits import CircuitConfig
from conminucion.classifier import EfficiencyCurve
from conminucion.plantas_reales import CLASE_MAX_AJUSTE_UM, VAZANTE_C1

PREFIX = "mu_"
KEY_BASE, KEY_VER, KEY_TABLA = PREFIX + "base", PREFIX + "ver", PREFIX + "tabla"
KEY_USAR = PREFIX + "sol_usar"
KEYS_SOLIDOS = tuple(PREFIX + "sol_" + c for c in CORRIENTES)
FUENTES = ("sintetico", "tus", "vazante")
SOLIDOS_VAZANTE = VAZANTE_C1.solidos_pct
COLORES = {"alim": "tab:blue", "uf": "tab:red", "of": "tab:green"}


def _tabla_editable(base: pd.DataFrame) -> pd.DataFrame:
    config = {
        c.clave: st.column_config.NumberColumn(c.titulo(current()), format="%g")
        for c in COLUMNAS_TABLA
    }
    ver = st.session_state.get(KEY_VER, 0)
    key = KEY_TABLA if ver == 0 else f"{KEY_TABLA}_{ver}"
    return st.data_editor(base, key=key, num_rows="dynamic", hide_index=True,
                          column_config=config, width="stretch")  # fmt: skip


def _solidos() -> tuple[float, float, float] | None:
    """Los tres % de sólidos si el visitante los tiene (con el ejemplo de Vazante por defecto)."""
    st.session_state.setdefault(KEY_USAR, True)
    for k, v in zip(KEYS_SOLIDOS, SOLIDOS_VAZANTE, strict=True):
        st.session_state.setdefault(k, float(v))
    st.checkbox(t("mu.sol.usar"), key=KEY_USAR, help=t("mu.sol.usar.help"))
    if not st.session_state[KEY_USAR]:
        return None
    cols = st.columns(3)
    vals = [
        c.number_input(t("mu.sol." + n), 0.0, 100.0, step=0.1, format="%g", key=k)
        for c, n, k in zip(cols, CORRIENTES, KEYS_SOLIDOS, strict=True)
    ]
    return vals[0], vals[1], vals[2]


def _entrada_tus_datos() -> tuple[pd.DataFrame, tuple[float, float, float] | None]:
    st.markdown(t("mu.intro.tus"))
    ejemplo = tabla_de_levantamiento(VAZANTE_C1).reindex(
        columns=[c.clave for c in COLUMNAS_ARCHIVO]
    )
    ejemplo.loc[0, ["solidos_alim", "solidos_uf", "solidos_of"]] = SOLIDOS_VAZANTE
    nuevo = cargador("mu", COLUMNAS_ARCHIVO, ejemplo)
    if nuevo is not None:
        st.session_state[KEY_BASE] = nuevo[CLAVES_TABLA]
        st.session_state[KEY_VER] = st.session_state.get(KEY_VER, 0) + 1
        sol = solidos_de_archivo(nuevo)
        st.session_state[KEY_USAR] = sol is not None
        if sol is not None:
            for k, v in zip(KEYS_SOLIDOS, sol, strict=True):
                st.session_state[k] = v
    st.subheader(t("mu.h.datos"))
    st.caption(t("mu.tabla.ayuda"))
    tabla = _tabla_editable(st.session_state.get(KEY_BASE, tabla_de_levantamiento(VAZANTE_C1)))
    return tabla, _solidos()


# ------------------------------------------------------------------ resultados
def _nombre(corriente: str) -> str:
    return t("mu.col." + corriente)


def _fmt(x: float) -> str:
    return f"{x:g}"


def _estado(r: Resultado) -> None:
    st.subheader(t("mu.h.estado"))
    ok_chi = r.chi2 <= r.chi2_critico
    m = r.mayor_ajuste
    ok_z = abs(m.z) <= Z_CORTE
    chi = dict(chi2=es(r.chi2, 2), crit=es(r.chi2_critico, 2), gl=r.grados_libertad)
    zc = dict(z=es(m.z, 2), corriente=_nombre(m.corriente), inf=_fmt(m.inferior_um),
              sup=_fmt(m.superior_um))  # fmt: skip
    panel([
        Fila("ok" if ok_chi else "aviso", t("mu.est.chi2." + ("ok" if ok_chi else "mal"), **chi),
             t("mu.est.chi2.ayuda")),
        Fila("ok" if ok_z else "aviso", t("mu.est.z." + ("ok" if ok_z else "mal"), **zc),
             t("mu.est.z.ayuda")),
    ], t("mu.est.todo_ok"))  # fmt: skip
    fila1, fila2 = st.columns(3), st.columns(3)
    fila1[0].metric(t("mu.m.r"), es(r.r, 4), help=t("mu.m.r.help"))
    fila1[1].metric(t("mu.m.cl"), es(r.carga_circulante, 3), help=t("mu.m.cl.help"))
    fila1[2].metric(t("mu.m.chi2"), es(r.chi2, 2), help=t("mu.m.chi2.help"))
    antes, despues = es(100 * r.cierre_antes, 2), es(100 * r.cierre_despues, 2)
    fila2[0].metric(t("mu.m.cierre"), f"{antes} → {despues}", help=t("mu.m.cierre.help"))
    fila2[1].metric(t("mu.m.z"), es(abs(m.z), 2), help=t("mu.m.z.help"))
    fila2[2].metric(t("mu.m.ic"), es(r.ancho_ic_d50c, 1), help=t("mu.m.ic.help"))
    st.caption(t("mu.nota.diagnostico"))


def tabla_granulometrias(r: Resultado) -> pd.DataFrame:
    """% retenido por clase, medido y reconciliado, y su z, con encabezados del idioma."""
    clases = []
    for k in range(len(r.tamices_um)):
        inf, sup = r.limites_clase(k)
        clases.append(f"{_fmt(sup)}–{_fmt(inf)}" if inf > 0 else f"<{_fmt(sup)}")
    out = {t("mu.col.clase"): clases}
    for c in CORRIENTES:
        out[t("mu.col.medido", corriente=_nombre(c))] = np.round(100 * r.medidas[c], 2)
        out[t("mu.col.reconc", corriente=_nombre(c))] = np.round(100 * r.reconciliadas[c], 2)
        out[t("mu.col.z", corriente=_nombre(c))] = np.round(r.z[c], 2)
    return pd.DataFrame(out)


def _pasante(retenido: np.ndarray) -> np.ndarray:
    return 100.0 * np.cumsum(retenido[::-1])[::-1]


def _grafico_granulometrias(r: Resultado) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.8))
    for c in CORRIENTES:
        n = _nombre(c)
        ax.plot(r.tamices_um, _pasante(r.medidas[c]), "o", ms=4, color=COLORES[c],
                label=t("mu.plot.medido", corriente=n))  # fmt: skip
        ax.plot(r.tamices_um, _pasante(r.reconciliadas[c]), "-", color=COLORES[c],
                label=t("mu.plot.reconc", corriente=n))  # fmt: skip
    ax.set(xscale="log", xlabel=t("mu.plot.size"), ylabel=t("mu.plot.pass"))
    ax.legend(fontsize=7)
    ax.grid(True, which="both", alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)


def _grafico_particion(r: Resultado) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.8))
    ax.scatter(r.part_x_um[r.usadas], r.part_pct[r.usadas], s=22, color="tab:blue",
               label=t("mu.plot.part.medida"), zorder=3)  # fmt: skip
    ax.scatter(r.part_x_um[~r.usadas], r.part_pct[~r.usadas], s=22, facecolors="none",
               edgecolors="tab:gray", label=t("mu.plot.part.fuera"), zorder=3)  # fmt: skip
    xs = np.geomspace(r.part_x_um.min(), r.part_x_um.max(), 200)
    ax.plot(xs, 100 * EfficiencyCurve(r.d50c, r.alpha, r.rf).efficiency(xs), color="tab:red",
            label=t("mu.plot.part.ajustada"))  # fmt: skip
    if r.metodo == "rf_fijo":
        libre = EfficiencyCurve(*(float(v) for v in r.libre.values)).efficiency(xs)
        ax.plot(xs, 100 * libre, "--", color="tab:gray", label=t("mu.plot.part.libre"))
    ax.set(xscale="log", xlabel=t("mu.plot.size"), ylabel=t("mu.plot.part.y"))
    ax.legend(fontsize=7)
    ax.grid(True, which="both", alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)


# Dominio físico de cada parámetro: d50c y α positivos, Rf entre 0 y 1, r/d positivo.
DOMINIO = {"d50c": (0.0, None), "alpha": (0.0, None), "Rf": (0.0, 1.0)}


def limite_ic(x: float, dominio: tuple[float | None, float | None] = (0.0, None)) -> str:
    """Un límite del IC lineal, o «no fiable» si cae fuera del dominio físico: el jacobiano con
    pocos puntos puede dar, por ejemplo, un d50c negativo, y ese número no se muestra."""
    bajo, alto = dominio
    fuera = (bajo is not None and x < bajo) or (alto is not None and x > alto)
    imposible = bajo == 0.0 and alto is None and x <= 0.0  # positivos estrictos
    if not np.isfinite(x) or fuera or imposible:
        return t("mu.p.nofiable")
    return es(x, 4)


def tabla_parametros(r: Resultado) -> pd.DataFrame:
    """d50c, α y Rf: el valor del método usado, y el ajuste libre con su IC95 %."""
    usado = (r.d50c, r.alpha, r.rf)
    filas = []
    for i, (nombre, (v, lo, hi)) in enumerate(r.libre.as_dict().items()):
        dom = DOMINIO.get(nombre, (None, None))
        filas.append({t("mu.p.param"): nombre, t("mu.p.valor"): es(usado[i], 4),
                      t("mu.p.libre"): es(v, 4), t("mu.p.lo"): limite_ic(lo, dom),
                      t("mu.p.hi"): limite_ic(hi, dom)})  # fmt: skip
    return pd.DataFrame(filas)


def _particion(r: Resultado, publicado: bool) -> None:
    st.subheader(t("mu.h.part"))
    st.markdown(t("mu.metodo.fijo" if r.metodo == "rf_fijo" else "mu.metodo.libre"))
    st.caption(t("mu.metodo.clases", n=int(r.usadas.sum()), corte=_fmt(CLASE_MAX_AJUSTE_UM)))
    _grafico_particion(r)
    st.subheader(t("mu.h.params"))
    st.dataframe(tabla_parametros(r), hide_index=True)
    st.caption(t("mu.params.nota"))
    if publicado:
        pub_d, pub_a = VAZANTE_C1.d50c_um, VAZANTE_C1.alpha
        st.caption(t("mu.pub", d50c=es(pub_d, 1), mio=es(r.d50c, 1),
                     dd=es(100 * (r.d50c / pub_d - 1), 1), a=es(pub_a, 2), amio=es(r.alpha, 2),
                     da=es(100 * (r.alpha / pub_a - 1), 1)))  # fmt: skip


def _molino(r: Resultado, knots: tuple[float, ...]) -> None:
    if r.molino is None and r.molino_error is None:
        return
    st.subheader(t("mu.h.molino"))
    if r.molino is None:
        st.warning(t(r.molino_error or "mu.err.ajuste"))
        return
    st.caption(t("mu.molino.nota", nudos=", ".join(_fmt(k) for k in knots)))
    f = r.molino
    st.dataframe(pd.DataFrame({
        t("mu.molino.param"): [_fmt(k) for k in knots], t("mu.molino.rd"): np.round(f.values, 4),
        t("mu.molino.lo"): [limite_ic(x) for x in f.ci_low],
        t("mu.molino.hi"): [limite_ic(x) for x in f.ci_high],
    }), hide_index=True)  # fmt: skip


def _mostrar(r: Resultado, publicado: bool, knots: tuple[float, ...]) -> None:
    _estado(r)
    st.subheader(t("mu.h.gran"))
    st.caption(t("mu.gran.caption"))
    st.dataframe(tabla_granulometrias(r), hide_index=True, width="stretch")
    _grafico_granulometrias(r)
    _particion(r, publicado)
    _molino(r, knots)


def muestreo_real(cfg: CircuitConfig, fuente: str) -> None:
    """El ajuste con la fuente «tus» datos o «vazante» (la sintética la dibuja `principal.py`)."""
    if fuente == "vazante":
        st.markdown(t("mu.intro.vazante"))
        tabla, solidos = tabla_de_levantamiento(VAZANTE_C1), SOLIDOS_VAZANTE
        columnas = {c.clave: c.titulo(current()) for c in COLUMNAS_TABLA[:4]}
        st.dataframe(tabla[list(columnas)].rename(columns=columnas), hide_index=True)
    else:
        tabla, solidos = _entrada_tus_datos()
    molino = (KNOT_SIZES, cfg.mill.fracture, cfg.mill.n_mixers)
    try:
        r = analizar(tabla, solidos, molino)
    except ErrorCarga as e:
        st.warning(mensaje_error(e))
        return
    _mostrar(r, fuente == "vazante", KNOT_SIZES)
