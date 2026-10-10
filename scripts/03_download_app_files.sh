#!/usr/bin/env bash
# Descarga a app/ los seis CSV que exporta gold y los dos modelos en JSON.
# Correr desde la carpeta app/ (en Cloud Shell o en una máquina con gsutil).
set -euo pipefail

BUCKET_NAME=taxis-chicago-grandes-datos-506301

for name in recent_profile dim_zones dashboard_daily dashboard_zone_hour dashboard_companies model_metrics; do
  gsutil cp "gs://$BUCKET_NAME/gold/app_export/$name/part-*.csv" "$name.csv"
done
gsutil cp "gs://$BUCKET_NAME/models/demand_*_v1.json" .
ls -lh
