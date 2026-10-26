"""Chancador de mandíbula, parrilla, curva de Nordberg, referencia R y diagnóstico."""

import numpy as np
import pytest

from conminucion.datos_mandibula import FUENTES, NORDBERG_R_CORTE
from conminucion.mandibula import (
    Grizzly,
    JawCrusher,
    carrera_amit_mm,
    pasante_en,
    rose_english_tph,
    taggart_tph,
)
from conminucion.mandibula_diagnostico import NIVELES, diagnostico
from conminucion.mandibula_producto import (
    nordberg_cumulative,
    nordberg_p80_over_oss,
    nordberg_product,
    referencia_clasificacion,
    referencia_producto,
)
from conminucion.mandibula_validacion import (
    alimentacion_rr,
    curva_objetivo,
    mandibula_de_punto,
    maquina_producto,
    puntos_king,
)
from conminucion.sizes import SizeGrid, rosin_rammler
from conminucion.stream import Stream
from conminucion.units import CrusherOp

GRID = SizeGrid.geometric(600_000.0, 40, 2.0**0.25)


def feed(x63_um=150_000.0, m=1.2, tph=100.0, grid=GRID):
    return Stream(grid, tph * rosin_rammler(grid, x63_um, m))


def jaw(**kw):
    base = dict(gape_mm=800.0, width_mm=1100.0, css_mm=100.0, rpm=180.0, power_kw=150.0)
    return JawCrusher(**(base | kw))


# --------------------------------------------------------------- geometría
def test_regla_amit_de_la_carrera():
    assert carrera_amit_mm(1000.0) == pytest.approx(50.2)
    assert carrera_amit_mm(254.0) == pytest.approx(0.0502 * 0.254**0.85 * 1000.0)


def test_valores_por_defecto_de_geometria():
    j = jaw()
    assert j.height == 1600.0
    assert j.stroke == pytest.approx(carrera_amit_mm(800.0))
    assert j.oss_mm == pytest.approx(100.0 + j.stroke)
    assert j.tan_theta == pytest.approx((800.0 - 100.0) / 1600.0)


def test_desgaste_abre_css_efectivo_y_oss():
    j0, j1 = jaw(), jaw(wear_mm=10.0)
    assert j1.css_eff_mm == pytest.approx(110.0)
    assert j1.oss_mm == pytest.approx(j0.oss_mm + 10.0)


def test_volumen_de_camara_es_el_trapecio():
    j = jaw(height_mm=1500.0)
    esperado = 1.1 * 1.5 * (0.8 + (0.1 + j.stroke / 2000.0)) / 2.0
    assert j.chamber_volume_m3 == pytest.approx(esperado)
    assert j.holdup_t == pytest.approx(esperado * j.k)


def test_golpes_y_residencia():
    j = jaw()
    assert j.strokes_to_exit == pytest.approx(1.6 / min(j.advance_m, j.free_fall_m))
    assert j.residence_s == pytest.approx(j.strokes_to_exit * 60.0 / j.rpm)


def test_velocidad_critica_iguala_avance_y_caida_libre():
    j = jaw()
    en_nc = j.with_(rpm=j.critical_rpm)
    assert en_nc.advance_m == pytest.approx(en_nc.free_fall_m, rel=1e-12)
    assert en_nc.speed_factor == 1.0


# --------------------------------------------------------------- capacidad
def test_identidad_con_rose_y_english():
    for p in puntos_king():
        j = mandibula_de_punto(p, k=1.485)
        assert j.rpm <= j.critical_rpm * 1.1  # incluye casos N > Nc: se compara con N <= Nc
        j_bajo = j.with_(rpm=min(j.rpm, j.critical_rpm))
        esperado = rose_english_tph(
            j_bajo.css_mm, j_bajo.stroke, j_bajo.gape_mm, j_bajo.width_mm, j_bajo.rpm, 1.485
        )
        assert j_bajo.capacity_tph() == pytest.approx(esperado, rel=1e-9, abs=0)


def test_capacidad_sube_al_abrir_el_css():
    caps = [jaw(css_mm=c).capacity_tph() for c in (60.0, 100.0, 140.0)]
    assert caps[0] < caps[1] < caps[2]


