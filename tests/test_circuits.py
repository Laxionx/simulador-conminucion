import numpy as np
import pytest

from conminucion.circuits import FRESH, KINDS, CircuitConfig, build_flowsheet, simulate
from conminucion.classifier import EfficiencyCurve
from conminucion.flowsheet import ConvergenceError, Flowsheet, Unit
from conminucion.mill import BallMill
from conminucion.units import ClassifierOp, MillOp, SumpOp

TIGHT = {"tol": 1e-14}


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("wegstein", [False, True])
def test_mass_conservation_every_circuit(cfg, kind, wegstein):
    res = simulate(kind, cfg, wegstein=wegstein, **TIGHT)
    assert abs(res.balance["error_solidos"]) < 1e-10
    assert res.balance["agua_agregada"] >= -1e-10
    s = res.streams
    if kind != "abierto":
        # balance por clase en el ciclón (conservación en la unidad)
        np.testing.assert_allclose(
            s["alim_ciclon"].solids, s["underflow"].solids + s["overflow"].solids, atol=1e-10
        )
        assert s["alim_ciclon"].water == pytest.approx(s["underflow"].water + s["overflow"].water)
        assert s["alim_ciclon"].pct_solids == pytest.approx(cfg.cyclone_feed_pct_solids)
        assert res.circulating_load == pytest.approx(
            s["underflow"].total_solids / s[FRESH].total_solids
        )


def test_wegstein_same_answer_and_faster(cfg):
    a = simulate("cerrado_directo", cfg, wegstein=False, **TIGHT)
    b = simulate("cerrado_directo", cfg, wegstein=True, **TIGHT)
    assert b.circulating_load == pytest.approx(a.circulating_load, rel=1e-9)
    assert b.streams["overflow"].p80 == pytest.approx(a.streams["overflow"].p80, rel=1e-9)
    assert b.solution.iterations < a.solution.iterations
    for k in a.streams:
        np.testing.assert_allclose(a.streams[k].solids, b.streams[k].solids, rtol=1e-8, atol=1e-9)


def test_open_circuit_reports(cfg):
    res = simulate("abierto", cfg)
    assert res.circulating_load is None and res.solution.iterations == 1
    t = res.table()
    assert list(t.columns) == ["corriente", "solidos_t_h", "agua_t_h", "pct_solidos", "P80_um"]
    assert res.bond_kwh_t > 0


def test_closed_circuit_finer_than_open(cfg):
    op, cl = simulate("abierto", cfg), simulate("cerrado_directo", cfg)
    assert cl.streams["overflow"].p80 < op.streams["producto"].p80
    assert cl.circulating_load > 0


def test_passing_table(cfg):
    res = simulate("cerrado_inverso", cfg)
    pt = res.passing_table()
    assert pt.shape[0] == cfg.fresh.grid.n and pt.iloc[0, 1:].max() == pytest.approx(100.0)


def test_non_convergence_and_errors(cfg):
    fs = build_flowsheet("cerrado_directo", cfg)
    with pytest.raises(ConvergenceError, match="No convergió"):
        fs.solve(max_iter=3)
    with pytest.raises(ValueError, match="Preset"):
        simulate("nada", cfg)
    with pytest.raises(ValueError, match="Ciclo sin corriente de corte"):
        Flowsheet(fs.units, fs.feeds, tears=[])
    with pytest.raises(ValueError, match="ninguna unidad"):
        Flowsheet(fs.units, fs.feeds, tears=["x"])
    with pytest.raises(ValueError, match="inexistentes"):
        Flowsheet([Unit("m", ("zzz",), ("o",), MillOp(BallMill()))], fs.feeds)
    with pytest.raises(ValueError, match="único origen"):
        Flowsheet([Unit("m", (FRESH,), (FRESH,), MillOp(BallMill()))], fs.feeds)


def test_tear_guess_accepted_and_two_tears(cfg):
    fs = build_flowsheet("cerrado_directo", cfg)
    sol = fs.solve(tear_guess={"underflow": cfg.fresh.scaled(3.0)}, tol=1e-12)
    assert sol.converged and sol.residuals[-1] <= 1e-12
    # dos cortes simultáneos (underflow y descarga del molino) dan el mismo estado estacionario
    units = [
        Unit("mezcla", (FRESH, "underflow"), ("alim_molino",), SumpOp()),
        Unit("molino", ("alim_molino",), ("descarga_molino",), MillOp(cfg.mill)),
        Unit("cajon", ("descarga_molino",), ("alim_ciclon",), SumpOp(45.0)),
        Unit("ciclon", ("alim_ciclon",), ("underflow", "overflow"), ClassifierOp(cfg.classifier)),
    ]
    two = Flowsheet(units, {FRESH: cfg.fresh}, tears=["underflow", "descarga_molino"])
    s2 = two.solve(tol=1e-12).streams
    ref = fs.solve(tol=1e-12).streams
    assert s2["overflow"].p80 == pytest.approx(ref["overflow"].p80, rel=1e-7)


def test_config_with_other_cyclone(cfg):
    other = CircuitConfig(cfg.fresh, cfg.mill, EfficiencyCurve(200.0, 3.0, 0.2), bond_wi=20.0)
    assert simulate("cerrado_directo", other).bond_kwh_t > 0
