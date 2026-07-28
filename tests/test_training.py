import numpy as np
import pandas as pd

from src.training import (
    add_baseline_predictions,
    compute_metrics,
    date_boundary_split,
    historical_mean_predictions,
    time_based_split,
)


def test_time_based_split_respects_calendar_order():
    dates = pd.date_range("2019-10-01", periods=30, freq="D", tz="UTC")
    rows = []
    for d in dates:
        rows.append(
            {
                "product_id": 1,
                "date": d,
                "purchases": 1,
                "purchases_next_day": 1,
                "views": 1,
                "carts": 0,
                "removals": 0,
                "views_7d": 1,
                "carts_7d": 0,
                "purchases_7d": 1,
            }
        )
    df = pd.DataFrame(rows)
    split = time_based_split(df, train_days=23, test_days=7)
    assert len(split.train_dates) == 23
    assert len(split.test_dates) == 7
    assert split.train["date"].max() < split.test["date"].min()


def test_compute_metrics_perfect_prediction():
    y = np.array([1.0, 2.0, 3.0])
    m = compute_metrics(y, y)
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["r2"] == 1.0


def test_historical_mean_uses_train_only():
    train = pd.DataFrame(
        {
            "product_id": [1, 1, 2],
            "purchases": [2.0, 4.0, 10.0],
        }
    )
    test = pd.DataFrame({"product_id": [1, 2, 3]})
    preds = historical_mean_predictions(train, test)
    assert preds[0] == 3.0
    assert preds[1] == 10.0
    assert preds[2] == 0.0


def test_add_baseline_predictions_lag1():
    df = pd.DataFrame(
        {
            "product_id": [1, 1, 1],
            "date": pd.date_range("2019-10-01", periods=3, tz="UTC"),
            "purchases": [1, 3, 5],
        }
    )
    out = add_baseline_predictions(df)
    # Lag-1 = today's purchases (Eq. 6.3)
    assert out["pred_lag1"].tolist() == [1, 3, 5]
    # MA7 through today: day3 mean of [1, 3, 5] = 3.0
    assert out["pred_ma7"].iloc[2] == 3.0


def test_date_boundary_split():
    dates = pd.date_range("2019-10-01", periods=60, freq="D", tz="UTC")
    df = pd.DataFrame(
        {
            "product_id": 1,
            "date": dates,
            "purchases": 1,
            "purchases_next_day": 1,
        }
    )
    split = date_boundary_split(
        df,
        train_end="2019-11-15",
        test_start="2019-11-16",
        test_days=14,
    )
    assert len(split.test_dates) == 14
    assert split.train["date"].max() <= pd.Timestamp("2019-11-15", tz="UTC")
    assert split.test["date"].min() >= pd.Timestamp("2019-11-16", tz="UTC")
