# Final Dissertation Implementation Plan

## Context

This is a clickstream-based demand forecasting pipeline for e-commerce.
Current state (mid-term, complete):
- Bronze → Silver → Gold pipeline on October 2019 data (42.4M events)
- Feature engineering: `product_summary.parquet`, `product_by_day.parquet`
- Six models trained: lag-1, ma7, hist_mean baselines + Random Forest, XGBoost, LightGBM
- Best result: Random Forest MAE 0.203 on Oct 24–30 holdout
- SHAP analysis complete
- All code in `scripts/`, `src/`, driven by `config.yaml`

What needs to be added for the final dissertation:

1. **November 2019 data** — download, process, and run three experiments
2. **Hyperparameter tuning** — tune the three ML models, compare before/after
3. **Error analysis** — deeper analysis of model performance and limitations
4. **FastAPI prediction service** — accept product_id + date, return prediction
5. **Makefile updates** — new targets for each phase

### Evaluation Strategy — Three Experiments

All test windows are 7 days so results are directly comparable.
Strict temporal ordering is maintained in all three — no data leakage.

| Experiment | Train set | Test set | Purpose |
|---|---|---|---|
| **E1** (existing, mid-term) | Oct 1–23 | Oct 24–30 | Baseline in-month evaluation |
| **E2** (new) | Oct 1–30 (full October) | Nov 1–7 | Generalization — does the model work on an unseen month? |
| **E3** (new) | Oct 1 – Nov 22 | Nov 23–29 | Does doubling training data improve accuracy? |

**Why this design:**
- E1 is the existing mid-term result — no code change needed, already have these numbers
- E2 answers: generalization to a new month with same training volume as E1
- E3 answers: does more training data (54 days vs 23 days) improve the same 7-day window test
- E1 and E3 have comparable test periods (both are late-month holdouts)
- E1 and E2 have comparable training sizes (23 vs 30 days)
- All three use the same feature set and evaluation metrics (MAE, RMSE, MAPE, R²)

The dissertation narrative:
> E1 establishes whether the approach works at all.
> E2 tests whether it generalises to an unseen month.
> E3 tests whether more training data produces measurably better predictions.

Save results to separate JSON files:
- `metadata/model_results.json` — E1 (existing)
- `metadata/generalization_results.json` — E2
- `metadata/extended_results.json` — E3

---

## Phase 1 — November 2019 Data and Generalization Test

### 1.1 Config changes (`config.yaml`)

Add support for multiple bronze files and a generalization test split:

```yaml
dataset:
  kaggle_slug: mkechinov/ecommerce-behavior-data-from-multi-category-store
  bronze_files:           # replaces single bronze_file key
    - "2019-Oct.csv"
    - "2019-Nov.csv"
  chunk_size: 500000
  max_chunks: null

training:
  gold_file: product_by_day.parquet
  target: purchases_next_day
  feature_columns:
    - views
    - carts
    - removals
    - purchases
    - views_7d
    - carts_7d
    - purchases_7d
  models_dir: data/models

  # E1 — existing in-month split (backward compat, already complete)
  train_days: 23
  test_days: 7
  results_file: metadata/model_results.json

  # E2 — generalization: train all of Oct, test first 7 days of Nov
  experiment_e2:
    train_end: "2019-10-30"    # last labeled day of October
    test_start: "2019-11-01"
    test_days: 7
    results_file: metadata/generalization_results.json

  # E3 — extended training: train Oct + most of Nov, test last week of Nov
  experiment_e3:
    train_end: "2019-11-22"
    test_start: "2019-11-23"
    test_days: 7
    results_file: metadata/extended_results.json

  shap:
    enabled: true
    sample_rows: 5000
    model: random_forest
```

### 1.2 Update `scripts/download.py`

Change to iterate over `config["dataset"]["bronze_files"]` instead of a single `bronze_file`.
Skip download if file already exists in bronze dir.

### 1.3 Update `scripts/clean.py`

Change to iterate over all files in `config["dataset"]["bronze_files"]`.
Each file is cleaned independently (same `clean_chunk` logic) and written to the same silver dir
(`data/silver/events/`). Parquet's `existing_data_behavior="overwrite_or_ignore"` already handles
multi-file writes partitioned by date — so no conflict between months.

Key change: replace `cfg["dataset"]["bronze_file"]` with a loop over `cfg["dataset"]["bronze_files"]`.

