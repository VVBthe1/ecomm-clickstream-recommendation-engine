# Figure: System architecture

Use in Methodology chapter. Export to PNG via Mermaid Live or VS Code extension.

```mermaid
flowchart TB
  subgraph sources [Data source]
    Kaggle[Kaggle REES46 October clickstream]
  end
  subgraph bronze [Bronze layer]
    Raw[Raw events archive]
  end
  subgraph silver [Silver layer]
    Clean[Clean and validate]
    Events[Events partitioned by date]
  end
  subgraph gold [Gold layer]
    Summary[Product summary table]
    Daily[Product-by-day features]
  end
  subgraph ml [Modelling layer]
    Train[Train models]
    Eval[Evaluation metrics]
  end
  Kaggle --> Raw
  Raw --> Clean --> Events
  Events --> Summary
  Events --> Daily
  Daily --> Train --> Eval
```

**Caption:** Batch architecture — raw clickstream → cleaned events → product-day features → model training and evaluation. API and real-time workers are out of scope.
