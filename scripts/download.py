#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze_files import resolve_bronze_csv
from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir


def main() -> None:
    cfg = load_config()
    bronze_dir = ensure_dir(resolve_path(cfg["paths"]["bronze_dir"]))
    bronze_file = cfg["dataset"]["bronze_file"]
    slug = cfg["dataset"]["kaggle_slug"]
    dest_csv = bronze_dir / bronze_file

    if dest_csv.exists():
        _log_ok(cfg, dest_csv)
        return

    zip_path = bronze_dir / f"{bronze_file}.zip"
    if zip_path.exists():
        _log_ok(cfg, resolve_bronze_csv(bronze_dir, bronze_file))
        return

    cmd = [
        "kaggle", "datasets", "download",
        "-d", slug, "-f", bronze_file,
        "-p", str(bronze_dir), "--force",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    _log_ok(cfg, resolve_bronze_csv(bronze_dir, bronze_file))


def _log_ok(cfg: dict, path: Path) -> None:
    append_run_log(
        resolve_path(cfg["paths"]["metadata_dir"]),
        "download",
        {"status": "ok", "path": str(path), "bytes": path.stat().st_size},
    )
    print(path)


if __name__ == "__main__":
    main()
