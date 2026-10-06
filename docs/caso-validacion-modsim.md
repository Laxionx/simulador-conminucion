# Caso de validación cruzada con MODSIM 3.6

Circuito cerrado **directo**: alimentación fresca -> molino de bolas -> cajón (agua de dilución) -> hidrociclón; underflow -> molino; overflow = producto. Todos los datos están listos para cargarlos a mano en MODSIM 3.6; la columna «MODSIM» queda vacía para que se complete con la corrida del usuario. Este documento se regenera con `python -m conminucion.validacion`.

## 1. Clases de tamaño y alimentación

Serie geométrica de razón √2 desde 9500 µm (17 tamices; la clase 17 es el fondo). Alimentación fresca: 100 t/h de sólidos secos, Rosin-Rammler x63 = 3200 µm, m = 1, truncada en el tamiz superior; densidad de sólidos 2.7 t/m³; F80 = 4561.1 µm.

| Clase | Tamiz sup. (µm) | Tamiz inf. (µm) | Tamaño repr. (µm) | Alimentación (% masa) | S_i (1/min) | Ea ciclón (%) |
|---|---|---|---|---|---|---|
| 1 | 9500.0 | 6717.5 | 7988.5 | 7.504 | 0.1544 | 100.00 |
| 2 | 6717.5 | 4750.0 | 5648.7 | 10.973 | 0.3032 | 100.00 |
| 3 | 4750.0 | 3358.8 | 3994.3 | 13.011 | 0.5478 | 100.00 |
| 4 | 3358.8 | 2375.0 | 2824.4 | 13.282 | 0.8340 | 100.00 |
| 5 | 2375.0 | 1679.4 | 1997.1 | 12.186 | 0.9875 | 100.00 |
| 6 | 1679.4 | 1187.5 | 1412.2 | 10.363 | 0.9247 | 100.00 |
| 7 | 1187.5 | 839.7 | 998.6 | 8.351 | 0.7511 | 100.00 |
| 8 | 839.7 | 593.7 | 706.1 | 6.478 | 0.5720 | 100.00 |
| 9 | 593.7 | 419.8 | 499.3 | 4.890 | 0.4248 | 100.00 |
| 10 | 419.8 | 296.9 | 353.0 | 3.622 | 0.3125 | 99.96 |
| 11 | 296.9 | 209.9 | 249.6 | 2.646 | 0.2292 | 99.15 |
| 12 | 209.9 | 148.4 | 176.5 | 1.915 | 0.1679 | 92.98 |
| 13 | 148.4 | 105.0 | 124.8 | 1.377 | 0.1229 | 74.71 |
| 14 | 105.0 | 74.2 | 88.3 | 0.985 | 0.0900 | 52.60 |
| 15 | 74.2 | 52.5 | 62.4 | 0.702 | 0.0659 | 37.91 |
| 16 | 52.5 | 37.1 | 44.1 | 0.499 | 0.0482 | 30.10 |
| 17 | 37.1 | 0 | 26.2 | 1.215 | 0 (fondo) | 24.72 |

## 2. Parámetros del molino de bolas (Austin)

| Parámetro | Valor |
|---|---|
| S_i = A (x/1000)^α / (1 + (x/μ)^Λ), x en µm, S en 1/min |  |
| A (1/min) | 0.8 |
| α | 0.9 |
| μ (µm) | 2500.0 |
| Λ | 3.0 |
| τ, tiempo de residencia medio (min) | 3.0 |
| Mezcladores perfectos en serie | 1 |
| Agua de adición al molino (t/h) | 0.0 |

Función de fractura acumulada B(k|j) = φ (s_k/s_j)^γ + (1-φ) (s_k/s_j)^β, con s_k el tamiz superior de la clase k:

| φ | γ | β |
|---|---|---|
| 0.6 | 0.8 | 3.5 |

## 3. Hidrociclón (curva de eficiencia)

Ec(x) = (exp(α x/d50c) - 1) / (exp(α x/d50c) + exp(α) - 2);  Ea = Rf + (1-Rf) Ec.

| d50c (µm) | α | Rf (fracción del agua al underflow) | % sólidos alim. ciclón |
|---|---|---|---|
| 100.0 | 3.0 | 0.2 | 45.0 |

## 4. Resultados de nuestro simulador

Convergencia: 83 iteraciones de sustitución sucesiva (tolerancia relativa 1e-14). Error de balance de sólidos del circuito: 2.36e-12 t/h.

| Magnitud | conminucion | MODSIM |
|---|---|---|
| P80 del producto (overflow), µm | 93.00 |  |
| Carga circulante (UF sólidos / alim. fresca) | 3.1630 |  |
| alim_molino: sólidos, t/h | 416.301 |  |
| alim_molino: agua, t/h | 101.763 |  |
| alim_molino: % sólidos | 80.36 |  |
| descarga_molino: sólidos, t/h | 416.301 |  |
| descarga_molino: agua, t/h | 101.763 |  |
| descarga_molino: % sólidos | 80.36 |  |
| alim_ciclon: sólidos, t/h | 416.301 |  |
| alim_ciclon: agua, t/h | 508.813 |  |
| alim_ciclon: % sólidos | 45.00 |  |
| underflow: sólidos, t/h | 316.301 |  |
| underflow: agua, t/h | 101.763 |  |
| underflow: % sólidos | 75.66 |  |
| overflow: sólidos, t/h | 100.000 |  |
| overflow: agua, t/h | 407.050 |  |
| overflow: % sólidos | 19.72 |  |
| Energía de Bond del circuito, kWh/t (Wi=14) | 12.444 | n/a |

## 5. Convenciones que podrían diferir entre ambos programas

- **Clases de tamaño**: aquí la clase k es [s_{k+1}, s_k) y el fondo va de 0 a s_n, con tamaño representativo = media geométrica (fondo: s_n/√2). Verificar cómo define MODSIM los intervalos y su tamaño representativo (afecta S_i, Ea y P80).
- **Fractura**: se usa la forma acumulada normalizada para que Σ a_kj = 1. Otra normalización (p. ej. sobre otra clase de referencia) cambia la distribución del producto fracturado.
- **Selección**: S_i se evalúa en el tamaño representativo; (r/d)_i = S_i τ con un único mezclador. Otro número de mezcladores o parametrización lleva a otra descarga.
- **Interpolación de P80**: log-lineal del pasante entre tamices; otros programas pueden usar splines o interpolación lineal.
- **Ciclón**: curva de Whiten/Lynch-Rao con bypass de agua Rf aplicado también a los finos; la forma exacta de la curva y el bypass en MODSIM debe confirmarse.
- **Agua**: el cajón agrega agua hasta el % de sólidos fijado; el molino no agrega agua.
- **Convergencia**: tolerancia y criterio de corte de reciclo distintos dan diferencias en la 4.ª-6.ª cifra de la carga circulante.
