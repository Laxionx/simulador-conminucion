"""Casos de validación con datos PUBLICADOS de plantas reales (no sintéticos).

Cada caso guarda los números tal como salen de la fuente (tabla y página citadas) y una
función que los pasa por el simulador. Las tolerancias viven en `tests/test_plantas_reales.py`
y se fijaron antes de correr; el detalle y los veredictos están en
`docs/VALIDACION_PLANTAS_REALES.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares

from .bond import bond_energy
from .circuits import CircuitConfig, CircuitResult, simulate
from .classifier import SharpnessCurve, corrected_efficiency
from .fitting import FitResult, fit_cyclone_partition
from .fracture import Fracture
from .mill import EnergyBallMill, EnergySelection
from .reconcile import reconcile_node
from .sizes import SQRT2, SizeGrid
from .stream import Stream

# --------------------------------------------------------------------------------------
# C2 · Vazante (Nexa Resources, Brasil): hidrociclones solos, circuito de molienda C.
# Costa, Bergerman y Delboni Jr. (2024), Minerals 14(7), 707. doi:10.3390/min14070707
# Granulometrías balanceadas: Tablas A3 (campaña 1) y A5 (campaña 2), pp. 18-19.
# Partición experimental: Tablas A6 y A7, pp. 19-20. Parámetros: Tabla 7, p. 13.
# --------------------------------------------------------------------------------------

CLASE_MAX_AJUSTE_UM = 350.0  # se ajustan las clases cuyo tamiz superior es <= 350 µm


@dataclass(frozen=True)
class CicloneSurvey:
    nombre: str
    tamices_um: tuple[float, ...]  # decrecientes; la clase k es [tamiz k+1, tamiz k)
    alimentacion: tuple[float, ...]  # % pasante acumulado, balanceado
    underflow: tuple[float, ...]
    overflow: tuple[float, ...]
    solidos_pct: tuple[float, float, float]  # alimentación, underflow, overflow (balanceado)
    particion_publicada: dict[float, float]  # tamiz inferior de la clase (µm) -> % al UF
    alpha: float  # parámetro de Whiten publicado
    d50c_um: float
    agua_a_gruesos_pct: float


VAZANTE_C1 = CicloneSurvey(
    nombre="Vazante, campaña 1 (abril 2022), ciclones solos",
    tamices_um=(12500, 9520, 6300, 3350, 2000, 1180, 298, 210, 149, 105, 74, 53, 37),
    alimentacion=(100, 100, 100, 97.9, 96.2, 93.1, 69.2, 53.9, 39.5, 28.0, 22.0, 17.7, 15.1),
    underflow=(100, 100, 100, 97.3, 95.1, 91.1, 60.5, 42.2, 26.4, 15.2, 10.2, 7.2, 5.6),
    overflow=(100, 100, 100, 100, 100, 100, 98.5, 93.5, 83.8, 71.1, 61.8, 53.3, 47.3),
    solidos_pct=(60.5, 84.1, 31.1),
    particion_publicada={298: 98.6, 210: 92.5, 149: 84.6, 105: 75.1, 74: 64.3, 53: 54.9, 37: 47.0},
    alpha=0.79,
    d50c_um=80.0,
    agua_a_gruesos_pct=22.3,
)

VAZANTE_C2 = CicloneSurvey(
    nombre="Vazante, campaña 2, ciclones solos",
    tamices_um=(
        12500,
        9520,
        6300,
        3350,
        2360,
        1180,
        850,
        600,
        350,
        212,
        150,
        106,
        75,
        53,
        45,
        37,
        20,
    ),
    alimentacion=(
        100,
        100,
        100,
        100,
        100,
        98.9,
        97.9,
        91.6,
        83.4,
        69.7,
        59.4,
        44.3,
        34.2,
        28.2,
        25.3,
        22.6,
        19.6,
    ),
    underflow=(
        100,
        100,
        100,
        100,
        100,
        98.2,
        96.5,
        86.2,
        73.3,
        54.7,
        42.5,
        27.1,
        18.3,
        13.8,
        11.8,
        10.1,
        8.4,
    ),
    overflow=(
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        99.8,
        98.4,
        92.3,
        84.8,
        70.1,
        58.1,
        49.9,
        45.5,
        41.5,
        36.3,
    ),
    solidos_pct=(53.2, 74.4, 37.2),
    particion_publicada={
        600: 98.5,
        350: 93.6,
        212: 82.3,
        150: 70.7,
        106: 61.1,
        75: 52.5,
        53: 45.4,
        45: 40.6,
        37: 38.4,
        20: 33.2,
    },
    alpha=0.71,
    d50c_um=131.0,
    agua_a_gruesos_pct=23.5,
)


@dataclass(frozen=True)
class CicloneResultado:
    theta: float  # fracción de los sólidos de la alimentación que va al underflow
    agua_a_gruesos_pct: float
    inferior_um: NDArray[np.float64]  # tamiz inferior de cada clase con partición
    superior_um: NDArray[np.float64]
    particion_pct: NDArray[np.float64]
    d50c_um: float
    alpha: float
    ajuste_libre: FitResult  # (d50c, alpha, Rf) libres, solo informativo


def _retenidos(acumulado: tuple[float, ...]) -> NDArray[np.float64]:
    """% pasante acumulado -> fracción retenida por clase (la última clase es el fondo)."""
    p = np.asarray(acumulado, dtype=float) / 100.0
    return np.append(-np.diff(p), p[-1])


def agua_a_gruesos(theta: float, solidos_pct: tuple[float, float, float]) -> float:
    """Fracción del agua de la alimentación que sale por el underflow (balance de agua)."""
    agua = [(100.0 - s) / s for s in solidos_pct]  # t de agua por t de sólidos
    return theta * agua[1] / agua[0]


def ajustar_whiten_rf_fijo(
    tamano_um: NDArray, particion: NDArray, rf: float
) -> tuple[float, float]:
    """Método del artículo: corrige por bypass de Kelsall con Rf = agua a gruesos y ajusta
    la curva corregida de Whiten (d50c, alpha) por mínimos cuadrados."""
    corregida = (np.asarray(particion) - rf) / (1.0 - rf)
    x = np.asarray(tamano_um, dtype=float)
    d0 = float(np.exp(np.interp(0.5, np.sort(corregida), np.log(x[np.argsort(corregida)]))))
    sol = least_squares(
        lambda th: corrected_efficiency(x, th[0], th[1]) - corregida,
        x0=[d0, 2.0],
        bounds=([1.0, 0.05], [1e5, 30.0]),
    )
    return float(sol.x[0]), float(sol.x[1])


def evaluar_ciclon(s: CicloneSurvey) -> CicloneResultado:
    rc = reconcile_node(_retenidos(s.alimentacion), _retenidos(s.underflow), _retenidos(s.overflow))
    tamices = np.asarray(s.tamices_um, dtype=float)
    particion = rc.partition(min_feed_fraction=0.01)[:-1]  # el fondo no tiene tamaño medio
    ok = np.isfinite(particion)
    inf, sup = tamices[1:][ok], tamices[:-1][ok]
    e = np.clip(particion[ok], 0.0, 1.0)
    rf = agua_a_gruesos(rc.r_underflow, s.solidos_pct)
    usar = sup <= CLASE_MAX_AJUSTE_UM
    medio = np.sqrt(inf * sup)
    d50c, alpha = ajustar_whiten_rf_fijo(medio[usar], e[usar], rf)
    libre = fit_cyclone_partition(medio[usar], e[usar])
    return CicloneResultado(rc.r_underflow, 100.0 * rf, inf, sup, 100.0 * e, d50c, alpha, libre)


# --------------------------------------------------------------------------------------
# C4 · Constancia (Hudbay, Perú): energía de Bond contra 14 muestreos de molinos de bolas.
# NI 43-101 Technical Report, 29-03-2021, Tabla 13-2 (F80, p. 95 del PDF) y
# Tabla 13-3 (Wi, P80, energía modelo y planta, p. 96 del PDF).
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MuestreoBolas:
    numero: int
    tipo_mineral: str  # Hyp = hipógeno, Sup = supérgeno
    wi_kwh_t: float
    f80_um: float
    p80_um: float
    energia_modelo: float  # kWh/t, columna «modelo» del reporte
    energia_planta: float  # kWh/t, medida
    factor_publicado: float  # planta / modelo


CONSTANCIA = (
    MuestreoBolas(1, "Hyp", 16.8, 1834, 192, 8.1, 7.8, 0.96),
    MuestreoBolas(2, "Hyp", 16.9, 1223, 195, 7.2, 7.0, 0.97),
    MuestreoBolas(3, "Sup", 11.0, 1138, 154, 5.5, 7.2, 1.30),
    MuestreoBolas(4, "Sup", 10.5, 614, 156, 4.1, 7.0, 1.69),
    MuestreoBolas(5, "Hyp", 15.2, 1504, 186, 7.1, 7.8, 1.10),
    MuestreoBolas(6, "Hyp", 16.4, 1068, 188, 6.8, 7.7, 1.12),
    MuestreoBolas(7, "Hyp", 17.4, 1246, 172, 8.2, 7.5, 0.92),
    MuestreoBolas(8, "Hyp", 16.2, 1178, 183, 7.1, 7.0, 0.99),
    MuestreoBolas(9, "Sup", 11.6, 1216, 161, 5.7, 7.1, 1.25),
    MuestreoBolas(10, "Sup", 11.7, 795, 175, 4.6, 6.3, 1.37),
    MuestreoBolas(11, "Hyp", 18.8, 918, 126, 10.4, 10.0, 0.96),
    MuestreoBolas(12, "Hyp", 18.3, 1155, 115, 11.5, 11.2, 0.97),
    MuestreoBolas(13, "Hyp", 15.6, 1198, 137, 8.7, 10.3, 1.18),
    MuestreoBolas(14, "Hyp", 17.8, 1567, 121, 11.5, 10.3, 0.89),
)
CONSTANCIA_FACTOR_PROMEDIO = 1.12  # fila «Average» de la Tabla 13-3


def energia_bond_constancia() -> list[tuple[MuestreoBolas, float]]:
    """(muestreo, energía de Bond del simulador en kWh/t) para cada muestreo."""
    return [(m, bond_energy(m.wi_kwh_t, m.f80_um, m.p80_um)) for m in CONSTANCIA]


# --------------------------------------------------------------------------------------
# C3 · Madneuli (Georgia): circuito 2 de molienda, 84,5 t/h medidas (85,4 tras balancear).
# Ergün, Ekmekçi, Gülsoy y Benzer (2004), Physicochem. Probl. Miner. Process. 38, 231-240.
# Fig. 3, p. 234: t/h de sólidos, % sólidos, P80 (mm) y % -74 µm de cada corriente balanceada.
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Corriente:
    tph: float
    solidos_pct: float
    p80_mm: float
    menos74_pct: float


MADNEULI = {
    "alim_fresca_1": Corriente(40.2, 36.5, 20.0, 7.96),
    "descarga_molino_1": Corriente(69.6, 48.1, 0.727, 29.6),
    "gruesos_espiral_1": Corriente(29.4, 84.9, 1.20, 5.51),
    "finos_espiral_1": Corriente(40.2, 36.5, 0.284, 47.9),
    "alim_fresca_2": Corriente(45.2, 36.5, 19.2, 6.03),
    "descarga_molino_2": Corriente(168.0, 62.1, 1.12, 13.4),
    "gruesos_espiral_2": Corriente(122.0, 83.8, 1.38, 3.66),
    "finos_espiral_2": Corriente(45.3, 36.5, 0.351, 39.6),
    "descarga_molino_sec": Corriente(25.4, 81.9, 0.433, 14.3),
    "alim_ciclon": Corriente(111.0, 41.8, 0.358, 36.8),
    "underflow": Corriente(25.4, 81.9, 0.587, 7.51),
    "overflow": Corriente(85.4, 36.5, 0.280, 45.5),
}

# Nodos del diagrama: entradas -> salidas (los nombres son claves de MADNEULI).
MADNEULI_NODOS = {
    "molino 1 (alim. fresca + gruesos = descarga)": (
        ("alim_fresca_1", "gruesos_espiral_1"),
        ("descarga_molino_1",),
    ),
    "espiral 1": (("descarga_molino_1",), ("gruesos_espiral_1", "finos_espiral_1")),
    "molino 2": (("alim_fresca_2", "gruesos_espiral_2"), ("descarga_molino_2",)),
    "espiral 2": (("descarga_molino_2",), ("gruesos_espiral_2", "finos_espiral_2")),
    "cajón": (("finos_espiral_1", "finos_espiral_2", "descarga_molino_sec"), ("alim_ciclon",)),
    "ciclón": (("alim_ciclon",), ("underflow", "overflow")),
}

# Clasificadores: (alimentación, gruesos, finos, alimentación fresca del circuito)
MADNEULI_CLASIFICADORES = {
    "espiral 1": ("descarga_molino_1", "gruesos_espiral_1", "finos_espiral_1", "alim_fresca_1"),
    "espiral 2": ("descarga_molino_2", "gruesos_espiral_2", "finos_espiral_2", "alim_fresca_2"),
    "ciclón": ("alim_ciclon", "underflow", "overflow", "overflow"),
}


def cierre_nodo(nodo: str, propiedad: str) -> float:
    """(salidas - entradas) / entradas de sólidos o de -74 µm (t/h) en un nodo."""
    entradas, salidas = MADNEULI_NODOS[nodo]

    def flujo(nombre: str) -> float:
        c = MADNEULI[nombre]
        return c.tph if propiedad == "solidos" else c.tph * c.menos74_pct / 100.0

    ent = sum(flujo(n) for n in entradas)
    return (sum(flujo(n) for n in salidas) - ent) / ent


def carga_circulante_por_granulometria(clasificador: str) -> tuple[float, float]:
    """(carga circulante del simulador, publicada). El simulador solo ve el % -74 µm de las
    tres corrientes del clasificador (reconciliación con 2 clases = fórmula de dos productos);
    la publicada sale de los flujos balanceados: gruesos / alimentación fresca."""
    alim, gruesos, finos, fresca = (MADNEULI[n] for n in MADNEULI_CLASIFICADORES[clasificador])

    def clases(c: Corriente) -> NDArray[np.float64]:
        return np.array([1.0 - c.menos74_pct / 100.0, c.menos74_pct / 100.0])

    rc = reconcile_node(clases(alim), clases(gruesos), clases(finos))
    simulada = rc.r_underflow * alim.tph / fresca.tph
    return simulada, gruesos.tph / fresca.tph


# --------------------------------------------------------------------------------------
# C1 · Bougainville: ejemplo de MODSIM 3.6.24 Academic (GPL v3), corrido por el usuario el
# 07-10-2026. Entrada: Bougainville.sid (malla, alimentación) y Bougainville.cur (modelos
# HFSU y CYCA). Referencia: STREAMPROPS.TXT que escribió MODSIM. Parámetros según el manual
# de MODSIM v3.6 (pp. 53-55 y 67-68) y la ayuda de HFSU.
# --------------------------------------------------------------------------------------

BOUGAINVILLE_TAMICES_UM = tuple(20000.0 / SQRT2**k for k in range(25))
BOUGAINVILLE_ALIMENTACION = (  # fracciones por clase de la corriente 1 (Bougainville.sid)
    1.5081e-3,
    1.8537e-2,
    7.5051e-2,
    1.4760e-1,
    1.5248e-1,
    9.5047e-2,
    7.9874e-2,
    5.6921e-2,
    4.8035e-2,
    3.6860e-2,
    3.1975e-2,
    2.6775e-2,
    2.5117e-2,
    2.3780e-2,
    2.0713e-2,
    1.7702e-2,
    1.7178e-2,
    2.4924e-2,
    2.9265e-2,
    2.0694e-2,
    1.4633e-2,
    1.0347e-2,
    7.3164e-3,
    5.1735e-3,
    1.2490e-2,
)
BOUGAINVILLE_ALIM_TPH = 127.8 * 3.6  # MODSIM guarda kg/s
# Salida de MODSIM (STREAMPROPS.TXT): % pasante que MODSIM rotula con el tamaño medio de
# cada clase y que corresponde al límite inferior de la clase (el fondo figura con 0,000).
MODSIM_PRODUCTO_PASANTE = (
    100.000,
    100.000,
    100.000,
    100.000,
    100.000,
    100.000,
    100.000,
    100.000,
    100.000,
    99.998,
    99.921,
    97.729,
    89.930,
    80.028,
    68.956,
    57.790,
    47.363,
    37.531,
    28.669,
    21.902,
    16.766,
    12.868,
    9.900,
    7.632,
)
MODSIM_UNDERFLOW_PASANTE = (
    99.814,
    98.332,
    94.008,
    87.083,
    80.080,
    74.480,
    69.009,
    63.544,
    57.391,
    50.048,
    40.510,
    30.922,
    27.494,
    24.428,
    21.047,
    17.639,
    14.456,
    11.455,
    8.751,
    6.685,
    5.117,
    3.927,
    3.022,
    2.329,
)
MODSIM_ALIM_MOLINO_PASANTE = (
    99.833,
    98.147,
    92.075,
    80.846,
    69.313,
    61.568,
    54.714,
    49.124,
    43.712,
    38.378,
    32.322,
    26.529,
    23.605,
    20.917,
    18.256,
    15.748,
    13.370,
    10.649,
    7.823,
    5.756,
    4.246,
    3.141,
    2.331,
    1.735,
)
MODSIM_DESCARGA_PASANTE = (
    99.916,
    99.249,
    97.302,
    94.184,
    91.030,
    88.509,
    86.046,
    83.585,
    80.814,
    77.507,
    73.170,
    67.648,
    61.817,
    54.992,
    47.384,
    39.711,
    32.546,
    25.790,
    19.700,
    15.050,
    11.521,
    8.842,
    6.803,
    5.244,
)
MODSIM_BOUGAINVILLE = {
    "underflow_tph": 376.92,
    "producto_tph": 460.44,
    "alim_molino_tph": 837.36,
    "agua_cajon_m3h": 222.05,
    "agua_molino_m3h": 123.05,
    "overflow_pct_solidos": 57.16,
    "underflow_pct_solidos": 81.37,
    "p80_um": 185.0,  # MODSIM imprime 3 cifras truncadas: 0.185E-03 m
    "p50_um": 71.9,
    "p20_um": 20.6,
}


def bougainville_config(convencion_modsim: bool = True) -> CircuitConfig:
    """Lectura literal del archivo de MODSIM. Con `convencion_modsim`, el ciclón y la selección
    se evalúan en el tamiz superior de cada clase y el ciclón no corrige por densidad: así lo
    hace MODSIM según su propia partición (ajuste: d50 = 400,08 µm, lambda = 9,839)."""
    grid = SizeGrid(np.asarray(BOUGAINVILLE_TAMICES_UM))
    fresh = Stream.from_fractions(grid, BOUGAINVILLE_ALIMENTACION, BOUGAINVILLE_ALIM_TPH)
    basis = "tamiz_superior" if convencion_modsim else "medio"
    mill = EnergyBallMill(
        EnergySelection(s1e=0.62, zeta1=0.551, zeta2=-0.331, size_basis=basis),
        Fracture(phi=0.79, gamma=0.696, beta=2.17),
        power_kw=5000.0,
        region_fractions=(1.0,),  # regiones 1 y 2 con fracción 0 en el .cur
        discharge_pct_solids=80.0,
    )
    cyclone = SharpnessCurve(
        d50c=400.0,
        sharpness=0.8,
        bypass=0.2,
        model="logistico",
        density_exponent=0.0 if convencion_modsim else 0.5,
        size_basis=basis,
    )
    return CircuitConfig(fresh, mill, cyclone, cyclone_feed_pct_solids=66.0)


def pasante_estilo_modsim(stream: Stream) -> NDArray[np.float64]:
    """% que pasa el límite inferior de cada clase (lo que MODSIM rotula con el tamaño medio)."""
    return 100.0 * stream.cumulative_passing[1:]


def tamano_estilo_modsim(stream: Stream, p: float) -> float:
    """Px como lo calcula MODSIM: interpolación en coordenadas de Rosin-Rammler
    (ln(-ln(1-P)) vs ln x) sobre los pares (tamaño medio, % pasante estilo MODSIM)."""
    medio = stream.grid.sizes[:-1]
    pas = pasante_estilo_modsim(stream) / 100.0
    ok = (pas > 0) & (pas < 1)
    x, y = np.log(medio[ok])[::-1], np.log(-np.log(1.0 - pas[ok]))[::-1]
    return float(np.exp(np.interp(np.log(-np.log(1.0 - p)), y, x)))


def simular_bougainville(convencion_modsim: bool = True) -> CircuitResult:
    return simulate("cerrado_directo", bougainville_config(convencion_modsim), tol=1e-10)
