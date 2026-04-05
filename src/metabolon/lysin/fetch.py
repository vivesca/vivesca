"""Fetch biology for hybridization grounding.

Source hierarchy: UniProt (protein mechanism) → Reactome (pathway context) → Wikipedia (general).
"""

import re
from dataclasses import dataclass, field

import httpx

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
_UNIPROT_FIELDS = (
    "accession,protein_name,cc_function,cc_catalytic_activity,cc_domain,cc_subunit,cc_pathway"
)


def _term_in_protein_name(term: str, result: dict) -> bool:
    """Check if the search term appears in the protein's actual name or gene names."""
    term_lower = term.lower()
    # Check protein name
    for name_key in ("recommendedName", "alternativeName"):
        name_obj = result.get("proteinDescription", {}).get(name_key, {})
        full = name_obj.get("fullName", {}).get("value", "")
        if term_lower in full.lower():
            return True
        for short in name_obj.get("shortNames", []):
            if term_lower in short.get("value", "").lower():
                return True
    # Check submitted names
    for sub in result.get("proteinDescription", {}).get("submissionNames", []):
        if term_lower in sub.get("fullName", {}).get("value", "").lower():
            return True
    # Check gene names
    for gene in result.get("genes", []):
        if term_lower in gene.get("geneName", {}).get("value", "").lower():
            return True
        for syn in gene.get("synonyms", []):
            if term_lower in syn.get("value", "").lower():
                return True
    return False


def _fetch_uniprot(term: str) -> BioArticle | None:
    """Search UniProt for a human protein by gene name or keyword."""
    queries = [
        f"gene_exact:{term} AND organism_id:9606 AND reviewed:true",
        f"gene:{term} AND organism_id:9606 AND reviewed:true",
        f"{term} AND organism_id:9606 AND reviewed:true",
        f"{term} AND organism_id:9606",
    ]
    # Broad queries (index 2+) need relevance filtering — they match any
    # protein that mentions the term anywhere in its record.
    _BROAD_QUERY_INDEX = 2

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0) as client:
        for qi, q in enumerate(queries):
            resp = client.get(
                _UNIPROT_SEARCH,
                params={"query": q, "format": "json", "fields": _UNIPROT_FIELDS, "size": "5"},
            )
            if resp.status_code != 200:
                continue
            results = resp.json().get("results", [])
            if not results:
                continue

            # For broad queries, find the first result where the term
            # actually appears in the protein/gene name (not just description).
            if qi >= _BROAD_QUERY_INDEX:
                r = None
                for candidate in results:
                    if _term_in_protein_name(term, candidate):
                        r = candidate
                        break
                if r is None:
                    continue
            else:
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
                    texts = [
                        _strip_pubmed_refs(t["value"])
                        for t in c.get("texts", [])
                        if t.get("value")
                    ]
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
                    texts = [
                        _strip_pubmed_refs(t["value"])
                        for t in c.get("texts", [])
                        if t.get("value")
                    ]
                    for t in texts:
                        sections.append({"title": "Domain", "text": t})
                elif ct == "SUBUNIT":
                    texts = [
                        _strip_pubmed_refs(t["value"])
                        for t in c.get("texts", [])
                        if t.get("value")
                    ]
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
# QuickGO (Gene Ontology)
# ---------------------------------------------------------------------------

_QUICKGO_SEARCH = "https://www.ebi.ac.uk/QuickGO/services/ontology/go/search"


def _fetch_quickgo(term: str) -> BioArticle | None:
    """Search Gene Ontology via QuickGO for biological process definitions."""
    with httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=15.0
    ) as client:
        resp = client.get(_QUICKGO_SEARCH, params={"query": term, "limit": "5"})
        if resp.status_code != 200:
            return None

        results = resp.json().get("results", [])
        if not results:
            return None

        # Prefer biological_process, then any match
        best = None
        for r in results:
            if r.get("aspect") == "biological_process":
                best = r
                break
        if best is None:
            best = results[0]

        go_id = best.get("id", "")
        name = best.get("name", term)
        defn = best.get("definition", {}).get("text", "")
        if not defn:
            return None

        synonyms = [s.get("name", "") for s in best.get("synonyms", []) if s.get("name")]
        children = [c.get("name", "") for c in best.get("children", []) if c.get("name")]

        sections: list[dict] = [{"title": "GO definition", "text": defn}]
        if synonyms:
            sections.append({"title": "Synonyms", "text": ", ".join(synonyms[:10])})
        if children:
            sections.append({"title": "Subtypes", "text": ", ".join(children[:10])})

        mechanism = "\n\n".join(f"**{s['title']}:** {s['text']}" for s in sections)

        return BioArticle(
            title=f"{name} ({go_id})",
            definition=defn.split(". ")[0] + "." if ". " in defn else defn,
            mechanism=mechanism,
            url=f"https://www.ebi.ac.uk/QuickGO/term/{go_id}",
            sections=sections,
            sources=["GO"],
        )
    return None


# ---------------------------------------------------------------------------
# MyGene.info
# ---------------------------------------------------------------------------

_MYGENE_QUERY = "https://mygene.info/v3/query"


