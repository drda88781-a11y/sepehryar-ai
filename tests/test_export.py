"""
Tests for DataExporter offline formats (CSV UTF-8 BOM, JSON, Markdown).
"""
import json
from pathlib import Path
from app.tools.export import DataExporter


def test_export_to_csv_with_utf8_sig(tmp_path: Path):
    target = tmp_path / "test_export.csv"
    data = [
        {"کد کالا": "1001", "نام کالا": "روغن موتور", "موجودی": 15},
        {"کد کالا": "1002", "نام کالا": "فیلتر هوا", "موجودی": 50},
    ]

    saved_path = DataExporter.export_to_csv(data, target)
    assert Path(saved_path).exists()

    # Read raw bytes to verify UTF-8 BOM (\xef\xbb\xbf)
    raw_bytes = target.read_bytes()
    assert raw_bytes.startswith(b"\xef\xbb\xbf")

    # Read as text
    text = target.read_text(encoding="utf-8-sig")
    assert "روغن موتور" in text
    assert "1001" in text


def test_export_to_json(tmp_path: Path):
    target = tmp_path / "test_export.json"
    data = [
        {"id": 1, "name": "شرکت سپهر", "balance": 15000000}
    ]

    saved = DataExporter.export_to_json(data, target)
    assert Path(saved).exists()
    content = json.loads(target.read_text(encoding="utf-8"))
    assert content[0]["name"] == "شرکت سپهر"


def test_export_to_markdown_table():
    data = [
        {"ID": 1, "Name": "کالا الف", "Qty": 10},
        {"ID": 2, "Name": "کالا ب", "Qty": 20},
    ]
    md = DataExporter.export_to_markdown_table(data)
    assert "| ID | Name | Qty |" in md
    assert "| --- | --- | --- |" in md
    assert "کالا الف" in md
