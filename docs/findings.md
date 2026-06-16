# Findings

Generated from `metadata/eda_summary.json` and `metadata/model_results.json`. Re-run `make explore` and `make train` on full October silver/gold to refresh for the final report.

## EDA summary

| Metric | Value |
|--------|-------|
| Gold rows (`product_by_day`) | 1,550 |
| Date range | 2019-10-01 → 2019-10-30 |
| Unique products | 50 |
| Total views (aggregated) | 6,705 |
| Total carts | 2,542 |
| Total purchases | 1,644 |

Charts: `metadata/figures/daily_activity.png`, `hourly_activity.png`, `event_funnel.png` (from `make explore` on silver).

**Note:** Current EDA JSON was produced from a pipeline smoke test. After `make clean && make explore` on full `2019-Oct.csv`, replace the table above with values from the updated `eda_summary.json`.

## Model comparison (temporal holdout)

Train: first 23 calendar days with labels (Oct 1–23). Test: next 7 days (Oct 24–30). Target: `purchases_next_day`. Oct 31 rows have no label (no November data).

| Model | MAE | RMSE | MAPE (%) | R² |
|-------|-----|------|----------|-----|
| lag1 | 0.214 | 1.187 | 84.1 | 0.963 |
| ma7 | 0.210 | 1.317 | 72.6 | 0.954 |
| hist_mean | 0.229 | 1.473 | 74.2 | 0.943 |
| **random_forest** | **0.203** | **0.993** | **68.8** | **0.974** |
| xgboost | 0.226 | 2.503 | 69.1 | 0.834 |
| lightgbm | 0.206 | 1.066 | 69.1 | 0.970 |

**Best by MAE:** random_forest (see `metadata/model_results.json`). Test holdout: Oct 24–30 (465,679 product-day rows).

SHAP plot (if enabled): `metadata/figures/shap_summary.png`.

## Interpretation (draft for Results chapter)

- Random Forest achieves the lowest MAE on the 7-day holdout; lag-1 and 7-day MA baselines remain strong on this sparse count target.
- High MAPE reflects many near-zero purchase days; MAE and RMSE are the primary metrics for the report.
- Re-run `make explore` on full silver to refresh EDA table (current `eda_summary.json` is still from smoke test).

## Report pointers

- Abstract + objectives: `docs/research_abstract.md`
- Literature + comparative table: `docs/literature.md`
- Methodology figures: `docs/figures/`
- Problem definition: `docs/prediction_problem.md`
