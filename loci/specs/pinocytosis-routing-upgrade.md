# Spec: pinocytosis smart routing upgrade

## Context

Benchmarked 6 web extraction tools (see `~/epigenome/marks/finding_web_extraction_benchmark_20260401.md`). No single tool wins everywhere. Current pinocytosis uses defuddle → agent-browser, missing the middle tier (Jina, Firecrawl) that handles JS-heavy and paywalled sites.

## Current chain

```
defuddle → agent-browser → error
```

## New chain (4-tier, source-aware)

```
defuddle → jina → firecrawl → agent-browser → error
```

With smart routing: known domains can skip tiers.

## Changes to `~/germline/effectors/pinocytosis`

### 1. Add Jina Reader tier (after defuddle, before Firecrawl)

```python
def _jina(url: str) -> str:
    """Extract via Jina Reader API (free, no auth needed)."""
    import urllib.request
    req = urllib.request.Request(
        f"https://r.jina.ai/{url}",
        headers={"Accept": "text/markdown", "User-Agent": "pinocytosis/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8")
        # Strip Jina metadata header
        import re
        text = re.sub(r'^(?:Title|URL Source|Markdown Content):.*\n?', '', text, flags=re.MULTILINE)
        if len(text) > 100:
            return text
    except Exception:
        pass
    return ""
```

### 2. Add Firecrawl tier (after Jina, before agent-browser)

```python
def _firecrawl(url: str) -> str:
    """Extract via Firecrawl API (1 credit/page). Reserved for paywalled/JS-heavy sites."""
    try:
        import subprocess
        key = subprocess.check_output(
            ["op", "item", "get", "Firecrawl", "--vault", "Agents", "--fields", "credential", "--reveal"],
            timeout=10,
        ).decode().strip()
        if not key:
            return ""
        from firecrawl import FirecrawlApp
        fc = FirecrawlApp(api_key=key)
        doc = fc.scrape(url, formats=["markdown"])
        return doc.markdown or ""
    except Exception:
        return ""
```

### 3. Source-aware routing

Add a domain-based hint system. Known domains can skip directly to the best tier:

```python
# Domains where specific tools are known-best (from benchmark)
DOMAIN_HINTS = {
    # Paywalled — skip straight to Firecrawl
    "ft.com": "firecrawl",
    "bloomberg.com": "firecrawl",
    "wsj.com": "firecrawl",
    # Government — defuddle is cleanest, no need for Jina's noise
    "hkma.gov.hk": "defuddle",
    "sfc.hk": "defuddle",
    "mas.gov.sg": "defuddle",
    # Evident — Firecrawl gets date + more links
    "evidentinsights.com": "firecrawl",
}
```

### 4. Update `fetch_url()` to use 4-tier chain with hints

```python
def fetch_url(url: str) -> dict:
    """Fetch URL content through smart fallback chain."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lstrip("www.")
    
    # Check domain hints for skip-to
    hint = None
    for pattern, tool in DOMAIN_HINTS.items():
        if domain.endswith(pattern):
            hint = tool
            break
    
    # Build chain based on hint
    chain = [
        ("defuddle", _defuddle),
        ("jina", _jina),
        ("firecrawl", _firecrawl),
        ("agent-browser", _agent_browser_eval),
    ]
    
    # If hint, try that tool first
    if hint:
        chain = sorted(chain, key=lambda x: 0 if x[0] == hint else 1)
    
    for name, fn in chain:
        text = fn(url)
        if text:
            return {"success": True, "text": text, "method": name, "url": url}
    
    return {"success": False, "text": "", "method": "none", "url": url,
            "error": "All extraction methods failed"}
```

### 5. Add `--method` flag for manual override

```python
parser.add_argument("--method", "-m", choices=["defuddle", "jina", "firecrawl", "agent-browser"],
                    help="Force specific extraction method")
```

## What NOT to change

- Screenshot functionality — unchanged
- JSON output format — unchanged  
- MCP tool in `pinocytosis.py` — unchanged (it's a different module for overnight summaries)
- The `evident-brief` effector — keeps its own chain (it does index parsing + article formatting that pinocytosis doesn't need)

## Testing

After implementing, verify on these 3 URLs:
```bash
pinocytosis https://evidentinsights.com/bankingbrief/its-not-the-ai-stupid --json
pinocytosis https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/03/20260305-3/ --json  
pinocytosis https://www.ft.com/content/3a3dfe47-4afa-4956-9244-893e5899453b --json
```

Expected methods: evident→firecrawl (domain hint), hkma→defuddle (domain hint), ft→firecrawl (domain hint).
