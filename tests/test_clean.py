import pandas as pd

from src.cleaning import clean_chunk


def test_clean_chunk_drops_invalid_and_adds_date():
    df = pd.read_csv("tests/fixtures/sample_events.csv")
    rows_in = len(df)
    out = clean_chunk(df)
    assert len(out) < rows_in
    assert "date" in out.columns
    assert set(out["event_type"].unique()).issubset(
        {"view", "cart", "purchase", "remove_from_cart"}
    )
    assert out["event_time"].dt.tz is not None


def test_clean_chunk_deduplicates_exact_rows():
    df = pd.read_csv("tests/fixtures/sample_events.csv")
    dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    out = clean_chunk(dup)
    assert len(out) == len(clean_chunk(df))
