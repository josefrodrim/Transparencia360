"""Portal de Transparencia Estándar (PTE) — rubro Personal.

Verificado el 2026-10-28 (ver docs/fuentes-huancavelica.md):
- La consulta por entidad/año/mes ofrece descargas XLS, CSV y XML vía
  /personal/pte_transparencia_personal_genera.aspx (ch_tipo_descarga=2 → CSV, UTF-8).
- Un periodo sin información devuelve un cuerpo vacío (0 bytes).
- El CSV no incluye DNI.
- robots.txt solo prohíbe /enlaces/pte_transparencia_verificar.aspx.
"""

import csv
import hashlib
import io
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

FUENTE = "pte_personal"
BASE_URL = "https://www.transparencia.gob.pe/personal/pte_transparencia_personal_genera.aspx"

# Códigos del selector "Régimen Laboral" de la página de consulta del PTE.
REGIMENES: dict[str, str] = {
    "1": "CAS",
    "2": "Régimen 276",
    "3": "Régimen 728/OTROS",
    "4": "PAC",
    "5": "FAG",
    "6": "PNUD",
    "7": "Altos Funcionarios",
    "8": "Pensionistas",
    "9": "Ley Servir",
}

COLUMNAS = [
    "PK_ID_PERSONAL",
    "VC_PERSONAL_RUC_ENTIDAD",
    "IN_PERSONAL_ANNO",
    "IN_PERSONAL_MES",
    "VC_PERSONAL_REGIMEN_LABORAL",
    "VC_PERSONAL_PATERNO",
    "VC_PERSONAL_MATERNO",
    "VC_PERSONAL_NOMBRES",
    "VC_PERSONAL_CARGO",
    "VC_PERSONAL_DEPENDENCIA",
    "MO_PERSONAL_REMUNERACIONES",
    "MO_PERSONAL_HONORARIOS",
    "MO_PERSONAL_INCENTIVO",
    "MO_PERSONAL_GRATIFICACION",
    "MO_PERSONAL_OTROS_BENEFICIOS",
    "MO_PERSONAL_TOTAL",
    "VC_PERSONAL_OBSERVACIONES",
    "FEC_REG",
]

MONTOS = {
    "remuneraciones": "MO_PERSONAL_REMUNERACIONES",
    "honorarios": "MO_PERSONAL_HONORARIOS",
    "incentivo": "MO_PERSONAL_INCENTIVO",
    "gratificacion": "MO_PERSONAL_GRATIFICACION",
    "otros_beneficios": "MO_PERSONAL_OTROS_BENEFICIOS",
}


class FormatoInesperadoError(ValueError):
    """El documento no tiene la estructura conocida; no se debe procesar a ciegas."""


def url_descarga(id_entidad: int, anio: int, mes: int) -> str:
    params = {
        "id_entidad": id_entidad,
        "in_anno_consulta": anio,
        "ch_mes_consulta": f"{mes:02d}",
        "ch_tipo_regimen": 0,
        "vc_dni_funcionario": "",
        "vc_nombre_funcionario": "",
        "ch_tipo_descarga": 2,
    }
    return f"{BASE_URL}?{urlencode(params)}"


def limpiar_texto(valor: str) -> str:
    return " ".join(valor.split())


def clave_busqueda(valor: str) -> str:
    """Minúsculas y sin tildes, para búsqueda tolerante. No altera el nombre publicado."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", valor) if unicodedata.category(c) != "Mn")
    return limpiar_texto(sin_tildes).lower()


def parse_monto(valor: str) -> Decimal:
    try:
        return Decimal(valor.strip())
    except InvalidOperation as exc:
        raise ValueError(f"monto no numérico: {valor!r}") from exc


def parse_fecha_registro(valor: str) -> datetime:
    # Formato observado: "10/9/2026 9:47:31 AM" (mes/día/año, 12 h).
    return datetime.strptime(valor.strip(), "%m/%d/%Y %I:%M:%S %p")


@dataclass(frozen=True)
class RegistroPersonal:
    pte_id_personal: str
    ruc_entidad: str
    anio: int
    mes: int
    regimen_codigo: str
    regimen: str | None
    apellido_paterno: str
    apellido_materno: str
    nombres: str
    cargo: str
    dependencia: str
    remuneraciones: Decimal
    honorarios: Decimal
    incentivo: Decimal
    gratificacion: Decimal
    otros_beneficios: Decimal
    total: Decimal
    observaciones: str
    fecha_registro_pte: datetime

    @property
    def nombre_publicado(self) -> str:
        apellidos = " ".join(p for p in (self.apellido_paterno, self.apellido_materno) if p)
        return f"{apellidos}, {self.nombres}" if self.nombres else apellidos

    @property
    def nombre_busqueda(self) -> str:
        return clave_busqueda(f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}")

    @property
    def huella_contenido(self) -> tuple:
        """Campos publicados, sin el id interno ni la fecha de carga: detecta re-cargas idénticas."""
        return (
            self.regimen_codigo,
            self.apellido_paterno,
            self.apellido_materno,
            self.nombres,
            self.cargo,
            self.dependencia,
            self.remuneraciones,
            self.honorarios,
            self.incentivo,
            self.gratificacion,
            self.otros_beneficios,
            self.total,
            self.observaciones,
        )

    @property
    def suma_componentes(self) -> Decimal:
        return self.remuneraciones + self.honorarios + self.incentivo + self.gratificacion + self.otros_beneficios


def leer_csv(content: bytes) -> list[dict[str, str]]:
    texto = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(texto, newline=""))
    if reader.fieldnames != COLUMNAS:
        raise FormatoInesperadoError(f"columnas inesperadas: {reader.fieldnames}")
    return list(reader)


def huella_csv(content: bytes) -> str:
    """Hash del conjunto de filas, independiente del orden (el PTE no garantiza un orden estable)."""
    filas = sorted(tuple(f.values()) for f in leer_csv(content))
    return hashlib.sha256(repr(filas).encode()).hexdigest()


def normalizar(fila: dict[str, str]) -> RegistroPersonal:
    codigo = fila["VC_PERSONAL_REGIMEN_LABORAL"].strip()
    montos = {campo: parse_monto(fila[col]) for campo, col in MONTOS.items()}
    return RegistroPersonal(
        pte_id_personal=fila["PK_ID_PERSONAL"].strip(),
        ruc_entidad=fila["VC_PERSONAL_RUC_ENTIDAD"].strip(),
        anio=int(fila["IN_PERSONAL_ANNO"]),
        mes=int(fila["IN_PERSONAL_MES"]),
        regimen_codigo=codigo,
        regimen=REGIMENES.get(codigo),
        apellido_paterno=limpiar_texto(fila["VC_PERSONAL_PATERNO"]),
        apellido_materno=limpiar_texto(fila["VC_PERSONAL_MATERNO"]),
        nombres=limpiar_texto(fila["VC_PERSONAL_NOMBRES"]),
        cargo=limpiar_texto(fila["VC_PERSONAL_CARGO"]),
        dependencia=limpiar_texto(fila["VC_PERSONAL_DEPENDENCIA"]),
        total=parse_monto(fila["MO_PERSONAL_TOTAL"]),
        observaciones=limpiar_texto(fila["VC_PERSONAL_OBSERVACIONES"]),
        fecha_registro_pte=parse_fecha_registro(fila["FEC_REG"]),
        **montos,
    )
