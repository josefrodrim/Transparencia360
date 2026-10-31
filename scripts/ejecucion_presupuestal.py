"""Ejecución presupuestal de las municipalidades: quién no gasta el dinero que recibe.

Uso (desde scripts/): ../.venv/bin/python ejecucion_presupuestal.py 09 > ../docs/ejecucion_presupuestal_huancavelica.md

Lee los subconjuntos RAW del MEF (data/raw/mef_gasto_devengado/{dep}/{AAAA}.csv, generados con munilens-mef).
Ejecución = devengado anual ÷ PIM (presupuesto institucional modificado), solo gastos presupuestarios.
Criterios (elegidos por el usuario el 2026-10-31):
  - Semáforo: verde ≥ 90 %, amarillo 75–90 %, naranja 60–75 %, rojo < 60 % (total e inversión, genérica 2.6).
  - Reincidentes: rojo o naranja en los dos últimos años cerrados.
  - Ritmo del año en curso: avance a septiembre frente a su propio avance histórico a septiembre.
  - Gasto de último minuto: diciembre concentra más del 30 % del devengado anual.
  - Ranking histórico: posición por año fiscal desde el primer año con presupuesto en los datos (2012 en adelante).
"""

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
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
SEMAFORO = [(90, "verde"), (75, "amarillo"), (60, "naranja"), (0, "rojo")]
ULTIMO_MINUTO = 0.30
RITMO_TOLERANCIA = 15  # puntos porcentuales por debajo de su avance histórico a septiembre
MES_CORTE = 9  # el año en curso tiene devengado hasta septiembre
OBRA_PIM_MIN = 200_000  # obra parada: presupuesto del año ≥ S/ 200 mil …
OBRA_AVANCE_MAX = 10  # … y avance ≤ 10 % al cierre del año


def color(pct: float | None) -> str:
    if pct is None:
        return "—"
    return next(c for umbral, c in SEMAFORO if pct >= umbral)


def soles_m(x: float) -> str:
    return f"{x / 1e6:,.1f}".replace(",", " ").replace(".", ",") + " M"


def cargar(dep: str) -> tuple[dict, list[int], dict, dict]:
    """Métricas por (ubigeo, año), por (ubigeo, año, proyecto) y por (año, función) desde los subconjuntos RAW."""
    carpeta = RAIZ / "data/raw/mef_gasto_devengado" / dep
    anios = sorted(int(p.stem) for p in carpeta.glob("*.csv"))
    datos: dict = defaultdict(lambda: defaultdict(float))
    proyectos: dict = defaultdict(lambda: {"pim": 0.0, "dev": 0.0, "nombre": "", "funcion": ""})
    funciones: dict = defaultdict(lambda: [0.0, 0.0])
    for anio in anios:
        with (carpeta / f"{anio}.csv").open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["TIPO_TRANSACCION"] != "2":
                    continue
                u = r["DEPARTAMENTO_EJECUTORA"] + r["PROVINCIA_EJECUTORA"] + r["DISTRITO_EJECUTORA"]
                d = datos[(u, anio)]
                pim = float(r["MONTO_PIM"] or 0)
                mensual = [float(r[f"MONTO_DEVENGADO_{m}"] or 0) for m in MESES]
                dev = sum(mensual)
                d["pim"] += pim
                d["dev"] += dev
                d["dev_sep"] += sum(mensual[:MES_CORTE])
                d["dev_dic"] += mensual[11]
                if r["GENERICA"] == "6":  # adquisición de activos no financieros (inversión)
                    d["pim_inv"] += pim
                    d["dev_inv"] += dev
                if r["RUBRO"] == "00":  # recursos ordinarios: lo no ejecutado revierte al Tesoro
                    d["pim_ro"] += pim
                    d["dev_ro"] += dev
                if r["TIPO_ACT_PROY"].upper().startswith("PROY"):
                    pr = proyectos[(u, anio, r["PRODUCTO_PROYECTO"])]
                    pr["pim"] += pim
                    pr["dev"] += dev
                    pr["nombre"] = r["PRODUCTO_PROYECTO_NOMBRE"].strip()
                    pr["funcion"] = r["FUNCION_NOMBRE"].strip()
                for clave in ((anio, r["FUNCION_NOMBRE"].strip()), (u, anio, r["FUNCION_NOMBRE"].strip())):
                    fn = funciones[clave]
                    fn[0] += pim
                    fn[1] += dev
    return datos, anios, proyectos, funciones


