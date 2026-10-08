"""Carga el modelo elegido y predice. Poisson solo usa numpy; XGBoost usa su propia librería."""
import json

import numpy as np
import pandas as pd

from features import FEATURES


def load(kind: str):
    if kind == "poisson":
        with open("demand_poisson_v1.json") as f:
            return json.load(f)
    if kind == "xgboost":
        import xgboost as xgb
        booster = xgb.Booster()
        booster.load_model("demand_xgboost_v1.json")
        return booster
    raise ValueError(f"Modelo desconocido: {kind}")


def predict_poisson(model: dict, x: pd.DataFrame) -> np.ndarray:
    """viajes = exp(intercepto + suma de coeficientes). La categoría base de cada variable vale 0."""
    c = model["coefficients"]
    eta = model["intercept"] + sum(
        x[column].map(lambda v, column=column: c.get(f"{column}_{int(v)}", 0.0))
        for column in ["zone", "hour", "day_of_week", "month"])
    eta = eta + sum(c[n] * x[n] for n in ["is_holiday", "temp_c", "prcp_mm", "snow"])
    eta = eta + c["log_profile"] * np.log1p(x["profile_4w"])
    return np.exp(eta).to_numpy()


def predict(kind: str, model, x: pd.DataFrame) -> np.ndarray:
    if kind == "poisson":
        return predict_poisson(model, x)
    import xgboost as xgb
    return model.predict(xgb.DMatrix(x[FEATURES]))
