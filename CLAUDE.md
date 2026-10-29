# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

MuniLens: plataforma de transparencia sobre el personal municipal del Perú, empezando por Huancavelica. El plan por
fases (1. fuentes → 2. scraper piloto → 3. PostgreSQL → 4. FastAPI → 5. Next.js → ...) está en `docs/plan.md`.
Estado actual: Fases 1 y 2 en curso. Existen `scrapers/` y `database/seeds/`; aún no hay backend ni frontend.

## Comandos

Entorno: `.venv` en la raíz (Python 3.12). Paquete instalado en modo editable: `.venv/bin/pip install -e "scrapers[dev]"`.

```bash
.venv/bin/munilens-extract --entidad mp-huancavelica --desde 2024-01 --hasta 2026-10   # desde la raíz → data/
.venv/bin/munilens-inei --url <xlsx del directorio INEI>   # → database/seeds/municipalidades.csv (+ .meta.json)
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

Particularidades del PTE: ver `docs/fuentes-huancavelica.md` (periodos vacíos = respuesta de 0 bytes, cargas
duplicadas, meses idénticos, desfase de publicación).

## Reglas del proyecto

- No inventar datos ni declarar que una fuente funciona sin comprobarla. Documentar cada fuente en `docs/`.
- No evadir CAPTCHA ni controles de acceso, y no hacer consultas masivas sin autorización. SUNEDU no se automatiza
  sin verificar antes que esté permitido.
- `data/` contiene datos personales reales y está en `.gitignore`. Los fixtures de pruebas son sintéticos.
- No eliminar registros de la fuente: marcarlos (p. ej. `duplicado_de`). Mismo nombre ≠ misma persona.
  No anualizar ni sumar importes entre periodos.
- Nunca añadir a Claude como coautor (`Co-Authored-By`) ni ninguna atribución de Claude en commits o PRs.
- Remoto: `origin` → https://github.com/josefrodrim/Transparencia360.git, rama `main`.
