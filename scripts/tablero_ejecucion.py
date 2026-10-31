"""Tablero de ejecución presupuestal (estilo resultados electorales) con los datos de ejecucion_presupuestal.

Uso (desde scripts/): ../.venv/bin/python tablero_ejecucion.py 09
  → web/ejecucion/index.html (plantilla web/ejecucion/plantilla.html + datos incrustados)

Solo montos públicos del MEF por municipalidad, función y proyecto; no hay datos de personas.
"""

import json
import sys
from pathlib import Path

import ejecucion_presupuestal as ejec

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web/ejecucion"
MARCA = "/*__DATOS__*/null"


def main(dep: str) -> None:
    filas, anios, cerrados, en_curso, _, _, recurrentes, _ = ejec.calcular(dep)
    nombres_fn: list[str] = []

    def idx_fn(nombre: str) -> int:
        if nombre not in nombres_fn:
            nombres_fn.append(nombre)
        return nombres_fn.index(nombre)

    codigos_recurrentes = {(v[0]["ubigeo"], v[0]["codigo"]) for v in recurrentes}
    munis = []
    for u, f in sorted(filas.items()):
        m = f["muni"]
        por_anio = {}
        for a, d in f["anios"].items():
            por_anio[a] = {
                # [pim, devengado, pim inversión, devengado inversión, RO no ejecutado, devengado a sep., dic.]
                "v": [
                    round(d[k]) for k in ("pim", "dev", "pim_inv", "dev_inv", "ro_no_ejecutado", "dev_sep", "dev_dic")
                ],
                "f": [[idx_fn(n), round(p), round(dv)] for n, (p, dv) in d["funciones"].items() if p > 0],
            }
        munis.append(
            {
                "u": u,
                "n": m["nombre"],
                "p": m["provincia"],
                "t": m["tipo"].lower(),
                "a": por_anio,
                "o": [
                    [
                        x["anio"],
                        x["codigo"],
                        x["nombre"],
                        idx_fn(x["funcion"]),
                        round(x["pim"]),
                        round(x["avance"], 1),
                        (u, x["codigo"]) in codigos_recurrentes,
                    ]
                    for x in f["obras_paradas"]
                ],
            }
        )
    datos = {
        "departamento": "Huancavelica",
        "anios": anios,
        "cerrados": cerrados,
        "en_curso": en_curso,
        "corte": "2026-10-22",
        "funciones": nombres_fn,
        "umbrales": {
            "semaforo": [90, 75, 60],
            "obra_pim_min": ejec.OBRA_PIM_MIN,
            "obra_avance_max": ejec.OBRA_AVANCE_MAX,
        },
        "munis": munis,
    }
    plantilla = (WEB / "plantilla.html").read_text(encoding="utf-8")
    if plantilla.count(MARCA) != 1:
        raise SystemExit(f"la plantilla debe contener una vez {MARCA}")
    js = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    destino = WEB / "index.html"
    destino.write_text(plantilla.replace(MARCA, js), encoding="utf-8")
    print(f"{destino}: {len(munis)} municipalidades, {len(js) / 1e6:.2f} MB de datos")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "09")
