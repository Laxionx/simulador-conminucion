"""Textos en español de la Guía: qué simula, cómo lo calcula, qué devuelve y qué no hace."""

T = {
    "guide.h.simula": "### Qué simula",
    "guide.simula": (
        "Un **circuito de molienda y clasificación**: el mineral chancado entra a un molino de "
        "bolas que lo muele y un hidrociclón separa lo que ya está fino (producto) de lo que "
        "todavía está grueso. El simulador calcula, para cada corriente, cuántas toneladas de "
        "sólidos y de agua lleva y qué tan fino es el mineral, a partir de ecuaciones "
        "publicadas."
    ),
    "guide.circuit": "**Circuito elegido.** {text}",
    "circuit.abierto": (
        "El mineral pasa una sola vez por el molino. Simple, pero el producto sale con gruesos: "
        "no hay nada que los devuelva."
    ),
    "circuit.cerrado_directo": (
        "El mineral fresco entra al molino junto con los gruesos que devuelve el ciclón. La "
        "descarga del molino va al cajón, se diluye y se bombea al ciclón: los finos salen por "
        "el rebalse como producto y los gruesos vuelven al molino."
    ),
    "circuit.cerrado_inverso": (
        "El mineral fresco entra primero al ciclón: si ya trae finos, salen directo al producto "
        "sin pasar por el molino. Solo los gruesos van al molino, y su descarga vuelve al cajón "
        "del ciclón."
    ),
    "guide.h.pasos": "### Cómo lo calcula, paso a paso",
    "step.1.title": "Alimentación",
    "step.1.text": (
        "La granulometría del mineral fresco se describe con una ecuación de dos parámetros, "
        "Rosin-Rammler o Gaudin-Schuhmann (King, 2001)."
    ),
    "step.1.latex": r"P(x) = 1 - e^{-(x/x_{63})^{m}} \qquad P(x) = \min\left[1, (x/k)^{\alpha}\right]",
    "step.2.title": "Molino de bolas",
    "step.2.text": (
        "Cada clase de tamaño se rompe a una velocidad propia (selección de Austin) y sus "
        "fragmentos caen a clases más finas según la función de fractura. El molino es uno o "
        "varios tanques de mezcla perfecta en serie (Whiten, 1974; Austin, Klimpel y Luckie, "
        "1984)."
    ),
    "step.2.latex": (
        r"p_i = \frac{f_i + \sum_{j<i} (r/d)_j\, a_{ij}\, p_j}{1 + (r/d)_i}"
        r"\qquad S_i = \frac{A\,(x_i/1000)^{\alpha}}{1 + (x_i/\mu)^{\Lambda}}"
    ),
    "step.3.title": "Cajón",
    "step.3.text": "Agrega el agua justa para que la pulpa llegue al ciclón con el % de sólidos pedido.",
    "step.3.latex": r"W = \sum m \cdot \frac{100 - \%s}{\%s}",
    "step.4.title": "Hidrociclón",
    "step.4.text": (
        "Cada tamaño se reparte entre la descarga (gruesos) y el rebalse (finos) según la curva "
        "de Whiten; una parte del agua, Rf, arrastra finos sin clasificar a la descarga (Lynch "
        "y Rao, 1975; Kelsall, 1953)."
    ),
    "step.4.latex": (
        r"E_a(x) = R_f + (1 - R_f)\,\frac{e^{\alpha x/d_{50c}} - 1}"
        r"{e^{\alpha x/d_{50c}} + e^{\alpha} - 2}"
    ),
    "step.5.title": "Reciclo",
    "step.5.text": (
        "Los gruesos que vuelven dependen de lo que sale del molino, que depende de los gruesos "
        "que vuelven: se itera hasta que la corriente devuelta no cambie más de una parte en mil "
        "millones. Wegstein acelera la iteración."
    ),
    "step.5.latex": r"x_{k+1} = q\,x_k + (1 - q)\,g(x_k) \qquad q = s/(s - 1)",
    "step.6.title": "Energía y potencia",
    "step.6.text": (
        "Bond (1952) estima la energía para llevar el mineral de F80 a P80. La potencia del "
        "molino sale de su tamaño, su llenado y su giro (Bond, con las correcciones de Rowland y "
        "Kjos, 1980). La velocidad crítica es la que pega las bolas a la pared."
    ),
    "step.6.latex": (
        r"W = 10\,W_i\left(\frac{1}{\sqrt{P_{80}}} - \frac{1}{\sqrt{F_{80}}}\right)"
        r"\qquad N_c = \frac{42{,}3}{\sqrt{D - d}}\ \text{rpm}"
    ),
    "guide.teoria": "Cada ecuación, con su derivación y referencia, en [docs/teoria.md]({url}).",
    "guide.h.datos": "### Qué datos necesita",
    "guide.datos": (
        "Cada dato tiene una ayuda (**?**) en la barra lateral. Para empezar, el botón **Cargar "
        "ejemplo típico** pone todos los valores de la columna «Ejemplo»."
    ),
    "guide.h.salidas": "### Qué devuelve y cómo leerlo",
    "out.1.name": "P80 del producto",
    "out.1.text": (
        "Tamaño bajo el que pasa el 80 % del producto. Es lo que la planta controla: define la "
        "liberación del mineral para la flotación."
    ),
    "out.2.name": "Carga circulante",
    "out.2.text": (
        "Toneladas que vuelven al molino por cada tonelada fresca. Alta = el ciclón devuelve "
        "mucho; el molino trabaja con más carga."
    ),
    "out.3.name": "Energía de Bond",
    "out.3.text": (
        "kWh por tonelada fresca que pide la reducción de tamaño según Bond. Se compara con la "
        "energía que entrega el molino (potencia ÷ t/h): si es menor, el molino no alcanza ese "
        "P80 según Bond. Es un chequeo grueso: no lleva los factores de eficiencia de Rowland."
    ),
    "out.4.name": "Iteraciones",
    "out.4.text": "Cuántas vueltas dio el cálculo del reciclo hasta converger.",
    "out.5.name": "Balance",
    "out.5.text": "Sólidos que entran contra sólidos que salen: debe cerrar casi a cero.",
    "guide.h.limites": "### Lo que no hace",
    "limit.1": "Estado estacionario: no simula arranques, paradas ni cambios en el tiempo.",
    "limit.2": (
        "El ciclón usa una curva de eficiencia con parámetros dados; no calcula el d50c desde la "
        "geometría del equipo (eso es Plitt, disponible en la librería, no en esta app)."
    ),
    "limit.3": (
        "La velocidad de fractura no cambia con la potencia del molino: tiempo de residencia y "
        "potencia se dan por separado."
    ),
    "limit.4": (
        "Pestaña de ajuste: datos sintéticos generados con parámetros conocidos, para mostrar "
        "que el método los recupera; no son datos de una planta."
    ),
}
