# Teoría: ecuaciones implementadas

Todo el código sale de las ecuaciones de la literatura citada al final. No se usó código,
formatos ni interfaz de ningún simulador comercial o académico.

## 0. Notación y convenciones

- Tamices s_1 > s_2 > … > s_n (µm), serie geométrica de razón √2 por defecto.
- Clase k = [s_{k+1}, s_k) para k < n; la clase n es el fondo (de 0 a s_n). Se supone que
  nada queda sobre s_1.
- Tamaño representativo x_k = √(s_k s_{k+1}) (media geométrica); para el fondo, x_n = s_n/√2.
- Corriente: sólidos por clase m_k (t/h), agua W (t/h), densidad de sólidos ρ_s (t/m³).
  % sólidos = 100 Σm / (Σm + W). Caudal de pulpa = Σm/ρ_s + W.
- Pasante acumulado en el tamiz s_k: P(s_k) = Σ_{j≥k} m_j / Σ m. P80 y F80 se obtienen por
  interpolación **log-lineal** de P contra ln(tamaño) entre tamices adyacentes; bajo s_n se
  usa un nodo virtual de P = 0 en s_n²/s_{n-1}.

### Generadores de alimentación

- Rosin-Rammler: P(x) = 1 − exp(−(x/x63)^m).
- Gaudin-Schuhmann: P(x) = min(1, (x/k)^α).

Se evalúan en los tamices, se diferencian para obtener la masa por clase y se renormalizan
por P(s_1) (truncado en el tamiz superior). Referencia: King (2001), cap. 2.

## 1. Función de fractura (Austin, Klimpel y Luckie, 1984)

Forma acumulada, fracción del material fracturado de la clase j que queda más fino que el
tamiz s_k (k > j):

    B(k|j) = φ (s_k/s_j)^γ + (1 − φ) (s_k/s_j)^β ,    B(n+1|j) := 0

Apariencia normalizada: la masa que aparece en la clase k es B(k|j) − B(k+1|j). Para que
toda la masa fracturada vaya a clases estrictamente más finas que j se divide por B(j+1|j):

    a_kj = [B(k|j) − B(k+1|j)] / B(j+1|j) ,    k = j+1 … n

**Prueba de Σ_k a_kj = 1** (j < n): la suma es telescópica,
Σ_{k=j+1}^{n} [B(k|j) − B(k+1|j)] = B(j+1|j) − B(n+1|j) = B(j+1|j), y al dividir por
B(j+1|j) se obtiene 1. La clase n (fondo) no se fractura (columna nula). Parámetros por
defecto: φ = 0,6, γ = 0,8, β = 3,5. Supuesto: la función es normalizable (no depende del
tamaño absoluto de j, solo de la razón s_k/s_j).

## 2. Molino de bolas de mezcla perfecta (Whiten, 1974; Napier-Munn et al., 1996)

Balance por clase en estado estacionario (r_i = tasa de ruptura, d_i = tasa de descarga):

    p_i = [ f_i + Σ_{j<i} (r/d)_j a_ij p_j ] / (1 + (r/d)_i)

resuelta de la clase más gruesa a la más fina; (r/d)_n = 0 en el fondo. **Conservación**:
sumando sobre i, Σ p_i (1 + (r/d)_i) = Σ f_i + Σ_j (r/d)_j p_j Σ_{i>j} a_ij, y como
Σ_{i>j} a_ij = 1 resulta Σ p_i = Σ f_i. El agua pasa sin cambio (más una adición opcional).

Dos parametrizaciones de (r/d)_i:

- **(a) Nudos** (x_m, (r/d)_m) definidos por el usuario: interpolación lineal de ln(r/d)
  contra ln(tamaño) y extrapolación constante fuera de los nudos.
- **(b) Selección de Austin**: S_i = A (x_i/1000 µm)^α / (1 + (x_i/μ)^Λ) en 1/min, con
  (r/d)_i = S_i τ y τ = tiempo de residencia medio (min). Referencia: Austin, Klimpel y
  Luckie (1984).

**N mezcladores en serie**: la descarga de uno alimenta al siguiente, cada uno con (r/d)/N
(equivale a τ/N); N → ∞ tiende al flujo pistón. Con r/d = 0 la descarga es igual a la
alimentación.

## 3. Clasificación por curva de eficiencia (Whiten; Lynch y Rao, 1975; Kelsall, 1953)

Eficiencia corregida a la descarga gruesa:

    Ec(x) = (exp(α x/d50c) − 1) / (exp(α x/d50c) + exp(α) − 2)

**Ec(d50c) = 0,5**: con x = d50c el numerador es e^α − 1 y el denominador 2(e^α − 1).
Además Ec(0) = 0 y Ec(∞) = 1. Se evalúa en la forma estable (1 − e^{−u})/(1 + (e^α − 2)e^{−u}),
u = α x/d50c, para evitar desbordes.

Con bypass de Kelsall, Rf = fracción del agua de alimentación que va a la descarga gruesa,
la eficiencia real es

    Ea(x) = Rf + (1 − Rf) Ec(x)

