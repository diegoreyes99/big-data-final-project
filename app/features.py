"""Variables del modelo. La misma lógica que el notebook 03_gold."""
import datetime as dt
import pandas as pd

FEATURES = ["zone", "hour", "day_of_week", "month", "is_weekend", "is_holiday",
            "temp_c", "prcp_mm", "snow", "profile_4w"]


def day_of_week(date: dt.date) -> int:
    """Igual que dayofweek de Spark: 1 = domingo ... 7 = sábado."""
    return date.isoweekday() % 7 + 1


def is_holiday(date: dt.date) -> int:
    m, d, dow = date.month, date.day, day_of_week(date)
    fixed = (m, d) in {(1, 1), (7, 4), (12, 25)}
    memorial = m == 5 and dow == 2 and d >= 25
    labor = m == 9 and dow == 2 and d <= 7
    thanksgiving = m == 11 and dow == 5 and 22 <= d <= 28
    return int(fixed or memorial or labor or thanksgiving)


def build(date: dt.date, hour: int, temp_c: float, prcp_mm: float, snow: int,
          profile: pd.DataFrame) -> pd.DataFrame:
    """Una fila por zona con las variables que espera el modelo."""
    dow = day_of_week(date)
    x = profile[(profile["day_of_week"] == dow) & (profile["hour"] == hour)].copy()
    x["month"] = date.month
    x["is_weekend"] = int(dow in (1, 7))
    x["is_holiday"] = is_holiday(date)
    x["temp_c"], x["prcp_mm"], x["snow"] = temp_c, prcp_mm, int(snow)
    return x[FEATURES].reset_index(drop=True)
