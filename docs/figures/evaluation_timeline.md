# Figure: Evaluation strategy (temporal split)

October 2019 calendar window — no random row split.

```mermaid
gantt
  title Train vs test window product_by_day
  dateFormat YYYY-MM-DD
  axisFormat %d Oct
  section Train
  Days 1-23           :train, 2019-10-01, 23d
  section Test
  Days 24-30 holdout  :test, 2019-10-24, 7d
```

| Setting | Value |
|---------|-------|
| Train | First 23 unique calendar dates with a valid target (Oct 1–23) |
| Test | Next 7 dates (Oct 24–30); Oct 31 has no `purchases_next_day` label |
| Target | `purchases_next_day` |
| Metrics | MAE (primary), RMSE, MAPE, R² |
| Why not random split? | Prevents leakage from future dates into training |

All models (baselines + RF + XGBoost + LightGBM) use the **same** date boundary.

**Caption:** Time-based holdout — models trained on early October, evaluated on the final week.
