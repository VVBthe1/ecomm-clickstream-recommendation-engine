#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir, read_silver_dataset


def main() -> None:
    cfg = load_config()
    silver_dir = resolve_path(cfg["paths"]["silver_dir"])
    gold_dir = ensure_dir(resolve_path(cfg["paths"]["gold_dir"]))
    window = int(cfg["processing"]["rolling_window_days"])

    df = read_silver_dataset(silver_dir)
    df["date"] = pd.to_datetime(df["date"], utc=True)

    product_summary = build_product_summary(df)
    product_by_day = build_product_by_day(df, window=window)

    summary_path = gold_dir / "product_summary.parquet"
    daily_path = gold_dir / "product_by_day.parquet"
    product_summary.to_parquet(summary_path, index=False)
    product_by_day.to_parquet(daily_path, index=False)

    append_run_log(
        resolve_path(cfg["paths"]["metadata_dir"]),
        "build_features",
        {
            "product_summary_rows": len(product_summary),
            "product_by_day_rows": len(product_by_day),
            "paths": [str(summary_path), str(daily_path)],
        },
    )
    print(gold_dir)


def build_product_summary(df: pd.DataFrame) -> pd.DataFrame:
    views = df[df["event_type"] == "view"].groupby("product_id").size()
    carts = df[df["event_type"] == "cart"].groupby("product_id").size()
    removals = df[df["event_type"] == "remove_from_cart"].groupby("product_id").size()
    purchases = df[df["event_type"] == "purchase"].groupby("product_id").size()

    products = pd.DataFrame({"product_id": df["product_id"].unique()})
    products = products.set_index("product_id")
    products["total_views"] = views
    products["total_carts"] = carts
    products["total_removals"] = removals
    products["total_purchases"] = purchases
    products = products.fillna(0).astype(
        {
            "total_views": "int64",
            "total_carts": "int64",
            "total_removals": "int64",
            "total_purchases": "int64",
        }
    )

    products["view_to_cart_rate"] = products["total_carts"] / products["total_views"].replace(0, pd.NA)
    products["cart_to_purchase_rate"] = products["total_purchases"] / products["total_carts"].replace(0, pd.NA)

    view_users = df[df["event_type"] == "view"].groupby("product_id")["user_id"].nunique()
    repeat_viewers = (
        df[df["event_type"] == "view"]
        .groupby(["product_id", "user_id"])
        .size()
        .reset_index(name="n")
    )
    repeat_viewers = (
        repeat_viewers[repeat_viewers["n"] > 1].groupby("product_id")["user_id"].nunique()
    )
    products["unique_viewers"] = view_users
    products["repeat_viewers"] = repeat_viewers
    products["unique_viewers"] = products["unique_viewers"].fillna(0).astype("int64")
    products["repeat_viewers"] = products["repeat_viewers"].fillna(0).astype("int64")

    purchase_prices = df[df["event_type"] == "purchase"].groupby("product_id")["price"].mean()
    products["avg_purchase_price"] = purchase_prices

    peak_hour = (
        df[df["event_type"] == "view"]
        .assign(hour=df["event_time"].dt.hour)
        .groupby(["product_id", "hour"])
        .size()
        .reset_index(name="n")
        .sort_values(["product_id", "n"], ascending=[True, False])
        .drop_duplicates("product_id")
        .set_index("product_id")["hour"]
    )
    products["peak_view_hour"] = peak_hour

    return products.reset_index()


def build_product_by_day(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    daily = (
        df.groupby(["product_id", "date", "event_type"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["view", "cart", "remove_from_cart", "purchase"]:
        if col not in daily.columns:
            daily[col] = 0
    daily = daily.rename(
        columns={
            "view": "views",
            "cart": "carts",
            "remove_from_cart": "removals",
            "purchase": "purchases",
        }
    )

    daily = daily.sort_values(["product_id", "date"])
    g = daily.groupby("product_id", group_keys=False)
    daily["purchases_next_day"] = g["purchases"].shift(-1)

    for col in ["views", "carts", "purchases"]:
        daily[f"{col}_{window}d"] = (
            g[col].transform(lambda s: s.rolling(window, min_periods=1).sum())
        )

    return daily


if __name__ == "__main__":
    main()
