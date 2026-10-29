from dataclasses import replace
from decimal import Decimal

from munilens_scrapers.sources import pte_personal as pte
from munilens_scrapers.validate import duplicados_exactos, validar


def _regs(csv_sintetico):
    return [pte.normalizar(f) for f in pte.leer_csv(csv_sintetico)]


def _codigos(rep):
    return {h.codigo for h in rep.hallazgos}


def test_datos_consistentes_sin_errores(csv_sintetico):
    rep = validar(_regs(csv_sintetico), 2026, 8, "20000000001")
    assert rep.errores == 0
    assert rep.registros == 3
    assert rep.estadisticas["suma_total"] == "12594.6900"
    assert rep.estadisticas["mediana"] == "3150.5000"


def test_detecta_inconsistencias(csv_sintetico):
    r0, r1, r2 = _regs(csv_sintetico)
    malos = [
        replace(r0, total=Decimal("1")),
        replace(r1, mes=7, regimen_codigo="99", regimen=None),
        replace(r2, ruc_entidad="1", nombres=""),
        r2,
    ]
    codigos = _codigos(validar(malos, 2026, 8, "20000000001"))
    assert {
        "total_inconsistente",
        "periodo_distinto",
        "regimen_desconocido",
        "ruc_distinto",
        "nombre_incompleto",
        "pk_duplicada",
    } <= codigos


def test_nombre_repetido_es_advertencia_no_error(csv_sintetico):
    r0, r1, _ = _regs(csv_sintetico)
    homonimo = replace(
        r1,
        pte_id_personal="9",
        apellido_paterno=r0.apellido_paterno,
        apellido_materno=r0.apellido_materno,
        nombres=r0.nombres,
    )
    rep = validar([r0, homonimo], 2026, 8, "20000000001")
    assert rep.errores == 0
    assert "nombre_repetido" in _codigos(rep)


def test_carga_duplicada_se_marca_y_excluye_de_agregados(csv_sintetico):
    r0, r1, r2 = _regs(csv_sintetico)
    recarga = replace(r0, pte_id_personal="10", fecha_registro_pte=r0.fecha_registro_pte.replace(hour=15))
    rep = validar([r0, r1, r2, recarga], 2026, 8, "20000000001")
    assert rep.errores == 0
    assert "carga_duplicada" in _codigos(rep)
    assert "nombre_repetido" not in _codigos(rep)
    assert rep.estadisticas["registros_publicados"] == 4
    assert rep.estadisticas["registros_unicos"] == 3
    assert rep.estadisticas["suma_total"] == "12594.6900"
    assert rep.estadisticas["suma_total_publicada"] == "14758.8800"
    assert duplicados_exactos([r0, r1, r2, recarga]) == {"10": r0.pte_id_personal}
