import sys
from pathlib import Path

# Ensure src is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extractors.maps_parser import parse_maps_results  # type: ignore  # noqa: E402
from extractors.utils_format import record_to_dict  # type: ignore  # noqa: E402

SAMPLE_HTML = """
<html>
  <body>
    <div class="business-result">
      <div class="business-name">Sunset Dental Group</div>
      <div class="business-address">1234 Sunset Blvd, Los Angeles, CA</div>
      <div class="business-phone">+1 310-555-1234</div>
      <a class="business-website" href="http://sunsetdental.com">Website</a>
    </div>
    <div class="business-result">
      <div class="business-name">Oceanview Dentistry</div>
      <div class="business-address">456 Ocean Ave, Los Angeles, CA</div>
      <div class="business-phone">+1 310-555-5678</div>
      <a class="business-website" href="http://oceanviewdentistry.com">Website</a>
    </div>
  </body>
</html>
"""

def test_parse_maps_results_basic():
    records = parse_maps_results(SAMPLE_HTML)
    assert len(records) == 2

    first = record_to_dict(records[0])
    assert first["Business Name"] == "Sunset Dental Group"
    assert first["Business Address"] == "1234 Sunset Blvd, Los Angeles, CA"
    assert first["Website"] == "http://sunsetdental.com"
    assert first["Phone"] == "+1 310-555-1234"

    second = record_to_dict(records[1])
    assert second["Business Name"] == "Oceanview Dentistry"
    assert second["Business Address"] == "456 Ocean Ave, Los Angeles, CA"