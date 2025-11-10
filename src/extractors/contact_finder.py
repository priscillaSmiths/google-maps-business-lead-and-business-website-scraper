import concurrent.futures
import logging
import re
from typing import Iterable, List, Optional, Tuple

import requests

from extractors.utils_format import (
    BusinessRecord,
    dedupe_emails,
    normalize_email,
)

LOGGER = logging.getLogger("gmaps_scraper.contact_finder")

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)

SOCIAL_PATTERNS = {
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"']+", re.I),
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"']+", re.I),
    "twitter": re.compile(
        r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[^\s\"']+",
        re.I,
    ),
    "linkedin": re.compile(
        r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/[^\s\"']+",
        re.I,
    ),
    "tiktok": re.compile(r"https?://(?:www\.)?tiktok\.com/[^\s\"']+", re.I),
    "youtube": re.compile(
        r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s\"']+",
        re.I,
    ),
}

def _safe_get(url: str, timeout: int) -> Optional[str]:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; BitbashScraper/1.0; +https://bitbash.dev)"
            )
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.debug("Failed to fetch %s: %s", url, exc)
        return None

def _extract_emails(html: str) -> List[str]:
    emails = [normalize_email(e) for e in EMAIL_REGEX.findall(html)]
    return dedupe_emails(e for e in emails if not e.endswith("@example.com"))

def _extract_social_links(html: str) -> Tuple[
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    profiles = {key: None for key in SOCIAL_PATTERNS.keys()}
    for key, pattern in SOCIAL_PATTERNS.items():
        match = pattern.search(html)
        if match:
            profiles[key] = match.group(0)
    return (
        profiles["facebook"],
        profiles["instagram"],
        profiles["twitter"],
        profiles["linkedin"],
        profiles["tiktok"],
        profiles["youtube"],
    )

def _enrich_single(record: BusinessRecord, timeout: int) -> BusinessRecord:
    if not record.website:
        return record

    html = _safe_get(record.website, timeout=timeout)
    if not html:
        return record

    emails = _extract_emails(html)
    (
        facebook,
        instagram,
        twitter,
        linkedin,
        tiktok,
        youtube,
    ) = _extract_social_links(html)

    # Merge emails
    combined_emails = dedupe_emails(list(record.emails) + emails)

    return BusinessRecord(
        business_name=record.business_name,
        business_address=record.business_address,
        website=record.website,
        phone=record.phone,
        emails=combined_emails,
        facebook=record.facebook or facebook,
        instagram=record.instagram or instagram,
        twitter=record.twitter or twitter,
        linkedin=record.linkedin or linkedin,
        tiktok=record.tiktok or tiktok,
        youtube=record.youtube or youtube,
    )

def enrich_business_records(
    records: Iterable[BusinessRecord],
    timeout: int = 10,
    max_workers: int = 5,
) -> List[BusinessRecord]:
    records_list = list(records)
    LOGGER.info("Enriching %d business records with contact info", len(records_list))

    if not records_list:
        return []

    enriched: List[BusinessRecord] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_record = {
            executor.submit(_enrich_single, record, timeout): record
            for record in records_list
        }
        for future in concurrent.futures.as_completed(future_to_record):
            original = future_to_record[future]
            try:
                new_record = future.result()
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.debug(
                    "Error enriching record %r: %s",
                    original.business_name,
                    exc,
                )
                enriched.append(original)
            else:
                enriched.append(new_record)

    return enriched