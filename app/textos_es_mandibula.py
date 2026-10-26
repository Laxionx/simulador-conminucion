"""Textos en español de la pestaña «Chancado primario» (claves `jaw.*`), del panel «Estado de la
operación» y de «Prueba esto» (claves `estado.*`, `prueba.*`, `sim.chk.*`, `sim.exp.*`)."""

T = {
    "tab.jaw": "Chancado primario",
    # ------------------------------------------------------------ componentes compartidos
    "estado.nivel.ok": "En rango",
    "estado.nivel.aviso": "Aviso",
    "estado.nivel.mal": "Problema",
    "estado.todo_ok": "Operación dentro de rango.",
    "estado.ver": "Ver los {n} chequeos en rango",
    "prueba.aplicar": "Aplicar este cambio a los controles",
    "prueba.restablecer": "Volver al ejemplo",
    # ------------------------------------------------------------ equipos y controles
    "jaw.h.equipos": "Equipos predefinidos",
    "jaw.equipos.intro": (
        "Elegir un equipo de la Tabla 3.1 de King fija su boca, ancho, rpm y kW; la altura de la "
        "cámara y la carrera salen de las reglas de AMIT 135, el CSS de un OSS de la tabla, y la "
        "alimentación es un SUPUESTO coherente con el tamaño. Después se puede cambiar todo."
    ),
    "jaw.equipo.label": "Equipo",
    "jaw.equipo.help": "Los 12 tamaños de la Tabla 3.1 de King (2000), o «Personalizado».",
    "jaw.equipo.personalizado": "Personalizado",
    "jaw.equipo.item": "{name} pulgadas · {kw} kW · {rpm} rpm",
    "jaw.oss.label": "OSS de la tabla (mm)",
    "jaw.oss.help": "Pone el CSS = OSS − carrera y la parrilla en esa abertura.",
    "jaw.h.controles": "Controles",
    "jaw.group.maquina": "Chancador",
    "jaw.group.alimentacion": "Alimentación y producto",
    "jaw.group.parrilla": "Parrilla y tolva",
    "jaw.reset": "Volver al ejemplo",
    "jaw.si_no": "sí / no",
    "jaw.si": "sí",
    "jaw.model.nordberg": "Nordberg (curva estándar)",
    "jaw.model.whiten": "Whiten (sin validar para mandíbula)",
    "jaw.campo.model.label": "Modelo del producto",
    "jaw.campo.model.meaning": (
        "Curva estándar de Nordberg (1976) o ciclo de fractura de Whiten con los parámetros del "
        "cono de MODSIM; este último no pasa la validación para mandíbula."
    ),
    "jaw.campo.grizzly.label": "Parrilla antes del chancador",
    "jaw.campo.grizzly.meaning": (
        "Con parrilla, los finos pasan directo a la correa y solo lo retenido entra a la cámara."
    ),
    "jaw.campo.gape.label": "Boca",
    "jaw.campo.gape.meaning": "Abertura de alimentación G, entre las dos mandíbulas arriba.",
    "jaw.campo.width.label": "Ancho",
    "jaw.campo.width.meaning": "Ancho de la cámara W (la otra dimensión del equipo).",
    "jaw.campo.height.label": "Altura de la cámara",
    "jaw.campo.height.meaning": "Altura D de la cámara; por regla, el doble de la boca.",
    "jaw.campo.stroke.label": "Carrera",
    "jaw.campo.stroke.meaning": "Carrera L en la descarga; OSS = CSS efectivo + carrera.",
    "jaw.campo.css.label": "CSS (lado cerrado)",
    "jaw.campo.css.meaning": "Abertura de descarga con la mandíbula más cerca, sin desgaste.",
    "jaw.campo.wear.label": "Desgaste de las placas",
    "jaw.campo.wear.meaning": "Suma al CSS: el CSS efectivo es CSS + desgaste.",
    "jaw.campo.rpm.label": "Velocidad del eje",
    "jaw.campo.rpm.meaning": "Golpes por minuto N; sobre la velocidad crítica Nc la capacidad cae.",
    "jaw.campo.mu.label": "Roce roca-placa μ",
    "jaw.campo.mu.meaning": "La roca muerde si el ángulo de mordida no supera 2·arctan μ.",
    "jaw.campo.power.label": "Potencia instalada",
    "jaw.campo.power.meaning": "Motor del chancador; limita la alimentación por energía de Bond.",
    "jaw.campo.tph.label": "Alimentación de mina",
    "jaw.campo.tph.meaning": "Sólidos que llegan a la parrilla (o a la boca, sin parrilla).",
    "jaw.campo.rho.label": "Densidad del sólido ρs",
    "jaw.campo.rho.meaning": (
        "Escala la densidad aparente efectiva k = 1,815·ρs/2,7 (mismo llenado que el ajuste)."
    ),
    "jaw.campo.top.label": "Tamaño máximo de la alimentación",
    "jaw.campo.top.meaning": "La roca más grande que trae la mina; sobre 0,8·boca son colpas.",
    "jaw.campo.f80.label": "F80 de la alimentación",
    "jaw.campo.f80.meaning": "Tamaño bajo el cual está el 80 % de la masa de la mina.",
    "jaw.campo.n.label": "n de Rosin-Rammler",
    "jaw.campo.n.meaning": "Ancho de la distribución de la mina: n bajo = más finos y más gruesos.",
    "jaw.campo.wi.label": "Wi de impacto",
    "jaw.campo.wi.meaning": "Índice de trabajo del mineral para la energía de Bond del chancador.",
    "jaw.campo.grz_ap.label": "Abertura de la parrilla",
    "jaw.campo.grz_ap.meaning": "Tamaño al que pasa la mitad de cada clase (d50 de la partición).",
    "jaw.campo.hopper.label": "Tolva",
    "jaw.campo.hopper.meaning": "Toneladas que caben antes de rebalsar, para el tiempo a rebalse.",
    "jaw.src.king_tn5": "de King (2000), Technical Notes 5 y Tabla 3.1",
    "jaw.src.amit135": "de las notas AMIT 135 (Univ. de Alaska Fairbanks)",
    "jaw.src.karra_king": "de la partición de Karra (notas de King)",
    "jaw.src.definicion": "es un dato de entrada del caso",
    "jaw.src.supuesto": "es un SUPUESTO, sin fuente en los documentos revisados",
    "jaw.err.numero": "Hay un valor que no es un número válido.",
    "jaw.err.rango": "Hay un valor fuera del rango de su control.",
    "jaw.err.boca": "La boca debe ser mayor que el OSS (CSS + desgaste + carrera).",
    "jaw.err.f80": "El F80 debe ser menor que el tamaño máximo de la alimentación.",
    "jaw.err.rr": "Con esa n, el F80 queda demasiado cerca del tamaño máximo: baja el F80 o sube n.",
    "jaw.err.modelo": "El modelo rechazó estos datos: {msg}",
    # ------------------------------------------------------------ indicadores y estado
    "jaw.m.cap": "Capacidad (t/h)",
    "jaw.m.cap.help": "Capacidad efectiva: la menor entre la capacidad de la cinemática y el límite del motor.",
    "jaw.m.util": "Utilización",
    "jaw.m.util.help": "Alimentación al chancador dividida por la capacidad efectiva.",
    "jaw.m.p80": "P80 producto (mm)",
    "jaw.m.p80.help": "P80 del producto total: producto del chancador más lo que pasó por la parrilla.",
    "jaw.m.pot": "Potencia (kW)",
    "jaw.m.pot.help": "Potencia de Bond (+ vacío) / instalada, en kW: energía de Bond por la alimentación al chancador.",
    "jaw.m.nnc": "N / Nc",
    "jaw.m.nnc.help": "Rpm sobre velocidad crítica; sobre 1 la capacidad se reduce.",
    "jaw.m.ang": "Mordida θ (°)",
    "jaw.m.ang.help": "Ángulo de mordida / límite, en °: θ = arctan((G − CSS efectivo)/D) frente a 2·arctan μ.",
    "jaw.h.estado": "Estado de la operación",
    "jaw.fuente": "Fuente: {fuente}.",
    "jaw.chk.rebalse": "La tolva se llena en {min} min.",
    "jaw.chk.no_muerde": "Ángulo de mordida θ = {theta}° frente al límite 2·arctan μ = {limite}°.",
    "jaw.chk.velocidad_critica": (
        "N = {rpm} rpm; velocidad crítica Nc = {nc} rpm; factor de velocidad {f}."
    ),
    "jaw.chk.rpm_fuera_de_rango": "N = {rpm} rpm; rango usual {min}–{max} rpm.",
    "jaw.chk.carrera_fuera_de_rango": "Carrera de {carrera} cm; rango usual {min}–{max} cm.",
    "jaw.chk.colpas": "Alimentación sobre 0,8·boca ({tam} mm): {pct} % de la masa.",
    "jaw.chk.razon_reduccion": "Razón de reducción F80/P80 = {razon}; rango usual {min}:1 a {max}:1.",
    "jaw.chk.sobrecarga": (
        "Alimentación al chancador {alim} t/h; capacidad efectiva {cap} t/h; utilización {util} %."
    ),
    "jaw.chk.potencia": "Potencia de Bond {req} kW; instalada {inst} kW.",
    "jaw.crit.no_muerde": (
        "Problema si θ supera 2·arctan μ: la roca resbala y no entra. μ es un SUPUESTO."
    ),
    "jaw.crit.velocidad_critica": (
        "Aviso si N supera Nc: la roca no alcanza a caer entre golpes y la capacidad se "
        "multiplica por (Nc/N)²."
    ),
    "jaw.crit.rpm_fuera_de_rango": "Aviso si N está fuera de 100–359 rpm.",
    "jaw.crit.carrera_fuera_de_rango": "Aviso si la carrera está fuera de 1–7 cm.",
    "jaw.crit.colpas": (
        "Aviso si algo de la alimentación supera 0,8·boca (AMIT: 0,8–0,9): puede trabar la boca."
    ),
    "jaw.crit.razon_reduccion": "Aviso si F80/P80 queda fuera de 4:1 a 9:1.",
    "jaw.crit.sobrecarga": (
        "Problema si la alimentación al chancador supera la capacidad efectiva: la tolva se llena."
    ),
    "jaw.crit.potencia": "Problema si la potencia de Bond (más el vacío) supera la instalada.",
    "jaw.fuente.king_tn5": "King (2000), Technical Notes 5: Crushers, y Tabla 3.1 (MODSIM)",
    "jaw.fuente.amit135": "Notas AMIT 135, Lección 5, Univ. de Alaska Fairbanks",
    "jaw.fuente.nordberg_1976": "Nordberg (1976), curva estándar de producto (MODSIM JAW1)",
    "jaw.fuente.karra_king": "Karra, en las notas de King sobre harneros (ec. 4-42)",
    "jaw.fuente.rose_english": "Rose y English (1967), en Gupta y Yan (2016), cap. 4",
    "jaw.fuente.taggart": "Taggart, fórmula empírica de capacidad",
    "jaw.fuente.bond_1952": "Bond (1952), energía específica",
    "jaw.fuente.definicion": "Definición geométrica o balance de masa, sin parámetros",
    "jaw.fuente.supuesto": "SUPUESTO declarado, sin fuente en los documentos revisados",
    "jaw.king": (
        "Tabla de King ({name} pulgadas, OSS {oss} mm): {q} t/h · modelo: {m} t/h ({d} %)."
    ),
    # ------------------------------------------------------------ esquema
    "jaw.h.esquema": "Esquema del chancador",
    "jaw.vista.label": "Vista",
    "jaw.vista.help": "Corte completo, o el detalle de la descarga (el mismo dibujo, acercado).",
    "jaw.vista.completo": "Corte completo",
    "jaw.vista.detalle": "Detalle de la descarga",
    "jaw.amp.label": "Amplificar la carrera (×)",
    "jaw.amp.help": "Solo cambia el dibujo: la carrera real es chica frente a la cámara.",
    "jaw.vel.label": "Velocidad de la animación (%)",
    "jaw.vel.help": "Solo cambia el dibujo: al 100 % el vaivén sería el real, demasiado rápido.",
    "jaw.ab.texto": (
        "La abertura de descarga oscila entre el CSS efectivo ({css} mm) y el OSS ({oss} mm), "
        "una carrera de {l} mm, en un ciclo de {s} s."
    ),
    "jaw.svg.label": "Corte lateral de un chancador de mandíbula de toggle simple",
    "jaw.svg.g": "boca G = {v} mm",
    "jaw.svg.d": "altura D = {v} mm",
    "jaw.svg.css": "CSS = {v} mm",
    "jaw.svg.oss": "OSS = {v} mm",
    "jaw.svg.theta": "θ = {v}°",
    "jaw.svg.fija": "mandíbula fija",
    "jaw.svg.volante": "volante y excéntrico",
    "jaw.svg.toggle": "placa de toggle",
    "jaw.svg.barra": "barra tensora y resorte",
    "jaw.svg.camara": "cámara en V",
    "jaw.svg.parrilla": "parrilla vibratoria",
    "jaw.svg.correa": "correa de producto",
    "jaw.svg.leg.fino": "≤ CSS: {p} % de la masa",
    "jaw.svg.leg.css_oss": "entre CSS y OSS: {p} %",
    "jaw.svg.leg.grueso": "mayor que el OSS: {p} %",
    "jaw.svg.leg.colpa": "colpa (> 0,8·boca): {p} %",
    "jaw.svg.prod": "Producto: {p} % bajo el OSS",
    "jaw.svg.finos": "finos de la parrilla → correa",
    "jaw.svg.prodtot": "producto total: {t} t/h · P80 {p} mm",
    "jaw.svg.solo2": "solo cambia el dibujo",
    "jaw.svg.title": "Chancador de mandíbula",
    "jaw.svg.dims": "Boca × ancho: {g} × {w} mm",
    "jaw.svg.rpm": "{rpm} rpm = un ciclo cada {p} s",
    "jaw.svg.view": "En el dibujo: {p} s por ciclo ({v} %)",
    "jaw.svg.stroke": "Carrera real {l} mm, dibujada ×{a}",
    "jaw.svg.note1": "De {m} cuantiles se dibujan las {n}",
    "jaw.svg.note2": "que caben sin encimarse. A escala.",
    "jaw.svg.note3": "Correa: {a} cuantiles del producto",
    "jaw.svg.note4": "y {b} de los finos de la parrilla.",
    "jaw.svg.solo": "Carrera ×{a}, velocidad {v} %:",
    "jaw.svg.ab.title": "Abertura de descarga en el tiempo",
    "jaw.svg.ab.x": "dos ciclos = {s} s a {n} rpm (velocidad real)",
    "jaw.svg.ab.label": "Abertura de descarga entre el CSS y el OSS en dos ciclos",
    # ------------------------------------------------------------ curvas y balance
    "jaw.h.curvas": "Curvas",
    "jaw.plot.mina": "Alimentación de mina",
    "jaw.plot.pasante": "Pasante de la parrilla",
    "jaw.plot.carga": "Alimentación al chancador",
    "jaw.plot.prod": "Producto del chancador",
    "jaw.plot.total": "Producto total",
    "jaw.plot.css": "CSS",
    "jaw.plot.oss": "OSS",
    "jaw.plot.gran.title": "Granulometría de cada corriente",
    "jaw.plot.gran.x": "Tamaño (mm)",
    "jaw.plot.gran.y": "Pasante acumulado (%)",
    "jaw.plot.cap.title": "Capacidad del chancador",
    "jaw.plot.cap.y": "Capacidad (t/h)",
    "jaw.plot.cap.modelo": "Modelo (cinemática)",
    "jaw.plot.cap.punto": "Punto de operación",
    "jaw.plot.cap.llega": "Llega al chancador",
    "jaw.plot.cap.potencia": "Límite por potencia",
    "jaw.plot.cap.nc": "Nc",
    "jaw.plot.cap.taggart": "Taggart",
    "jaw.plot.cap.king": "Tabla de King",
    "jaw.plot.cap.x.rpm": "Velocidad del eje (rpm)",
    "jaw.plot.cap.x.css": "CSS (mm)",
    "jaw.eje.label": "Eje de la capacidad",
    "jaw.eje.help": "Capacidad según las rpm, o según el CSS con Taggart y la Tabla de King.",
    "jaw.eje.rpm": "rpm",
    "jaw.eje.css": "CSS",
    "jaw.curvas.nota": (
        "Los puntos de la Tabla de King solo aparecen si la boca y el ancho son los de uno de los "
        "12 equipos."
    ),
    "jaw.h.balance": "Balance de masa",
    "jaw.bal.corriente": "Corriente",
    "jaw.bal.tph": "Sólidos (t/h)",
    "jaw.bal.p80": "P80 (mm)",
    "jaw.bal.p50": "P50 (mm)",
    "jaw.bal.css": "Bajo el CSS (%)",
    "jaw.bal.mina": "Alimentación de mina",
    "jaw.bal.pasante": "Pasante de la parrilla",
    "jaw.bal.carga": "Alimentación al chancador",
    "jaw.bal.prod": "Producto del chancador",
    "jaw.bal.total": "Producto total",
    "jaw.balance": (
        "Balance: entran {in_} t/h y salen {out} t/h; error relativo de sólidos {err}."
    ),
    "jaw.dl": "Descargar las corrientes (CSV)",
    # ------------------------------------------------------------ prueba esto
    "jaw.h.prueba": "Prueba esto",
    "jaw.prueba.intro": (
        "Cada experimento parte del **estado de ejemplo** (el que abre la pestaña) y sus números "
        "los calcula el modelo en vivo. El botón pone el cambio en los controles para que lo veas "
        "en el panel de arriba."
    ),
    "jaw.exp.css.titulo": "Cerrar el CSS",
    "jaw.exp.css.texto": (
        "Pasar el CSS de {css0} a {css1} mm. Con {feed0} t/h llegando al chancador, la capacidad "
        "baja de {q0} a {q1} t/h y la utilización sube de {u0} % a {u1} %: el panel marca "
        "**sobrecarga**. A cambio el producto sale más fino, con P80 de {p0} a {p1} mm."
    ),
    "jaw.exp.rpm.titulo": "Subir las rpm sobre Nc",
    "jaw.exp.rpm.texto": (
        "Con {rpm0} rpm la velocidad crítica es Nc = {nc0} rpm y el chancador trabaja bajo ella. "
        "Subir a {rpm1} rpm no aumenta la capacidad: la baja de {q0} a {q1} t/h, porque la roca "
        "no alcanza a caer entre golpes. La utilización pasa de {u0} % a {u1} % y el panel marca "
        "un **aviso** de velocidad crítica y **sobrecarga**."
    ),
    "jaw.exp.parrilla.titulo": "Apagar la parrilla",
    "jaw.exp.parrilla.texto": (
        "Sin parrilla, los finos que pasaban directo a la correa entran a la cámara: la "
        "alimentación al chancador sube de {feed0} a {feed1} t/h y la utilización de {u0} % a "
        "{u1} %, y el panel marca **sobrecarga**. La capacidad no cambia ({q0} t/h): cambia lo "
        "que se le pide."
    ),
    "jaw.exp.desgaste.titulo": "Subir el desgaste de las placas",
    "jaw.exp.desgaste.texto": (
        "El desgaste sube de {wear0} a {wear1} mm y el OSS pasa de {oss0} a {oss1} mm. La "
        "capacidad sube de {q0} a {q1} t/h (la utilización baja de {u0} % a {u1} %), pero el "
        "producto se hace más grueso, con P80 de {p0} a {p1} mm, y la razón de reducción cae a "
        "{ratio1}:1, bajo el mínimo usual. El panel marca un **aviso** de razón de reducción y "
        "otro de velocidad crítica (Nc baja a {nc1} rpm)."
    ),
    "jaw.exp.colpas.titulo": "Subir el tamaño máximo de la alimentación",
    "jaw.exp.colpas.texto": (
        "Con tamaño máximo de {top0} mm toda la alimentación está bajo 0,8·boca = {lim0} mm. "
        "Subirlo a {top1} mm deja {colpas1} % de la masa sobre ese límite (colpas) y el panel "
        "marca un **aviso**. La capacidad no cambia ({q0} t/h)."
    ),
    "jaw.exp.motor.titulo": "Motor chico con un mineral duro",
    "jaw.exp.motor.texto": (
        "Con un motor de {inst1} kW y un Wi de {wi1} kWh/t (en vez de {inst0} kW y {wi0} kWh/t), "
        "la potencia de Bond sube de {pot0} a {pot1} kW, sobre lo instalado: el panel marca un "
        "**problema** de potencia. El motor pasa a limitar la capacidad, que baja de {q0} a {q1} "
        "t/h, y la utilización sube de {u0} % a {u1} %."
    ),
    # ------------------------------------------------------------ guía de la pestaña
    "jaw.guia.titulo": "Guía de esta pestaña: cómo funciona, ecuaciones, supuestos y validación",
    "jaw.guia.como": (
        "**Qué hace.** Pasa una alimentación de mina por una parrilla (opcional) y por un "
        "chancador de mandíbula de toggle simple. La parrilla deja pasar los finos directo a la "
        "correa; lo retenido entra a la cámara en V. En cada golpe la mandíbula móvil se acerca "
        "a la fija, pellizca la roca y la hace bajar hasta que cabe por la abertura de descarga, "
        "que oscila entre el CSS (lado cerrado) y el OSS = CSS + carrera (lado abierto). El "
        "desgaste de las placas suma al CSS. De la geometría y las rpm sale la **capacidad**; de "
        "la alimentación y el Wi, la **potencia** (energía de Bond); y de la curva estándar de "
        "Nordberg, la **granulometría del producto**. El panel *Estado de la operación* revisa "
        "el resultado contra criterios con fuente."
    ),
    "jaw.guia.ecuaciones": (
        "**Ecuaciones.** La cinemática es la de Hersam, Broman y Rose y English: $G$ es la "
        "boca, $D$ la altura de la cámara, $W$ el ancho, $L$ la carrera, $\\delta$ el desgaste y "
        "$N$ las rpm. La forma de baja frecuencia de Rose y English (1967) es la misma identidad "
        "con $D = 2G$. $N_c$ es la velocidad crítica (la roca cae justo entre dos golpes) y $k$ "
        "la densidad aparente efectiva. Para comparar se muestra la fórmula de Taggart. El "
        "producto sigue la curva estándar de Nordberg (1976); la parrilla, la partición de "
        "Karra (fracción retenida, con $d_{50}$ igual a la abertura, $P_{80}$ y $F_{80}$ en µm); la energía, la ley de Bond (1952)."
    ),
    "jaw.guia.eq1": (
        "\\tan\\theta=\\frac{G-\\mathrm{CSS}_e}{D},\\qquad h=\\frac{L}{\\tan\\theta},\\qquad "
        "N_c=30\\sqrt{\\frac{g\\,\\tan\\theta}{2L}},\\qquad "
        "\\theta\\le 2\\arctan\\mu\\ \\text{(muerde)}"
    ),
    "jaw.guia.eq2": (
        "V=W\\,h\\left(\\mathrm{CSS}_e+\\tfrac{L}{2}\\right),\\qquad Q=60\\,N\\,V\\,f_N\\,k,"
        "\\qquad f_N=\\begin{cases}1 & N\\le N_c\\\\ (N_c/N)^2 & N>N_c\\end{cases}"
    ),
    "jaw.guia.eq3": (
        "\\mathrm{CSS}_e=\\mathrm{CSS}+\\delta,\\qquad \\mathrm{OSS}=\\mathrm{CSS}_e+L,"
        "\\qquad L=0{,}0502\\,G^{0{,}85},\\qquad D=2G\\quad\\text{(AMIT 135)}"
    ),
    "jaw.guia.eq4": (
        "P(r)=1-\\exp\\!\\left[-(r/\\kappa)^{n}\\right],\\quad r=\\frac{x}{\\mathrm{OSS}},"
        "\\quad (n,\\kappa)=\\begin{cases}(0{,}9756;\\ 0{,}81) & r\\le 0{,}4073\\\\ "
        "(1{,}435;\\ 0{,}65) & r>0{,}4073\\end{cases}"
    ),
    "jaw.guia.eq5": (
        "W=10\\,W_i\\left(\\frac{1}{\\sqrt{P_{80}}}-\\frac{1}{\\sqrt{F_{80}}}\\right)"
        "\\ \\mathrm{kWh/t},\\qquad "
        "Q_{\\mathrm{Taggart}}=0{,}093\\,W\\,\\mathrm{OSS}\\,\\frac{\\rho_b}{1{,}6}"
    ),
    "jaw.guia.eq6": (
        "c(d)=1-\\exp\\!\\left[-0{,}693\\left(\\frac{d}{d_{50}}\\right)^{5{,}9}\\right]"
    ),
    "jaw.guia.supuestos": (
        "**Supuestos y límites.** Lo rotulado SUPUESTO no tiene fuente en los documentos "
        "revisados.\n\n"
        "- **SUPUESTO.** Roce roca-placa μ = 0,3.\n"
        "- **SUPUESTO.** Densidad aparente efectiva k = 1,815 t/m³ para ρs = 2,7 t/m³ (ajuste "
        "global a la Tabla 3.1 de King); con otro ρs se escala k = 1,815·ρs/2,7, que supone el "
        "mismo llenado de la cámara.\n"
        "- **SUPUESTO.** Wi de impacto de 12,5 kWh/t (el del ejercicio 3-1 de King, no medido "
        "para tu mineral) y potencia en vacío igual a 0.\n"
        "- **SUPUESTO.** La abertura de la parrilla hace de d50 en la partición de Karra.\n"
        "- **SUPUESTO.** La mina es una Rosin-Rammler truncada en el tamaño máximo, con su P80 "
        "en el F80 que pones; no es una granulometría medida.\n"
        "- La altura D = 2·boca y la carrera de 0,0502·boca^0,85 son reglas de AMIT 135 "
        "(promedios de catálogo), no la medida de tu equipo.\n"
        "- El modelo de Whiten usa los parámetros del cono de MODSIM, sin ajustar a mandíbula.\n"
        "- La capacidad es la cinemática: no modela atascos, humedad ni el desgaste durante el "
        "turno. El dibujo es un esquema; la carrera real va de 1 a 7 cm."
    ),
    "jaw.guia.validacion": (
        "**Validación.** (1) Capacidad contra la Tabla 3.1 de King (56 puntos de 12 tamaños): "
        "con $k$ ajustado a todos los puntos y dejando fuera un tamaño cada vez, la mediana de "
        "|error| es 17,2 % y el 83,9 % de los puntos queda a ±30 %: **pasa**. Con φ = 0,55 sin "
        "calibrar (k = 1,485), solo el 71,4 % queda dentro de ±30 %: no pasa. La fórmula de "
        "Taggart subestima las máquinas grandes (−31 % a −52 %). (2) Producto: la curva "
        "estándar de Nordberg es el dato de referencia; el modelo de Whiten con parámetros "
        "ajustados no pasa (4 de 8 pruebas), por eso va marcado «sin validar para mandíbula»."
    ),
    "jaw.guia.datos": "**Datos que necesita** (los controles de arriba, con sus rangos).",
    "jaw.guia.fuentes": (
        "**Fuentes.** King (2000), *Technical Notes 5: Crushers* y Tabla 3.1 (MODSIM); notas "
        "AMIT 135 de la Universidad de Alaska Fairbanks (D = 2·boca, carrera = 0,0502·boca^0,85, "
        "rangos de carrera y rpm, alimentación máxima de 0,8–0,9·boca, reducción de 4:1 a 7:1); "
        "Nordberg (1976), como lo codifica el modelo JAW1 de MODSIM; Karra, en las notas de King "
        "sobre harneros; Rose y English (1967), en Gupta y Yan (2016); Taggart; Bond (1952). "
        "Números de la validación y su método: `docs/chancado.md`."
    ),
    "jaw.col.campo": "Dato",
    "jaw.col.unit": "Unidad",
    "jaw.col.range": "Rango",
    "jaw.col.example": "Ejemplo",
    "jaw.col.what": "Qué es",
    "jaw.col.how": "De dónde sale",
    # ------------------------------------------------------------ pestaña Simulación
    "sim.h.estado": "#### Estado de la operación",
    "sim.chk.potencia": (
        "Potencia del molino (Bond-Rowland): {avail} kWh/t disponibles frente a {need} kWh/t "
        "de la energía de Bond (relación {ratio})."
    ),
    "sim.chk.abierto": "Circuito abierto: no hay reciclo que converger.",
    "sim.chk.reciclo": (
        "El reciclo convergió en {it} iteraciones ({method}); carga circulante {cl}."
    ),
    "sim.chk.balance": (
        "Balance de masa: error relativo de sólidos {err} (tolerancia del solver {tol})."
    ),
    "sim.crit.potencia": (
        "Problema si la potencia en el piñón (Bond-Rowland; Rowland y Kjos, 1980) por tonelada "
        "fresca es menor que la energía de Bond. Vale para cargas normales."
    ),
    "sim.crit.reciclo": "Problema si el solver no converge dentro de sus iteraciones máximas.",
    "sim.crit.balance": "Aviso si el error relativo de sólidos supera la tolerancia del solver.",
    "sim.h.prueba": "#### Prueba esto",
    "sim.prueba.intro": (
        "Experimentos desde el **ejemplo de la barra lateral**; los números los calcula el "
        "modelo en vivo. El botón pone el cambio en los datos."
    ),
    "sim.exp.d50c.titulo": "Subir el d50c del ciclón",
    "sim.exp.d50c.texto": (
        "Con d50c de {d1} µm en vez de {d0} µm, el ciclón devuelve menos gruesos al molino: la "
        "carga circulante baja de {cl0} a {cl1}, la energía de Bond baja de {need0} a {need1} "
        "kWh/t y el producto sale más grueso, con P80 de {p0} a {p1} µm. El panel sigue en "
        "rango: el molino da {disp0} kWh/t."
    ),
    "sim.exp.tph.titulo": "Subir la alimentación fresca",
    "sim.exp.tph.texto": (
        "Con {tph1} t/h en vez de {tph0} t/h, el mismo molino reparte su potencia entre más "
        "mineral: da {disp1} kWh/t en vez de {disp0}, y Bond pide {need1} kWh/t. El panel marca "
        "un **problema** de potencia. Subir el molino a 85 % de la velocidad crítica ayuda, "
        "pero no alcanza: {disp2} kWh/t."
    ),
    "sim.exp.abierto.titulo": "Cambiar a circuito abierto",
    "sim.exp.abierto.texto": (
        "En circuito abierto no hay reciclo y el panel lo dice. El producto sale mucho más "
        "grueso, con P80 de {p0} a {p1} µm, y la energía de Bond baja de {need0} a {need1} "
        "kWh/t, porque el molino hace menos trabajo."
    ),
}
