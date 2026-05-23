# Prediction problem

Forecast **next-day purchase count** per product.

- Grain: `product_id`, `date`
- Features: same-day activity + 7-day rollups in `product_by_day.parquet`
- Target: `purchases_next_day`
- Validation: hold out the last week of the window (time-based split)
