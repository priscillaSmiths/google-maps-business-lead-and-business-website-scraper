import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Ensure src directory is on sys.path so namespace packages like `extractors` work
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extractors.maps_parser import parse_maps_results  # type: ignore  # noqa: E402
from extractors.contact_finder import enrich_business_records  # type: ignore  # noqa: E402
from extractors.utils_format import (  # type: ignore  # noqa: E402
    BusinessRecord,
    record_to_dict,
)
from outputs.exporters import export_records  # type: ignore  # noqa: E402

LOGGER = logging.getLogger("gmaps_scraper")

def load_settings(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def load_queries_from_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Inputs file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("inputs.sample.json must contain a JSON array of query objects")
    return data

def fetch_search_html(query: str, user_agent: str, timeout: int) -> str:
    """
    Fetch HTML for a Google Maps / Local Search query.

    NOTE: Real markup may differ and this function may require adjustments
    if Google changes their HTML. It is kept simple on purpose.
    """
    url = "https://www.google.com/maps/search/" + requests.utils.quote(query)
    headers = {"User-Agent": user_agent}
    LOGGER.info("Fetching search HTML for query=%r", query)
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def build_business_records(query: str, settings: Dict[str, Any]) -> List[BusinessRecord]:
    html = fetch_search_html(
        query=query,
        user_agent=settings.get(
            "user_agent",
            "Mozilla/5.0 (compatible; BitbashScraper/1.0; +https://bitbash.dev)",
        ),
        timeout=int(settings.get("request_timeout", 15)),
    )
    records = parse_maps_results(html)

    if not records:
        LOGGER.warning("No business results parsed for query %r", query)

    if settings.get("enrich_contacts", True):
        records = enrich_business_records(
            records,
            timeout=int(settings.get("request_timeout", 15)),
            max_workers=int(settings.get("max_workers", 5)),
        )
    return records

def run_for_query(
    query: str,
    settings: Dict[str, Any],
    fmt: str,
    output_dir: Path,
) -> Path:
    records = build_business_records(query, settings)
    LOGGER.info("Parsed %d business records for %r", len(records), query)
    output_dir.mkdir(parents=True, exist_ok=True)

    sanitized_query = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in query)
    base_name = sanitized_query[:80] or "results"

    output_path = export_records(
        records=[record_to_dict(r) for r in records],
        fmt=fmt,
        output_dir=output_dir,
        base_filename=base_name,
    )
    LOGGER.info("Exported %d records to %s", len(records), output_path)
    return output_path

def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Google Maps Business Lead and Business Website Scraper"
    )
    parser.add_argument(
        "--query",
        help="Single search query, e.g. 'dentists in Los Angeles'.",
    )
    parser.add_argument(
        "--inputs",
        help="Path to JSON file with an array of query objects. Each object must at "
        "least contain a 'query' field and may include a 'format' override.",
    )
    parser.add_argument(
        "--config",
        help="Path to settings JSON file.",
        default=str(SRC_DIR / "config" / "settings.example.json"),
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["csv", "json", "excel"],
        help="Override the default output format (csv, json, excel).",
    )
    parser.add_argument(
        "--output-dir",
        help="Override the output directory defined in the settings file.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv).",
    )
    return parser.parse_args(argv)

def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    configure_logging(args.verbose)

    settings_path = Path(args.config)
    settings = load_settings(settings_path)

    default_fmt = args.fmt or settings.get("default_output_format", "csv")
    if default_fmt not in ("csv", "json", "excel"):
        raise ValueError("default_output_format must be one of: csv, json, excel")

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(settings.get("output_directory", "data/outputs"))

    if not args.query and not args.inputs:
        raise SystemExit("You must provide either --query or --inputs")

    if args.query and args.inputs:
        raise SystemExit("Please provide either --query or --inputs, not both")

    if args.query:
        LOGGER.info("Running single-query scrape")
        run_for_query(args.query, settings, default_fmt, output_dir)
        return

    # Multiple queries from inputs file
    queries = load_queries_from_file(Path(args.inputs))
    for item in queries:
        query = item.get("query")
        if not query:
            LOGGER.warning("Skipping entry without 'query' field: %r", item)
            continue
        fmt = item.get("format", default_fmt)
        LOGGER.info("Running query %r with format %s", query, fmt)
        run_for_query(query, settings, fmt, output_dir)

if __name__ == "__main__":
    main()