def test_p80_engrosa_al_abrir_el_css():
    f = feed()
    for modelo in ("whiten", "nordberg"):
        p80 = [jaw(css_mm=c, product_model=modelo)(f).p80 for c in (60.0, 100.0, 140.0)]
        assert p80[0] < p80[1] < p80[2]


def test_sobre_nc_la_capacidad_baja_al_subir_n():
    j = jaw()
    nc = j.critical_rpm
    q = [j.with_(rpm=nc * f).capacity_tph() for f in (1.1, 1.3, 1.6)]
    assert q[0] > q[1] > q[2]
    # bajo Nc la capacidad es lineal en N
    assert j.with_(rpm=nc * 0.5).capacity_tph() * 2 == pytest.approx(
        j.with_(rpm=nc * 0.25).capacity_tph() * 4
    )


def test_taggart_a_mano():
    assert taggart_tph(508.0, 25.0) == pytest.approx(0.093 * 50.8 * 2.5)
    assert taggart_tph(508.0, 25.0, rho_b=3.2) == pytest.approx(2 * 0.093 * 50.8 * 2.5)
    assert jaw().taggart_tph() == pytest.approx(taggart_tph(1100.0, jaw().oss_mm))


# --------------------------------------------------------------- producto
def test_nordberg_a_mano():
    r = np.array([0.1, 0.4073, 1.0])
    k, n = np.array([0.81, 0.81, 0.65]), np.array([0.9756, 0.9756, 1.435])
    esperado = 1.0 - np.exp(-((r / k) ** n))
    assert nordberg_cumulative(r) == pytest.approx(esperado, rel=1e-9)
    assert nordberg_cumulative(1.0) == pytest.approx(1 - np.exp(-((1 / 0.65) ** 1.435)), rel=1e-9)


def test_nordberg_continua_en_el_corte():
    r = NORDBERG_R_CORTE
    fino = 1 - np.exp(-((r / 0.81) ** 0.9756))
    grueso = 1 - np.exp(-((r / 0.65) ** 1.435))
    assert abs(fino - grueso) < 1e-3  # continua a la precisión de las constantes publicadas
    assert abs(float(nordberg_cumulative(r)) - fino) < 1e-12
    assert abs(float(nordberg_cumulative(r * (1 + 1e-9))) - fino) < 1e-4  # salto de las constantes


def test_nordberg_p80():
    p80 = nordberg_p80_over_oss()
    assert p80 == pytest.approx(0.65 * np.log(5.0) ** (1 / 1.435), rel=1e-9)
    assert float(nordberg_cumulative(p80)) == pytest.approx(0.8, rel=1e-9)


def test_nordberg_rechaza_r_negativo():
    with pytest.raises(ValueError, match="negativo"):
        nordberg_cumulative(-0.1)


def test_nordberg_producto_conserva_masa_y_no_es_mas_grueso():
    f = feed(x63_um=20_000.0, m=1.5)  # alimentación fina: el tope de la alimentación actúa
    prod = nordberg_product(f, 100.0)
    assert prod.total_solids == pytest.approx(f.total_solids, rel=1e-12)
    assert np.all(prod.cumulative_passing >= f.cumulative_passing - 1e-12)
    assert np.all(prod.solids >= 0)
    # con alimentación gruesa el producto sigue a la curva en tamaños medianos
    grueso = nordberg_product(feed(400_000.0, 3.0), 100.0)
    assert grueso.total_solids == pytest.approx(100.0, rel=1e-12)


def test_nordberg_producto_corriente_vacia_y_oss_invalido():
    vacia = Stream.empty(GRID)
    assert nordberg_product(vacia, 100.0).total_solids == 0.0
    with pytest.raises(ValueError, match="OSS"):
        nordberg_product(feed(), 0.0)


def test_whiten_conserva_masa_y_usa_el_oss():
    j = jaw()
    f = feed()
    prod = j(f)
    assert prod.total_solids == pytest.approx(f.total_solids, rel=1e-9)
    # equivale a un cono cuyo ajuste es el OSS
    from conminucion.chancadora import ConeCrusher

    cono = ConeCrusher(j.oss_mm)(f)
    assert prod.solids == pytest.approx(cono.solids, rel=1e-12)


