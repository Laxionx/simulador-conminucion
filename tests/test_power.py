"""Potencia de Bond-Rowland. Tolerancias fijadas antes de correr: ±0,5 % contra los ejemplos
resueltos de Gupta y Yan (2016) y entre las tres formas publicadas de la misma ecuación."""

import numpy as np
import pytest

from conminucion.power import (
    ball_charge_t,
    bond_kw_per_t_balls,
    bond_mill_power,
)


def test_ejemplo_1_gupta_yan_kw_por_tonelada_de_bolas():
    # D = 3,35 m, J = 0,40, Cs = 0,75 -> 10,15 kW/t (el ejemplo no aplica el factor de bola)
    assert bond_kw_per_t_balls(3.35, 0.40, 0.75) == pytest.approx(10.15, rel=0.005)


def test_ejemplo_2_gupta_yan_potencia_total():
    # D = 2,1 m, J = 0,45, Cs = 0,70, 16,6 t de bolas -> 127,8 kW
    assert bond_kw_per_t_balls(2.1, 0.45, 0.70) * 16.6 == pytest.approx(127.8, rel=0.005)


@pytest.mark.parametrize(
    ("d", "length", "j", "cs"), [(5.36, 6.25, 0.42, 0.74), (2.1, 3.0, 0.3, 0.7)]
)
def test_tres_formas_publicadas_coinciden(d, length, j, cs):
    speed = cs * (1 - 0.1 / 2 ** (9 - 10 * cs))
    ours = bond_mill_power(d, length, j, cs, media_density=7.8, voidage=0.4)
    # Austin, Klimpel y Luckie (1984): 15,6 D^0,3 (1 - 0,937 J) por tonelada de bolas
    akl = 15.6 * d**0.3 * (1 - 0.937 * j) * speed
    assert ours.kw_per_t_balls == pytest.approx(akl, rel=0.005)
    # Gupta y Yan (2016): P = 7,33 J Cs (1 - 0,937 J) rho_b L D^2,3 (1 - 0,1/2^(9-10Cs))
    gupta = 7.33 * j * speed * (1 - 0.937 * j) * 7.8 * length * d**2.3
    assert ours.kw == pytest.approx(gupta, rel=0.005)


def test_factor_de_bola_tipo_de_molino_y_validaciones():
    base = bond_kw_per_t_balls(5.0, 0.4, 0.75)
    chica = bond_kw_per_t_balls(5.0, 0.4, 0.75, top_ball_mm=50.0)
    assert chica == pytest.approx(base + 1.102 * (50 - 62.5) / 50.8)
    assert bond_kw_per_t_balls(3.0, 0.4, 0.75, top_ball_mm=10.0) == pytest.approx(
        bond_kw_per_t_balls(3.0, 0.4, 0.75)
    )  # bajo 3,3 m no se aplica
    assert bond_kw_per_t_balls(3.0, 0.4, 0.75, mill_type="parrilla_humedo") == pytest.approx(
        1.16 * bond_kw_per_t_balls(3.0, 0.4, 0.75)
    )
    assert ball_charge_t(2.0, 3.0, 0.4) == pytest.approx(0.4 * np.pi * 3.0 * 7.8 * 0.6)
    for bad in ((0, 0.4, 0.7), (3, 1.0, 0.7), (3, 0.4, 1.2)):
        with pytest.raises(ValueError):
            bond_kw_per_t_balls(*bad)
    with pytest.raises(ValueError):
        bond_kw_per_t_balls(3, 0.4, 0.7, mill_type="otro")
    with pytest.raises(ValueError):
        ball_charge_t(3, 0, 0.4)
