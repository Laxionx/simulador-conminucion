"""Sección «Comparar con tu planta» de «Chancado primario»: la capacidad y el P80 medidos del
visitante contra el modelo, la calibración de k (factor de planta f) y el desgaste implícito en el
P80. El cálculo está en `planta_datos.py`. Solo se dibujan números y textos de diccionarios."""

from __future__ import annotations

import streamlit as st
from equipos import es
from i18n import t
from mandibula_datos import F_PLANTA_MAX, F_PLANTA_MIN, PREFIX, Calculo
from planta_datos import (
    DESGASTE_MAX_MM,
    ComparaCapacidad,
    ComparaP80,
    comparar_capacidad,
    comparar_p80,
    factor_k,
)

KEY_KF, KEY_Q, KEY_P80 = PREFIX + "kf", PREFIX + "q_med", PREFIX + "p80_med"
KEY_WEAR = PREFIX + "wear"
Q_MAX, P80_MAX = 100_000.0, 5_000.0


def factor_aplicado() -> float:
    """El factor de planta de la sesión (1 = k de King)."""
    return float(st.session_state.get(KEY_KF, 1.0))


def _fijar_factor(f: float) -> None:
    st.session_state[KEY_KF] = f


def _fijar_desgaste(mm: float) -> None:
    st.session_state[KEY_WEAR] = float(mm)


def nota_calibracion(c: Calculo, curvas: bool = False) -> None:
    """Debajo de los indicadores y de las curvas: dice que k está calibrado con la planta."""
    f = factor_k(c)
    if f == 1.0:
        return
    if curvas:
        st.caption(t("plant.cal.curvas", f=es(f, 3)))
    else:
        k = c.jaw.k
        st.caption(t("plant.cal.activa", f=es(f, 3), k=es(k, 3), k0=es(k / f, 3)))


def _capacidad(c: Calculo, q: float | None) -> None:
    if q is not None:
        cap = comparar_capacidad(c, q)
        _texto_capacidad(cap, q)
        if cap.calibrable:
            st.button(t("plant.btn.usar"), key=PREFIX + "usar_cal", on_click=_fijar_factor,
                      args=(cap.f,))  # fmt: skip
    if factor_k(c) != 1.0:
        st.button(t("plant.btn.king"), key=PREFIX + "volver_king", on_click=_fijar_factor,
                  args=(1.0,))  # fmt: skip


def _texto_capacidad(cap: ComparaCapacidad, q: float) -> None:
    if cap.estado == "motor":
        st.warning(t("plant.q.motor", motor=es(cap.q_motor, 1), vol=es(cap.q_volumetrica, 1)))
    elif cap.estado == "motor_medido":
        st.warning(t("plant.q.motor2", medido=es(q, 1), motor=es(cap.q_motor, 1)))
    elif cap.estado == "rango":
        st.warning(t("plant.q.rango", f=es(cap.f, 3), lo=es(F_PLANTA_MIN, 1),
                     hi=es(F_PLANTA_MAX, 0)))  # fmt: skip
    else:
        st.markdown(t("plant.q.res", modelo=es(cap.q_modelo, 1), medido=es(q, 1),
                      delta=es(cap.delta_pct, 1), f=es(cap.f, 3),
                      kplanta=es(cap.k_planta, 3)))  # fmt: skip


def _p80(c: Calculo, p80: float | None) -> None:
    if p80 is None:
        return
    r = comparar_p80(c, p80)
    _texto_p80(r, c)
    if r.aplicable:
        st.button(t("plant.btn.desgaste"), key=PREFIX + "usar_desgaste", on_click=_fijar_desgaste,
                  args=(round(r.desgaste, 2),))  # fmt: skip
    st.caption(t("plant.p80.nota"))


def _texto_p80(r: ComparaP80, c: Calculo) -> None:
    st.markdown(t("plant.p80.res", razon=es(r.razon, 3), oss=es(r.oss_implicito, 1),
                  nominal=es(r.oss_nominal, 1), dif=es(r.diferencia, 1)))  # fmt: skip
    if r.estado == "neg":
        st.warning(t("plant.p80.neg"))
    elif r.estado == "fuera":
        st.warning(t("plant.p80.fuera", wear=es(r.desgaste, 1), hi=es(DESGASTE_MAX_MM, 0)))
    else:
        st.markdown(t("plant.p80.desgaste", wear=es(r.desgaste, 1),
                      actual=es(c.jaw.wear_mm, 1)))  # fmt: skip


def comparar_con_planta(c: Calculo) -> None:
    """Dibuja la sección. Los dos campos son opcionales y se miden con los controles actuales."""
    st.subheader(t("plant.h"))
    st.markdown(t("plant.intro"))
    a, b = st.columns(2)
    q = a.number_input(t("plant.q.label"), 0.1, Q_MAX, value=None, step=1.0, format="%g",
                       key=KEY_Q, help=t("plant.q.help"))  # fmt: skip
    p80 = b.number_input(t("plant.p80.label"), 0.1, P80_MAX, value=None, step=1.0, format="%g",
                         key=KEY_P80, help=t("plant.p80.help"))  # fmt: skip
    _capacidad(c, q)
    _p80(c, p80)
