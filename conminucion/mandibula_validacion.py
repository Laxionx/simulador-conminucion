"""Validación del chancador de mandíbula contra datos publicados.

A) Capacidad contra la Tabla 3.1 de King (56 puntos) con cuatro modelos: M1 referencia R
   (sin parámetros), M2 la misma cinemática con un factor k ajustado, M3 Taggart y M4 un
   control empírico Q = a·W^b·OSS^c. M2 y M4 se evalúan fuera de muestra dejando fuera un
   tamaño entero cada vez.
B) Producto contra la curva estándar de Nordberg (referencia R y «whiten» ajustado).

Aquí solo hay cálculo; los listones (tolerancias) viven en las pruebas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from .bond import bond_energy
from .datos_mandibula import F80_SOBRE_BOCA, K_REF, TABLA_KING, WI_EJERCICIO_3_1
from .mandibula import JawCrusher, carrera_amit_mm, pasante_en, taggart_tph
from .mandibula_producto import (
    MM,
    nordberg_cumulative,
    nordberg_p80_over_oss,
    referencia_producto,
)
from .sizes import SizeGrid, rosin_rammler
from .stream import Stream

# ---------------------------------------------------------------- A) capacidad


@dataclass(frozen=True)
class PuntoKing:
    nombre: str
    boca_mm: float
    largo_mm: float
    rpm: float
    kw: float
    oss_mm: float
    q_tph: float


def puntos_king() -> list[PuntoKing]:
    """Los 56 puntos (máquina, OSS) de la Tabla 3.1."""
    return [
        PuntoKing(m.nombre, m.boca_mm, m.largo_mm, m.rpm, m.kw, float(oss), q)
        for m in TABLA_KING
        for oss, q in m.capacidad_tph.items()
    ]


def mandibula_de_punto(p: PuntoKing, k: float = K_REF) -> JawCrusher:
    """CSS = OSS - L_T (regla AMIT), D = 2G, N = rpm de la tabla, W = largo."""
    css = p.oss_mm - carrera_amit_mm(p.boca_mm)
    return JawCrusher(p.boca_mm, p.largo_mm, css, p.rpm, power_kw=p.kw, k=k)


def error_pct(pred, obs) -> np.ndarray:
    return 100.0 * (np.asarray(pred, dtype=float) / np.asarray(obs, dtype=float) - 1.0)


def _capacidad_unitaria(puntos: list[PuntoKing]) -> np.ndarray:
    return np.array([mandibula_de_punto(p, 1.0).capacity_tph() for p in puntos])


def _tamanos(puntos: list[PuntoKing]) -> list[str]:
    return list(dict.fromkeys(p.nombre for p in puntos))


def modelo_m1(puntos: list[PuntoKing]) -> np.ndarray:
    """Referencia R: k = ρ_s·φ = 2,7·0,55, sin parámetros libres."""
    return K_REF * _capacidad_unitaria(puntos)


def modelo_m3(puntos: list[PuntoKing]) -> np.ndarray:
    """Taggart con ρ_b = 1,6."""
    return np.array([taggart_tph(p.largo_mm, p.oss_mm) for p in puntos])


def modelo_m2_cv(puntos: list[PuntoKing]) -> tuple[np.ndarray, dict[str, float], float]:
    """Cinemática con un factor k por mínimos cuadrados en log, fuera de muestra por tamaño.
    Devuelve (predicción, k por pliegue, k global)."""
    unit = _capacidad_unitaria(puntos)
    obs = np.array([p.q_tph for p in puntos])
    nombres = np.array([p.nombre for p in puntos])
    log_ratio = np.log(obs / unit)
    pred = np.empty(len(puntos))
    k_pliegue: dict[str, float] = {}
    for t in _tamanos(puntos):
        fuera = nombres == t
        k = float(np.exp(log_ratio[~fuera].mean()))
        k_pliegue[t] = k
        pred[fuera] = k * unit[fuera]
    return pred, k_pliegue, float(np.exp(log_ratio.mean()))


def modelo_m4_cv(puntos: list[PuntoKing]) -> np.ndarray:
    """Control empírico log Q = log a + b·log W + c·log OSS, fuera de muestra por tamaño."""
    nombres = np.array([p.nombre for p in puntos])
    x = np.column_stack(
        [np.ones(len(puntos)), np.log([p.largo_mm for p in puntos]),
         np.log([p.oss_mm for p in puntos])]
    )  # fmt: skip
    y = np.log([p.q_tph for p in puntos])
    pred = np.empty(len(puntos))
    for t in _tamanos(puntos):
        fuera = nombres == t
        coef, *_ = np.linalg.lstsq(x[~fuera], y[~fuera], rcond=None)
        pred[fuera] = np.exp(x[fuera] @ coef)
    return pred


def resumen_errores(errores: np.ndarray, puntos: list[PuntoKing], banda_pct: float = 30.0):
    """Mediana de |error| (%), fracción dentro de ±banda y peor punto (tamaño, OSS, error)."""
    absoluto = np.abs(errores)
    peor = int(np.argmax(absoluto))
    return {
        "mediana_abs": float(np.median(absoluto)),
        "frac_banda": float(np.mean(absoluto <= banda_pct)),
        "peor": (puntos[peor].nombre, puntos[peor].oss_mm, float(errores[peor])),
    }


def desglose_por_tamano(errores: np.ndarray, puntos: list[PuntoKing]) -> dict[str, tuple]:
    """Por tamaño: (error medio con signo, mediana de |error|, n puntos)."""
    nombres = np.array([p.nombre for p in puntos])
    return {
        t: (
            float(errores[nombres == t].mean()),
            float(np.median(np.abs(errores[nombres == t]))),
            int((nombres == t).sum()),
        )
        for t in _tamanos(puntos)
    }


def razones_n_nc(puntos: list[PuntoKing]) -> dict[str, tuple[float, float]]:
    """N/Nc por tamaño: (mínimo, máximo) sobre los OSS de la tabla."""
    r: dict[str, list[float]] = {}
    for p in puntos:
        j = mandibula_de_punto(p)
        r.setdefault(p.nombre, []).append(j.rpm / j.critical_rpm)
    return {t: (min(v), max(v)) for t, v in r.items()}


def guarda_potencia(
    puntos: list[PuntoKing], wi: float = WI_EJERCICIO_3_1, f80_boca: float = F80_SOBRE_BOCA
) -> np.ndarray:
    """kW de Bond a la capacidad de la tabla / kW del motor (< 1 ⇒ el motor alcanza).
    F80 = f80_boca·G (SUPUESTO) y P80 de la curva de Nordberg."""
    out = []
    for p in puntos:
        f80 = f80_boca * p.boca_mm * MM
        p80 = nordberg_p80_over_oss() * p.oss_mm * MM
        out.append(p.q_tph * bond_energy(wi, f80, p80) / p.kw)
    return np.array(out)


# ---------------------------------------------------------------- B) producto

MAQUINA_PRODUCTO = ("42x48", 152)  # tamaño y OSS (mm) de la Tabla 3.1
R_PRODUCTO = (0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5)
ALIMENTACIONES = tuple((n, f) for n in (0.8, 1.2, 1.6) for f in (3.0, 5.0, 7.0))
ALIMENTACION_AJUSTE = (1.2, 5.0)
CLASES = 80
RAZON_CLASES = 2.0 ** (1.0 / 8.0)
BOCA_MAX_ALIMENTACION = 0.9  # recorte de la alimentación: 0,9·G


def maquina_producto() -> JawCrusher:
    p = next(
        p for p in puntos_king() if (p.nombre, p.oss_mm) == MAQUINA_PRODUCTO
    )  # fmt: skip
    return mandibula_de_punto(p)


def alimentacion_rr(jaw: JawCrusher, n: float, f80_sobre_oss: float) -> Stream:
    """Rosin-Rammler con F80 = f80_sobre_oss·OSS (antes del recorte), truncada en 0,9·G,
    en 80 clases de razón 2^(1/8); 100 t/h."""
    grid = SizeGrid.geometric(BOCA_MAX_ALIMENTACION * jaw.gape_mm * MM, CLASES, RAZON_CLASES)
    x63 = f80_sobre_oss * jaw.oss_mm * MM / np.log(5.0) ** (1.0 / n)
    return Stream(grid, 100.0 * rosin_rammler(grid, x63, n))


def curva_objetivo(jaw: JawCrusher, n: float, f80_sobre_oss: float, r) -> np.ndarray:
    """Curva de Nordberg exacta (no discretizada) en r = x/OSS, sin pasar de la alimentación
    truncada (analítica)."""
    r = np.asarray(r, dtype=float)
    top = BOCA_MAX_ALIMENTACION * jaw.gape_mm * MM
    x63 = f80_sobre_oss * jaw.oss_mm * MM / np.log(5.0) ** (1.0 / n)

    def rr(x):
        return 1.0 - np.exp(-((x / x63) ** n))

    feed = np.minimum(rr(r * jaw.oss_mm * MM) / rr(top), 1.0)
    return np.maximum(nordberg_cumulative(r), feed)


def delta_pp(jaw: JawCrusher, producto: Stream, n: float, f80_sobre_oss: float) -> np.ndarray:
    """Modelo - Nordberg (puntos porcentuales) en R_PRODUCTO."""
    modelo = np.array([pasante_en(producto, r * jaw.oss_mm * MM) for r in R_PRODUCTO])
    return 100.0 * (modelo - curva_objetivo(jaw, n, f80_sobre_oss, R_PRODUCTO))


def deltas_referencia(jaw: JawCrusher) -> dict[tuple[float, float], np.ndarray]:
    """P1: referencia R en las 9 alimentaciones, sin ajuste."""
    out = {}
    for n, f in ALIMENTACIONES:
        feed = alimentacion_rr(jaw, n, f)
        prod = referencia_producto(feed, jaw.css_eff_mm, jaw.oss_mm)
        out[(n, f)] = delta_pp(jaw, prod, n, f)
    return out


def _con_parametros(jaw: JawCrusher, theta) -> JawCrusher:
    a1, brecha, expo = theta
    return jaw.with_(alpha1=float(a1), alpha2=float(a1 + brecha), exponent=float(expo))


def ajustar_whiten(jaw: JawCrusher) -> tuple[JawCrusher, float]:
    """P2: ajusta α1, α2 y el exponente solo con la alimentación (n, F80/OSS) de
    ALIMENTACION_AJUSTE. Devuelve (máquina ajustada, RMS en pp de ese ajuste)."""
    n, f = ALIMENTACION_AJUSTE
    feed = alimentacion_rr(jaw, n, f)

    def residuo(theta):
        return delta_pp(jaw, _con_parametros(jaw, theta)(feed), n, f)

    mejor = None
    for inicio in ((0.65, 1.0, 1.0), (0.3, 0.5, 2.0), (0.8, 2.0, 0.5), (0.5, 1.5, 3.0)):
        sol = least_squares(
            residuo, inicio, bounds=([0.05, 0.01, 0.1], [1.5, 4.0, 10.0]), x_scale=[0.5, 1.0, 1.0]
        )
        if mejor is None or sol.cost < mejor.cost:
            mejor = sol
    assert mejor is not None
    rms = float(np.sqrt(np.mean(mejor.fun**2)))
    return _con_parametros(jaw, mejor.x), rms


def deltas_whiten(ajustada: JawCrusher) -> dict[tuple[float, float], np.ndarray]:
    out = {}
    for n, f in ALIMENTACIONES:
        feed = alimentacion_rr(ajustada, n, f)
        out[(n, f)] = delta_pp(ajustada, ajustada(feed), n, f)
    return out


def max_abs_por_alimentacion(deltas: dict) -> dict[tuple[float, float], float]:
    return {k: float(np.max(np.abs(v))) for k, v in deltas.items()}
