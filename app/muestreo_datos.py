"""Datos y cálculo del «Ajuste a datos» con un muestreo REAL de molienda: las columnas de la tabla
(las mismas para pegar, subir un CSV/XLSX y la plantilla), la validación, la reconciliación del
nodo del ciclón, la partición, el ajuste de d50c, α y Rf y los diagnósticos del muestreo.

Con % de sólidos se usa EXACTAMENTE el camino validado (`plantas_reales.evaluar_ciclon`, con Rf =
agua a gruesos por el balance de agua). Sin % de sólidos, Rf se ajusta libre con
`fit_cyclone_partition`. Las σ de la reconciliación son las de `reconcile_node` (5 % relativo, con
un piso de 0,002): son un supuesto declarado y el χ² depende de ellas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from carga import Columna, ErrorCarga
from numpy.typing import NDArray
from scipy import stats

from conminucion.fitting import FitResult, fit_cyclone_partition, fit_mill_knots
from conminucion.fracture import Fracture
from conminucion.plantas_reales import CLASE_MAX_AJUSTE_UM, CicloneSurvey, evaluar_ciclon
from conminucion.reconcile import Reconciliation, reconcile_node
from conminucion.sizes import SizeGrid

REL_SIGMA, ABS_SIGMA = 0.05, 0.002  # los de `reconcile_node` (supuesto declarado)
MIN_MALLAS = 4  # mallas mínimas, y clases mínimas para ajustar (3 parámetros + 1 de holgura)
MIN_ALIMENTACION = (
    0.01  # fracción mínima de la alimentación para calcular la partición de una clase
)
Z_CORTE = 3.0  # criterio estadístico de 3σ
NIVEL_CONFIANZA = 0.95
CORRIENTES = ("alim", "uf", "of")

C_TAMIZ = Columna("tamiz", "Tamiz (µm)", "Sieve (µm)")
C_FLUJOS = (
    Columna("alim", "Alimentación (% pasante)", "Feed (% passing)"),
    Columna("uf", "Underflow (% pasante)", "Underflow (% passing)"),
    Columna("of", "Overflow (% pasante)", "Overflow (% passing)"),
)
C_MOLINO = (
    Columna("molino_alim", "Molino, alimentación (% pasante)", "Mill feed (% passing)", False),
    Columna("molino_desc", "Molino, descarga (% pasante)", "Mill discharge (% passing)", False),
)
C_SOLIDOS = (
    Columna("solidos_alim", "% sólidos alimentación", "Feed solids (%)", False),
    Columna("solidos_uf", "% sólidos underflow", "Underflow solids (%)", False),
    Columna("solidos_of", "% sólidos overflow", "Overflow solids (%)", False),
)
COLUMNAS_TABLA = (C_TAMIZ, *C_FLUJOS, *C_MOLINO)
COLUMNAS_ARCHIVO = (*COLUMNAS_TABLA, *C_SOLIDOS)  # el archivo puede traer también los % sólidos
CLAVES_TABLA = [c.clave for c in COLUMNAS_TABLA]


# ------------------------------------------------------------------ la tabla
def tabla_de_levantamiento(s: CicloneSurvey) -> pd.DataFrame:
    """La tabla editable de un muestreo publicado (sin datos de molino)."""
    return pd.DataFrame({
        "tamiz": np.asarray(s.tamices_um, float), "alim": np.asarray(s.alimentacion, float),
        "uf": np.asarray(s.underflow, float), "of": np.asarray(s.overflow, float),
        "molino_alim": np.nan, "molino_desc": np.nan,
    })  # fmt: skip


def solidos_de_archivo(tabla: pd.DataFrame) -> tuple[float, float, float] | None:
    """Los % de sólidos de un archivo cargado (el primer valor de cada columna), o None si no vienen
    los tres."""
    valores = []
    for c in C_SOLIDOS:
        col = tabla[c.clave].dropna() if c.clave in tabla else pd.Series(dtype=float)
        if col.empty:
            return None
        valores.append(float(col.iloc[0]))
    return valores[0], valores[1], valores[2]


def retenidos(pasante_pct: NDArray) -> NDArray[np.float64]:
    """% pasante acumulado → fracción retenida por clase (la última clase es el fondo)."""
    p = np.asarray(pasante_pct, dtype=float) / 100.0
    return np.append(-np.diff(p), p[-1])


def validar(tabla: pd.DataFrame, solidos: tuple[float, float, float] | None = None) -> pd.DataFrame:
    """La tabla limpia (filas vacías fuera) o `ErrorCarga` con la clave del texto del problema."""
    d = tabla.reindex(columns=CLAVES_TABLA).apply(pd.to_numeric, errors="coerce")
    d = d.replace([np.inf, -np.inf], np.nan).dropna(how="all").reset_index(drop=True)
    n = len(d)
    cuentas = d.notna().sum()
    if n == 0 or cuentas["tamiz"] == 0:
        raise ErrorCarga("mu.err.menos", {"min": MIN_MALLAS})
    flujos = [cuentas[c.clave] for c in (C_TAMIZ, *C_FLUJOS)]
    if len(set(flujos)) != 1 or flujos[0] != n:
        raise ErrorCarga("mu.err.filas", {"tamiz": flujos[0], "alim": flujos[1], "uf": flujos[2],
                                          "of": flujos[3]})  # fmt: skip
    if cuentas["molino_alim"] != cuentas["molino_desc"] or cuentas["molino_alim"] not in (0, n):
        raise ErrorCarga("mu.err.filas_molino", {"n": n, "alim": cuentas["molino_alim"],
                                                 "desc": cuentas["molino_desc"]})  # fmt: skip
    if n < MIN_MALLAS:
        raise ErrorCarga("mu.err.menos", {"min": MIN_MALLAS})
    tam = d["tamiz"].to_numpy()
    if np.any(tam <= 0) or np.any(np.diff(tam) >= 0):
        raise ErrorCarga("mu.err.tamices")
    for c in (*C_FLUJOS, *C_MOLINO):
        if cuentas[c.clave] == 0:
            continue
        p = d[c.clave].to_numpy()
        if np.any((p < 0) | (p > 100)):
            raise ErrorCarga("mu.err.rango", {"col": c})
        sube = np.flatnonzero(np.diff(p) > 0)
        if sube.size:
            raise ErrorCarga("mu.err.monotono", {"col": c, "tamiz": f"{tam[sube[0] + 1]:g}"})
    if solidos is not None and not all(0.0 < s < 100.0 for s in solidos):
        raise ErrorCarga("mu.err.solidos")
    return d


# ------------------------------------------------------------------ el resultado
@dataclass(frozen=True)
class Ajuste:
    """El ajuste estandarizado z = (medido − reconciliado)/σ de una corriente y una clase."""

    corriente: str
    inferior_um: float
    superior_um: float
    z: float


@dataclass(frozen=True)
class Resultado:
    tamices_um: NDArray[np.float64]
    medidas: dict[str, NDArray[np.float64]]  # fracción retenida por clase
    reconciliadas: dict[str, NDArray[np.float64]]
    z: dict[str, NDArray[np.float64]]
    mayor_ajuste: Ajuste
    chi2: float
    grados_libertad: int
    chi2_critico: float
    r: float
    carga_circulante: float
    cierre_antes: float  # máx |f − (R·u + (1−R)·o)| con lo medido (fracción)
    cierre_despues: float
    part_x_um: NDArray[np.float64]  # tamaño medio de cada clase con partición
    part_pct: NDArray[np.float64]  # partición medida, de los datos reconciliados
    usadas: NDArray[np.bool_]  # clases que entran al ajuste
    d50c: float
    alpha: float
    rf: float
    metodo: str  # "rf_fijo" (con % sólidos) o "rf_libre"
    libre: FitResult  # d50c, alpha y Rf libres, con IC
    molino: FitResult | None
    molino_error: str | None

    @property
    def ancho_ic_d50c(self) -> float:
        return float(self.libre.ci_high[0] - self.libre.ci_low[0])

    def limites_clase(self, k: int) -> tuple[float, float]:
        """(inferior, superior) en µm de la clase k; el fondo tiene inferior 0."""
        sup = float(self.tamices_um[k])
        return (float(self.tamices_um[k + 1]) if k + 1 < len(self.tamices_um) else 0.0), sup


def _mayor_ajuste(z: dict[str, NDArray], tam: NDArray) -> Ajuste:
    corriente, k = max(((c, int(np.argmax(np.abs(z[c])))) for c in CORRIENTES),
                       key=lambda ck: abs(z[ck[0]][ck[1]]))  # fmt: skip
    inf = float(tam[k + 1]) if k + 1 < len(tam) else 0.0
    return Ajuste(corriente, inf, float(tam[k]), float(z[corriente][k]))


def _cierre(f: NDArray, u: NDArray, o: NDArray, r: float) -> float:
    return float(np.max(np.abs(f - (r * u + (1.0 - r) * o))))


def _particion(rc: Reconciliation, tam: NDArray) -> tuple[NDArray, NDArray, NDArray, NDArray]:
    """(tamaño medio, partición [0-1], límite superior, tamiz inferior) de las clases con partición
    (como `evaluar_ciclon`: el fondo no tiene tamaño medio)."""
    part = rc.partition(min_feed_fraction=MIN_ALIMENTACION)[:-1]
    ok = np.isfinite(part)
    inf, sup = tam[1:][ok], tam[:-1][ok]
    return np.sqrt(inf * sup), np.clip(part[ok], 0.0, 1.0), sup, inf


def analizar(
    tabla: pd.DataFrame,
    solidos: tuple[float, float, float] | None = None,
    molino: tuple[tuple[float, ...], Fracture, int] | None = None,
) -> Resultado:
    """Reconcilia, ajusta y diagnostica un muestreo. `solidos`: % de sólidos de alimentación,
    underflow y overflow (o None); `molino`: (tamaños de los nudos, fractura, mezcladores) para
    ajustar el molino si la tabla trae sus datos. Lanza `ErrorCarga` si los datos no sirven."""
    d = validar(tabla, solidos)
    tam = d["tamiz"].to_numpy(float)
    medidas = {c.clave: retenidos(d[c.clave].to_numpy(float)) for c in C_FLUJOS}
    rc = reconcile_node(medidas["alim"], medidas["uf"], medidas["of"], REL_SIGMA, ABS_SIGMA)
    rec = {"alim": rc.feed, "uf": rc.underflow, "of": rc.overflow}
    z = {}
    for c in CORRIENTES:
        sigma = np.maximum(REL_SIGMA * np.abs(medidas[c]), ABS_SIGMA)
        z[c] = (medidas[c] - rec[c]) / sigma
    n = len(tam)
    grados = n + 2  # n balances de clase + 3 sumas = n + 3 restricciones, menos R, desconocida
    medio, part, sup, _ = _particion(rc, tam)
    usadas = sup <= CLASE_MAX_AJUSTE_UM
    if int(usadas.sum()) < MIN_MALLAS:
        raise ErrorCarga("mu.err.utiles", {"n": int(usadas.sum()), "min": MIN_MALLAS,
                                           "corte": f"{CLASE_MAX_AJUSTE_UM:g}"})  # fmt: skip
    try:
        libre = fit_cyclone_partition(medio[usadas], part[usadas])
        if solidos is None:
            d50c, alpha, rf = (float(v) for v in libre.values)
            metodo = "rf_libre"
        else:
            enc = CicloneSurvey("datos", tuple(tam), tuple(d["alim"]), tuple(d["uf"]),
                                tuple(d["of"]), solidos, {}, float("nan"), float("nan"),
                                float("nan"))  # fmt: skip
            res = evaluar_ciclon(enc)
            d50c, alpha, rf = res.d50c_um, res.alpha, res.agua_a_gruesos_pct / 100.0
            libre, metodo = res.ajuste_libre, "rf_fijo"
    except (ValueError, np.linalg.LinAlgError) as exc:
        raise ErrorCarga("mu.err.ajuste") from exc
    fit_molino, error_molino = _molino(d, tam, molino)
    return Resultado(
        tam, medidas, rec, z, _mayor_ajuste(z, tam), rc.chi2, grados,
        float(stats.chi2.ppf(NIVEL_CONFIANZA, grados)), rc.r_underflow, rc.circulating_load,
        _cierre(medidas["alim"], medidas["uf"], medidas["of"], rc.r_underflow),
        _cierre(rc.feed, rc.underflow, rc.overflow, rc.r_underflow),
        medio, 100.0 * part, usadas, d50c, alpha, rf, metodo, libre, fit_molino, error_molino,
    )  # fmt: skip


def _molino(d: pd.DataFrame, tam: NDArray, molino) -> tuple[FitResult | None, str | None]:
    """El ajuste de los r/d por nudos si hay datos del molino y su configuración."""
    if molino is None or d["molino_alim"].isna().all():
        return None, None
    nudos, fractura, mezcladores = molino
    try:
        fit = fit_mill_knots(SizeGrid(tam), retenidos(d["molino_alim"].to_numpy(float)),
                             retenidos(d["molino_desc"].to_numpy(float)), nudos, fractura,
                             mezcladores)  # fmt: skip
    except (ValueError, np.linalg.LinAlgError):
        return None, "mu.err.molino"
    return fit, None
