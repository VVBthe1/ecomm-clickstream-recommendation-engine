#!/usr/bin/env python3
"""Train baselines + ML models for E1, E2, and E_final (default params).

Optionally apply tuned params from metadata/best_params.json for E_final
and write data/models/best_model.joblib.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir
from src.training import (
    best_model_by_mae,
    date_boundary_split,
    evaluate_all_models,
    time_based_split,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use-tuned",
        action="store_true",
        help="Re-run E_final with best_params.json and save best_model.joblib",
    )
    parser.add_argument(
        "--experiment",
        choices=["all", "e1", "e2", "final"],
        default="all",
        help="Which experiment(s) to run",
    )
    args = parser.parse_args()

    cfg = load_config()
    training = cfg["training"]
    gold_path = resolve_path(cfg["paths"]["gold_dir"]) / training["gold_file"]
    metadata_dir = resolve_path(cfg["paths"]["metadata_dir"])
    figures_dir = ensure_dir(resolve_path(cfg["paths"]["figures_dir"]))
    models_dir = ensure_dir(resolve_path(training["models_dir"]))

    df = pd.read_parquet(gold_path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.dropna(subset=[training["target"]])

    feature_columns = list(training["feature_columns"])
    target = training["target"]

    best_params: dict[str, Any] | None = None
    params_path = metadata_dir / "best_params.json"
    if args.use_tuned and params_path.exists():
        best_params = json.loads(params_path.read_text())
        print(f"Using tuned params from {params_path}")

    results_summary: dict[str, Any] = {}

    if args.experiment in ("all", "e1") and not args.use_tuned:
        e1 = time_based_split(
            df,
            train_days=int(training["train_days"]),
            test_days=int(training["test_days"]),
        )
        metrics, fitted = evaluate_all_models(
            e1.train, e1.test, feature_columns, target
        )
        out = _write_results(
            resolve_path(training["results_file"]),
            "e1",
            e1,
            metrics,
        )
        results_summary["e1"] = out["best_by_mae"]
        for name, model in fitted.items():
            joblib.dump(model, models_dir / f"e1_{name}.joblib")
        print(f"E1 best: {out['best_by_mae']} -> {out['path']}")

    if args.experiment in ("all", "e2") and not args.use_tuned:
        e2_cfg = training["experiment_e2"]
        try:
            e2 = date_boundary_split(
                df,
                train_end=e2_cfg["train_end"],
                test_start=e2_cfg["test_start"],
                test_days=int(e2_cfg["test_days"]),
            )
        except ValueError as exc:
            print(f"SKIP E2 (need November gold): {exc}")
        else:
            metrics, fitted = evaluate_all_models(
                e2.train, e2.test, feature_columns, target
            )
            out = _write_results(
                resolve_path(e2_cfg["results_file"]),
                "e2",
                e2,
                metrics,
            )
            results_summary["e2"] = out["best_by_mae"]
            for name, model in fitted.items():
                joblib.dump(model, models_dir / f"e2_{name}.joblib")
            print(f"E2 best: {out['best_by_mae']} -> {out['path']}")

    if args.experiment in ("all", "final") or args.use_tuned:
        ef_cfg = training["experiment_final"]
        try:
            ef = date_boundary_split(
                df,
                train_end=ef_cfg["train_end"],
                test_start=ef_cfg["test_start"],
                test_days=int(ef_cfg["test_days"]),
            )
        except ValueError as exc:
            print(f"SKIP E_final (need November gold): {exc}")
            if args.use_tuned:
                raise
        else:
            metrics, fitted = evaluate_all_models(
                ef.train,
                ef.test,
                feature_columns,
                target,
                model_params=best_params if args.use_tuned else None,
            )
            results_name = (
                "metadata/final_results_tuned.json"
                if args.use_tuned
                else ef_cfg["results_file"]
            )
            out = _write_results(
                resolve_path(results_name),
                "e_final_tuned" if args.use_tuned else "e_final",
                ef,
                metrics,
                tuned=bool(args.use_tuned),
            )
            results_summary["e_final"] = out["best_by_mae"]
            suffix = "final_tuned" if args.use_tuned else "final"
            for name, model in fitted.items():
                joblib.dump(model, models_dir / f"{suffix}_{name}.joblib")

            best_name = out["best_by_mae"]
            tree_models = ["random_forest", "xgboost", "lightgbm"]
            # API needs a sklearn-like estimator; prefer best tree if MAE winner is a baseline
            if best_name in tree_models:
                api_name = best_name
            else:
                api_name = min(tree_models, key=lambda m: metrics[m]["mae"])
            best_obj = fitted[api_name]
            joblib.dump(best_obj, models_dir / "best_model.joblib")
            info = {
                "model_name": api_name,
                "overall_best_by_mae": best_name,
                "experiment": "e_final",
                "tuned": bool(args.use_tuned),
                "mae": metrics[api_name]["mae"],
                "params": (best_params or {}).get(api_name),
                "train_end": ef_cfg["train_end"],
                "test_start": ef_cfg["test_start"],
                "test_days": ef_cfg["test_days"],
                "feature_columns": feature_columns,
                "target": target,
            }
            info_path = metadata_dir / "best_model_info.json"
            info_path.write_text(json.dumps(info, indent=2))
            print(f"E_final best: {best_name} -> {models_dir / 'best_model.joblib'}")

            shap_cfg = training.get("shap", {})
            if shap_cfg.get("enabled", False):
                shap_key = shap_cfg.get("model", best_name)
                if shap_key not in fitted or not hasattr(fitted[shap_key], "predict"):
                    shap_key = (
                        best_name if hasattr(best_obj, "predict") else "random_forest"
                    )
                _maybe_shap(
                    fitted,
                    ef.test,
                    feature_columns,
                    {**shap_cfg, "model": shap_key},
                    figures_dir,
                )

    # If E_final was skipped, promote E1 best *tree* model for API continuity
    best_path = models_dir / "best_model.joblib"
    if not best_path.exists() and (models_dir / "e1_random_forest.joblib").exists():
        e1_results = resolve_path(training["results_file"])
        payload = json.loads(e1_results.read_text()) if e1_results.exists() else {}
        overall_best = payload.get("best_by_mae", "random_forest")
        metrics = payload.get("models", {})
        tree_models = ["random_forest", "xgboost", "lightgbm"]
        api_name = min(
            (m for m in tree_models if m in metrics),
            key=lambda m: metrics[m]["mae"],
            default="random_forest",
        )
        src = models_dir / f"e1_{api_name}.joblib"
        if src.exists():
            joblib.dump(joblib.load(src), best_path)
            (metadata_dir / "best_model_info.json").write_text(
                json.dumps(
                    {
                        "model_name": api_name,
                        "experiment": "e1_fallback",
                        "tuned": False,
                        "overall_best_by_mae": overall_best,
                        "mae": metrics.get(api_name, {}).get("mae"),
                        "note": (
                            "E_final unavailable — API uses best tree model from E1 "
                            f"(overall MAE winner was {overall_best})"
                        ),
                        "feature_columns": feature_columns,
                        "target": target,
                    },
                    indent=2,
                )
            )
            print(f"API fallback best_model from E1 tree: {api_name}")
            # SHAP on E1 test for examiner figure
            shap_cfg = training.get("shap", {})
            if shap_cfg.get("enabled", False):
                e1 = time_based_split(
                    df,
                    train_days=int(training["train_days"]),
                    test_days=int(training["test_days"]),
                )
                fitted_tree = {api_name: joblib.load(best_path)}
                _maybe_shap(
                    fitted_tree,
                    e1.test.dropna(subset=[target]),
                    feature_columns,
                    {**shap_cfg, "model": api_name},
                    figures_dir,
                )

    append_run_log(
        metadata_dir,
        "train_models",
        {"experiments": results_summary, "use_tuned": args.use_tuned},
    )


def _write_results(
    path: Path,
    label: str,
    split,
    metrics: dict,
    tuned: bool = False,
) -> dict:
    ensure_dir(path.parent)
    payload = {
        "experiment": label,
        "tuned": tuned,
        "split": {
            "train_dates": split.train_dates,
            "test_dates": split.test_dates,
            "train_rows": len(split.train.dropna(subset=["purchases_next_day"]))
            if "purchases_next_day" in split.train.columns
            else len(split.train),
            "test_rows": len(split.test),
        },
        "models": metrics,
        "best_by_mae": best_model_by_mae(metrics),
    }
    # Fix train_rows properly
    payload["split"]["train_rows"] = int(
        split.train["purchases_next_day"].notna().sum()
        if "purchases_next_day" in split.train.columns
        else len(split.train)
    )
    payload["split"]["test_rows"] = int(
        split.test["purchases_next_day"].notna().sum()
        if "purchases_next_day" in split.test.columns
        else len(split.test)
    )
    path.write_text(json.dumps(payload, indent=2))
    return {"best_by_mae": payload["best_by_mae"], "path": str(path)}


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

    model_key = shap_cfg.get("model", "random_forest")
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
    print(f"SHAP saved: {out}")


if __name__ == "__main__":
    main()
