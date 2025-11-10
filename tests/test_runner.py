import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Ensure src is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import runner  # type: ignore  # noqa: E402
from extractors.utils_format import BusinessRecord, record_to_dict  # type: ignore  # noqa: E402
from outputs.exporters import export_records  # type: ignore  # noqa: E402

SAMPLE_HTML = """
<html>
  <body>
    <div class="business-result">
      <div class="business-name">Test Business</div>
      <div class="business-address">1 Test Street</div>
      <div class="business-phone">+1 000-000-0000</div>
      <a class="business-website" href="http://example.com">Website</a>
    </div>
  </body>
</html>
"""

class DummyResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None

def test_build_business_records_uses_parser_and_enrichment(monkeypatch):
    # Patch fetch_search_html to avoid real network calls
    monkeypatch.setattr(runner, "fetch_search_html", lambda q, user_agent, timeout: SAMPLE_HTML)

    # Patch enrich_business_records to avoid hitting websites and to verify call
    captured_records: List[BusinessRecord] = []

    def fake_enrich(records: List[BusinessRecord], timeout: int, max_workers: int) -> List[BusinessRecord]:
        captured_records.extend(records)
        return records

    monkeypatch.setattr(runner, "enrich_business_records", fake_enrich)

    settings: Dict[str, Any] = {
        "user_agent": "TestAgent/1.0",
        "request_timeout": 5,
        "enrich_contacts": True,
        "max_workers": 2,
    }

    records = runner.build_business_records("test query", settings)
    assert len(records) == 1
    assert captured_records  # ensure enrich was called

    as_dict = record_to_dict(records[0])
    assert as_dict["Business Name"] == "Test Business"
    assert as_dict["Website"] == "http://example.com"

def test_export_records_creates_files(tmp_path: Path):
    records: List[Dict[str, Any]] = [
        {
            "Business Name": "A",
            "Business Address": "Addr",
            "Website": "http://a.com",
            "Phone": "123",
            "Emails": ["a@example.com"],
            "Facebook": "N/A",
            "Instagram": "N/A",
            "Twitter": "N/A",
            "LinkedIn": "N/A",
            "TikTok": "N/A",
            "YouTube": "N/A",
        }
    ]

    json_path = export_records(records, "json", tmp_path, "test")
    csv_path = export_records(records, "csv", tmp_path, "test")
    xlsx_path = export_records(records, "excel", tmp_path, "test")

    assert json_path.exists()
    assert csv_path.exists()
    assert xlsx_path.exists()