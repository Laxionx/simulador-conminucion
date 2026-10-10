# Hidrociclón de Plitt (B3)

`PlittCyclone` (en `conminucion/plitt.py`) predice el corte del ciclón desde su geometría y su alimentación. Calcula:
- el d50c;
- la nitidez m;
- la partición de caudal y el agua que va a la descarga.

A diferencia de `EfficiencyCurve` o `SharpnessCurve`, el d50c no es un dato de entrada.

```python
from conminucion.plitt import PlittCyclone

ciclon = PlittCyclone(diameter_m=0.6, n_cyclones=4)   # geometría «estándar» de MODSIM
descarga, rebalse = ciclon.split(alimentacion)
ciclon.performance(alimentacion).d50c_um
ciclon.ropes(descarga)                                # aviso de embanque (Mular y Jull)
```

En un circuito se usa como cualquier clasificador: `ClassifierOp(PlittCyclone(...))`.

## Qué versión de Plitt

Se implementó **la forma SI de King, que es el modelo CYCL de MODSIM 3.6**. Su código (`CLASMODS.FOR`, GPL v3) se leyó y no se copió. Las ecuaciones están en el docstring del módulo.

Las versiones publicadas de Plitt (1976) no coinciden entre sí, y el artículo original es de pago:
- la constante del d50c es 50,5 en la documentación de SysCAD y 39,7 en otras fuentes;
- además cambian las unidades.

La de MODSIM vale 2690/√1000 ≈ 85,07 en m y m³/s. Pasada a cm y L/min, queda a un 3 % de la de 50,5.

Además de Plitt, MODSIM agrega dos cosas:
- un factor de viscosidad, (μ/0,001)^0,35 (Kawatra et al. 1996);
- una densidad de la pulpa en la zona de separación.

Ambas están incluidas.

**Valores por defecto:** los del formulario de MODSIM.

| Parámetro | Valor |
|---|---|
| h | 3·Dc |
| Entrada | 0,2·Dc |
| Vórtice | 0,167·Dc |
| Ápex | 0,116·Dc |
| Altura de alimentación | 3 m |
| Viscosidad | 0,0012 Pa·s |
| Exponente de densidad | 0,5 |
| Factores de calibración | 1 |

## Validación

La referencia son los resultados de MODSIM del ejercicio 2-2 del curso que trae MODSIM 3.6.24 Academic (`DOCS/Modsim Training/Module2`):
- un ciclón de 60 cm;
- 50 t/h de sílice al 40 % de sólidos;
- la granulometría de 10 tamices del ejercicio 2-1.

Para repartir esa alimentación en las 25 clases internas se replicó la interpolación de la interfaz de MODSIM (`FRPASS` en `SYSDAT.BAS`, en `conminucion/modsim.py`). Es localmente Rosin-Rammler entre tamices vecinos y evalúa en el punto medio de cada clase.

Las tolerancias se fijaron antes de correr (`tests/test_plitt.py`).

| Prueba | MODSIM | Este simulador | Tolerancia |
|---|---|---|---|
| d50c, ápex estándar (11,6 %) | 90,9 µm | 90,93 µm | ±0,1 µm ✅ |
| d50c, ápex 15 % | 75,8 µm | 75,76 µm | ±0,1 µm ✅ |
| % de sólidos de la descarga, ápex estándar | 70,9 % | 70,88 % | ±0,1 ✅ |
| % de sólidos del rebalse, ápex estándar | 13,7 % | 13,68 % | ±0,1 ✅ |
| % de sólidos de la descarga, ápex 15 % | 55,1 % | 55,14 % | ±0,1 ✅ |
| d80 del rebalse | 81,6 µm | 81,6 µm | ±1 % ✅ |
| d80 de la descarga | 516 µm | 516 µm | ±1 % ✅ |
| Ápex mínimo de Mular y Jull | 7,4 cm | 7,41 cm | ±0,05 cm ✅ |
| Aviso de embanque con los dos ápex | sí, sí | sí, sí | ✅ |
| Conservación de sólidos y agua | — | — | 1e-12 ✅ |

La prueba del d50c **no es ciega**: al leer el código se calculó a mano (90,94 y 75,76 µm) para confirmar la lectura. Las demás sí lo son.

**Hallazgo:** como en la chancadora y en Bougainville, la convención decide. MODSIM evalúa la curva en el límite inferior de cada clase. Evaluada en el tamaño medio, el rebalse sale 15 % más fino: d80 de 69,5 µm contra 81,6. Por eso el caso de MODSIM usa `size_basis="tamiz_inferior"`.

**Rareza de MODSIM, replicada a propósito:** si el primer tamiz de los datos ya deja pasar el 100 %, sobre ese tamaño `FRPASS` extrapola desde el par siguiente y da un poco menos de 100 % (99,57 % en la prueba).

Para comprobar que las pruebas pueden fallar, se metieron 6 errores a propósito y todos se detectaron:
- constante del d50c en 2600;
- partición con el % de sólidos en vez de la fracción;
- Rf igual a Rv;
- curva evaluada en el tamaño medio;
- alimentación interpolada en el límite y no en el punto medio;
- Mular y Jull con t/h en vez de kg/s.

## Límites

- **Es una comparación contra la implementación de MODSIM, no contra ciclones medidos.** Sin calibrar, Plitt predice mal en planta. Con datos de fosfato de 15 geometrías, la versión original llegó a una correlación del 11,5 % con el d50c medido.
- Para usarlo en una planta hay que ajustar F1, F2 y F3 con un muestreo. Ejemplo: el ejercicio 8-1 de MODSIM obtuvo 0,293, 0,152 y 0,856 para una planta real.
- El criterio de Concha, que MODSIM informa en su reporte, no está implementado. El curso considera que Mular y Jull avisa de más.
- Un solo mineral. Con varios minerales, MODSIM corrige el d50 de cada uno por su densidad.
