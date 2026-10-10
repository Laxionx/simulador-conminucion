# Chancadora de cono (B3)

`ConeCrusher` (en `conminucion/chancadora.py`) es el modelo de clasificación interna y fractura de Whiten (1973), en la forma de King (2001, *Technical Notes 5: Crushers*).

En cada ciclo de la chancadora, una fracción c(d) de cada clase queda retenida y se rompe, y el resto sale. Para cada clase, de la más gruesa a la más fina:

    M m_i / W = (p_i^F + Σ_{j<i} c_j (M m_j / W) b_ij) / (1 − c_i b_ii)
    producto_i = (1 − c_i) M m_i / W

- **Clasificación interna:** c = 0 bajo d1 = α1·CSS, c = 1 sobre d2 = α2·CSS + d*, y entre ambos c = 1 − ((d − d2)/(d1 − d2))^n.
- **Fractura:** B(x; y) = K (x/y)^n1 + (1 − K)(x/y)^n2, con K la fracción de finos.

```python
from conminucion.chancadora import ConeCrusher

secundaria = ConeCrusher.standard(css_mm=35.0)    # cono estándar (CRSH de MODSIM)
terciaria = ConeCrusher.short_head(css_mm=13.0)   # cabeza corta (SHHD)
producto = secundaria(alimentacion)               # Stream -> Stream
```

En un circuito se usa `CrusherOp` (`conminucion/units.py`), por ejemplo cerrado con un harnero.

## Valores por defecto

Son los de MODSIM 3.6, leídos de su código (`CRSHMODS.FOR`, GPL v3). El código solo se leyó; no se copió.

| | Cono estándar | Cabeza corta |
|---|---|---|
| α1 · α2 | 0,653 · 1,6 | 0,653 · 2,0 |
| d* | 0 | 4,826 mm |
| Exponente n de la clasificación | **1** | 2 |
| n1 · n2 de la fractura | 0,5 · 4,5 | 0,518 · 2,475 (Karra 1982) |
| Fracción de finos K | 0,2 | 0,2 |

Las notas de King dicen que n «suele ser cercano a 2». El código de MODSIM usa 1 para el cono estándar.

## Convenciones

Igual que en el ejemplo Bougainville, el tamaño con que se evalúa cada término decide el resultado:

| | `"modsim"` (por defecto) | `"literal"` (notas de King) |
|---|---|---|
| c(d) | límite inferior de la clase | tamaño medio |
| Partícula madre | límite inferior | tamaño medio |
| B, para repartir entre clases hijas | en los tamaños medios | en los límites |

Las dos conservan la masa.

## Validación

La referencia son los reportes de MODSIM que trae su propio curso, en la carpeta `DOCS/Modsim Training/Module3` de MODSIM 3.6.24 Academic:
- ejercicio 3-4: cono estándar, CSS 35 mm, 819,3 t/h;
- ejercicio 3-5: cabeza corta, CSS 13 mm, 1.429 t/h.

Cada reporte trae la granulometría de la alimentación y la del producto, F80, P80 y la potencia. Las tolerancias se fijaron antes de correr (`tests/test_chancadora.py`).

| Prueba | Tolerancia | Cono estándar | Cabeza corta |
|---|---|---|---|
| % pasante del producto, 24 filas, convención MODSIM | ±0,1 puntos | máx. 0,009 ✅ | máx. 0,009 ✅ |
| F80 interpolado como MODSIM | ±0,5 % | 155,74 mm, 0,00 % ✅ | 34,05 mm, +0,03 % ✅ |
| P80 | ±0,5 % | −0,015 % ✅ | +0,066 % ✅ |
| Potencia de Bond (Wi de impacto 12) | ±1 % | 259,4 contra 259 kW ✅ | 452,5 contra 453 kW ✅ |
| Conservación de la masa, ambas convenciones | 1e-12 | ✅ | ✅ |

La potencia que informa MODSIM es la de Bond: 10·Wi·(1/√P80 − 1/√F80) por las t/h.

**Hallazgo:** con la convención literal de las notas de King, el producto se aparta hasta 13,9 puntos del de MODSIM:
- en el cono estándar, el P80 sale en 31,5 mm contra 37,4 mm (−16 %);
- en la cabeza corta, en 13,4 mm contra 15,4 mm (−13 %).

Por eso la convención por defecto es la de MODSIM, que es la que se pudo validar.

Para comprobar que las pruebas pueden fallar, se metieron 5 errores a propósito y todos se detectaron:
- exponente de la cabeza corta en 1;
- cabeza corta sin d*;
- n2 del cono estándar en 3,5;
- convención literal por defecto;
- olvidar la fracción que se queda en su propia clase (b_ii).

## Límites

- Es una comparación contra la implementación de MODSIM, no contra una chancadora medida. Los parámetros (α1, α2, K) se deben calibrar con muestreos de cada planta. King dice que, una vez calibrados para un mineral y una chancadora, no dependen del CSS.
- No predice la capacidad (t/h) ni la potencia instalada de la chancadora. La potencia que se informa es la de Bond.
- No incluye la chancadora primaria (giratoria o de mandíbula). MODSIM la modela con curvas tipo de fabricante normalizadas por el d80.
