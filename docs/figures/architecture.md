# Figure: System architecture

Use in Methodology chapter. Export to PNG via Mermaid Live or VS Code extension.

```mermaid
flowchart TB
  subgraph sources [Data sources]
    Kaggle[Kaggle REES46 Oct CSV]
  end
  subgraph bronze [Bronze raw store]
    Raw[data/bronze/2019-Oct.csv]
  end
  subgraph processing [Processing engine]
    Clean[scripts/clean.py]
    Silver[data/silver/events Parquet]
  end
  subgraph features [Feature store gold]
    Build[scripts/build_features.py]
    Summary[product_summary.parquet]
    Daily[product_by_day.parquet]
  end
  subgraph prediction [Prediction engine]
    Train[scripts/train_models.py]
    Models[data/models/]
    Results[metadata/model_results.json]
  end
  Kaggle --> Raw
  Raw --> Clean --> Silver
  Silver --> Build
  Build --> Summary
  Build --> Daily
  Daily --> Train --> Models
  Train --> Results
```

**Caption:** Batch architecture — raw clickstream → cleaned events → product-day features → model training and evaluation. API and real-time workers are out of scope.
