"""Fixture XLSX generado en memoria con datos SINTÉTICOS que imitan la estructura del directorio del INEI."""

import io

import openpyxl
import pytest

from munilens_scrapers.sources import inei_directorio as inei


def _xlsx(filas: list[tuple], cabecera: tuple = inei.CABECERA) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(("DIRECTORIO NACIONAL DE MUNICIPALIDADES PROVINCIALES Y DISTRITALES 2026",))
    ws.append(())
    ws.append(("Actualizado al 14/10/2026",))
    ws.append(cabecera)
    for f in filas:
        ws.append(f)
    ws.append(("1/ Distrito creado en 2025 (nota sintética).",))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


FILAS = [
    (
        "990101",
        "Sintético",
        "Provincia A",
        "Provincia A",
        "Alcalde Provincial",
        "ALCALDE UNO",
        "Hombre",
        "Jr. X",
        "000",
        900000000,
        "uno@ejemplo.org",
    ),
    (
        "990102",
        "Sintético",
        "Provincia A",
        "Distrito  B 1/",
        "Alcalde Distrital",
        "ALCALDE DOS (a)",
        "Mujer",
        "S/N",
        "000",
        None,
        None,
    ),
    (
        "990201",
        "Sintético",
        "Provincia C",
        "Provincia C ",
        "Alcalde Provincial",
        "ALCALDE TRES",
        "Hombre",
        None,
        None,
        None,
        None,
    ),
]


def test_lee_directorio_y_descarta_contactos():
    d = inei.leer_xlsx(_xlsx(FILAS))
    assert d.actualizado_al.isoformat() == "2026-10-14"
    assert [m.ubigeo for m in d.municipalidades] == ["990101", "990102", "990201"]
    b = d.municipalidades[1]
    assert (b.distrito, b.nota, b.tipo) == ("Distrito B", "1", "distrital")
    assert b.nombre == "Municipalidad Distrital de Distrito B"
    assert d.municipalidades[2].nombre == "Municipalidad Provincial de Provincia C"
    assert d.notas == ["1/ Distrito creado en 2025 (nota sintética)."]
    assert not any(hasattr(b, campo) for campo in ("telefono", "correo", "direccion", "sexo"))
    assert inei.validar(d.municipalidades) == []


def test_cabecera_distinta_falla():
    with pytest.raises(inei.FormatoInesperadoError):
        inei.leer_xlsx(_xlsx(FILAS, cabecera=("Ubigeo", "Depto")))


def test_validar_detecta_inconsistencias():
    malas = [
        *FILAS,
        ("990202", "Otro nombre", "Provincia C", "D", "Alcalde Provincial", "X", None, None, None, None, None),
        ("990301", "Sintético", "Provincia E", "E", "Alcalde Distrital", "X", None, None, None, None, None),
    ]
    errores = inei.validar(inei.leer_xlsx(_xlsx(malas)).municipalidades)
    texto = "\n".join(errores)
    assert "departamento inconsistente" in texto
    assert "990202: tipo 'provincial' no corresponde" in texto
    assert "990301: tipo 'distrital' no corresponde" in texto
    assert "provincia 9902: 2 municipalidades provinciales" in texto
    assert "provincia 9903: 0 municipalidades provinciales" in texto


def test_unifica_variantes_de_mayusculas_y_las_registra():
    filas = [
        *FILAS,
        ("990103", "SintÉtico", "Provincia A", "F", "Alcalde Distrital", "X", None, None, None, None, None),
    ]
    d = inei.leer_xlsx(_xlsx(filas))
    assert {m.departamento for m in d.municipalidades} == {"Sintético"}
    assert d.correcciones == ["990103: departamento 'SintÉtico' → 'Sintético'"]
    assert inei.validar(d.municipalidades) == []
