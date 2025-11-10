from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional

@dataclass(frozen=True)
class BusinessRecord:
    business_name: str
    business_address: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    emails: List[str]
    facebook: Optional[str]
    instagram: Optional[str]
    twitter: Optional[str]
    linkedin: Optional[str]
    tiktok: Optional[str]
    youtube: Optional[str]

def make_basic_record(
    name: str,
    address: Optional[str] = None,
    website: Optional[str] = None,
    phone: Optional[str] = None,
) -> BusinessRecord:
    return BusinessRecord(
        business_name=name,
        business_address=address,
        website=website,
        phone=phone,
        emails=[],
        facebook=None,
        instagram=None,
        twitter=None,
        linkedin=None,
        tiktok=None,
        youtube=None,
    )

def normalize_email(email: str) -> str:
    return email.strip().lower()

def dedupe_emails(emails: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for e in emails:
        norm = normalize_email(e)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out

def record_to_dict(record: BusinessRecord) -> Dict[str, object]:
    """
    Convert a BusinessRecord into the JSON-friendly schema used in the README.
    """
    data = asdict(record)
    return {
        "Business Name": data["business_name"],
        "Business Address": data["business_address"] or "N/A",
        "Website": data["website"] or "N/A",
        "Phone": data["phone"] or "N/A",
        "Emails": data["emails"] or "N/A",
        "Facebook": data["facebook"] or "N/A",
        "Instagram": data["instagram"] or "N/A",
        "Twitter": data["twitter"] or "N/A",
        "LinkedIn": data["linkedin"] or "N/A",
        "TikTok": data["tiktok"] or "N/A",
        "YouTube": data["youtube"] or "N/A",
    }