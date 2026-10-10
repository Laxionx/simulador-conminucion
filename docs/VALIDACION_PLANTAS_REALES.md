# Validación con plantas reales publicadas

Aquí se pregunta si el simulador reproduce los números que publicaron plantas reales, y dónde falla. Solo se usaron fuentes públicas y gratuitas. Las tolerancias se fijaron **antes** de correr cada caso y ningún caso se ajustó para que pase.

- Código: `conminucion/plantas_reales.py` (datos tal como salen de la fuente, con tabla y página).
- Pruebas: `tests/test_plantas_reales.py`.
- Casos del simulador de procesos (P1-P3): `simulador-procesos/docs/VALIDACION_PLANTAS_REALES.md`.

## Resumen

| Caso | Planta | Qué se prueba | Veredicto |
|---|---|---|---|
| C1 | Bougainville (ejemplo de MODSIM) | Circuito completo contra la salida de MODSIM | **No corrido**: faltan 2 modelos (ver C1) |
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

## C1 · Bougainville (MODSIM): no corrido

El ejemplo de MODSIM simula el molino de bolas con un modelo que escala la ruptura con la energía del motor (`HFSU`, de Herbst y Fuerstenau) y el ciclón con su propio modelo (`CYCA`). Este simulador no tiene ninguno de los dos: su molino usa la selección de Austin o por nudos con tiempo de residencia, y su ciclón la curva de Whiten. Reproducir la salida de MODSIM (P80 de 185 µm y carga circulante de 82 %) exigiría implementar esos modelos. El brief excluía cambiar modelos salvo por un bug, así que el caso se descarta con nota y queda para una fase siguiente.

**Observación, sin veredicto:** el archivo del ejemplo (`Bougainville.siz`) trae granulometrías de la descarga del molino, el underflow y el overflow.
- Reconciliadas, dan una carga circulante de **3,7**, con χ² = 86. Es una cifra poco coherente: la fracción al underflow varía entre 0,70 y 0,86 según el tamiz.
- MODSIM, con los parámetros del ejemplo, da **0,82**.
- No consta si esas granulometrías son un muestreo real, así que no se usan como referencia.
