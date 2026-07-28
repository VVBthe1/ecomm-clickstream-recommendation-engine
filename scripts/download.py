#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze_files import assert_valid_zip, resolve_bronze_csv
from src.config import load_config, resolve_path
from src.io_utils import append_run_log, ensure_dir


def main() -> None:
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Download bronze CSVs from Kaggle")
    parser.add_argument(
        "--file",
        action="append",
        dest="files",
        help="Specific bronze filename (repeatable). Default: all from config.",
    )
    args = parser.parse_args()

    cfg = load_config()
    bronze_dir = ensure_dir(resolve_path(cfg["paths"]["bronze_dir"]))
    slug = cfg["dataset"]["kaggle_slug"]
    files = args.files or cfg["dataset"].get("bronze_files") or [
        cfg["dataset"]["bronze_file"]
    ]

    for bronze_file in files:
        _download_one(cfg, bronze_dir, slug, bronze_file)


def _kaggle_prefix() -> list[str]:
    """Prefer venv's kaggle CLI next to this Python; fall back to python -m kaggle."""
    sibling = Path(sys.executable).with_name("kaggle")
    if sibling.exists():
        return [str(sibling)]
    return [sys.executable, "-m", "kaggle"]


def _load_dotenv() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def _download_one(cfg: dict, bronze_dir: Path, slug: str, bronze_file: str) -> None:
    dest_csv = bronze_dir / bronze_file

    if dest_csv.exists() and not zipfile.is_zipfile(dest_csv):
        _log_ok(cfg, dest_csv)
        return

    zip_path = bronze_dir / f"{bronze_file}.zip"
    if zip_path.exists():
        try:
            assert_valid_zip(zip_path)
            _log_ok(cfg, resolve_bronze_csv(bronze_dir, bronze_file))
            return
        except zipfile.BadZipFile as exc:
            print(f"Removing corrupt zip and re-downloading: {exc}", file=sys.stderr)
            zip_path.unlink(missing_ok=True)

    cmd = [
        *_kaggle_prefix(),
        "datasets",
        "download",
        "-d",
        slug,
        "-f",
        bronze_file,
        "-p",
        str(bronze_dir),
        "--force",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "").strip()
        if msg:
            print(msg, file=sys.stderr)
        print(
            f"Failed to download {bronze_file}. "
            "Ensure kaggle is installed in the venv (`make install`) "
            "and credentials are in .env or ~/.kaggle/kaggle.json.",
            file=sys.stderr,
        )
        sys.exit(result.returncode or 1)

    # Kaggle may write either name.csv or name.csv.zip
    if dest_csv.exists() and zipfile.is_zipfile(dest_csv):
        dest_csv.rename(zip_path)
    if zip_path.exists():
        try:
            assert_valid_zip(zip_path)
        except zipfile.BadZipFile as exc:
            print(exc, file=sys.stderr)
            print(
                "Download finished but the zip is corrupt/incomplete. "
                "Delete it and re-run: make download",
                file=sys.stderr,
            )
            sys.exit(1)

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
