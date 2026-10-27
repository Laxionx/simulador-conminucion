"""Textos en español de los datos reales: la carga de CSV/XLSX (claves `carga.*`), el ajuste a un
muestreo de molienda (`mu.*`) y la calibración del chancador con la planta (`plant.*`)."""

T = {
    # ------------------------------------------------------------ carga de archivos
    "carga.aviso": (
        "Lo que subes viaja a los servidores de Streamlit y no se guarda; para datos de una "
        "empresa, usa la app en local (`streamlit run app/streamlit_app.py`, ver el README)."
    ),
    "carga.label": "Subir un archivo (CSV o XLSX)",
    "carga.help": (
        "Máximo 1 MB y 500 filas. CSV con «;» y coma decimal (Excel en español) o con «,» y punto "
        "decimal (Excel en inglés), en UTF-8 o Latin-1. XLSX: la primera hoja, con los encabezados "
        "en la primera fila; no se evalúan fórmulas, se usa el valor guardado. Los encabezados "
        "pueden estar en español o en inglés."
    ),
    "carga.plantilla": "Descargar plantilla (CSV)",
    "carga.ok": "Archivo leído: {n} filas. Los datos están en la tabla de abajo; puedes editarla.",
    "carga.err.ext": "Solo se aceptan archivos .csv y .xlsx (no .xls ni .xlsm).",
    "carga.err.tamano": "El archivo es demasiado grande: el máximo es 1 MB.",
    "carga.err.filas": "El archivo tiene demasiadas filas: el máximo es {max}.",
    "carga.err.faltan": "Faltan columnas obligatorias en el archivo: {cols}.",
    "carga.err.celda": (
        "La fila {fila} no tiene un número en la columna «{col}» (celda vacía, texto, fecha o "
        "valor no finito)."
    ),
    "carga.err.ilegible": "No se pudo leer el archivo: no es un CSV ni un XLSX válido.",
    "carga.err.vacio": "El archivo no tiene filas de datos.",
    "carga.err.xml": "No se puede leer un XLSX en este servidor (falta el lector seguro de XML).",
    # ------------------------------------------------------------ muestreo real: fuente y datos
    "mu.fuente.label": "Fuente de los datos",
    "mu.fuente.sintetico": "Muestreo sintético (como hasta ahora)",
    "mu.fuente.tus": "Tus datos",
    "mu.fuente.vazante": "Vazante, campaña 1 (publicado)",
    "mu.fuente.help": (
        "Sintético: datos generados con parámetros conocidos. Tus datos: una tabla que pegas o "
        "subes. Vazante: el muestreo de ciclones de Costa, Bergerman y Delboni Jr. (2024)."
    ),
    "mu.intro.tus": (
        "Pega la tabla desde Excel o sube un archivo: una fila por tamiz (µm, de mayor a menor) "
        "con el **% pasante acumulado** de la alimentación, el underflow y el overflow del "
        "ciclón. Opcional: el pasante de la alimentación y la descarga del molino. La tabla "
        "trae precargado el muestreo de Vazante como ejemplo: reemplázalo con el tuyo."
    ),
    "mu.intro.vazante": (
        "Muestreo balanceado de la campaña 1 (abril 2022) de la planta de Vazante (Nexa "
        "Resources, Brasil), con ciclones solos. Fuente: Costa, Bergerman y Delboni Jr. (2024), "
        "*Minerals* 14(7), 707, Tabla A3. Es el caso de la validación C2."
    ),
    "mu.h.datos": "Datos del muestreo",
    "mu.tabla.ayuda": (
        "Tamices decrecientes en µm; los % son pasantes acumulados (0–100, que no suben al ir a "
        "tamices más finos). Hasta 500 filas."
    ),
    "mu.sol.usar": "Tengo el % de sólidos de las tres corrientes",
    "mu.sol.usar.help": (
        "Con los % de sólidos se usa el método validado con Vazante: Rf = agua que va a gruesos, "
        "por el balance de agua. Sin ellos, Rf se ajusta libre y su IC es más ancho."
    ),
    "mu.sol.alim": "% sólidos de la alimentación",
    "mu.sol.uf": "% sólidos del underflow",
    "mu.sol.of": "% sólidos del overflow",
    "mu.col.clase": "Clase (µm)",
    "mu.err.menos": "Se necesitan al menos {min} mallas con datos.",
    "mu.err.filas": (
        "Las columnas no tienen el mismo número de filas con datos: tamiz {tamiz}, alimentación "
        "{alim}, underflow {uf}, overflow {of}."
    ),
    "mu.err.filas_molino": (
        "Los datos del molino deben venir completos o ninguno: {n} mallas, alimentación del molino "
        "{alim} filas, descarga {desc}."
    ),
    "mu.err.tamices": "Los tamices deben ser positivos y decrecientes (de mayor a menor).",
    "mu.err.rango": "La columna «{col}» tiene valores fuera de 0–100 %.",
    "mu.err.monotono": (
        "La columna «{col}» no es un acumulado: sube al pasar al tamiz de {tamiz} µm."
    ),
    "mu.err.solidos": "Los % de sólidos deben estar entre 0 y 100, sin incluirlos.",
    "mu.err.utiles": (
        "Quedan {n} clases útiles para ajustar la partición (se usan las de tamiz superior hasta "
        "{corte} µm, con alimentación suficiente) y se necesitan al menos {min}."
    ),
    "mu.err.ajuste": "El ajuste de la partición no converge con estos datos.",
    "mu.err.molino": (
        "No se pudo ajustar el molino: faltan datos para los r/d por nudos (se necesitan al menos "
        "6 mallas) o no converge."
    ),
    # ------------------------------------------------------------ muestreo real: estado
    "mu.h.estado": "Estado del muestreo",
    "mu.est.chi2.ok": (
        "Coherencia global: χ² = {chi2} no supera el crítico al 95 % ({crit}, {gl} grados de "
        "libertad)."
    ),
    "mu.est.chi2.mal": (
        "Coherencia global: χ² = {chi2} supera el crítico al 95 % ({crit}, {gl} grados de "
        "libertad): los datos no cuadran con un balance dentro del ruido supuesto."
    ),
    "mu.est.chi2.ayuda": (
        "Definición estadística: χ² = Σ ((medido − reconciliado)/σ)² sobre las tres "
        "granulometrías, con σ = máx(5 % del valor; 0,002) (supuesto declarado). Grados de "
        "libertad = n + 2 (n balances de clase y 3 sumas, menos R). Crítico = percentil 95 de la "
        "distribución χ²."
    ),
    "mu.est.z.ok": (
        "Mayor ajuste estandarizado: z = {z} en {corriente}, clase {inf}–{sup} µm; no pasa de 3σ."
    ),
    "mu.est.z.mal": (
        "Mayor ajuste estandarizado: z = {z} en {corriente}, clase {inf}–{sup} µm; pasa de 3σ."
    ),
    "mu.est.z.ayuda": (
        "z = (medido − reconciliado)/σ, con la clase entre dos tamices (el acumulado se pasa a "
        "retenido). Criterio estadístico de 3σ. Ojo: el balance reparte un error entre las tres "
        "corrientes; en pruebas con un error plantado, el z más grande cayó en la malla "
        "correcta pero en la alimentación y bajo 3σ. Sirve para ver DÓNDE se corrige más, no "
        "para decir qué corriente está mal."
    ),
    "mu.est.todo_ok": "Muestreo coherente: el χ² y el mayor ajuste están dentro de lo esperado.",
    "mu.params.nota": (
        "Los IC salen de una aproximación lineal (jacobiano): un límite negativo en d50c o α "
        "indica que, con tan pocos puntos, el IC no es fiable."
    ),
    "mu.nota.diagnostico": (
        "El χ² y el z dicen cuánto se tuvo que corregir, no qué corriente está mal: en la prueba "
        "con un error plantado de +4 puntos, el χ² solo superó su crítico en 1 de 3 casos y el "
        "mayor z cayó en la malla correcta pero en la alimentación. Por eso no se sugiere qué "
        "re-muestrear."
    ),
    "mu.m.r": "R (sólidos al underflow)",
    "mu.m.r.help": "Fracción de los sólidos de la alimentación que sale por el underflow.",
    "mu.m.cl": "Carga circulante",
    "mu.m.cl.help": "Sólidos del underflow / sólidos del overflow (= alimentación fresca).",
    "mu.m.chi2": "χ² ponderado",
    "mu.m.chi2.help": "Σ ((medido − reconciliado)/σ)². Se compara con el crítico en el panel.",
    "mu.m.cierre": "Cierre antes → después",
    "mu.m.cierre.help": (
        "Mayor |f − (R·u + (1 − R)·o)| entre las clases, en puntos porcentuales: con lo medido "
        "(antes) y con lo reconciliado (después, cero por construcción)."
    ),
    "mu.m.z": "Mayor |z|",
    "mu.m.z.help": "El mayor ajuste estandarizado de todas las corrientes y clases.",
    "mu.m.ic": "Ancho IC95 % de d50c",
    "mu.m.ic.help": (
        "Ancho del intervalo de confianza al 95 % de d50c del ajuste libre (aproximación lineal "
        "por el jacobiano). Se muestra sin umbral."
    ),
    # ------------------------------------------------------------ muestreo real: resultados
    "mu.h.gran": "Granulometrías medidas y reconciliadas",
    "mu.gran.caption": (
        "% retenido por clase (la clase de una fila va entre su tamiz y el siguiente). z = "
        "(medido − reconciliado)/σ."
    ),
    "mu.col.alim": "alimentación",
    "mu.col.uf": "underflow",
    "mu.col.of": "overflow",
    "mu.col.medido": "{corriente} medido",
    "mu.col.reconc": "{corriente} reconciliado",
    "mu.col.z": "z {corriente}",
    "mu.plot.size": "Tamaño (µm)",
    "mu.plot.pass": "Pasante acumulado (%)",
    "mu.plot.medido": "{corriente}, medido",
    "mu.plot.reconc": "{corriente}, reconciliado",
    "mu.h.part": "Partición al underflow: medida y ajustada",
    "mu.plot.part.y": "Partición al underflow (%)",
    "mu.plot.part.medida": "medida (datos reconciliados), usada en el ajuste",
    "mu.plot.part.fuera": "medida, fuera del ajuste",
    "mu.plot.part.ajustada": "ajustada",
    "mu.plot.part.libre": "ajuste libre (Rf libre)",
    "mu.metodo.fijo": (
        "Con % de sólidos: método validado con Vazante (Rf = agua a gruesos por el balance de "
        "agua; d50c y α por mínimos cuadrados). El ajuste libre de las tres, con su IC95 %, es "
        "informativo."
    ),
    "mu.metodo.libre": (
        "Sin % de sólidos: Rf, d50c y α se ajustan libres a la partición medida, con su IC95 %. "
        "El Rf libre suele tener un IC ancho; con los % de sólidos se fija con el balance de agua."
    ),
    "mu.metodo.clases": (
        "Se ajustan las {n} clases con tamiz superior de hasta {corte} µm y alimentación "
        "suficiente (criterio de la validación). Los puntos huecos no entran."
    ),
    "mu.h.params": "Parámetros de la partición",
    "mu.p.param": "parámetro",
    "mu.p.valor": "valor del método",
    "mu.p.libre": "ajuste libre",
    "mu.p.lo": "IC95 inf (libre)",
    "mu.p.hi": "IC95 sup (libre)",
    "mu.pub": (
        "Publicado: d50c = {d50c} µm (esta app: {mio}, diferencia {dd} %) y α = {a} (esta app: "
        "{amio}, diferencia {da} %)."
    ),
    "mu.h.molino": "Molino: r/d por nudos",
    "mu.molino.nota": (
        "Ajuste de los r/d de los nudos ({nudos} µm) a la alimentación y descarga del molino, con "
        "la fractura y los mezcladores de la barra lateral (supuestos de la app, no medidos)."
    ),
    "mu.molino.param": "nudo (µm)",
    "mu.molino.rd": "r/d estimado",
    "mu.molino.lo": "IC95 inf",
    "mu.molino.hi": "IC95 sup",
    # ------------------------------------------------------------ chancador: comparar con la planta
    "plant.h": "Comparar con tu planta",
    "plant.intro": (
        "Dos datos opcionales medidos en la planta **con las condiciones de los controles de "
        "arriba**: la capacidad y el P80 del producto del chancador (sin los finos de la "
        "parrilla). Con la capacidad se calibra la densidad aparente efectiva k; con el P80 se "
        "estima el desgaste."
    ),
    "plant.q.label": "Capacidad medida (t/h)",
    "plant.q.help": "Toneladas por hora que procesa el chancador en esas condiciones.",
    "plant.p80.label": "P80 medido del producto del chancador (mm)",
    "plant.p80.help": "P80 del producto del chancador, sin los finos que pasan por la parrilla.",
    "plant.q.res": (
        "Capacidad del modelo con el k de King: {modelo} t/h; medida: {medido} t/h (diferencia "
        "{delta} %). Factor de planta f = medido / modelo = {f}, que da k de la planta = k · f = "
        "{kplanta} t/m³."
    ),
    "plant.q.motor": (
        "El modelo dice que el motor limita (la potencia permite {motor} t/h y el límite "
        "volumétrico es {vol} t/h): con esa medición no se puede calibrar k."
    ),
    "plant.q.motor2": (
        "Lo medido ({medido} t/h) supera lo que permite el motor en el modelo ({motor} t/h): con "
        "esa medición no se puede calibrar k. Revisa la potencia instalada, el Wi o las "
        "condiciones."
    ),
    "plant.q.rango": "Factor f = {f}, fuera de {lo}–{hi}: revisa unidades o condiciones.",
    "plant.btn.usar": "Usar mi calibración",
    "plant.btn.king": "Volver al k de King",
    "plant.cal.activa": "Calibrado con tu planta (f = {f}): k = {k} t/m³ en vez de {k0} t/m³.",
    "plant.cal.curvas": (
        "Calibrado con tu planta (f = {f}): las capacidades de las curvas y de los indicadores "
        "usan k · f."
    ),
    "plant.p80.res": (
        "OSS implícito = P80 medido / (P80/OSS de Nordberg = {razon}) = {oss} mm; OSS nominal = "
        "CSS + δ + carrera = {nominal} mm. Diferencia = {dif} mm."
    ),
    "plant.p80.desgaste": "Desgaste estimado: δ = {wear} mm (el control tiene {actual} mm).",
    "plant.p80.neg": (
        "Producto más fino que la curva de Nordberg: revisa el muestreo o el ajuste."
    ),
    "plant.p80.fuera": "El desgaste estimado ({wear} mm) queda fuera del rango del control (0–{hi}).",
    "plant.p80.nota": (
        "La inversa usa la curva de Nordberg aunque el modelo de producto elegido sea otro."
    ),
    "plant.btn.desgaste": "Poner ese desgaste en el control",
}
