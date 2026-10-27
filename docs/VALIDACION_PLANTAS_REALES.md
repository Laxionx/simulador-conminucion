# Validación con plantas reales publicadas

Aquí se pregunta si el simulador reproduce los números que publicaron plantas reales, y dónde falla. Solo se usaron fuentes públicas y gratuitas. Las tolerancias se fijaron **antes** de correr cada caso y ningún caso se ajustó para que pase.

- Código: `conminucion/plantas_reales.py` (datos tal como salen de la fuente, con tabla y página).
- Pruebas: `tests/test_plantas_reales.py`.
- Casos del simulador de procesos (P1-P3): `simulador-procesos/docs/VALIDACION_PLANTAS_REALES.md`.

## Resumen

| Caso | Planta | Qué se prueba | Veredicto |
|---|---|---|---|
| C1 | Bougainville (ejemplo de MODSIM 3.6.24) | Circuito completo contra la salida de MODSIM | **Pasa 7 de 7**: lo reproduce dentro de la tolerancia de convergencia de MODSIM |
| C2 | Vazante, Nexa (Brasil) | Curva de partición del ciclón: d50c, alpha y agua a gruesos | **Pasa** en las 2 campañas |
| C3 | Madneuli (Georgia) | Balance del circuito y carga circulante | **Pasa** en 3 de 3 clasificadores |
| C4 | Constancia, Hudbay (Perú) | Energía de Bond en 14 muestreos de molinos de bolas | **Pasa** en 14 de 14 |
| M | Chancador de mandíbula (King, Tabla 3.1; Nordberg 1976) | Capacidad en 56 puntos y producto contra la curva estándar | **Mixto**: pasan M2 (cinemática con un k) y el control empírico M4; **fallan** la referencia R, Taggart y los dos modelos de producto (resultado negativo) |

Para comprobar que las pruebas pueden fallar, se metieron 3 errores a propósito y las 3 pruebas los detectaron:
- Bond con +5 % de energía;
- la ecuación de Whiten con `e^α − 1` en vez de `e^α − 2`;
- el balance de agua con el % de sólidos en vez de la razón agua/sólidos.

## C2 · Vazante (Nexa Resources): partición de hidrociclones

