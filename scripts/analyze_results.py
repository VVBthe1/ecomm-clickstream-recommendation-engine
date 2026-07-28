#!/usr/bin/env python3
"""Error analysis plots for the best E_final model + temporal vs random figure."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir
from src.training import date_boundary_split, predict_baseline, historical_mean_predictions


def main() -> None:
    cfg = load_config()
    training = cfg["training"]
    figures_dir = ensure_dir(resolve_path(cfg["paths"]["figures_dir"]))
    metadata_dir = resolve_path(cfg["paths"]["metadata_dir"])
    models_dir = resolve_path(training["models_dir"])
    gold_path = resolve_path(cfg["paths"]["gold_dir"]) / training["gold_file"]

    df = pd.read_parquet(gold_path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.dropna(subset=[training["target"]])

    ef_cfg = training["experiment_final"]
    try:
        split = date_boundary_split(
            df,
            train_end=ef_cfg["train_end"],
            test_start=ef_cfg["test_start"],
            test_days=int(ef_cfg["test_days"]),
        )
        split_label = "e_final"
    except ValueError as exc:
        print(f"E_final unavailable ({exc}); analyzing E1 holdout instead")
        from src.training import time_based_split

        split = time_based_split(
            df,
            train_days=int(training["train_days"]),
            test_days=int(training["test_days"]),
        )
        split_label = "e1"
    features = list(training["feature_columns"])
    target = training["target"]
    test = split.test.dropna(subset=[target]).copy()
    y_true = test[target].to_numpy(dtype=float)

    info_path = metadata_dir / "best_model_info.json"
    model_path = models_dir / "best_model.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Missing {model_path}; run make train first")

    best = joblib.load(model_path)
    if info_path.exists():
        info = json.loads(info_path.read_text())
        model_name = info.get("model_name", "best")
    else:
        info = {}
        model_name = "best"

    if hasattr(best, "predict"):
        y_pred = np.asarray(best.predict(test[features]), dtype=float)
    elif isinstance(best, dict) and best.get("type") == "baseline":
        col = best.get("column", "pred_lag1")
        y_pred = predict_baseline(split.train, test, col)
    else:
        y_pred = historical_mean_predictions(split.train, test)

    _plot_pred_vs_actual(y_true, y_pred, model_name, figures_dir)
    _plot_residuals(y_true, y_pred, model_name, figures_dir)
    _plot_error_by_activity(test, y_true, y_pred, model_name, figures_dir)
    _plot_experiment_comparison(metadata_dir, figures_dir)
    _plot_temporal_vs_random(figures_dir)

    residuals = y_true - y_pred
    summary = {
        "model_name": model_name,
        "split": split_label,
        "n_test": int(len(y_true)),
        "mae": float(np.mean(np.abs(residuals))),
        "rmse": float(np.sqrt(np.mean(residuals**2))),
        "mean_residual": float(np.mean(residuals)),
        "best_model_info": info,
        "figures": [
            "pred_vs_actual_best.png",
            "residuals_best.png",
            "error_by_activity_best.png",
            "experiment_comparison.png",
            "temporal_vs_random_split.png",
        ],
    }
    out = metadata_dir / "analysis_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    append_run_log(metadata_dir, "analyze_results", {"path": str(out)})
    print(out)


def _plot_pred_vs_actual(y_true, y_pred, name, figures_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(y_true, y_pred, alpha=0.15, s=8, c="#2c5aa0")
    lim = max(y_true.max(), y_pred.max(), 1)
    ax.plot([0, lim], [0, lim], "k--", lw=1, label="Perfect")
    ax.set_xlabel("Actual purchases_next_day")
    ax.set_ylabel("Predicted")
    ax.set_title(f"Predicted vs actual — {name}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "pred_vs_actual_best.png", dpi=120)
    plt.close(fig)


def _plot_residuals(y_true, y_pred, name, figures_dir: Path) -> None:
    residuals = y_true - y_pred
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(residuals, bins=80, color="#4a7c59", edgecolor="white")
    ax.axvline(0, color="black", ls="--", lw=1)
    ax.set_xlabel("Residual (actual − predicted)")
    ax.set_ylabel("Count")
    ax.set_title(f"Residuals — {name}")
    fig.tight_layout()
    fig.savefig(figures_dir / "residuals_best.png", dpi=120)
    plt.close(fig)


def _plot_error_by_activity(test, y_true, y_pred, name, figures_dir: Path) -> None:
    work = test.copy()
    work["_abs_err"] = np.abs(y_true - y_pred)
    views = work["views"].to_numpy()
    q33, q66 = np.quantile(views, [0.33, 0.66])
    bins = pd.cut(
        work["views"],
        bins=[-0.1, q33, q66, views.max() + 1],
        labels=["low_views", "medium_views", "high_views"],
    )
    mae_by = work.groupby(bins, observed=True)["_abs_err"].mean()
    fig, ax = plt.subplots(figsize=(7, 4))
    mae_by.plot(kind="bar", ax=ax, color="#b5651d", rot=0)
    ax.set_ylabel("MAE")
    ax.set_title(f"Error by activity (views) — {name}")
    fig.tight_layout()
    fig.savefig(figures_dir / "error_by_activity_best.png", dpi=120)
    plt.close(fig)


def _plot_experiment_comparison(metadata_dir: Path, figures_dir: Path) -> None:
    files = {
        "E1 (Oct holdout)": metadata_dir / "model_results.json",
        "E2 (early Nov)": metadata_dir / "generalization_results.json",
        "E_final (late Nov)": metadata_dir / "final_results.json",
    }
    models = ["lag1", "ma7", "hist_mean", "random_forest", "xgboost", "lightgbm"]
    data = {}
    for label, path in files.items():
        if not path.exists():
            continue
        payload = json.loads(path.read_text())
        data[label] = {
            m: payload["models"][m]["mae"]
            for m in models
            if m in payload.get("models", {})
        }
    if not data:
        return

    x = np.arange(len(models))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (label, maes) in enumerate(data.items()):
        vals = [maes.get(m, np.nan) for m in models]
        ax.bar(x + i * width, vals, width, label=label)
    ax.set_xticks(x + width)
    ax.set_xticklabels(models, rotation=20)
    ax.set_ylabel("MAE")
    ax.set_title("Experiment comparison (MAE by model)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "experiment_comparison.png", dpi=120)
    plt.close(fig)


def _plot_temporal_vs_random(figures_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    # Temporal
    ax = axes[0]
    ax.broken_barh([(0, 23)], (0.6, 0.6), facecolors="#2c5aa0", label="Train")
    ax.broken_barh([(23, 7)], (0.6, 0.6), facecolors="#c44e52", label="Test")
    ax.set_ylim(0, 2)
    ax.set_xlim(0, 30)
    ax.set_yticks([])
    ax.set_xlabel("October calendar day")
    ax.set_title("Temporal split (correct)")
    ax.legend(loc="upper right")
    ax.text(0.5, 1.5, "No future leakage — test is always after train", fontsize=9)

    # Random
    ax = axes[1]
    rng = np.random.default_rng(0)
    days = np.arange(30)
    is_test = rng.random(30) < 0.23
    for d in days:
        color = "#c44e52" if is_test[d] else "#2c5aa0"
        ax.barh(0.9, 1, left=d, height=0.6, color=color, edgecolor="white", linewidth=0.3)
    ax.set_ylim(0, 2)
    ax.set_xlim(0, 30)
    ax.set_yticks([])
    ax.set_xlabel("October calendar day")
    ax.set_title("Random row split (incorrect)")
    ax.text(0.5, 1.5, "Test days mixed into past — leakage risk", fontsize=9)

    fig.suptitle("Why demand forecasting uses a time-based holdout", fontsize=12)
    fig.tight_layout()
    fig.savefig(figures_dir / "temporal_vs_random_split.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
