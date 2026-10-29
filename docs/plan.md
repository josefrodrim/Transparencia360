# Plan de trabajo MuniLens

Leyenda: [x] hecho · [ ] pendiente

## Fase 1 — Fuentes (Huancavelica)
- [x] Inspeccionar el PTE de la MPH: formatos, campos, robots.txt y acceso (`docs/fuentes-huancavelica.md`)
- [x] Directorio oficial de municipalidades y ubigeos (INEI) → `database/seeds/municipalidades.csv` (102 en Huancavelica)
- [ ] `id_entidad` PTE de las municipalidades del departamento y disponibilidad de datos de cada una
- [ ] Evaluar los periodos 2013–2023 de la MPH
- [ ] Revisar las condiciones de uso de transparencia.gob.pe y Datos Abiertos

## Fase 2 — Scraper piloto (MPH)
- [x] Extractor del CSV del PTE con RAW + hash + manifiesto + detección de cambios
- [x] Normalización, validación y reporte de calidad; duplicados marcados
- [x] Pruebas unitarias e integración CSV frente a HTML
- [x] Primer dataset 2024-01 → 2026-10 (local en `data/`)
- [ ] Revisión manual del reporte de calidad (2024-04 incompleto, meses idénticos) y validación del piloto
- [ ] CI (GitHub Actions): ruff + pytest

## Fases 3 a 9
Según el documento de requisitos: PostgreSQL/Alembic → FastAPI → Next.js MVP → escalamiento departamental →
formación académica (solo por vía legítima) → analítica → publicación (con revisión legal previa).
