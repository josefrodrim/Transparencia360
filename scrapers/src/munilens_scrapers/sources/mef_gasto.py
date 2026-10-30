"""MEF — Presupuesto y Ejecución de Gasto, devengado mensual (Consulta Amigable en datos abiertos).

Verificado el 2026-10-29:
- Catálogo: https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecución-de-gasto-–-devengado-mensual
- Archivos: https://fs.datosabiertos.mef.gob.pe/datastorefiles/{AAAA}-Gasto-Devengado-Mensual.csv (2025+);
  hasta 2024: {AAAA}-Gasto-Devengado.csv. ~2,5 GB por año, todo el sector público, una fila por cadena de gasto
  con MONTO_DEVENGADO_ENERO … _DICIEMBRE.
- Son montos AGREGADOS por unidad ejecutora (no por persona). Complementan al PTE para municipalidades que no
  publican su personal.

Indicadores (clasificador de gasto; verificados contra los datos de 2026 de Huancavelica). Una fila puede sumar a
más de un indicador (p. ej. CAS también está dentro de "personal"):
- personal: genérica 2.1 "PERSONAL Y OBLIGACIONES SOCIALES" completa (planilla, CAS, obreros, dietas, aportes…).
- cas: 2.1.1.13 "CONTRATO ADMINISTRATIVO DE SERVICIOS". En años anteriores el CAS se registraba en 2.3.2.8; esa
  partida también se cuenta como "cas" (no forma parte de "personal" porque está en bienes y servicios).
- dietas: 2.1.1.10 "DIETAS" (regidores).
- locacion_pn: 2.3.2.9 "LOCACIÓN DE SERVICIOS REALIZADOS POR PERSONAS NATURALES" (honorarios a personas).
- pensiones: genérica 2.2 "PENSIONES Y OTRAS PRESTACIONES SOCIALES".
"""

import csv
from collections import defaultdict
from collections.abc import Iterable, Iterator
from decimal import Decimal

FUENTE = "mef_gasto_devengado"
MESES = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]
COLUMNAS_MES = [f"MONTO_DEVENGADO_{m}" for m in MESES]
REQUERIDAS = {
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
    "MONTO_PIM",
    *COLUMNAS_MES,
}


class FormatoInesperadoError(ValueError):
    pass


def url_anual(anio: int) -> str:
    nombre = f"{anio}-Gasto-Devengado.csv" if anio <= 2024 else f"{anio}-Gasto-Devengado-Mensual.csv"
    return f"https://fs.datosabiertos.mef.gob.pe/datastorefiles/{nombre}"


def filtrar(lineas: Iterable[str], departamento: str, nivel: str = "M") -> Iterator[list[str]]:
    """Primera fila = cabecera. Devuelve solo filas del nivel de gobierno y departamento de la ejecutora."""
    reader = csv.reader(lineas)
    cab = next(reader)
    if missing := REQUERIDAS - set(cab):
        raise FormatoInesperadoError(f"faltan columnas: {sorted(missing)}")
    i_niv, i_dep = cab.index("NIVEL_GOBIERNO"), cab.index("DEPARTAMENTO_EJECUTORA")
    yield cab
    for fila in reader:
        if len(fila) == len(cab) and fila[i_niv] == nivel and fila[i_dep] == departamento:
            yield fila


def indicadores(fila: dict[str, str]) -> list[str]:
    if fila["TIPO_TRANSACCION"] != "2":  # 2 = gastos presupuestarios
        return []
    g, sg, sgd = fila["GENERICA"], fila["SUBGENERICA"], fila["SUBGENERICA_DET"]
    res = []
    if g == "1":
        res.append("personal")
        if (sg, sgd) == ("1", "13"):
            res.append("cas")
        elif (sg, sgd) == ("1", "10"):
            res.append("dietas")
    elif g == "2":
        res.append("pensiones")
    elif (g, sg, sgd) == ("3", "2", "8"):
        res.append("cas")
    elif (g, sg, sgd) == ("3", "2", "9"):
        res.append("locacion_pn")
    return res


def agregar(filas: Iterable[dict[str, str]]) -> list[dict[str, object]]:
    """Suma devengado por (ubigeo de la ejecutora, ejecutora, mes, indicador)."""
    tot: dict[tuple, Decimal] = defaultdict(Decimal)
    nombres: dict[tuple, tuple[str, str]] = {}
    for f in filas:
        inds = indicadores(f)
        if not inds:
            continue
        ubigeo = f["DEPARTAMENTO_EJECUTORA"] + f["PROVINCIA_EJECUTORA"] + f["DISTRITO_EJECUTORA"]
        clave_ej = (ubigeo, f["SEC_EJEC"])
        nombres[clave_ej] = (f["PLIEGO_NOMBRE"], f["EJECUTORA_NOMBRE"])
        for mes, col in enumerate(COLUMNAS_MES, start=1):
            monto = Decimal(f[col] or "0")
            if monto:
                for ind in inds:
                    tot[(*clave_ej, int(f["ANO_EJE"]), mes, ind)] += monto
    salida = []
    for (ubigeo, sec, anio, mes, ind), monto in sorted(tot.items()):
        pliego, ejecutora = nombres[(ubigeo, sec)]
        salida.append(
            {
                "ubigeo": ubigeo,
                "sec_ejec": sec,
                "pliego": pliego,
                "ejecutora": ejecutora,
                "anio": anio,
                "mes": mes,
                "indicador": ind,
                "devengado": monto,
            }
        )
    return salida