def test_referencia_r_clasificacion_y_producto():
    x = np.array([1.0, 1e5, 1e7])
    c = referencia_clasificacion(x, 100.0, 150.0)
    assert c[0] == 0.0 and c[-1] == 1.0
    j = maquina_producto()
    f = alimentacion_rr(j, 1.2, 5.0)
    prod = referencia_producto(f, j.css_eff_mm, j.oss_mm)
    assert prod.total_solids == pytest.approx(f.total_solids, rel=1e-9)
    assert prod.p80 < f.p80
    with pytest.raises(ValueError, match="K2"):
        referencia_clasificacion(x, 200.0, 100.0)


def test_curva_objetivo_acotada():
    j = maquina_producto()
    c = curva_objetivo(j, 1.2, 5.0, [0.1, 0.5, 1.5, 100.0])
    assert np.all((c >= 0) & (c <= 1)) and np.all(np.diff(c) > 0)


def test_pasante_en():
    f = feed()
    assert pasante_en(f, GRID.sieves[0] * 2) == 1.0
    assert pasante_en(f, GRID.sieves[5]) == pytest.approx(f.cumulative_passing[5])
    assert pasante_en(f, 1e-3) == 0.0
    with pytest.raises(ValueError):
        pasante_en(f, 0.0)


# --------------------------------------------------------------- parrilla
@pytest.mark.parametrize("modo", ["karra", "constante"])
def test_parrilla_conserva_masa(modo):
    f = Stream(GRID, feed().solids, water=7.0)
    pasa, queda = Grizzly(60.0, modo).split(f)
    assert (pasa.solids + queda.solids) == pytest.approx(f.solids, abs=1e-9)
    assert pasa.water + queda.water == pytest.approx(7.0, abs=1e-9)


def test_parrilla_constante_y_karra():
    g = Grizzly(60.0, "constante", eta=0.85)
    p = g.passing_fraction([10_000.0, 59_999.0, 60_000.0, 100_000.0])
    assert p == pytest.approx([0.85, 0.85, 0.0, 0.0])
    k = Grizzly(60.0)
    assert float(k.passing_fraction(60_000.0)) == pytest.approx(0.5, abs=1e-3)  # d50 = abertura
    assert k.passing_fraction([1_000.0, 200_000.0])[0] > 0.999
    pasa, _ = k.split(feed())
    assert pasa.p80 < feed().p80


def test_parrilla_sin_solidos():
    pasa, queda = Grizzly(60.0).split(Stream.empty(GRID))
    assert pasa.total_solids == 0 == queda.total_solids


def test_parrilla_entradas_invalidas():
    with pytest.raises(ValueError, match="abertura"):
        Grizzly(0.0)
    with pytest.raises(ValueError, match="Modo"):
        Grizzly(10.0, "otro")


# --------------------------------------------------------------- potencia y carga
def test_potencia_utilizacion_y_rebalse():
    f = feed(tph=100.0)
    j = jaw()
    cap = j.effective_capacity_tph(f)
    assert cap == min(j.capacity_tph(), j.motor_limit_tph(f))
    assert j.utilization(f) == pytest.approx(100.0 / cap)
    pesada = f.scaled(cap / 100.0 * 1.5)  # 150 % de la capacidad
    assert j.utilization(pesada) == pytest.approx(1.5)
    assert j.overflow_minutes(pesada, 30.0) == pytest.approx(30.0 / (0.5 * cap) * 60.0)
    assert j.overflow_minutes(f.scaled(0.1), 30.0) == float("inf")
    assert j.power_draw_kw(f) > 0


def test_motor_limita_y_vacio_cuenta():
    f = feed()
    chico = jaw(power_kw=5.0)
    assert chico.motor_limit_tph(f) < chico.capacity_tph()
    j_vacio = jaw(idle_fraction=0.2)
    assert j_vacio.power_draw_kw(f) == pytest.approx(jaw().power_draw_kw(f) + 0.2 * 150.0)
    assert jaw(power_kw=None).motor_limit_tph(f) == float("inf")
    assert jaw(power_kw=None).effective_capacity_tph(f) == jaw().capacity_tph()


def test_sin_reduccion_no_gasta_energia_de_bond():
    fina = feed(x63_um=1_000.0, m=2.0)  # más fina que el OSS: producto = alimentación
    j = jaw(product_model="nordberg")
    assert j.power_draw_kw(fina) == pytest.approx(0.0, abs=1e-9)
    assert j.motor_limit_tph(fina) == float("inf")


