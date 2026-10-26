"""Datos y constantes publicados para el chancador de mandíbula, con su fuente.

Todo lo que no tiene fuente va rotulado SUPUESTO.
"""

from __future__ import annotations

from dataclasses import dataclass

PULGADA_MM = 25.4

# Fuentes citables por clave (las usan el diagnóstico y la documentación)
FUENTES: dict[str, str] = {
    "king_tn5": "King, R.P. (2000) Technical Notes 5: Crushers, Tabla 3.1 y texto (MODSIM)",
    "amit135": "AMIT 135, Lección 5, Univ. de Alaska Fairbanks (reglas de geometría y rangos)",
    "nordberg_1976": "Nordberg Process Machinery Reference Manual (1976), curva estándar de "
    "producto, constantes tal como las codifica el modelo JAW1 de MODSIM 3.6",
    "karra_king": "King, R.P. Technical Notes, harneros vibratorios, ec. 4-42 (Karra)",
    "rose_english": "Rose y English (1967), en Gupta y Yan (2016), cap. 4",
    "taggart": "Taggart, capacidad de la mandíbula (fórmula empírica)",
    "bond_1952": "Bond (1952), energía específica",
    "definicion": "Definición geométrica o balance de masa (sin parámetros)",
    "supuesto": "SUPUESTO declarado, sin fuente en los documentos revisados",
}

# --- Reglas de geometría (AMIT 135, lección 5) ---
ALTURA_SOBRE_BOCA = 2.0  # D = 2·boca
CARRERA_COEF = 0.0502  # L_T = 0,0502·boca^0,85, ambos en metros
CARRERA_EXP = 0.85
CARRERA_RANGO_CM = (1.0, 7.0)
RPM_RANGO = (100.0, 359.0)
COLPA_FRACCION_BOCA = 0.8  # tamaño máximo de alimentación ≈ 0,8·boca (King; AMIT: 0,8-0,9)
RAZON_REDUCCION_RANGO = (4.0, 9.0)  # King: 4:1 a 9:1 (AMIT: 4:1 a 7:1)
G_GRAVEDAD = 9.81

# --- Supuestos de la referencia R (simulador educativo ajeno) ---
RHO_S_REF = 2.7
LLENADO_REF = 0.55  # φ
K_REF = RHO_S_REF * LLENADO_REF  # t/m³ de densidad aparente efectiva
R_K1, R_K2, R_K3 = 1.05, 1.25, 2.3  # C(x): K1·CSS_e, K2·OSS, exponente
R_ETA_PARRILLA = 0.85
TAGGART_RHO_B = 1.6
KARRA_EXPONENTE = 5.9
KARRA_LN2 = 0.693

# --- Curva estándar de producto de Nordberg (r = x/OSS) ---
NORDBERG_R_CORTE = 0.4073
NORDBERG_FINO = (0.9756, 0.81)  # (n, k) para r <= corte
NORDBERG_GRUESO = (1.435, 0.65)  # (n, k) para r > corte

# --- Supuestos de la validación ---
WI_EJERCICIO_3_1 = 12.5  # kWh/t, ejercicio 3-1 de King
F80_SOBRE_BOCA = 0.6  # SUPUESTO: F80 = 0,6·boca en la guarda de potencia
WI_MANDIBULA_DEFECTO = WI_EJERCICIO_3_1  # SUPUESTO: Wi de impacto del chancador
MU_DEFECTO = 0.3  # SUPUESTO: coeficiente de roce roca-placa (sin fuente en los PDFs)
VACIO_DEFECTO = 0.0  # SUPUESTO: fracción de la potencia instalada que se gasta en vacío


@dataclass(frozen=True)
class MaquinaKing:
    """Una fila de la Tabla 3.1 de King (boca × largo en pulgadas)."""

    boca_in: float
    largo_in: float
    rpm: float
    kw: float
    capacidad_tph: dict[int, float]  # OSS (mm) -> t/h

    @property
    def nombre(self) -> str:
        return f"{self.boca_in:g}x{self.largo_in:g}"

    @property
    def boca_mm(self) -> float:
        return self.boca_in * PULGADA_MM

    @property
    def largo_mm(self) -> float:
        return self.largo_in * PULGADA_MM


# Transcrita desde la imagen de las págs. 5-6 y 5-7 de Crushers.pdf. EXCLUIDO: 30x42 a
# OSS 102 mm, impreso «118 / 2» (errata; por progresión sería ~182 t/h).
TABLA_KING: tuple[MaquinaKing, ...] = (
    MaquinaKing(10, 20, 300, 15, {25: 12.7, 32: 15.4, 38: 18.2, 51: 23, 63: 31}),
    MaquinaKing(10, 24, 275, 11, {25: 14.5, 32: 17.3, 38: 20, 51: 23, 63: 30}),
    MaquinaKing(15, 24, 275, 22, {32: 20.9, 38: 24.5, 51: 31, 63: 38.1, 76: 45.4}),
    MaquinaKing(14, 24, 275, 19, {38: 23.6, 51: 30, 63: 37.2, 76: 45.4}),
    MaquinaKing(24, 36, 250, 56, {51: 70, 63: 86.3, 76: 103, 102: 136}),
    MaquinaKing(30, 42, 200, 75, {63: 113, 76: 136, 127: 227, 152: 272}),
    MaquinaKing(32, 42, 200, 75, {102: 227, 127: 263, 152: 300, 178: 327, 203: 363}),
    MaquinaKing(36, 48, 180, 93, {76: 189, 102: 245, 127: 300, 152: 354, 178: 409}),
    MaquinaKing(42, 48, 180, 110, {127: 345, 152: 381, 178: 426, 203: 463, 229: 490, 254: 527}),
    MaquinaKing(48, 60, 170, 150, {152: 436, 178: 481, 203: 517, 229: 554, 254: 600}),
    MaquinaKing(56, 72, 120, 186, {178: 454, 203: 500, 229: 567, 254: 617}),
    MaquinaKing(66, 84, 90, 225, {178: 700, 203: 772, 229: 863, 254: 950}),
)
