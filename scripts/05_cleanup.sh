#!/usr/bin/env bash
# Borra el clúster al terminar cada sesión de trabajo. El bucket y la app se conservan.
set -euo pipefail

gcloud dataproc clusters delete taxis-cluster --region=us-central1 --quiet
gcloud dataproc clusters list --region=us-central1   # debe responder: Listed 0 items.

# Al terminar el curso, para borrar también la app:
#   gcloud run services delete taxis-app --region us-central1
