"""English texts of the "Primary crushing" tab (keys `jaw.*`), the "Operating state" panel and
"Try this" (keys `estado.*`, `prueba.*`, `sim.chk.*`, `sim.exp.*`)."""

T = {
    "tab.jaw": "Primary crushing",
    # ------------------------------------------------------------ shared components
    "estado.nivel.ok": "In range",
    "estado.nivel.aviso": "Warning",
    "estado.nivel.mal": "Problem",
    "estado.todo_ok": "Operation within range.",
    "estado.ver": "Show the {n} checks in range",
    "prueba.aplicar": "Apply this change to the controls",
    "prueba.restablecer": "Back to the example",
    # ------------------------------------------------------------ machines and controls
    "jaw.h.equipos": "Preset machines",
    "jaw.equipos.intro": (
        "Picking a machine from King's Table 3.1 sets its gape, width, rpm and kW; the chamber "
        "height and the stroke come from the AMIT 135 rules, the CSS from an OSS in the table, "
        "and the feed is an ASSUMPTION consistent with the size. Everything can be changed "
        "afterwards."
    ),
    "jaw.equipo.label": "Machine",
    "jaw.equipo.help": 'The 12 sizes of King\'s (2000) Table 3.1, or "Custom".',
    "jaw.equipo.personalizado": "Custom",
    "jaw.equipo.item": "{name} inches · {kw} kW · {rpm} rpm",
    "jaw.oss.label": "OSS from the table (mm)",
    "jaw.oss.help": "Sets CSS = OSS − stroke and the grizzly at that aperture.",
    "jaw.h.controles": "Controls",
    "jaw.group.maquina": "Crusher",
    "jaw.group.alimentacion": "Feed and product",
    "jaw.group.parrilla": "Grizzly and hopper",
    "jaw.reset": "Back to the example",
    "jaw.si_no": "yes / no",
    "jaw.si": "yes",
    "jaw.model.nordberg": "Nordberg (standard curve)",
    "jaw.model.whiten": "Whiten (not validated for jaw crushers)",
    "jaw.campo.model.label": "Product model",
    "jaw.campo.model.meaning": (
        "Nordberg's (1976) standard curve or Whiten's breakage cycle with the MODSIM cone "
        "parameters; the latter fails the validation for jaw crushers."
    ),
    "jaw.campo.grizzly.label": "Grizzly before the crusher",
    "jaw.campo.grizzly.meaning": (
        "With a grizzly the fines go straight to the belt and only the retained rock enters the "
        "chamber."
    ),
    "jaw.campo.gape.label": "Gape",
    "jaw.campo.gape.meaning": "Feed opening G, between the two jaws at the top.",
    "jaw.campo.width.label": "Width",
    "jaw.campo.width.meaning": "Chamber width W (the other dimension of the machine).",
    "jaw.campo.height.label": "Chamber height",
    "jaw.campo.height.meaning": "Chamber height D; by rule, twice the gape.",
    "jaw.campo.stroke.label": "Stroke",
    "jaw.campo.stroke.meaning": "Stroke L at the discharge; OSS = effective CSS + stroke.",
    "jaw.campo.css.label": "CSS (closed side)",
    "jaw.campo.css.meaning": "Discharge opening with the jaw closest, without wear.",
    "jaw.campo.wear.label": "Liner wear",
    "jaw.campo.wear.meaning": "Adds to the CSS: the effective CSS is CSS + wear.",
    "jaw.campo.rpm.label": "Shaft speed",
    "jaw.campo.rpm.meaning": "Strokes per minute N; above the critical speed Nc the capacity drops.",
    "jaw.campo.mu.label": "Rock-liner friction μ",
    "jaw.campo.mu.meaning": "The rock is nipped if the nip angle does not exceed 2·arctan μ.",
    "jaw.campo.power.label": "Installed power",
    "jaw.campo.power.meaning": "Crusher motor; it limits the feed through Bond's energy.",
    "jaw.campo.tph.label": "Mine feed",
    "jaw.campo.tph.meaning": "Solids reaching the grizzly (or the gape, with no grizzly).",
    "jaw.campo.rho.label": "Solid density ρs",
    "jaw.campo.rho.meaning": (
        "Scales the effective bulk density k = 1.815·ρs/2.7 (same fill as the fit)."
    ),
    "jaw.campo.top.label": "Maximum feed size",
    "jaw.campo.top.meaning": "The largest rock the mine brings; above 0.8·gape it is oversize.",
    "jaw.campo.f80.label": "Feed F80",
    "jaw.campo.f80.meaning": "Size below which 80 % of the mine feed mass lies.",
    "jaw.campo.n.label": "Rosin-Rammler n",
    "jaw.campo.n.meaning": "Width of the mine distribution: low n = more fines and more coarse.",
    "jaw.campo.wi.label": "Impact Wi",
    "jaw.campo.wi.meaning": "Work index of the ore for the crusher's Bond energy.",
    "jaw.campo.grz_ap.label": "Grizzly aperture",
    "jaw.campo.grz_ap.meaning": "Size at which half of each class passes (d50 of the partition).",
    "jaw.campo.hopper.label": "Hopper",
    "jaw.campo.hopper.meaning": "Tonnes it holds before overflowing, for the time to overflow.",
    "jaw.src.king_tn5": "from King (2000), Technical Notes 5 and Table 3.1",
    "jaw.src.amit135": "from the AMIT 135 notes (Univ. of Alaska Fairbanks)",
    "jaw.src.karra_king": "from Karra's partition (King's notes)",
    "jaw.src.definicion": "is an input of the case",
    "jaw.src.supuesto": "is an ASSUMPTION, with no source in the documents reviewed",
    "jaw.err.numero": "A value is not a valid number.",
    "jaw.err.rango": "A value is outside the range of its control.",
    "jaw.err.boca": "The gape must be larger than the OSS (CSS + wear + stroke).",
    "jaw.err.f80": "The F80 must be smaller than the maximum feed size.",
    "jaw.err.rr": "With that n, the F80 is too close to the maximum size: lower F80 or raise n.",
    "jaw.err.modelo": "The model rejected these data: {msg}",
    # ------------------------------------------------------------ indicators and state
    "jaw.m.cap": "Capacity (t/h)",
    "jaw.m.cap.help": "Effective capacity: the lower of the kinematic capacity and the motor limit.",
    "jaw.m.util": "Utilization",
    "jaw.m.util.help": "Feed to the crusher divided by the effective capacity.",
    "jaw.m.p80": "Product P80 (mm)",
    "jaw.m.p80.help": "Total product P80: crusher product plus what passed through the grizzly.",
    "jaw.m.pot": "Power (kW)",
    "jaw.m.pot.help": "Bond power (+ idle) / installed, in kW: Bond energy times the crusher feed.",
    "jaw.m.nnc": "N / Nc",
    "jaw.m.nnc.help": "Rpm over critical speed; above 1 the capacity is reduced.",
    "jaw.m.ang": "Nip θ (°)",
    "jaw.m.ang.help": "Nip angle / limit, in °: θ = arctan((G − effective CSS)/D) against 2·arctan μ.",
    "jaw.h.estado": "Operating state",
    "jaw.fuente": "Source: {fuente}.",
    "jaw.chk.rebalse": "The hopper fills in {min} min.",
    "jaw.chk.no_muerde": "Nip angle θ = {theta}° against the limit 2·arctan μ = {limite}°.",
    "jaw.chk.velocidad_critica": ("N = {rpm} rpm; critical speed Nc = {nc} rpm; speed factor {f}."),
    "jaw.chk.rpm_fuera_de_rango": "N = {rpm} rpm; usual range {min}–{max} rpm.",
    "jaw.chk.carrera_fuera_de_rango": "Stroke of {carrera} cm; usual range {min}–{max} cm.",
    "jaw.chk.colpas": "Feed above 0.8·gape ({tam} mm): {pct} % of the mass.",
    "jaw.chk.razon_reduccion": "Reduction ratio F80/P80 = {razon}; usual range {min}:1 to {max}:1.",
    "jaw.chk.sobrecarga": (
        "Crusher feed {alim} t/h; effective capacity {cap} t/h; utilization {util} %."
    ),
    "jaw.chk.potencia": "Bond power {req} kW; installed {inst} kW.",
    "jaw.crit.no_muerde": (
        "Problem if θ exceeds 2·arctan μ: the rock slips and does not enter. μ is an ASSUMPTION."
    ),
    "jaw.crit.velocidad_critica": (
        "Warning if N exceeds Nc: the rock cannot fall between strokes and the capacity is "
        "multiplied by (Nc/N)²."
    ),
    "jaw.crit.rpm_fuera_de_rango": "Warning if N is outside 100–359 rpm.",
    "jaw.crit.carrera_fuera_de_rango": "Warning if the stroke is outside 1–7 cm.",
    "jaw.crit.colpas": (
        "Warning if any of the feed exceeds 0.8·gape (AMIT: 0.8–0.9): it can block the gape."
    ),
    "jaw.crit.razon_reduccion": "Warning if F80/P80 is outside 4:1 to 9:1.",
    "jaw.crit.sobrecarga": (
        "Problem if the crusher feed exceeds the effective capacity: the hopper fills."
    ),
    "jaw.crit.potencia": "Problem if the Bond power (plus idle) exceeds the installed power.",
    "jaw.fuente.king_tn5": "King (2000), Technical Notes 5: Crushers, and Table 3.1 (MODSIM)",
    "jaw.fuente.amit135": "AMIT 135 notes, Lesson 5, Univ. of Alaska Fairbanks",
    "jaw.fuente.nordberg_1976": "Nordberg (1976), standard product curve (MODSIM JAW1)",
    "jaw.fuente.karra_king": "Karra, in King's notes on screens (eq. 4-42)",
    "jaw.fuente.rose_english": "Rose and English (1967), in Gupta and Yan (2016), ch. 4",
    "jaw.fuente.taggart": "Taggart, empirical capacity formula",
    "jaw.fuente.bond_1952": "Bond (1952), specific energy",
    "jaw.fuente.definicion": "Geometric definition or mass balance, no parameters",
    "jaw.fuente.supuesto": "Declared ASSUMPTION, no source in the documents reviewed",
    "jaw.king": ("King's table ({name} inches, OSS {oss} mm): {q} t/h · model: {m} t/h ({d} %)."),
    # ------------------------------------------------------------ diagram
    "jaw.h.esquema": "Crusher diagram",
    "jaw.vista.label": "View",
    "jaw.vista.help": "Full section, or the discharge detail (the same drawing, zoomed in).",
    "jaw.vista.completo": "Full section",
    "jaw.vista.detalle": "Discharge detail",
    "jaw.amp.label": "Amplify the stroke (×)",
    "jaw.amp.help": "Changes only the drawing: the real stroke is small next to the chamber.",
    "jaw.vel.label": "Animation speed (%)",
    "jaw.vel.help": "Changes only the drawing: at 100 % the swing would be real, too fast to see.",
    "jaw.ab.texto": (
        "The discharge opening swings between the effective CSS ({css} mm) and the OSS ({oss} "
        "mm), a stroke of {l} mm, in a cycle of {s} s."
    ),
    "jaw.svg.label": "Side section of a single-toggle jaw crusher",
    "jaw.svg.g": "gape G = {v} mm",
    "jaw.svg.d": "height D = {v} mm",
    "jaw.svg.css": "CSS = {v} mm",
    "jaw.svg.oss": "OSS = {v} mm",
    "jaw.svg.theta": "θ = {v}°",
    "jaw.svg.fija": "fixed jaw",
    "jaw.svg.volante": "flywheel and eccentric",
    "jaw.svg.toggle": "toggle plate",
    "jaw.svg.barra": "tension rod and spring",
    "jaw.svg.camara": "V-shaped chamber",
    "jaw.svg.parrilla": "vibrating grizzly",
    "jaw.svg.correa": "product belt",
    "jaw.svg.leg.fino": "≤ CSS: {p} % of the mass",
    "jaw.svg.leg.css_oss": "between CSS and OSS: {p} %",
    "jaw.svg.leg.grueso": "larger than the OSS: {p} %",
    "jaw.svg.leg.colpa": "oversize (> 0.8·gape): {p} %",
    "jaw.svg.prod": "Product: {p} % below the OSS",
    "jaw.svg.finos": "grizzly fines → belt",
    "jaw.svg.prodtot": "total product: {t} t/h · P80 {p} mm",
    "jaw.svg.solo2": "only the drawing changes",
    "jaw.svg.title": "Jaw crusher",
    "jaw.svg.dims": "Gape × width: {g} × {w} mm",
    "jaw.svg.rpm": "{rpm} rpm = one cycle every {p} s",
    "jaw.svg.view": "In the drawing: {p} s per cycle ({v} %)",
    "jaw.svg.stroke": "Real stroke {l} mm, drawn ×{a}",
    "jaw.svg.note1": "Of {m} quantiles, the {n} that",
    "jaw.svg.note2": "fit without overlapping are drawn.",
    "jaw.svg.note3": "Belt: {a} product quantiles",
    "jaw.svg.note4": "and {b} of the grizzly fines.",
    "jaw.svg.solo": "Stroke ×{a}, speed {v} %:",
    "jaw.svg.ab.title": "Discharge opening over time",
    "jaw.svg.ab.x": "two cycles = {s} s at {n} rpm (real speed)",
    "jaw.svg.ab.label": "Discharge opening between the CSS and the OSS over two cycles",
    # ------------------------------------------------------------ curves and balance
    "jaw.h.curvas": "Curves",
    "jaw.plot.mina": "Mine feed",
    "jaw.plot.pasante": "Grizzly undersize",
    "jaw.plot.carga": "Crusher feed",
    "jaw.plot.prod": "Crusher product",
    "jaw.plot.total": "Total product",
    "jaw.plot.css": "CSS",
    "jaw.plot.oss": "OSS",
    "jaw.plot.gran.title": "Size distribution of each stream",
    "jaw.plot.gran.x": "Size (mm)",
    "jaw.plot.gran.y": "Cumulative passing (%)",
    "jaw.plot.cap.title": "Crusher capacity",
    "jaw.plot.cap.y": "Capacity (t/h)",
    "jaw.plot.cap.modelo": "Model (kinematics)",
    "jaw.plot.cap.punto": "Operating point",
    "jaw.plot.cap.llega": "Reaching the crusher",
    "jaw.plot.cap.potencia": "Power limit",
    "jaw.plot.cap.nc": "Nc",
    "jaw.plot.cap.taggart": "Taggart",
    "jaw.plot.cap.king": "King's table",
    "jaw.plot.cap.x.rpm": "Shaft speed (rpm)",
    "jaw.plot.cap.x.css": "CSS (mm)",
    "jaw.eje.label": "Capacity axis",
    "jaw.eje.help": "Capacity against rpm, or against CSS with Taggart and King's table.",
    "jaw.eje.rpm": "rpm",
    "jaw.eje.css": "CSS",
    "jaw.curvas.nota": (
        "King's table points appear only if the gape and width are those of one of the 12 machines."
    ),
    "jaw.h.balance": "Mass balance",
    "jaw.bal.corriente": "Stream",
    "jaw.bal.tph": "Solids (t/h)",
    "jaw.bal.p80": "P80 (mm)",
    "jaw.bal.p50": "P50 (mm)",
    "jaw.bal.css": "Below the CSS (%)",
    "jaw.bal.mina": "Mine feed",
    "jaw.bal.pasante": "Grizzly undersize",
    "jaw.bal.carga": "Crusher feed",
    "jaw.bal.prod": "Crusher product",
    "jaw.bal.total": "Total product",
    "jaw.balance": ("Balance: {in_} t/h in and {out} t/h out; relative solids error {err}."),
    "jaw.dl": "Download the streams (CSV)",
    # ------------------------------------------------------------ try this
    "jaw.h.prueba": "Try this",
    "jaw.prueba.intro": (
        "Each experiment starts from the **example state** (the one the tab opens with) and the "
        "model computes its numbers live. The button puts the change into the controls so you "
        "can see it in the panel above."
    ),
    "jaw.exp.css.titulo": "Close the CSS",
    "jaw.exp.css.texto": (
        "Take the CSS from {css0} to {css1} mm. With {feed0} t/h reaching the crusher, the "
        "capacity drops from {q0} to {q1} t/h and the utilization rises from {u0} % to {u1} %: "
        "the panel flags **overload**. In return the product is finer, with P80 going from {p0} "
        "to {p1} mm."
    ),
    "jaw.exp.rpm.titulo": "Raise the rpm above Nc",
    "jaw.exp.rpm.texto": (
        "At {rpm0} rpm the critical speed is Nc = {nc0} rpm and the crusher runs below it. "
        "Raising it to {rpm1} rpm does not increase the capacity: it lowers it from {q0} to {q1} "
        "t/h, because the rock cannot fall between strokes. The utilization goes from {u0} % to "
        "{u1} % and the panel shows a critical-speed **warning** and **overload**."
    ),
    "jaw.exp.parrilla.titulo": "Switch the grizzly off",
    "jaw.exp.parrilla.texto": (
        "With no grizzly, the fines that went straight to the belt enter the chamber: the "
        "crusher feed rises from {feed0} to {feed1} t/h and the utilization from {u0} % to "
        "{u1} %, and the panel flags **overload**. The capacity does not change ({q0} t/h): "
        "what is asked of it does."
    ),
    "jaw.exp.desgaste.titulo": "Raise the liner wear",
    "jaw.exp.desgaste.texto": (
        "The wear rises from {wear0} to {wear1} mm and the OSS goes from {oss0} to {oss1} mm. "
        "The capacity rises from {q0} to {q1} t/h (the utilization drops from {u0} % to {u1} "
        "%), but the product gets coarser, with P80 from {p0} to {p1} mm, and the reduction "
        "ratio falls to {ratio1}:1, below the usual minimum. The panel shows a reduction-ratio "
        "**warning** and a critical-speed one (Nc drops to {nc1} rpm)."
    ),
    "jaw.exp.colpas.titulo": "Raise the maximum feed size",
    "jaw.exp.colpas.texto": (
        "With a maximum size of {top0} mm all of the feed is below 0.8·gape = {lim0} mm. "
        "Raising it to {top1} mm leaves {colpas1} % of the mass above that limit (oversize) and "
        "the panel shows a **warning**. The capacity does not change ({q0} t/h)."
    ),
    "jaw.exp.motor.titulo": "Small motor with a hard ore",
    "jaw.exp.motor.texto": (
        "With a {inst1} kW motor and a Wi of {wi1} kWh/t (instead of {inst0} kW and {wi0} "
        "kWh/t), the Bond power rises from {pot0} to {pot1} kW, above what is installed: the "
        "panel flags a power **problem**. The motor now limits the capacity, which drops from "
        "{q0} to {q1} t/h, and the utilization rises from {u0} % to {u1} %."
    ),
    # ------------------------------------------------------------ tab guide
    "jaw.guia.titulo": "Guide to this tab: how it works, equations, assumptions and validation",
    "jaw.guia.como": (
        "**What it does.** It passes a mine feed through a grizzly (optional) and a single-toggle "
        "jaw crusher. The grizzly lets the fines go straight to the belt; what it retains enters "
        "the V-shaped chamber. On each stroke the moving jaw approaches the fixed one, nips the "
        "rock and makes it descend until it fits through the discharge opening, which swings "
        "between the CSS (closed side) and the OSS = CSS + stroke (open side). Liner wear adds to "
        "the CSS. The geometry and the rpm give the **capacity**; the feed and the Wi give the "
        "**power** (Bond energy); and Nordberg's standard curve gives the **product size "
        "distribution**. The *Operating state* panel checks the result against criteria with a "
        "source."
    ),
    "jaw.guia.ecuaciones": (
        "**Equations.** The kinematics are those of Hersam, Broman, and Rose and English: $G$ is "
        "the gape, $D$ the chamber height, $W$ the width, $L$ the stroke, $\\delta$ the wear and "
        "$N$ the rpm. The low-frequency form of Rose and English (1967) is the same identity "
        "with $D = 2G$. $N_c$ is the critical speed (the rock falls exactly between two strokes) "
        "and $k$ the effective bulk density. Taggart's formula is shown for comparison. The "
        "product follows Nordberg's (1976) standard curve; the grizzly, Karra's partition (retained fraction, with $d_{50}$ equal to the aperture, $P_{80}$ and $F_{80}$ in µm); the "
        "energy, Bond's (1952) law."
    ),
    "jaw.guia.eq1": (
        "\\tan\\theta=\\frac{G-\\mathrm{CSS}_e}{D},\\qquad h=\\frac{L}{\\tan\\theta},\\qquad "
        "N_c=30\\sqrt{\\frac{g\\,\\tan\\theta}{2L}},\\qquad "
        "\\theta\\le 2\\arctan\\mu\\ \\text{(nips)}"
    ),
    "jaw.guia.eq2": (
        "V=W\\,h\\left(\\mathrm{CSS}_e+\\tfrac{L}{2}\\right),\\qquad Q=60\\,N\\,V\\,f_N\\,k,"
        "\\qquad f_N=\\begin{cases}1 & N\\le N_c\\\\ (N_c/N)^2 & N>N_c\\end{cases}"
    ),
    "jaw.guia.eq3": (
        "\\mathrm{CSS}_e=\\mathrm{CSS}+\\delta,\\qquad \\mathrm{OSS}=\\mathrm{CSS}_e+L,"
        "\\qquad L=0.0502\\,G^{0.85},\\qquad D=2G\\quad\\text{(AMIT 135)}"
    ),
    "jaw.guia.eq4": (
        "P(r)=1-\\exp\\!\\left[-(r/\\kappa)^{n}\\right],\\quad r=\\frac{x}{\\mathrm{OSS}},"
        "\\quad (n,\\kappa)=\\begin{cases}(0.9756;\\ 0.81) & r\\le 0.4073\\\\ "
        "(1.435;\\ 0.65) & r>0.4073\\end{cases}"
    ),
    "jaw.guia.eq5": (
        "W=10\\,W_i\\left(\\frac{1}{\\sqrt{P_{80}}}-\\frac{1}{\\sqrt{F_{80}}}\\right)"
        "\\ \\mathrm{kWh/t},\\qquad "
        "Q_{\\mathrm{Taggart}}=0.093\\,W\\,\\mathrm{OSS}\\,\\frac{\\rho_b}{1.6}"
    ),
    "jaw.guia.eq6": ("c(d)=1-\\exp\\!\\left[-0.693\\left(\\frac{d}{d_{50}}\\right)^{5.9}\\right]"),
    "jaw.guia.supuestos": (
        "**Assumptions and limits.** What is labeled ASSUMPTION has no source in the documents "
        "reviewed.\n\n"
        "- **ASSUMPTION.** Rock-liner friction μ = 0.3.\n"
        "- **ASSUMPTION.** Effective bulk density k = 1.815 t/m³ for ρs = 2.7 t/m³ (global fit "
        "to King's Table 3.1); with another ρs, k = 1.815·ρs/2.7 is scaled, which assumes the "
        "same chamber fill.\n"
        "- **ASSUMPTION.** Impact Wi of 12.5 kWh/t (that of King's exercise 3-1, not measured "
        "for your ore) and idle power equal to 0.\n"
        "- **ASSUMPTION.** The grizzly aperture acts as the d50 in Karra's partition.\n"
        "- **ASSUMPTION.** The mine feed is a Rosin-Rammler truncated at the maximum size, with "
        "its P80 at the F80 you set; it is not a measured size distribution.\n"
        "- The height D = 2·gape and the stroke of 0.0502·gape^0.85 are AMIT 135 rules "
        "(catalog averages), not the measurement of your machine.\n"
        "- Whiten's model uses the MODSIM cone parameters, not fitted to jaw crushers.\n"
        "- The capacity is the kinematic one: it does not model blockages, moisture or wear "
        "during the shift. The drawing is a diagram; the real stroke goes from 1 to 7 cm."
    ),
    "jaw.guia.validacion": (
        "**Validation.** (1) Capacity against King's Table 3.1 (56 points of 12 sizes): with $k$ "
        "fitted to all the points and leaving one size out each time, the median |error| is "
        "17.2 % and 83.9 % of the points fall within ±30 %: it **passes**. With φ = 0.55 "
        "uncalibrated (k = 1.485), only 71.4 % fall within ±30 %: it fails. Taggart's formula "
        "underestimates the large machines (−31 % to −52 %). (2) Product: Nordberg's standard "
        "curve is the reference data; Whiten's model with fitted parameters fails (4 of 8 "
        'tests), so it is marked "not validated for jaw crushers".'
    ),
    "jaw.guia.datos": "**Data it needs** (the controls above, with their ranges).",
    "jaw.guia.fuentes": (
        "**Sources.** King (2000), *Technical Notes 5: Crushers* and Table 3.1 (MODSIM); AMIT "
        "135 notes from the University of Alaska Fairbanks (D = 2·gape, stroke = "
        "0.0502·gape^0.85, stroke and rpm ranges, maximum feed of 0.8–0.9·gape, reduction of "
        "4:1 to 7:1); Nordberg (1976), as encoded in MODSIM's JAW1 model; Karra, in King's notes "
        "on screens; Rose and English (1967), in Gupta and Yan (2016); Taggart; Bond (1952). "
        "Validation numbers and method: `docs/chancado.md`."
    ),
    "jaw.col.campo": "Input",
    "jaw.col.unit": "Unit",
    "jaw.col.range": "Range",
    "jaw.col.example": "Example",
    "jaw.col.what": "What it is",
    "jaw.col.how": "Where it comes from",
    # ------------------------------------------------------------ Simulation tab
    "sim.h.estado": "#### Operating state",
    "sim.chk.potencia": (
        "Mill power (Bond-Rowland): {avail} kWh/t available against {need} kWh/t of Bond energy "
        "(ratio {ratio})."
    ),
    "sim.chk.abierto": "Open circuit: there is no recycle to converge.",
    "sim.chk.reciclo": (
        "The recycle converged in {it} iterations ({method}); circulating load {cl}."
    ),
    "sim.chk.balance": ("Mass balance: relative solids error {err} (solver tolerance {tol})."),
    "sim.crit.potencia": (
        "Problem if the pinion power (Bond-Rowland; Rowland and Kjos, 1980) per fresh tonne is "
        "below the Bond energy. It holds for normal charges."
    ),
    "sim.crit.reciclo": "Problem if the solver does not converge within its maximum iterations.",
    "sim.crit.balance": "Warning if the relative solids error exceeds the solver tolerance.",
    "sim.h.prueba": "#### Try this",
    "sim.prueba.intro": (
        "Experiments from the **sidebar example**; the model computes the numbers live. The "
        "button puts the change into the inputs."
    ),
    "sim.exp.d50c.titulo": "Raise the cyclone d50c",
    "sim.exp.d50c.texto": (
        "With a d50c of {d1} µm instead of {d0} µm, the cyclone returns less coarse material to "
        "the mill: the circulating load drops from {cl0} to {cl1}, the Bond energy drops from "
        "{need0} to {need1} kWh/t and the product is coarser, with P80 from {p0} to {p1} µm. "
        "The panel stays in range: the mill delivers {disp0} kWh/t."
    ),
    "sim.exp.tph.titulo": "Raise the fresh feed",
    "sim.exp.tph.texto": (
        "With {tph1} t/h instead of {tph0} t/h, the same mill spreads its power over more ore: "
        "it delivers {disp1} kWh/t instead of {disp0}, and Bond asks for {need1} kWh/t. The "
        "panel flags a power **problem**. Raising the mill to 85 % of the critical speed "
        "helps, but it is not enough: {disp2} kWh/t."
    ),
    "sim.exp.abierto.titulo": "Switch to open circuit",
    "sim.exp.abierto.texto": (
        "In open circuit there is no recycle and the panel says so. The product is much "
        "coarser, with P80 from {p0} to {p1} µm, and the Bond energy drops from {need0} to "
        "{need1} kWh/t, because the mill does less work."
    ),
}
