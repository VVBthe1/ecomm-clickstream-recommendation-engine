#!/usr/bin/env python3
"""Modest hyperparameter search on E_final training window only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir
from src.training import date_boundary_split

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None

try:
    import xgboost as xgb
except ImportError:  # pragma: no cover
    xgb = None


RF_PARAMS = {
    "n_estimators": [100, 200, 300],
    "max_depth": [8, 10, 12, 15, None],
    "min_samples_leaf": [2, 5, 10],
    "max_features": ["sqrt", "log2", 0.5],
}

XGB_PARAMS = {
    "n_estimators": [100, 200, 300],
    "learning_rate": [0.05, 0.1, 0.2],
    "max_depth": [4, 6, 8],
    "subsample": [0.7, 0.8, 1.0],
    "colsample_bytree": [0.7, 0.8, 1.0],
}

LGBM_PARAMS = {
    "n_estimators": [100, 200, 300],
    "learning_rate": [0.05, 0.1, 0.2],
    "num_leaves": [31, 63, 127],
    "subsample": [0.7, 0.8, 1.0],
    "min_child_samples": [10, 20, 50],
}


def _json_default(obj):
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if obj is None:
        return None
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(type(obj))


def main() -> None:
    cfg = load_config()
    training = cfg["training"]
    tune_cfg = training.get("tune", {})
    n_iter = int(tune_cfg.get("n_iter", 12))
    cv_splits = int(tune_cfg.get("cv_splits", 3))
    metadata_dir = resolve_path(cfg["paths"]["metadata_dir"])
    gold_path = resolve_path(cfg["paths"]["gold_dir"]) / training["gold_file"]

    df = pd.read_parquet(gold_path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.dropna(subset=[training["target"]])

    ef_cfg = training["experiment_final"]
    split = date_boundary_split(
        df,
        train_end=ef_cfg["train_end"],
        test_start=ef_cfg["test_start"],
        test_days=int(ef_cfg["test_days"]),
    )
    train = split.train.sort_values("date").reset_index(drop=True)
    features = list(training["feature_columns"])
    target = training["target"]
    x = train[features]
    y = train[target]

    cv = TimeSeriesSplit(n_splits=cv_splits)
    flat_params: dict = {}
    cv_meta: dict = {}

    print(f"Tuning on E_final train ({len(train):,} rows), n_iter={n_iter}")

    rf = RandomForestRegressor(n_jobs=-1, random_state=42)
    params, mae = _search(rf, RF_PARAMS, x, y, cv, n_iter, "random_forest")
    flat_params["random_forest"] = params
    cv_meta["random_forest"] = {"best_cv_mae": mae, "best_params": params}

    if xgb is not None:
        model = xgb.XGBRegressor(
            objective="reg:squarederror", n_jobs=-1, random_state=42
        )
        params, mae = _search(model, XGB_PARAMS, x, y, cv, n_iter, "xgboost")
        flat_params["xgboost"] = params
        cv_meta["xgboost"] = {"best_cv_mae": mae, "best_params": params}

    if lgb is not None:
        model = lgb.LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1)
        params, mae = _search(model, LGBM_PARAMS, x, y, cv, n_iter, "lightgbm")
        flat_params["lightgbm"] = params
        cv_meta["lightgbm"] = {"best_cv_mae": mae, "best_params": params}

    out_path = resolve_path(tune_cfg.get("results_file", "metadata/best_params.json"))
    ensure_dir(out_path.parent)
    # Flat dict for train_models --use-tuned
    out_path.write_text(json.dumps(flat_params, indent=2, default=_json_default))
    (metadata_dir / "best_params_cv.json").write_text(
        json.dumps(cv_meta, indent=2, default=_json_default)
    )
    append_run_log(
        metadata_dir,
        "tune_models",
        {"path": str(out_path), "n_iter": n_iter, "train_rows": len(train)},
    )
    print(f"Saved {out_path}")


def _search(model, param_dist, x, y, cv, n_iter, name: str) -> tuple[dict, float]:
    print(f"  Searching {name}...")
    search = RandomizedSearchCV(
        model,
        param_distributions=param_dist,
        n_iter=n_iter,
        cv=cv,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
        random_state=42,
        verbose=1,
    )
    search.fit(x, y)
    mae = float(-search.best_score_)
    print(f"  {name} best CV MAE={mae:.4f} params={search.best_params_}")
    return dict(search.best_params_), mae


if __name__ == "__main__":
    main()
