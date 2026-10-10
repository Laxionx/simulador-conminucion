"""Convenciones de entrada de MODSIM 3.6, leídas de su código (GPL v3; solo leído, no copiado).

- La lista de tamaños es una serie √2 que baja desde el «tamaño mayor»; cada tamaño es el límite
  INFERIOR de su clase, así que la clase 1 queda sobre el tamaño mayor.
- La alimentación se reparte en esas clases interpolando el % pasante de los datos en el punto
  medio geométrico de cada par de tamaños (SYSDATA.FRM). La interpolación es localmente
  Rosin-Rammler entre tamices vecinos, y bajo el último tamiz es una ley de potencia
  (FRPASS en SYSDAT.BAS).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from .sizes import SQRT2, SizeGrid
from .stream import Stream

ALMOST_ONE = 0.999999
ALMOST_ZERO = 1e-6


def lista_modsim(mayor_um: float, n: int) -> tuple[float, ...]:
    """Los n tamaños de MODSIM (límites inferiores de cada clase), en µm."""
    return tuple(mayor_um / SQRT2**k for k in range(n))


def grilla_modsim(mayor_um: float, n: int) -> SizeGrid:
    """Grilla equivalente: tamices superiores de cada clase; la última clase es el fondo."""
    lista = lista_modsim(mayor_um, n)
    return SizeGrid(np.asarray((mayor_um * SQRT2,) + lista[:-1]))


def _algr(fraction: float) -> float:
    return -math.log(1.0 - fraction)


def pasante_frpass(tamices_um: Sequence[float], pasante_pct: Sequence[float], x: float) -> float:
    """% pasante en x como lo interpola MODSIM (FRPASS). Tamices en orden decreciente."""
    if x <= 0:
        return 0.0
    size = list(tamices_um)
    cum = [p / 100.0 for p in pasante_pct]
    last = len(size) - 1  # índice del tamiz más fino
    i = 0
    if size[0] > x:
        for i in range(last):
            if size[i] <= x and cum[i] >= 1.0:
                return 100.0
            if cum[i] < 1.0 and (size[i] > x >= size[i + 1] or size[i] <= x):
                break
        else:
            i = last
    if i == last:  # bajo el último tamiz: ley de potencia con los dos últimos
        if cum[last] <= ALMOST_ZERO:
            return 0.0
        alpha = math.log(cum[last - 1] / cum[last]) / math.log(size[last - 1] / size[last])
        return 100.0 * cum[last] * (x / size[last]) ** alpha
    if cum[i] > ALMOST_ONE and cum[i + 1] > ALMOST_ONE:
        return 100.0
    if cum[i] <= ALMOST_ZERO:
        return 0.0
    if cum[i] >= ALMOST_ONE:
        i += 1
    if cum[i + 1] <= ALMOST_ZERO:
        i -= 1
    xi = math.log(x / size[i + 1]) / math.log(size[i] / size[i + 1])
    eta = (_algr(cum[i]) / _algr(cum[i + 1])) ** xi
    return 100.0 * (1.0 - (1.0 - cum[i + 1]) ** eta)


def alimentacion_modsim(
    mayor_um: float,
    n: int,
    tamices_um: Sequence[float],
    pasante_pct: Sequence[float],
    tph: float,
    water: float = 0.0,
    rho_s: float = 2.7,
) -> Stream:
    """Corriente de alimentación repartida en las clases de MODSIM como lo hace su interfaz."""
    lista = lista_modsim(mayor_um, n)
    rotulos = [math.sqrt(lista[j] * lista[j + 1]) for j in range(n - 1)]
    passing = [100.0] + [pasante_frpass(tamices_um, pasante_pct, r) for r in rotulos] + [0.0]
    fractions = -np.diff(passing)
    return Stream.from_fractions(grilla_modsim(mayor_um, n), fractions, tph, water, rho_s)
