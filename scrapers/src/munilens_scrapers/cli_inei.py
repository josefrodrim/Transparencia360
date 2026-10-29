"""CLI: descarga el Directorio Nacional de Municipalidades del INEI y genera el seed versionable.

Ejemplo:
    munilens-inei --url "https://cdn.www.gob.pe/uploads/document/file/.../directorio-...-octubre-2026.xlsx"
"""

import argparse
import csv
import json
import logging
from collections import Counter
from pathlib import Path

from munilens_scrapers.client import PoliteClient
from munilens_scrapers.logging_setup import setup_logging
from munilens_scrapers.sources import inei_directorio as inei
from munilens_scrapers.storage import RawStore

log = logging.getLogger("munilens.inei")

SEED_DEFAULT = Path(__file__).resolve().parents[3] / "database" / "seeds" / "municipalidades.csv"
# El seed versionado no incluye el nombre del alcalde (dato personal): queda solo en data/processed.
COLUMNAS_SEED = ["ubigeo", "departamento", "provincia", "distrito", "tipo", "nombre", "nota_inei"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="URL del XLSX del directorio (cambia con cada edición)")
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--seed", type=Path, default=SEED_DEFAULT)
    args = ap.parse_args(argv)

    setup_logging()
    content = PoliteClient().get(args.url).content
    directorio = inei.leer_xlsx(content)
    periodo = directorio.actualizado_al.isoformat()
    ext = RawStore(args.data_dir / "raw").guardar(inei.FUENTE, "nacional", periodo, args.url, content, ext="xlsx")

    errores = inei.validar(directorio.municipalidades)
    for e in errores:
        log.error("inconsistencia", extra={"ctx": {"detalle": e}})
    if errores:
        return 1

    munis = sorted(directorio.municipalidades, key=lambda m: m.ubigeo)
    args.seed.parent.mkdir(parents=True, exist_ok=True)
    with args.seed.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNAS_SEED)
        for m in munis:
            w.writerow([m.ubigeo, m.departamento, m.provincia, m.distrito, m.tipo, m.nombre, m.nota or ""])
    (args.seed.with_suffix(".meta.json")).write_text(
        json.dumps(
            {
                "fuente": "INEI - Registro Nacional de Municipalidades (RENAMU)",
                "pagina": inei.PAGINA,
                "url_archivo": args.url,
                "sha256_archivo": ext.sha256,
                "actualizado_al": periodo,
                "municipalidades": len(munis),
                "por_tipo": dict(Counter(m.tipo for m in munis)),
                "notas_inei": directorio.notas,
                "correcciones_aplicadas": directorio.correcciones,
                "campos_excluidos": ["alcalde", "sexo", "dirección", "teléfonos", "correo electrónico"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    procesado = args.data_dir / "processed" / inei.FUENTE / f"{periodo}.csv"
    procesado.parent.mkdir(parents=True, exist_ok=True)
    with procesado.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([*COLUMNAS_SEED, "alcalde"])
        for m in munis:
            w.writerow([m.ubigeo, m.departamento, m.provincia, m.distrito, m.tipo, m.nombre, m.nota or "", m.alcalde])

    log.info(
        "directorio procesado",
        extra={
            "ctx": {
                "actualizado_al": periodo,
                "municipalidades": len(munis),
                "estado_raw": ext.estado,
                "seed": str(args.seed),
            }
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
