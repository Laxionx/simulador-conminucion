# Desgaste de bolas: carga estacionaria y consumo

Módulo `conminucion/desgaste.py`; pruebas en `tests/test_desgaste.py`.

## Teoría

Una bola de diámetro d pierde masa a razón proporcional a d^Δ (Austin, Klimpel y Luckie, 1984). Como su masa va con d³, el diámetro baja según

    dd/dt = −k · d^(Δ−2)

Con recarga continua y bolas que salen al llegar al diámetro de descarte d₀, el número de bolas de cada tamaño es el caudal de recarga multiplicado por el tiempo que pasan en ese tamaño. De ahí sale que la **masa acumulada de la carga bajo d es proporcional a d^(6−Δ)**:

| Δ | Ley | Masa acumulada | Fuente |
|---|---|---|---|
| 3 | Volumen: pierde masa en proporción a su peso | d³ | Davis (1919) |
| 2 | Superficie o desgaste lineal: dd/dt constante | d⁴ | Prentice (1943); Bond (1958) |
| 2,2 | Curva empírica de Bond, (d/D)^3,8 | d^3,8 | Bond (1958) |

Funciones del módulo:

| Función | Qué hace |
|---|---|
| `seasoned_charge` | Distribución en masa de la carga para una o varias medidas de recarga, con descarte. |
| `charge_balance` | Con la masa de la carga y la recarga en kg/h, deduce la velocidad de desgaste k, la vida de una bola, cuántas bolas hay y cuánto acero sale descartado o gastado. |
| `fit_wear_exponent` | Ajusta Δ a una carga tamizada en planta. |
| `bond_wear_kg_per_kwh` | Las correlaciones de Bond (1964) por índice de abrasión Ai: bolas, barras, revestimientos y chancadoras. |

### Ejemplo encadenado

Un molino de 5,36 × 6,25 m, con 42 % de carga, al 74 % de la velocidad crítica y Ai = 0,30:

| Paso | Resultado |
|---|---|
| Potencia y carga (`power.py`) | 3.107 kW y 277 t de bolas |
| Desgaste de Bond | 0,105 kg/kWh, o sea 326 kg/h de recarga |
| Balance, con bolas de 3" y descarte a 1" (ley lineal) | Una bola dura 96 días; hay unas 414.000 bolas en el molino |

## Validación

Las tolerancias se fijaron antes de correr.

| Prueba | Referencia | Tolerancia | Resultado |
|---|---|---|---|
| Teoría de Davis: 5 de las 18 columnas de la Tabla 21 | Davis (1919), vía 911Metallurgist | ±0,05 pt | 4 pasan; la quinta tiene errores de aritmética **en la fuente** (ver abajo) |
| Columnas «calculadas» de las Tablas 19 y 20 | Davis (1919) | ±0,05 pt | pasan |
| **Cargas medidas en planta**, con Δ = 3 | Miami Copper (Tabla 19) y Golden Cycle (Tabla 20) | ±3 pt por intervalo | pasan: Miami a 0,80 pt como máximo, Golden Cycle a 2,61 pt |
| Ley lineal frente a la curva de Bond (d/D)^3,8 | Bond (1958) | ±3 pt | pasa; Δ = 2,2 da la curva de Bond exacta |
| Simulación por cohortes frente a la solución analítica | Control numérico independiente | 1e-6 | pasa con 4 millones de cohortes |
| Correlaciones de Bond (1964) para bolas, barras y chancadoras | Informe GM71739 de Quebec, Tabla 6 (Sirios Resources, 2015) | ±1 % | pasan |
| Revestimientos | El mismo informe | ±1 % | fallan entre 0,4 y 2 %, porque **el informe redondeó los coeficientes** (ver abajo) |

Para comprobar que las pruebas pueden fallar, se metieron 3 errores a propósito y todos se detectaron:
- correr 0,1 el exponente de la masa;
- convertir mal la libra;
- cambiar el exponente de Bond de 0,33 a 0,34.

## Hallazgos

- **Qué ley sigue cada planta.** Se ajustó el exponente a cada carga medida:

  | Planta | Δ ajustado | Ley lineal (Δ = 2) |
  |---|---|---|
  | Miami Copper | 2,98, la ley de volumen casi exacta | falla por hasta 6,9 pt |
  | Golden Cycle | 2,63 | — |

  La curva de Bond (Δ = 2,2) describe mejor aceros modernos. **Δ no es universal: hay que ajustarlo con un tamizado de la carga de cada planta.**
- **Errata en Davis.** En la Tabla 21, columna de 2" con descarte a 0,5", publicó 18,16 % y 3,69 %; la fórmula exacta da 18,06 % y 3,77 %. Las otras columnas probadas coinciden.
- **El informe de Quebec cambió dos coeficientes de Bond.** Para los revestimientos de molinos de barras y de bolas usó 0,016 y 0,012 kg/kWh, y en el de bolas (Ai − 0,020) en vez de (Ai − 0,015). Con sus propias fórmulas se reproduce su tabla; con las de Bond, sus valores quedan entre 0,4 y 2 % arriba.
- **La fórmula de Bond sobrestima el consumo real.** Varias operaciones reportan consumos cercanos a la mitad de lo que predice: según datos de Newmont en SAG 2011, citados en el foro de 911Metallurgist, el factor es 0,5. Úsese como cota de diseño, no como dato de planta. Esos factores no se validaron aquí, porque no hay datos públicos de consumo real con su Ai.

## Fuentes

- Davis, E. W. (1919). Fine crushing in ball mills. *Trans. AIME* 61, 250-296. Tablas 19-21 reproducidas en 911Metallurgist, «Grinding Media Wear Rate Calculation in Ball Mill».
- Bond, F. C. (1958). Grinding ball size selection. *Mining Engineering* 10, 592-595.
- Bond, F. C. (1964). Lab equipment and tests help predict metal consumption in crushing and grinding units. *Engineering and Mining Journal* 165(6), 169-176.
- Austin, L. G., Klimpel, R. R. y Luckie, P. T. (1984). *Process Engineering of Size Reduction: Ball Milling*. SME-AIME.
- Sirios Resources (2015). Informe GM71739, proyecto Cheechoo. Ministerio de Recursos Naturales de Quebec.
