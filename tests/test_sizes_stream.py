import numpy as np
import pytest

from conminucion.bond import bond_energy
from conminucion.sizes import (
    SizeGrid,
    cumulative_passing,
    gaudin_schuhmann,
    rosin_rammler,
    size_at_passing,
)
from conminucion.stream import Stream


def test_grid_geometric_and_sizes(grid):
    assert grid.n == 17
    assert grid.sieves[0] / grid.sieves[1] == pytest.approx(np.sqrt(2))
    assert grid.sizes[0] == pytest.approx(np.sqrt(grid.sieves[0] * grid.sieves[1]))
    assert grid.sizes[-1] == pytest.approx(grid.sieves[-1] / np.sqrt(2))


@pytest.mark.parametrize("bad", [[3, 2], [3, 4, 2], [3, 2, 0], [[3, 2, 1]]])
def test_grid_invalid(bad):
    with pytest.raises(ValueError):
        SizeGrid(np.array(bad, dtype=float))


def test_generators_sum_one_and_values(grid):
    rr = rosin_rammler(grid, 3000.0, 1.0)
    assert rr.sum() == pytest.approx(1.0)
    assert np.all(rr >= 0)
    gs = gaudin_schuhmann(grid, 5000.0, 0.8)
    assert gs.sum() == pytest.approx(1.0)
    # Gaudin-Schuhmann truncada a 1 si el tamiz supera k
    gs2 = gaudin_schuhmann(grid, 1000.0, 0.8)
    assert gs2[0] == pytest.approx(0.0)
    for bad in (lambda: rosin_rammler(grid, -1, 1), lambda: gaudin_schuhmann(grid, 1, 0)):
        with pytest.raises(ValueError):
            bad()


def test_cumulative_and_p80_loglinear(grid):
    mass = np.zeros(grid.n)
    mass[4], mass[5] = 0.5, 0.5  # mitad en la clase 5, mitad en la 6
    cum = cumulative_passing(mass)
    assert cum[0] == pytest.approx(1.0) and cum[-1] == pytest.approx(0.0)
    # Pasante en s_5 = 1, en s_6 = 0.5, en s_7 = 0 -> P80 entre s_5 y s_6 (log-lineal)
    s5, s6 = grid.sieves[4], grid.sieves[5]
    expected = np.exp(np.log(s6) + (0.8 - 0.5) / (1 - 0.5) * (np.log(s5) - np.log(s6)))
    assert size_at_passing(grid, mass, 0.8) == pytest.approx(expected)
    assert np.isnan(size_at_passing(grid, np.zeros(grid.n), 0.8))
    with pytest.raises(ValueError):
        size_at_passing(grid, mass, 1.0)


def test_p80_inside_pan_and_flat_segments(grid):
    mass = np.zeros(grid.n)
    mass[-1] = 1.0  # todo en el fondo: P80 bajo el último tamiz
    assert 0 < size_at_passing(grid, mass, 0.8) < grid.sieves[-1]
    mass = np.zeros(grid.n)
    mass[0], mass[-1] = 0.5, 0.5  # tramo plano en el pasante
    assert np.isfinite(size_at_passing(grid, mass, 0.5))


def test_stream_basics(grid):
    s = Stream.from_fractions(grid, rosin_rammler(grid, 3000, 1), 100.0, water=50.0, rho_s=3.0)
    assert s.total_solids == pytest.approx(100.0)
    assert s.pct_solids == pytest.approx(100 * 100 / 150)
    assert s.volume_flow == pytest.approx(100 / 3 + 50)
    assert s.fractions.sum() == pytest.approx(1.0)
    assert s.f80 == s.p80 and s.cumulative_passing[0] == pytest.approx(1.0)
    assert s.size_at(0.5) < s.p80
    assert s.total_mass == pytest.approx(150.0)
    assert s.scaled(2).total_solids == pytest.approx(200.0)
    assert s.with_water(10).water == 10
    e = Stream.empty(grid)
    assert e.pct_solids == 0 and e.fractions.sum() == 0


def test_stream_mix_and_validation(grid):
    a = Stream.from_fractions(grid, rosin_rammler(grid, 3000, 1), 60.0, 10.0, 2.7)
    b = Stream.from_fractions(grid, rosin_rammler(grid, 500, 1), 40.0, 5.0, 4.0)
    m = Stream.mix([a, b])
    assert m.total_solids == pytest.approx(100.0) and m.water == pytest.approx(15.0)
    assert m.rho_s == pytest.approx(100 / (60 / 2.7 + 40 / 4.0))
    assert Stream.mix([Stream.empty(grid)]).rho_s == 2.7
    with pytest.raises(ValueError):
        Stream(grid, -np.ones(grid.n))
    with pytest.raises(ValueError):
        Stream(grid, np.ones(3))
    with pytest.raises(ValueError):
        Stream(grid, np.ones(grid.n), rho_s=0)


def test_bond_reference_value():
    assert bond_energy(15.0, 10000.0, 150.0) == pytest.approx(10.747, abs=5e-4)
    with pytest.raises(ValueError):
        bond_energy(0, 1, 1)
