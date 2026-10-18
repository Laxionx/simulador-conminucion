"""Los mensajes de error del modelo (`conminucion`) en español, vertidos al inglés para la app.

El modelo no cambia: sus textos siguen en español. Aquí se traducen los mensajes que la app puede
mostrar (el circuito que no converge y los datos fuera de dominio). Los números se vuelven al
formato inglés. Lo que no se conoce se muestra tal cual.
"""

from __future__ import annotations

import re

ERRORS: tuple[tuple[str, str], ...] = (
    (
        r"No convergió en (.+) iteraciones \(error relativo (.+) > (.+)\)",
        "It did not converge in {0} iterations (relative error {1} > {2})",
    ),
    (r"No convergió en (.+) iteraciones", "It did not converge in {0} iterations"),
    (r"wi, f80 y p80 deben ser positivos", "wi, f80 and p80 must be positive"),
    (r"Se requiere d50c>0, alpha>0 y 0<=rf<=1", "It requires d50c>0, alpha>0 and 0<=rf<=1"),
    (r"Se necesitan al menos 3 tamices", "At least 3 sieves are needed"),
    (
        r"Los tamices deben ser positivos y estrictamente decrecientes",
        "The sieves must be positive and strictly decreasing",
    ),
    (r"Flujos negativos", "Negative flows"),
    (r"Preset desconocido: (.+)\. Opciones: (.+)", "Unknown preset: {0}. Options: {1}"),
    (r"Faltan datos: observaciones <= parámetros", "Missing data: observations <= parameters"),
    (
        r"Las tres granulometrías deben tener igual número de clases",
        "The three size distributions must have the same number of classes",
    ),
)
_DECIMAL = re.compile(r"(?<=\d),(?=\d)")


def translate_error(message: str) -> str:
    """Un mensaje de error del modelo en inglés; si no se conoce, el original."""
    for pattern, template in ERRORS:
        m = re.fullmatch(pattern, message, flags=re.S)
        if m:
            return template.format(*(_DECIMAL.sub(".", g) for g in m.groups()))
    return message
