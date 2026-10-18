"""Textos en español de la pestaña «Ensayo de Bond» (claves `bond.*`)."""

T = {
    "tab.bond": "Ensayo de Bond",
    # ------------------------------------------------------------ ficha
    "bond.h.ficha": "#### Qué es esta pestaña",
    "bond.ficha.que": (
        "**Qué hace.** Muestra, ciclo a ciclo, cómo se hace el ensayo de Bond del molino de bolas "
        "(molino de laboratorio de 305 × 305 mm que gira a 70 rpm, con tamiz de cierre y 250 % de "
        "carga circulante) y de dónde sale el índice de trabajo **Wi**. Tiene dos partes: una "
        "**calculadora** con la contabilidad del procedimiento y una **simulación** del mismo "
        "ensayo con un modelo de molienda por lotes que solo conoce los dos primeros ciclos."
    ),
    "bond.ficha.datos": "**Datos que necesita** (la calculadora los pide abajo, con estos rangos).",
    "bond.ficha.ciclos": (
        "Además, una fila por ciclo con los **finos totales** pesados al final de cada ciclo "
        "(g que pasan el tamiz de cierre), entre 0 y {max} g, hasta {n} ciclos."
    ),
    "bond.ficha.devuelve": (
        "**Qué devuelve.** Por ciclo: alimentación nueva, revoluciones, finos de la alimentación y "
        "nuevos, gramos netos por revolución (Gbp) y carga circulante; al final, el Gbp (media de "
        "los últimos tres ciclos), si el criterio de término se cumple y el Wi en kWh/t. La "
        "simulación devuelve esas mismas cantidades calculadas con el modelo."
    ),
    "bond.ficha.fuentes": (
        "**Fuentes.** GMG (2021), *Guideline: Determining the Bond Efficiency of Industrial "
        "Grinding Circuits* (procedimiento, ecuación del Wi y criterio de término; abierta). "
        "Liang, Wei, Xu, Xia y Li (2016), *Study on the Selection of Comminution Circuits for a "
        "Magnetite Ore in Eastern Hebei, China*, Minerals 6(2), 39, "
        "[doi:10.3390/min6020039](https://doi.org/10.3390/min6020039) (CC BY; los 11 ciclos de la "
        "Tabla 2). Austin, Klimpel y Luckie (1984), *Process Engineering of Size Reduction: Ball "
        "Milling* (selección S y función de fractura). Una revisión de 2023, «The truth about "
        "population balance modeling», sostiene que un ensayo por lotes no predice el de ciclo "
        "cerrado en minerales heterogéneos: la simulación de abajo puede fallar, y se informa tal "
        "cual sale."
    ),
    "bond.ficha.supuestos": (
        "**Supuestos declarados.** (1) Las masas se redondean a 0,1 g, la resolución de una "
        "balanza. (2) La alimentación de la simulación es una curva Rosin-Rammler que pasa por dos "
        "puntos del artículo (F80 y el porcentaje bajo el tamiz); la curva completa del artículo "
        "es un gráfico y no se usó. (3) Grilla de tamaños casi √2 desde 3 350 µm, con el tamiz de "
        "cierre exacto en la grilla. (4) Tamizado ideal. (5) El modelo ajusta solo *a* y α de "
        "Austin; μ, Λ y la función de fractura quedan en los valores por defecto del simulador "
        "(un ejemplo típico de Austin et al., no medido para esta mena). (6) El llenado de bolas "
        "del dibujo sale de 20,125 kg de acero con la densidad y los huecos del simulador. "
        "(7) La constante del Wi es la de la guía (1,1023 × 44,5)."
    ),
    # ------------------------------------------------------------ datos de la calculadora
    "bond.campo.carga.label": "Carga del molino",
    "bond.campo.carga.meaning": "Masa de la carga: 700 cm³ de mineral compactado.",
    "bond.campo.carga.source": "se pesa en el laboratorio (GMG 2021, paso 5)",
    "bond.campo.finos_carga.label": "Finos de la carga inicial",
    "bond.campo.finos_carga.meaning": (
        "Masa de la carga inicial que ya pasa el tamiz de cierre; da la fracción de finos de la "
        "alimentación."
    ),
    "bond.campo.finos_carga.source": "se tamiza la carga inicial antes de moler",
    "bond.campo.rev1.label": "Revoluciones del ciclo 1",
    "bond.campo.rev1.meaning": "Revoluciones del primer ciclo; el procedimiento sugiere 100 a 150.",
    "bond.campo.rev1.source": "la fija el laboratorio (GMG 2021, paso 8)",
    "bond.campo.tamiz.label": "Tamiz de cierre",
    "bond.campo.tamiz.meaning": "Abertura del tamiz que separa el producto (P1).",
    "bond.campo.tamiz.source": "se elige al diseñar el ensayo",
    "bond.campo.f80.label": "F80 de la alimentación",
    "bond.campo.f80.meaning": "Tamaño bajo el cual pasa el 80 % de la alimentación.",
    "bond.campo.f80.source": "análisis granulométrico (tamizado) de la alimentación",
    "bond.campo.p80.label": "P80 del producto",
    "bond.campo.p80.meaning": (
        "Tamaño bajo el cual pasa el 80 % del producto de los últimos tres ciclos juntos."
    ),
    "bond.campo.p80.source": "análisis granulométrico del producto combinado",
    "bond.col.campo": "Dato",
    "bond.col.unit": "Unidad",
    "bond.col.range": "Rango",
    "bond.col.example": "Ejemplo (Hebei)",
    "bond.col.what": "Qué es",
    "bond.col.how": "Cómo se obtiene",
    # ------------------------------------------------------------ calculadora
    "bond.h.calc": "#### Calculadora del ensayo",
    "bond.calc.intro": (
        "Cada fila de la tabla es un ciclo: escribe los **finos totales** que pesaste al final. "
        "Las revoluciones del ciclo siguiente salen de la regla de GMG: *(IPP − finos que trae la "
        "alimentación nueva) / Gbp del ciclo anterior*, con IPP = carga / 3,5. La tabla viene "
        "cargada con el ensayo de Hebei."
    ),
    "bond.calc.example": "Volver al ejemplo de Hebei",
    "bond.edit.finos": "Finos totales < tamiz (g)",
    "bond.edit.help": "Gramos que pasan el tamiz de cierre al final del ciclo. Una fila por ciclo.",
    "bond.err.numero": "Algún dato no es un número válido: vuelve al ejemplo de Hebei.",
    "bond.err.rango": "Algún dato está fuera de su rango (ver la ficha).",
    "bond.err.filas": "La tabla debe tener entre {lo} y {hi} ciclos.",
    "bond.err.vacio": "Hay celdas vacías o con texto en la tabla de ciclos: complétalas con números.",
    "bond.err.finos": "Los finos de cada ciclo van de 0 g a la masa de la carga.",
    "bond.err.carga": "Los finos de la carga inicial deben ser menos que la carga.",
    "bond.err.tamaños": "Se requiere P80 del producto < tamiz de cierre < F80 de la alimentación.",
    "bond.err.calculo": (
        "Esos datos no cuadran: algún ciclo no produce finos nuevos (sus finos totales no superan "
        "los de su alimentación). Revisa la tabla."
    ),
    "bond.t.ciclo": "Ciclo",
    "bond.t.alim": "Alimentación nueva (g)",
    "bond.t.rev": "Revoluciones",
    "bond.t.total": "Finos totales (g)",
    "bond.t.dealim": "Finos de la alimentación (g)",
    "bond.t.nuevos": "Finos nuevos (g)",
    "bond.t.gbp": "Gbp (g/rev)",
    "bond.t.cl": "Carga circulante (%)",
    "bond.t.inv": "Invierte",
    "bond.yes": "sí",
    "bond.no": "no",
    "bond.calc.res": (
        "**Gbp final** (media de los últimos tres ciclos): **{gbp}** g/rev · IPP: {ipp} g · "
        "**Wi = {wi} kWh/t**."
    ),
    "bond.calc.fin.si": (
        "**Criterio de término:** se cumple desde el ciclo {k}: hay al menos cinco ciclos y el Gbp "
        "invirtió su dirección. La guía no fija una tolerancia numérica para «equilibrio», así que "
        "solo se evalúa la inversión."
    ),
    "bond.calc.fin.no": (
        "**Criterio de término:** todavía no se cumple (hacen falta al menos cinco ciclos y una "
        "inversión del Gbp)."
    ),
    "bond.calc.ref": "Referencia del artículo (Hebei): Gbp {gbp} g/rev y Wi {wi} kWh/t.",
    # ------------------------------------------------------------ simulación
    "bond.h.sim": "#### Simulación del ensayo de Hebei",
    "bond.sim.intro": (
        "Un modelo de molienda por lotes (*dw/dt = −S·w + B·S·w*, con la selección de Austin y su "
        "función de fractura) se ajusta **solo** a los finos nuevos de los ciclos 1 y 2: dos datos "
        "para dos parámetros, *a* = {a} 1/min y α = {alpha}. Con eso simula los 11 ciclos, con el "
        "tamizado ideal y la regla de GMG para las revoluciones, y se compara con lo medido. Los "
        "ciclos 3 a 11 son una predicción."
    ),
    "bond.sim.cycle": "Ciclo del ensayo",
    "bond.sim.cycle.help": "Elige el ciclo que muestra el molino.",
    "bond.sim.cap": (
        "Ciclo {k} de {n}: {rev} revoluciones a {rpm} rpm = {s} s de molienda · Gbp medido {gm} "
        "g/rev, simulado {gs} g/rev · carga circulante simulada {cl} %."
    ),
    "bond.sim.alt": "Molino de Bond de laboratorio girando a 70 rpm",
    "bond.sim.legend": (
        "Esquema, no a escala: las cantidades sí son del cálculo (giro del molino, llenado de "
        "bolas, revoluciones y Gbp de cada ciclo). La inclinación de la carga y la caída de las "
        "bolas son ilustrativas."
    ),
    "bond.h.res": "**Resultado frente a lo medido** (corte: ±{cut} %)",
    "bond.res.row": "{name}: simulado **{sim}**, medido {med} ({err} %) → {verdict}",
    "bond.res.gbp": "Gbp final",
    "bond.res.p80": "P80 del producto (µm)",
    "bond.res.wi": "Wi (kWh/t)",
    "bond.res.in": "dentro del corte",
    "bond.res.out": "fuera del corte",
    "bond.res.nota": (
        "Lo que no pasa el corte se deja tal cual, sin ajustar más parámetros para que cuadre: "
        "es un resultado negativo. El P80 simulado sale de interpolar el pasante en una grilla "
        "de tamaños y el Wi lo amplifica."
    ),
    "bond.plot.title": "Ensayo de Bond: medido frente a simulado",
    "bond.plot.x": "Ciclo",
    "bond.plot.y1": "Gramos netos por revolución, Gbp (g/rev)",
    "bond.plot.y2": "Carga circulante (%)",
    "bond.plot.med": "Medido",
    "bond.plot.sim": "Simulado",
    "bond.plot.note": "Ciclo {k} de {n} · Gbp medido {gm} · simulado {gs}",
}
