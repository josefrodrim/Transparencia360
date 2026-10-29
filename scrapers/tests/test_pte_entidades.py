from munilens_scrapers.sources import pte_entidades as pe
from munilens_scrapers.sources.inei_directorio import Municipalidad


def _m(ubigeo, provincia, distrito, tipo="distrital"):
    return Municipalidad(ubigeo, "Huancavelica", provincia, distrito, tipo, "", None)


def test_parse_resultados():
    page = (
        '<a href="../enlaces/pte_transparencia_enlaces.aspx?id_entidad=11915">MUNICIPALIDAD DISTRITAL DE ANTA - '
        'HUANCAVELICA</a><a href="x.aspx?id_entidad=11915">dup</a><a href="x.aspx?id_entidad=7">  &Aacute;REA </a>'
    )
    assert pe.parse_resultados(page) == [
        pe.Candidato(11915, "MUNICIPALIDAD DISTRITAL DE ANTA - HUANCAVELICA"),
        pe.Candidato(7, "ÁREA"),
    ]


def test_sufijo_con_departamento_da_confianza_alta():
    cands = [
        pe.Candidato(1, "MUNICIPALIDAD DISTRITAL DE ANTA - CUSCO"),
        pe.Candidato(11915, "MUNICIPALIDAD DISTRITAL DE ANTA - HUANCAVELICA"),
    ]
    e = pe.emparejar(_m("090303", "Acobamba", "Anta"), cands, homonimos_nacionales=2)
    assert (e.id_entidad, e.confianza) == (11915, "alta")


def test_sufijo_con_provincia_y_guiones():
    cands = [pe.Candidato(11944, "MUNICIPALIDAD DISTRITAL DE SAN JUAN-CASTROVIRREYNA-HUANCAVELICA")]
    e = pe.emparejar(_m("090410", "Castrovirreyna", "San Juan"), cands, homonimos_nacionales=5)
    assert (e.id_entidad, e.confianza) == (11944, "alta")


def test_nombre_unico_nacional_sin_sufijo_y_tildes():
    cands = [pe.Candidato(11959, "MUNICIPALIDAD PROVINCIAL DE HUAYTARA"), pe.Candidato(2, "UGEL HUAYTARA")]
    e = pe.emparejar(_m("090601", "Huaytará", "Huaytará", "provincial"), cands, homonimos_nacionales=1)
    assert (e.id_entidad, e.confianza) == (11959, "alta")


def test_homonimo_sin_sufijo_queda_pendiente():
    cands = [pe.Candidato(5, "MUNICIPALIDAD DISTRITAL DE PILPICHACA")]
    e = pe.emparejar(_m("090611", "Huaytará", "Pilpichaca"), cands, homonimos_nacionales=2)
    assert e.confianza == "pendiente" and e.id_entidad == 5


def test_sin_coincidencias_y_tipo_distinto():
    cands = [pe.Candidato(9, "MUNICIPALIDAD PROVINCIAL DE ACOBAMBA")]
    e = pe.emparejar(_m("090202", "Acobamba", "Acobamba"), cands, homonimos_nacionales=1)
    assert (e.id_entidad, e.confianza, e.motivo) == (None, "pendiente", "sin coincidencias")


def test_terminos_busqueda():
    assert pe.terminos_busqueda(_m("090616", "Huaytará", "Santiago de Chocorvos")) == [
        "Santiago de Chocorvos",
        "CHOCORVOS",
    ]
    assert pe.terminos_busqueda(_m("090101", "Huancavelica", "Huancavelica", "provincial")) == ["Huancavelica"]


def test_parse_ficha():
    assert pe.parse_ficha('<h2 class="x"> Municipalidad Distrital de Conayca (MD-Conayca)</h2>') == (
        "Municipalidad Distrital de Conayca (MD-Conayca)"
    )
    assert pe.parse_ficha("<h2>  </h2>") is None


def test_provincial_sin_de_con_capital():
    m = _m("090301", "Angaraes", "Lircay", "provincial")
    e = pe.emparejar(m, [pe.Candidato(1, "MUNICIPALIDAD PROVINCIAL ANGARAES LIRCAY")], homonimos_nacionales=1)
    assert (e.id_entidad, e.confianza) == (1, "alta")


def test_bloque_coincidencia_unica_y_prefijos_no_confunden():
    bloque = {
        11897: "Municipalidad Distrital de Conayca (MD-Conayca)",
        11931: "Municipalidad Distrital de San Antonio de Antaparco",
        11950: "Municipalidad Distrital de Anco",
        11951: "Municipalidad Distrital de Anco Huallo",
    }
    assert pe.emparejar_bloque(_m("090104", "Huancavelica", "Conayca"), bloque).id_entidad == 11897
    assert pe.emparejar_bloque(_m("090502", "Churcampa", "Anco"), bloque).id_entidad == 11950
    e = pe.emparejar_bloque(_m("090699", "Huaytará", "Inexistente"), bloque)
    assert (e.id_entidad, e.confianza) == (None, "pendiente")


def test_homonimos_en_el_mismo_departamento_se_resuelven_por_provincia():
    bloque = {
        11899: "Municipalidad Distrital de Huachocolpa - Huancavelica (MD-Huachocolpa)",
        11983: "MUNICIPALIDAD DISTRITAL DE HUACHOCOLPA - HUANCAVELICA - TAYACAJA",
    }
    provs = {"Huancavelica", "Tayacaja"}
    assert pe.emparejar_bloque(_m("090106", "Huancavelica", "Huachocolpa"), bloque, provs).id_entidad == 11899
    assert pe.emparejar_bloque(_m("090707", "Tayacaja", "Huachocolpa"), bloque, provs).id_entidad == 11983


def test_nombres_con_guion():
    m = _m("090307", "Angaraes", "Huanca-Huanca")
    assert pe.emparejar_bloque(m, {11927: "Municipalidad Distrital de Huanca-Huanca"}).id_entidad == 11927
    assert pe.emparejar_bloque(m, {11927: "Municipalidad Distrital de Huanca Huanca (MDHH)"}).id_entidad == 11927
