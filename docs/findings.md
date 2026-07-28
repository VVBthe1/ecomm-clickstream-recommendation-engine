# Findings

Refresh after `make train` / `make analyze` on Oct+Nov gold. Current numbers below are **E1 only** (October) after the lag-1/ma7 baseline fix. E2 and E_final require `2019-Nov.csv`.

## Experiments

| Experiment | Train | Test | Results file | Status |
|------------|-------|------|--------------|--------|
| E1 | Oct 1–23 | Oct 24–30 | `metadata/model_results.json` | **Done** |
| E2 | Oct 1–30 | Nov 1–7 | `metadata/generalization_results.json` | Needs Nov gold |
| E_final | Oct 1 – Nov 15 | Nov 16–29 | `metadata/final_results.json` | Needs Nov gold |

Primary API model: `data/models/best_model.joblib` (see `metadata/best_model_info.json`).

## E1 model comparison (after lag-1 fix)

Lag-1 = same-day `purchases` (Eq. 6.3). MA7 = 7-day rolling mean through today (Eq. 6.4).

| Model | MAE | RMSE | MAPE (%) | R² |
|-------|-----|------|----------|-----|
| lag1 | 0.202 | 1.014 | 81.9 | 0.973 |
| **ma7** | **0.202** | 1.180 | 71.3 | 0.963 |
| hist_mean | 0.229 | 1.473 | 74.2 | 0.943 |
| random_forest | 0.203 | **0.993** | **68.8** | **0.974** |
| xgboost | 0.226 | 2.503 | 69.1 | 0.834 |
| lightgbm | 0.206 | 1.066 | 69.1 | 0.970 |

**Best by MAE (E1):** ma7 (narrowly). **API tree model:** random_forest (best among RF/XGB/LGBM).  
RF still has the best RMSE/R²/MAPE among tree models.

## Lag-1 definition (aligned with report)

`pred_lag1` = same-day `purchases` on the feature row.  
`pred_ma7` = 7-day rolling mean of same-day `purchases` through today.

## Analysis artifacts

After `make analyze` (currently on E1 holdout until Nov exists):

- `metadata/figures/pred_vs_actual_best.png`
- `metadata/figures/residuals_best.png`
- `metadata/figures/error_by_activity_best.png`
- `metadata/figures/experiment_comparison.png`
- `metadata/figures/temporal_vs_random_split.png`
- `metadata/figures/shap_summary.png` (Random Forest)
- `metadata/analysis_summary.json`

## How to finish Nov experiments (on your machine)

```bash
# needs working Kaggle auth / network
make install
make all          # download → clean → explore → features → train → tune → retrain → analyze
make api
```

## API

`make api` → http://127.0.0.1:8000/docs  

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"product_id":1004856,"date":"2019-10-29"}'
```
