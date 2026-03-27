"""Fetch biology for hybridization grounding.

Source hierarchy: UniProt (protein mechanism) → Reactome (pathway context) → Wikipedia (general).
"""

import httpx
from dataclasses import dataclass, field
import re

USER_AGENT = "lysin/0.2.0 (https://github.com/terry-li-hm; vivesca biology fetcher)"


@dataclass
class BioArticle:
    title: str
    definition: str
    mechanism: str
    url: str
    sections: list[dict] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _strip_pubmed_refs(text: str) -> str:
    """Remove inline PubMed references like (PubMed:12345678)."""
    return re.sub(r"\s*\(PubMed:\d+(?:,\s*PubMed:\d+)*\)", "", text)


# ---------------------------------------------------------------------------
# UniProt
# ---------------------------------------------------------------------------

_UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
_UNIPROT_FIELDS = "accession,protein_name,cc_function,cc_catalytic_activity,cc_domain,cc_subunit,cc_pathway"


def _fetch_uniprot(term: str) -> BioArticle | None:
    """Search UniProt for a human protein by gene name or keyword."""
    queries = [
        f"gene_exact:{term} AND organism_id:9606",
        f"gene:{term} AND organism_id:9606",
        f"{term} AND organism_id:9606",
    ]
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0) as client:
        for q in queries:
            resp = client.get(
                _UNIPROT_SEARCH,
                params={"query": q, "format": "json", "fields": _UNIPROT_FIELDS, "size": "1"},
            )
            if resp.status_code != 200:
                continue
            results = resp.json().get("results", [])
            if not results:
                continue

            r = results[0]
            accession = r.get("primaryAccession", "")
            name = (
                r.get("proteinDescription", {})
                .get("recommendedName", {})
                .get("fullName", {})
                .get("value", term)
            )

            sections: list[dict] = []
            definition = ""

            for c in r.get("comments", []):
                ct = c.get("commentType", "")
                if ct == "FUNCTION":
                    texts = [_strip_pubmed_refs(t["value"]) for t in c.get("texts", []) if t.get("value")]
                    if texts:
                        definition = texts[0].split(". ")[0] + "."
                        sections.append({"title": "Function", "text": " ".join(texts)})
                elif ct == "CATALYTIC ACTIVITY":
                    rxn = c.get("reaction", {})
                    rxn_name = rxn.get("name", "")
                    ec = rxn.get("ecNumber", "")
                    if rxn_name:
                        label = f"Catalytic activity (EC {ec})" if ec else "Catalytic activity"
                        sections.append({"title": label, "text": rxn_name})
                elif ct == "DOMAIN":
                    texts = [_strip_pubmed_refs(t["value"]) for t in c.get("texts", []) if t.get("value")]
                    for t in texts:
                        sections.append({"title": "Domain", "text": t})
                elif ct == "SUBUNIT":
                    texts = [_strip_pubmed_refs(t["value"]) for t in c.get("texts", []) if t.get("value")]
                    if texts:
                        sections.append({"title": "Subunit interactions", "text": " ".join(texts)})

            if not sections:
                continue

            mechanism = "\n\n".join(f"**{s['title']}:** {s['text']}" for s in sections)

            return BioArticle(
                title=name,
                definition=definition or name,
                mechanism=mechanism,
                url=f"https://www.uniprot.org/uniprotkb/{accession}",
                sections=sections,
                sources=["UniProt"],
            )
    return None


# ---------------------------------------------------------------------------
# Reactome
# ---------------------------------------------------------------------------

_REACTOME_SEARCH = "https://reactome.org/ContentService/search/query"
_REACTOME_QUERY = "https://reactome.org/ContentService/data/query/{stId}"


