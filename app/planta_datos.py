"""Calibración del chancador con datos medidos en la planta (lógica pura, sin Streamlit).

Capacidad: la capacidad volumétrica es lineal en k (`Q = 60·N·V·f_N·k`), así que un Q medido da un
factor de planta f = Q_medido / Q_modelo y k_planta = k·f, y con ese k el modelo devuelve el Q
medido. Solo se puede si el modelo NO está limitado por el motor (si lo está, Q no depende de k).

P80: la curva de Nordberg tiene P80/OSS constante, así que el OSS efectivo implícito es
P80_medido / (P80/OSS) y la diferencia con el OSS nominal (CSS + δ + carrera) es un desgaste.
"""

from __future__ import annotations

from dataclasses import dataclass

from mandibula_datos import BY_KEY, F_PLANTA_MAX, F_PLANTA_MIN, Calculo

from conminucion.mandibula_producto import nordberg_p80_over_oss

ESTADOS_CAPACIDAD = ("ok", "motor", "motor_medido", "rango")
DESGASTE_MAX_MM = BY_KEY["wear"].hi


def factor_k(c: Calculo) -> float:
    """El factor de planta que ya está aplicado en el cálculo (1 = k de King)."""
    return float(c.v.get("kf", 1.0))  # type: ignore[arg-type]


@dataclass(frozen=True)
class ComparaCapacidad:
    estado: str  # uno de ESTADOS_CAPACIDAD
    q_modelo: float  # t/h efectiva con el k de King (mín. volumétrica y motor)
    q_volumetrica: float  # t/h con el k de King
    q_motor: float  # t/h que permite el motor
    delta_pct: float  # 100·(medido/modelo − 1)
    f: float  # Q_medido / Q_volumétrica con el k de King
    k_king: float
    k_planta: float  # k·f

    @property
    def calibrable(self) -> bool:
        return self.estado == "ok"


def comparar_capacidad(c: Calculo, q_medido: float) -> ComparaCapacidad:
    """Compara el Q medido con el del modelo con el k de King (aunque ya haya una calibración
    aplicada: se deshace dividiendo por su factor)."""
    if not q_medido > 0:
        raise ValueError("La capacidad medida debe ser positiva")
    kf = factor_k(c)
    k_king = c.jaw.k / kf
    vol = c.jaw.capacity_tph() / kf
    motor = c.jaw.motor_limit_tph(c.carga, c.prod_chancador)
    modelo = min(vol, motor)
    f = q_medido / vol
    if motor < vol:
        estado = "motor"
    elif q_medido > motor:
        estado = "motor_medido"
    elif not F_PLANTA_MIN <= f <= F_PLANTA_MAX:
        estado = "rango"
    else:
        estado = "ok"
    return ComparaCapacidad(estado, modelo, vol, motor, 100.0 * (q_medido / modelo - 1.0), f,
                            k_king, k_king * f)  # fmt: skip


@dataclass(frozen=True)
class ComparaP80:
    estado: str  # "ok", "neg" (más fino que Nordberg) o "fuera" (desgaste fuera del control)
    razon: float  # P80/OSS de Nordberg
    oss_implicito: float  # mm
    oss_nominal: float  # mm: CSS + δ + carrera
    diferencia: float  # mm: implícito − nominal
    desgaste: float  # mm: δ del control + diferencia (el valor que iría en el control)

    @property
    def aplicable(self) -> bool:
        return self.estado == "ok"


def comparar_p80(c: Calculo, p80_medido_mm: float) -> ComparaP80:
    """OSS efectivo implícito en un P80 medido del producto del chancador y su desgaste."""
    if not p80_medido_mm > 0:
        raise ValueError("El P80 medido debe ser positivo")
    razon = nordberg_p80_over_oss()
    implicito = p80_medido_mm / razon
    nominal = c.jaw.oss_mm
    dif = implicito - nominal
    desgaste = c.jaw.wear_mm + dif
    if dif < 0:
        estado = "neg"
    elif desgaste > DESGASTE_MAX_MM:
        estado = "fuera"
    else:
        estado = "ok"
    return ComparaP80(estado, razon, implicito, nominal, dif, desgaste)
