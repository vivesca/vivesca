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
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Perplexity backend (inlined from former chemotaxis_engine)
# ---------------------------------------------------------------------------

_PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
_PERPLEXITY_LOG = Path.home() / "germline" / "loci" / "signals" / "chemotaxis.jsonl"
_PERPLEXITY_MODELS = {
    "quick": "sonar",
    "thorough": "sonar-pro",
    "deep": "sonar-deep-research",
}


def _perplexity_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        raise ValueError("PERPLEXITY_API_KEY not set")
    return key


def _perplexity_query(model: str, query: str, timeout: int = 300) -> str:
    """Query Perplexity API and return synthesised text."""
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Answer accurately based on what you can find. "
                        "If you cannot confirm specific facts, say explicitly "
                        "that you could not confirm it. Distinguish between "
                        "'not found in results' and 'does not exist'."
                    ),
                },
                {"role": "user", "content": query},
            ],
        }
    ).encode()

    req = urllib.request.Request(
        _PERPLEXITY_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {_perplexity_key()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read())

    content = result["choices"][0]["message"]["content"]

    citations = result.get("citations", [])
    if citations:
        content += "\n\nSources:\n" + "\n".join(f"- {c}" for c in citations)

    # Log for sensorium / gradient sensing
    try:
        _PERPLEXITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_PERPLEXITY_LOG, "a") as f:
            f.write(
                json.dumps(
                    {
                        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
                        "model": model,
                        "query": query,
                    }
                )
                + "\n"
            )
    except OSError:
        pass

    return content


# Public Perplexity tier functions (used by enzymes/chemotaxis.py scan tool)
def perplexity_quick(query: str) -> str:
    """Quick search (~$0.006)."""
    return _perplexity_query(_PERPLEXITY_MODELS["quick"], query, timeout=30)


def perplexity_thorough(query: str) -> str:
    """Thorough search (~$0.01)."""
    return _perplexity_query(_PERPLEXITY_MODELS["thorough"], query, timeout=60)


def perplexity_deep(query: str, save_path: str = "") -> str:
    """Deep research (~$0.40). EXPENSIVE."""
    result = _perplexity_query(_PERPLEXITY_MODELS["deep"], query, timeout=300)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            f.write(result)
    return result


_DEPTH_FN = {
    "quick": perplexity_quick,
    "thorough": perplexity_thorough,
    "deep": perplexity_deep,
}


# ---------------------------------------------------------------------------
# Multi-backend types and helpers
# ---------------------------------------------------------------------------

@dataclass
class RheotaxisResult:
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


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

def search_perplexity(query: str, _timeout: int = 30, depth: str = "quick") -> RheotaxisResult:
    """Perplexity — depth selects model tier (quick/thorough/deep)."""
    try:
        fn = _DEPTH_FN.get(depth, perplexity_quick)
        answer = fn(query)
        return RheotaxisResult(
            backend="perplexity",
            query=query,
            results=[],
            answer=answer,
        )
    except Exception as e:
        return RheotaxisResult(backend="perplexity", query=query, results=[], error=str(e))


def search_exa(query: str, timeout: int = 15) -> RheotaxisResult:
    """Exa — neural search, good for finding specific entities/locations."""
    try:
        key = _get_key("EXA_API_KEY")
        body = json.dumps(
            {
                "query": query,
                "numResults": 5,
            }
        ).encode()
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
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": (r.get("text", "") or "")[:300],
                }
            )
        return RheotaxisResult(backend="exa", query=query, results=results)
    except Exception as e:
        return RheotaxisResult(backend="exa", query=query, results=[], error=str(e))


def search_tavily(query: str, timeout: int = 15) -> RheotaxisResult:
    """Tavily — search API built for AI agents, returns answer + results."""
    try:
        key = _get_key("TAVILY_API_KEY")
        body = json.dumps(
            {
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": 5,
            }
        ).encode()
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
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:300],
                }
            )
        return RheotaxisResult(
            backend="tavily",
            query=query,
            results=results,
            answer=data.get("answer", ""),
        )
    except Exception as e:
        return RheotaxisResult(backend="tavily", query=query, results=[], error=str(e))


def search_serper(query: str, timeout: int = 15) -> RheotaxisResult:
    """Serper — Google SERP results, good for local/maps queries."""
    try:
        key = _get_key("SERPER_API_KEY")
        body = json.dumps(
            {
                "q": query,
                "num": 5,
            }
        ).encode()
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
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("link", ""),
                    "snippet": r.get("snippet", "")[:300],
                }
            )
        kg = data.get("knowledgeGraph", {})
        answer = ""
        if kg:
            answer = f"{kg.get('title', '')}: {kg.get('description', '')}"
        return RheotaxisResult(
            backend="serper",
            query=query,
            results=results,
            answer=answer,
        )
    except Exception as e:
        return RheotaxisResult(backend="serper", query=query, results=[], error=str(e))


_BACKENDS = {
    "perplexity": search_perplexity,
    "exa": search_exa,
    "tavily": search_tavily,
    "serper": search_serper,
}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def parallel_search(
    query: str,
    backends: list[str] | None = None,
    depth: str = "quick",
    timeout: int = 20,
) -> list[RheotaxisResult]:
    """Search all backends in parallel. Returns list of RheotaxisResults."""
    if backends is None:
        backends = list(_BACKENDS.keys())

    with ThreadPoolExecutor(max_workers=len(backends)) as pool:
        futures = {}
        for b in backends:
            if b not in _BACKENDS:
                continue
            if b == "perplexity":
                futures[pool.submit(_BACKENDS[b], query, timeout, depth)] = b
            else:
                futures[pool.submit(_BACKENDS[b], query, timeout)] = b
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    return results


def multi_query_search(
    queries: list[str],
    backends: list[str] | None = None,
    depth: str = "quick",
    timeout: int = 20,
) -> dict[str, list[RheotaxisResult]]:
    """Run multiple query framings across all backends.

    Returns {query: [RheotaxisResult, ...]} for each query.
    """
    if backends is None:
        backends = list(_BACKENDS.keys())

    all_results: dict[str, list[RheotaxisResult]] = {}
    with ThreadPoolExecutor(max_workers=len(queries) * len(backends)) as pool:
        futures = {}
        for q in queries:
            for b in backends:
                if b not in _BACKENDS:
                    continue
                if b == "perplexity":
                    future = pool.submit(_BACKENDS[b], q, timeout, depth)
                else:
                    future = pool.submit(_BACKENDS[b], q, timeout)
                futures[future] = q
        for future in as_completed(futures):
            q = futures[future]
            if q not in all_results:
                all_results[q] = []
            all_results[q].append(future.result())
    return all_results


def format_results(results: list[RheotaxisResult]) -> str:
    """Format RheotaxisResults into readable text."""
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
            if hit["snippet"]:
                lines.append(f"    {hit['snippet'][:150]}")
        if not r.answer and not r.results:
            lines.append("  (no results)")
        lines.append("")
    return "\n".join(lines)
