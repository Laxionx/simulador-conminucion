"""Chancadora de cono (Whiten, en la forma de King 2001) contra los reportes de MODSIM 3.6.

Fuente: los ejercicios 3-4 (cono estándar, CRSH) y 3-5 (cabeza corta, SHHD) del curso que trae
MODSIM 3.6.24 Academic (DOCS/Modsim Training/Module3). Cada página reproduce el reporte de la
unidad: alimentación, producto, F80, P80 y potencia. Tolerancias fijadas ANTES de correr:

- Producto, convención de MODSIM, las 24 filas del % pasante: ±0,1 puntos. La alimentación se
  imprime con 2 decimales y MODSIM calcula en precisión simple.
- F80 y P80 interpolados como MODSIM sobre las filas impresas: ±0,5 %.
- Potencia de Bond con esos F80 y P80 (Wi de impacto 12, t/h del reporte): ±1 %.
- Conservación de la masa: 1e-12 relativo, en ambas convenciones.
- Convención literal de las notas de King (c y madre en el tamaño medio, fractura en los
  límites): sin tolerancia; su diferencia con MODSIM se informa en docs/chancado.md.
"""

from __future__ import annotations

import numpy as np
import pytest

from conminucion.bond import bond_energy
from conminucion.chancadora import ConeCrusher
from conminucion.plantas_reales import pasante_estilo_modsim, tamano_estilo_modsim
from conminucion.sizes import SQRT2, SizeGrid
from conminucion.stream import Stream

# Ejercicio 3-3: tamaño mayor 1,2 m y 25 clases en serie √2. Cada tamaño es el límite INFERIOR
# de su clase (convención de MODSIM, como en Bougainville). En µm.
LISTA_UM = tuple(1.2e6 / SQRT2**k for k in range(25))

# % pasante impreso, 24 filas (la 25.ª, el fondo, es 0)
CRSH_ALIM = (100.00, 100.00, 100.00, 99.86, 97.66, 87.49, 66.10, 38.64, 17.90, 5.13, 4.02, 3.12,
             2.39, 1.82, 1.38, 1.04, .78, .59, .44, .33, .25, .18, .14, .10)  # fmt: skip
CRSH_PROD = (100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 92.03,
             64.67, 45.30, 35.18, 28.82, 23.97, 20.01, 16.73, 13.99, 11.71, 9.81, 8.22, 6.89,
             5.77, 4.84)  # fmt: skip
SHHD_ALIM = (100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 95.26,
             73.86, 56.55, 30.43, 7.65, 5.33, 3.88, 2.98, 2.36, 1.91, 1.56, 1.28, 1.05, .87,
             .72)  # fmt: skip
SHHD_PROD = (100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00,
             100.00, 98.47, 81.90, 50.63, 32.41, 21.98, 16.19, 12.58, 10.10, 8.26, 6.82, 5.66,
             4.71, 3.92)  # fmt: skip

CASOS = {
    # nombre: (chancadora, alimentación, producto, t/h, F80 mm, P80 mm, kW)
    "CRSH": (ConeCrusher.standard(css_mm=35.0), CRSH_ALIM, CRSH_PROD, 819.3, 155.74, 37.39, 259.0),
    "SHHD": (ConeCrusher.short_head(css_mm=13.0), SHHD_ALIM, SHHD_PROD, 1429.0, 34.04, 15.39,
             453.0),
}  # fmt: skip


def _grid() -> SizeGrid:
    return SizeGrid(np.asarray((LISTA_UM[0] * SQRT2,) + LISTA_UM[:-1]))


def _feed(passing: tuple[float, ...], tph: float) -> Stream:
    p = np.array((100.0,) + passing + (0.0,))
    return Stream.from_fractions(_grid(), p[:-1] - p[1:], tph)


