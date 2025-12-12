import feedparser
from datetime import datetime
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse


def _parse_date(date_str) -> Optional[datetime]:
    try:
        return datetime(*date_str[:6])
    except Exception:
        return None


def _to_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _extract_domain(link: str) -> str:
    try:
        return urlparse(link).netloc
    except Exception:
        return ""


def _normalize_yyyymmdd(date_input: Union[str, datetime]) -> datetime:
    if isinstance(date_input, datetime):
        return date_input
    if isinstance(date_input, str):
        digits = "".join([c for c in date_input if c.isdigit()])
        if len(digits) == 8:
            return datetime.strptime(digits, "%Y%m%d")
    raise ValueError("Tarih formatı YYYYMMDD olmalı (örn: 20251111).")


def fetch_news_tr(company_name: str, start_date: str, end_date: str, limit: int = 100) -> List[Dict]:
    """
    Türkçe Google News RSS araması (hl=tr&gl=TR&ceid=TR:tr) ve tarih filtresi.
    start_date, end_date: YYYYMMDD
    """
    start_dt = _normalize_yyyymmdd(start_date)
    end_dt = _normalize_yyyymmdd(end_date)

    q = company_name.replace(" ", "+")
    google_query = f"\"{q}\"+after:{_to_iso(start_dt)}+before:{_to_iso(end_dt)}"
    url = f"https://news.google.com/rss/search?q={google_query}&hl=tr&gl=TR&ceid=TR:tr"

    feed = feedparser.parse(url)
    results = []

    for entry in feed.entries:
        pub_dt = _parse_date(entry.published_parsed)
        if not pub_dt:
            continue
        if pub_dt < start_dt or pub_dt > end_dt:
            continue

        results.append({
            "title": entry.title,
            "link": entry.link,
            "published": pub_dt.isoformat(),
            "source": _extract_domain(entry.link),
            "language": "tr",
        })
        if len(results) >= limit:
            break

    return results

