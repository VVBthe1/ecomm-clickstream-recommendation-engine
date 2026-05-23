#!/usr/bin/env python3

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cleaning import clean_chunk
from src.config import load_config, resolve_path
from src.bronze_files import resolve_bronze_csv
from src.io_utils import append_run_log, ensure_dir


def main() -> None:
    cfg = load_config()
    bronze_path = resolve_bronze_csv(
        resolve_path(cfg["paths"]["bronze_dir"]),
        cfg["dataset"]["bronze_file"],
    )
    silver_dir = ensure_dir(resolve_path(cfg["paths"]["silver_dir"]))
    chunk_size = int(cfg["dataset"]["chunk_size"])
    max_chunks = cfg["dataset"].get("max_chunks")
    valid_types = frozenset(cfg["processing"]["valid_event_types"])

    if not bronze_path.exists():
        raise FileNotFoundError(
            f"Bronze file missing: {bronze_path}\nRun: make download"
        )

    if silver_dir.exists():
        shutil.rmtree(silver_dir)
    ensure_dir(silver_dir)

    rows_in = 0
    rows_out = 0
    chunks_written = 0
    parts: list[pd.DataFrame] = []
    part_rows = 0
    max_part_rows = chunk_size * 2

    reader = pd.read_csv(bronze_path, chunksize=chunk_size, compression="infer")
    for i, chunk in enumerate(reader, start=1):
        rows_in += len(chunk)
        cleaned = clean_chunk(chunk, valid_event_types=valid_types)
        rows_out += len(cleaned)
        if len(cleaned) == 0:
            if max_chunks and i >= max_chunks:
                break
            continue

        parts.append(cleaned)
        part_rows += len(cleaned)

        if part_rows >= max_part_rows:
            _flush_parts(parts, silver_dir)
            parts = []
            part_rows = 0

        chunks_written = i
        if i == 1 or i % 20 == 0:
            print(f"chunk {i}: {rows_out:,} rows")
        if max_chunks and i >= max_chunks:
            break

    if parts:
        _flush_parts(parts, silver_dir)

    append_run_log(
        resolve_path(cfg["paths"]["metadata_dir"]),
        "clean",
        {
            "bronze": str(bronze_path),
            "silver": str(silver_dir),
            "rows_in": rows_in,
            "rows_out": rows_out,
            "chunks": chunks_written,
        },
    )
    print(f"{silver_dir}: {rows_out:,} rows")


def _flush_parts(parts: list[pd.DataFrame], silver_dir: Path) -> None:
    combined = pd.concat(parts, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], utc=True)
    combined.to_parquet(
        silver_dir,
        partition_cols=["date"],
        engine="pyarrow",
        index=False,
        existing_data_behavior="overwrite_or_ignore",
    )


if __name__ == "__main__":
    main()
