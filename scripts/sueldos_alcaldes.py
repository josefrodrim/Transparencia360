"""Compensación mensual de los alcaldes de un departamento: MEF (2.1.1.1.1.1) contrastado con el PTE.

Uso (desde la raíz): .venv/bin/python scripts/sueldos_alcaldes.py 09 > docs/sueldos_alcaldes_huancavelica.md

Lee data/processed (munilens-mef con el indicador `alcalde` y munilens-extract). No incluye nombres.
"""

import csv
import glob
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MESES_2026 = range(1, 10)  # corte del MEF: devengado hasta septiembre de 2026


def soles(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def moda(valores: list[float], referencia: list[float] = ()) -> float:
    """Monto más repetido; si es el doble de otro monto observado (pago atrasado acumulado), devuelve la mitad."""
    nz = [round(v) for v in valores if round(v) > 0]
    if not nz:
        return 0.0
    m = statistics.mode(nz)
    todos = Counter(nz) + Counter(round(v) for v in referencia if round(v) > 0)
    mitades = [v for v, n in todos.items() if abs(2 * v - m) <= 2 and n >= 2]  # el doble = dos meses juntos
    if mitades:
        m = mitades[0]
    return float(m)


def pte_alcalde(ubigeo: str, slug_por_ubigeo: dict[str, str]) -> dict[str, float]:
    """{'AAAA-MM': total} de los registros con cargo «ALCALDE…» publicados en el PTE."""
    carpeta = RAIZ / "data/processed/pte_personal" / slug_por_ubigeo.get(ubigeo, f"ubigeo-{ubigeo}")
    out: dict[str, float] = defaultdict(float)
    for f in sorted(glob.glob(str(carpeta / "*.csv"))):
        with open(f) as fh:
            for r in csv.DictReader(fh):
                if not r["duplicado_de"] and r["cargo"].strip().upper().startswith("ALCALDE"):
                    out[Path(f).stem] += float(r["total"])
    return out


def main(dep: str) -> None:
    with (RAIZ / "database/seeds/municipalidades.csv").open() as f:
        munis = [r for r in csv.DictReader(f) if r["ubigeo"].startswith(dep)]
    mef: dict[str, dict] = {
        "alcalde": defaultdict(lambda: defaultdict(float)),
        "ley_servir": defaultdict(lambda: defaultdict(float)),
    }
    with (RAIZ / f"data/processed/mef_gasto_devengado/{dep}.csv").open() as f:
        for r in csv.DictReader(f):
            if r["indicador"] in mef:
                mef[r["indicador"]][r["ubigeo"]][(int(r["anio"]), int(r["mes"]))] += float(r["devengado"])
    slugs = {"090101": "mp-huancavelica"}

    filas = []
    for m in munis:
        u = m["ubigeo"]
        # Partida propia del alcalde; si no existe, la de Ley Servir (algunas municipalidades lo registran ahí).
        propia = {k: v for k, v in mef["alcalde"].get(u, {}).items() if k[0] >= 2025}
        fuente, d = ("MEF", propia) if propia else ("Servir", mef["ley_servir"].get(u, {}))
        v25 = [d.get((2025, i), 0.0) for i in range(1, 13)]
        v26 = [d.get((2026, i), 0.0) for i in MESES_2026]
        mensual_26, mensual_25 = moda(v26, v25), moda(v25, v26)
        irregulares = sum(1 for v in v25 if round(v) != mensual_25) + sum(1 for v in v26 if round(v) != mensual_26)
        pte = pte_alcalde(u, slugs)
        pte_26 = moda([t for p, t in pte.items() if p.startswith("2026")])
        if not d and pte_26:
            mensual_26, mensual_25, fuente = pte_26, moda([t for p, t in pte.items() if p.startswith("2025")]), "PTE"
        filas.append((mensual_26, m, mensual_25, sum(v25), irregulares, pte_26, fuente))

    print("# Compensación mensual de los alcaldes de Huancavelica\n")
    print(f"Generado con `scripts/sueldos_alcaldes.py {dep}`. Fuente principal: MEF, devengado mensual, específica")
    print("2.1.1.1.1.1 «Funcionarios elegidos por elección política» (corte 22/10/2026; 2026 = enero–septiembre).")
    print("La fija el D.S. 413-2019-EF según la municipalidad (Ley 30057, art. 52), no el concejo. Montos brutos.\n")
    print(
        "- **Mensual**: el monto que más se repite en los meses con pago (los meses en 0 seguidos de un pago doble son"
    )
    print("  pagos atrasados, no cambios de sueldo).")
    print("- **Devengado 2025**: suma de los 12 meses tal como la registra el MEF (incluye atrasos y ajustes).")
    print("- **Meses irregulares**: meses de 2025–2026 cuyo devengado no coincide con el mensual (0, dobles, ajustes).")
    print("- **PTE 2026**: lo que la municipalidad publicó para el cargo «Alcalde» en el Portal de Transparencia.")
    print(
        "- **¹** Sin partida 2.1.1.1.1.1: se usa 2.1.1.1.1.8 «Personal de la Ley Servir», donde estas municipalidades"
    )
    print(
        "  registran al alcalde (Ley 30057). Es probable pero no seguro: esa partida puede incluir a otros servidores.\n"
    )
    print(
        "| # | Ubigeo | Municipalidad | Provincia | Mensual 2026 | Mensual 2025 | Devengado 2025 | "
        "Meses irregulares | PTE 2026 |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for i, (m26, m, m25, t25, irr, pte26, fuente) in enumerate(sorted(filas, key=lambda x: -x[0]), start=1):
        marca = {"PTE": " (PTE)", "Servir": " ¹"}.get(fuente, "")
        print(
            f"| {i} | {m['ubigeo']} | {m['nombre']} | {m['provincia']} | "
            f"{soles(m26) if m26 else '—'}{marca} | {soles(m25) if m25 else '—'} | "
            f"{soles(t25) if t25 else '—'} | {irr if m26 and fuente != 'PTE' else '—'} | "
            f"{soles(pte26) if pte26 else '—'} |"
        )

    con = [f[0] for f in filas if f[0]]
    print(
        f"\n**Resumen:** {len(con)} de {len(filas)} alcaldes con monto identificado. Mediana mensual 2026: "
        f"S/ {soles(statistics.median(con))}; rango S/ {soles(min(con))} – {soles(max(con))}."
    )
    dist = Counter(f[0] for f in filas if f[1]["tipo"].lower().startswith("distr") and f[0])
    print(
        "Montos distritales más frecuentes: " + ", ".join(f"S/ {soles(v)} ({n})" for v, n in dist.most_common(5)) + "."
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "09")
