"""English texts for real data: CSV/XLSX upload (keys `carga.*`), fitting to a grinding survey
(`mu.*`) and calibrating the crusher with the plant (`plant.*`)."""

T = {
    # ------------------------------------------------------------ file upload
    "carga.aviso": (
        "What you upload travels to Streamlit's servers and is not stored; for company data, run "
        "the app locally (`streamlit run app/streamlit_app.py`, see the README)."
    ),
    "carga.label": "Upload a file (CSV or XLSX)",
    "carga.help": (
        'At most 1 MB and 500 rows. CSV with ";" and decimal comma (Excel in Spanish) or with '
        '"," and decimal point (Excel in English), in UTF-8 or Latin-1. XLSX: the first sheet, '
        "with the headers in the first row; formulas are not evaluated, the saved value is used. "
        "Headers can be in Spanish or English."
    ),
    "carga.plantilla": "Download template (CSV)",
    "carga.ok": "File read: {n} rows. The data is in the table below; you can edit it.",
    "carga.err.ext": "Only .csv and .xlsx files are accepted (not .xls or .xlsm).",
    "carga.err.tamano": "The file is too large: the maximum is 1 MB.",
    "carga.err.filas": "The file has too many rows: the maximum is {max}.",
    "carga.err.faltan": "Required columns are missing from the file: {cols}.",
    "carga.err.celda": (
        'Row {fila} has no number in the column "{col}" (empty cell, text, date or non-finite '
        "value)."
    ),
    "carga.err.ilegible": "The file could not be read: it is not a valid CSV or XLSX.",
    "carga.err.vacio": "The file has no data rows.",
    "carga.err.xml": "An XLSX cannot be read on this server (the safe XML reader is missing).",
    # ------------------------------------------------------------ real survey: source and data
    "mu.fuente.label": "Data source",
    "mu.fuente.sintetico": "Synthetic survey (as before)",
    "mu.fuente.tus": "Your data",
    "mu.fuente.vazante": "Vazante, campaign 1 (published)",
    "mu.fuente.help": (
        "Synthetic: data generated with known parameters. Your data: a table you paste or upload. "
        "Vazante: the cyclone survey of Costa, Bergerman and Delboni Jr. (2024)."
    ),
    "mu.intro.tus": (
        "Paste the table from Excel or upload a file: one row per sieve (µm, largest first) with "
        "the **cumulative % passing** of the cyclone feed, underflow and overflow. Optional: the "
        "% passing of the mill feed and discharge. The table comes preloaded with the Vazante "
        "survey as an example: replace it with yours."
    ),
    "mu.intro.vazante": (
        "Balanced survey of campaign 1 (April 2022) at the Vazante plant (Nexa Resources, Brazil), "
        "cyclones only. Source: Costa, Bergerman and Delboni Jr. (2024), *Minerals* 14(7), 707, "
        "Table A3. This is validation case C2."
    ),
    "mu.h.datos": "Survey data",
    "mu.tabla.ayuda": (
        "Decreasing sieves in µm; the values are cumulative % passing (0–100, not rising toward "
        "finer sieves). Up to 500 rows."
    ),
    "mu.sol.usar": "I have the % solids of the three streams",
    "mu.sol.usar.help": (
        "With the % solids, the method validated on Vazante is used: Rf = water to coarse, from "
        "the water balance. Without them, Rf is fitted freely and its CI is wider."
    ),
    "mu.sol.alim": "Feed % solids",
    "mu.sol.uf": "Underflow % solids",
    "mu.sol.of": "Overflow % solids",
    "mu.col.clase": "Class (µm)",
    "mu.err.menos": "At least {min} sieves with data are needed.",
    "mu.err.filas": (
        "The columns do not have the same number of rows with data: sieve {tamiz}, feed {alim}, "
        "underflow {uf}, overflow {of}."
    ),
    "mu.err.filas_molino": (
        "The mill data must be complete or absent: {n} sieves, mill feed {alim} rows, discharge "
        "{desc}."
    ),
    "mu.err.tamices": "Sieves must be positive and decreasing (largest first).",
    "mu.err.rango": 'The column "{col}" has values outside 0–100 %.',
    "mu.err.monotono": (
        'The column "{col}" is not a cumulative curve: it rises at the {tamiz} µm sieve.'
    ),
    "mu.err.solidos": "The % solids must be between 0 and 100, both excluded.",
    "mu.err.utiles": (
        "{n} classes are usable to fit the partition (classes with upper sieve up to {corte} µm "
        "and enough feed are used) and at least {min} are needed."
    ),
    "mu.err.ajuste": "The partition fit does not converge with these data.",
    "mu.err.molino": (
        "The mill could not be fitted: the r/d per knot need more data (at least 6 sieves) or the "
        "fit does not converge."
    ),
    # ------------------------------------------------------------ real survey: status
    "mu.h.estado": "Survey status",
    "mu.est.chi2.ok": (
        "Global coherence: χ² = {chi2} does not exceed the 95 % critical value ({crit}, {gl} "
        "degrees of freedom)."
    ),
    "mu.est.chi2.mal": (
        "Global coherence: χ² = {chi2} exceeds the 95 % critical value ({crit}, {gl} degrees of "
        "freedom): the data do not close a balance within the assumed noise."
    ),
    "mu.est.chi2.ayuda": (
        "Statistical definition: χ² = Σ ((measured − reconciled)/σ)² over the three size "
        "distributions, with σ = max(5 % of the value; 0.002) (declared assumption). Degrees of "
        "freedom = n + 2 (n class balances and 3 sums, minus R). Critical value = 95th percentile "
        "of the χ² distribution."
    ),
    "mu.est.z.ok": (
        "Largest standardized adjustment: z = {z} in {corriente}, class {inf}–{sup} µm; within 3σ."
    ),
    "mu.est.z.mal": (
        "Largest standardized adjustment: z = {z} in {corriente}, class {inf}–{sup} µm; beyond 3σ."
    ),
    "mu.est.z.ayuda": (
        "z = (measured − reconciled)/σ, for the class between two sieves (the cumulative curve is "
        "converted to retained). Statistical 3σ criterion. Note: the balance spreads an error "
        "over the three streams; in tests with a planted error, the largest z fell on the right "
        "sieve but in the feed and below 3σ. It shows WHERE the most is corrected, not which "
        "stream is wrong."
    ),
    "mu.nota.diagnostico": (
        "The χ² and z say how much had to be corrected, not which stream is wrong: in the test "
        "with a planted error of +4 points, χ² exceeded its critical value in only 1 of 3 cases "
        "and the largest z fell on the right sieve but in the feed. That is why no advice on what "
        "to resample is given."
    ),
    "mu.m.r": "R (solids to underflow)",
    "mu.est.todo_ok": "Coherent survey: the χ² and the largest adjustment are within expectations.",
    "mu.params.nota": (
        "The CIs come from a linear approximation (Jacobian): a negative limit on d50c or α "
        "means the CI is not reliable with so few points."
    ),
    "mu.m.r.help": "Fraction of the feed solids that leaves through the underflow.",
    "mu.m.cl": "Circulating load",
    "mu.m.cl.help": "Underflow solids / overflow solids (= fresh feed).",
    "mu.m.chi2": "Weighted χ²",
    "mu.m.chi2.help": "Σ ((measured − reconciled)/σ)². It is compared with the critical value in the panel.",
    "mu.m.cierre": "Closure before → after",
    "mu.m.cierre.help": (
        "Largest |f − (R·u + (1 − R)·o)| over the classes, in percentage points: with the "
        "measured values (before) and the reconciled ones (after, zero by construction)."
    ),
    "mu.m.z": "Largest |z|",
    "mu.m.z.help": "The largest standardized adjustment over all streams and classes.",
    "mu.m.ic": "d50c 95 % CI width",
    "mu.m.ic.help": (
        "Width of the 95 % confidence interval of d50c from the free fit (linear approximation "
        "through the Jacobian). Shown without a threshold."
    ),
    # ------------------------------------------------------------ real survey: results
    "mu.h.gran": "Measured and reconciled size distributions",
    "mu.gran.caption": (
        "% retained per class (a row's class lies between its sieve and the next one). z = "
        "(measured − reconciled)/σ."
    ),
    "mu.col.alim": "feed",
    "mu.col.uf": "underflow",
    "mu.col.of": "overflow",
    "mu.col.medido": "{corriente} measured",
    "mu.col.reconc": "{corriente} reconciled",
    "mu.col.z": "z {corriente}",
    "mu.plot.size": "Size (µm)",
    "mu.plot.pass": "Cumulative passing (%)",
    "mu.plot.medido": "{corriente}, measured",
    "mu.plot.reconc": "{corriente}, reconciled",
    "mu.h.part": "Partition to underflow: measured and fitted",
    "mu.plot.part.y": "Partition to underflow (%)",
    "mu.plot.part.medida": "measured (reconciled data), used in the fit",
    "mu.plot.part.fuera": "measured, outside the fit",
    "mu.plot.part.ajustada": "fitted",
    "mu.plot.part.libre": "free fit (free Rf)",
    "mu.metodo.fijo": (
        "With % solids: method validated on Vazante (Rf = water to coarse from the water balance; "
        "d50c and α by least squares). The free fit of the three, with its 95 % CI, is "
        "informative."
    ),
    "mu.metodo.libre": (
        "Without % solids: Rf, d50c and α are fitted freely to the measured partition, with their "
        "95 % CI. The free Rf usually has a wide CI; with the % solids it is fixed by the water "
        "balance."
    ),
    "mu.metodo.clases": (
        "The {n} classes with upper sieve up to {corte} µm and enough feed are fitted (the "
        "validation's criterion). Hollow points are not in the fit."
    ),
    "mu.h.params": "Partition parameters",
    "mu.p.param": "parameter",
    "mu.p.valor": "method value",
    "mu.p.libre": "free fit",
    "mu.p.lo": "95% CI low (free)",
    "mu.p.hi": "95% CI high (free)",
    "mu.pub": (
        "Published: d50c = {d50c} µm (this app: {mio}, difference {dd} %) and α = {a} (this app: "
        "{amio}, difference {da} %)."
    ),
    "mu.h.molino": "Mill: r/d per knot",
    "mu.molino.nota": (
        "Fit of the knot r/d values ({nudos} µm) to the mill feed and discharge, with the "
        "fracture and mixers of the sidebar (app assumptions, not measured)."
    ),
    "mu.molino.param": "knot (µm)",
    "mu.molino.rd": "estimated r/d",
    "mu.molino.lo": "95% CI low",
    "mu.molino.hi": "95% CI high",
    # ------------------------------------------------------------ crusher: compare with your plant
    "plant.h": "Compare with your plant",
    "plant.intro": (
        "Two optional plant measurements taken **under the conditions of the controls above**: "
        "the capacity and the P80 of the crusher product (without the grizzly fines). The "
        "capacity calibrates the effective bulk density k; the P80 estimates the wear."
    ),
    "plant.q.label": "Measured capacity (t/h)",
    "plant.q.help": "Tonnes per hour the crusher processes under those conditions.",
    "plant.p80.label": "Measured P80 of the crusher product (mm)",
    "plant.p80.help": "P80 of the crusher product, without the fines that pass the grizzly.",
    "plant.q.res": (
        "Model capacity with King's k: {modelo} t/h; measured: {medido} t/h (difference {delta} "
        "%). Plant factor f = measured / model = {f}, giving plant k = k · f = {kplanta} t/m³."
    ),
    "plant.q.motor": (
        "The model says the motor limits (power allows {motor} t/h and the volumetric limit is "
        "{vol} t/h): k cannot be calibrated with that measurement."
    ),
    "plant.q.motor2": (
        "The measurement ({medido} t/h) exceeds what the motor allows in the model ({motor} t/h): "
        "k cannot be calibrated with it. Check the installed power, the Wi or the conditions."
    ),
    "plant.q.rango": "Factor f = {f}, outside {lo}–{hi}: check units or conditions.",
    "plant.btn.usar": "Use my calibration",
    "plant.btn.king": "Back to King's k",
    "plant.cal.activa": "Calibrated with your plant (f = {f}): k = {k} t/m³ instead of {k0} t/m³.",
    "plant.cal.curvas": (
        "Calibrated with your plant (f = {f}): the capacities in the curves and indicators use "
        "k · f."
    ),
    "plant.p80.res": (
        "Implied OSS = measured P80 / (Nordberg P80/OSS = {razon}) = {oss} mm; nominal OSS = "
        "CSS + δ + stroke = {nominal} mm. Difference = {dif} mm."
    ),
    "plant.p80.desgaste": "Estimated wear: δ = {wear} mm (the control has {actual} mm).",
    "plant.p80.neg": "Product finer than the Nordberg curve: check the sampling or the fit.",
    "plant.p80.fuera": "The estimated wear ({wear} mm) is outside the control's range (0–{hi}).",
    "plant.p80.nota": "The inverse uses the Nordberg curve even if another product model is chosen.",
    "plant.btn.desgaste": "Put that wear in the control",
}