def calcular(dep: str):
    with (RAIZ / "database/seeds/municipalidades.csv").open() as f:
        munis = {r["ubigeo"]: r for r in csv.DictReader(f) if r["ubigeo"].startswith(dep)}
    datos, anios, proyectos, funciones = cargar(dep)
    en_curso = max(anios)
    cerrados = [a for a in anios if a < en_curso]

    def ejec(d, k="") -> float | None:
        p = d.get(f"pim{k}", 0)
        return 100 * d.get(f"dev{k}", 0) / p if p > 0 else None

    filas = {}
    for u, m in munis.items():
        por_anio = {}
        for a in anios:
            d = datos.get((u, a))
            if not d or d["pim"] <= 0:
                continue
            por_anio[a] = {
                "pim": d["pim"],
                "dev": d["dev"],
                "ejec": ejec(d),
                "ejec_inv": ejec(d, "_inv"),
                "sin_ejecutar": d["pim"] - d["dev"],
                "ro_no_ejecutado": d["pim_ro"] - d["dev_ro"],
                "avance_sep": 100 * d["dev_sep"] / d["pim"],
                "dic": d["dev_dic"] / d["dev"] if d["dev"] > 0 else None,
                # montos base para agregar por provincia o departamento
                "pim_inv": d["pim_inv"],
                "dev_inv": d["dev_inv"],
                "dev_sep": d["dev_sep"],
                "dev_dic": d["dev_dic"],
                "funciones": {k[2]: v for k, v in funciones.items() if len(k) == 3 and k[0] == u and k[1] == a},
            }
        filas[u] = {"muni": m, "anios": por_anio}

    # Ranking por año fiscal cerrado (1 = la que más ejecuta)
    for a in cerrados:
        orden = sorted((u for u in filas if a in filas[u]["anios"]), key=lambda u: -filas[u]["anios"][a]["ejec"])
        for i, u in enumerate(orden, start=1):
            filas[u]["anios"][a]["puesto"] = i
            filas[u]["anios"][a]["de"] = len(orden)

    ult2 = cerrados[-2:]
    for u, f in filas.items():
        a_ = f["anios"]
        hist = [a_[a]["ejec"] for a in cerrados if a in a_]
        f["primer_anio"] = min(a_) if a_ else None
        f["ejec_media"] = statistics.mean(hist) if hist else None
        f["anios_rojo"] = sum(1 for a in cerrados if a in a_ and color(a_[a]["ejec"]) == "rojo")
        f["reincidente"] = all(a in a_ and color(a_[a]["ejec"]) in ("rojo", "naranja") for a in ult2)
        f["ultimo_minuto"] = [a for a in cerrados if a in a_ and (a_[a]["dic"] or 0) > ULTIMO_MINUTO]
        previos = [a_[a]["avance_sep"] for a in cerrados if a in a_]
        f["avance_esperado"] = statistics.median(previos) if previos else None
        actual = a_.get(en_curso, {}).get("avance_sep")
        f["avance_actual"] = actual
        f["ritmo_lento"] = (
            actual is not None and f["avance_esperado"] is not None and actual < f["avance_esperado"] - RITMO_TOLERANCIA
        )
    ranking_hist = sorted(
        (u for u in filas if filas[u]["ejec_media"] is not None), key=lambda u: filas[u]["ejec_media"]
    )

    # Obras paradas: proyecto con presupuesto relevante y avance mínimo al cierre de un año
    paradas = []
    por_codigo: dict = defaultdict(list)
    for (u, a, cod), pr in proyectos.items():
        if a in cerrados and u in munis and pr["pim"] >= OBRA_PIM_MIN:
            avance = 100 * pr["dev"] / pr["pim"]
            if avance <= OBRA_AVANCE_MAX:
                fila = {"ubigeo": u, "anio": a, "codigo": cod, "avance": avance, **pr}
                paradas.append(fila)
                por_codigo[(u, cod)].append(fila)
    recurrentes = sorted(
        (v for v in por_codigo.values() if len(v) >= 2), key=lambda v: (-len(v), -max(x["pim"] for x in v))
    )
    for u, f in filas.items():
        f["obras_paradas"] = sorted((x for x in paradas if x["ubigeo"] == u), key=lambda x: (-x["anio"], -x["pim"]))
    return filas, anios, cerrados, en_curso, ranking_hist, paradas, recurrentes, funciones