### 1.4 Update `src/bronze_files.py`

Update `resolve_bronze_csv()` or add `resolve_bronze_csvs()` that returns a list of paths,
one per file in `bronze_files`.

### 1.5 Update `scripts/build_features.py`

No change needed — it reads from silver, which now contains both months.
The `product_by_day.parquet` will automatically span October + November.

### 1.6 Add generalization test to `scripts/train_models.py`

After the existing in-month split evaluation, add a second evaluation block:

```python
# Generalization test: train on all of October, test on first N days of November
gen_cfg = cfg["training"].get("generalization", {})
if gen_cfg:
    gen_split = month_based_split(
        df,
        train_month=gen_cfg["train_month"],   # "2019-10"
        test_days=int(gen_cfg["test_days"]),   # 7
    )
    gen_metrics, _ = evaluate_all_models(
        gen_split.train, gen_split.test,
        feature_columns, target
    )
    # Save to metadata/generalization_results.json
```

### 1.7 Add `date_boundary_split()` to `src/training.py`

A single general-purpose split function that covers all three experiments:

```python
def date_boundary_split(df, train_end: str, test_start: str, test_days: int):
    """
    Split a product_by_day DataFrame by explicit date boundaries.
    Strict temporal ordering — no leakage.

    train_end:   last date (inclusive) in the training set  e.g. "2019-10-30"
    test_start:  first date of the test set                 e.g. "2019-11-01"
    test_days:   number of calendar days to include in test set

    E1: date_boundary_split(df, "2019-10-23", "2019-10-24", 7)  # existing
    E2: date_boundary_split(df, "2019-10-30", "2019-11-01", 7)  # generalization
    E3: date_boundary_split(df, "2019-11-22", "2019-11-23", 7)  # extended

    Returns the same Split namedtuple as time_based_split.
    """
```

Keep the existing `time_based_split()` unchanged — E1 still uses it.
E2 and E3 use `date_boundary_split()`.

---

## Phase 2 — Hyperparameter Tuning

### 2.1 New script: `scripts/tune_models.py`

Tune Random Forest, XGBoost, and LightGBM using RandomizedSearchCV
with TimeSeriesSplit cross-validation on the October training set.

```python
# Entry point
def main():
    # Load gold data (October only, first 23 days as per training split)
    # Run RandomizedSearchCV for each model
    # Save best params to metadata/best_params.json
    # Print comparison: default MAE vs best-params MAE
```

Parameter search spaces:

```python
RF_PARAMS = {
    "n_estimators": [100, 200, 300, 500],
    "max_depth": [6, 8, 10, 12, 15, None],
    "min_samples_leaf": [1, 2, 5, 10],
    "max_features": ["sqrt", "log2", 0.5],
}

XGB_PARAMS = {
    "n_estimators": [100, 200, 300],
    "learning_rate": [0.01, 0.05, 0.1, 0.2],
    "max_depth": [4, 6, 8],
    "subsample": [0.7, 0.8, 1.0],
    "colsample_bytree": [0.7, 0.8, 1.0],
}

LGBM_PARAMS = {
    "n_estimators": [100, 200, 300],
    "learning_rate": [0.01, 0.05, 0.1, 0.2],
    "num_leaves": [31, 63, 127],
    "subsample": [0.7, 0.8, 1.0],
    "min_child_samples": [10, 20, 50],
}
```

Use `n_iter=30`, `cv=TimeSeriesSplit(n_splits=3)`, `scoring="neg_mean_absolute_error"`.

Save output to `metadata/best_params.json`:
```json
{
  "random_forest": { "n_estimators": 300, "max_depth": 10, ... },
  "xgboost": { ... },
  "lightgbm": { ... }
}
```

### 2.2 Update `scripts/train_models.py`

Run all three experiments. For each experiment, run with default params first,
then with tuned params if `metadata/best_params.json` exists.

