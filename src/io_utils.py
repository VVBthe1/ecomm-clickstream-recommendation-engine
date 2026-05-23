from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_run_log(metadata_dir: Path, stage: str, stats: dict[str, Any]) -> None:
    ensure_dir(metadata_dir)
    log_path = metadata_dir / "run_log.jsonl"
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "stage": stage, **stats}
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def write_profile(metadata_dir: Path, name: str, profile: dict[str, Any]) -> Path:
    ensure_dir(metadata_dir)
    out = metadata_dir / f"{name}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, default=str)
    return out


def read_silver_dataset(silver_dir: Path) -> pd.DataFrame:
    silver_dir = Path(silver_dir)
    if not silver_dir.exists():
        raise FileNotFoundError(silver_dir)
    return pd.read_parquet(silver_dir)
