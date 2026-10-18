"""Ensayo de Bond del molino de bolas (ciclo cerrado, 250 % de carga circulante).

Tres partes independientes:

1. **Contabilidad del procedimiento** de GMG (2021, «Guideline: Determining the Bond Efficiency of
   Industrial Grinding Circuits», sección 5.3): carga de 700 cm³ compactados, IPP = masa de la carga
   / 3,5, revoluciones del ciclo siguiente = (IPP - finos que trae la alimentación nueva) / Gbp del
   ciclo anterior, y el índice de trabajo con la ecuación 13 de la guía.
2. **Molienda por lotes** de primer orden (Austin, Klimpel y Luckie, 1984):
   dw/dt = (B - I) S w, resuelta con la exponencial de matriz.
3. **Simulación del ensayo ciclo a ciclo** con ese modelo y el tamizado ideal en el tamiz de cierre.

Lo que se fija y su origen: molino de 305 x 305 mm a 70 rpm (GMG 2021); masas al 0,1 g (resolución
de la balanza, supuesto); los parámetros μ, Λ y de fractura son los valores por defecto del repo
(`AustinSelection`, `Fracture`), no medidos para esta mena.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import expm
from scipy.optimize import brentq, least_squares

from .fracture import Fracture
from .mill import AustinSelection
from .sizes import SizeGrid, rosin_rammler, size_at_passing

MOLINO_RPM = 70.0  # GMG 2021: molino de 305 x 305 mm
MOLINO_DIAMETRO_M = 0.305
CARGA_CIRCULANTE = 2.5  # 250 %: IPP = carga / (1 + 2,5)
MIN_CICLOS = 5  # GMG, paso 14: «al menos cinco ciclos»
FACTOR_WI = 1.1023 * 44.5  # GMG ec. 13: t cortas/t y coeficiente empírico de Bond
EXP_P1, EXP_GBP = 0.23, 0.82
RESOLUCION_G = 0.1  # supuesto: la balanza pesa al 0,1 g
CICLOS_FINALES = 3  # el Gbp final es la media de los últimos tres ciclos


def indice_trabajo(p1_um: float, gbp: float, p80_um: float, f80_um: float) -> float:
    """Wi de Bond (kWh/t, métrico), GMG ec. 13:
    1,1023 x 44,5 / (P1^0,23 Gbp^0,82 (10/√P80 - 10/√F80))."""
    if min(p1_um, gbp, p80_um, f80_um) <= 0:
        raise ValueError("P1, Gbp, P80 y F80 deben ser positivos")
    if p80_um >= f80_um:
        raise ValueError("El P80 del producto debe ser menor que el F80 de la alimentación")
    gap = 10.0 / np.sqrt(p80_um) - 10.0 / np.sqrt(f80_um)
    return float(FACTOR_WI / (p1_um**EXP_P1 * gbp**EXP_GBP * gap))


def _redondear(x: float, paso: float = RESOLUCION_G) -> float:
    return float(np.round(x / paso) * paso)


# ------------------------------------------------------------------ 1. contabilidad del ensayo
@dataclass(frozen=True)
class CicloBond:
    ciclo: int
    alimentacion_nueva_g: float
    revoluciones: int
    finos_total_g: float
    finos_de_alimentacion_g: float
    finos_nuevos_g: float
    gbp: float
    carga_circulante_pct: float
    invierte: bool  # el Gbp cambió de dirección respecto del ciclo anterior


@dataclass(frozen=True)
class ResultadoBond:
    ipp_g: float
    ciclos: tuple[CicloBond, ...]
    gbp_final: float
    termina_en: int | None  # primer ciclo >= 5 en que el Gbp invirtió su dirección
    wi: float | None

    def columna(self, nombre: str) -> list:
        return [getattr(c, nombre) for c in self.ciclos]


def ipp(carga_g: float) -> float:
    """Producto potencial ideal (g): la carga entre 3,5, para 250 % de carga circulante."""
    if carga_g <= 0:
        raise ValueError("La carga debe ser positiva")
    return carga_g / (1.0 + CARGA_CIRCULANTE)


def siguientes_revoluciones(ipp_g: float, finos_alimentacion_g: float, gbp_previo: float) -> int:
    """Revoluciones del ciclo siguiente (GMG ec. 10), redondeadas al entero como el molino."""
    if gbp_previo <= 0:
        raise ValueError("El Gbp del ciclo anterior debe ser positivo")
    return max(1, int(np.round((ipp_g - finos_alimentacion_g) / gbp_previo)))


def contabilidad(
    carga_g: float,
    finos_carga_g: float,
    finos_ciclos_g: Sequence[float],
    revoluciones_inicial: int,
    tamiz_um: float,
    f80_um: float | None = None,
    p80_um: float | None = None,
) -> ResultadoBond:
    """Procedimiento de GMG con los finos totales medidos de cada ciclo.

    La alimentación nueva de un ciclo pesa lo que los finos del anterior (GMG 5.3.3); la fracción
    de finos de la alimentación es la de la carga inicial (`finos_carga_g / carga_g`).
    Con `f80_um` y `p80_um` calcula también el Wi con el Gbp final.
    """
    finos = [float(x) for x in finos_ciclos_g]
    if not finos:
        raise ValueError("Se necesita al menos un ciclo")
    if carga_g <= 0 or not 0 <= finos_carga_g < carga_g or revoluciones_inicial < 1:
        raise ValueError("Carga positiva, finos de la carga menores que ella y revoluciones >= 1")
    if min(finos) < 0 or max(finos) > carga_g:
        raise ValueError("Los finos de cada ciclo van de 0 a la masa de la carga")
    objetivo, fraccion = ipp(carga_g), finos_carga_g / carga_g
    ciclos: list[CicloBond] = []
    alimentacion, rev = carga_g, int(revoluciones_inicial)
    for k, total in enumerate(finos, start=1):
        de_alimentacion = finos_carga_g if k == 1 else _redondear(fraccion * alimentacion)
        nuevos = _redondear(total - de_alimentacion)
        if nuevos <= 0:
            raise ValueError(f"El ciclo {k} no produjo finos nuevos: revise los datos")
        gbp = nuevos / rev
        previo = ciclos[-1].gbp if ciclos else None
        invierte = bool(
            len(ciclos) >= 2 and (gbp - previo) * (previo - ciclos[-2].gbp) < 0  # type: ignore[operator]
        )
        ciclos.append(
            CicloBond(
                k,
                alimentacion,
                rev,
                total,
                de_alimentacion,
                nuevos,
                gbp,
                100.0 * (carga_g - total) / total if total > 0 else float("nan"),
                invierte,
            )  # fmt: skip
        )
        alimentacion = total  # se repone con tanta alimentación como finos se sacaron
        if k < len(finos):
            rev = siguientes_revoluciones(objetivo, _redondear(fraccion * alimentacion), gbp)
    ultimos = [c.gbp for c in ciclos[-CICLOS_FINALES:]]
    gbp_final = float(np.mean(ultimos))
    termina = next((c.ciclo for c in ciclos if c.invierte and c.ciclo >= MIN_CICLOS), None)
    wi = None
    if f80_um is not None and p80_um is not None:
        wi = indice_trabajo(tamiz_um, gbp_final, p80_um, f80_um)
    return ResultadoBond(objetivo, tuple(ciclos), gbp_final, termina, wi)


# ------------------------------------------------------------------ 2. molienda por lotes
def matriz_generadora(seleccion: NDArray, aparicion: NDArray) -> NDArray:
    """M = (B - I) diag(S) con B[k, j] la fracción de la clase j que aparece en la clase k:
    dw/dt = M w. Cada columna suma cero, así que la masa se conserva."""
    s = np.asarray(seleccion, dtype=float)
    return (np.asarray(aparicion, dtype=float) - np.eye(len(s))) * s[None, :]


def seleccion_lotes(grid: SizeGrid, sel: AustinSelection) -> NDArray:
    """S_i (1/min) de Austin; el fondo no se fractura."""
    s = sel.selection(grid)
    s[-1] = 0.0
    return s


def moler_lote(
    grid: SizeGrid, masa: NDArray, minutos: float, sel: AustinSelection, fractura: Fracture
) -> NDArray:
    """Masa por clase tras `minutos` de molienda por lotes: w(t) = exp(M t) w(0)."""
    if minutos < 0:
        raise ValueError("El tiempo no puede ser negativo")
    m = matriz_generadora(seleccion_lotes(grid, sel), fractura.appearance(grid))
    return expm(m * minutos) @ np.asarray(masa, dtype=float)


# ------------------------------------------------------------------ 3. ensayo simulado
@dataclass(frozen=True)
class Alimentacion:
    """Alimentación del ensayo: Rosin-Rammler que pasa por dos puntos (supuesto declarado:
    la curva completa del artículo es un gráfico). `idx_tamiz`: el tamiz de cierre en la grilla."""

    grid: SizeGrid
    idx_tamiz: int
    fracciones: NDArray
    x63_um: float
    m: float

    @property
    def tamiz_um(self) -> float:
        return float(self.grid.sieves[self.idx_tamiz])

    @property
    def fraccion_bajo_tamiz(self) -> float:
        return float(self.fracciones[self.idx_tamiz :].sum())


def grilla_ensayo(tamiz_um: float, tope_um: float = 3350.0, n_sobre: int = 9, n_bajo: int = 6):
    """Grilla casi √2 desde `tope_um` con el tamiz de cierre exacto en el índice `n_sobre`
    (razón (tope/tamiz)^(1/n_sobre) ≈ 1,4125 para 3.350 -> 150 µm), y `n_bajo` clases más
    finas. Devuelve (grilla, índice del tamiz de cierre)."""
    razon = (tope_um / tamiz_um) ** (1.0 / n_sobre)
    return SizeGrid.geometric(tope_um, n_sobre + 1 + n_bajo, razon), n_sobre


def alimentacion_dos_puntos(
    tamiz_um: float, f80_um: float, fraccion_bajo_tamiz: float, grid: SizeGrid | None = None
) -> Alimentacion:
    """Rosin-Rammler (x63, m) con P(f80) = 0,8 y P(tamiz) = fraccion, ambos sobre la curva
    truncada en el tamiz superior de la grilla, que es como la usa el resto del repo."""
    if not 0 < fraccion_bajo_tamiz < 0.8 or not tamiz_um < f80_um:
        raise ValueError("Se requiere 0 < fracción bajo el tamiz < 0,8 y tamiz < F80")
    grid, idx = (grid, int(np.argmin(np.abs(grid.sieves - tamiz_um)))) if grid else (
        grilla_ensayo(tamiz_um)
    )  # fmt: skip
    top = grid.sieves[0]

    def pasante(x, x63, m):
        return np.expm1(-((x / x63) ** m)) / np.expm1(-((top / x63) ** m))

    def resto(m):
        # con m fijo, x63 sale de P(f80) = 0,8; el residuo es P(tamiz) - fracción
        x63 = brentq(lambda v: pasante(f80_um, v, m) - 0.8, 10.0, 1e7)
        return pasante(tamiz_um, x63, m) - fraccion_bajo_tamiz, x63

    m = brentq(lambda v: resto(v)[0], 0.3, 5.0)
    x63 = resto(m)[1]
    return Alimentacion(grid, idx, rosin_rammler(grid, x63, m), float(x63), float(m))


@dataclass(frozen=True)
class CicloSimulado:
    ciclo: int
    revoluciones: int
    finos_total_g: float
    finos_de_alimentacion_g: float
    finos_nuevos_g: float
    gbp: float
    carga_circulante_pct: float


@dataclass(frozen=True)
class EnsayoSimulado:
    ciclos: tuple[CicloSimulado, ...]
    gbp_final: float
    p80_um: float
    wi: float

    def columna(self, nombre: str) -> list:
        return [getattr(c, nombre) for c in self.ciclos]


def _ciclo(alim: Alimentacion, carga: NDArray, rev: int, sel: AustinSelection, fractura: Fracture):
    """Un ciclo: (finos de la alimentación, finos totales, finos retirados por clase, carga
    siguiente) con tamizado ideal en el tamiz de cierre y reposición con alimentación nueva."""
    idx = alim.idx_tamiz
    de_alim = float(carga[idx:].sum())
    salida = moler_lote(alim.grid, carga, rev / MOLINO_RPM, sel, fractura)
    fino = np.zeros(alim.grid.n)
    fino[idx:] = salida[idx:]
    total = float(fino.sum())
    return de_alim, total, fino, salida - fino + total * alim.fracciones


def simular_ensayo(
    alim: Alimentacion,
    sel: AustinSelection,
    fractura: Fracture,
    carga_g: float,
    n_ciclos: int,
    revoluciones_inicial: int,
    f80_um: float,
    revoluciones_forzadas: dict[int, int] | None = None,
) -> EnsayoSimulado:
    """Ensayo ciclo a ciclo: molienda por lotes, tamizado ideal en el tamiz de cierre, reposición
    con alimentación nueva por el peso de los finos retirados y revoluciones de la regla de GMG."""
    objetivo, forzadas = ipp(carga_g), revoluciones_forzadas or {}
    carga, rev = carga_g * alim.fracciones, int(revoluciones_inicial)
    ciclos: list[CicloSimulado] = []
    productos = []
    for k in range(1, n_ciclos + 1):
        rev = forzadas.get(k, rev)
        de_alim, total, fino, carga = _ciclo(alim, carga, rev, sel, fractura)
        gbp = (total - de_alim) / rev
        ciclos.append(CicloSimulado(k, rev, total, de_alim, total - de_alim, gbp,
                                    100.0 * (carga_g - total) / total))  # fmt: skip
        productos.append(fino)
        rev = siguientes_revoluciones(objetivo, alim.fraccion_bajo_tamiz * total, gbp)
    gbp_final = float(np.mean([c.gbp for c in ciclos[-CICLOS_FINALES:]]))
    p80 = size_at_passing(alim.grid, np.sum(productos[-CICLOS_FINALES:], axis=0), 0.8)
    wi = indice_trabajo(alim.tamiz_um, gbp_final, p80, f80_um)
    return EnsayoSimulado(tuple(ciclos), gbp_final, p80, wi)


def nuevos_primeros_ciclos(alim, sel, fractura, carga_g, revoluciones) -> NDArray:
    """Finos nuevos (g) de los primeros ciclos con las revoluciones dadas."""
    carga, out = carga_g * alim.fracciones, []
    for rev in revoluciones:
        de_alim, total, _, carga = _ciclo(alim, carga, rev, sel, fractura)
        out.append(total - de_alim)
    return np.array(out)


def ajustar_a_alpha(
    alim: Alimentacion,
    fractura: Fracture,
    carga_g: float,
    nuevos_medidos_g: tuple[float, float],
    revoluciones: tuple[int, int],
    base: AustinSelection | None = None,
) -> AustinSelection:
    """Ajusta solo `A` y `α` de Austin a los finos nuevos de los ciclos 1 y 2 (dos datos, dos
    parámetros); μ, Λ y τ quedan como en `base`. Mínimos cuadrados con residuos relativos."""
    base = base or AustinSelection()
    medidos = np.asarray(nuevos_medidos_g, dtype=float)

    def sel_de(p) -> AustinSelection:
        return AustinSelection(float(np.exp(p[0])), float(p[1]), base.mu, base.lam, base.tau)

    def residuos(p):
        return (
            nuevos_primeros_ciclos(alim, sel_de(p), fractura, carga_g, revoluciones) / medidos - 1
        )

    fit = least_squares(residuos, [np.log(base.A), base.alpha],
                        bounds=([np.log(1e-3), 0.05], [np.log(50.0), 4.0]),
                        xtol=1e-14, ftol=1e-14, gtol=1e-14)  # fmt: skip
    return sel_de(fit.x)
