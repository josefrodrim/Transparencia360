"""CLI: filtra en streaming el devengado mensual del MEF para las municipalidades de un departamento y agrega.

Ejemplo:
    munilens-mef --departamento 09 --anios 2024,2025,2026
"""

import argparse
import codecs
import csv
import hashlib
import json
import logging
import time
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import requests

from munilens_scrapers.client import PoliteClient
from munilens_scrapers.logging_setup import setup_logging
from munilens_scrapers.sources import mef_gasto as mef

log = logging.getLogger("munilens.mef")


def bytes_reanudables(client: PoliteClient, url: str, info: dict, intentos: int = 8) -> Iterator[bytes]:
    """Bytes del archivo en streaming; si la conexión se corta, reanuda con `Range: bytes=<offset>-`."""
    offset, fallos = 0, 0
    while True:
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        try:
            client._throttle()
            with client.session.get(url, stream=True, timeout=client.timeout_s, headers=headers) as resp:
                resp.raise_for_status()
                if offset and resp.status_code != 206:
                    raise RuntimeError("el servidor no respetó Range; no se puede reanudar sin duplicar datos")
                if not offset:
                    info.update(
                        last_modified=resp.headers.get("Last-Modified"),
                        content_length=resp.headers.get("Content-Length"),
                    )
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    offset += len(chunk)
                    yield chunk
            return
        except (requests.RequestException, OSError, ValueError) as exc:
            fallos += 1
            info["reanudaciones"] = fallos
            log.warning(
                "conexión cortada; reanudando", extra={"ctx": {"offset": offset, "intento": fallos, "error": repr(exc)}}
            )
            if fallos > intentos:
                raise
            time.sleep(min(60, 5 * fallos))


def lineas_de(chunks: Iterable[bytes]) -> Iterator[str]:
    dec = codecs.getincrementaldecoder("utf-8-sig")()
    resto = ""
    for chunk in chunks:
        resto += dec.decode(chunk)
        *completas, resto = resto.split("\n")
        for linea in completas:
            yield linea + "\n"
    resto += dec.decode(b"", final=True)
    if resto:
        yield resto


def descargar_filtrado(client: PoliteClient, url: str, departamento: str, destino: Path) -> dict:
    """Lee el CSV oficial en streaming y guarda solo el subconjunto; no almacena el archivo completo."""
    if not client._robots_for(url).can_fetch(client.user_agent, url):
        raise SystemExit(f"robots.txt no permite {url}")
    info: dict = {"reanudaciones": 0}
    leidos = 0

    def contar(lineas: Iterable[str]) -> Iterator[str]:
        nonlocal leidos
        for linea in lineas:
            leidos += 1
            yield linea

    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".part")
    n = 0
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for fila in mef.filtrar(contar(lineas_de(bytes_reanudables(client, url, info))), departamento):
            w.writerow(fila)
            n += 1
            if n % 20000 == 0:
                log.info("progreso", extra={"ctx": {"url": url, "lineas_leidas": leidos, "filas_filtradas": n - 1}})
    tmp.replace(destino)
    return {
        "url": url,
        **info,
        "extraido_en": datetime.now(UTC).isoformat(timespec="seconds"),
        "filtro": {"NIVEL_GOBIERNO": "M", "DEPARTAMENTO_EJECUTORA": departamento},
        "lineas_leidas": leidos,
        "filas_filtradas": n - 1,
        "sha256_subconjunto": hashlib.sha256(destino.read_bytes()).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--departamento", required=True)
    ap.add_argument("--anios", required=True, help="p. ej. 2024,2025,2026")
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--reusar", action="store_true", help="no descargar si el subconjunto RAW ya existe")
    args = ap.parse_args(argv)

    setup_logging()
    client = PoliteClient(timeout_s=600)
    agregados = []
    for anio in map(int, args.anios.split(",")):
        raw = args.data_dir / "raw" / mef.FUENTE / args.departamento / f"{anio}.csv"
        if not (args.reusar and raw.exists()):
            meta = descargar_filtrado(client, mef.url_anual(anio), args.departamento, raw)
            raw.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            log.info("subconjunto guardado", extra={"ctx": meta})
        with raw.open(encoding="utf-8", newline="") as fh:
            agregados += mef.agregar(csv.DictReader(fh))

    salida = args.data_dir / "processed" / mef.FUENTE / f"{args.departamento}.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["ubigeo", "sec_ejec", "pliego", "ejecutora", "anio", "mes", "indicador", "devengado"]
        )
        w.writeheader()
        w.writerows(agregados)
    log.info("agregado escrito", extra={"ctx": {"ruta": str(salida), "filas": len(agregados)}})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
