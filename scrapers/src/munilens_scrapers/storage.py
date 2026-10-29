"""Almacenamiento RAW inmutable con hash SHA-256, manifiesto de extracciones y detección de cambios.

Estructura:
    <base>/<fuente>/<entidad>/<periodo>/<sha256[:16]>.<ext>
    <base>/<fuente>/<entidad>/manifest.jsonl   (una línea por intento de extracción)
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

Estado = Literal["nuevo", "cambiado", "sin_cambios", "sin_datos", "error"]


@dataclass(frozen=True)
class Extraccion:
    fuente: str
    entidad: str
    periodo: str
    url: str
    extraido_en: str
    estado: Estado
    sha256: str | None = None
    huella: str | None = None  # hash canónico del contenido (independiente del orden de filas)
    bytes: int = 0
    ruta: str | None = None
    error: str | None = None


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class RawStore:
    def __init__(self, base: Path) -> None:
        self.base = Path(base)

    def _dir(self, fuente: str, entidad: str) -> Path:
        return self.base / fuente / entidad

    def manifest_path(self, fuente: str, entidad: str) -> Path:
        return self._dir(fuente, entidad) / "manifest.jsonl"

    def historial(self, fuente: str, entidad: str) -> list[Extraccion]:
        path = self.manifest_path(fuente, entidad)
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as fh:
            return [Extraccion(**json.loads(line)) for line in fh if line.strip()]

    def ultima_version(self, fuente: str, entidad: str, periodo: str) -> Extraccion | None:
        for ext in reversed(self.historial(fuente, entidad)):
            if ext.periodo == periodo and ext.sha256:
                return ext
        return None

    def _registrar(self, ext: Extraccion) -> Extraccion:
        path = self.manifest_path(ext.fuente, ext.entidad)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(ext), ensure_ascii=False) + "\n")
        return ext

    def guardar(
        self,
        fuente: str,
        entidad: str,
        periodo: str,
        url: str,
        content: bytes,
        ext: str = "csv",
        huella: str | None = None,
    ) -> Extraccion:
        """Guarda el documento original. `huella` permite comparar versiones ignorando diferencias
        irrelevantes (p. ej. el PTE devuelve las filas en orden variable); por defecto, el SHA-256."""
        ahora = datetime.now(UTC).isoformat(timespec="seconds")
        if not content.strip():
            return self._registrar(Extraccion(fuente, entidad, periodo, url, ahora, "sin_datos"))
        digest = sha256(content)
        huella = huella or digest
        previo = self.ultima_version(fuente, entidad, periodo)
        if previo is not None and (previo.huella or previo.sha256) == huella:
            # Mismo contenido: no se duplica el archivo, se referencia la versión ya guardada.
            return self._registrar(
                Extraccion(
                    fuente,
                    entidad,
                    periodo,
                    url,
                    ahora,
                    "sin_cambios",
                    previo.sha256,
                    huella,
                    previo.bytes,
                    previo.ruta,
                )
            )
        destino = self._dir(fuente, entidad) / periodo / f"{digest[:16]}.{ext}"
        if not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(content)
        estado: Estado = "nuevo" if previo is None else "cambiado"
        return self._registrar(
            Extraccion(
                fuente,
                entidad,
                periodo,
                url,
                ahora,
                estado,
                digest,
                huella,
                len(content),
                str(destino.relative_to(self.base)),
            )
        )

    def registrar_error(self, fuente: str, entidad: str, periodo: str, url: str, error: str) -> Extraccion:
        ahora = datetime.now(UTC).isoformat(timespec="seconds")
        return self._registrar(Extraccion(fuente, entidad, periodo, url, ahora, "error", error=error))