Los sólidos de cada clase se reparten Ea a la descarga gruesa y 1 − Ea a la fina; el agua,
Rf y 1 − Rf. Se usa el mismo modelo para el **hidrociclón** (gruesa = underflow, Rf típico
0,1-0,4) y para el **harnero** (gruesa = sobretamaño, Rf ≈ 0). Casos límite: d50c → ∞ envía
todo al overflow salvo el bypass Rf; Rf = 1 envía todo al underflow.

## 4. Hidrociclón de Plitt (1976): NO implementado

Ver el README (fase 2). Las constantes publicadas no coinciden entre fuentes consultadas
(por ejemplo, 50,5 frente a 39,7 en d50c, y 1,9 frente a 3,29 en la partición de agua), y no se
inventan constantes.

## 5. Energía de Bond (1952)

    W = 10 Wi (1/√P80 − 1/√F80)      [kWh/t, Wi en kWh/t, tamaños en µm]

Verificación: Wi = 15, F80 = 10 000 µm, P80 = 150 µm → W = 10,747 kWh/t. En un circuito se
usa F80 de la alimentación fresca y P80 del producto final, por tonelada de alimentación
fresca.

## 6. Solucionador secuencial-modular

Diagrama de unidades y corrientes. Las unidades que forman un ciclo se cortan en
**corrientes de corte** (tear); el orden de cálculo del resto se obtiene por ordenamiento
topológico. La corriente de corte x (sólidos por clase y agua) se itera:

- Sustitución sucesiva: x_{k+1} = g(x_k).
- Wegstein (opcional), por componente: s = (g_k − g_{k−1})/(x_k − x_{k−1}),
  q = s/(s − 1) acotado a [−5, 0], x_{k+1} = q x_k + (1 − q) g(x_k).

Criterio: máx|g(x) − x| / máx|g(x)| ≤ 1e-9 (relativo), máximo 500 iteraciones; si no
converge se lanza `ConvergenceError`. La carga circulante es sólidos del underflow /
sólidos de la alimentación fresca. Nota: el error de balance global del circuito es del orden
de la tolerancia por el flujo (el balance por unidad es exacto).

El **cajón** agrega el agua de dilución necesaria para que el % de sólidos de la alimentación
al ciclón sea el fijado: W = Σm (100 − %s)/%s (si la mezcla ya está más diluida, no quita agua).

## 7. Reconciliación de un nodo

Para el ciclón: f_i = R u_i + (1 − R) o_i, con R = fracción de los sólidos de alimentación
que va al underflow, y Σ f = Σ u = Σ o = 1 (fracciones). Mínimos cuadrados ponderados
con σ_i = máx(σ_rel x_i, σ_abs):

    min Σ (x̂ − x_med)² / σ²    sujeto a    A(R) x̂ = b

Para R fijo la solución es lineal: x̂ = x − W⁻¹Aᵀ (A W⁻¹ Aᵀ)⁺ (A x − b); R se obtiene
minimizando el objetivo con un buscador escalar acotado. Las variables que salen negativas se
fijan en cero y se resuelve de nuevo. Carga circulante reconciliada = R/(1 − R). Referencia:
Napier-Munn et al. (1996) para el tratamiento de balances de masa.

## 8. Ajuste de parámetros e intervalos de confianza

`scipy.optimize.least_squares` (TRF, con cotas). **Intervalos al 95 % por covarianza del
jacobiano** (no bootstrap): cov = s² (JᵀJ)⁻¹ con s² = SSR/(m − p), y theta ± t_{0,975; m−p} · se.
Es una aproximación lineal; cerca de una cota (por ejemplo Rf = 0) puede ser optimista.

- Ciclón: (d50c, α, Rf) contra la partición real medida (a la descarga gruesa).
- Molino: ln(r/d) en los nudos contra la descarga medida, con la fractura fija; el IC de
  r/d se obtiene exponenciando el IC de ln(r/d).

## Referencias

- Whiten, W. J. (1974). A matrix theory of comminution machines. *Chemical Engineering
  Science* 29, 589-599.
- Napier-Munn, T. J., Morrell, S., Morrison, R. D. y Kojovic, T. (1996). *Mineral Comminution
  Circuits: Their Operation and Optimisation*. JKMRC, University of Queensland.
- Austin, L. G., Klimpel, R. R. y Luckie, P. T. (1984). *Process Engineering of Size
  Reduction: Ball Milling*. SME-AIME.
- Lynch, A. J. y Rao, T. C. (1975). Modelling and scale-up of hydrocyclone classifiers.
  *Proc. 11th International Mineral Processing Congress*, Cagliari.
- Kelsall, D. F. (1953). A further study of the hydraulic cyclone. *Chemical Engineering
  Science* 2, 254-272.
- Bond, F. C. (1952). The third theory of comminution. *Trans. AIME* 193, 484-494.
- King, R. P. (2001). *Modeling and Simulation of Mineral Processing Systems*.
  Butterworth-Heinemann.
