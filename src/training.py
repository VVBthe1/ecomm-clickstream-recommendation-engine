from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None

try:
    import xgboost as xgb
except ImportError:  # pragma: no cover
    xgb = None


@dataclass
class SplitResult:
    train: pd.DataFrame
    test: pd.DataFrame
    train_dates: list
    test_dates: list


def time_based_split(
    df: pd.DataFrame,
    train_days: int,
    test_days: int,
    date_col: str = "date",
) -> SplitResult:
    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col], utc=True)
    unique_dates = sorted(work[date_col].unique())
    if len(unique_dates) < train_days + test_days:
        raise ValueError(
            f"Need at least {train_days + test_days} dates; got {len(unique_dates)}"
        )
    train_dates = unique_dates[:train_days]
    test_dates = unique_dates[train_days : train_days + test_days]
    train = work[work[date_col].isin(train_dates)].copy()
    test = work[work[date_col].isin(test_dates)].copy()
    return SplitResult(
        train=train,
        test=test,
        train_dates=[str(d) for d in train_dates],
        test_dates=[str(d) for d in test_dates],
    )


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float | None]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred)) if len(y_true) > 1 else None
    mask = y_true != 0
    if mask.any():
        mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)
    else:
        mape = None
    return {"mae": mae, "rmse": rmse, "mape": mape, "r2": r2}


def add_baseline_predictions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["product_id", "date"]).copy()
    g = out.groupby("product_id", group_keys=False)
    # lag(1): predict using yesterday's purchases
    out["pred_lag1"] = g["purchases"].shift(1)
    # lag(1) then 7-day rolling mean: predict using average of prior 7 days
    out["pred_ma7"] = g["purchases"].transform(
        lambda s: s.shift(1).rolling(7, min_periods=1).mean()
    )
    return out


def historical_mean_predictions(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target: str = "purchases",
) -> np.ndarray:
    means = train.groupby("product_id")[target].mean()
    return test["product_id"].map(means).fillna(0).to_numpy()


def predict_baseline(
    train: pd.DataFrame,
    test: pd.DataFrame,
    column: str,
) -> np.ndarray:
    combined = pd.concat([train, test], ignore_index=True)
    combined = combined.sort_values(["product_id", "date"])
    combined = add_baseline_predictions(combined)
    merged = test[["product_id", "date"]].merge(
        combined[["product_id", "date", column]],
        on=["product_id", "date"],
        how="left",
    )
    return merged[column].fillna(0).to_numpy()


def fit_random_forest(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    random_state: int = 42,
) -> RandomForestRegressor:
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=random_state,
    )
    model.fit(x_train, y_train)
    return model


def fit_xgboost(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    random_state: int = 42,
) -> Any:
    if xgb is None:
        raise ImportError("xgboost is not installed")
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        n_jobs=-1,
        random_state=random_state,
    )
    model.fit(x_train, y_train)
    return model


def fit_lightgbm(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    random_state: int = 42,
) -> Any:
    if lgb is None:
        raise ImportError("lightgbm is not installed")
    model = lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=random_state,
        verbose=-1,
    )
    model.fit(x_train, y_train)
    return model


def evaluate_all_models(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
    target: str,
) -> tuple[dict[str, dict[str, float | None]], dict[str, Any]]:
    train = train.dropna(subset=[target])
    test = test.dropna(subset=[target])
    x_train = train[feature_columns]
    y_train = train[target]
    x_test = test[feature_columns]
    y_test = test[target].to_numpy()

    metrics: dict[str, dict[str, float | None]] = {}
    fitted: dict[str, Any] = {}

    for name, col in [("lag1", "pred_lag1"), ("ma7", "pred_ma7")]:
        preds = predict_baseline(train, test, col)
        metrics[name] = compute_metrics(y_test, preds)
        fitted[name] = {"type": "baseline", "column": col}

    hist_preds = historical_mean_predictions(train, test)
    metrics["hist_mean"] = compute_metrics(y_test, hist_preds)
    fitted["hist_mean"] = {
        "type": "baseline",
        "product_means": train.groupby("product_id")["purchases"].mean().to_dict(),
    }

    rf = fit_random_forest(x_train, y_train)
    metrics["random_forest"] = compute_metrics(y_test, rf.predict(x_test))
    fitted["random_forest"] = rf

    xgb_model = fit_xgboost(x_train, y_train)
    metrics["xgboost"] = compute_metrics(y_test, xgb_model.predict(x_test))
    fitted["xgboost"] = xgb_model

    lgb_model = fit_lightgbm(x_train, y_train)
    metrics["lightgbm"] = compute_metrics(y_test, lgb_model.predict(x_test))
    fitted["lightgbm"] = lgb_model

    return metrics, fitted


def best_model_by_mae(metrics: dict[str, dict[str, float | None]]) -> str:
    ranked = sorted(
        metrics.items(),
        key=lambda item: item[1]["mae"] if item[1]["mae"] is not None else float("inf"),
    )
    return ranked[0][0]
