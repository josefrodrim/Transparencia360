"""Descubrimiento de `id_entidad` del PTE para las municipalidades del directorio del INEI.

El PTE no publica el ubigeo de sus entidades, así que el cruce es por nombre (verificado 2026-10-29):
- Ficha: /enlaces/pte_transparencia_enlaces.aspx?id_entidad=N; el nombre está en el primer <h2>.
- Las municipalidades de un departamento ocupan un bloque de ids consecutivo en orden de ubigeo (Huancavelica:
  ~11895–11992); distritos creados después tienen ids fuera del bloque.
- Buscador: POST /buscador/pte_transparencia_listado_entidades.aspx: insensible a tildes, busca por subcadena,
  devuelve como máximo 20 resultados y no encuentra algunas entidades que sí existen: solo sirve de respaldo.
- Nombres con variantes: "... DE ANTA - HUANCAVELICA", "...-CASTROVIRREYNA-HUANCAVELICA", "PROVINCIAL ANGARAES LIRCAY".
- Se prioriza la precisión: ante cualquier ambigüedad el resultado queda `pendiente` para revisión manual.
"""

import html
import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from munilens_scrapers.sources.inei_directorio import Municipalidad

BUSCADOR = "https://www.transparencia.gob.pe/buscador/pte_transparencia_listado_entidades.aspx"
FICHA = "https://www.transparencia.gob.pe/enlaces/pte_transparencia_enlaces.aspx?id_entidad={id}"
_H2 = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)
_ENLACE = re.compile(r"id_entidad=(\d+)[^>]*>(.*?)</a>", re.S)
_PREFIJO = re.compile(r"^MUNICIPALIDAD (PROVINCIAL|DISTRITAL)(?: DEL?)? (.+?)(?:\s*-\s*(.+))?$")

Confianza = Literal["alta", "pendiente"]


@dataclass(frozen=True)
class Candidato:
    id_entidad: int
    nombre: str


@dataclass(frozen=True)
class Emparejamiento:
    ubigeo: str
    id_entidad: int | None
    nombre_pte: str | None
    confianza: Confianza
    motivo: str
    candidatos: tuple[Candidato, ...] = ()