**Fuente:** Costa, Bergerman y Delboni Jr. (2024), *Minerals* 14(7), 707, [doi:10.3390/min14070707](https://www.mdpi.com/2075-163X/14/7/707). Configuración «solo ciclones» del circuito C:

| Dato | Tabla | Página |
|---|---|---|
| Granulometrías balanceadas | A3 (campaña 1) y A5 (campaña 2) | 18-19 |
| Partición experimental | A6 y A7 | 19-20 |
| Parámetros publicados | 7 | 13 |

**Qué hace el simulador:**
1. `reconcile_node` obtiene de las 3 granulometrías la fracción de sólidos que va al underflow.
2. Con ella calcula la partición por clase.
3. El balance de agua (% de sólidos) da el agua a gruesos.
4. Se ajusta la curva de Whiten con el método del artículo: bypass de Kelsall con Rf igual al agua a gruesos.
5. El tamaño representativo de cada clase es la media geométrica de sus tamices.
6. Se ajustan las clases bajo 350 µm, con particiones del 31 al 92 %. Las gruesas superan el 93 % y sus tamices no son seguros (ver los hallazgos).

**Tolerancias:**
- partición recalculada vs la publicada: ±1,5 puntos;
- agua a gruesos: ±0,5 puntos;
- d50c: ±10 %;
- alpha: ±15 %.

| Campaña | | Simulador | Publicado | Desvío |
|---|---|---|---|---|
| 1 | d50c (µm) | 78,9 | 80 | −1,4 % |
| 1 | alpha | 0,790 | 0,79 | 0,0 % |
| 1 | Agua a gruesos (%) | 22,34 | 22,3 | +0,04 pt |
| 2 | d50c (µm) | 129,4 | 131 | −1,2 % |
| 2 | alpha | 0,721 | 0,71 | +1,5 % |
| 2 | Agua a gruesos (%) | 23,51 | 23,5 | +0,01 pt |

La partición recalculada coincide con las Tablas A6 y A7 en todas las clases publicadas, con un máximo de 1,0 punto de diferencia.

Como dato aparte, `fit_cyclone_partition` ajusta los 3 parámetros libres, sin fijar Rf, y da:

| Campaña | Rf libre | Agua a gruesos |
|---|---|---|
| 1 | 0,236 | 22,3 % |
| 2 | 0,221 | 23,5 % |

Los dos métodos coinciden en el bypass dentro de 1,5 puntos.

**Hallazgos sobre la fuente**, que no afectan el veredicto:
- **Tamices de la campaña 1.** Las tablas usan tamices de 2,0 y 0,298 mm, pero la lista de la sección 2.3 trae 2,36 y 0,350 mm, además de 0,850 y 0,600 mm. Para las clases gruesas, la columna di/d50c solo cuadra si hubo un tamiz de unos 0,42 mm que la tabla no muestra. Por eso esas clases quedaron fuera del ajuste.
- **Tabla 3 contra el texto.** La tabla da alpha = 1,27 para el ciclón dentro de la configuración combinada; el texto de la p. 7 dice 1,17.
- **d50c de la campaña 2.** La columna di/d50c implica un d50c de unos 126 µm, no los 131 µm de la Tabla 7. Son 4 % de diferencia.
- **Extracción del PDF.** El texto extraído desplaza una fila la columna di/d50c de la Tabla A7. Por eso las particiones se recalcularon desde las granulometrías y no se leyeron de esa tabla.

## C3 · Madneuli: balance y carga circulante

**Fuente:** Ergün, Ekmekçi, Gülsoy y Benzer (2004), *Physicochemical Problems of Mineral Processing* 38, 231-240, [PDF](https://www.911metallurgist.com/wp-content/uploads/2016/03/MODELLING-AND-SIMULATION-OF-GRINDING-Circuit.pdf).
- Circuito 2 de la concentradora: 84,5 t/h medidas, 85,4 t/h tras balancear.
- La Fig. 3 (p. 234) da t/h, % de sólidos, P80 y % −74 µm de 12 corrientes.
- La asignación de cada recuadro a su corriente se leyó del dibujo, no del texto extraído.

**Qué hace el simulador:**
1. Cierre de sólidos en los 6 nodos y de −74 µm en los 4 nodos sin molienda.
2. Carga circulante de cada clasificador con `reconcile_node`. Solo ve el % −74 µm de las 3 corrientes, sin los flujos; con 2 clases equivale a la fórmula de dos productos.
3. Se compara con la carga que sale de los flujos publicados: gruesos / alimentación fresca.

**Tolerancias:** cierres ±2 %; carga circulante ±10 %.

| Clasificador | Simulador | Publicada | Desvío |
|---|---|---|---|
| Espiral 1 | 0,747 | 0,731 | +2,2 % |
| Espiral 2 | 2,710 | 2,699 | +0,4 % |
| Ciclón secundario | 0,298 | 0,297 | +0,1 % |

Los sólidos cierran dentro de 0,5 % en los 6 nodos, y la fracción −74 µm dentro de 1,4 % en los 4 nodos sin molienda.

**Error mío, corregido:** el primer intento aplicó el balance de −74 µm también a los molinos. Un molino fabrica finos, así que ese balance no puede cerrar ahí. La prueba ahora lo exige solo donde no hay molienda, y comprueba aparte que los molinos sí generan finos.

## C4 · Constancia (Hudbay): energía de Bond

**Fuente:** Constancia, NI 43-101 Technical Report del 29-03-2021, [PDF](https://s23.q4cdn.com/405985100/files/doc_downloads/tech_reports/peru/Constancia-NI-43-101-Technical-Report-March-29-2021_FINAL.pdf):
- Tabla 13-2: F80 de los molinos de bolas (p. 95 del PDF).
- Tabla 13-3: Wi, P80, energía «modelo» y energía de planta de 14 muestreos (p. 96 del PDF).

**Qué hace el simulador:** `bond_energy(Wi, F80, P80)` para cada muestreo.

**Tolerancias:**
- energía del simulador vs la columna «modelo»: ±5 %;
- promedio planta/modelo vs el publicado (1,12): ±0,01.

| Resultado | Valor |
|---|---|
| Desvío contra la columna «modelo» | +1,0 a +2,2 % en los 14 muestreos |
| Promedio planta / modelo | 1,119 (publicado: 1,12) |

El simulador da siempre un poco más que el reporte. Es un sesgo constante, no ruido: probablemente el reporte aplica una corrección que su tabla no describe, y no se puede saber cuál.

**Hallazgo útil para diseñar:** Bond acierta en el mineral hipógeno y falla en el supérgeno.

| Mineral | Muestreos | Planta / Bond (promedio) | Rango |
|---|---|---|---|
| Hipógeno | 10 | 1,01 | 0,89 a 1,18 |
| Supérgeno | 4 | 1,40 | 1,25 a 1,69 |

Con supérgeno, la planta gasta en promedio 40 % más energía que la que predice Bond. Si se diseña con `bond_energy` para ese mineral, hay que multiplicar el Wi por un factor operativo.

## C1 · Bougainville: comparación con MODSIM 3.6.24

**Fuente:** el ejemplo `Bougainville.JOB` de MODSIM 3.6.24 Academic, corrido por el usuario el 07-10-2026. Esa versión se distribuye con licencia GPL v3 (`DOCS/LICENSE.TXT`).
- MODSIM escribió todas las corrientes en `STREAMPROPS.TXT`: caudales, agua y granulometrías.
- Los parámetros de entrada salen de `Bougainville.sid` (malla y alimentación) y `Bougainville.cur` (modelos).

**Lo que hubo que implementar:**
- **Molino `HFSU`:** selección específica de energía de Herbst y Fuerstenau con 5.000 kW netos, fractura de Austin (β = 2,17, γ = 0,696, Φ = 0,79) y una sola región de mezcla perfecta.
- **Ciclón `CYCA`:** curva logística con d50c = 400 µm, nitidez d25/d75 = 0,8 y bypass 0,2.

Ambos se escribieron desde sus ecuaciones publicadas (`docs/teoria.md`, secciones 1, 3b y 3c). Con permiso del usuario, se leyó el código fuente de MODSIM (`MILLMODS.FOR` y `CLASMODS.FOR`, en github.com/schneiderclaudio/ModSIm) solo para identificar sus convenciones. **No se copió código.**

**Tolerancias**, declaradas antes de correr:
- carga circulante y alimentación al molino: ±5 %;
- P80, P50 y P20 del producto: ±5 %;
- cada punto de la granulometría del producto: ±3 puntos;
- agua del cajón y % de sólidos del rebose: ±2 %.

### Cómo se llegó

1. **Lectura literal: falla.** Se tomaron los tamaños de la lista como tamices superiores, todo se evaluó en el tamaño medio y se usó la fractura del simulador. Resultado: carga circulante −10,5 % y P80 +13 %.
2. **Diagnóstico por equipo, con la salida de MODSIM.** El ciclón coincidía exacto si se evaluaba en el tamaño de la lista y sin escalado por densidad: el ajuste de su partición da d50 = 400,08 µm y λ = 9,839. El molino quedaba a 0,6-1,4 puntos con cualquier variante. El circuito pasaba 6 de 7 métricas; el P20 daba −5,2 %.
3. **Lectura del código de MODSIM.** Mostró la causa y corrigió una interpretación mía:
   - **Cada tamaño de la lista de MODSIM es el límite INFERIOR de su clase**, no el superior como yo había supuesto. La clase 1 es lo retenido en 20 mm y el fondo va de 0 a 6,9 µm. En ese límite inferior MODSIM evalúa la selección y el ciclón; los números del paso 2 eran los correctos, pero mi lectura de la convención estaba invertida.
   - **La fractura toma como tamaño de la partícula madre el límite inferior de su clase.** Así, todos los fragmentos caen en clases más finas y no hace falta normalizar. La fractura del simulador, en cambio, usa el tamiz superior y renormaliza los fragmentos que quedarían en la misma clase. Esa diferencia era el residuo del molino.
   - **El ciclón corrige por densidad respecto de la densidad del primer mineral**, no de 2,67 como dice el manual. Con un solo mineral no corrige nada.
   - **Detalles que no afectan este caso:** el agua al underflow nunca baja del 5 % aunque el bypass sea menor, y en el modelo de suma exponencial el α se aproxima como 1,099·(1+SI)/(1−SI) en vez de calcularse exacto.

El simulador ahora admite esas convenciones como opciones. Son `size_basis="tamiz_inferior"` en la selección y en el ciclón, y `Fracture(parent_size="tamiz_inferior")`. El comportamiento por defecto no cambia.

### Resultado

| Métrica | Simulador | MODSIM | Desvío |
|---|---|---|---|
| Carga circulante | 0,8187 | 0,8192 | −0,06 % |
| Alimentación al molino (t/h) | 836,75 | 837,36 | −0,07 % |
| P80 / P50 / P20 del producto (µm) | 185,6 / 71,88 / 20,61 | 185 / 71,9 / 20,6 | ≤0,3 % |
| Granulometría de las 4 corrientes (96 puntos) | máx. 0,025 pt | | |
| Agua del cajón y del molino (m³/h) | 221,87 y 122,98 | 222,05 y 123,05 | ≤0,1 % |
| % de sólidos del rebose y del underflow | 57,158 y 81,375 | 57,16 y 81,37 | ≤0,01 pt |

Las 7 métricas pasan. Lo que queda cabe en la tolerancia de convergencia de MODSIM (10⁻³): su propio producto sale con 460,44 t/h para una alimentación de 460,08. Por eso hay además una guarda de regresión al 0,2 %.

Para comprobar que las pruebas pueden fallar, se metieron 5 errores a propósito y todos se detectaron:
- λ del logístico −5 %;
- energía específica −5 %;
- signo de ζ2 invertido;
- madre en el tamiz superior;
- tamaño del fondo mal tomado.

### Hallazgo para quien use MODSIM: su P80 informado es un 16 % menor que el de un tamizado

MODSIM rotula cada % pasante con la media geométrica de dos tamaños consecutivos de su lista, pero ese % es lo que pasa el tamaño más grueso de los dos. La etiqueta queda 2^(1/4) = 1,19 veces por debajo del tamiz real.

| Medida sobre la misma distribución | P80 |
|---|---|
| Informada por MODSIM | 185 µm |
| Tamizado contra los límites de clase de MODSIM | 220,7 µm |

Antes de comparar un P80 de MODSIM con uno de planta, hay que deshacer ese corrimiento.

## M · Chancador de mandíbula: capacidad y producto

Código: `conminucion/mandibula*.py`; pruebas: `tests/test_mandibula_validacion.py`. Los listones se fijaron antes de ver los resultados y no se cambiaron; lo que no pasa queda como `xfail` estricto con los números medidos. Detalle del modelo en [chancado.md](chancado.md).

**Datos.** Tabla 3.1 de King (2000, Technical Notes 5), 12 máquinas y 56 puntos (se excluye 30x42 a OSS 102 mm, impreso «118 / 2», una errata). Curva estándar de Nordberg (1976) con las constantes del modelo JAW1 de MODSIM 3.6; geometría y rangos de AMIT 135 (Univ. de Alaska Fairbanks).

**Capacidad.** Listón: 80 % de los puntos dentro de ±30 %.

| Modelo | Mediana \|error\| | Dentro de ±30 % | Veredicto |
|---|---|---|---|
| M1 referencia R (k = 1,485) | 19,3 % | 71,4 % | No pasa |
| M2 cinemática + 1 factor k, fuera de muestra | 17,2 % | 83,9 % | Pasa |
| M3 Taggart | 40,7 % | 35,7 % | No pasa |
| M4 control empírico Q = a·W^b·OSS^c, fuera de muestra | 16,2 % | 83,9 % | Pasa |

Hallazgo: la cinemática pasa solo con un k ajustado (1,78 a 1,86 t/m³ en los 12 pliegues, contra 1,485 de R), y el control empírico hace lo mismo con 3 parámetros. La física no gana a un ajuste de curva en esta tabla. N/Nc está entre 0,55 y 1,03 en todos los tamaños (24x36 llega a 1,03); el motor alcanza para la capacidad de la tabla en los 56 puntos con Wi = 12,5 kWh/t y F80 = 0,6·G (SUPUESTO), con una razón de potencia de 0,40 a 0,70.

**Producto.** Listón: |Δ| ≤ 5 puntos porcentuales en 7 valores de r = x/OSS y 9 alimentaciones.

| Modelo | máx \|Δ\| | Veredicto |
|---|---|---|
| P1 referencia R sin ajuste | 17,2 a 20,8 pp | No pasa |
| P2 «whiten» ajustado en una alimentación, evaluado en las otras 8 | 2,0 a 9,4 pp | No pasa (4 de 8 dentro) |

Límites: la curva de Nordberg es una curva tipo de fabricante, no un muestreo de planta; la validación mide si el modelo la reproduce, no si predice una mandíbula real. Los parámetros μ, vacío, Wi y d50 de la parrilla son supuestos.

## D · Diagnóstico del muestreo con un error plantado (resultado negativo)

La pestaña «Ajuste a datos» muestra, con datos propios, el χ² de la reconciliación frente a su crítico al 95 % (n + 2 grados de libertad, con σ = máx(5 % del valor; 0,002)) y el ajuste estandarizado más grande, z = (medido − reconciliado)/σ. Se probó si ese z señala la corriente y la malla con un error: sobre Vazante (campaña 1) se sumaron +4 puntos de % pasante en una corriente y una malla (el acumulado sigue en orden sin más cambios). El criterio se escribió antes de mirar el resultado y no se ajustó (`tests/test_muestreo_error_plantado.py`): el mayor |z| debía caer en esa corriente, en una clase con esa malla por límite, con |z| > 3, y el χ² debía empeorar.

| Error plantado | χ² (base 0,04; crítico 25,0) | Mayor ajuste (z) | ¿Señala la corriente? |
|---|---|---|---|
| underflow, 149 µm | 27,28 | alimentación, 149–210 µm (2,91) | No |
| overflow, 74 µm | 13,21 | alimentación, 74–105 µm (2,11) | No |
| alimentación, 298 µm | 18,90 | alimentación, 210–298 µm (2,54) | Sí, pero |z| < 3 |

Veredicto: **no pasa**. El χ² empeora en los tres casos pero solo pasa su crítico en uno, y el mayor z cae siempre en la malla correcta y en la alimentación, con |z| < 3 en los tres: el balance reparte el error entre las tres corrientes. Por eso la app muestra el χ² y el z como medidas de cuánto se corrigió, no ofrece «qué mejorar» y no sugiere qué corriente re-muestrear.
