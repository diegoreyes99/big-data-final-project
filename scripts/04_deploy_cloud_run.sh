#!/usr/bin/env bash
# Primer despliegue manual de la app en Cloud Run. Correr desde la carpeta app/ en Cloud Shell.
# Después de este paso, cada push a la rama main lo publica Cloud Build de forma automática.
set -euo pipefail

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

gcloud run deploy taxis-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --max-instances 1 \
  --session-affinity

# Registros de la app si algo falla:
#   gcloud run services logs read taxis-app --region us-central1 --limit 50
