"""CLI: descarga los microdatos RENAMU (F01) del INEI y genera el seed de personal municipal por régimen.

Ejemplo (RENAMU 2026: encuesta 1049, módulo 1963; personal al 31/12/2025 y al 31/03/2026):
    munilens-renamu --anio 2026 --encuesta 1049 --modulo 1963
"""

import argparse
import csv
import json
import logging
from pathlib import Path

from munilens_scrapers.client import PoliteClient
from munilens_scrapers.logging_setup import setup_logging
from munilens_scrapers.sources import inei_renamu as renamu
from munilens_scrapers.storage import RawStore

log = logging.getLogger("munilens.renamu")

SEEDS = Path(__file__).resolve().parents[3] / "database" / "seeds"
COLUMNAS = [
    "ubigeo",
    "tiene_personal",
    "total_dic",
    "d276_nombrado_dic",
    "d276_contratado_dic",
    "d728_dic",
    "cas_dic",
    "funcionarios_dic",
    "funcionarios_cas_dic",
    "locacion_dic",
    "total_mar",
    "locacion_mar",
]


def _v(x: int | None) -> str:
    return "" if x is None else str(x)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--anio", required=True, type=int, help="año de la edición RENAMU (el personal es de dic. anterior)"
    )
    ap.add_argument("--encuesta", required=True, help="código de encuesta en el portal de microdatos")
    ap.add_argument("--modulo", required=True, help="código de módulo en el portal de microdatos")
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--seed", type=Path, default=None)
    args = ap.parse_args(argv)

    setup_logging()
    url = renamu.url_csv(args.encuesta, args.modulo)
    content = PoliteClient().get(url).content
    ext = RawStore(args.data_dir / "raw").guardar(renamu.FUENTE, "nacional", str(args.anio), url, content, ext="zip")
    archivo, registros = renamu.leer_zip(content)

    errores = renamu.validar(registros)
    for e in errores:
        log.error("inconsistencia", extra={"ctx": {"detalle": e}})
    if errores:
        return 1

    seed = args.seed or SEEDS / f"renamu{args.anio}_personal.csv"
    seed.parent.mkdir(parents=True, exist_ok=True)
    with seed.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNAS)
        for r in sorted(registros, key=lambda r: r.ubigeo):
            reg = r.por_regimen_dic
            w.writerow(
                [
                    r.ubigeo,
                    "si" if r.tiene_personal else "no",
                    _v(r.total_dic),
                    reg["276_nombrado"],
                    reg["276_contratado"],
                    reg["728"],
                    reg["cas"],
                    _v(r.funcionarios),
                    _v(r.funcionarios_cas),
                    _v(r.locacion_dic),
                    _v(r.total_mar),
                    _v(r.locacion_mar),
                ]
            )
    seed.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "fuente": "INEI - Registro Nacional de Municipalidades (RENAMU), formulario F01, pregunta 19",
                "portal": renamu.PORTAL,
                "url_archivo": url,
                "archivo_csv": archivo,
                "sha256_archivo": ext.sha256,
                "edicion": args.anio,
                "corte_dic": f"{args.anio - 1}-12-31",
                "corte_mar": f"{args.anio}-03-31",
                "municipalidades": len(registros),
                "nota": "Conteos declarados por cada municipalidad al INEI; *_dic al 31 de diciembre del año anterior.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    log.info(
        "renamu procesado",
        extra={"ctx": {"municipalidades": len(registros), "estado_raw": ext.estado, "seed": str(seed)}},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
