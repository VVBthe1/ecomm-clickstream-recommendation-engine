# Prediction problem

**Objective:** product-level **demand forecasting** from clickstream behaviour.

Forecast next-day **purchase count** per product.

| Item | Choice |
|------|--------|
| Grain | `product_id`, `date` |
| Target | `purchases_next_day` in `data/gold/product_by_day.parquet` |
| Features | Same-day views/carts/purchases + 7-day rollups |
| Baselines | Lag-1, 7-day moving average, per-product historical mean |
| Models | Random Forest, XGBoost, LightGBM |
| Validation | Time-based holdout (first 24 days train, last 7 test) |
| Metrics | MAE, RMSE, MAPE, R² |

Not in scope: inventory rules, recommendation ranking (demo FastAPI predict endpoint is in scope for final).

| Experiment | Train | Test |
|------------|-------|------|
| E1 (mid-term) | Oct 1–23 | Oct 24–30 |
| E2 | Oct 1–30 | Nov 1–7 |
| E_final (primary) | Oct 1 – Nov 15 | Nov 16–29 |

Run training: `make train` → E1/E2/E_final metrics. Tune: `make tune` then `make retrain`. API: `make api`.
