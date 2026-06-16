# Figure: Preprocessing flow (silver layer)

From `src/cleaning.py` — decision rules applied per chunk.

```mermaid
flowchart TD
  Start[Raw CSV chunk] --> ParseTime[Parse event_time UTC]
  ParseTime --> DropBadTime{Valid timestamp?}
  DropBadTime -->|no| Drop1[Drop row]
  DropBadTime -->|yes| FilterType[Keep view cart remove_from_cart purchase]
  FilterType --> ValidPrice[Numeric price >= 0]
  ValidPrice --> ValidIDs[Valid product category user IDs]
  ValidIDs --> Normalize[Normalize brand category_code session]
  Normalize --> Dedupe[Drop exact duplicates]
  Dedupe --> AddDate[Add date column]
  AddDate --> Parquet[Write silver Parquet by date partition]
```

**Caption:** Silver-layer cleaning rules — invalid timestamps, event types, prices, and IDs are removed; duplicates dropped; events partitioned by date.
