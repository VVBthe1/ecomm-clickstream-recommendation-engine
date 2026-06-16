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

Not in scope: inventory rules, recommendation ranking, live API (see `docs/literature.md` for related work cited as background only).

Run training: `make train` → `metadata/model_results.json`.
