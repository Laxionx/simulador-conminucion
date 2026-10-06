"""Caso de referencia (circuito cerrado directo) y generador de docs/caso-validacion-modsim.md."""

from __future__ import annotations

import sys
from pathlib import Path

from .circuits import CircuitConfig, CircuitResult, simulate
from .classifier import EfficiencyCurve
from .fracture import Fracture
from .mill import AustinSelection, BallMill
from .sizes import SizeGrid, rosin_rammler
from .stream import Stream

DOC_PATH = Path(__file__).resolve().parents[1] / "docs" / "caso-validacion-modsim.md"
FEED_TPH = 100.0
X63, M_RR = 3200.0, 1.0


def reference_case() -> CircuitConfig:
    grid = SizeGrid.geometric(top=9500.0, n=17)
    fresh = Stream.from_fractions(grid, rosin_rammler(grid, X63, M_RR), FEED_TPH, water=0.0)
    mill = BallMill(AustinSelection(A=0.8, alpha=0.9, mu=2500.0, lam=3.0, tau=3.0), Fracture())
    return CircuitConfig(fresh, mill, EfficiencyCurve(100.0, 3.0, 0.2), 45.0, 14.0)


def _table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def _results_rows(res: CircuitResult) -> list[list[str]]:
    s = res.streams
    rows = [
        ["P80 del producto (overflow), µm", f"{s['overflow'].p80:.2f}", ""],
        ["Carga circulante (UF sólidos / alim. fresca)", f"{res.circulating_load:.4f}", ""],
    ]
    for name in ("alim_molino", "descarga_molino", "alim_ciclon", "underflow", "overflow"):
        rows.append([f"{name}: sólidos, t/h", f"{s[name].total_solids:.3f}", ""])
        rows.append([f"{name}: agua, t/h", f"{s[name].water:.3f}", ""])
        rows.append([f"{name}: % sólidos", f"{s[name].pct_solids:.2f}", ""])
    rows.append(["Energía de Bond del circuito, kWh/t (Wi=14)", f"{res.bond_kwh_t:.3f}", "n/a"])
    return rows


