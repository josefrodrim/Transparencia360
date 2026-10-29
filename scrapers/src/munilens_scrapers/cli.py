"""CLI: extrae el rubro Personal del PTE para una entidad y un rango de periodos.

Ejemplo:
    munilens-extract --entidad mp-huancavelica --desde 2026-01 --hasta 2026-09
"""

import argparse
import csv
import json
import logging
import tomllib
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path

import requests

from munilens_scrapers.client import PoliteClient, RobotsDisallowedError
from munilens_scrapers.logging_setup import setup_logging
from munilens_scrapers.sources import pte_personal as pte
from munilens_scrapers.storage import Extraccion, RawStore
from munilens_scrapers.validate import ReporteCalidad, duplicados_exactos, validar

log = logging.getLogger("munilens.extract")

CONFIG_DEFAULT = Path(__file__).resolve().parents[2] / "config" / "entidades.toml"

COLUMNAS_SALIDA = [
    "fuente",
    "url_origen",
    "sha256_documento",
    "extraido_en",
    "entidad_slug",
    "pte_id_personal",
    "ruc_entidad",
    "anio",
    "mes",
    "regimen_codigo",
    "regimen",
    "apellido_paterno",
    "apellido_materno",
    "nombres",
    "nombre_publicado",
    "nombre_busqueda",
    "cargo",
    "dependencia",
    "remuneraciones",
    "honorarios",
    "incentivo",
    "gratificacion",
    "otros_beneficios",
    "total",
    "observaciones",
    "fecha_registro_pte",
    "duplicado_de",
]


SEEDS = Path(__file__).resolve().parents[3] / "database" / "seeds"


def cargar_por_ubigeo(ubigeo: str, seeds: Path = SEEDS) -> dict:
    """Entidad a partir de los seeds (directorio INEI + cruce PTE). Solo cruces de confianza alta."""
    with (seeds / "municipalidades.csv").open(encoding="utf-8", newline="") as fh:
        muni = next((r for r in csv.DictReader(fh) if r["ubigeo"] == ubigeo), None)
    if muni is None:
        raise SystemExit(f"Ubigeo {ubigeo} no está en el directorio INEI")
    with (seeds / f"pte_entidades_{ubigeo[:2]}.csv").open(encoding="utf-8", newline="") as fh:
        cruce = next((r for r in csv.DictReader(fh) if r["ubigeo"] == ubigeo), None)
    if cruce is None or cruce["confianza"] != "alta":
        raise SystemExit(f"Ubigeo {ubigeo} sin id PTE de confianza alta")
    return {
        "slug": f"ubigeo-{ubigeo}",
        "nombre": muni["nombre"],
        "ubigeo": ubigeo,
        "pte_id_entidad": int(cruce["pte_id_entidad"]),
        "ruc": None,
    }


def cargar_entidad(slug: str, config: Path) -> dict:
    with config.open("rb") as fh:
        entidades = tomllib.load(fh)["entidad"]
    for ent in entidades:
        if ent["slug"] == slug:
            return ent
    raise SystemExit(f"Entidad '{slug}' no está en {config}")


def periodos(desde: str, hasta: str) -> Iterator[tuple[int, int]]:
    anio, mes = map(int, desde.split("-"))
    fin = tuple(map(int, hasta.split("-")))
    while (anio, mes) <= fin:
        yield anio, mes
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)


def escribir_procesado(path: Path, registros: list[pte.RegistroPersonal], ext: Extraccion, slug: str) -> None:
    dup = duplicados_exactos(registros)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS_SALIDA)
        w.writeheader()
        for r in registros:
            fila = asdict(r)
            fila.update(
                fuente=pte.FUENTE,
                url_origen=ext.url,
                sha256_documento=ext.sha256,
                extraido_en=ext.extraido_en,
                entidad_slug=slug,
                nombre_publicado=r.nombre_publicado,
                nombre_busqueda=r.nombre_busqueda,
                fecha_registro_pte=r.fecha_registro_pte.isoformat(),
                duplicado_de=dup.get(r.pte_id_personal, ""),
            )
            w.writerow(fila)


