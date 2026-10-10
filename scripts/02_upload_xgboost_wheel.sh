#!/usr/bin/env bash
# El clúster no tiene salida a internet (--no-address), así que XGBoost se descarga
# una sola vez en Cloud Shell y se deja en el bucket. El notebook 04_model lo instala desde ahí.
set -euo pipefail

BUCKET_NAME=taxis-chicago-grandes-datos-506301

pip download xgboost-cpu==2.1.4 --no-deps --only-binary=:all: \
  --python-version 3.10 --platform manylinux2014_x86_64 --platform manylinux_2_28_x86_64 \
  -d xgb_wheel
gsutil cp xgb_wheel/*.whl "gs://$BUCKET_NAME/libs/"