def _fetch_mygene(term: str) -> BioArticle | None:
    """Search MyGene.info for protein summaries by common name."""
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0) as client:
        resp = client.get(
            _MYGENE_QUERY,
            params={
                "q": term,
                "species": "human",
                "fields": "name,summary,symbol,pathway.reactome",
                "size": "3",
            },
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            return None

        # Pick the hit whose name/symbol best matches the term
        term_lower = term.lower()
        best = hits[0]
        for hit in hits:
            name = hit.get("name", "").lower()
            symbol = hit.get("symbol", "").lower()
            if term_lower in name or term_lower == symbol:
                best = hit
                break

        name = best.get("name", term)
        symbol = best.get("symbol", "")
        summary = best.get("summary", "")
        if not summary:
            return None

        sections: list[dict] = [{"title": "Summary", "text": summary}]

        # Extract Reactome pathways
        pathways = best.get("pathway", {}).get("reactome", [])
        if isinstance(pathways, dict):
            pathways = [pathways]
        if pathways:
            pw_names = [p.get("name", "") for p in pathways[:8] if p.get("name")]
            if pw_names:
                sections.append({"title": "Pathways", "text": ", ".join(pw_names)})

        definition = summary.split(". ")[0] + "." if ". " in summary else summary
        title = f"{name} ({symbol})" if symbol else name
        mechanism = "\n\n".join(f"**{s['title']}:** {s['text']}" for s in sections)

        return BioArticle(
            title=title,
            definition=definition,
            mechanism=mechanism,
            url=f"https://mygene.info/v3/gene/{best.get('_id', '')}",
            sections=sections,
            sources=["MyGene"],
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

        # Take best match, but verify relevance
        entry = entries[0]
        st_id = entry.get("stId", "")
        name = _strip_html(entry.get("name", term))

        # Skip if the pathway name doesn't contain any word from the search term
        term_words = {w.lower() for w in term.split() if len(w) > 2}
        name_lower = name.lower()
        if term_words and not any(w in name_lower for w in term_words):
            return None

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
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True
    ) as client:
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


def _looks_like_gene(term: str) -> bool:
    """Heuristic: gene/protein names are typically short, uppercase, or have digits."""
    t = term.strip()
    # All-caps or mostly caps with digits (DNMT1, TP53, BRCA2)
    if re.match(r"^[A-Z][A-Z0-9]{1,10}$", t):
        return True
    # Known protein name patterns (lowercase with digits)
    if re.match(r"^[a-z]+\d+[a-z]?$", t, re.IGNORECASE):
        return True
    # Process/concept suffixes → NOT a gene
    _PROCESS_SUFFIXES = (
        "osis",
        "esis",
        "tion",
        "sion",
        "meant",
        "ance",
        "ence",
        "ism",
        "lysozyme",
        "trophy",
        "plasia",
        "kinesis",
        "stasis",
    )
    if any(t.lower().endswith(suf) for suf in _PROCESS_SUFFIXES):
        return False
    # Single word, no spaces, short — might be a gene/protein
    return bool(" " not in t and len(t) <= 15)


def _merge_articles(articles: list[BioArticle]) -> BioArticle:
    """Merge results from multiple sources into one combined article."""
    if len(articles) == 1:
        return articles[0]

    # Use the most specific source for title/definition (UniProt > Reactome > Wikipedia)
    primary = articles[0]
    all_sources = []
    all_sections = list(primary.sections)
    mechanism_parts = [primary.mechanism]

    for article in articles[1:]:
        all_sources.extend(article.sources)
        # Add non-duplicate sections from other sources
        existing_titles = {s["title"] for s in all_sections}
        for sec in article.sections:
            source_label = article.sources[0] if article.sources else "?"
            tagged_title = f"{sec['title']} ({source_label})"
            if tagged_title not in existing_titles and sec["title"] not in existing_titles:
                all_sections.append({"title": tagged_title, "text": sec["text"]})
        mechanism_parts.append(f"\n\n--- {', '.join(article.sources)} ---\n\n{article.mechanism}")

    return BioArticle(
        title=primary.title,
        definition=primary.definition,
        mechanism="\n".join(mechanism_parts),
        url=primary.url,
        sections=all_sections,
        sources=primary.sources + all_sources,
    )


def fetch_summary(term: str) -> BioArticle:
    """Fetch biology grounding from all sources in parallel, merge results."""
    from concurrent.futures import ThreadPoolExecutor

    is_gene = _looks_like_gene(term)

    # Route by term type, query all relevant sources in parallel
    if is_gene:
        fetchers = [_fetch_uniprot, _fetch_mygene, _fetch_reactome, _fetch_wikipedia]
    else:
        fetchers = [_fetch_quickgo, _fetch_reactome, _fetch_wikipedia]

    with ThreadPoolExecutor(max_workers=len(fetchers)) as pool:
        futures = {pool.submit(fn, term): fn.__name__ for fn in fetchers}
        results = []
        for future in futures:
            try:
                article = future.result(timeout=20)
                if article:
                    results.append(article)
            except Exception:
                pass

    if not results:
        raise LookupError(f"Term '{term}' not found in UniProt, Reactome, or Wikipedia.")

    # Sort: most specific first
    source_priority = {"UniProt": 0, "MyGene": 1, "GO": 2, "Reactome": 3, "Wikipedia": 4}
    results.sort(key=lambda a: source_priority.get(a.sources[0], 9))

    return _merge_articles(results)


def fetch_sections(title: str) -> list[dict]:
    """Fetch Wikipedia sections (legacy --full support)."""
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True
    ) as client:
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
