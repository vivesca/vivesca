"""rheotaxis_engine — multi-backend web search with parallel execution.

Named after rheotaxis: orientation in response to current flow.
Multiple sensors triangulate where the current points.

Backends: Perplexity (sonar), Exa, Tavily, Serper.
Credentials via importin (macOS Keychain → env vars).
"""

from __future__ import annotations

import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

# Reuse Perplexity backend
from . import chemotaxis_engine


@dataclass
class SearchResult:
    backend: str
    query: str
    results: list[dict]  # [{title, url, snippet}]
    answer: str = ""  # synthesised answer if backend provides one
    error: str = ""


def _get_key(env_var: str) -> str:
    key = os.environ.get(env_var, "")
    if not key:
        raise ValueError(f"{env_var} not set — run eval $(importin)")
    return key


def search_perplexity(query: str, timeout: int = 30) -> SearchResult:  # noqa: ARG001
    """Perplexity sonar — fast, synthesised answer with citations."""
    try:
        answer = chemotaxis_engine.recall(query)
        return SearchResult(
            backend="perplexity",
            query=query,
            results=[],
            answer=answer,
        )
    except Exception as e:
        return SearchResult(backend="perplexity", query=query, results=[], error=str(e))


def search_exa(query: str, timeout: int = 15) -> SearchResult:
    """Exa — neural search, good for finding specific entities/locations."""
    try:
        key = _get_key("EXA_API_KEY")
        body = json.dumps({
            "query": query,
            "numResults": 5,
        }).encode()
        req = urllib.request.Request(
            "https://api.exa.ai/search",
            data=body,
            headers={
                "x-api-key": key,
                "Content-Type": "application/json",
                "accept": "application/json",
                "User-Agent": "rheotaxis/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        results = []
        for r in data.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": (r.get("text", "") or "")[:300],
            })
        return SearchResult(backend="exa", query=query, results=results)
    except Exception as e:
        return SearchResult(backend="exa", query=query, results=[], error=str(e))


def search_tavily(query: str, timeout: int = 15) -> SearchResult:
    """Tavily — search API built for AI agents, returns answer + results."""
    try:
        key = _get_key("TAVILY_API_KEY")
        body = json.dumps({
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 5,
        }).encode()
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        results = []
        for r in data.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:300],
            })
        return SearchResult(
            backend="tavily",
            query=query,
            results=results,
            answer=data.get("answer", ""),
        )
    except Exception as e:
        return SearchResult(backend="tavily", query=query, results=[], error=str(e))


def search_serper(query: str, timeout: int = 15) -> SearchResult:
    """Serper — Google SERP results, good for local/maps queries."""
    try:
        key = _get_key("SERPER_API_KEY")
        body = json.dumps({
            "q": query,
            "num": 5,
        }).encode()
        req = urllib.request.Request(
            "https://google.serper.dev/search",
            data=body,
            headers={
                "X-API-KEY": key,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        results = []
        for r in data.get("organic", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", "")[:300],
            })
        # Include knowledge graph if present
        kg = data.get("knowledgeGraph", {})
        answer = ""
        if kg:
            answer = f"{kg.get('title', '')}: {kg.get('description', '')}"
        return SearchResult(
            backend="serper",
            query=query,
            results=results,
            answer=answer,
        )
    except Exception as e:
        return SearchResult(backend="serper", query=query, results=[], error=str(e))


_BACKENDS = {
    "perplexity": search_perplexity,
    "exa": search_exa,
    "tavily": search_tavily,
    "serper": search_serper,
}


def parallel_search(
    query: str,
    backends: Optional[list[str]] = None,
    timeout: int = 20,
) -> list[SearchResult]:
    """Search all backends in parallel. Returns list of SearchResults."""
    if backends is None:
        backends = list(_BACKENDS.keys())

    with ThreadPoolExecutor(max_workers=len(backends)) as pool:
        futures = {
            pool.submit(_BACKENDS[b], query, timeout): b
            for b in backends
            if b in _BACKENDS
        }
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    return results


def multi_query_search(
    queries: list[str],
    backends: Optional[list[str]] = None,
    timeout: int = 20,
) -> dict[str, list[SearchResult]]:
    """Run multiple query framings across all backends.

    Returns {query: [SearchResult, ...]} for each query.
    """
    if backends is None:
        backends = list(_BACKENDS.keys())

    all_results: dict[str, list[SearchResult]] = {}
    with ThreadPoolExecutor(max_workers=len(queries) * len(backends)) as pool:
        futures = {}
        for q in queries:
            for b in backends:
                if b in _BACKENDS:
                    future = pool.submit(_BACKENDS[b], q, timeout)
                    futures[future] = q
        for future in as_completed(futures):
            q = futures[future]
            if q not in all_results:
                all_results[q] = []
            all_results[q].append(future.result())
    return all_results


def format_results(results: list[SearchResult]) -> str:
    """Format SearchResults into readable text."""
    lines = []
    for r in results:
        lines.append(f"## {r.backend} ({r.query})")
        if r.error:
            lines.append(f"  ERROR: {r.error}")
            continue
        if r.answer:
            lines.append(f"  Answer: {r.answer}")
        for hit in r.results:
            lines.append(f"  - {hit['title']}")
            lines.append(f"    {hit['url']}")
            if hit['snippet']:
                lines.append(f"    {hit['snippet'][:150]}")
        if not r.answer and not r.results:
            lines.append("  (no results)")
        lines.append("")
    return "\n".join(lines)