def procesar_periodo(
    client: PoliteClient, store: RawStore, data_dir: Path, ent: dict, anio: int, mes: int
) -> tuple[Extraccion, ReporteCalidad | None]:
    slug, periodo = ent["slug"], f"{anio:04d}-{mes:02d}"
    url = pte.url_descarga(ent["pte_id_entidad"], anio, mes)
    try:
        content = client.get(url).content
    except (requests.RequestException, RobotsDisallowedError) as exc:
        log.error("fallo de descarga", extra={"ctx": {"periodo": periodo, "error": repr(exc)}})
        return store.registrar_error(pte.FUENTE, slug, periodo, url, repr(exc)), None

    huella = pte.huella_csv(content) if content.strip() else None
    ext = store.guardar(pte.FUENTE, slug, periodo, url, content, huella=huella)
    if ext.estado == "sin_datos":
        return ext, None

    registros = [pte.normalizar(f) for f in pte.leer_csv(content)]
    reporte = validar(registros, anio, mes, ent["ruc"])
    salida = data_dir / "processed" / pte.FUENTE / slug
    escribir_procesado(salida / f"{periodo}.csv", registros, ext, slug)
    (salida / f"{periodo}.calidad.json").write_text(
        json.dumps(asdict(reporte), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(
        "periodo procesado",
        extra={
            "ctx": {
                "periodo": periodo,
                "estado": ext.estado,
                "registros": reporte.registros,
                "errores": reporte.errores,
                "advertencias": reporte.advertencias,
            }
        },
    )
    return ext, reporte


def resumen_markdown(ent: dict, resultados: list[tuple[Extraccion, ReporteCalidad | None]]) -> str:
    lineas = [
        f"# Reporte de extracción — {ent['nombre']}",
        "",
        f"Fuente: PTE Personal (id_entidad={ent['pte_id_entidad']}, RUC {ent['ruc'] or 'no verificado'})",
        "",
        "| Periodo | Estado | Publicados | Únicos | Errores | Advertencias | Suma únicos (S/) | Mediana (S/) | Nota |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    # Periodos con contenido idéntico a otro periodo (posible copia del mismo listado).
    vistos: dict[str, str] = {}
    for ext, rep in resultados:
        if rep is None:
            lineas.append(f"| {ext.periodo} | {ext.estado} | – | – | – | – | – | – | |")
            continue
        e = rep.estadisticas
        nota = ""
        if (firma := e.get("firma_contenido")) in vistos:
            nota = f"contenido idéntico a {vistos[firma]}"
        else:
            vistos[firma] = ext.periodo
        if e["registros_unicos"] != e["registros_publicados"]:
            nota = "; ".join(filter(None, [nota, "carga duplicada"]))
        lineas.append(
            f"| {ext.periodo} | {ext.estado} | {e['registros_publicados']} | {e['registros_unicos']} | "
            f"{rep.errores} | {rep.advertencias} | {e['suma_total']} | {e['mediana']} | {nota} |"
        )
    lineas += [
        "",
        "- Los importes son los publicados para cada mes; no se anualizan ni se suman entre periodos.",
        "- «Únicos» excluye registros idénticos cargados más de una vez en el mismo periodo (se conservan en RAW).",
        "- «Contenido idéntico» señala periodos cuyo listado coincide exactamente con otro; puede ser real o una",
        "  re-publicación del mismo listado. No se corrige: se informa.",
    ]
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--entidad", help="slug en config/entidades.toml")
    grupo.add_argument("--ubigeo", help="ubigeo INEI (usa database/seeds/pte_entidades_XX.csv)")
    ap.add_argument("--desde", required=True, help="YYYY-MM")
    ap.add_argument("--hasta", required=True, help="YYYY-MM")
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    ap.add_argument("--intervalo", type=float, default=3.0, help="segundos mínimos entre peticiones")
    args = ap.parse_args(argv)

    setup_logging()
    ent = cargar_entidad(args.entidad, args.config) if args.entidad else cargar_por_ubigeo(args.ubigeo)
    client = PoliteClient(min_interval_s=args.intervalo)
    store = RawStore(args.data_dir / "raw")
    resultados = [
        procesar_periodo(client, store, args.data_dir, ent, a, m) for a, m in periodos(args.desde, args.hasta)
    ]
    reporte = args.data_dir / "reports" / f"{pte.FUENTE}_{ent['slug']}_{args.desde}_{args.hasta}.md"
    reporte.parent.mkdir(parents=True, exist_ok=True)
    reporte.write_text(resumen_markdown(ent, resultados), encoding="utf-8")
    log.info("reporte escrito", extra={"ctx": {"ruta": str(reporte)}})
    return 1 if any(ext.estado == "error" for ext, _ in resultados) else 0


if __name__ == "__main__":
    raise SystemExit(main())
