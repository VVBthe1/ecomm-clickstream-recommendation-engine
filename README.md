# Clickstream demand forecasting

E-commerce clickstream pipeline that turns raw store events into **next-day product purchase** forecasts. Built for a BITS WILP dissertation on public [Kaggle multi-category behaviour data](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) (October and November 2019).

Flow: **bronze → silver → gold → models → (optional) API**.

| Layer | Path | Role |
|-------|------|------|
| Bronze | `data/bronze/` | Raw Kaggle CSVs (`2019-Oct.csv`, `2019-Nov.csv`) |
| Silver | `data/silver/events/` | Cleaned events, Parquet partitioned by date |
| Gold | `data/gold/` | `product_summary`, `product_by_day` (modelling table) |

Target column: `purchases_next_day`. Features are same-day and 7-day clickstream aggregates (`views`, `carts`, `removals`, `purchases`, and the `*_7d` rollups). Config lives in `config.yaml`.

## Setup

```bash
make install
cp .env.example .env   # Kaggle credentials for download
```

Python 3.12+, dependencies in `requirements.txt`. Scripts expect `.venv/bin/python`.

## Pipeline

```bash
make download    # Kaggle → bronze (Oct + Nov)
make clean       # bronze → silver
make explore     # EDA summaries / charts → metadata/
make features    # silver → gold
make train       # E1, E2, E_final (default hyperparameters)
make tune        # random search on E_final train window
make retrain     # E_final with tuned params → data/models/best_model.joblib
make analyze     # error / comparison figures
make api         # FastAPI on :8000
```

`make all` runs the full chain through analyze. `make test` runs pytest. `make dry-run` limits cleaning to two chunks for a quick sanity check.

**Note:** `make clean` deletes and rebuilds silver. Re-download only when bronze files are missing or corrupt.

### Experiments (temporal splits)

| | Train | Test | Results file |
|--|-------|------|----------------|
| E1 | Oct 1–23 | Oct 24–30 | `metadata/model_results.json` |
| E2 | through Oct 30 | Nov 1–7 | `metadata/generalization_results.json` |
| E_final | through Nov 15 | Nov 16–29 | `metadata/final_results.json` (+ `_tuned` after retrain) |

Models: lag-1, 7-day moving average, historical mean, Random Forest, XGBoost, LightGBM. The API serves the best **tree** model from the tuned E_final run (currently Random Forest), even when a baseline wins on MAE.

## API

```bash
make api
# Swagger: http://127.0.0.1:8000/docs
```

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Model loaded + gold date range |
| GET | `/products` | Sample product ids |
| POST | `/predict` | Next-day forecast for `product_id` + `date` (includes actual from gold when available) |
| GET | `/top` | Top-N products by predicted demand for a date |

Feature dates must fall inside the gold calendar (Oct–Nov 2019). This is a demo on historical gold, not a live feed.

## Layout

```
api/           FastAPI app
scripts/       download, clean, explore, features, train, tune, analyze
src/           shared cleaning, training, I/O, config
tests/         pytest
data/          bronze / silver / gold (local; not for git dumps of raw CSV)
metadata/      metrics JSON, figures, best_params, run log
docs/          report source notes (see below)
```

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/research_abstract.md](docs/research_abstract.md) | Abstract / objectives |
| [docs/literature.md](docs/literature.md) | Literature notes |
| [docs/data_layers.md](docs/data_layers.md) | Bronze / silver / gold |
| [docs/prediction_problem.md](docs/prediction_problem.md) | Target, features, models, metrics |
| [docs/findings.md](docs/findings.md) | Results notes (refresh from `metadata/` after a full run) |
| [docs/figures/](docs/figures/) | Mermaid diagrams for methodology |

## Main outputs

- `data/gold/product_by_day.parquet` — modelling grain
- `metadata/model_results.json`, `generalization_results.json`, `final_results.json`, `final_results_tuned.json`
- `metadata/best_params.json`, `best_model_info.json`
- `data/models/best_model.joblib`
- `metadata/figures/` — EDA, SHAP, pred vs actual, residuals, experiment comparison
