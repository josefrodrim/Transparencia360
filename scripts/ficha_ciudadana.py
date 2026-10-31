"""Ficha ciudadana: página web con un resumen en lenguaje claro por municipalidad.

Uso (desde scripts/): ../.venv/bin/python ficha_ciudadana.py 09 [variante]
  → web/ficha_ciudadana/index.html (plantilla.html + datos incrustados)
  → con variante «mac»: index_mac.html desde plantilla_mac.html (prueba de diseño estilo app de macOS)

Reutiliza los cálculos de sueldos_alcaldes, ranking_transparencia y senales_alerta. Solo agregados: no incluye
nombres de personas (el cargo de alcalde se informa sin nombre).
"""

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import ranking_transparencia as ranking
import senales_alerta as senales
import sueldos_alcaldes as sueldos

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web/ficha_ciudadana"
MARCA = "/*__DATOS__*/null"


def pte_resumen(ubigeo: str, periodo: str | None) -> dict | None:
    """Cifras agregadas del último mes publicado en el PTE (sin nombres)."""
    if not periodo:
        return None
    f = RAIZ / "data/processed/pte_personal" / ranking.SLUGS.get(ubigeo, f"ubigeo-{ubigeo}") / f"{periodo}.csv"
    with f.open() as fh:
        totales = [float(r["total"]) for r in csv.DictReader(fh) if not r["duplicado_de"] and float(r["total"]) > 0]
    if not totales:
        return None
    return {
        "periodo": periodo,
        "personas": len(totales),
        "mediana": round(statistics.median(totales)),
        "minimo": round(min(totales)),
        "maximo": round(max(totales)),
    }


def main(dep: str, variante: str = "") -> None:
    with (RAIZ / "database/seeds/renamu2026_personal.csv").open() as f:
        ren = {r["ubigeo"]: r for r in csv.DictReader(f)}
    mef: dict = defaultdict(float)
    with (RAIZ / f"data/processed/mef_gasto_devengado/{dep}.csv").open() as f:
        for r in csv.DictReader(f):
            a, m = int(r["anio"]), int(r["mes"])
            if a == 2025:
                mef[(r["ubigeo"], r["indicador"], "2025")] += float(r["devengado"])
            if m <= 9 and a in (2025, 2026):
                mef[(r["ubigeo"], r["indicador"], f"{a}s")] += float(r["devengado"])

    alcaldes = {f[1]["ubigeo"]: f for f in sueldos.calcular(dep)}
    filas_rk, publican, _, _, pte_ids = ranking.calcular(dep)
    posicion = {f[1]["ubigeo"]: i for i, f in enumerate(publican, start=1)}
    _, hallazgos = senales.calcular(dep)
    alertas = defaultdict(list)
    for clave, lista in hallazgos.items():
        for m, det in lista:
            titulo, criterio, inocente = senales.SENALES[clave]
            alertas[m["ubigeo"]].append({"titulo": titulo, "detalle": det, "criterio": criterio, "posible": inocente})

    salida = []
    for total, m, e, p in filas_rk:
        u = m["ubigeo"]
        al = alcaldes[u]
        r = ren.get(u, {})
        g = {k: round(mef[(u, k, "2025")]) for k in ("personal", "cas", "locacion_pn", "dietas", "alcalde")}
        p25s, p26s = mef[(u, "personal", "2025s")], mef[(u, "personal", "2026s")]
        salida.append(
            {
                "ubigeo": u,
                "nombre": m["nombre"],
                "tipo": m["tipo"].lower(),
                "provincia": m["provincia"],
                "alcalde": {"mensual": round(al[0]), "anual_2025": round(al[3]), "fuente": al[6]},
                "gasto_2025": g,
                "variacion_2026": round(100 * (p26s / p25s - 1)) if p25s else None,
                "renamu": {
                    "tiene_personal": r.get("tiene_personal"),
                    "total": int(r["total_dic"]) if r.get("total_dic") else None,
                    "cas": int(r["cas_dic"]) if r.get("cas_dic") else None,
                    "locacion": int(r["locacion_dic"]) if r.get("locacion_dic") else None,
                },
                "transparencia": {
                    "puntaje": round(total),
                    "posicion": posicion.get(u),
                    "meses": len(e["periodos"]),
                    "meses_posibles": len(ranking.meses()),
                    "ultimo": e["periodos"][-1] if e["periodos"] else None,
                    "cobertura": round(100 * e["cobertura"]) if e["cobertura"] is not None else None,
                    "ficha_pte": pte_ids.get(u, {}).get("confianza") == "alta",
                    "id_pte": pte_ids.get(u, {}).get("pte_id_entidad") or None,
                },
                "pte": pte_resumen(u, e["periodos"][-1] if e["periodos"] else None),
                "alertas": alertas.get(u, []),
            }
        )

    def mediana(campo, tipo):
        vals = [campo(x) for x in salida if x["tipo"] == tipo and campo(x)]
        return round(statistics.median(vals)) if vals else None

    datos = {
        "departamento": "Huancavelica",
        "corte": {"mef": "2026-10-22", "pte": "2026-10-31", "renamu": "2025-12-31"},
        "referencias": {
            t: {
                "alcalde": mediana(lambda x: x["alcalde"]["mensual"], t),
                "personal": mediana(lambda x: x["gasto_2025"]["personal"], t),
            }
            for t in ("provincial", "distrital")
        },
        "publican": len(publican),
        "municipalidades": sorted(salida, key=lambda x: x["ubigeo"]),
    }
    sufijo = f"_{variante}" if variante else ""
    plantilla = (WEB / f"plantilla{sufijo}.html").read_text(encoding="utf-8")
    if plantilla.count(MARCA) != 1:
        raise SystemExit(f"la plantilla debe contener una vez {MARCA}")
    js = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    destino = WEB / f"index{sufijo}.html"
    destino.write_text(plantilla.replace(MARCA, js), encoding="utf-8")
    print(f"{destino}: {len(salida)} municipalidades")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "09", sys.argv[2] if len(sys.argv) > 2 else "")