@pytest.mark.parametrize("name", list(CASOS))
def test_producto_igual_al_de_modsim(name):
    crusher, feed, product, tph, *_ = CASOS[name]
    ours = pasante_estilo_modsim(crusher(_feed(feed, tph)))
    np.testing.assert_allclose(ours, product, atol=0.1)


@pytest.mark.parametrize("name", list(CASOS))
def test_f80_p80_y_potencia_de_bond(name):
    crusher, feed, product, tph, f80, p80, kw = CASOS[name]
    stream = _feed(feed, tph)
    ours_f80 = tamano_estilo_modsim(stream, 0.8, LISTA_UM) / 1000.0
    ours_p80 = tamano_estilo_modsim(crusher(stream), 0.8, LISTA_UM) / 1000.0
    assert ours_f80 == pytest.approx(f80, rel=0.005)
    assert ours_p80 == pytest.approx(p80, rel=0.005)
    power = bond_energy(12.0, ours_f80 * 1000.0, ours_p80 * 1000.0) * tph
    assert power == pytest.approx(kw, rel=0.01)


@pytest.mark.parametrize("convention", ["modsim", "literal"])
@pytest.mark.parametrize("name", list(CASOS))
def test_conserva_la_masa(name, convention):
    crusher, feed, _, tph, *_ = CASOS[name]
    out = crusher.with_convention(convention)(_feed(feed, tph))
    assert out.total_solids == pytest.approx(tph, rel=1e-12)
    assert np.all(out.solids >= 0.0)


def test_clasificacion_interna():
    crusher = ConeCrusher.short_head(css_mm=13.0)
    d1, d2 = 0.653 * 13_000.0, 2.0 * 13_000.0 + 4_826.0
    c = crusher.classification(np.array([d1 * 0.99, d1, (d1 + d2) / 2, d2, d2 * 1.01]))
    np.testing.assert_allclose(c, [0.0, 0.0, 0.75, 1.0, 1.0])


def test_cerrar_la_abertura_afina_el_producto():
    feed = _feed(CRSH_ALIM, 819.3)
    fine = tamano_estilo_modsim(ConeCrusher.standard(css_mm=25.0)(feed), 0.8, LISTA_UM)
    coarse = tamano_estilo_modsim(ConeCrusher.standard(css_mm=45.0)(feed), 0.8, LISTA_UM)
    assert fine < coarse


def test_errores():
    with pytest.raises(ValueError):
        ConeCrusher(css_mm=0.0)
    with pytest.raises(ValueError):
        ConeCrusher(css_mm=10.0, fines=1.5)
    with pytest.raises(ValueError):
        ConeCrusher(css_mm=10.0, alpha1=2.0, alpha2=1.0)
    with pytest.raises(ValueError):
        ConeCrusher(css_mm=10.0, convention="otra")


def test_circuito_cerrado_con_harnero():
    from conminucion.classifier import EfficiencyCurve
    from conminucion.flowsheet import Flowsheet, Unit
    from conminucion.units import ClassifierOp, CrusherOp, SumpOp

    feed = _feed(SHHD_ALIM, 1000.0)
    screen = EfficiencyCurve(d50c=13_000.0, alpha=4.0, rf=0.0)
    sheet = Flowsheet(
        [
            Unit("cajón", ("alimentación", "chancado"), ("al_harnero",), SumpOp()),
            Unit("harnero", ("al_harnero",), ("sobretamaño", "producto"), ClassifierOp(screen)),
            Unit("chancadora", ("sobretamaño",), ("chancado",),
                 CrusherOp(ConeCrusher.short_head(css_mm=13.0))),
        ],
        {"alimentación": feed},
        tears=("chancado",),
    )  # fmt: skip
    solution = sheet.solve(wegstein=True, tol=1e-10)
    assert solution.converged
    product = solution.streams["producto"]
    assert product.total_solids == pytest.approx(1000.0, rel=1e-8)
    p80 = tamano_estilo_modsim(product, 0.8, LISTA_UM)
    assert p80 < tamano_estilo_modsim(feed, 0.8, LISTA_UM)
