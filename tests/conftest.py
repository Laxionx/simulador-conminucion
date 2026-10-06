import pytest

from conminucion.circuits import CircuitConfig
from conminucion.classifier import EfficiencyCurve
from conminucion.mill import BallMill
from conminucion.sizes import SizeGrid, rosin_rammler
from conminucion.stream import Stream


@pytest.fixture
def grid():
    return SizeGrid.geometric()


@pytest.fixture
def fresh(grid):
    return Stream.from_fractions(grid, rosin_rammler(grid, 3000.0, 1.0), 100.0)


@pytest.fixture
def cfg(fresh):
    return CircuitConfig(fresh, BallMill(), EfficiencyCurve(100.0, 3.0, 0.2))
