import csv
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

LOGGER = logging.getLogger("gmaps_scraper.exporters")

def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def export_to_json(records: Iterable[Dict[str, object]], path: Path) -> Path:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(list(records), f, ensure_ascii=False, indent=2)
    return path

def export_to_csv(records: Iterable[Dict[str, object]], path: Path) -> Path:
    _ensure_parent(path)
    records_list: List[Dict[str, object]] = list(records)
    if not records_list:
        # Create an empty file with headers only
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Business Name",
                    "Business Address",
                    "Website",
                    "Phone",
                    "Emails",
                    "Facebook",
                    "Instagram",
                    "Twitter",
                    "LinkedIn",
                    "TikTok",
                    "YouTube",
                ]
            )
        return path

    headers = list(records_list[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in records_list:
            writer.writerow(row)
    return path

def export_to_excel(records: Iterable[Dict[str, object]], path: Path) -> Path:
    _ensure_parent(path)
    df = pd.DataFrame(list(records))
    df.to_excel(path, index=False)
    return path

def export_records(
    records: Iterable[Dict[str, object]],
    fmt: str,
    output_dir: Path,
    base_filename: str,
) -> Path:
    fmt = fmt.lower()
    if fmt == "json":
        target = output_dir / f"{base_filename}.json"
        LOGGER.debug("Exporting JSON to %s", target)
        return export_to_json(records, target)
    if fmt == "csv":
        target = output_dir / f"{base_filename}.csv"
        LOGGER.debug("Exporting CSV to %s", target)
        return export_to_csv(records, target)
    if fmt == "excel":
        target = output_dir / f"{base_filename}.xlsx"
        LOGGER.debug("Exporting Excel to %s", target)
        return export_to_excel(records, target)

    raise ValueError(f"Unsupported export format: {fmt}")