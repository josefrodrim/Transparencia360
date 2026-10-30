#!/usr/bin/env bash
# Extrae PTE Personal (todos los meses del rango) para cada ubigeo de una lista. Reanudable: si se corta,
# volver a ejecutarlo omite los periodos ya registrados en el manifiesto.
#   scripts/sondeo_exhaustivo.sh data/exhaustivo_ubigeos.txt 2024-01 2026-10
set -u
lista=${1:?lista de ubigeos}; desde=${2:-2024-01}; hasta=${3:-2026-10}
cd "$(dirname "$0")/.."
mkdir -p data/logs
total=$(grep -c . "$lista"); i=0
while read -r u; do
  [ -z "$u" ] && continue
  i=$((i + 1))
  .venv/bin/munilens-extract --ubigeo "$u" --desde "$desde" --hasta "$hasta" --reanudar 2>> "data/logs/extract_$u.log"
  rc=$?
  echo "$(date '+%F %T') $i/$total $u exit=$rc" | tee -a data/logs/exhaustivo.progress
done < "$lista"
