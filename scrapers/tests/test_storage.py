from munilens_scrapers.storage import RawStore


def test_nuevo_sin_cambios_cambiado_y_sin_datos(tmp_path):
    s = RawStore(tmp_path)
    a = s.guardar("f", "e", "2026-08", "u", b"v1")
    b = s.guardar("f", "e", "2026-08", "u", b"v1")
    c = s.guardar("f", "e", "2026-08", "u", b"v2")
    d = s.guardar("f", "e", "2020-06", "u", b"")
    assert [x.estado for x in (a, b, c, d)] == ["nuevo", "sin_cambios", "cambiado", "sin_datos"]
    assert a.ruta == b.ruta != c.ruta  # no duplica archivos idénticos
    assert len(list((tmp_path / "f" / "e" / "2026-08").iterdir())) == 2
    assert len(s.historial("f", "e")) == 4


def test_error_queda_registrado(tmp_path):
    s = RawStore(tmp_path)
    s.registrar_error("f", "e", "2026-08", "u", "timeout")
    (h,) = s.historial("f", "e")
    assert h.estado == "error" and h.error == "timeout"


def test_huella_canonica_ignora_reordenamiento(tmp_path):
    s = RawStore(tmp_path)
    a = s.guardar("f", "e", "p", "u", b"x\ny", huella="H")
    b = s.guardar("f", "e", "p", "u", b"y\nx", huella="H")
    assert (a.estado, b.estado) == ("nuevo", "sin_cambios")
    assert b.ruta == a.ruta and b.sha256 == a.sha256
    assert len(list((tmp_path / "f" / "e" / "p").iterdir())) == 1
