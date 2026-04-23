import calendar
from datetime import UTC, datetime

import feedparser
import trafilatura

from epsin.models import Item, Source

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Epsin/0.1; +https://github.com/terry-li-hm/epsin)"
}

RSS_URL = "https://simonwillison.net/atom/everything/"


class SimonWillisonExtractor:
    def fetch(self, source: Source, full: bool = False) -> list[Item]:
        feed = feedparser.parse(source.rss or RSS_URL, request_headers=HEADERS)

        items: list[Item] = []
        for entry in feed.entries[:20]:
            title = str(getattr(entry, "title", "")).strip()
            if not title:
                continue

            link = str(getattr(entry, "link", ""))
            date = self._parse_datetime(entry)

            # Simon's entries often have rich summaries — use first sentence
            from bs4 import BeautifulSoup
            import re
            summary_html = getattr(entry, "summary", "")
            if summary_html:
                soup = BeautifulSoup(summary_html, "html.parser")
                text = soup.get_text().replace("\n", " ").strip()
                summary = re.split(r"[.!?]", text)[0].strip()[:120]
            else:
                summary = title[:120]

            # Custom tag extraction: Simon tags entries in categories
            tags = source.tags[:]
            for cat in getattr(entry, "categories", []):
                cat_str = str(cat.get("term", "") if hasattr(cat, "get") else cat).lower()
                if cat_str and cat_str not in tags:
                    tags.append(cat_str)

            content_md = ""
            if full and link:
                content_md = _extract_content(link)

            items.append(Item(
                source=source.name,
                title=title,
                url=link,
                date=date,
                summary=summary,
                tags=tags,
                content_md=content_md,
            ))

        return items

    @staticmethod
    def _parse_datetime(entry: object) -> str:
        for field in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, field, None)
            if parsed:
                try:
                    ts = calendar.timegm(parsed)
                    dt = datetime.fromtimestamp(ts, tz=UTC)
                    return dt.isoformat()
                except (TypeError, OverflowError, OSError):
                    continue
        return ""


def _extract_content(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(downloaded, output_format="markdown")
            return result or ""
    except Exception:
        pass
    return ""


EXTRACTOR = SimonWillisonExtractor()