def _fetch_reactome(term: str) -> BioArticle | None:
    """Search Reactome for a pathway by keyword."""
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0) as client:
        resp = client.get(
            _REACTOME_SEARCH,
            params={"query": term, "species": "Homo sapiens", "types": "Pathway", "rows": "3"},
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        entries = []
        for group in data.get("results", []):
            entries.extend(group.get("entries", []))
        if not entries:
            return None

        # Take best match
        entry = entries[0]
        st_id = entry.get("stId", "")
        name = _strip_html(entry.get("name", term))

        # Fetch pathway detail
        detail_resp = client.get(_REACTOME_QUERY.format(stId=st_id))
        if detail_resp.status_code != 200:
            return None

        detail = detail_resp.json()
        summation = detail.get("summation", [])
        if not summation:
            return None

        text = _strip_html(summation[0].get("text", ""))
        if not text:
            return None

        definition = text.split(". ")[0] + "." if ". " in text else text

        return BioArticle(
            title=f"{name} (pathway)",
            definition=definition,
            mechanism=text,
            url=f"https://reactome.org/content/detail/{st_id}",
            sections=[{"title": "Pathway summary", "text": text}],
            sources=["Reactome"],
        )
    return None


# ---------------------------------------------------------------------------
# Wikipedia (fallback)
# ---------------------------------------------------------------------------

_WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_WIKI_SECTIONS = "https://en.wikipedia.org/api/rest_v1/page/mobile-sections/{title}"
_WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"


def _search_wikipedia(term: str, limit: int = 5) -> list[str]:
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
        params = {"action": "opensearch", "search": term, "limit": limit, "format": "json"}
        resp = client.get(_WIKI_SEARCH, params=params)
        resp.raise_for_status()
        data = resp.json()
        if len(data) > 1 and data[1]:
            return data[1]
        return []


def _fetch_wikipedia(term: str) -> BioArticle | None:
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True) as client:
        url = _WIKI_SUMMARY.format(title=term)
        resp = client.get(url)

        if resp.status_code == 404:
            results = _search_wikipedia(term)
            if not results:
                return None
            url = _WIKI_SUMMARY.format(title=results[0])
            resp = client.get(url)

        if resp.status_code != 200:
            return None

        data = resp.json()
        extract = data.get("extract", "")
        if "may refer to:" in extract.lower():
            return None

        title = data.get("title", term)
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

        parts = extract.split(". ")
        definition = parts[0] + "." if parts else extract

        # Fetch sections
        sections: list[dict] = []
        sec_resp = client.get(_WIKI_SECTIONS.format(title=title))
        if sec_resp.status_code == 200:
            sec_data = sec_resp.json()
            for sec in sec_data.get("remaining", {}).get("sections", []):
                sec_title = _strip_html(sec.get("line", ""))
                sec_text = _strip_html(sec.get("text", ""))
                if sec_title and sec_text and len(sec_text) > 50:
                    sections.append({"title": sec_title, "text": sec_text})

        return BioArticle(
            title=title,
            definition=definition,
            mechanism=extract,
            url=page_url,
            sections=sections,
            sources=["Wikipedia"],
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_summary(term: str) -> BioArticle:
    """Fetch biology grounding for a term. Tries UniProt → Reactome → Wikipedia."""
    # Try UniProt first (best for proteins/enzymes)
    article = _fetch_uniprot(term)
    if article:
        return article

    # Try Reactome (best for biological processes/pathways)
    article = _fetch_reactome(term)
    if article:
        return article

    # Fall back to Wikipedia
    article = _fetch_wikipedia(term)
    if article:
        return article

    raise LookupError(f"Term '{term}' not found in UniProt, Reactome, or Wikipedia.")


def fetch_sections(title: str) -> list[dict]:
    """Fetch Wikipedia sections (legacy --full support)."""
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True) as client:
        url = _WIKI_SECTIONS.format(title=title)
        resp = client.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        sections = []
        for sec in data.get("remaining", {}).get("sections", []):
            sec_title = _strip_html(sec.get("line", ""))
            sec_text = _strip_html(sec.get("text", ""))
            if sec_title and sec_text:
                sections.append({"title": sec_title, "text": sec_text})
        return sections
