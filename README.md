# conminucion — grinding & classification circuit simulator

Python simulator for ball-mill / hydrocyclone circuits, built from scratch from published equations (Whiten, Austin, Lynch-Rao, Kelsall, Bond).
Includes a modular flowsheet solver with recycles, plant-data reconciliation and parameter fitting with confidence intervals, and a Streamlit app.

[![CI](https://github.com/Laxionx/simulador-conminucion/actions/workflows/ci.yml/badge.svg)](https://github.com/Laxionx/simulador-conminucion/actions/workflows/ci.yml)

## Qué es

Un simulador de circuitos de molienda y clasificación para aprender y practicar balance de
masa en conminución. Resuelve molino de bolas (mezcla perfecta, Whiten/Austin), clasificación
por curva de eficiencia con bypass (hidrociclón y harnero), energía de Bond, circuitos con
reciclo (abierto, cerrado directo y cerrado inverso), reconciliación de balance en un nodo y
ajuste de parámetros a datos de planta con intervalos de confianza del 95 %.

## Por qué se hizo desde las ecuaciones publicadas

Los simuladores industriales de referencia (por ejemplo JKSimMet) son software cerrado. Este
proyecto **no** copia, descompila ni imita código, archivos, formatos o interfaz de ninguno:
todo sale de las ecuaciones de la literatura, documentadas una por una en
[`docs/teoria.md`](docs/teoria.md). Escribirlo así obliga a entender cada supuesto
(normalización de la fractura, interpolación de P80, criterio de convergencia del reciclo).

## Capturas

| Simulación (circuito cerrado directo) | Ajuste con muestreo sintético |
|---|---|
| ![Simulación](docs/img/app-simulacion.png) | ![Ajuste](docs/img/app-ajuste.png) |

## Cómo correrlo

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (Git Bash: source .venv/Scripts/activate); Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
streamlit run app/streamlit_app.py
```

Pruebas y estilo:

```bash
ruff check .
pytest --cov=conminucion --cov-report=term-missing
```

Caso de validación cruzada (regenera `docs/caso-validacion-modsim.md`):

```bash
python -m conminucion.validacion
```

Uso como librería:

```python
from conminucion.sizes import SizeGrid, rosin_rammler
from conminucion.stream import Stream
from conminucion.mill import BallMill
from conminucion.classifier import EfficiencyCurve
from conminucion.circuits import CircuitConfig, simulate

grid = SizeGrid.geometric(top=9500, n=17)
fresh = Stream.from_fractions(grid, rosin_rammler(grid, 3200, 1.0), tph=100)
res = simulate("cerrado_directo", CircuitConfig(fresh, BallMill(), EfficiencyCurve(100, 3.0, 0.2)))
print(res.table(), res.circulating_load, res.bond_kwh_t)
```

## Qué incluye

- Clases de tamaño, generadores Rosin-Rammler y Gaudin-Schuhmann, P80/F80 log-lineales.
- Fractura de Austin-Klimpel-Luckie normalizada (columnas suman 1, demostrado en teoría).
- Molino de mezcla perfecta con (r/d) por nudos o función de selección de Austin, N mezcladores.
- Curva de eficiencia de Whiten/Lynch-Rao con bypass de Kelsall (ciclón y harnero).
- Solucionador secuencial-modular con corrientes de corte y Wegstein opcional.
- Reconciliación de nodo por mínimos cuadrados ponderados con restricciones.
- Ajuste de d50c, α y Rf (ciclón) y de r/d por nudos (molino), IC por covarianza del jacobiano.
- Muestreo de planta sintético que comprueba la recuperación de parámetros dentro de su IC.
- App Streamlit con curvas de pasante, tabla de corrientes, carga circulante, energía y CSV.

## Alcance y limitaciones honestas

- **No reemplaza a un simulador industrial calibrado.** Los parámetros por defecto son
  razonables pero no están calibrados con datos reales de una planta.
- Un solo mineral (una densidad de sólidos), sin liberación ni mineralogía.
- El molino es de mezcla perfecta; no modela carga de bolas, potencia ni escalamiento.
- El ciclón usa una curva de eficiencia con d50c fijo: **no** predice d50c a partir de la
  geometría ni de la presión (ver fase 2).
- Los IC por jacobiano son una aproximación lineal; cerca de cotas (Rf = 0) son optimistas.
  La partición derivada de datos reconciliados tiene errores heterocedásticos y su cobertura
  real es menor que la nominal (se observó ~50-80 % en simulaciones de prueba); la
  recuperación dentro de IC está garantizada y probada para la curva de partición medida y
  para los nudos del molino.
- El caso de validación contra MODSIM 3.6 queda **pendiente de que el usuario cargue los
  datos** y complete la columna «MODSIM»; no se han comparado números todavía.
- La energía de Bond usa Wi constante, sin factores de corrección de eficiencia.
- Las páginas exactas de algunas referencias (Kelsall, Bond, Lynch-Rao) no fueron
  verificadas contra el original.

## Fase 2

- **Hidrociclón de Plitt (1976)** como estimador de d50c, nitidez y partición de agua: **no se
  implementó**. Las constantes publicadas no coinciden entre las fuentes accesibles por web
  (p. ej. constante de d50c 50,5 en la documentación de SysCAD frente a 39,7 en otras
  fuentes; constante de la partición de agua 1,9 frente a 3,29 con distinto término de
  presión; además hay versiones con otras unidades y la corrección de Flintoff 1987). Como no
  hay dos fuentes independientes que coincidan y no se tuvo acceso al artículo original (CIM
  Bulletin 69(776), 114-123), no se inventan constantes.
- Molino SAG/AG, chancadoras (modelo de Whiten/Andersen-Awachie), flotación.
- Bootstrap de residuos como alternativa de IC.
- Mezcla de varios minerales y densidades distintas.

## Estructura

```
conminucion/   sizes, stream, fracture, mill, classifier, bond, units, flowsheet,
               circuits, reconcile, fitting, synthetic, validacion
app/           streamlit_app.py
docs/          teoria.md, caso-validacion-modsim.md, img/
tests/         pytest (cobertura >= 90 %)
```

Licencia MIT. Construido con desarrollo asistido por IA (Claude Code), con revisión y pruebas propias.
