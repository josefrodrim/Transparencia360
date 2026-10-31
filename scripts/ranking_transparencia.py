"""Ranking de transparencia salarial de las municipalidades de un departamento (PTE frente al MEF).

Uso (desde la raíz): .venv/bin/python scripts/ranking_transparencia.py 09 > docs/ranking_transparencia_huancavelica.md

Lee data/processed (munilens-extract, munilens-mef) y los seeds. Solo agregados: sin nombres ni DNI.
Puntaje 0–100 (criterios y pesos documentados en la salida):
  publicación 40 · completitud 25 · actualidad 15 · oportunidad 10 · calidad 10.
"""

import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESDE, HASTA = (2024, 1), (2026, 10)
CORTE = date(2026, 10, 31)
COBERTURA_PLENA = 0.80  # el MEF suma aportes del empleador: una publicación completa ronda el 80 %
COBERTURA_MAX = 1.20
MESES_MIN = 6  # meses publicados necesarios para obtener toda la puntuación de completitud
ERRORES_REGISTRO = {"total_inconsistente", "nombre_incompleto", "total_cero"}
SLUGS = {"090101": "mp-huancavelica"}


def meses() -> list[str]:
    (a, m), out = DESDE, []
    while (a, m) <= HASTA:
        out.append(f"{a}-{m:02d}")
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return out


def fin_de_mes(periodo: str) -> date:
    a, m = map(int, periodo.split("-"))
    a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return date.fromordinal(date(a, m, 1).toordinal() - 1)