def main(dep: str) -> None:
    filas, anios, cerrados, en_curso, ranking_hist, paradas, recurrentes, funciones = calcular(dep)
    ult = cerrados[-1]
    nombre = lambda u: filas[u]["muni"]["nombre"].replace("Municipalidad ", "")

    print("# Ejecución presupuestal de las municipalidades de Huancavelica\n")
    print(
        f"Generado con `scripts/ejecucion_presupuestal.py {dep}`. Fuente: MEF, gasto devengado mensual (datos abiertos),"
    )
    print(f"años {anios[0]}–{en_curso} ({en_curso} con devengado hasta septiembre). **Ejecución** = devengado ÷ PIM")
    print(
        "(presupuesto final del año, con modificaciones). **Inversión** = genérica 2.6. Solo gastos presupuestarios.\n"
    )
    print("- **Semáforo:** verde ≥ 90 %, amarillo 75–90 %, naranja 60–75 %, rojo < 60 %.")
    print(f"- **Reincidente:** rojo o naranja en {cerrados[-2]} y {cerrados[-1]}.")
    print(
        f"- **Ritmo {en_curso}:** avance a septiembre más de {RITMO_TOLERANCIA} puntos por debajo de su avance típico a"
    )
    print("  septiembre en años anteriores.")
    print(f"- **Último minuto:** diciembre concentra más del {int(ULTIMO_MINUTO * 100)} % del gasto del año.")
    print("- **Recursos ordinarios no ejecutados:** según el MEF, lo no ejecutado con recursos ordinarios revierte al")
    print(
        "  Tesoro al cierre (comunicado 013-2020-EF/52.06); el saldo de otras fuentes (canon, FONCOMUN, etc.) pasa al"
    )
    print("  año siguiente como saldo de balance (comunicado 030-2023-EF/50.01). No es dinero perdido para la")
    print("  municipalidad salvo en el primer caso.\n")

    # Resumen departamental por año
    print("## Departamento: cuánto se dejó de gastar cada año\n")
    print(
        "| Año | PIM | Devengado | Ejecución | Sin ejecutar | De ello, recursos ordinarios | Municipalidades en rojo |"
    )
    print("|---|---|---|---|---|---|---|")
    for a in cerrados:
        pim = sum(f["anios"][a]["pim"] for f in filas.values() if a in f["anios"])
        dev = sum(f["anios"][a]["dev"] for f in filas.values() if a in f["anios"])
        ro = sum(f["anios"][a]["ro_no_ejecutado"] for f in filas.values() if a in f["anios"])
        rojos = sum(1 for f in filas.values() if a in f["anios"] and color(f["anios"][a]["ejec"]) == "rojo")
        n = sum(1 for f in filas.values() if a in f["anios"])
        print(
            f"| {a} | {soles_m(pim)} | {soles_m(dev)} | {100 * dev / pim:.0f} % | {soles_m(pim - dev)} | "
            f"{soles_m(ro)} | {rojos} de {n} |"
        )

    print(f"\n## Semáforo {ult} (último año cerrado)\n")
    print(f"| # | Municipalidad | Provincia | PIM {ult} | Ejecución | Inversión | Sin ejecutar | Puesto | Señales |")
    print("|---|---|---|---|---|---|---|---|---|")
    orden = sorted((u for u in filas if ult in filas[u]["anios"]), key=lambda u: filas[u]["anios"][ult]["ejec"])
    for i, u in enumerate(orden, start=1):
        f, d = filas[u], filas[u]["anios"][ult]
        senales = []
        if f["reincidente"]:
            senales.append("reincidente")
        if f["ritmo_lento"]:
            senales.append(f"ritmo {en_curso} lento")
        if f["ultimo_minuto"]:
            n = len(f["ultimo_minuto"])
            senales.append(f"último minuto ({n} {'año' if n == 1 else 'años'})")
        inv = f"{d['ejec_inv']:.0f} % {color(d['ejec_inv'])}" if d["ejec_inv"] is not None else "—"
        print(
            f"| {i} | {nombre(u)} ({u}) | {f['muni']['provincia']} | {soles_m(d['pim'])} | "
            f"**{d['ejec']:.0f} %** {color(d['ejec'])} | {inv} | {soles_m(d['sin_ejecutar'])} | "
            f"{d['puesto']} de {d['de']} | {', '.join(senales) or '—'} |"
        )

    print(f"\n## Ritmo {en_curso}: van más lento que de costumbre\n")
    lentos = sorted(
        (u for u in filas if filas[u]["ritmo_lento"]),
        key=lambda u: filas[u]["avance_actual"] - filas[u]["avance_esperado"],
    )
    print(f"| Municipalidad | Avance a sep. {en_curso} | Avance típico a sep. | Diferencia | PIM {en_curso} |")
    print("|---|---|---|---|---|")
    for u in lentos:
        f = filas[u]
        print(
            f"| {nombre(u)} ({u}) | {f['avance_actual']:.0f} % | {f['avance_esperado']:.0f} % | "
            f"{f['avance_actual'] - f['avance_esperado']:+.0f} pp | {soles_m(f['anios'][en_curso]['pim'])} |"
        )
    if not lentos:
        print("| — | — | — | — | — |")

    print("\n## Ranking histórico (promedio de ejecución en sus años fiscales cerrados)\n")
    print(
        "Desde el primer año con presupuesto en los datos abiertos del MEF (2012) o desde su creación, si es posterior.\n"
    )
    print("| # | Municipalidad | Desde | Años | Ejecución promedio | Años en rojo | Mejor año | Peor año |")
    print("|---|---|---|---|---|---|---|---|")
    for i, u in enumerate(ranking_hist, start=1):
        f = filas[u]
        cer = {a: f["anios"][a]["ejec"] for a in cerrados if a in f["anios"]}
        mejor, peor = max(cer, key=cer.get), min(cer, key=cer.get)
        print(
            f"| {i} | {nombre(u)} ({u}) | {f['primer_anio']} | {len(cer)} | **{f['ejec_media']:.0f} %** | "
            f"{f['anios_rojo']} | {mejor} ({cer[mejor]:.0f} %) | {peor} ({cer[peor]:.0f} %) |"
        )

    print("\n## Gasto de último minuto (diciembre > 30 % del año)\n")
    um = sorted((u for u in filas if filas[u]["ultimo_minuto"]), key=lambda u: -len(filas[u]["ultimo_minuto"]))
    print("| Municipalidad | Años | Mayor proporción en diciembre |")
    print("|---|---|---|")
    for u in um:
        f = filas[u]
        peor = max(f["ultimo_minuto"], key=lambda a: f["anios"][a]["dic"])
        print(
            f"| {nombre(u)} ({u}) | {', '.join(map(str, f['ultimo_minuto']))} | "
            f"{100 * f['anios'][peor]['dic']:.0f} % en {peor} |"
        )

    print(f"\n## En qué se gastó en {ult} (departamento, por función)\n")
    print("| Función | Presupuesto (PIM) | Gastado | Ejecución | Sin gastar |")
    print("|---|---|---|---|---|")
    dep_fn = ((k, v) for k, v in funciones.items() if len(k) == 2 and k[0] == ult)
    for (a, fn), (p, d) in sorted(dep_fn, key=lambda x: -x[1][0]):
        if p > 0:
            print(
                f"| {fn.capitalize()} | {soles_m(p)} | {soles_m(d)} | {100 * d / p:.0f} % {color(100 * d / p)} | "
                f"{soles_m(p - d)} |"
            )

    print(f"\n## Obras paradas en {ult}\n")
    print(
        f"Proyectos con presupuesto de S/ {OBRA_PIM_MIN:,} o más en el año y {OBRA_AVANCE_MAX} % o menos de avance".replace(
            ",", " "
        )
        + " al cierre. Ordenados por presupuesto sin usar.\n"
    )
    print("| Municipalidad | Código | Proyecto | Función | PIM | Avance |")
    print("|---|---|---|---|---|---|")
    for x in sorted((x for x in paradas if x["anio"] == ult), key=lambda x: -(x["pim"] - x["dev"])):
        print(
            f"| {nombre(x['ubigeo'])} | {x['codigo']} | {x['nombre']} | {x['funcion'].capitalize()} | "
            f"{soles_m(x['pim'])} | {x['avance']:.0f} % |"
        )

    print("\n## Obras paradas varios años\n")
    print("El mismo proyecto aparece parado (≥ S/ 200 mil y ≤ 10 % de avance) en dos o más años fiscales.\n")
    print("| Municipalidad | Código | Proyecto | Años parado | Mayor PIM anual |")
    print("|---|---|---|---|---|")
    for v in recurrentes:
        x = v[0]
        print(
            f"| {nombre(x['ubigeo'])} | {x['codigo']} | {x['nombre']} | {', '.join(str(y['anio']) for y in sorted(v, key=lambda y: y['anio']))} | "
            f"{soles_m(max(y['pim'] for y in v))} |"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "09")
