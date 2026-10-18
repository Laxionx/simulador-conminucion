"""English texts of the Guide: what it simulates, how it calculates, what it returns and what it
does not do."""

T = {
    "guide.h.simula": "### What it simulates",
    "guide.simula": (
        "A **grinding and classification circuit**: the crushed ore enters a ball mill that "
        "grinds it and a hydrocyclone separates what is already fine (product) from what is "
        "still coarse. The simulator calculates, for each stream, how many tonnes of solids and "
        "water it carries and how fine the ore is, from published equations."
    ),
    "guide.circuit": "**Chosen circuit.** {text}",
    "circuit.abierto": (
        "The ore passes through the mill only once. Simple, but the product leaves with coarse "
        "particles: nothing sends them back."
    ),
    "circuit.cerrado_directo": (
        "The fresh ore enters the mill together with the coarse particles that the cyclone "
        "returns. The mill discharge goes to the sump, is diluted and is pumped to the cyclone: "
        "the fines leave through the overflow as product and the coarse particles return to the "
        "mill."
    ),
    "circuit.cerrado_inverso": (
        "The fresh ore enters the cyclone first: if it already carries fines, they go straight "
        "to the product without passing through the mill. Only the coarse particles go to the "
        "mill, and its discharge returns to the cyclone sump."
    ),
    "guide.h.pasos": "### How it calculates, step by step",
    "step.1.title": "Feed",
    "step.1.text": (
        "The size distribution of the fresh ore is described with a two-parameter equation, "
        "Rosin-Rammler or Gaudin-Schuhmann (King, 2001)."
    ),
    "step.1.latex": r"P(x) = 1 - e^{-(x/x_{63})^{m}} \qquad P(x) = \min\left[1, (x/k)^{\alpha}\right]",
    "step.2.title": "Ball mill",
    "step.2.text": (
        "Each size class breaks at its own rate (Austin's selection) and its fragments fall into "
        "finer classes according to the breakage function. The mill is one or several perfectly "
        "mixed tanks in series (Whiten, 1974; Austin, Klimpel and Luckie, 1984)."
    ),
    "step.2.latex": (
        r"p_i = \frac{f_i + \sum_{j<i} (r/d)_j\, a_{ij}\, p_j}{1 + (r/d)_i}"
        r"\qquad S_i = \frac{A\,(x_i/1000)^{\alpha}}{1 + (x_i/\mu)^{\Lambda}}"
    ),
    "step.3.title": "Sump",
    "step.3.text": (
        "It adds just enough water for the pulp to reach the cyclone at the requested % solids."
    ),
    "step.3.latex": r"W = \sum m \cdot \frac{100 - \%s}{\%s}",
    "step.4.title": "Hydrocyclone",
    "step.4.text": (
        "Each size is split between the underflow (coarse) and the overflow (fines) according to "
        "Whiten's curve; part of the water, Rf, carries unclassified fines into the underflow "
        "(Lynch and Rao, 1975; Kelsall, 1953)."
    ),
    "step.4.latex": (
        r"E_a(x) = R_f + (1 - R_f)\,\frac{e^{\alpha x/d_{50c}} - 1}"
        r"{e^{\alpha x/d_{50c}} + e^{\alpha} - 2}"
    ),
    "step.5.title": "Recycle",
    "step.5.text": (
        "The coarse particles that return depend on what leaves the mill, which depends on the "
        "coarse particles that return: it iterates until the returned stream changes by no more "
        "than one part in a billion. Wegstein accelerates the iteration."
    ),
    "step.5.latex": r"x_{k+1} = q\,x_k + (1 - q)\,g(x_k) \qquad q = s/(s - 1)",
    "step.6.title": "Energy and power",
    "step.6.text": (
        "Bond (1952) estimates the energy to take the ore from F80 to P80. The mill power comes "
        "from its size, its filling and its speed (Bond, with the corrections of Rowland and "
        "Kjos, 1980). The critical speed is the one that pins the balls to the wall."
    ),
    "step.6.latex": (
        r"W = 10\,W_i\left(\frac{1}{\sqrt{P_{80}}} - \frac{1}{\sqrt{F_{80}}}\right)"
        r"\qquad N_c = \frac{42.3}{\sqrt{D - d}}\ \text{rpm}"
    ),
    "guide.teoria": "Each equation, with its derivation and reference, in [docs/teoria.md]({url}) (in Spanish).",
    "guide.h.datos": "### What data it needs",
    "guide.datos": (
        "Each datum has a help (**?**) in the sidebar. To start, the **Load typical example** "
        "button sets all the values of the «Example» column."
    ),
    "guide.h.salidas": "### What it returns and how to read it",
    "out.1.name": "Product P80",
    "out.1.text": (
        "Size below which 80 % of the product passes. It is what the plant controls: it defines "
        "the liberation of the mineral for flotation."
    ),
    "out.2.name": "Circulating load",
    "out.2.text": (
        "Tonnes that return to the mill per fresh tonne. High = the cyclone returns a lot; the "
        "mill works with more load."
    ),
    "out.3.name": "Bond energy",
    "out.3.text": (
        "kWh per fresh tonne that the size reduction asks for according to Bond. It is compared "
        "with the energy the mill delivers (power ÷ t/h): if it is lower, the mill does not "
        "reach that P80 according to Bond. It is a rough check: it carries no Rowland efficiency "
        "factors."
    ),
    "out.4.name": "Iterations",
    "out.4.text": "How many turns the recycle calculation took to converge.",
    "out.5.name": "Balance",
    "out.5.text": "Solids in against solids out: it must close almost to zero.",
    "guide.h.limites": "### What it does not do",
    "limit.1": "Steady state: it does not simulate start-ups, shutdowns or changes in time.",
    "limit.2": (
        "The cyclone uses an efficiency curve with given parameters; it does not calculate the "
        "d50c from the geometry of the equipment (that is Plitt, available in the library, not "
        "in this app)."
    ),
    "limit.3": (
        "The breakage rate does not change with the mill power: residence time and power are "
        "given separately."
    ),
    "limit.4": (
        "Fitting tab: synthetic data generated with known parameters, to show that the method "
        "recovers them; they are not plant data."
    ),
}