```python
def run_experiment(label, train_df, test_df, feature_columns, target,
                   results_path, models_dir, best_params=None):
    """
    Run evaluate_all_models on the given split.
    Save metrics to results_path.
    Save model artifacts to models_dir with label suffix (e.g. _e2, _e2_tuned).
    """

def main():
    # --- E1: existing in-month split (Oct 1-23 train, Oct 24-30 test) ---
    e1_split = time_based_split(df, train_days=23, test_days=7)
    run_experiment("e1", e1_split.train, e1_split.test, ...)

    # --- E2: generalization (Oct 1-30 train, Nov 1-7 test) ---
    e2_cfg = cfg["training"]["experiment_e2"]
    e2_split = date_boundary_split(df, e2_cfg["train_end"],
                                    e2_cfg["test_start"], e2_cfg["test_days"])
    run_experiment("e2", e2_split.train, e2_split.test, ...)

    # --- E3: extended training (Oct 1 - Nov 22 train, Nov 23-29 test) ---
    e3_cfg = cfg["training"]["experiment_e3"]
    e3_split = date_boundary_split(df, e3_cfg["train_end"],
                                    e3_cfg["test_start"], e3_cfg["test_days"])
    run_experiment("e3", e3_split.train, e3_split.test, ...)

    # --- Tuned pass: re-run all three experiments with best params ---
    best_params_path = metadata_dir / "best_params.json"
    if best_params_path.exists():
        best_params = json.loads(best_params_path.read_text())
        run_experiment("e1_tuned", ..., model_params=best_params)
        run_experiment("e2_tuned", ..., model_params=best_params)
        run_experiment("e3_tuned", ..., model_params=best_params)
```

The best model for the API is whichever Random Forest variant achieves the lowest MAE
across E1/E2/E3 tuned results. Save this as `data/models/best_model.joblib` with a
`metadata/best_model_info.json` recording which experiment it came from.

### 2.3 Update `src/training.py`

Update `evaluate_all_models()` to accept an optional `model_params` dict:

```python
def evaluate_all_models(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list,
    target: str,
    model_params: dict | None = None,   # ADD THIS
) -> tuple[dict, dict]:
```

When `model_params` is provided, use those params instead of defaults for RF/XGBoost/LightGBM.

### 2.4 Add `make tune` to Makefile

```makefile
tune:
    $(BIN)/python scripts/tune_models.py
```

---

## Phase 3 — Error Analysis

### 3.1 New script: `scripts/analyze_results.py`

Generates analysis plots and a summary JSON. Saves all outputs to `metadata/figures/`.

Functions to implement:

**`plot_predicted_vs_actual(y_true, y_pred, model_name)`**
- Scatter plot: x = actual purchases, y = predicted purchases
- Diagonal line = perfect prediction
- Save as `metadata/figures/pred_vs_actual_{model_name}.png`

**`plot_residuals(y_true, y_pred, model_name)`**
- Histogram of residuals (y_true - y_pred)
- Save as `metadata/figures/residuals_{model_name}.png`

**`plot_error_by_activity(df_test, y_pred, model_name)`**
- Bucket products by view count into low/medium/high
- Calculate MAE per bucket
- Bar chart showing error by product activity level
- Save as `metadata/figures/error_by_activity_{model_name}.png`

**`plot_model_comparison(all_metrics)`**
- Bar chart: MAE for all 6 models (default) + 3 tuned models side by side
- Save as `metadata/figures/model_comparison.png`

**`plot_three_experiment_comparison(e1, e2, e3)`**
- Bar chart with three groups (E1 / E2 / E3), one bar per model in each group
- Shows MAE across all three experiments side by side for every model
- Answers: does the model generalise? does more data help?
- Save as `metadata/figures/experiment_comparison.png`

**`plot_tuning_impact(default_metrics, tuned_metrics)`**
- Bar chart: MAE before vs after tuning for each ML model (RF, XGBoost, LightGBM)
- Save as `metadata/figures/tuning_impact.png`

**`save_analysis_summary()`**
- Writes `metadata/analysis_summary.json` with:
  - Best model name and params
  - Improvement from tuning (% MAE reduction)
  - Generalization gap (Oct MAE vs Nov MAE)
  - Error by activity bucket
  - Feature importance ranking from SHAP

### 3.2 Add `make analyze` to Makefile

```makefile
analyze:
    $(BIN)/python scripts/analyze_results.py
```

---

## Phase 4 — FastAPI Prediction Service

### 4.1 New directory structure

```
api/
├── __init__.py
├── main.py          # FastAPI app, routes
├── predictor.py     # Model loading, feature lookup, prediction logic
└── schemas.py       # Pydantic request/response models
```

### 4.2 `api/schemas.py`

