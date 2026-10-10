# Pronóstico de demanda de taxis en Chicago

Proyecto final de Grandes Datos (Universidad Panamericana). Pipeline medallion en Google Cloud que procesa 212 millones de viajes de taxi de Chicago (2013–2023), entrena dos modelos de pronóstico de demanda por zona y hora, y los publica en una app de Streamlit con tablero directivo.

**App en línea:** https://taxis-app-521071336581.us-central1.run.app

## Pregunta de negocio

¿Cuántos viajes de taxi se van a pedir en cada zona de Chicago, a cada hora, para colocar la flota donde va a estar la demanda?

## Arquitectura

```
BigQuery (fuentes públicas)
   │  bq extract (Parquet, Snappy)
   ▼
Cloud Storage ── procesado con PySpark en Dataproc ─────────────────────────
   bronze/   copia cruda          212,046,737 filas   10.81 GiB
   silver/   limpio, particionado 142,333,309 viajes   7.69 GiB
   gold/     zona × fecha × hora    7,371,672 filas   39.63 MiB
   models/   Poisson y XGBoost en JSON
   │  6 CSV y 2 JSON
   ▼
GitHub (app/) ── Cloud Build ── Cloud Run (Streamlit, sin clúster)
```

| Pieza | Para qué |
| --- | --- |
| BigQuery | Fuente: `chicago_taxi_trips.taxi_trips` (77.1 GB) y `noaa_gsod.gsod2013`–`gsod2023` |
| Cloud Storage + Parquet | Capas bronze, silver y gold; lectura columnar y por partición |
| Dataproc 2.1 (Spark 3.3.2) | Limpieza, agregación y modelos; 1 maestro e2-highmem-2 y 3 workers e2-standard-2 |
| Streamlit + Cloud Run | Tablero y pronóstico; la app lee solo archivos exportados de gold |
| Cloud Build | Despliegue continuo: cada push a `main` publica la app en unos 3 minutos |

## Estructura del repositorio

```
.
├── app/                    App de Streamlit (lo que se despliega en Cloud Run)
│   ├── app.py              Interfaz: Tablero, Pronóstico y Pronóstico por archivo
│   ├── features.py         Variables del modelo (misma lógica que gold)
│   ├── predictor.py        Carga Poisson o XGBoost desde JSON y predice sin Spark
│   ├── dashboard.py        Cálculos del tablero con pandas
│   ├── *.csv, *.json       Seis agregados de gold y los dos modelos exportados
│   ├── Dockerfile
│   └── requirements.txt
├── notebooks/              Pipeline en PySpark, uno por etapa (con sus salidas)
│   ├── 01_bronze.ipynb          Esquema y conteos de bronze
│   ├── 01b_bronze.ipynb         Análisis exploratorio (EDA) que fija las reglas de limpieza
│   ├── 02_silver.ipynb          Limpieza de viajes y clima, reporte de calidad
│   ├── 03_gold.ipynb            Tablas de negocio, variables y exportaciones del tablero
│   ├── 03b_gold_preview.ipynb   Auxiliar: vista previa de las tablas de gold y los CSV
│   ├── 04_model.ipynb           Poisson y XGBoost, comparación y exportación a JSON
│   └── 05_performance.ipynb     Pruebas de rendimiento y escalabilidad
└── scripts/                Comandos de Cloud Shell
    ├── 00_setup_gcp.sh            Bucket y clúster de Dataproc
    ├── 01_ingest_bronze.sh        bq extract de viajes y clima
    ├── 02_upload_xgboost_wheel.sh Instalador de XGBoost para el clúster sin internet
    ├── 03_download_app_files.sh   CSV y modelos de gold a app/
    ├── 04_deploy_cloud_run.sh     Primer despliegue de la app
    └── 05_cleanup.sh              Borrar el clúster al terminar
```

## Cómo reproducirlo

1. **GCP:** en Cloud Shell, `bash scripts/00_setup_gcp.sh` crea el bucket y el clúster.
2. **Bronze:** `bash scripts/01_ingest_bronze.sh` exporta las fuentes de BigQuery a Parquet.
3. **XGBoost:** `bash scripts/02_upload_xgboost_wheel.sh` deja el instalador en el bucket.
4. **Pipeline:** en JupyterLab del clúster (Dataproc → Interfaces web), correr en orden los notebooks `01_bronze` a `05_performance`.
5. **App:** desde `app/`, `bash ../scripts/03_download_app_files.sh` y luego `streamlit run app.py` para probar en local.
6. **Publicación:** `bash scripts/04_deploy_cloud_run.sh` la primera vez; después basta con `git push` a `main`.
7. **Costo:** `bash scripts/05_cleanup.sh` borra el clúster. El clúster también se borra solo tras una hora sin uso.

## Resultados principales

**Datos.** El 20.1% de las filas de la fuente son duplicados exactos y el 12.7% de los viajes no tiene zona de origen. Silver conserva 142,333,309 viajes, el 67.1% de bronze.

**Modelos.** Entrenamiento de enero de 2022 a junio de 2023 (1,009,008 filas) y prueba de julio a diciembre de 2023 (340,032 filas):

| Modelo | MAE | RMSE | R² |
| --- | --- | --- | --- |
| `profile_4w` (línea base) | 2.4502 | 10.0088 | 0.9242 |
| Poisson | 2.4429 | 9.3090 | 0.9345 |
| XGBoost (en la app) | 2.4497 | 9.4937 | 0.9318 |

Los modelos igualan a la línea base en error promedio y reducen entre 5% y 7% los errores grandes (RMSE). Un día festivo reduce la demanda 37.1%.

**Rendimiento.** La limpieza crece de forma lineal hasta 71 millones de filas. Con 3 workers tarda 44% menos que con 2. Filtrar por la partición `year` es entre 5 y 6 veces más rápido que filtrar por fecha.

## Limitaciones

- Los datos llegan al 31 de diciembre de 2023. Para fechas posteriores, la app usa el patrón de las últimas 4 semanas disponibles; el calendario del pronóstico permite de 2024 a 2028.
- Los viajes sin zona de origen (12.7%) quedan fuera del pronóstico.
- El despliegue de la app es automático; los notebooks de datos y modelos se corren a mano.
