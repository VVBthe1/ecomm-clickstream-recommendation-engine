# Research abstract (Chapter 1)

Copy the block below into the report synopsis / introduction (approx. 300 words).

---

E-commerce platforms record large volumes of clickstream data — views, cart additions, and purchases — yet product-level demand is still often planned using simple historical rules. There is a practical need for reproducible pipelines that transform raw behavioural events into structured features and produce short-horizon demand forecasts using standard machine learning.

Much published work focuses on session-level purchase intent or retail sales forecasting from historical sales alone, without documenting an end-to-end path from public multi-category clickstream logs to product-day demand targets. Few studies combine open customer-data-platform (CDP) event data with comparative tree-based models under strict temporal validation. This dissertation addresses that gap by forecasting **next-day purchase count per product** from clickstream-derived behavioural features.

The methodology follows a batch bronze–silver–gold pipeline. Raw October 2019 events from the REES46/Kaggle open dataset are cleaned and validated (event types, prices, IDs, deduplication), aggregated to product-day grain, and enriched with same-day counts and 7-day rolling sums of views, carts, and purchases. The target variable is `purchases_next_day`. Models include lag-1, 7-day moving-average, and per-product historical-mean baselines, plus Random Forest, XGBoost, and LightGBM regressors. All models are trained on the first 23 labeled calendar days of the window and evaluated on the following 7 days using MAE, RMSE, MAPE, and R². (October-only data yields 30 labeled days: `purchases_next_day` is undefined on Oct 31 without November events.)

Expected outcomes are: a reproducible pipeline (`make all`, `make train`), documented gold feature tables, a comparative metrics table (`metadata/model_results.json`), saved model artifacts, and optional SHAP-based feature explanation for the best tree model. The contribution is a practical, documented link between open clickstream data and product-level demand forecasting — not a new algorithm, but an implementable system with explicit preprocessing, feature definitions, and evaluation against established baselines and peer-reviewed comparison practice.

---

## Measurable objectives

| ID | Objective | Deliverable | Success criterion |
|----|-----------|-------------|-------------------|
| O1 | Reproducible clickstream processing pipeline | Repo + `make all` | Silver and gold parquet from October bronze |
| O2 | Product-day behavioural features | `data/gold/product_by_day.parquet` | Documented schema; rollups at product-day grain |
| O3 | Compare demand forecasting models | `scripts/train_models.py` + `metadata/model_results.json` | Baselines + RF + XGBoost + LightGBM on same split |
| O4 | Evaluate with regression metrics | Results chapter | MAE and RMSE on temporal holdout (last 7 days) |
| O5 | Position work against prior research | Chapter 2 + `docs/literature.md` | Comparative table (15 refs + this work) and gap statement |

## Novelty (proportionate claim)

An end-to-end, reproducible batch pipeline that transforms public multi-category clickstream events into product-day demand features and compares tree-based ML models (with simple baselines) under temporal validation on open CDP data — a combination under-documented in session-intent and sales-only forecasting literature.
