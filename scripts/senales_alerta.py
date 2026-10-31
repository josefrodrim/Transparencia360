"""Señales de alerta sobre el gasto en personal de las municipalidades de un departamento.

Uso (desde la raíz): .venv/bin/python scripts/senales_alerta.py 09 > docs/senales_alerta_huancavelica.md

Cruza MEF (devengado), RENAMU (personal declarado al INEI) y PTE (salarios publicados). Solo agregados por
municipalidad: no nombra personas. Una señal es un indicio para revisar, no una prueba de irregularidad.
"""

import csv
import glob
import statistics
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SLUGS = {"090101": "mp-huancavelica"}
MESES_25 = [(2025, m) for m in range(1, 13)]
MESES_26 = [(2026, m) for m in range(1, 10)]  # corte MEF: septiembre 2026

SENALES = {
    "sin_personal_declarado": (
        "Declara al INEI no tener personal, pero paga planilla",
        "RENAMU 2026 (P19 = no tiene personal) y aun así el MEF registra gasto CAS en 2025.",
        "Error al llenar el formulario del INEI.",
    ),
    "locacion_mayor_que_planilla": (
        "Paga más en locación de servicios que en toda su planilla",
        "Locación a personas naturales (2.3.2.9) 2025 > personal y obligaciones sociales (2.1) 2025.",
        (
            "Contrataciones temporales legítimas (consultorías, proyectos). Esas personas no figuran en el rubro Personal "
            "del PTE ni tienen derechos laborales."
        ),
    ),
    "salto_gasto_personal": (
        "Gasto en personal 2026 crece más de 25 %",
        "Personal 2.1 ene–sep 2026 frente a ene–sep 2025. 2026 es año de elecciones municipales.",
        "Aumentos dispuestos por norma, nuevas plazas presupuestadas o pago de deudas laborales.",
    ),
    "pagos_alcalde_irregulares": (
        "Pagos al alcalde irregulares en 6 o más meses",
        (
            "Meses de 2025–2026 en los que la compensación del alcalde se devenga en 0 o acumulada (≥ 1,9 veces la "
            "mensual): indica atrasos en la gestión de la planilla."
        ),
        "Retrasos administrativos sin perjuicio económico.",
    ),
    "personal_renamu_vs_pte": (
        "El personal publicado no coincide con el declarado al INEI",
        (
            "Solo para quienes publican: registros en el PTE de 2025-12 frente al total declarado a RENAMU al 31/12/2025, "
            "con una diferencia mayor al 30 %."
        ),
        "RENAMU incluye personal pagado con proyectos de inversión; el PTE puede omitir regímenes.",
    ),
    "locacion_renamu_igual_total": (
        "Declara al INEI el doble o más de locadores que de personal en planilla",
        "RENAMU: personal de locación / orden de servicios al 31/12/2025 ≥ 2 × total de personal en planilla.",
        "Municipalidades que operan principalmente con locadores, o error de llenado.",
    ),
}


