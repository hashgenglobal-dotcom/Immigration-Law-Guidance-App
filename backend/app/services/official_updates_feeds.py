"""Fetch official update items from whitelisted government sources."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

_USER_AGENT = "SourcePath-Updates/1.0 (immigration official announcements; +https://github.com)"


@dataclass(frozen=True)
class FeedItem:
    publisher: str
    external_id: str
    title: str
    official_url: str
    published_at: datetime
    raw_excerpt: str | None


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_rss(xml_text: str, publisher: str) -> list[FeedItem]:
    items: list[FeedItem] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    channel = root.find("channel")
    if channel is None:
        channel = root

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        guid_el = item.find("guid")
        desc_el = item.find("description")
        date_el = item.find("pubDate")

        title = (title_el.text or "").strip() if title_el is not None else ""
        link = (link_el.text or "").strip() if link_el is not None else ""
        if not title or not link:
            continue

        guid = (guid_el.text or link).strip() if guid_el is not None else link
        excerpt = _strip_html(desc_el.text or "") if desc_el is not None and desc_el.text else None
        if excerpt and len(excerpt) > 1200:
            excerpt = excerpt[:1200] + "…"

        published = datetime.now(timezone.utc)
        if date_el is not None and date_el.text:
            try:
                published = parsedate_to_datetime(date_el.text.strip())
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass

        items.append(
            FeedItem(
                publisher=publisher,
                external_id=guid[:512],
                title=title[:1000],
                official_url=link[:2000],
                published_at=published,
                raw_excerpt=excerpt,
            )
        )
    return items


async def fetch_rss(url: str, publisher: str, *, timeout: float = 30.0) -> list[FeedItem]:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
        return _parse_rss(resp.text, publisher)


async def fetch_federal_register_immigration(*, timeout: float = 45.0) -> list[FeedItem]:
    """USCIS-related documents from Federal Register API (JSON)."""
    url = (
        "https://www.federalregister.gov/api/v1/documents.json"
        "?conditions[term]=immigration"
        "&conditions[agencies][]=u-s-citizenship-and-immigration-services"
        "&per_page=20"
        "&order=newest"
    )
    items: list[FeedItem] = []
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
        data = resp.json()

    for doc in data.get("results", []):
        title = (doc.get("title") or "").strip()
        html_url = doc.get("html_url") or doc.get("pdf_url")
        if not title or not html_url:
            continue
        pub = doc.get("publication_date") or doc.get("effective_on")
        try:
            published = datetime.strptime(pub, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            published = datetime.now(timezone.utc)

        abstract = (doc.get("abstract") or doc.get("body") or "")[:1200]
        abstract = _strip_html(abstract) if abstract else None
        doc_number = doc.get("document_number") or html_url

        items.append(
            FeedItem(
                publisher="federal_register",
                external_id=str(doc_number)[:512],
                title=title[:1000],
                official_url=str(html_url)[:2000],
                published_at=published,
                raw_excerpt=abstract,
            )
        )
    return items


WHITELISTED_FEEDS: list[tuple[str, str]] = [
    ("uscis", "https://www.uscis.gov/news/rss/news-releases"),
    ("dhs", "https://www.dhs.gov/news-releases/rss.xml"),
]


async def fetch_all_whitelisted() -> list[FeedItem]:
    """Fetch all configured feeds; skip failures per source."""
    out: list[FeedItem] = []
    for publisher, url in WHITELISTED_FEEDS:
        try:
            out.extend(await fetch_rss(url, publisher))
        except (httpx.HTTPError, OSError):
            continue
    try:
        out.extend(await fetch_federal_register_immigration())
    except (httpx.HTTPError, OSError, ValueError):
        pass
    return out


def content_hash(title: str, url: str, excerpt: str | None) -> str:
    payload = f"{title}|{url}|{excerpt or ''}"
    return hashlib.sha256(payload.encode()).hexdigest()
