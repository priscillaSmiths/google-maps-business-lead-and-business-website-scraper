from typing import List, Optional

from bs4 import BeautifulSoup

from extractors.utils_format import BusinessRecord, make_basic_record

def _text_or_none(element) -> Optional[str]:
    if element is None:
        return None
    text = element.get_text(strip=True)
    return text or None

def parse_maps_results(html: str) -> List[BusinessRecord]:
    """
    Parse business results from a Google Maps / local search HTML page.

    This implementation is intentionally conservative and does not depend on
    brittle class names from Google. It instead expects a generic structure
    that can be reproduced in tests and adapted for real scraping:

        <div class="business-result">
            <div class="business-name">Name</div>
            <div class="business-address">Address</div>
            <div class="business-phone">+1 000-000-0000</div>
            <a class="business-website" href="https://example.com">Website</a>
        </div>

    For real-world usage, you may need to adjust the selectors to match the
    actual HTML structure Google returns in your environment.
    """
    soup = BeautifulSoup(html, "lxml")

    results: List[BusinessRecord] = []

    # Primary path: our friendly "business-result" blocks (used in tests).
    business_nodes = soup.select(".business-result")

    # Fallback: attempt to find generic result-like blocks if none match
    if not business_nodes:
        # This is heuristic and may need tweaking for real-world HTML.
        business_nodes = soup.select('[data-result-type="business"]')

    for node in business_nodes:
        name_el = node.select_one(".business-name")
        if not name_el:
            # Try some heuristics: strong title, aria-label, etc.
            name_el = node.select_one("a[aria-label]") or node.select_one("strong")

        name = _text_or_none(name_el)
        if not name:
            # Skip results we cannot reliably name.
            continue

        address_el = node.select_one(".business-address")
        phone_el = node.select_one(".business-phone")
        website_el = node.select_one("a.business-website")

        address = _text_or_none(address_el)
        phone = _text_or_none(phone_el)
        website = website_el.get("href") if website_el else None

        record = make_basic_record(
            name=name,
            address=address,
            website=website,
            phone=phone,
        )
        results.append(record)

    return results