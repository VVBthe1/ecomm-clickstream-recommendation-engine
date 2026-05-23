from __future__ import annotations

import zipfile
from pathlib import Path


def extract_csv_zip(zip_path: Path, dest_csv: Path) -> Path:
    zip_path = Path(zip_path)
    dest_csv = Path(dest_csv)
    if dest_csv.exists() and dest_csv.stat().st_mtime >= zip_path.stat().st_mtime:
        return dest_csv

    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_members = [
            n for n in zf.namelist()
            if n.lower().endswith(".csv") and not n.startswith("__")
        ]
        if not csv_members:
            raise ValueError(f"No CSV in {zip_path}")
        member = csv_members[0]
        if len(csv_members) > 1:
            stem = dest_csv.name.lower()
            for name in csv_members:
                if Path(name).name.lower() == stem:
                    member = name
                    break
        dest_csv.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, dest_csv.open("wb") as dst:
            while chunk := src.read(8 * 1024 * 1024):
                dst.write(chunk)
    return dest_csv


def resolve_bronze_csv(bronze_dir: Path, bronze_file: str) -> Path:
    bronze_dir = Path(bronze_dir)
    csv_path = bronze_dir / bronze_file
    if csv_path.is_file():
        return csv_path

    zip_path = bronze_dir / f"{bronze_file}.zip"
    if zip_path.is_file():
        return extract_csv_zip(zip_path, csv_path)

    zips = sorted(bronze_dir.glob("*.zip"))
    if len(zips) == 1:
        return extract_csv_zip(zips[0], csv_path)

    raise FileNotFoundError(f"No bronze data in {bronze_dir}. Run: make download")
