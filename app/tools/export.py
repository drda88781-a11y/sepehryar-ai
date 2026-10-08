"""
Offline Data Export Engine for Sepehryar AI Engine.
Exports query results and reports to CSV (UTF-8 BOM for Persian Excel), JSON, and Markdown tables.
"""
import csv
import json
from pathlib import Path
from typing import Any, Optional
from app.core.logger import get_logger

logger = get_logger("tools.export")


class DataExporter:
    """Exports structured database results to various offline formats."""

    @classmethod
    def export_to_csv(cls, rows: list[dict[str, Any]], filepath: Path) -> str:
        """
        Export rows to CSV with UTF-8 BOM encoding for perfect Persian character display in Excel.
        """
        if not rows:
            filepath.write_text("", encoding="utf-8-sig")
            return str(filepath.resolve())

        filepath.parent.mkdir(parents=True, exist_ok=True)
        headers = list(rows[0].keys())

        with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        logger.info(f"Exported {len(rows)} rows to CSV at {filepath}")
        return str(filepath.resolve())

    @classmethod
    def export_to_json(cls, rows: list[dict[str, Any]], filepath: Path, indent: int = 2) -> str:
        """Export rows to JSON file with Persian characters preserved."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=indent, default=str)

        logger.info(f"Exported {len(rows)} rows to JSON at {filepath}")
        return str(filepath.resolve())

    @classmethod
    def export_to_markdown_table(cls, rows: list[dict[str, Any]], max_rows: int = 50) -> str:
        """Convert list of row dictionaries into a formatted Markdown table."""
        if not rows:
            return "_هیچ داده‌ای یافت نشد._"

        headers = list(rows[0].keys())
        header_line = "| " + " | ".join(headers) + " |"
        separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"

        data_lines = []
        for r in rows[:max_rows]:
            vals = [str(r.get(h, "")).replace("|", "\\|") for h in headers]
            data_lines.append("| " + " | ".join(vals) + " |")

        if len(rows) > max_rows:
            data_lines.append(f"_نمایش {max_rows} ردیف از مجموع {len(rows)} ردیف_")

        return "\n".join([header_line, separator_line] + data_lines)


data_exporter = DataExporter()
