from urllib.parse import urljoin

import httpx
import trafilatura
from bs4 import BeautifulSoup

from epsin.extractors.generic import _is_safe_url, HEADERS, TIMEOUT
from epsin.models import Item, Source


class TheBatchExtractor:
    BASE_URL = "https://www.deeplearning.ai/the-batch/"

    def fetch(self, source: Source, full: bool = False) -> list[Item]:
        url = source.url or self.BASE_URL
        if not _is_safe_url(url):
            return []

        try:
            with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                html = resp.text
        except httpx.HTTPError:
            return []

        soup = BeautifulSoup(html, "html.parser")
        items: list[Item] = []

        # deeplearning.ai uses custom article card selectors
        cards = soup.select(".post-card, .article-card, .batch-item, a[href*='/the-batch/']")
        if not cards:
            cards = soup.select("article a, .card a, h2 a, h3 a")

        for card in cards[:20]:
            heading = card.find(["h2", "h3", "h4"])
            if heading:
                title = heading.get_text().strip()
            else:
                title = card.get_text().strip()

            if not title or len(title) < 10:
                continue

            link = str(card.get("href", "")) if card.name == "a" else ""
            if not link:
                a_tag = card.find("a")
                link = str(a_tag.get("href", "")) if a_tag else ""

            if link and not link.startswith("http"):
                link = urljoin(url, link)

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


def _trafilatura_extract(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(downloaded, output_format="markdown")
            return result or ""
    except Exception:
        pass
    return ""


EXTRACTOR = TheBatchExtractor()
