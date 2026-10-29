from datetime import datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest

from munilens_scrapers.sources import pte_personal as pte


def test_url_descarga_usa_csv_y_mes_con_dos_digitos():
    q = parse_qs(urlsplit(pte.url_descarga(980, 2026, 8)).query, keep_blank_values=True)
    assert q["id_entidad"] == ["980"]
    assert q["in_anno_consulta"] == ["2026"]
    assert q["ch_mes_consulta"] == ["08"]
    assert q["ch_tipo_descarga"] == ["2"]
    assert q["ch_tipo_regimen"] == ["0"]


def test_leer_y_normalizar(csv_sintetico):
    regs = [pte.normalizar(f) for f in pte.leer_csv(csv_sintetico)]
    assert len(regs) == 3
    r = regs[0]
    assert r.nombres == "ANA MARÍA"  # espacios colapsados, tilde preservada
    assert r.nombre_publicado == "SINTETICO PRUEBA, ANA MARÍA"
    assert r.nombre_busqueda == "ana maria sintetico prueba"
    assert r.regimen == "CAS"
    assert r.total == Decimal("2164.19")
    assert r.fecha_registro_pte == datetime(2026, 10, 9, 9, 47, 31)
    assert regs[1].suma_componentes == regs[1].total == Decimal("3150.50")
    assert regs[2].regimen == "Altos Funcionarios"
    assert regs[2].fecha_registro_pte.hour == 21


def test_bom_utf8_se_acepta(csv_sintetico):
    assert len(pte.leer_csv(b"\xef\xbb\xbf" + csv_sintetico)) == 3


def test_columnas_inesperadas_fallan():
    with pytest.raises(pte.FormatoInesperadoError):
        pte.leer_csv(b"NOMBRE,SUELDO\nX,1\n")


def test_monto_invalido_falla(csv_sintetico):
    fila = pte.leer_csv(csv_sintetico)[0] | {"MO_PERSONAL_TOTAL": "S/ 1,000"}
    with pytest.raises(ValueError, match="monto"):
        pte.normalizar(fila)


def test_clave_busqueda_tolerante_a_tildes_y_mayusculas():
    assert pte.clave_busqueda("  NÚÑEZ  Peña ") == "nunez pena"


def test_huella_csv_independiente_del_orden(csv_sintetico):
    cab, *filas = csv_sintetico.decode().splitlines(keepends=True)
    invertido = (cab + "".join(reversed(filas))).encode()
    assert invertido != csv_sintetico
    assert pte.huella_csv(invertido) == pte.huella_csv(csv_sintetico)
