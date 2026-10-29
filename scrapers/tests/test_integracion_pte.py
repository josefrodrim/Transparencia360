"""Pruebas contra el portal real. Opt-in: MUNILENS_RED=1 pytest -m red

Valida que el CSV descargado coincide con lo que el PTE muestra en su tabla HTML (página 1).
"""

import html
import os
import re
from decimal import Decimal

import pytest

from munilens_scrapers.client import PoliteClient
from munilens_scrapers.sources import pte_personal as pte

pytestmark = [
    pytest.mark.red,
    pytest.mark.skipif(os.environ.get("MUNILENS_RED") != "1", reason="requiere MUNILENS_RED=1"),
]

ID_ENTIDAD, RUC, ANIO, MES = 980, "20171725144", 2026, 8
CONSULTA = "https://www.transparencia.gob.pe/personal/pte_transparencia_personal.aspx"


def _filas_html(texto: str) -> list[list[str]]:
    filas = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", texto, re.S | re.I):
        celdas = [
            " ".join(html.unescape(re.sub(r"<[^>]+>", " ", c)).split())
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        ]
        if len(celdas) == 10:
            filas.append(celdas)
    return filas


def _monto_html(v: str) -> Decimal:
    return Decimal(v.replace("S/", "").replace(",", "").strip())


def test_csv_coincide_con_tabla_html():
    client = PoliteClient()
    regs = [pte.normalizar(f) for f in pte.leer_csv(client.get(pte.url_descarga(ID_ENTIDAD, ANIO, MES)).content)]
    assert regs and all(r.ruc_entidad == RUC for r in regs)

    resp = client.session.post(
        CONSULTA,
        data={
            "ch_tipo_busqueda": 1,
            "id_entidad": ID_ENTIDAD,
            "id_tema": 32,
            "in_anno_consulta": ANIO,
            "ch_mes_consulta": f"{MES:02d}",
            "vc_nombre_funcionario": "",
            "vc_dni_funcionario": "",
            "ch_tipo_regimen": 0,
        },
        timeout=120,
    )
    resp.raise_for_status()
    filas = _filas_html(resp.text)
    assert filas, "la tabla HTML no tiene filas de datos"

    por_nombre = {r.nombre_publicado: r for r in regs}
    for regimen, nombre, cargo, dependencia, *montos in filas:
        r = por_nombre[nombre]
        assert r.regimen == regimen
        assert r.cargo == cargo and r.dependencia == dependencia
        assert [_monto_html(m) for m in montos] == [
            r.remuneraciones,
            r.honorarios,
            r.incentivo,
            r.gratificacion,
            r.otros_beneficios,
            r.total,
        ]
