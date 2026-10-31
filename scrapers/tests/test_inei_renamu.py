"""Datos SINTÉTICOS con la estructura del CSV F01 de RENAMU (separador «;», UTF-8 con BOM)."""

import io
import zipfile

import pytest

from munilens_scrapers.sources import inei_renamu as renamu

COLS = sorted(renamu.REQUERIDAS - {"Ubigeo"})


def _csv(filas: list[dict[str, str]]) -> str:
    cab = ["Año", "Ubigeo", *COLS]
    lineas = [";".join(cab)]
    for f in filas:
        lineas.append(";".join(f.get(c, "") for c in cab))
    return "﻿" + "\r\n".join(lineas) + "\r\n"


def _fila(ubigeo, **v):
    base = {"Ubigeo": ubigeo, "P19": "1"}
    base.update({k: str(x) for k, x in v.items()})
    return base


def test_lee_conteos_por_regimen():
    texto = _csv(
        [
            _fila("090101", P19D_T=10, P19D_NM=1, P19D_NH=2, P19D_VM=3, P19D_VH=4, P19D_CH=0, P19A_1_T=5),
            {"Ubigeo": "090116", "P19": "2", "P19D_T": "#¡NULO!", "P19A_1_T": "11"},
        ]
    )
    a, b = renamu.leer_csv(texto.lstrip("﻿"))
    assert a.total_dic == 10 and a.por_regimen_dic == {"276_nombrado": 3, "276_contratado": 0, "728": 0, "cas": 7}
    assert a.locacion_dic == 5 and a.tiene_personal
    assert not b.tiene_personal and b.total_dic is None and b.locacion_dic == 11
    assert renamu.validar([a, b]) == []


def test_valida_total_y_duplicados():
    texto = _csv([_fila("090101", P19D_T=9, P19D_VM=3), _fila("090101", P19D_T=0)])
    errores = renamu.validar(renamu.leer_csv(texto))
    assert any("≠ suma" in e for e in errores) and any("duplicado" in e for e in errores)


def test_zip_y_formato_inesperado():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Base_de_Datos_F01_RENAMU2099.csv", _csv([_fila("090101", P19D_T=1, P19D_VH=1)]).encode())
        z.writestr("diccionario.pdf", b"%PDF")
    nombre, regs = renamu.leer_zip(buf.getvalue())
    assert nombre.endswith(".csv") and regs[0].por_regimen_dic["cas"] == 1
    with pytest.raises(renamu.FormatoInesperadoError):
        renamu.leer_csv("Ubigeo;P19\n090101;1\n")
    with pytest.raises(renamu.FormatoInesperadoError):
        renamu.leer_csv(_csv([_fila("090101", P19D_T="abc")]))
