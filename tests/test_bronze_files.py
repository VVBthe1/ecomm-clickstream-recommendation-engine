import zipfile
from pathlib import Path

from src.bronze_files import extract_csv_zip, resolve_bronze_csv


def test_extract_csv_zip(tmp_path: Path):
    csv_in = tmp_path / "inner.csv"
    csv_in.write_text("event_time,event_type\n2019-10-01 00:00:00 UTC,view\n")
    zpath = tmp_path / "data.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.write(csv_in, arcname="2019-Oct.csv")
    out = tmp_path / "2019-Oct.csv"
    extract_csv_zip(zpath, out)
    assert out.read_text().startswith("event_time")


def test_resolve_bronze_csv_from_zip(tmp_path: Path):
    bronze = tmp_path / "bronze"
    bronze.mkdir()
    csv_in = bronze / "2019-Oct.csv"
    csv_in.write_text("a,b\n1,2\n")
    zpath = bronze / "2019-Oct.csv.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.write(csv_in, arcname="2019-Oct.csv")
    csv_in.unlink()
    path = resolve_bronze_csv(bronze, "2019-Oct.csv")
    assert path.name == "2019-Oct.csv"
    assert path.exists()
