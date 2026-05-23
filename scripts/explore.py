#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, resolve_path
from src.io_utils import ensure_dir, read_silver_dataset, write_profile


def main() -> None:
    cfg = load_config()
    silver_dir = resolve_path(cfg["paths"]["silver_dir"])
    metadata_dir = resolve_path(cfg["paths"]["metadata_dir"])
    figures_dir = ensure_dir(resolve_path(cfg["paths"]["figures_dir"]))

    df = read_silver_dataset(silver_dir)
    df["event_time"] = pd.to_datetime(df["event_time"], utc=True)
    df["date"] = pd.to_datetime(df["date"], utc=True)

    event_counts = df["event_type"].value_counts().to_dict()
    funnel = {
        "view": int(event_counts.get("view", 0)),
        "cart": int(event_counts.get("cart", 0)),
        "remove_from_cart": int(event_counts.get("remove_from_cart", 0)),
        "purchase": int(event_counts.get("purchase", 0)),
    }

    daily = df.groupby(df["event_time"].dt.date).size()
    hourly = df.groupby(df["event_time"].dt.hour).size()

    top_products = (
        df[df["event_type"] == "view"]
        .groupby("product_id")
        .size()
        .sort_values(ascending=False)
        .head(20)
        .astype(int)
        .to_dict()
    )

    summary = {
        "rows": int(len(df)),
        "date_min": str(df["event_time"].min()),
        "date_max": str(df["event_time"].max()),
        "unique_products": int(df["product_id"].nunique()),
        "unique_users": int(df["user_id"].nunique()),
        "event_counts": {k: int(v) for k, v in event_counts.items()},
        "funnel": funnel,
        "top_viewed_products": {str(k): v for k, v in top_products.items()},
    }
    out_json = write_profile(metadata_dir, "eda_summary", summary)
    _plot_daily(daily, figures_dir / "daily_activity.png")
    _plot_hourly(hourly, figures_dir / "hourly_activity.png")
    _plot_funnel(funnel, figures_dir / "event_funnel.png")
    print(figures_dir)


def _plot_daily(series: pd.Series, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    series.plot(ax=ax)
    ax.set_title("Daily event volume")
    ax.set_xlabel("Date")
    ax.set_ylabel("Events")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _plot_hourly(series: pd.Series, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    series.sort_index().plot(kind="bar", ax=ax)
    ax.set_title("Events by hour of day (UTC)")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Events")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _plot_funnel(funnel: dict[str, int], path: Path) -> None:
    labels = list(funnel.keys())
    values = [funnel[k] for k in labels]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values)
    ax.set_title("Event type counts")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
