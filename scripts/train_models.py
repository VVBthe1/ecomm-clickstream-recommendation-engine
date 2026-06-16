#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir
from src.training import best_model_by_mae, evaluate_all_models, time_based_split


def main() -> None:
    cfg = load_config()
    training = cfg["training"]
    gold_dir = resolve_path(cfg["paths"]["gold_dir"])
    metadata_dir = resolve_path(cfg["paths"]["metadata_dir"])
    figures_dir = ensure_dir(resolve_path(cfg["paths"]["figures_dir"]))
    models_dir = ensure_dir(resolve_path(training["models_dir"]))

    gold_path = gold_dir / training["gold_file"]
    df = pd.read_parquet(gold_path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.dropna(subset=[training["target"]])

    split = time_based_split(
        df,
        train_days=int(training["train_days"]),
        test_days=int(training["test_days"]),
    )

    feature_columns = list(training["feature_columns"])
    target = training["target"]

    metrics, fitted = evaluate_all_models(
        split.train,
        split.test,
        feature_columns,
        target,
    )

    results = {
        "split": {
            "train_dates": split.train_dates,
            "test_dates": split.test_dates,
            "train_rows": len(split.train),
            "test_rows": len(split.test),
        },
        "models": metrics,
        "best_by_mae": best_model_by_mae(metrics),
    }

    results_path = resolve_path(training["results_file"])
    ensure_dir(results_path.parent)
    with results_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    for name, model in fitted.items():
        joblib.dump(model, models_dir / f"{name}.joblib")

    shap_cfg = training.get("shap", {})
    if shap_cfg.get("enabled", False):
        _maybe_shap(
            fitted,
            split.test,
            feature_columns,
            shap_cfg,
            figures_dir,
        )

    append_run_log(
        metadata_dir,
        "train_models",
        {
            "results_file": str(results_path),
            "best_by_mae": results["best_by_mae"],
            "models_dir": str(models_dir),
        },
    )
    print(results_path)


def _maybe_shap(
    fitted: dict,
    test: pd.DataFrame,
    feature_columns: list[str],
    shap_cfg: dict,
    figures_dir: Path,
) -> None:
    try:
        import shap
    except ImportError:
        return

    model_key = shap_cfg.get("model", "xgboost")
    model = fitted.get(model_key)
    if model is None or not hasattr(model, "predict"):
        return

    sample_n = int(shap_cfg.get("sample_rows", 5000))
    x_test = test[feature_columns]
    if len(x_test) > sample_n:
        x_test = x_test.sample(n=sample_n, random_state=42)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(x_test)

    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, x_test, show=False)
    out = figures_dir / "shap_summary.png"
    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