```python
from pydantic import BaseModel

class PredictRequest(BaseModel):
    product_id: int
    date: str           # format: "YYYY-MM-DD"

class PredictResponse(BaseModel):
    product_id: int
    date: str
    predicted_purchases_next_day: float
    model_used: str
    features_used: dict     # the feature values that fed the model
    note: str | None        # e.g. "product not seen in training data"

class HealthResponse(BaseModel):
    status: str
    model_loaded: str
    gold_data_range: dict   # {"min_date": "...", "max_date": "..."}
```

### 4.3 `api/predictor.py`

```python
class DemandPredictor:
    def __init__(self, config_path="config.yaml"):
        # Load config
        # Load best available model (tuned > default, prefer random_forest)
        #   from data/models/random_forest_tuned.joblib or data/models/random_forest.joblib
        # Load product_by_day.parquet into memory (indexed by product_id + date)

    def predict(self, product_id: int, date: str) -> dict:
        # Look up the feature row for this product_id + date from gold table
        # If not found: return note "no data for this product/date combination"
        # If found: run model.predict() on the feature row
        # Return prediction + the feature values used
        
    def get_gold_date_range(self) -> dict:
        # Return min/max date from the gold table
```

### 4.4 `api/main.py`

```python
from fastapi import FastAPI, HTTPException
from api.predictor import DemandPredictor
from api.schemas import PredictRequest, PredictResponse, HealthResponse

app = FastAPI(
    title="Demand Forecasting API",
    description="Predicts next-day purchase count for a product given its clickstream activity",
    version="1.0.0",
)

predictor = DemandPredictor()

@app.get("/health", response_model=HealthResponse)
def health():
    ...

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    ...

@app.get("/products")
def list_products(limit: int = 20):
    # Return top N products by total purchases from gold table
    ...
```

### 4.5 Add `fastapi` and `uvicorn` to `requirements.txt`

```
fastapi>=0.110.0
uvicorn>=0.29.0
```

### 4.6 Add `make api` to Makefile

```makefile
api:
    $(BIN)/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.7 Add `pytest.ini` test for API

Add `tests/test_api.py`:
- Test `/health` returns 200
- Test `/predict` with a known product_id + date from gold table returns a valid float
- Test `/predict` with unknown product_id returns a note (not a 500 error)

---

## Phase 5 — Makefile Final State

```makefile
# New targets to add:
download-nov:    # download November 2019 CSV only
    $(BIN)/python scripts/download.py --file 2019-Nov.csv

tune:            # hyperparameter tuning → metadata/best_params.json
    $(BIN)/python scripts/tune_models.py

retrain:         # retrain with tuned params → data/models/*_tuned.joblib
    $(BIN)/python scripts/train_models.py --use-tuned

analyze:         # error analysis → metadata/figures/
    $(BIN)/python scripts/analyze_results.py

api:             # start FastAPI server on port 8000
    $(BIN)/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Full final pipeline:
all-final: download clean features tune retrain analyze
```

---

## Implementation Order for Cursor

Do these in order — each phase depends on the previous:

1. `config.yaml` — add `bronze_files` list and `generalization` block
2. `src/bronze_files.py` — update to return list of paths
3. `scripts/download.py` — loop over bronze_files
4. `scripts/clean.py` — loop over bronze_files
5. `src/training.py` — add `month_based_split()`, update `evaluate_all_models()` signature
6. `scripts/train_models.py` — add generalization test block + tuned params block
7. `scripts/tune_models.py` — new file, full hyperparameter search
8. `scripts/analyze_results.py` — new file, all analysis plots
9. `api/` directory — schemas, predictor, main
10. `requirements.txt` — add fastapi, uvicorn
11. `Makefile` — new targets
12. `tests/test_api.py` — basic API tests

---

## Notes for Cursor

- The gold table (`product_by_day.parquet`) is a flat file, not partitioned. Reading it fully into
  memory for the API is fine — it is ~150MB at most.
- The best trained model is saved as a joblib file in `data/models/`. The API should prefer
  `random_forest_tuned.joblib` if it exists, falling back to `random_forest.joblib`.
- Do not change `src/cleaning.py` — the `clean_chunk()` function works correctly as-is.
- Preserve backward compatibility: `config.yaml` still supports the old single `bronze_file` key
  as a fallback if `bronze_files` is not present.
- Use `append_run_log()` from `src/io_utils.py` in every new script for audit trail.
- All new figures go to `metadata/figures/` (same as existing SHAP/EDA figures).