def test_overflow_negativo():
    with pytest.raises(ValueError, match="tolva"):
        jaw().overflow_minutes(feed(), -1.0)


# --------------------------------------------------------------- validación de entradas
@pytest.mark.parametrize(
    "kw, texto",
    [
        ({"gape_mm": 0.0}, "positivos"),
        ({"rpm": -1.0}, "positivos"),
        ({"wear_mm": -1.0}, "desgaste"),
        ({"idle_fraction": 1.0}, "vacío"),
        ({"stroke_mm": 0.0}, "stroke_mm"),
        ({"power_kw": -3.0}, "power_kw"),
        ({"mu": 0.0}, "μ"),
        ({"product_model": "x"}, "producto"),
        ({"gape_mm": 100.0}, "boca"),
        ({"alpha1": 2.0}, "α1"),
    ],
)
def test_entradas_invalidas(kw, texto):
    with pytest.raises(ValueError, match=texto):
        jaw(**kw)


def test_funciones_con_entradas_invalidas():
    with pytest.raises(ValueError):
        carrera_amit_mm(0.0)
    with pytest.raises(ValueError):
        taggart_tph(0.0, 10.0)
    with pytest.raises(ValueError):
        rose_english_tph(100.0, 10.0, 50.0, 100.0, 100.0, 1.0)


# --------------------------------------------------------------- operación unitaria y diagnóstico
def test_crusher_op_acepta_mandibula():
    f = feed()
    (sal,) = CrusherOp(jaw())([f, f.scaled(0.5)])
    assert sal.total_solids == pytest.approx(150.0, rel=1e-9)


def _por_codigo(checks):
    return {c.codigo: c for c in checks}


def test_diagnostico_estructura_y_fuentes():
    checks = diagnostico(jaw(), feed(), hopper_t=20.0)
    assert len(checks) == 8
    for c in checks:
        assert c.nivel in NIVELES and c.fuente in FUENTES and c.valores


def test_diagnostico_no_muerde():
    j = jaw(mu=0.1)  # 2·atan(0,1) = 11,4° < θ ≈ 23,6°
    assert not j.bites
    assert _por_codigo(diagnostico(j, feed()))["no_muerde"].nivel == "mal"
    assert _por_codigo(diagnostico(jaw(), feed()))["no_muerde"].nivel == "ok"


def test_diagnostico_velocidad_rangos_y_colpas():
    j = jaw(gape_mm=500.0, rpm=400.0, stroke_mm=90.0)
    c = _por_codigo(diagnostico(j, feed(x63_um=500_000.0, m=3.0)))
    assert c["velocidad_critica"].nivel == "aviso"
    assert c["rpm_fuera_de_rango"].nivel == "aviso"
    assert c["carrera_fuera_de_rango"].nivel == "aviso"
    assert c["colpas"].nivel == "aviso" and c["colpas"].valores["fraccion"] > 0
    ok = _por_codigo(diagnostico(jaw(), feed(x63_um=100_000.0, m=3.0)))
    assert ok["colpas"].nivel == "ok" and ok["velocidad_critica"].nivel == "ok"


def test_diagnostico_razon_reduccion():
    c = _por_codigo(diagnostico(jaw(css_mm=30.0, product_model="nordberg"), feed(300_000.0, 2.0)))
    assert c["razon_reduccion"].nivel in ("ok", "aviso")
    poca = _por_codigo(diagnostico(jaw(css_mm=300.0, product_model="nordberg"), feed()))
    assert poca["razon_reduccion"].nivel == "aviso"


def test_diagnostico_sobrecarga_y_potencia():
    f = feed(tph=100.0)
    j = jaw()
    carga = f.scaled(2.0 * j.effective_capacity_tph(f) / 100.0)
    c = _por_codigo(diagnostico(j, carga, hopper_t=10.0))
    assert c["sobrecarga"].nivel == "mal"
    assert np.isfinite(c["sobrecarga"].valores["minutos_a_rebalse"])
    chico = _por_codigo(diagnostico(jaw(power_kw=1.0), f))
    assert chico["potencia"].nivel == "mal"
    sin_motor = _por_codigo(diagnostico(jaw(power_kw=None), f))
    assert "potencia" not in sin_motor
