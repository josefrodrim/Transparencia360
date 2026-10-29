"""CLI: descubre el `id_entidad` del PTE de cada municipalidad de un departamento y sondea si publica personal.

Ejemplo:
    munilens-pte-descubrir --departamento 09 --bloque 11890-11995 --sondeo 2026-08,2025-12

`--bloque`: rango de ids del PTE donde están las municipalidades del departamento (se determina empíricamente; ver
docs/fuentes-huancavelica.md). Se leen las fichas de ese rango y se cruzan por nombre; el buscador del PTE se usa
como respaldo para las que no aparecen en el bloque.
"""

import argparse
import csv
import logging
from collections import Counter
from pathlib import Path

import requests

from munilens_scrapers.cli_inei import SEED_DEFAULT
from munilens_scrapers.client import PoliteClient
from munilens_scrapers.logging_setup import setup_logging
from munilens_scrapers.sources import pte_entidades as pe
from munilens_scrapers.sources import pte_personal as pte
from munilens_scrapers.sources.inei_directorio import Municipalidad
from munilens_scrapers.storage import RawStore

log = logging.getLogger("munilens.pte_descubrir")

COLUMNAS = ["ubigeo", "tipo", "provincia", "distrito", "pte_id_entidad", "nombre_pte", "confianza", "motivo"]


