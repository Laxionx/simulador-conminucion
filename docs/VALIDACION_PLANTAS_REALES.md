# Validación con plantas reales publicadas

Aquí se pregunta si el simulador reproduce los números que publicaron plantas reales, y dónde falla. Solo se usaron fuentes públicas y gratuitas. Las tolerancias se fijaron **antes** de correr cada caso y ningún caso se ajustó para que pase.

- Código: `conminucion/plantas_reales.py` (datos tal como salen de la fuente, con tabla y página).
- Pruebas: `tests/test_plantas_reales.py`.
- Casos del simulador de procesos (P1-P3): `simulador-procesos/docs/VALIDACION_PLANTAS_REALES.md`.

## Resumen

| Caso | Planta | Qué se prueba | Veredicto |
|---|---|---|---|
| C1 | Bougainville (ejemplo de MODSIM 3.6.24) | Circuito completo contra la salida de MODSIM | **Pasa 6 de 7** métricas; el P20 queda en −5,2 % |
| C2 | Vazante, Nexa (Brasil) | Curva de partición del ciclón: d50c, alpha y agua a gruesos | **Pasa** en las 2 campañas |
| C3 | Madneuli (Georgia) | Balance del circuito y carga circulante | **Pasa** en 3 de 3 clasificadores |
| C4 | Constancia, Hudbay (Perú) | Energía de Bond en 14 muestreos de molinos de bolas | **Pasa** en 14 de 14 |

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

**Fuente:** el ejemplo `Bougainville.JOB` de MODSIM 3.6.24 Academic, con licencia GPL v3, corrido por el usuario el 07-10-2026.
- MODSIM escribió todas las corrientes en `STREAMPROPS.TXT`: caudales, agua y granulometrías.
- Los parámetros de entrada salen de `Bougainville.sid` (malla y alimentación) y `Bougainville.cur` (modelos).
- Su significado está en el manual de MODSIM v3.6 (pp. 53-55 y 67-68) y en la ayuda de HFSU.

**Lo que hubo que implementar.** Los dos modelos del ejemplo se programaron desde sus ecuaciones publicadas, sin usar código de MODSIM (ver `docs/teoria.md`, secciones 3b y 3c):
- **Molino `HFSU`:** selección específica de energía de Herbst y Fuerstenau con 5.000 kW netos y fractura de Austin (β = 2,17, γ = 0,696, Φ = 0,79). Es una sola región de mezcla perfecta, porque las regiones 1 y 2 tienen fracción 0.
- **Ciclón `CYCA`:** curva logística con d50c = 400 µm, nitidez d25/d75 = 0,8 y bypass 0,2.

**Cómo informa MODSIM**, deducido de su propia salida:
- Rotula cada % pasante con el tamaño medio de la clase, pero el valor es el % que pasa por el límite inferior. El fondo figura con 0,000 y la alimentación cuadra con las fracciones del `.sid`.
- Calcula P80, P50 y P20 interpolando en coordenadas de Rosin-Rammler. Así se reproducen sus 6,48 mm de la alimentación y sus 71,9 µm del producto.
- El simulador informa igual para comparar (`pasante_estilo_modsim`, `tamano_estilo_modsim`).

**Tolerancias**, declaradas antes de correr:
- carga circulante y alimentación al molino: ±5 %;
- P80, P50 y P20 del producto: ±5 %;
- cada punto de la granulometría del producto: ±3 puntos;
- agua del cajón y % de sólidos del rebose: ±2 %.

**Primer intento, con la lectura literal: falla.** Carga circulante 0,733 contra 0,819 (−10,5 %) y P80 209 contra 185 µm (+13 %).

**Diagnóstico por equipo.** Cada equipo se alimentó con la corriente exacta que calculó MODSIM:
- **Ciclón:** la partición implícita de MODSIM tiene la misma nitidez, pero corta más fino. Ajustada, da d50 = **400,08 µm** y λ = 9,839, frente a 400 y 9,847 de sus parámetros, si la curva se evalúa en el **tamiz superior** de cada clase. Evaluada en el tamaño medio daría 336,4 µm, que es 400 × 2^(−1/4). Además, MODSIM no aplicó el escalado por densidad: con él, el d50 sería 396,5 µm. Con esa convención, nuestro ciclón reproduce a MODSIM **exacto**: underflow de 377,05 contra 376,92 t/h y curva del rebose a 0,002 puntos.
- **Molino:** queda cerca, pero no exacto. Con la selección en el tamiz superior, la diferencia máxima es de 1,09 puntos; en el tamaño medio, de 1,40. Se probaron también otra discretización de la fractura y las 3 regiones del modelo GMIL. La mejor variante queda a 0,60 puntos y ninguna reproduce a MODSIM. Una sola región de mezcla perfecta sí se confirma: con 3 regiones el error sube a ~4,5 puntos. Ahí se paró la búsqueda, porque seguir probando variantes hasta que algo pase sería ajustar el modelo a la respuesta.

**Resultado con la convención de MODSIM** (ciclón y selección en el tamiz superior, sin escalado por densidad):

| Métrica | Simulador | MODSIM | Desvío | Veredicto |
|---|---|---|---|---|
| Carga circulante | 0,790 | 0,819 | −3,5 % | ✅ |
| Alimentación al molino (t/h) | 823,6 | 837,4 | −1,6 % | ✅ |
| P80 del producto (µm) | 179,6 | 185 | −2,9 % | ✅ |
| P50 del producto (µm) | 68,5 | 71,9 | −4,7 % | ✅ |
| P20 del producto (µm) | 19,5 | 20,6 | **−5,2 %** | ❌ |
| Granulometría del producto, 24 puntos | máx. 1,41 pt | | | ✅ |
| Agua del cajón (m³/h) y % de sólidos del rebose | 218,4 y 57,54 % | 222,05 y 57,16 % | −1,6 % y +0,7 % | ✅ |

**El P20 queda fuera por 0,2 puntos y no se ajustó nada para que pase.** En la suite figura como fallo esperado y estricto.

El residuo viene del molino, y su efecto se ve al cambiar dónde se evalúa la selección:

| Selección evaluada en | Carga circulante | P80 |
|---|---|---|
| Tamiz superior (la elegida) | 0,790 | 179,6 µm |
| Tamaño medio | 0,8195, casi igual a la de MODSIM | 195,6 µm (+5,7 %) |

MODSIM queda entre las dos. Para cerrar la diferencia habría que ver cómo discretiza su molino. El código de MODSIM es GPL v3 y es público, pero no se consultó.

**Mutaciones detectadas:** λ del logístico −5 %, energía específica −5 % y signo de ζ2 invertido. Las tres hacen fallar las pruebas.
