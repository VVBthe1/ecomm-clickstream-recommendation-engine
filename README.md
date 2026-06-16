# Clickstream demand analytics

Batch pipeline for e-commerce clickstream: clean events, build features, forecast **next-day product demand**. Layout: **bronze → silver → gold**.

| Layer | Folder | Contents |
|-------|--------|----------|
| Bronze (raw) | `data/bronze/` | Kaggle download |
| Silver (processed) | `data/silver/events/` | Cleaned events (Parquet) |
| Gold (features) | `data/gold/` | `product_summary`, `product_by_day` |

## Setup

```bash
make venv install
cp .env.example .env    # Kaggle API key
```

## Run

```bash
make download   # Kaggle → data/bronze
make clean      # bronze → silver (cleaned events)
make explore    # summaries and charts → metadata/
make features   # silver → gold (product_summary, product_by_day)
make train      # gold → models + metadata/model_results.json
```

Or `make all` for the full chain including training. `make dry-run` processes two chunks only (handy for a quick check). `make test` runs unit tests.

## Outputs

- `data/gold/product_summary.parquet` — per product
- `data/gold/product_by_day.parquet` — per product per day (`purchases_next_day` is the forecast target)
- `metadata/model_results.json` — MAE, RMSE, MAPE, R² by model
- `data/models/` — fitted baselines and ML models

## Documentation

| Location | Purpose |
|----------|---------|
| [`docs/`](docs/) | Report sources committed to Git (see [`docs/README.md`](docs/README.md)) |
| [`workspace/`](workspace/) | Personal WIP — verification workbooks, plans, report drafts (gitignored) |

**Data:** [Kaggle eCommerce behavior](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) — `2019-Oct.csv` in config.