def cargar_seed(path: Path) -> list[Municipalidad]:
    with path.open(encoding="utf-8", newline="") as fh:
        return [
            Municipalidad(
                r["ubigeo"], r["departamento"], r["provincia"], r["distrito"], r["tipo"], "", r["nota_inei"] or None
            )
            for r in csv.DictReader(fh)
        ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--departamento", required=True, help="código ubigeo de 2 dígitos, p. ej. 09")
    ap.add_argument("--bloque", default="", help="rango de ids PTE 'inicio-fin' a leer por ficha")
    ap.add_argument("--sondeo", default="2026-08,2025-12", help="periodos AAAA-MM a sondear (coma); '' = no sondear")
    ap.add_argument("--seed", type=Path, default=SEED_DEFAULT)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    args = ap.parse_args(argv)

    setup_logging()
    todas = cargar_seed(args.seed)
    homonimos = Counter((m.tipo, pe.norm(m.provincia if m.tipo == "provincial" else m.distrito)) for m in todas)
    munis = [m for m in todas if m.ubigeo.startswith(args.departamento)]
    client = PoliteClient()
    cache: dict[str, list[pe.Candidato]] = {}

    def buscar(termino: str) -> list[pe.Candidato]:
        clave = pe.norm(termino)
        if clave not in cache:
            cache[clave] = pe.parse_resultados(client.post(pe.BUSCADOR, {"var_nombre_entidad": termino}).text)
        return cache[clave]

    bloque: dict[int, str] = {}
    if args.bloque:
        ini, fin = map(int, args.bloque.split("-"))
        for id_ in range(ini, fin + 1):
            try:
                if nombre := pe.parse_ficha(client.get(pe.FICHA.format(id=id_)).text):
                    bloque[id_] = nombre
            except requests.RequestException as exc:
                log.error("ficha", extra={"ctx": {"id": id_, "error": repr(exc)}})
        log.info("bloque leído", extra={"ctx": {"rango": args.bloque, "fichas": len(bloque)}})

    provincias = {m.provincia for m in munis}
    resultados: list[pe.Emparejamiento] = []
    for m in munis:
        if bloque and (e := pe.emparejar_bloque(m, bloque, provincias)).id_entidad is not None:
            resultados.append(e)
            log.info("emparejamiento", extra={"ctx": {"ubigeo": m.ubigeo, "id": e.id_entidad, "motivo": e.motivo}})
            continue
        n_hom = homonimos[(m.tipo, pe.norm(m.provincia if m.tipo == "provincial" else m.distrito))]
        try:
            e = None
            for termino in pe.terminos_busqueda(m):
                e = pe.emparejar(m, buscar(termino), n_hom)
                if e.id_entidad is not None:
                    break
        except requests.RequestException as exc:
            e = pe.Emparejamiento(m.ubigeo, None, None, "pendiente", f"error de búsqueda: {exc!r}")
        resultados.append(e)
        log.info(
            "emparejamiento",
            extra={"ctx": {"ubigeo": m.ubigeo, "id": e.id_entidad, "confianza": e.confianza, "motivo": e.motivo}},
        )

    # Un mismo id asignado a dos ubigeos es un error de cruce: ambos pasan a pendiente.
    repetidos = {i for i, n in Counter(e.id_entidad for e in resultados if e.id_entidad).items() if n > 1}
    resultados = [
        pe.Emparejamiento(
            e.ubigeo, e.id_entidad, e.nombre_pte, "pendiente", "id asignado a varios ubigeos", e.candidatos
        )
        if e.id_entidad in repetidos
        else e
        for e in resultados
    ]

    salida = args.seed.parent / f"pte_entidades_{args.departamento}.csv"
    por_ubigeo = {m.ubigeo: m for m in munis}
    with salida.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNAS)
        for e in resultados:
            m = por_ubigeo[e.ubigeo]
            w.writerow(
                [
                    e.ubigeo,
                    m.tipo,
                    m.provincia,
                    m.distrito,
                    e.id_entidad or "",
                    e.nombre_pte or "",
                    e.confianza,
                    e.motivo,
                ]
            )

    # Sondeo de disponibilidad (solo emparejamientos de confianza alta).
    periodos = [tuple(map(int, p.split("-"))) for p in args.sondeo.split(",") if p]
    store = RawStore(args.data_dir / "raw")
    filas_reporte = []
    for e in resultados:
        m = por_ubigeo[e.ubigeo]
        celdas = []
        if e.confianza == "alta":
            for anio, mes in periodos:
                url = pte.url_descarga(e.id_entidad, anio, mes)
                try:
                    content = client.get(url).content
                    ext = store.guardar(
                        pte.FUENTE,
                        f"pte-{e.id_entidad}",
                        f"{anio:04d}-{mes:02d}",
                        url,
                        content,
                        huella=pte.huella_csv(content) if content.strip() else None,
                    )
                    celdas.append("0" if ext.estado == "sin_datos" else str(len(pte.leer_csv(content))))
                except (requests.RequestException, pte.FormatoInesperadoError) as exc:
                    celdas.append(f"error: {type(exc).__name__}")
        else:
            celdas = ["–"] * len(periodos)
        filas_reporte.append((m, e, celdas))

    if not periodos:
        log.info("fin (sin sondeo)", extra={"ctx": {"seed": str(salida), **Counter(e.confianza for e in resultados)}})
        return 0
    reporte = args.data_dir / "reports" / f"pte_disponibilidad_{args.departamento}.md"
    reporte.parent.mkdir(parents=True, exist_ok=True)
    cab = " | ".join(f"Registros {a:04d}-{m:02d}" for a, m in periodos)
    lineas = [
        f"# Disponibilidad PTE Personal — departamento {args.departamento}",
        "",
        f"| Ubigeo | Municipalidad | id PTE | Confianza | Motivo | {cab} |",
        "|" + "---|" * (5 + len(periodos)),
    ]
    for m, e, celdas in filas_reporte:
        lineas.append(
            f"| {m.ubigeo} | {m.nombre} | {e.id_entidad or ''} | {e.confianza} | {e.motivo} | "
            + " | ".join(celdas)
            + " |"
        )
    c = Counter(e.confianza for e in resultados)
    con_datos = sum(
        1
        for _, e, cs in filas_reporte
        if e.confianza == "alta" and any(x not in ("0", "–") and not x.startswith("error") for x in cs)
    )
    lineas += [
        "",
        f"- Municipalidades: {len(resultados)} · confianza alta: {c['alta']} · pendientes: {c['pendiente']}",
        f"- Con al menos un periodo sondeado con datos: {con_datos}",
    ]
    reporte.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    log.info("fin", extra={"ctx": {"seed": str(salida), "reporte": str(reporte), **c, "con_datos": con_datos}})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
