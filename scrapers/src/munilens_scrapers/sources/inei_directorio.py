"""INEI — Directorio Nacional de Municipalidades Provinciales y Distritales (RENAMU).

Verificado el 2026-10-29 (ver docs/fuentes-huancavelica.md):
- Publicado en https://www.gob.pe/institucion/inei/informes-publicaciones/3364652-... como XLSX; la URL del archivo
  cambia con cada edición, así que se pasa por parámetro.
- Una hoja: título, "Actualizado al dd/mm/aaaa", cabecera de 11 columnas, una fila por municipalidad y notas al pie.
- Incluye teléfonos, correos (a veces personales), dirección y sexo del alcalde: **no se extraen** (minimización).
"""

import io
import re
import warnings
from collections import Counter
from dataclasses import dataclass, field, replace
from datetime import date, datetime

import openpyxl

FUENTE = "inei_directorio"
PAGINA = (
    "https://www.gob.pe/institucion/inei/informes-publicaciones/3364652-nation-registry-of-municipalities-renamu-2026"
)

CABECERA = (
    "Ubigeo",
    "Departamento",
    "Provincia",
    "Distrito",
    "Cargo",
    "Nombres y Apellidos del Alcalde",
    "Sexo",
    "Dirección",
    "Código de ciudad",
    "Teléfonos",
    "Correo Electrónico",
)
TIPOS = {"Alcalde Provincial": "provincial", "Alcalde Distrital": "distrital"}
_NOTA = re.compile(r"\s+(\d+)/\s*$")
_ACTUALIZADO = re.compile(r"Actualizado al (\d{2}/\d{2}/\d{4})")


class FormatoInesperadoError(ValueError):
    pass


@dataclass(frozen=True)
class Municipalidad:
    ubigeo: str
    departamento: str
    provincia: str
    distrito: str
    tipo: str  # provincial | distrital
    alcalde: str  # nombre publicado (fuente: JNE vía INEI); "(a)" = administrador temporal
    nota: str | None  # número de nota al pie del INEI (p. ej. distrito de creación reciente)

    @property
    def ubigeo_departamento(self) -> str:
        return self.ubigeo[:2]

    @property
    def ubigeo_provincia(self) -> str:
        return self.ubigeo[:4]

    @property
    def nombre(self) -> str:
        if self.tipo == "provincial":
            return f"Municipalidad Provincial de {self.provincia}"
        return f"Municipalidad Distrital de {self.distrito}"


@dataclass(frozen=True)
class Directorio:
    actualizado_al: date
    municipalidades: list[Municipalidad]
    notas: list[str]
    correcciones: list[str] = field(default_factory=list)


def _texto(v: object) -> str:
    return " ".join(str(v).split()) if v is not None else ""


def leer_xlsx(content: bytes) -> Directorio:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # cabecera/pie de página no parseable: irrelevante
        ws = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True).active
        filas = list(ws.iter_rows(values_only=True))

    actualizado = next((m for f in filas[:10] if (m := _ACTUALIZADO.search(_texto(f[0])))), None)
    if actualizado is None:
        raise FormatoInesperadoError("no se encontró 'Actualizado al dd/mm/aaaa'")
    try:
        i_cab = next(i for i, f in enumerate(filas) if tuple(_texto(c) for c in f[:11]) == CABECERA)
    except StopIteration:
        raise FormatoInesperadoError("cabecera no encontrada o distinta a la esperada") from None

    munis: list[Municipalidad] = []
    notas: list[str] = []
    for f in filas[i_cab + 1 :]:
        ubigeo = _texto(f[0])
        if re.fullmatch(r"\d{6}", ubigeo):
            cargo = _texto(f[4])
            if cargo not in TIPOS:
                raise FormatoInesperadoError(f"cargo desconocido en {ubigeo}: {cargo!r}")
            distrito = _texto(f[3])
            nota = None
            if m := _NOTA.search(distrito):
                nota, distrito = m.group(1), distrito[: m.start()]
            munis.append(Municipalidad(ubigeo, _texto(f[1]), _texto(f[2]), distrito, TIPOS[cargo], _texto(f[5]), nota))
        elif ubigeo:
            notas.append(ubigeo)
    munis, correcciones = _unificar_nombres(munis)
    return Directorio(datetime.strptime(actualizado.group(1), "%d/%m/%Y").date(), munis, notas, correcciones)


def _unificar_nombres(munis: list[Municipalidad]) -> tuple[list[Municipalidad], list[str]]:
    """Unifica variantes que difieren solo en mayúsculas/minúsculas (p. ej. 'ApurÍmac' vs 'Apurímac') usando la
    grafía más frecuente para el mismo código. Diferencias de otro tipo se dejan para que `validar` las reporte."""
    correcciones: list[str] = []
    for campo, codigo in (("departamento", lambda m: m.ubigeo[:2]), ("provincia", lambda m: m.ubigeo[:4])):
        conteo: dict[str, Counter[str]] = {}
        for m in munis:
            conteo.setdefault(codigo(m), Counter())[getattr(m, campo)] += 1
        canon = {c: v.most_common(1)[0][0] for c, v in conteo.items()}
        nuevas = []
        for m in munis:
            actual, esperado = getattr(m, campo), canon[codigo(m)]
            if actual != esperado and actual.casefold() == esperado.casefold():
                correcciones.append(f"{m.ubigeo}: {campo} '{actual}' → '{esperado}'")
                m = replace(m, **{campo: esperado})
            nuevas.append(m)
        munis = nuevas
    return munis, correcciones


def validar(munis: list[Municipalidad]) -> list[str]:
    """Devuelve la lista de inconsistencias estructurales (vacía si todo está bien)."""
    errores: list[str] = []
    vistos: set[str] = set()
    nombres_dep: dict[str, str] = {}
    nombres_prov: dict[str, str] = {}
    provinciales: dict[str, int] = {}
    for m in munis:
        if m.ubigeo in vistos:
            errores.append(f"ubigeo duplicado {m.ubigeo}")
        vistos.add(m.ubigeo)
        if nombres_dep.setdefault(m.ubigeo_departamento, m.departamento) != m.departamento:
            errores.append(f"{m.ubigeo}: departamento inconsistente '{m.departamento}'")
        if nombres_prov.setdefault(m.ubigeo_provincia, m.provincia) != m.provincia:
            errores.append(f"{m.ubigeo}: provincia inconsistente '{m.provincia}'")
        if (m.tipo == "provincial") != m.ubigeo.endswith("01"):
            errores.append(f"{m.ubigeo}: tipo '{m.tipo}' no corresponde al ubigeo")
        if m.tipo == "provincial":
            provinciales[m.ubigeo_provincia] = provinciales.get(m.ubigeo_provincia, 0) + 1
        if not m.distrito:
            errores.append(f"{m.ubigeo}: distrito vacío")
    for prov in nombres_prov:
        if provinciales.get(prov) != 1:
            errores.append(f"provincia {prov}: {provinciales.get(prov, 0)} municipalidades provinciales")
    return errores
