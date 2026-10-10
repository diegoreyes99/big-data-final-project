#!/usr/bin/env bash
# Ingesta a bronze: exporta las fuentes públicas de BigQuery a Parquet, sin filtros.
# No necesita el clúster. Correr en Cloud Shell.
# Si se repite, borrar antes la carpeta de destino para no duplicar filas:
#   gsutil -m rm -r gs://$BUCKET_NAME/bronze/taxi_trips
set -euo pipefail

BUCKET_NAME=taxis-chicago-grandes-datos-506301

# Viajes de taxi de Chicago (212,046,737 filas, 77.1 GB en BigQuery)
bq extract --destination_format=PARQUET --compression=SNAPPY \
  'bigquery-public-data:chicago_taxi_trips.taxi_trips' \
  "gs://$BUCKET_NAME/bronze/taxi_trips/part-*.parquet"

# Clima diario NOAA GSOD, una tabla por año de 2013 a 2023 (todas las estaciones)
for year in $(seq 2013 2023); do
  bq extract --destination_format=PARQUET --compression=SNAPPY \
    "bigquery-public-data:noaa_gsod.gsod$year" \
    "gs://$BUCKET_NAME/bronze/weather/gsod$year-*.parquet"
done

# Verificación de tamaños
gsutil du -sh "gs://$BUCKET_NAME/bronze/taxi_trips" "gs://$BUCKET_NAME/bronze/weather"
