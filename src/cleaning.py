from __future__ import annotations

import pandas as pd

VALID_EVENT_TYPES = frozenset({"view", "cart", "remove_from_cart", "purchase"})

REQUIRED_COLUMNS = [
    "event_time",
    "event_type",
    "product_id",
    "category_id",
    "category_code",
    "brand",
    "price",
    "user_id",
    "user_session",
]


def clean_chunk(
    df: pd.DataFrame,
    valid_event_types: frozenset[str] | None = None,
) -> pd.DataFrame:
    allowed = valid_event_types or VALID_EVENT_TYPES
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    out = df.copy()
    out["event_time"] = pd.to_datetime(out["event_time"], utc=True, errors="coerce")
    out = out.dropna(subset=["event_time"])

    out["event_type"] = out["event_type"].astype(str).str.strip().str.lower()
    out = out[out["event_type"].isin(allowed)]

    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    out = out.dropna(subset=["price"])
    out = out[out["price"] >= 0]

    out["product_id"] = pd.to_numeric(out["product_id"], errors="coerce")
    out["category_id"] = pd.to_numeric(out["category_id"], errors="coerce")
    out["user_id"] = pd.to_numeric(out["user_id"], errors="coerce")
    out = out.dropna(subset=["product_id", "category_id", "user_id"])
    out["product_id"] = out["product_id"].astype("int64")
    out["category_id"] = out["category_id"].astype("int64")
    out["user_id"] = out["user_id"].astype("int64")

    out["category_code"] = out["category_code"].astype(str).str.strip()
    out.loc[out["category_code"].isin(["", "nan", "None"]), "category_code"] = pd.NA
    out["brand"] = out["brand"].astype(str).str.strip()
    out.loc[out["brand"].isin(["", "nan", "None"]), "brand"] = pd.NA
    out["user_session"] = out["user_session"].astype(str).str.strip()

    out = out.drop_duplicates()
    out["date"] = out["event_time"].dt.floor("D")

    return out[REQUIRED_COLUMNS + ["date"]]
