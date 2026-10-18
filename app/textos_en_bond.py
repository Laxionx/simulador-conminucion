"""English texts of the "Bond test" tab (keys `bond.*`)."""

T = {
    "tab.bond": "Bond test",
    # ------------------------------------------------------------ data sheet
    "bond.h.ficha": "#### What this tab is",
    "bond.ficha.que": (
        "**What it does.** It shows, cycle by cycle, how the Bond ball mill test is run (a "
        "305 × 305 mm laboratory mill turning at 70 rpm, with a closing screen and 250 % "
        "circulating load) and where the work index **Wi** comes from. It has two parts: a "
        "**calculator** with the bookkeeping of the procedure and a **simulation** of the same "
        "test with a batch grinding model that only knows the first two cycles."
    ),
    "bond.ficha.datos": "**Data it needs** (the calculator asks for them below, within these ranges).",
    "bond.ficha.ciclos": (
        "Plus one row per cycle with the **total fines** weighed at the end of each cycle (g "
        "passing the closing screen), from 0 to {max} g, up to {n} cycles."
    ),
    "bond.ficha.devuelve": (
        "**What it returns.** Per cycle: new feed, revolutions, fines from the feed and new fines, "
        "net grams per revolution (Gbp) and circulating load; at the end, the Gbp (mean of the "
        "last three cycles), whether the stopping criterion is met and the Wi in kWh/t. The "
        "simulation returns the same quantities calculated with the model."
    ),
    "bond.ficha.fuentes": (
        "**Sources.** GMG (2021), *Guideline: Determining the Bond Efficiency of Industrial "
        "Grinding Circuits* (procedure, Wi equation and stopping criterion; open access). "
        "Liang, Wei, Xu, Xia and Li (2016), *Study on the Selection of Comminution Circuits for a "
        "Magnetite Ore in Eastern Hebei, China*, Minerals 6(2), 39, "
        "[doi:10.3390/min6020039](https://doi.org/10.3390/min6020039) (CC BY; the 11 cycles of "
        "Table 2). Austin, Klimpel and Luckie (1984), *Process Engineering of Size Reduction: Ball "
        "Milling* (selection S and breakage function). A 2023 review, “The truth about "
        "population balance modeling”, argues that a batch test does not predict the closed "
        "circuit test in heterogeneous ores: the simulation below can fail, and it is reported "
        "as it comes out."
    ),
    "bond.ficha.supuestos": (
        "**Declared assumptions.** (1) Masses are rounded to 0.1 g, the resolution of a balance. "
        "(2) The simulation feed is a Rosin-Rammler curve through two points of the paper (F80 "
        "and the percentage under the screen); the full curve of the paper is a chart and was not "
        "used. (3) Size grid close to √2 from 3,350 µm, with the closing screen exactly on the "
        "grid. (4) Ideal screening. (5) The model fits only Austin's *a* and α; μ, Λ and the "
        "breakage function stay at the simulator defaults (a typical example from Austin et al., "
        "not measured for this ore). (6) The ball filling in the drawing comes from 20.125 kg of "
        "steel with the density and voidage of the simulator. (7) The Wi constant is the one in "
        "the guideline (1.1023 × 44.5)."
    ),
    # ------------------------------------------------------------ calculator data
    "bond.campo.carga.label": "Mill charge",
    "bond.campo.carga.meaning": "Mass of the charge: 700 cm³ of packed ore.",
    "bond.campo.carga.source": "weighed in the laboratory (GMG 2021, step 5)",
    "bond.campo.finos_carga.label": "Fines in the initial charge",
    "bond.campo.finos_carga.meaning": (
        "Mass of the initial charge that already passes the closing screen; it gives the fines "
        "fraction of the feed."
    ),
    "bond.campo.finos_carga.source": "the initial charge is screened before grinding",
    "bond.campo.rev1.label": "Revolutions of cycle 1",
    "bond.campo.rev1.meaning": "Revolutions of the first cycle; the procedure suggests 100 to 150.",
    "bond.campo.rev1.source": "set by the laboratory (GMG 2021, step 8)",
    "bond.campo.tamiz.label": "Closing screen",
    "bond.campo.tamiz.meaning": "Aperture of the screen that separates the product (P1).",
    "bond.campo.tamiz.source": "chosen when the test is designed",
    "bond.campo.f80.label": "Feed F80",
    "bond.campo.f80.meaning": "Size under which 80 % of the feed passes.",
    "bond.campo.f80.source": "size analysis (screening) of the feed",
    "bond.campo.p80.label": "Product P80",
    "bond.campo.p80.meaning": (
        "Size under which 80 % of the product of the last three cycles together passes."
    ),
    "bond.campo.p80.source": "size analysis of the combined product",
    "bond.col.campo": "Input",
    "bond.col.unit": "Unit",
    "bond.col.range": "Range",
    "bond.col.example": "Example (Hebei)",
    "bond.col.what": "What it is",
    "bond.col.how": "How to get it",
    # ------------------------------------------------------------ calculator
    "bond.h.calc": "#### Test calculator",
    "bond.calc.intro": (
        "Each row of the table is a cycle: type the **total fines** you weighed at the end. The "
        "revolutions of the next cycle come from the GMG rule: *(IPP − fines in the new feed) / "
        "Gbp of the previous cycle*, with IPP = charge / 3.5. The table comes loaded with the "
        "Hebei test."
    ),
    "bond.calc.example": "Back to the Hebei example",
    "bond.edit.finos": "Total fines < screen (g)",
    "bond.edit.help": "Grams passing the closing screen at the end of the cycle. One row per cycle.",
    "bond.err.numero": "An input is not a valid number: go back to the Hebei example.",
    "bond.err.rango": "An input is outside its range (see the data sheet).",
    "bond.err.filas": "The table must have between {lo} and {hi} cycles.",
    "bond.err.vacio": "There are empty or text cells in the cycle table: fill them with numbers.",
    "bond.err.finos": "The fines of each cycle go from 0 g to the mass of the charge.",
    "bond.err.carga": "The fines of the initial charge must be less than the charge.",
    "bond.err.tamaños": "Product P80 < closing screen < feed F80 is required.",
    "bond.err.calculo": (
        "These data do not add up: some cycle makes no new fines (its total fines do not exceed "
        "those of its feed). Check the table."
    ),
    "bond.t.ciclo": "Cycle",
    "bond.t.alim": "New feed (g)",
    "bond.t.rev": "Revolutions",
    "bond.t.total": "Total fines (g)",
    "bond.t.dealim": "Fines from the feed (g)",
    "bond.t.nuevos": "New fines (g)",
    "bond.t.gbp": "Gbp (g/rev)",
    "bond.t.cl": "Circulating load (%)",
    "bond.t.inv": "Reverses",
    "bond.yes": "yes",
    "bond.no": "no",
    "bond.calc.res": (
        "**Final Gbp** (mean of the last three cycles): **{gbp}** g/rev · IPP: {ipp} g · "
        "**Wi = {wi} kWh/t**."
    ),
    "bond.calc.fin.si": (
        "**Stopping criterion:** met from cycle {k}: there are at least five cycles and the Gbp "
        "reversed its direction. The guideline sets no numeric tolerance for “equilibrium”, so "
        "only the reversal is checked."
    ),
    "bond.calc.fin.no": (
        "**Stopping criterion:** not met yet (it needs at least five cycles and a reversal of "
        "the Gbp)."
    ),
    "bond.calc.ref": "Reference from the paper (Hebei): Gbp {gbp} g/rev and Wi {wi} kWh/t.",
    # ------------------------------------------------------------ simulation
    "bond.h.sim": "#### Simulation of the Hebei test",
    "bond.sim.intro": (
        "A batch grinding model (*dw/dt = −S·w + B·S·w*, with Austin's selection and breakage "
        "function) is fitted **only** to the new fines of cycles 1 and 2: two data points for two "
        "parameters, *a* = {a} 1/min and α = {alpha}. With that it simulates the 11 cycles, with "
        "ideal screening and the GMG rule for the revolutions, and compares them with the "
        "measurements. Cycles 3 to 11 are a prediction."
    ),
    "bond.sim.cycle": "Test cycle",
    "bond.sim.cycle.help": "Pick the cycle the mill shows.",
    "bond.sim.cap": (
        "Cycle {k} of {n}: {rev} revolutions at {rpm} rpm = {s} s of grinding · measured Gbp {gm} "
        "g/rev, simulated {gs} g/rev · simulated circulating load {cl} %."
    ),
    "bond.sim.alt": "Laboratory Bond mill turning at 70 rpm",
    "bond.sim.legend": (
        "Diagram, not to scale: the quantities are from the calculation (mill rotation, ball "
        "filling, revolutions and Gbp of each cycle). The tilt of the charge and the falling "
        "balls are illustrative."
    ),
    "bond.h.res": "**Result against the measurement** (cut: ±{cut} %)",
    "bond.res.row": "{name}: simulated **{sim}**, measured {med} ({err} %) → {verdict}",
    "bond.res.gbp": "Final Gbp",
    "bond.res.p80": "Product P80 (µm)",
    "bond.res.wi": "Wi (kWh/t)",
    "bond.res.in": "within the cut",
    "bond.res.out": "outside the cut",
    "bond.res.nota": (
        "What misses the cut is left as it is, without fitting more parameters to make it match: "
        "it is a negative result. The simulated P80 comes from interpolating the passing curve on "
        "a size grid and the Wi amplifies it."
    ),
    "bond.plot.title": "Bond test: measured against simulated",
    "bond.plot.x": "Cycle",
    "bond.plot.y1": "Net grams per revolution, Gbp (g/rev)",
    "bond.plot.y2": "Circulating load (%)",
    "bond.plot.med": "Measured",
    "bond.plot.sim": "Simulated",
    "bond.plot.note": "Cycle {k} of {n} · measured Gbp {gm} · simulated {gs}",
}
