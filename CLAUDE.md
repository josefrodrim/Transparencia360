# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

MuniLens: plataforma de transparencia sobre el personal municipal del Perú, empezando por Huancavelica.
**Prioridad: obtener las remuneraciones (salarios) individuales publicadas**; todo lo demás es secundario. El plan por
fases (1. fuentes → 2. scraper piloto → 3. PostgreSQL → 4. FastAPI → 5. Next.js → ...) está en `docs/plan.md`.
Estado actual: Fases 1 y 2 en curso. Existen `scrapers/` y `database/seeds/`; aún no hay backend ni frontend.

## Comandos

Entorno: `.venv` en la raíz (Python 3.12). Paquete instalado en modo editable: `.venv/bin/pip install -e "scrapers[dev]"`.

```bash
.venv/bin/munilens-extract --entidad mp-huancavelica --desde 2024-01 --hasta 2026-10   # desde la raíz → data/
.venv/bin/munilens-extract --ubigeo 090201 --desde 2024-01 --hasta 2026-10              # cualquier muni con cruce PTE "alta"
.venv/bin/munilens-inei --url <xlsx del directorio INEI>   # → database/seeds/municipalidades.csv (+ .meta.json)
.venv/bin/munilens-pte-descubrir --departamento 09 --bloque 11890-11995 --sondeo ""   # → database/seeds/pte_entidades_09.csv
cd scrapers && ../.venv/bin/pytest                         # unitarias
../.venv/bin/pytest tests/test_validate.py::test_detecta_inconsistencias   # una prueba
MUNILENS_RED=1 ../.venv/bin/pytest -m red                  # integración contra el portal real
../.venv/bin/ruff check . && ../.venv/bin/ruff format .
```

## Arquitectura de `scrapers/src/munilens_scrapers`

Flujo por periodo (`cli.procesar_periodo`): `client.PoliteClient` (robots.txt, 3 s entre peticiones, reintentos) →
`storage.RawStore.guardar` (RAW inmutable + `manifest.jsonl`; compara versiones por *huella* canónica porque el PTE
devuelve las filas en orden variable) → `sources/pte_personal` (`leer_csv` exige las columnas exactas y lanza
`FormatoInesperadoError` si cambian; `normalizar` → `RegistroPersonal` con `Decimal`) → `validate.validar`
(`ReporteCalidad`; `duplicados_exactos` marca las re-cargas del mismo periodo) → CSV procesado + JSON de calidad +
reporte Markdown. Cada fuente nueva va en `sources/` como módulo propio; las entidades, en `config/entidades.toml`.

`sources/inei_directorio` + `cli_inei`: directorio de municipalidades del INEI (XLSX) → seed versionado
`database/seeds/municipalidades.csv` (ubigeo como clave; sin alcalde, teléfonos ni correos).

`sources/pte_entidades` + `cli_pte_descubrir`: cruce INEI ↔ `id_entidad` del PTE. Lee las fichas de un bloque de ids
consecutivo (las municipalidades de un departamento están en orden de ubigeo) y cruza por nombre; el buscador del PTE
solo es respaldo (máx. 20 resultados, subcadena, omite entidades). Ante ambigüedad → `pendiente`.

Particularidades del PTE: ver `docs/fuentes-huancavelica.md` (periodos vacíos = respuesta de 0 bytes, cargas
duplicadas, meses idénticos, desfase de publicación).

## Estado y cómo retomar (actualizado 2026-10-29)

Hecho y en git:
- Extractor PTE Personal validado con la MP de Huancavelica (id 980): 26 periodos con datos entre 2024-01 y 2026-10.
- Directorio INEI (oct. 2026): 102 municipalidades en Huancavelica → `database/seeds/municipalidades.csv`.
- Cruce PTE: 95/102 con confianza alta; 7 pendientes (Cosme 090511 y distritos nuevos de Tayacaja 090719–090725),
  probablemente sin ficha en el PTE.
- Sondeo de salarios (2026-05, 2025-12, 2024-06) en 91 municipalidades: **solo 7 publicaron personal** en esos meses:
  MP Huancavelica, MD Ascensión (090118), MP Acobamba (090201), MD Caja (090204), MP Angaraes (090301),
  MD San Antonio de Antaparco (090310), MP Tayacaja (090701). El resto devolvió 0 registros en los 3 meses.

