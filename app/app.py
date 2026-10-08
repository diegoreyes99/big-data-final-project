import datetime as dt

import altair as alt
import pandas as pd
import streamlit as st

import dashboard
import predictor
from features import build

MODEL_KIND = "xgboost"   # el modelo que ganó la comparación del notebook 04: "xgboost" o "poisson"

st.set_page_config(page_title="Taxis de Chicago", layout="wide")


@st.cache_resource
def load_model():
    return (predictor.load(MODEL_KIND),
            pd.read_csv("recent_profile.csv"),
            pd.read_csv("dim_zones.csv"))


@st.cache_data
def load_dashboard():
    return (pd.read_csv("dashboard_daily.csv", parse_dates=["date"]),
            pd.read_csv("dashboard_zone_hour.csv"),
            pd.read_csv("dashboard_companies.csv"),
            pd.read_csv("model_metrics.csv"))


model, profile, zones = load_model()
daily, zone_hour, companies, model_metrics = load_dashboard()


def predict(date, hour, temp_c, prcp_mm, snow):
    x = build(date, hour, temp_c, prcp_mm, snow, profile)
    out = x[["zone"]].merge(zones, on="zone", how="left")
    out["expected_trips"] = predictor.predict(MODEL_KIND, model, x).round(1)
    out["radius_m"] = 150 + out["expected_trips"] * 10   # tamaño del punto en el mapa
    return out.sort_values("expected_trips", ascending=False)


st.title("Taxis de Chicago demanda por zona y hora")
tab_dashboard, tab_single, tab_batch = st.tabs(["Tablero", "Pronóstico", "Pronóstico por archivo"])

with tab_dashboard:
    year = st.selectbox("Año", sorted(zone_hour["year"].unique(), reverse=True))
    k = dashboard.kpis(daily, year)
    a, b, c = st.columns(3)
    a.metric("Viajes", f"{k['trips']:,.0f}")
    b.metric("Ingreso (USD)", f"{k['revenue']:,.0f}")
    c.metric("Ingreso por viaje (USD)", f"{k['revenue_per_trip']:.2f}")

    st.subheader("Viajes por mes, todo el periodo")
    st.line_chart(dashboard.monthly_series(daily))

    left, right = st.columns(2)
    left.subheader(f"Zonas con más viajes en {year}")
    left.bar_chart(dashboard.top_zones(zone_hour, year))
    right.subheader(f"Participación por empresa en {year} (%)")
    right.bar_chart(dashboard.company_share(companies, year))

    st.subheader("Cuándo hay demanda: día de la semana por hora")
    zone_name = st.selectbox("Zona", ["Toda la ciudad"] + sorted(zone_hour["zone_name"].unique()))
    heat = dashboard.heatmap(zone_hour, year, None if zone_name == "Toda la ciudad" else zone_name)
    st.altair_chart(alt.Chart(heat).mark_rect().encode(
        x=alt.X("hour:O", title="Hora"),
        y=alt.Y("day:O", sort=dashboard.DAYS, title=None),
        color=alt.Color("trips:Q", title="Viajes"),
        tooltip=["day", "hour", "trips"]))

    st.subheader(f"Viajes promedio por día según el clima en {year}")
    st.bar_chart(dashboard.weather_effect(daily, year))

    st.subheader("Qué tan bien pronostica cada modelo (julio a diciembre de 2023)")
    st.dataframe(model_metrics, hide_index=True)
    st.caption(f"La pestaña de pronóstico usa el modelo: {MODEL_KIND}. MAE = error promedio en viajes por zona y hora.")

with tab_single:
    c1, c2, c3, c4, c5 = st.columns(5)
    date = c1.date_input("Fecha", dt.date.today() + dt.timedelta(days=1),
                         min_value=dt.date(2024, 1, 1), max_value=dt.date(2028, 12, 31))
    hour = c2.slider("Hora", 0, 23, 18)
    temp_c = c3.number_input("Temperatura (°C)", -30.0, 45.0, 10.0)
    prcp_mm = c4.number_input("Lluvia (mm)", 0.0, 150.0, 0.0)
    snow = c5.checkbox("Nieve")

    result = predict(date, hour, temp_c, prcp_mm, snow)
    st.metric("Viajes esperados en la ciudad en esa hora", f"{result['expected_trips'].sum():,.0f}")
    left, right = st.columns(2)
    left.subheader("Zonas con más demanda")
    left.bar_chart(result.head(10).set_index("zone_name")["expected_trips"])
    right.subheader("Mapa")
    right.map(result.dropna(subset=["lat", "lon"]), latitude="lat", longitude="lon", size="radius_m")
    st.dataframe(result[["zone", "zone_name", "expected_trips"]], hide_index=True)

with tab_batch:
    st.write("Sube un CSV con las columnas: date, hour, temp_c, prcp_mm, snow")
    uploaded = st.file_uploader("Escenarios", type="csv")
    if uploaded:
        scenarios = pd.read_csv(uploaded, parse_dates=["date"])
        parts = []
        for s in scenarios.itertuples():
            p = predict(s.date.date(), int(s.hour), float(s.temp_c), float(s.prcp_mm), int(s.snow))
            p.insert(0, "hour", s.hour)
            p.insert(0, "date", s.date.date())
            parts.append(p)
        everything = pd.concat(parts)
        st.dataframe(everything, hide_index=True)
        st.download_button("Descargar predicciones", everything.to_csv(index=False), "predictions.csv")