def norm(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", sin_tildes.upper()).split())


def parse_resultados(page: str) -> list[Candidato]:
    vistos: dict[int, Candidato] = {}
    for id_, nombre in _ENLACE.findall(page):
        limpio = " ".join(html.unescape(re.sub(r"<[^>]+>", "", nombre)).split())
        if limpio:
            vistos.setdefault(int(id_), Candidato(int(id_), limpio))
    return list(vistos.values())


def parse_ficha(page: str) -> str | None:
    m = _H2.search(page)
    nombre = " ".join(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split()) if m else ""
    return nombre or None


def terminos_busqueda(m: Municipalidad) -> list[str]:
    base = m.provincia if m.tipo == "provincial" else m.distrito
    palabras = sorted((p for p in norm(base).split() if len(p) >= 4), key=len, reverse=True)
    return [base, *palabras[:1]] if palabras and palabras[0] != norm(base) else [base]


def _descomponer(nombre_pte: str) -> tuple[str, str, str, str] | None:
    """'MUNICIPALIDAD DISTRITAL DE ANTA - HUANCAVELICA' → ('distrital', 'ANTA', 'HUANCAVELICA', 'ANTA HUANCAVELICA').
    El último elemento es el nombre completo sin partir por guiones (para 'HUANCA-HUANCA', 'QUITO-ARMA')."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre_pte) if unicodedata.category(c) != "Mn")
    texto = " ".join(re.sub(r"\(.*?\)", " ", sin_tildes.upper()).split())
    m = _PREFIJO.match(texto)
    if not m:
        return None
    resto = texto[m.end(1) :].removeprefix(" DE ").removeprefix(" DEL ")
    return m.group(1).lower(), norm(m.group(2)), norm(m.group(3) or ""), norm(resto)


def _coincide(m: Municipalidad, nombre_pte: str) -> tuple[bool, bool]:
    """(coincide, tiene_contexto): el nombre del PTE corresponde a la municipalidad y menciona su provincia,
    departamento o capital (desambiguación)."""
    partes = _descomponer(nombre_pte)
    if not partes or partes[0] != m.tipo:
        return False, False
    _, base, sufijo, completo = partes
    objetivo = norm(m.provincia if m.tipo == "provincial" else m.distrito)
    contexto = {norm(m.departamento), norm(m.provincia), norm(m.distrito)} - {objetivo}
    if completo == objetivo:
        return True, False
    if base == objetivo:
        return True, bool(sufijo) and any(t in sufijo for t in contexto)
    # "ANGARAES LIRCAY": el resto del nombre es la capital/provincia/departamento.
    if base.startswith(objetivo + " ") and base[len(objetivo) + 1 :] in contexto:
        return True, True
    return False, False


def emparejar(m: Municipalidad, candidatos: list[Candidato], homonimos_nacionales: int) -> Emparejamiento:
    """`homonimos_nacionales`: cuántas municipalidades del mismo tipo comparten el nombre en el directorio INEI."""
    evaluados = [(c, *_coincide(m, c.nombre)) for c in candidatos]
    coinciden = [(c, ctx) for c, ok, ctx in evaluados if ok]
    con_contexto = [c for c, ctx in coinciden if ctx]

    if len(con_contexto) == 1:
        c = con_contexto[0]
        return Emparejamiento(m.ubigeo, c.id_entidad, c.nombre, "alta", "nombre + sufijo de departamento/provincia")
    if len(coinciden) == 1 and homonimos_nacionales == 1:
        c = coinciden[0][0]
        return Emparejamiento(m.ubigeo, c.id_entidad, c.nombre, "alta", "nombre único a nivel nacional")
    if len(coinciden) == 1:
        c = coinciden[0][0]
        return Emparejamiento(
            m.ubigeo,
            c.id_entidad,
            c.nombre,
            "pendiente",
            f"nombre sin sufijo y {homonimos_nacionales} homónimos en el INEI",
            tuple(candidatos),
        )
    motivo = "sin coincidencias" if not coinciden else f"{len(coinciden)} coincidencias ambiguas"
    return Emparejamiento(
        m.ubigeo, None, None, "pendiente", motivo, tuple(c for c, _ in coinciden) or tuple(candidatos)
    )


def emparejar_bloque(m: Municipalidad, bloque: dict[int, str], provincias: set[str] = frozenset()) -> Emparejamiento:
    """Cruce dentro del bloque de ids del departamento: basta una coincidencia única de nombre y tipo.

    `provincias`: provincias del departamento. Con homónimos dentro del mismo departamento (p. ej. Huachocolpa en
    Huancavelica y en Tayacaja) se descartan los candidatos cuyo sufijo nombra otra provincia."""
    hits = [Candidato(i, n) for i, n in bloque.items() if _coincide(m, n)[0]]
    if len(hits) > 1:
        otras = {norm(p) for p in provincias} - {norm(m.provincia), norm(m.departamento)}
        sufijo = {c.id_entidad: (_descomponer(c.nombre) or ("", "", "", ""))[2] for c in hits}
        hits = [c for c in hits if not any(o in sufijo[c.id_entidad] for o in otras)]
        prov = norm(m.provincia)
        if len(hits) > 1 and prov != norm(m.departamento):
            hits = [c for c in hits if prov in sufijo[c.id_entidad]] or hits
    if len(hits) == 1:
        return Emparejamiento(m.ubigeo, hits[0].id_entidad, hits[0].nombre, "alta", "nombre único en el bloque de ids")
    motivo = "sin coincidencias en el bloque" if not hits else f"{len(hits)} coincidencias en el bloque"
    return Emparejamiento(m.ubigeo, None, None, "pendiente", motivo, tuple(hits))
