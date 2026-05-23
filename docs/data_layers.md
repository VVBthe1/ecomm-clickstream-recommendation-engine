# Data layers

**Bronze** — raw download under `data/bronze/`.

**Silver** — cleaned events in `data/silver/events/` (Parquet, by `date`). Built by `scripts/clean.py`.

**Gold** — `product_summary.parquet` and `product_by_day.parquet` under `data/gold/`. Built by `scripts/build_features.py`.

Scripts run in order: `download` → `clean` → `explore` → `build_features` (or `make all`).