def soles(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def evaluar(ubigeo: str, mef_personal: dict) -> dict:
    carpeta = RAIZ / "data/processed/pte_personal" / SLUGS.get(ubigeo, f"ubigeo-{ubigeo}")
    periodos, coberturas, demoras = [], [], []
    registros = con_error = 0
    for per in meses():
        f = carpeta / f"{per}.calidad.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        est = d["estadisticas"]
        n = est.get("registros_unicos") or 0
        if not n:
            continue
        periodos.append(per)
        registros += n
        con_error += sum(1 for h in d["hallazgos"] if h["codigo"] in ERRORES_REGISTRO and h.get("pte_id_personal"))
        a, m = map(int, per.split("-"))
        if mef := mef_personal.get((a, m)):
            coberturas.append(float(est["suma_total"]) / mef)
        lotes = est.get("lotes_por_fecha_registro") or {}
        if lotes:  # fecha del lote principal de carga
            principal = max(lotes, key=lotes.get)
            demoras.append((date.fromisoformat(principal) - fin_de_mes(per)).days)
    return {
        "periodos": periodos,
        "cobertura": statistics.median(coberturas) if coberturas else None,
        "demora": statistics.median(demoras) if demoras else None,
        "pct_error": con_error / registros if registros else None,
        "registros": registros,
    }


def puntaje(e: dict) -> dict[str, float]:
    if not e["periodos"]:
        return {"publicacion": 0, "completitud": 0, "actualidad": 0, "oportunidad": 0, "calidad": 0}
    ultimo = fin_de_mes(e["periodos"][-1])
    evidencia = min(len(e["periodos"]) / MESES_MIN, 1)  # completitud, oportunidad y calidad exigen ≥ 6 meses
    antig = (CORTE.year - ultimo.year) * 12 + CORTE.month - ultimo.month  # meses desde el último publicado
    return {
        "publicacion": 40 * len(e["periodos"]) / len(meses()),
        # > 120 % no es interpretable (cargas erróneas o atípicas); con pocos meses no se demuestra completitud
        "completitud": 0
        if (e["cobertura"] or 0) > COBERTURA_MAX
        else 25 * min((e["cobertura"] or 0) / COBERTURA_PLENA, 1) * evidencia,
        "actualidad": 15 * max(0, 1 - max(antig - 2, 0) / 22),  # completo si ≤ 2 meses; 0 a los 24
        "oportunidad": 10 * max(0, 1 - max((e["demora"] or 0) - 30, 0) / 150) * evidencia
        if e["demora"] is not None
        else 0,
        "calidad": 10 * (1 - min(e["pct_error"] or 0, 1)) * evidencia,
    }


def main(dep: str) -> None:
    with (RAIZ / "database/seeds/municipalidades.csv").open() as f:
        munis = [r for r in csv.DictReader(f) if r["ubigeo"].startswith(dep)]
    with (RAIZ / f"database/seeds/pte_entidades_{dep}.csv").open() as f:
        pte_ids = {r["ubigeo"]: r for r in csv.DictReader(f)}
    mef: dict = defaultdict(dict)
    personal_2025: dict = defaultdict(float)
    with (RAIZ / f"data/processed/mef_gasto_devengado/{dep}.csv").open() as f:
        for r in csv.DictReader(f):
            if r["indicador"] == "personal":
                k = (int(r["anio"]), int(r["mes"]))
                mef[r["ubigeo"]][k] = mef[r["ubigeo"]].get(k, 0.0) + float(r["devengado"])
                if r["anio"] == "2025":
                    personal_2025[r["ubigeo"]] += float(r["devengado"])

    filas = []
    for m in munis:
        e = evaluar(m["ubigeo"], mef.get(m["ubigeo"], {}))
        p = puntaje(e)
        filas.append((round(sum(p.values()), 1), m, e, p))
    publican = sorted((f for f in filas if f[2]["periodos"]), key=lambda f: -f[0])
    no_publican = sorted((f for f in filas if not f[2]["periodos"]), key=lambda f: -personal_2025[f[1]["ubigeo"]])

    print("# Ranking de transparencia salarial: municipalidades de Huancavelica\n")
    print(
        f"Generado con `scripts/ranking_transparencia.py {dep}`. Mide si cada municipalidad publica los salarios de su"
    )
    print("personal en el Portal de Transparencia Estándar (PTE, rubro Personal) entre 2024-01 y 2026-10, y qué tan")
    print("completo, actual y limpio es lo publicado. Corte: 31/10/2026.\n")
    print("| Criterio | Puntos | Cómo se mide |")
    print("|---|---|---|")
    print(f"| Publicación | 40 | Meses con datos sobre los {len(meses())} del periodo |")
    print(
        "| Completitud | 25 | Mediana de (suma publicada ÷ gasto en personal 2.1 del MEF del mismo mes): 80 % o más = 25; "
        "más de 120 % (⚠, no interpretable) = 0 |"
    )
    print("| Actualidad | 15 | Antigüedad del último mes publicado: 15 si tiene ≤ 2 meses, 0 si tiene 24 o más |")
    print("| Oportunidad | 10 | Mediana de días entre el fin del mes y la carga principal: 10 si ≤ 30, 0 si ≥ 180 |")
    print(
        "| Calidad | 10 | Proporción de registros sin errores (total ≠ suma de componentes, total 0, nombre incompleto) |"
    )
    print(
        "\nCompletitud, oportunidad y calidad se escalan si hay menos de 6 meses publicados: un solo mes no basta para"
    )
    print("evaluar cómo publica una municipalidad.")
    print(
        "\nLas municipalidades que no publicaron ningún mes tienen 0 puntos y se listan aparte, ordenadas por su gasto"
    )
    print("en personal (cuanto más gastan, más pesa la falta de información).\n")

    print(f"## Publican salarios ({len(publican)} de {len(filas)})\n")
    print(
        "| # | Municipalidad | Puntaje | Meses publicados | Último mes | Completitud | Demora (días) | "
        "Registros con error | Publicación | Completitud | Actualidad | Oportunidad | Calidad |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, (total, m, e, p) in enumerate(publican, start=1):
        cob = f"{100 * e['cobertura']:.0f} %" if e["cobertura"] is not None else "—"
        if (e["cobertura"] or 0) > COBERTURA_MAX:
            cob += " ⚠"
        dem = f"{max(e['demora'], 0):.0f}" if e["demora"] is not None else "—"
        err = f"{100 * e['pct_error']:.0f} %" if e["pct_error"] is not None else "—"
        print(
            f"| {i} | {m['nombre']} ({m['ubigeo']}) | **{total:.0f}** | {len(e['periodos'])}/{len(meses())} | "
            f"{e['periodos'][-1]} | {cob} | {dem} | {err} | {p['publicacion']:.0f} | {p['completitud']:.0f} | "
            f"{p['actualidad']:.0f} | {p['oportunidad']:.0f} | {p['calidad']:.0f} |"
        )

    print(f"\n## No publican salarios ({len(no_publican)} de {len(filas)}): 0 puntos\n")
    print("| # | Municipalidad | Provincia | Gasto en personal 2025 (MEF) | Ficha en el PTE |")
    print("|---|---|---|---|---|")
    for i, (_, m, _, _) in enumerate(no_publican, start=1):
        ficha = pte_ids.get(m["ubigeo"], {}).get("confianza", "")
        ficha = "sí" if ficha == "alta" else "sin confirmar"
        print(
            f"| {i} | {m['nombre']} ({m['ubigeo']}) | {m['provincia']} | "
            f"{soles(personal_2025[m['ubigeo']])} | {ficha} |"
        )

    gasto_total = sum(personal_2025.values())
    gasto_pub = sum(personal_2025[f[1]["ubigeo"]] for f in publican)
    print(
        f"\n**Resumen:** {len(publican)} de {len(filas)} municipalidades publican algo; juntas representan el "
        f"{100 * gasto_pub / gasto_total:.0f} % del gasto en personal del departamento en 2025 "
        f"(S/ {soles(gasto_pub)} de S/ {soles(gasto_total)}). Las otras {len(no_publican)} gastaron "
        f"S/ {soles(gasto_total - gasto_pub)} sin publicar un solo salario."
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "09")