def soles(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def main(dep: str) -> None:
    with (RAIZ / "database/seeds/municipalidades.csv").open() as f:
        munis = [r for r in csv.DictReader(f) if r["ubigeo"].startswith(dep)]
    with (RAIZ / "database/seeds/renamu2026_personal.csv").open() as f:
        ren = {r["ubigeo"]: r for r in csv.DictReader(f)}
    mef: dict = defaultdict(lambda: defaultdict(float))
    with (RAIZ / f"data/processed/mef_gasto_devengado/{dep}.csv").open() as f:
        for r in csv.DictReader(f):
            mef[(r["ubigeo"], r["indicador"])][(int(r["anio"]), int(r["mes"]))] += float(r["devengado"])

    def suma(u, ind, meses):
        return sum(mef[(u, ind)].get(k, 0.0) for k in meses)

    hallazgos: dict[str, list[tuple[dict, str]]] = defaultdict(list)
    for m in munis:
        u, r = m["ubigeo"], ren.get(m["ubigeo"], {})
        personal25, cas25, loc25 = (
            suma(u, "personal", MESES_25),
            suma(u, "cas", MESES_25),
            suma(u, "locacion_pn", MESES_25),
        )
        alcalde25, dietas25 = suma(u, "alcalde", MESES_25), suma(u, "dietas", MESES_25)

        if r.get("tiene_personal") == "no" and cas25 > 0:
            otros = personal25 - alcalde25 - dietas25
            hallazgos["sin_personal_declarado"].append(
                (m, f"CAS 2025: S/ {soles(cas25)}; personal 2.1 sin alcalde ni dietas: S/ {soles(otros)}")
            )
        if loc25 > personal25 > 0:
            hallazgos["locacion_mayor_que_planilla"].append(
                (m, f"locación S/ {soles(loc25)} frente a planilla S/ {soles(personal25)} ({loc25 / personal25:.1f}×)")
            )
        p25s, p26s = suma(u, "personal", [(2025, mm) for mm in range(1, 10)]), suma(u, "personal", MESES_26)
        if p25s and p26s / p25s - 1 > 0.25:
            hallazgos["salto_gasto_personal"].append(
                (m, f"S/ {soles(p25s)} → S/ {soles(p26s)} ({100 * (p26s / p25s - 1):+.0f} %)")
            )
        serie = [mef[(u, "alcalde")].get(k, 0.0) for k in MESES_25 + MESES_26]
        nz = [round(v) for v in serie if v > 0]
        if nz:
            base = statistics.mode(nz)  # monto mensual más repetido (los acumulados no lo desplazan)
            irregulares = sum(1 for v in serie if v <= 0 or v >= 1.9 * base)
            if irregulares >= 6:
                hallazgos["pagos_alcalde_irregulares"].append(
                    (m, f"{irregulares} de {len(serie)} meses en 0 o acumulados (mensual típico S/ {soles(base)})")
                )
        if r.get("total_dic"):
            total = int(r["total_dic"])
            pte = glob.glob(str(RAIZ / "data/processed/pte_personal" / SLUGS.get(u, f"ubigeo-{u}") / "2025-12.csv"))
            if pte:
                with open(pte[0]) as fh:
                    publicados = sum(1 for x in csv.DictReader(fh) if not x["duplicado_de"])
                if publicados and abs(publicados - total) / total > 0.30:
                    hallazgos["personal_renamu_vs_pte"].append(
                        (m, f"PTE 2025-12: {publicados} registros; RENAMU 31/12/2025: {total} personas")
                    )
            if r.get("locacion_dic") and int(r["locacion_dic"]) >= 2 * total:
                hallazgos["locacion_renamu_igual_total"].append(
                    (m, f"locación {r['locacion_dic']} frente a {total} en planilla")
                )

    print("# Señales de alerta: gasto en personal de las municipalidades de Huancavelica\n")
    print(f"Generado con `scripts/senales_alerta.py {dep}` a partir del MEF (devengado, corte 22/10/2026), RENAMU 2026")
    print("(personal declarado al INEI) y el PTE (salarios publicados). **Una señal es un indicio para revisar, no una")
    print("prueba de irregularidad**: cada una lista sus explicaciones legítimas posibles. No se nombra a personas.\n")
    print("| Señal | Municipalidades |")
    print("|---|---|")
    for clave, (titulo, _, _) in SENALES.items():
        print(f"| {titulo} | {len(hallazgos[clave])} |")

    for clave, (titulo, criterio, inocente) in SENALES.items():
        print(f"\n## {titulo} ({len(hallazgos[clave])})\n")
        print(f"- **Criterio:** {criterio}")
        print(f"- **Explicaciones posibles:** {inocente}\n")
        if not hallazgos[clave]:
            print("Ninguna municipalidad cumple el criterio.")
            continue
        print("| Ubigeo | Municipalidad | Provincia | Detalle |")
        print("|---|---|---|---|")
        for m, det in sorted(hallazgos[clave], key=lambda x: x[0]["ubigeo"]):
            print(f"| {m['ubigeo']} | {m['nombre']} | {m['provincia']} | {det} |")

    conteo: dict = defaultdict(list)
    for clave, lista in hallazgos.items():
        for m, _ in lista:
            conteo[m["ubigeo"]].append(SENALES[clave][0])
    nombres = {m["ubigeo"]: m["nombre"] for m in munis}
    varias = sorted(((u, s) for u, s in conteo.items() if len(s) >= 2), key=lambda x: (-len(x[1]), x[0]))
    print(f"\n## Municipalidades con dos o más señales ({len(varias)})\n")
    print("| Ubigeo | Municipalidad | Señales |")
    print("|---|---|---|")
    for u, s in varias:
        print(f"| {u} | {nombres[u]} | {len(s)}: {'; '.join(s)} |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "09")
