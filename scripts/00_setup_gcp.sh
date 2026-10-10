#!/usr/bin/env bash
# Crea el bucket y el clúster de Dataproc. Correr en Cloud Shell.
set -euo pipefail

PROJECT_ID=grandes-datos-506301
REGION=us-central1
ZONE=us-central1-a
BUCKET_NAME=taxis-chicago-grandes-datos-506301
CLUSTER_NAME=taxis-cluster

# Bucket para bronze, silver, gold, modelos y notebooks (solo la primera vez)
gsutil mb -l "$REGION" "gs://$BUCKET_NAME" || echo "El bucket ya existe"

# Clúster de Dataproc: configuración de la sección B del README de MLOPS
gcloud dataproc clusters create "$CLUSTER_NAME" \
    --project="$PROJECT_ID" --region="$REGION" --zone="$ZONE" \
    --image-version=2.1-ubuntu20 \
    --master-machine-type=e2-highmem-2 --master-boot-disk-size 50 \
    --num-workers=3 --worker-machine-type=e2-standard-2 --worker-boot-disk-size 100 \
    --no-address \
    --optional-components JUPYTER \
    --enable-component-gateway \
    --max-idle=1h \
    --scopes 'https://www.googleapis.com/auth/cloud-platform' \
    --properties="dataproc:jupyter.notebook.gcs.dir=gs://$BUCKET_NAME/notebooks"
