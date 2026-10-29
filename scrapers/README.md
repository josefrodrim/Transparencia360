# munilens-scrapers

Extractores de fuentes públicas para MuniLens. Por ahora: Portal de Transparencia Estándar (PTE), rubro Personal.

## Uso

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e "scrapers[dev]"   # desde la raíz del repo
.venv/bin/munilens-extract --entidad mp-huancavelica --desde 2024-01 --hasta 2026-10
```

Salidas (en `data/`, fuera de git):

- `raw/pte_personal/<entidad>/<AAAA-MM>/<sha16>.csv`: documento original, inmutable.
- `raw/pte_personal/<entidad>/manifest.jsonl`: cada intento de extracción, con URL, fecha, SHA-256, huella y estado
  (`nuevo`, `cambiado`, `sin_cambios`, `sin_datos` o `error`).
- `processed/pte_personal/<entidad>/<AAAA-MM>.csv`: registros normalizados con trazabilidad (URL, hash y fecha) y
  la columna `duplicado_de`.
- `processed/.../<AAAA-MM>.calidad.json`: hallazgos y estadísticas del periodo.
- `reports/pte_personal_<entidad>_<desde>_<hasta>.md`: resumen del rango.

Las entidades se configuran en `config/entidades.toml`. Define `MUNILENS_CONTACTO` (ver `.env.example`) para incluir un contacto en el User-Agent.

## Pruebas

```bash
cd scrapers
../.venv/bin/pytest                          # unitarias (fixtures sintéticos)
../.venv/bin/pytest tests/test_pte_personal.py::test_leer_y_normalizar   # una prueba
MUNILENS_RED=1 ../.venv/bin/pytest -m red    # integración contra el portal real: CSV frente a tabla HTML
../.venv/bin/ruff check . && ../.venv/bin/ruff format --check .
```
