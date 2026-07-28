from __future__ import annotations

import zipfile
from pathlib import Path


def assert_valid_zip(zip_path: Path) -> None:
    """Raise clearly if path is missing, empty, or not a readable zip (e.g. truncated download)."""
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise FileNotFoundError(f"Zip not found: {zip_path}")
    if zip_path.stat().st_size == 0:
        raise zipfile.BadZipFile(f"Empty zip (re-download): {zip_path}")
    if not zipfile.is_zipfile(zip_path):
        raise zipfile.BadZipFile(
            f"Not a valid zip (incomplete/corrupt download?): {zip_path} "
            f"({zip_path.stat().st_size} bytes). Delete it and re-run download."
        )


def extract_csv_zip(zip_path: Path, dest_csv: Path) -> Path:
    zip_path = Path(zip_path)
    dest_csv = Path(dest_csv)
    if (
        dest_csv.exists()
        and not zipfile.is_zipfile(dest_csv)
        and dest_csv.stat().st_mtime >= zip_path.stat().st_mtime
    ):
        return dest_csv

    assert_valid_zip(zip_path)
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
    if csv_path.is_file() and zipfile.is_zipfile(csv_path):
        # Kaggle often saves a zip archive as "<name>.csv" without extracting.
        zip_path = bronze_dir / f"{bronze_file}.zip"
        if not zip_path.exists():
            csv_path.rename(zip_path)
        elif csv_path.resolve() != zip_path.resolve():
            csv_path.unlink()
        return extract_csv_zip(zip_path, csv_path)

    if csv_path.is_file():
        return csv_path

    zip_path = bronze_dir / f"{bronze_file}.zip"
    if zip_path.is_file():
        return extract_csv_zip(zip_path, csv_path)

    zips = sorted(bronze_dir.glob("*.zip"))
    if len(zips) == 1:
        return extract_csv_zip(zips[0], csv_path)

    raise FileNotFoundError(f"No bronze data in {bronze_dir}. Run: make download")


def resolve_bronze_csvs(bronze_dir: Path, cfg_dataset: dict) -> list[Path]:
    """Resolve one or more bronze CSVs from config (bronze_files or bronze_file)."""
    bronze_dir = Path(bronze_dir)
    files = cfg_dataset.get("bronze_files")
    if not files:
        files = [cfg_dataset["bronze_file"]]
    return [resolve_bronze_csv(bronze_dir, name) for name in files]