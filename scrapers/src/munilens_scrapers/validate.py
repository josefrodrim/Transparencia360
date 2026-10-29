"""Validaciones de calidad sobre los registros del PTE Personal."""

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
from statistics import median
from typing import Literal

from munilens_scrapers.sources.pte_personal import RegistroPersonal

Severidad = Literal["error", "advertencia"]


@dataclass(frozen=True)
class Hallazgo:
    severidad: Severidad
    codigo: str
    mensaje: str
    pte_id_personal: str | None = None


@dataclass
class ReporteCalidad:
    periodo: str
    registros: int
    hallazgos: list[Hallazgo] = field(default_factory=list)
    estadisticas: dict[str, object] = field(default_factory=dict)

    @property
    def errores(self) -> int:
        return sum(1 for h in self.hallazgos if h.severidad == "error")

    @property
    def advertencias(self) -> int:
        return sum(1 for h in self.hallazgos if h.severidad == "advertencia")


def duplicados_exactos(registros: list[RegistroPersonal]) -> dict[str, str]:
    """{pte_id_personal duplicado: pte_id_personal de la primera aparición}.

    El PTE contiene periodos cargados dos veces (lotes con distinta FEC_REG). No se eliminan:
    se marcan para poder excluirlos de los agregados.
    """
    primero: dict[tuple, str] = {}
    dup: dict[str, str] = {}
    for r in sorted(registros, key=lambda r: (r.fecha_registro_pte, r.pte_id_personal)):
        if (pk := primero.setdefault(r.huella_contenido, r.pte_id_personal)) != r.pte_id_personal:
            dup[r.pte_id_personal] = pk
    return dup


def validar(registros: list[RegistroPersonal], anio: int, mes: int, ruc_esperado: str) -> ReporteCalidad:
    rep = ReporteCalidad(periodo=f"{anio:04d}-{mes:02d}", registros=len(registros))
    add = rep.hallazgos.append

    for pk, n in Counter(r.pte_id_personal for r in registros).items():
        if n > 1:
            add(Hallazgo("error", "pk_duplicada", f"aparece {n} veces", pk))

    for r in registros:
        pk = r.pte_id_personal
        if (r.anio, r.mes) != (anio, mes):
            add(Hallazgo("error", "periodo_distinto", f"{r.anio}-{r.mes:02d}", pk))
        if r.ruc_entidad != ruc_esperado:
            add(Hallazgo("error", "ruc_distinto", r.ruc_entidad, pk))
        if r.regimen is None:
            add(Hallazgo("advertencia", "regimen_desconocido", r.regimen_codigo, pk))
        if not (r.apellido_paterno or r.apellido_materno) or not r.nombres:
            add(Hallazgo("error", "nombre_incompleto", r.nombre_publicado, pk))
        if not r.cargo:
            add(Hallazgo("advertencia", "cargo_vacio", "", pk))
        if r.total != r.suma_componentes:
            add(Hallazgo("error", "total_inconsistente", f"{r.total} != {r.suma_componentes}", pk))
        if min(r.total, r.remuneraciones, r.honorarios, r.incentivo, r.gratificacion, r.otros_beneficios) < 0:
            add(Hallazgo("error", "monto_negativo", str(r.total), pk))
        if r.total == 0:
            add(Hallazgo("advertencia", "total_cero", "", pk))

    dup = duplicados_exactos(registros)
    if dup:
        add(Hallazgo("advertencia", "carga_duplicada", f"{len(dup)} registros idénticos a otros del mismo periodo"))
    unicos = [r for r in registros if r.pte_id_personal not in dup]

    # Mismo nombre publicado repetido (fuera de duplicados exactos): NO implica misma persona.
    nombres = Counter(r.nombre_busqueda for r in unicos)
    for nombre, n in nombres.items():
        if n > 1:
            add(Hallazgo("advertencia", "nombre_repetido", f"{n} registros con nombre '{nombre}'"))

    if registros:
        totales = [r.total for r in unicos]
        rep.estadisticas = {
            "registros_publicados": len(registros),
            "registros_unicos": len(unicos),
            "suma_total_publicada": str(sum((r.total for r in registros), Decimal(0))),
            "suma_total": str(sum(totales, Decimal(0))),
            "minimo": str(min(totales)),
            "maximo": str(max(totales)),
            "mediana": str(median(totales)),
            "por_regimen": dict(Counter(r.regimen or r.regimen_codigo for r in unicos)),
            "firma_contenido": sha256(
                repr(sorted(map(repr, (r.huella_contenido for r in unicos)))).encode()
            ).hexdigest(),
            "lotes_por_fecha_registro": dict(Counter(r.fecha_registro_pte.date().isoformat() for r in registros)),
            "fecha_registro_pte_min": min(r.fecha_registro_pte for r in registros).isoformat(),
            "fecha_registro_pte_max": max(r.fecha_registro_pte for r in registros).isoformat(),
        }
    return rep
