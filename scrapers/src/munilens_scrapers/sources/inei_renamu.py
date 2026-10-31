"""INEI — Registro Nacional de Municipalidades (RENAMU), microdatos del formulario F01: personal por régimen.

Verificado el 2026-10-31 (ver docs/fuentes-huancavelica.md):
- Portal de microdatos https://proyectos.inei.gob.pe/microdatos/ → «Registro Nacional de Municipalidades - RENAMU».
  Descarga pública sin registro: /iinei/srienaho/descarga/CSV/{encuesta}-Modulo{modulo}.zip (2026: 1049 / 1963).
- El ZIP trae el diccionario (PDF) y Base_de_Datos_F01_RENAMU{AAAA}.csv: UTF-8 con BOM, separador «;», una fila
  por municipalidad (respuestas de la propia municipalidad al INEI).
- Pregunta 19: personal al 31 de diciembre del año anterior (P19D_*) y al 31 de marzo (P19M_*), por régimen:
  N = D. Leg. 276 nombrado, C = 276 contratado, L = D. Leg. 728, V = CAS; sufijos M/H = mujer/hombre.
  P19_1_* = funcionarios y directivos (incluye cargos de confianza). P19A_* = locación / orden de servicios.
- Solo se extraen conteos agregados: no hay datos personales.
"""

import csv
import io
import zipfile
from dataclasses import dataclass

FUENTE = "inei_renamu"
PORTAL = "https://proyectos.inei.gob.pe/microdatos/"


def url_csv(encuesta: str, modulo: str) -> str:
    return f"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/CSV/{encuesta}-Modulo{modulo}.zip"


REGIMENES = {"276_nombrado": "N", "276_contratado": "C", "728": "L", "cas": "V"}
REQUERIDAS = {
    "Ubigeo",
    "P19",
    "P19D_T",
    "P19M_T",
    "P19_1_T",
    "P19_1_VM",
    "P19_1_VH",
    "P19A_1_T",
    "P19A_2_T",
    *(f"P19D_{r}{s}" for r in REGIMENES.values() for s in "MH"),
}


class FormatoInesperadoError(ValueError):
    pass


@dataclass(frozen=True)
class PersonalMunicipal:
    ubigeo: str
    tiene_personal: bool
    total_dic: int | None
    por_regimen_dic: dict[str, int]  # 276_nombrado, 276_contratado, 728, cas
    funcionarios: int | None
    funcionarios_cas: int | None
    locacion_dic: int | None
    total_mar: int | None
    locacion_mar: int | None


NULOS = {"", "#¡NULO!", "#NULL!"}  # celdas vacías exportadas desde Excel/SPSS


def _int(v: str | None) -> int | None:
    v = (v or "").strip()
    if v in NULOS:
        return None
    try:
        return int(float(v))
    except ValueError as e:
        raise FormatoInesperadoError(f"valor no numérico: {v!r}") from e


def _suma(fila: dict[str, str], *cols: str) -> int | None:
    vals = [_int(fila[c]) for c in cols]
    return None if all(v is None for v in vals) else sum(v or 0 for v in vals)


def leer_zip(content: bytes) -> tuple[str, list[PersonalMunicipal]]:
    """Devuelve (nombre del CSV dentro del ZIP, registros)."""
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(csvs) != 1:
            raise FormatoInesperadoError(f"se esperaba un CSV en el ZIP, hay {csvs}")
        return csvs[0], leer_csv(z.read(csvs[0]).decode("utf-8-sig"))


def leer_csv(texto: str) -> list[PersonalMunicipal]:
    reader = csv.DictReader(io.StringIO(texto), delimiter=";")
    if missing := REQUERIDAS - set(reader.fieldnames or []):
        raise FormatoInesperadoError(f"faltan columnas: {sorted(missing)}")
    out = []
    for f in reader:
        out.append(
            PersonalMunicipal(
                ubigeo=f["Ubigeo"].strip().zfill(6),
                tiene_personal=f["P19"].strip() == "1",
                total_dic=_int(f["P19D_T"]),
                por_regimen_dic={k: _suma(f, f"P19D_{c}M", f"P19D_{c}H") or 0 for k, c in REGIMENES.items()},
                funcionarios=_int(f["P19_1_T"]),
                funcionarios_cas=_suma(f, "P19_1_VM", "P19_1_VH"),
                locacion_dic=_int(f["P19A_1_T"]),
                total_mar=_int(f["P19M_T"]),
                locacion_mar=_int(f["P19A_2_T"]),
            )
        )
    return out


def validar(registros: list[PersonalMunicipal]) -> list[str]:
    """Inconsistencias que impiden usar el dato (no se corrigen: se informan)."""
    errores = []
    vistos = set()
    for r in registros:
        if len(r.ubigeo) != 6 or not r.ubigeo.isdigit():
            errores.append(f"{r.ubigeo}: ubigeo inválido")
        if r.ubigeo in vistos:
            errores.append(f"{r.ubigeo}: ubigeo duplicado")
        vistos.add(r.ubigeo)
        if r.total_dic is not None and r.total_dic != sum(r.por_regimen_dic.values()):
            errores.append(f"{r.ubigeo}: total {r.total_dic} ≠ suma por régimen {sum(r.por_regimen_dic.values())}")
    return errores