def render_markdown() -> str:
    cfg = reference_case()
    res = simulate("cerrado_directo", cfg, tol=1e-12)
    g, mill = cfg.fresh.grid, cfg.mill
    sel, fr, cl = mill.selection, mill.fracture, cfg.classifier
    feed = cfg.fresh
    cls_rows = []
    for k in range(g.n):
        lo = f"{g.sieves[k + 1]:.1f}" if k < g.n - 1 else "0"
        cls_rows.append(
            [
                str(k + 1),
                f"{g.sieves[k]:.1f}",
                lo,
                f"{g.sizes[k]:.1f}",
                f"{100 * feed.fractions[k]:.3f}",
                f"{sel.selection(g)[k]:.4f}" if k < g.n - 1 else "0 (fondo)",
                f"{100 * float(cl.efficiency(g.sizes[k])):.2f}",
            ]
        )
    parts = [
        "# Caso de validación cruzada con MODSIM 3.6",
        "",
        "Circuito cerrado **directo**: alimentación fresca -> molino de bolas -> cajón (agua de "
        "dilución) -> hidrociclón; underflow -> molino; overflow = producto. Todos los datos "
        "están listos para cargarlos a mano en MODSIM 3.6; la columna «MODSIM» queda vacía para "
        "que se complete con la corrida del usuario. Este documento se regenera con "
        "`python -m conminucion.validacion`.",
        "",
        "## 1. Clases de tamaño y alimentación",
        "",
        f"Serie geométrica de razón √2 desde {g.sieves[0]:.0f} µm ({g.n} tamices; la clase "
        f"{g.n} es el fondo). Alimentación fresca: {FEED_TPH:.0f} t/h de sólidos secos, "
        f"Rosin-Rammler x63 = {X63:.0f} µm, m = {M_RR:g}, truncada en el tamiz superior; "
        f"densidad de sólidos {feed.rho_s} t/m³; F80 = {feed.p80:.1f} µm.",
        "",
        _table(
            [
                "Clase",
                "Tamiz sup. (µm)",
                "Tamiz inf. (µm)",
                "Tamaño repr. (µm)",
                "Alimentación (% masa)",
                "S_i (1/min)",
                "Ea ciclón (%)",
            ],
            cls_rows,
        ),
        "",
        "## 2. Parámetros del molino de bolas (Austin)",
        "",
        _table(
            ["Parámetro", "Valor"],
            [
                ["S_i = A (x/1000)^α / (1 + (x/μ)^Λ), x en µm, S en 1/min", ""],
                ["A (1/min)", f"{sel.A}"],
                ["α", f"{sel.alpha}"],
                ["μ (µm)", f"{sel.mu}"],
                ["Λ", f"{sel.lam}"],
                ["τ, tiempo de residencia medio (min)", f"{sel.tau}"],
                ["Mezcladores perfectos en serie", f"{mill.n_mixers}"],
                ["Agua de adición al molino (t/h)", f"{mill.added_water}"],
            ],
        ),
        "",
        "Función de fractura acumulada B(k|j) = φ (s_k/s_j)^γ + (1-φ) (s_k/s_j)^β, "
        "con s_k el tamiz superior de la clase k:",
        "",
        _table(["φ", "γ", "β"], [[f"{fr.phi}", f"{fr.gamma}", f"{fr.beta}"]]),
        "",
        "## 3. Hidrociclón (curva de eficiencia)",
        "",
        "Ec(x) = (exp(α x/d50c) - 1) / (exp(α x/d50c) + exp(α) - 2);  Ea = Rf + (1-Rf) Ec.",
        "",
        _table(
            ["d50c (µm)", "α", "Rf (fracción del agua al underflow)", "% sólidos alim. ciclón"],
            [[f"{cl.d50c}", f"{cl.alpha}", f"{cl.rf}", f"{cfg.cyclone_feed_pct_solids}"]],
        ),
        "",
        "## 4. Resultados de nuestro simulador",
        "",
        f"Convergencia: {res.solution.iterations} iteraciones de sustitución sucesiva "
        "(tolerancia relativa 1e-12). Error de balance de sólidos del circuito: "
        f"{res.balance['error_solidos']:.2e} t/h.",
        "",
        _table(["Magnitud", "conminucion", "MODSIM"], _results_rows(res)),
        "",
        "## 5. Convenciones que podrían diferir entre ambos programas",
        "",
        "- **Clases de tamaño**: aquí la clase k es [s_{k+1}, s_k) y el fondo va de 0 a s_n, con "
        "tamaño representativo = media geométrica (fondo: s_n/√2). Verificar cómo define MODSIM "
        "los intervalos y su tamaño representativo (afecta S_i, Ea y P80).",
        "- **Fractura**: se usa la forma acumulada normalizada para que Σ a_kj = 1. Otra "
        "normalización (p. ej. sobre otra clase de referencia) cambia la distribución del "
        "producto fracturado.",
        "- **Selección**: S_i se evalúa en el tamaño representativo; (r/d)_i = S_i τ con un "
        "único mezclador. Otro número de mezcladores o parametrización lleva a otra descarga.",
        "- **Interpolación de P80**: log-lineal del pasante entre tamices; otros programas "
        "pueden usar splines o interpolación lineal.",
        "- **Ciclón**: curva de Whiten/Lynch-Rao con bypass de agua Rf aplicado también a los "
        "finos; la forma exacta de la curva y el bypass en MODSIM debe confirmarse.",
        "- **Agua**: el cajón agrega agua hasta el % de sólidos fijado; el molino no agrega agua.",
        "- **Convergencia**: tolerancia y criterio de corte de reciclo distintos dan diferencias "
        "en la 4.ª-6.ª cifra de la carga circulante.",
        "",
    ]
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    text = render_markdown()
    DOC_PATH.write_text(text, encoding="utf-8")
    res = simulate("cerrado_directo", reference_case(), tol=1e-12)
    s = res.streams
    out = (
        f"P80 producto = {s['overflow'].p80:.2f} um | carga circulante = "
        f"{res.circulating_load:.4f} | F80 = {s['alimentacion_fresca'].p80:.1f} um | "
        f"Bond circuito = {res.bond_kwh_t:.3f} kWh/t | iteraciones = {res.solution.iterations}"
    )
    print(out)
    print(res.table().to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"Escrito: {DOC_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
