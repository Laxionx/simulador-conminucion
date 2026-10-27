"""Textos en español de las pestañas Simulación y Ajuste y de sus gráficos."""

T = {
    "page.title": "Simulador de conminución",
    "app.title": "Simulador de circuitos de molienda y clasificación",
    "app.caption": (
        "Construido desde ecuaciones publicadas (Whiten, Austin, Lynch-Rao, Bond). Empieza por "
        "la **Guía**; los datos se cambian en la barra lateral."
    ),
    "err.generic": "Algo falló al calcular. Prueba con otros datos o recarga la página.",
    "toggle.label": "Mover los equipos",
    "toggle.help": (
        "Apaga las animaciones de los esquemas. También se apagan solas si el sistema tiene "
        "activado «reducir movimiento»."
    ),
    "tab.guide": "Guía",
    "tab.sim": "Simulación",
    "tab.fit": "Ajuste a datos",
    "method.wegstein": "Wegstein",
    "method.succ": "Sustitución sucesiva",
    # ------------------------------------------------------------ simulación
    "m.p80": "P80 del producto (µm)",
    "m.cl": "Carga circulante",
    "m.bond": "Energía de Bond (kWh/t)",
    "m.iter": "Iteraciones",
    "sim.h.energy": "#### Energía del molino",
    "sim.h.equip": "#### Los equipos por dentro",
    "sim.h.streams": "#### Corrientes",
    "e.avail": "Energía que entrega el molino (kWh/t)",
    "e.avail.help": "Potencia de Bond-Rowland dividida por las t/h frescas.",
    "e.need": "Energía que pide Bond para este P80 (kWh/t)",
    "e.need.help": "W = 10 Wi (1/√P80 − 1/√F80), sin factores de eficiencia de Rowland.",
    "e.yes": "alcanza",
    "e.no": "no alcanza",
    "e.caption": (
        "Según Bond, el molino **{verdict}** para moler hasta este P80 ({ratio} veces lo pedido). "
        "Chequeo grueso: la cinética del molino (τ, selección) no depende de su potencia en este "
        "modelo."
    ),
    "sim.alt.flow": "Diagrama de flujo del circuito",
    "sim.alt.mill": "Molino de bolas en corte",
    "sim.alt.cyclone": "Hidrociclón",
    "sim.journey": (
        "Aprieta «Reproducir»: cada paso agrega una etapa del recorrido, incluida la salida de "
        "cada mezclador del molino."
    ),
    "sim.balance": (
        "Balance: sólidos in {in_} / out {out} t/h (error {err}); agua agregada {water} t/h."
    ),
    "sim.dl.streams": "Exportar corrientes (CSV)",
    "sim.dl.passing": "Exportar pasantes (CSV)",
    "conv.noconv": "{method} no converge en 500 iteraciones con estos datos.",
    "conv.caption": (
        "El reciclo arranca vacío. Cada iteración pasa el mineral por el molino y el ciclón y "
        "devuelve más gruesos, hasta que lo que vuelve ya no cambia: eso es la carga circulante "
        "final."
    ),
    "tcol.corriente": "corriente",
    "tcol.solidos_t_h": "solidos_t_h",
    "tcol.agua_t_h": "agua_t_h",
    "tcol.pct_solidos": "pct_solidos",
    "tcol.P80_um": "P80_um",
    "tcol.tamiz_um": "tamiz_um",
    "tid.alimentacion_fresca": "alimentacion_fresca",
    "tid.underflow": "underflow",
    "tid.alim_molino": "alim_molino",
    "tid.descarga_molino": "descarga_molino",
    "tid.alim_ciclon": "alim_ciclon",
    "tid.overflow": "overflow",
    "tid.producto": "producto",
    # ------------------------------------------------------------ ajuste
    "fit.intro": (
        "Muestreo de planta **sintético**: se generan datos con parámetros conocidos más ruido "
        "gaussiano y se comprueba que el ajuste los recupera dentro de su IC al 95 % "
        "(covarianza del jacobiano de `least_squares`)."
    ),
    "fit.seed": "Semilla",
    "fit.sigma": "Ruido de la partición (σ absoluta)",
    "fit.rel": "Ruido relativo de granulometrías",
    "fit.h1": "1. Ciclón: curva de partición medida",
    "fit.h2": "2. Reconciliación del nodo del ciclón",
    "fit.h3": "3. Molino: r/d por nudos desde alimentación y descarga",
    "fit.measured": "medido (sintético)",
    "fit.fitted": "ajustado",
    "fit.true": "verdadero",
    "fit.xlabel": "Tamaño (µm)",
    "fit.ylabel": "Partición al underflow",
    "fit.warn": "El circuito cerrado directo no se puede reconciliar con estos datos: {exc}",
    "fit.write": (
        "Fracción de sólidos al underflow: verdadera {true_r}, reconciliada {rec_r}. Carga "
        "circulante: verdadera {true_cl}, reconciliada {rec_cl} (χ² ponderado {chi2})."
    ),
    "fit.cap": (
        "La partición derivada de datos reconciliados tiene errores heterocedásticos; sus IC por "
        "jacobiano pueden ser optimistas (ver README)."
    ),
    "ci.param": "parámetro",
    "ci.true": "verdadero",
    "ci.est": "estimado",
    "ci.lo": "IC95 inf",
    "ci.hi": "IC95 sup",
    "ci.in": "dentro del IC",
    # ------------------------------------------------------------ gráficos
    "plot.play": "▶ Reproducir",
    "plot.pause": "⏸ Pausa",
    "plot.conv.name": "{label} ({n} iteraciones)",
    "plot.conv.note": "Iteración {k}: ",
    "plot.conv.title": "Cómo se llena el reciclo, iteración por iteración",
    "plot.conv.x": "Iteración",
    "plot.conv.y": "Carga circulante (underflow / fresca)",
    "plot.journey.mixer": "Molino: mezclador {i} de {n}",
    "plot.journey.mill": "Molino",
    "plot.journey.product": "Producto (descarga del molino)",
    "plot.journey.note": "Etapa {i} de {n}: {label}",
    "plot.journey.title": "El mineral a lo largo del circuito",
    "plot.size": "Tamaño (µm)",
    "plot.passing": "Pasante acumulado (%)",
    "plot.streams.title": "Granulometría de cada corriente",
    # ------------------------------------------------------------ nombres de las corrientes
    "stream.alimentacion_fresca": "Alimentación fresca",
    "stream.alim_molino": "Alimentación al molino",
    "stream.descarga_molino": "Descarga del molino",
    "stream.alim_ciclon": "Alimentación al ciclón",
    "stream.underflow": "Descarga del ciclón (gruesos)",
    "stream.overflow": "Rebalse (producto)",
    "stream.producto": "Producto",
}