- Extracción completa 2024-01→2026-10 hecha para esas 7 (tabla en `docs/fuentes-huancavelica.md` §3). 090106,
  090307 y 090609 no tienen datos. Ascensión y Acobamba traen filas con total ≠ suma de componentes (se marcan, no se
  corrigen). `data/` es local: si se perdió, se regenera con `munilens-extract --ubigeo <u> --desde 2024-01 --hasta 2026-10`.

- **Sondeo exhaustivo terminado** (2026-10-29): de 102 municipalidades, solo 10 publicaron personal en 2024-01→2026-10
  (090101, 090117, 090118, 090119, 090201, 090204, 090301, 090304, 090310, 090701); tabla en
  `docs/fuentes-huancavelica.md` §3. Para rehacerlo: `scripts/sondeo_exhaustivo.sh <lista> 2024-01 2026-10` (reanudable).
- El lector repara registros partidos en varias líneas (`fila_reparada`); `validate` marca `monto_atipico`
  (> 10× la mediana y > S/ 30 000) solo para revisión.

- Perfil de Angaraes (0903): `docs/perfil_angaraes.md`, generado con `scripts/perfil_provincia.py 0903` (cruza
  PTE con MEF; solo agregados). Sirve para cualquier provincia (`0901`, `0907`...).
- Sueldos de alcaldes (102/102): `docs/sueldos_alcaldes_huancavelica.md` con `scripts/sueldos_alcaldes.py 09`
  (indicadores MEF `alcalde` = 2.1.1.1.1.1 y `ley_servir` = 2.1.1.1.1.8; contrastado con el PTE).

- RENAMU 2026 (personal por régimen, 1 892 municipalidades): `munilens-renamu` → `database/seeds/renamu2026_personal.csv`.
  Promedio CAS = MEF ÷ RENAMU no es fiable (ver `docs/fuentes-huancavelica.md` §4.3).
- Ranking de transparencia: `docs/ranking_transparencia_huancavelica.md` con `scripts/ranking_transparencia.py 09`.
- Señales de alerta: `docs/senales_alerta_huancavelica.md` con `scripts/senales_alerta.py 09` (indicios, no pruebas).
- En curso (pedido del usuario): ficha ciudadana por municipalidad (junta sueldos, ranking y alertas).

Siguiente:
- MEF devengado 2024–2026 extraído para las 102 municipalidades; tabla en `docs/mef_gasto_personal_huancavelica.md`
  (subconjuntos RAW en `data/raw/mef_gasto_devengado/09/`, regenerables).

1. (Hecho) Para las 92 que no publican: MEF devengado mensual (gasto agregado por municipalidad: personal 2.1, CAS 2.3.2.8,
   pensiones 2.2) → `munilens-mef --departamento 09 --anios 2024,2025,2026` (streaming de ~2,5 GB/año, guarda solo el
   subconjunto). **Las solicitudes de acceso a la información (Ley 27806) quedan descartadas por decisión del usuario.**
2. Alcance: solo municipalidades (el usuario descartó el Congreso).

## Reglas del proyecto

- No inventar datos ni declarar que una fuente funciona sin comprobarla. Documentar cada fuente en `docs/`.
- No evadir CAPTCHA ni controles de acceso, y no hacer consultas masivas sin autorización. SUNEDU no se automatiza
  sin verificar antes que esté permitido.
- `data/` contiene datos personales reales y está en `.gitignore`. Los fixtures de pruebas son sintéticos.
- No eliminar registros de la fuente: marcarlos (p. ej. `duplicado_de`). Mismo nombre ≠ misma persona.
  No anualizar ni sumar importes entre periodos.
- Nunca añadir a Claude como coautor (`Co-Authored-By`) ni ninguna atribución de Claude en commits o PRs.
- Antes de cada push: revisar secretos, correos/teléfonos y datos personales en lo versionado (el contacto del
  User-Agent va en `MUNILENS_CONTACTO`, no en el código). El usuario autorizó hacer push tras esa revisión.
- Remoto: `origin` → https://github.com/josefrodrim/Transparencia360.git, rama `main`.
