"""Perfil de una provincia: salarios publicados en el PTE frente al gasto devengado del MEF.

Uso (desde la raíz): .venv/bin/python scripts/perfil_provincia.py 0903 > docs/perfil_angaraes.md

Lee lo ya extraído en data/ (munilens-extract y munilens-mef). Solo publica agregados: sin nombres ni DNI.
"""

import csv
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PTE = RAIZ / "data/processed/pte_personal"
MEF = RAIZ / "data/processed/mef_gasto_devengado/09.csv"
SEED = RAIZ / "database/seeds/municipalidades.csv"
BANDAS = [(0, 1500, "< 1 500"), (1500, 2500, "1 500–2 499"), (2500, 3500, "2 500–3 499"), (3500, 10**9, "≥ 3 500")]


def soles(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def mef_por_mes(prefijo: str) -> dict:
    """{(ubigeo, anio, mes): {indicador: devengado}} sumando unidades ejecutoras."""
    out: dict = defaultdict(lambda: defaultdict(float))
    with MEF.open() as f:
        for r in csv.DictReader(f):
            if r["ubigeo"].startswith(prefijo):
                out[(r["ubigeo"], int(r["anio"]), int(r["mes"]))][r["indicador"]] += float(r["devengado"])
    return out


def pte_periodos(ubigeo: str) -> dict:
    """{'AAAA-MM': [registros sin re-cargas duplicadas]}"""
    out = {}
    for f in sorted((PTE / f"ubigeo-{ubigeo}").glob("*.csv")) if (PTE / f"ubigeo-{ubigeo}").exists() else []:
        with f.open() as fh:
            out[f.stem] = [r for r in csv.DictReader(fh) if not r["duplicado_de"]]
    return out


def main(prefijo: str) -> None:
    with SEED.open() as f:
        munis = [r for r in csv.DictReader(f) if r["ubigeo"].startswith(prefijo)]
    provincia = munis[0]["provincia"]
    mef = mef_por_mes(prefijo)

    def anual(u, anio, ind, meses=range(1, 13)):
        return sum(mef.get((u, anio, m), {}).get(ind, 0.0) for m in meses)

    print(f"# Perfil de la provincia de {provincia}: salarios publicados y gasto en personal\n")
    print("Generado con `scripts/perfil_provincia.py " + prefijo + "` a partir del PTE (Personal, 2024-01 → 2026-10)")
    print("y del MEF (devengado mensual, corte 22/10/2026). Solo agregados: sin nombres ni DNI.")
    print("Definiciones de los indicadores MEF: `docs/mef_gasto_personal_huancavelica.md`.\n")

    print("## 1. Gasto en personal de las municipalidades (MEF)\n")
    print(
        "| Ubigeo | Municipalidad | Personal 2.1 2025 | CAS 2025 | % CAS | Locación PN 2025 | "
        "Personal ene–sep 2026 | Var. vs ene–sep 2025 | Publica salarios (PTE) |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    filas, tot = [], Counter()
    for m in munis:
        u = m["ubigeo"]
        p25, c25, l25 = anual(u, 2025, "personal"), anual(u, 2025, "cas"), anual(u, 2025, "locacion_pn")
        p25s, p26s = anual(u, 2025, "personal", range(1, 10)), anual(u, 2026, "personal", range(1, 10))
        filas.append((p25, u, m["nombre"], c25, l25, p25s, p26s, bool(pte_periodos(u))))
        tot.update(personal=p25, cas=c25, loc=l25, p25s=p25s, p26s=p26s)
    for p25, u, nombre, c25, l25, p25s, p26s, pub in sorted(filas, reverse=True):
        var = f"{100 * (p26s / p25s - 1):+.0f} %" if p25s else "—"
        pct = f"{100 * c25 / p25:.0f} %" if p25 else "—"
        print(
            f"| {u} | {nombre} | {soles(p25)} | {soles(c25)} | {pct} | {soles(l25)} | {soles(p26s)} | {var} | "
            f"{'sí' if pub else 'no'} |"
        )
    var_t = 100 * (tot["p26s"] / tot["p25s"] - 1)
    print(
        f"| | **Total provincia** | **{soles(tot['personal'])}** | **{soles(tot['cas'])}** | "
        f"{100 * tot['cas'] / tot['personal']:.0f} % | **{soles(tot['loc'])}** | **{soles(tot['p26s'])}** | "
        f"{var_t:+.0f} % | {sum(f[-1] for f in filas)}/{len(filas)} |\n"
    )

    print("## 2. Salarios individuales publicados (PTE) y cobertura frente al MEF\n")
    print("Cobertura = suma de totales publicados en el PTE ÷ devengado MEF del mismo mes. El MEF incluye aportes")
    print("del empleador y pagos de meses anteriores, así que una publicación completa queda por debajo del 100 %;")
    print("una cobertura muy baja indica que el PTE solo trae una parte del personal.\n")
    for m in munis:
        u = m["ubigeo"]
        periodos = pte_periodos(u)
        if not periodos:
            continue
        print(f"### {m['nombre']} ({u})\n")
        print(
            "| Periodo | Personas | Regímenes | Suma PTE | Mediana | Máximo | MEF personal 2.1 | MEF CAS | "
            "PTE / MEF 2.1 |"
        )
        print("|---|---|---|---|---|---|---|---|---|")
        personas, todos = set(), []
        for per, rs in periodos.items():
            anio, mes = map(int, per.split("-"))
            tot_rs = [float(r["total"]) for r in rs]
            reg = ", ".join(f"{k} {v}" for k, v in Counter(r["regimen"] for r in rs).most_common())
            g = mef.get((u, anio, mes), {})
            p, c = g.get("personal", 0.0), g.get("cas", 0.0)
            cob = f"{100 * sum(tot_rs) / p:.0f} %" if p else "—"
            print(
                f"| {per} | {len(rs)} | {reg} | {soles(sum(tot_rs))} | {soles(statistics.median(tot_rs))} | "
                f"{soles(max(tot_rs))} | {soles(p)} | {soles(c)} | {cob} |"
            )
            personas |= {r["nombre_busqueda"] for r in rs}
            todos += rs
        bandas = Counter(next(e for lo, hi, e in BANDAS if lo <= float(r["total"]) < hi) for r in todos)
        deps = Counter(r["dependencia"] for r in todos)
        print(
            f"\nNombres distintos en todo el rango: {len(personas)} (mismo nombre ≠ misma persona). "
            "Registros por banda de total mensual (S/): "
            + ", ".join(f"{e}: {bandas[e]}" for _, _, e in BANDAS if bandas[e])
            + "."
        )
        print(
            "Dependencias con más registros: " + "; ".join(f"{d.title()} ({n})" for d, n in deps.most_common(4)) + ".\n"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "0903")
