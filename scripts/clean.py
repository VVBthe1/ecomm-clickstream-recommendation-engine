#!/usr/bin/env python3

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze_files import resolve_bronze_csvs
from src.cleaning import clean_chunk
from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir


def main() -> None:
    cfg = load_config()
    bronze_dir = resolve_path(cfg["paths"]["bronze_dir"])
    bronze_paths = resolve_bronze_csvs(bronze_dir, cfg["dataset"])
    silver_dir = ensure_dir(resolve_path(cfg["paths"]["silver_dir"]))
    chunk_size = int(cfg["dataset"]["chunk_size"])
    max_chunks = cfg["dataset"].get("max_chunks")
    valid_types = frozenset(cfg["processing"]["valid_event_types"])

    for bronze_path in bronze_paths:
        if not bronze_path.exists():
            raise FileNotFoundError(
                f"Bronze file missing: {bronze_path}\nRun: make download"
            )

    # Wipe once, then write all months into the same silver tree
    if silver_dir.exists():
        shutil.rmtree(silver_dir)
    ensure_dir(silver_dir)

    total_in = 0
    total_out = 0
    for bronze_path in bronze_paths:
        rows_in, rows_out, chunks = _clean_file(
            bronze_path,
            silver_dir,
            chunk_size,
            max_chunks,
            valid_types,
        )
        total_in += rows_in
        total_out += rows_out
        print(f"{bronze_path.name}: {rows_out:,} rows ({chunks} chunks)")

    append_run_log(
        resolve_path(cfg["paths"]["metadata_dir"]),
        "clean",
        {
            "bronze": [str(p) for p in bronze_paths],
            "silver": str(silver_dir),
            "rows_in": total_in,
            "rows_out": total_out,
        },
    )
    print(f"{silver_dir}: {total_out:,} rows total")


def _clean_file(
    bronze_path: Path,
    silver_dir: Path,
    chunk_size: int,
    max_chunks: int | None,
    valid_types: frozenset[str],
) -> tuple[int, int, int]:
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
            print(f"  {bronze_path.name} chunk {i}: {rows_out:,} rows")
        if max_chunks and i >= max_chunks:
            break

    if parts:
        _flush_parts(parts, silver_dir)

    return rows_in, rows_out, chunks_written


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
