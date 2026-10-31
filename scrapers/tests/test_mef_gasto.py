"""Datos SINTÉTICOS con la estructura del CSV de devengado mensual del MEF."""

import csv
import io
from decimal import Decimal

import pytest

from munilens_scrapers.sources import mef_gasto as mef

CAB = [
    "ANO_EJE",
    "NIVEL_GOBIERNO",
    "PLIEGO",
    "PLIEGO_NOMBRE",
    "SEC_EJEC",
    "EJECUTORA_NOMBRE",
    "DEPARTAMENTO_EJECUTORA",
    "PROVINCIA_EJECUTORA",
    "DISTRITO_EJECUTORA",
    "TIPO_TRANSACCION",
    "GENERICA",
    "SUBGENERICA",
    "SUBGENERICA_DET",
    "ESPECIFICA",
    "ESPECIFICA_DET",
    "MONTO_PIM",
    *mef.COLUMNAS_MES,
]


def _fila(niv, dep, g, sg, sgd, enero, febrero="0", tt="2", dist="01", esp="0", espdet="0"):
    return [
        "2026",
        niv,
        "1",
        "MUNI X",
        "300001",
        "MUNI X",
        dep,
        "01",
        dist,
        tt,
        g,
        sg,
        sgd,
        esp,
        espdet,
        "0",
        enero,
        febrero,
        *["0"] * 10,
    ]


def _csv(filas):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CAB)
    w.writerows(filas)
    return buf.getvalue().splitlines(keepends=True)


def test_filtra_por_nivel_y_departamento():
    filas = [
        _fila("M", "09", "1", "1", "1", "10"),
        _fila("R", "09", "1", "1", "1", "10"),
        _fila("M", "15", "1", "1", "1", "10"),
    ]
    out = list(mef.filtrar(_csv(filas), "09"))
    assert out[0] == CAB and len(out) == 2 and out[1][1:2] == ["M"]


def test_cabecera_incompleta_falla():
    with pytest.raises(mef.FormatoInesperadoError):
        list(mef.filtrar(["A,B\n", "1,2\n"], "09"))


def test_agrega_indicadores_por_mes():
    filas = [
        _fila("M", "09", "1", "1", "1", "100", "50"),  # personal (planilla)
        _fila("M", "09", "1", "1", "1", "75", esp="1", espdet="1"),  # alcalde (elegido)
        _fila("M", "09", "1", "1", "1", "8", esp="1", espdet="8"),  # Ley Servir
        _fila("M", "09", "1", "3", "1", "20"),  # personal (aportes)
        _fila("M", "09", "1", "1", "13", "300"),  # CAS dentro de 2.1 (vigente)
        _fila("M", "09", "1", "1", "10", "5"),  # dietas
        _fila("M", "09", "3", "2", "8", "11"),  # CAS en 2.3.2.8 (años anteriores)
        _fila("M", "09", "3", "2", "9", "999"),  # locación a personas naturales
        _fila("M", "09", "3", "2", "7", "123"),  # servicios profesionales: no se cuenta
        _fila("M", "09", "2", "1", "1", "40"),  # pensiones
        _fila("M", "09", "1", "1", "1", "7", tt="1"),  # no presupuestario
    ]
    rows = list(csv.DictReader(_csv(filas)))
    res = {(r["mes"], r["indicador"]): r["devengado"] for r in mef.agregar(rows)}
    assert res == {
        (1, "personal"): Decimal("508"),
        (1, "ley_servir"): Decimal("8"),
        (1, "alcalde"): Decimal("75"),
        (1, "cas"): Decimal("311"),
        (1, "dietas"): Decimal("5"),
        (1, "locacion_pn"): Decimal("999"),
        (1, "pensiones"): Decimal("40"),
        (2, "personal"): Decimal("50"),
    }
    assert {r["ubigeo"] for r in mef.agregar(rows)} == {"090101"}


def test_lineas_de_chunks_partidos_y_utf8_multibyte():
    from munilens_scrapers.cli_mef import lineas_de

    datos = "\ufeffA,B\nÑAÑA,1\nx,2".encode()
    chunks = [datos[i : i + 3] for i in range(0, len(datos), 3)]  # corta dentro de caracteres multibyte
    assert list(lineas_de(chunks)) == ["A,B\n", "ÑAÑA,1\n", "x,2"]


def test_reanuda_con_range_tras_corte(monkeypatch):
    from unittest.mock import MagicMock

    from munilens_scrapers.cli_mef import bytes_reanudables
    from munilens_scrapers.client import PoliteClient

    def resp(status, chunks, falla=False):
        r = MagicMock(status_code=status, headers={})
        r.__enter__.return_value = r

        def it(chunk_size):
            yield from chunks
            if falla:
                raise ConnectionError("cortado")

        r.iter_content.side_effect = it
        return r

    session = MagicMock(headers={})
    session.get.side_effect = [resp(200, [b"abc"], falla=True), resp(206, [b"def"])]
    client = PoliteClient(min_interval_s=0, session=session)
    monkeypatch.setattr("munilens_scrapers.cli_mef.time.sleep", lambda s: None)
    info: dict = {}
    assert b"".join(bytes_reanudables(client, "https://x/y.csv", info)) == b"abcdef"
    assert session.get.call_args_list[1].kwargs["headers"] == {"Range": "bytes=3-"}
    assert info["reanudaciones"] == 1
