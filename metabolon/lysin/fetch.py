import httpx
from dataclasses import dataclass
import re

@dataclass
class BioArticle:
    title: str
    definition: str      # First sentence
    mechanism: str        # Full extract text
    url: str              # Wikipedia URL
    sections: list[dict]  # [{title: str, text: str}, ...] for --full mode

SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
SECTIONS_URL = "https://en.wikipedia.org/api/rest_v1/page/mobile-sections/{title}"
SEARCH_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "lysin/0.1.0 (https://github.com/terry-li-hm; vivesca biology fetcher)"

def _strip_html(text: str) -> str:
    """Strip HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text).strip()

def search_term(term: str, limit: int = 5) -> list[str]:
    """Search Wikipedia for matching article titles."""
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
        params = {
            "action": "opensearch",
            "search": term,
            "limit": limit,
            "format": "json"
        }
        response = client.get(SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if len(data) > 1 and data[1]:
            return data[1]
        return []

def fetch_summary(term: str) -> BioArticle:
    """Fetch Wikipedia summary for a biology term.

    Try exact match first. If 404, search and use best result.
    Raise LookupError if term not found.
    """
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True) as client:
        # Try exact match first
        url = SUMMARY_URL.format(title=term)
        response = client.get(url)
        
        if response.status_code == 404:
            # Fall back to search
            results = search_term(term)
            if not results:
                raise LookupError(f"Term '{term}' not found.")
            
            title = results[0]
            url = SUMMARY_URL.format(title=title)
            response = client.get(url)
            
        if response.status_code != 200:
            raise LookupError(f"Failed to fetch summary for '{term}'. Status: {response.status_code}")
            
        data = response.json()
        
        extract = data.get("extract", "")
        # Detect disambiguation page
        if "may refer to:" in extract.lower() or "may refer to" in extract.lower():
            raise LookupError(f"Term '{term}' is a disambiguation page. Suggestions: {extract}")
            
        title = data.get("title", term)
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        
        # Extract first sentence
        parts = extract.split(". ")
        definition = parts[0] + "." if parts else extract
        if len(parts) == 1 and not extract.endswith("."):
            definition = extract
            
        return BioArticle(
            title=title,
            definition=definition,
            mechanism=extract,
            url=page_url,
            sections=[]
        )

def fetch_sections(title: str) -> list[dict]:
    """Fetch all article sections for --full mode."""
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True) as client:
        url = SECTIONS_URL.format(title=title)
        response = client.get(url)
        if response.status_code != 200:
            return []
            
        data = response.json()
        
        lead_sections = data.get("lead", {}).get("sections", [])
        remaining_sections = data.get("remaining", {}).get("sections", [])
        all_sections_data = lead_sections + remaining_sections
        
        sections = []
        for sec in all_sections_data:
            sec_title = _strip_html(sec.get("line", ""))
            sec_text = _strip_html(sec.get("text", ""))
            if sec_title and sec_text:
                sections.append({
                    "title": sec_title,
                    "text": sec_text
                })
                
        return sections
