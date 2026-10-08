"""Cálculos del tablero. Solo pandas, para poder probarlos sin abrir la app."""
import pandas as pd

DAYS = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]   # day_of_week 1 a 7, como en Spark


def kpis(daily: pd.DataFrame, year: int) -> dict:
    d = daily[daily["date"].dt.year == year]
    trips, revenue = d["trips"].sum(), d["revenue"].sum()
    return {"trips": trips, "revenue": revenue,
            "revenue_per_trip": revenue / trips if trips else 0.0}


def monthly_series(daily: pd.DataFrame) -> pd.Series:
    return daily.set_index("date")["trips"].resample("MS").sum()


def top_zones(zone_hour: pd.DataFrame, year: int, n: int = 10) -> pd.Series:
    z = zone_hour[zone_hour["year"] == year]
    return z.groupby("zone_name")["trips"].sum().nlargest(n)


def heatmap(zone_hour: pd.DataFrame, year: int, zone_name=None) -> pd.DataFrame:
    z = zone_hour[zone_hour["year"] == year]
    if zone_name:
        z = z[z["zone_name"] == zone_name]
    m = z.groupby(["day_of_week", "hour"], as_index=False)["trips"].sum()
    m["day"] = m["day_of_week"].map(lambda d: DAYS[d - 1])
    return m


def company_share(companies: pd.DataFrame, year: int, n: int = 8) -> pd.Series:
    c = companies[companies["year"] == year].groupby("company")["trips"].sum()
    return (c / c.sum() * 100).nlargest(n).round(1)


def weather_effect(daily: pd.DataFrame, year: int) -> pd.Series:
    d = daily[daily["date"].dt.year == year].copy()
    d["condition"] = "Seco"
    d.loc[d["prcp_mm"] > 0, "condition"] = "Lluvia"
    d.loc[d["snow"] == 1, "condition"] = "Nieve"
    return d.groupby("condition")["trips"].mean().round(0)
