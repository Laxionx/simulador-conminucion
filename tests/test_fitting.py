import numpy as np
import pytest

from conminucion.circuits import simulate
from conminucion.classifier import EfficiencyCurve
from conminucion.fitting import FitResult, fit_cyclone_partition, fit_mill_knots
from conminucion.fracture import Fracture
from conminucion.mill import BallMill, KnotSelection
from conminucion.reconcile import reconcile_node
from conminucion.sizes import rosin_rammler
from conminucion.synthetic import (
    synthetic_cyclone_survey,
    synthetic_mill_survey,
    synthetic_partition_curve,
)

TRUE_CYC = (100.0, 3.0, 0.2)
KNOTS = (4750.0, 1187.0, 297.0, 74.0)
TRUE_RD = (0.9, 1.6, 1.0, 0.35)


def test_reconciliation_closes_balance_and_recovers_r(cfg):
    res = simulate("cerrado_directo", cfg)
    s = res.streams
    sv = synthetic_cyclone_survey(s["alim_ciclon"], cfg.classifier, seed=3)
    rc = reconcile_node(sv.feed, sv.underflow, sv.overflow)
    # cierre exacto del balance por clase tras el ajuste
    np.testing.assert_allclose(
        rc.feed, rc.r_underflow * rc.underflow + (1 - rc.r_underflow) * rc.overflow, atol=1e-10
    )
    for x in (rc.feed, rc.underflow, rc.overflow):
        assert x.sum() == pytest.approx(1.0, abs=1e-9)
    assert abs(rc.r_underflow - sv.true_r) < 0.03
    assert rc.circulating_load == pytest.approx(res.circulating_load, rel=0.25)
    assert rc.chi2 >= 0
    assert np.nanmax(rc.partition()) < 1.5
    with pytest.raises(ValueError):
        reconcile_node(sv.feed, sv.underflow[:-1], sv.overflow)


def test_reconciliation_noise_free_is_exact(cfg):
    s = simulate("cerrado_directo", cfg).streams
    rc = reconcile_node(
        s["alim_ciclon"].fractions, s["underflow"].fractions, s["overflow"].fractions
    )
    true_r = s["underflow"].total_solids / s["alim_ciclon"].total_solids
    assert rc.r_underflow == pytest.approx(true_r, abs=1e-6)
    assert rc.chi2 < 1e-12


def test_cyclone_fit_recovers_params_within_ci(grid):
    curve = EfficiencyCurve(*TRUE_CYC)
    x, y = synthetic_partition_curve(grid, curve, sigma=0.02, seed=11)
    fit = fit_cyclone_partition(x, y)
    assert isinstance(fit, FitResult) and fit.dof == grid.n - 3
    assert all(fit.contains(TRUE_CYC))
    assert fit.rmse < 0.05
    assert set(fit.as_dict()) == {"d50c", "alpha", "Rf"}


def test_cyclone_fit_coverage_monte_carlo(grid):
    curve = EfficiencyCurve(*TRUE_CYC)
    hits = np.zeros(3)
    n = 100
    for seed in range(n):
        x, y = synthetic_partition_curve(grid, curve, sigma=0.02, seed=seed)
        hits += fit_cyclone_partition(x, y).contains(TRUE_CYC)
    assert np.all(hits / n >= 0.85)  # cobertura nominal 95 %


def test_cyclone_fit_with_sigma_and_nans(grid):
    curve = EfficiencyCurve(*TRUE_CYC)
    x, y = synthetic_partition_curve(grid, curve, sigma=0.01, seed=5)
    y[3] = np.nan
    fit = fit_cyclone_partition(x, y, sigma=np.full(grid.n, 0.01))
    assert all(fit.contains(TRUE_CYC))
    with pytest.raises(ValueError, match="Faltan datos"):
        fit_cyclone_partition(x[:3], y[:3])


def test_mill_fit_recovers_knots_within_ci(grid):
    mill = BallMill(KnotSelection(KNOTS, TRUE_RD), Fracture())
    f = rosin_rammler(grid, 3000.0, 1.0)
    fm, pm = synthetic_mill_survey(grid, f, mill, seed=2)
    fit = fit_mill_knots(grid, fm, pm, KNOTS)
    assert all(fit.contains(TRUE_RD))
    assert fit.rmse < 0.01 and len(fit.names) == 4


def test_mill_fit_coverage_monte_carlo(grid):
    mill = BallMill(KnotSelection(KNOTS, TRUE_RD))
    f = rosin_rammler(grid, 3000.0, 1.0)
    hits = np.zeros(4)
    n = 60
    for seed in range(n):
        fm, pm = synthetic_mill_survey(grid, f, mill, seed=seed)
        hits += fit_mill_knots(grid, fm, pm, KNOTS).contains(TRUE_RD)
    assert np.all(hits / n >= 0.80)


def test_validation_doc_generation(tmp_path, monkeypatch, capsys):
    from conminucion import validacion

    monkeypatch.setattr(validacion, "DOC_PATH", tmp_path / "caso.md")
    assert validacion.main() == 0
    text = (tmp_path / "caso.md").read_text(encoding="utf-8")
    assert "MODSIM" in text and "Carga circulante" in text
    assert "P80 producto" in capsys.readouterr().out
