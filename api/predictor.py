"""Load best model and look up gold features for prediction."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import load_config, resolve_path


class DemandPredictor:
    def __init__(self) -> None:
        self.cfg = load_config()
        training = self.cfg["training"]
        self.feature_columns = list(training["feature_columns"])
        models_dir = resolve_path(training["models_dir"])
        metadata_dir = resolve_path(self.cfg["paths"]["metadata_dir"])

        model_path = models_dir / "best_model.joblib"
        if not model_path.exists():
            for candidate in (
                models_dir / "final_random_forest.joblib",
                models_dir / "final_tuned_random_forest.joblib",
                models_dir / "random_forest.joblib",
            ):
                if candidate.exists():
                    model_path = candidate
                    break
        if not model_path.exists():
            raise FileNotFoundError(
                f"No model found under {models_dir}. Run make train first."
            )

        self.model = joblib.load(model_path)
        self.model_path = model_path
        info_path = metadata_dir / "best_model_info.json"
        self.info = (
            json.loads(info_path.read_text())
            if info_path.exists()
            else {"model_name": model_path.stem}
        )

        gold_path = resolve_path(self.cfg["paths"]["gold_dir"]) / training["gold_file"]
        gold = pd.read_parquet(gold_path)
        gold["date"] = pd.to_datetime(gold["date"], utc=True)
        gold["date_str"] = gold["date"].dt.strftime("%Y-%m-%d")
        self.gold = gold

    @property
    def model_name(self) -> str:
        return str(self.info.get("model_name", self.model_path.stem))

    def get_gold_date_range(self) -> dict[str, str]:
        return {
            "min_date": str(self.gold["date"].min().date()),
            "max_date": str(self.gold["date"].max().date()),
        }

    def predict(self, product_id: int, date: str) -> dict[str, Any]:
        hit = self.gold[
            (self.gold["product_id"] == product_id) & (self.gold["date_str"] == date)
        ]
        if hit.empty:
            return {
                "product_id": product_id,
                "date": date,
                "predicted_purchases_next_day": 0.0,
                "model_used": self.model_name,
                "features_used": {},
                "note": "no data for this product/date combination",
            }

        row = hit.iloc[0]
        features = {
            c: float(row[c]) if pd.notna(row[c]) else 0.0 for c in self.feature_columns
        }
        x = pd.DataFrame([features])[self.feature_columns]

        if hasattr(self.model, "predict"):
            pred = float(self.model.predict(x)[0])
        else:
            pred = float(features.get("purchases", 0.0))

        return {
            "product_id": product_id,
            "date": date,
            "predicted_purchases_next_day": pred,
            "model_used": self.model_name,
            "features_used": features,
            "note": None,
        }

    def top_products(self, limit: int = 20) -> list[dict[str, Any]]:
        totals = (
            self.gold.groupby("product_id")["purchases"]
            .sum()
            .sort_values(ascending=False)
            .head(limit)
        )
        return [
            {"product_id": int(pid), "total_purchases": int(val)}
            for pid, val in totals.items()
        ]

    def top_predicted(
        self,
        date: str,
        limit: int = 10,
        min_views: float = 0.0,
    ) -> dict[str, Any]:
        """Rank products by predicted next-day purchases for a gold feature date."""
        day = self.gold[self.gold["date_str"] == date].copy()
        if day.empty:
            return {
                "date": date,
                "limit": limit,
                "model_used": self.model_name,
                "count": 0,
                "products": [],
                "note": (
                    f"no gold rows for date {date}; "
                    f"valid range {self.get_gold_date_range()}"
                ),
            }

        if min_views > 0 and "views" in day.columns:
            day = day[day["views"].fillna(0) >= min_views]
        if day.empty:
            return {
                "date": date,
                "limit": limit,
                "model_used": self.model_name,
                "count": 0,
                "products": [],
                "note": f"no products with views >= {min_views} on {date}",
            }

        x = day[self.feature_columns].fillna(0.0)
        if hasattr(self.model, "predict"):
            preds = self.model.predict(x)
        else:
            preds = day["purchases"].fillna(0.0).to_numpy()

        day = day.assign(_pred=preds)
        top = day.nlargest(limit, "_pred")

        products = [
            {
                "rank": i + 1,
                "product_id": int(row["product_id"]),
                "predicted_purchases_next_day": float(row["_pred"]),
                "purchases": float(row["purchases"]) if pd.notna(row["purchases"]) else None,
                "views": float(row["views"]) if pd.notna(row["views"]) else None,
            }
            for i, (_, row) in enumerate(top.iterrows())
        ]
        return {
            "date": date,
            "limit": limit,
            "model_used": self.model_name,
            "count": len(products),
            "products": products,
            "note": None,
        }
