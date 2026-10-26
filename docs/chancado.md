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

## Chancador de mandíbula y parrilla

Código: `conminucion/mandibula.py` (`JawCrusher`, `Grizzly`), `mandibula_producto.py` (curva de Nordberg y producto de la referencia R), `mandibula_diagnostico.py` y `datos_mandibula.py` (Tabla 3.1 de King, constantes y fuentes). Pruebas: `tests/test_mandibula.py` y `tests/test_mandibula_validacion.py`. `CrusherOp` acepta tanto el cono como la mandíbula.

**Geometría** (G boca, W ancho, D altura de la cámara = 2G, L_T carrera, CSS_e = CSS + desgaste, OSS = CSS_e + L_T). La carrera por defecto sigue AMIT 135: L_T = 0,0502·G^0,85 (G y L_T en metros).

**Cinemática** (misma estructura que la referencia R):

- tan θ = (G − CSS_e)/D; muerde si θ ≤ 2·arctan μ.
- h = L_T/tan θ; s = ½·g·(30/N)²; Nc = 30·√(g·tan θ/(2·L_T)).
- V = W·h·(CSS_e + L_T/2); Q = 60·N·V·f_N·k, con f_N = 1 si N ≤ Nc y (Nc/N)² si no.
- Con D = 2G y N ≤ Nc, Q coincide con la forma de baja frecuencia de Rose y English (1967): Q = 60·L_T·N·W·(2·CSS + L_T)·R/(R − 1)·k, R = G/CSS. La prueba lo verifica a 1e-9 en los 56 puntos de la tabla.
- La cámara es un trapecio de volumen W·D·(G + CSS_e + L_T/2)/2; los golpes de una partícula son D/mín(h, s).

**Producto**, a elegir: `"whiten"` (el ciclo del cono con el ajuste igual al OSS: d1 = α1·OSS, d2 = α2·OSS + d*; reutiliza `resolver_ciclo` y el cono queda idéntico) o `"nordberg"` (curva estándar de Nordberg, 1976, tal como la codifica el modelo JAW1 de MODSIM: con r = x/OSS, P = 1 − exp(−(r/k)^n), n = 0,9756 y k = 0,81 si r ≤ 0,4073, y n = 1,435 y k = 0,65 si no; evaluada en la media geométrica de cada clase y sin permitir un producto más grueso que la alimentación). Solo se citan las constantes; no se copió código de MODSIM (GPL).

**Parrilla**: partición de Karra c(d) = 1 − exp(−0,693·(d/d50)^5,9) a sobretamaño con d50 = abertura entre barras (SUPUESTO), o la variante "constante" de R (pasa η·f(x) si x < abertura, η = 0,85). Devuelve (pasante, retenido) con balance de masa a 1e-9.

**Diagnóstico** (`diagnostico`, puro, sin textos): no muerde, N > Nc, rpm fuera de 100-359, carrera fuera de 1-7 cm, colpas (> 0,8·G), razón de reducción fuera de 4-9, sobrecarga con tiempo a rebalse y potencia de Bond + vacío mayor que la instalada. Cada chequeo lleva su fuente.

**SUPUESTOS declarados** (sin fuente en los documentos revisados): μ = 0,3; fracción de potencia en vacío = 0; Wi de impacto = 12,5 kWh/t (valor del ejercicio 3-1 de King, de otro uso); α1, α2 y el exponente del `"whiten"` por defecto son los del cono (no calibrados para mandíbula); F80 = 0,6·G en la guarda de potencia; la abertura de la parrilla hace de d50.

### Validación (ver también `VALIDACION_PLANTAS_REALES.md`, caso M)

Capacidad contra la Tabla 3.1 de King (56 puntos; se excluye 30x42 a OSS 102 mm, impreso «118 / 2»), con CSS = OSS − L_T, D = 2G, N de la tabla y W = largo. Listón fijado antes: 80 % de los puntos dentro de ±30 % (fuera de muestra en M2 y M4, dejando fuera un tamaño entero cada vez).

| Modelo | Mediana \|error\| | Dentro de ±30 % | Peor punto | ¿Pasa? |
|---|---|---|---|---|
| M1 referencia R (k = 2,7·0,55, sin parámetros) | 19,3 % | 40/56 = 71,4 % | 36x48 OSS 76: −47,5 % | **No** (xfail) |
| M2 cinemática con un k ajustado (12 pliegues) | 17,2 % | 47/56 = 83,9 % | 48x60 OSS 254: +52,5 % | Sí |
| M3 Taggart (ρ_b = 1,6) | 40,7 % | 20/56 = 35,7 % | 42x48 OSS 127: −58,3 % | **No** (xfail) |
| M4 control empírico a·W^b·OSS^c (12 pliegues) | 16,2 % | 47/56 = 83,9 % | 56x72 OSS 254: +63,3 % | Sí |

El k de M2 sale casi constante entre pliegues (1,78 a 1,86 t/m³; global 1,815 contra 1,485 de R): la cinemática tiene la forma correcta pero R la subestima un 18 %. Pero el control empírico de tres parámetros le gana en la mediana y empata en la fracción: la física aporta poco más que un ajuste de curva con esta tabla. Taggart falla porque subestima de 31 a 52 % todas las máquinas desde la 24x36.

Producto contra la curva de Nordberg (42x48 a OSS 152 mm; r = x/OSS en 0,1 a 1,5; 9 alimentaciones Rosin-Rammler truncadas en 0,9·G; listón |Δ| ≤ 5 puntos porcentuales):

| Modelo | máx \|Δ\| por alimentación | ¿Pasa? |
|---|---|---|
| P1 referencia R, sin ajuste | 17,2 a 20,8 pp | **No** (xfail) |
| P2 «whiten» ajustado con n = 1,2 y F80/OSS = 5 (α1 = 0,350, α2 = 4,350, exponente 7,80) | 2,0 a 9,4 pp en las 8 alimentaciones fuera de muestra (4 pasan, 4 no) | **No** (xfail) |

El ajuste de P2 deja un RMS de 1,5 pp en su alimentación, pero α2 − α1 llegó al límite superior de la búsqueda (4,0) y el exponente es muy alto: la curva de clasificación del ciclo es casi un escalón ancho, y no generaliza a las alimentaciones más finas (n = 0,8). Es un resultado negativo.

## Límites

- Es una comparación contra la implementación de MODSIM, no contra una chancadora medida. Los parámetros (α1, α2, K) se deben calibrar con muestreos de cada planta. King dice que, una vez calibrados para un mineral y una chancadora, no dependen del CSS.
- No predice la capacidad (t/h) ni la potencia instalada de la chancadora. La potencia que se informa es la de Bond.
- La mandíbula tiene su propia sección arriba. La giratoria primaria no está incluida; MODSIM la modela con curvas tipo de fabricante normalizadas por el d80.
