import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

TARGET = "rented_bike_count"

# Features signed off in the feature inventory (Step 3).
WEATHER = ["temperature", "humidity", "wind_speed", "rainfall", "snowfall"]
SIGNED_OFF = ["hour", "month", "weekday", "holiday_flag"] + WEATHER

# Columns that a linear model must read as categories, not as quantities.
CATEGORY_COLUMNS = ["hour", "month", "weekday"]


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with holiday_flag (1 on a holiday, else 0)."""
    out = df.copy()
    out["holiday_flag"] = out["holiday"].ne("No Holiday").astype(int)
    out["is_weekend"] = out["is_weekend"].astype(int)
    return out


def score(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    """Four numbers for one set of predictions. Residual = predicted minus actual."""
    residual = np.asarray(y_pred) - np.asarray(y_true)
    sse = (residual ** 2).sum()
    sst = ((y_true - y_true.mean()) ** 2).sum()
    return {
        "mae": np.abs(residual).mean(),
        "rmse": np.sqrt((residual ** 2).mean()),
        "r2": 1 - sse / sst,
        "mean_error": residual.mean(),
    }


def group_mean_baseline(train: pd.DataFrame, test: pd.DataFrame, keys: list) -> np.ndarray:
    """Predict the training mean of each group. An empty key list gives one overall mean."""
    if not keys:
        return np.full(len(test), train[TARGET].mean())
    table = train.groupby(keys)[TARGET].mean().rename("prediction").reset_index()
    merged = test[keys].merge(table, on=keys, how="left")
    return merged["prediction"].fillna(train[TARGET].mean()).to_numpy()


def build_models(features: list) -> dict:
    """Three models, each ready to fit on a frame holding the given features."""
    categories = [c for c in CATEGORY_COLUMNS if c in features]
    linear = Pipeline([
        ("prepare", ColumnTransformer(
            [("categories", OneHotEncoder(handle_unknown="ignore"), categories)],
            remainder="passthrough",
        )),
        ("model", LinearRegression()),
    ])
    forest = RandomForestRegressor(
        n_estimators=300, min_samples_leaf=5, random_state=42, n_jobs=-1
    )
    boosting = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.05, random_state=42
    )
    return {
        "Linear regression": linear,
        "Random forest": forest,
        "Gradient boosting": boosting,
    }


def fit_and_score(model, train: pd.DataFrame, test: pd.DataFrame, features: list):
    """Fit on train, predict test. Return the scores and the predictions."""
    model.fit(train[features], train[TARGET])
    predictions = model.predict(test[features])
    return score(test[TARGET], predictions), predictions


def error_by(test: pd.DataFrame, predictions: np.ndarray, column: str) -> pd.DataFrame:
    """Rows, MAE, RMSE and mean error for each value of one column."""
    frame = test[[column, TARGET]].copy()
    frame["residual"] = predictions - frame[TARGET]
    frame["abs_error"] = frame["residual"].abs()
    frame["sq_error"] = frame["residual"] ** 2
    grouped = frame.groupby(column)
    return pd.DataFrame({
        "rows": grouped.size(),
        "mae": grouped["abs_error"].mean(),
        "rmse": np.sqrt(grouped["sq_error"].mean()),
        "mean_error": grouped["residual"].mean(),
    })