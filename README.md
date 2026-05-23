# Clickstream demand analytics

Batch pipeline for e-commerce event data: clean clickstream, build features, then (separately) train models and expose results via API. Layout follows **bronze → silver → gold**.

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
make features   # silver → gold (product tables)
```

Or `make all` for the full chain. `make dry-run` processes two chunks only (handy for a quick check). `make test` runs unit tests.

## Outputs

- `data/gold/product_summary.parquet` — per product
- `data/gold/product_by_day.parquet` — per product per day (`purchases_next_day` is the forecast target)

More detail: `docs/data_layers.md`, `docs/prediction_problem.md`.

**Data:** [Kaggle eCommerce behavior](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) — `2019-Oct.csv` in config.
