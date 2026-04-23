import ipaddress
import socket
from urllib.parse import urlparse

import feedparser
import httpx
import trafilatura

from epsin.models import Item, Source

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Epsin/0.1; +https://github.com/terry-li-hm/epsin)"
}

TIMEOUT = 15


def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        addrs = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _family, _type, _proto, _canonname, sockaddr in addrs:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError, OSError):
        return False
    return True


def _parse_datetime(entry: object) -> str:
    import calendar
    from datetime import UTC, datetime

    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, field, None)
        if parsed:
            try:
                ts = calendar.timegm(parsed)
                dt = datetime.fromtimestamp(ts, tz=UTC)
                return dt.isoformat()
            except (TypeError, OverflowError, OSError):
                continue

    for field in ("published", "updated", "created"):
        raw = getattr(entry, field, "")
        if not raw:
            continue
        from datetime import datetime as _dt
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = _dt.strptime(str(raw).strip(), fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC).isoformat()
            except ValueError:
                continue
    return ""


def _extract_summary(entry: object) -> str:
    from bs4 import BeautifulSoup
    import re

    summary = getattr(entry, "summary", "")
    if not summary:
        return ""
    soup = BeautifulSoup(summary, "html.parser")
    text = soup.get_text().replace("\n", " ").strip()
    first = re.split(r"[.!?。！？]", text)[0].strip()
    return first[:120]


def _fetch_rss(source: Source, full: bool) -> list[Item]:
    if not source.rss:
        return []

    if not _is_safe_url(source.rss):
        return []

    feed = feedparser.parse(source.rss, request_headers=HEADERS)

    if getattr(feed, "bozo", False) and not hasattr(feed, "entries"):
        return []

    items: list[Item] = []
    for entry in feed.entries[:20]:
        title = str(getattr(entry, "title", "")).strip()
        if not title:
            continue

        link = str(getattr(entry, "link", ""))
        date = _parse_datetime(entry)
        summary = _extract_summary(entry)
        content_md = ""

        if full and link and _is_safe_url(link):
            content_md = _trafilatura_extract(link)

        items.append(Item(
            source=source.name,
            title=title,
            url=link,
            date=date,
            summary=summary,
            tags=source.tags,
            content_md=content_md,
        ))

    return items


def _trafilatura_extract(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(downloaded, output_format="markdown")
            return result or ""
    except Exception:
        pass
    return ""


def _fetch_web(source: Source, full: bool) -> list[Item]:
    if not _is_safe_url(source.url):
        return []

    try:
        with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
            resp = client.get(source.url)
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPError:
        return []

    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    soup = BeautifulSoup(html, "html.parser")
    items: list[Item] = []

    for tag in soup.select("article h2 a, article h3 a, h2 a, h3 a, .post-title a")[:20]:
        title = tag.get_text().strip()
        if not title or len(title) < 10:
            continue
        link = str(tag.get("href", ""))
        if link and not link.startswith("http"):
            link = urljoin(source.url, link)

        content_md = ""
        if full and link and _is_safe_url(link):
            content_md = _trafilatura_extract(link)

        items.append(Item(
            source=source.name,
            title=title,
            url=link,
            date="",
            summary=title[:120],
            tags=source.tags,
            content_md=content_md,
        ))

    return items


class GenericExtractor:
    def fetch(self, source: Source, full: bool = False) -> list[Item]:
        items = _fetch_rss(source, full)
        if items:
            return items
        return _fetch_web(source, full)


EXTRACTOR = GenericExtractor()
