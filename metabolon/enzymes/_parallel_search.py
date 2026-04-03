from __future__ import annotations

"""elencho — parallel AI research orchestrator.

Runs query through multiple search tools in parallel, synthesises
agreements and disagreements. Absorbed from ~/code/elencho/.

Tools:
  elencho — parallel research with synthesis
"""

import asyncio
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Internal module — no MCP tool decorator. Called by rheotaxis.


# --- Types ---

@dataclass
class ToolResult:
    tool: str
    query: str
    result: str
    citations: list[str] = field(default_factory=list)
    cost: float = 0.0
    latency_s: float = 0.0
    error: Optional[str] = None


# --- Binary resolution ---

def _find_bin(name: str, *fallbacks: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    for fb in fallbacks:
        p = Path(fb).expanduser()
        if p.exists():
            return str(p)
    return name


# --- Tool runners (async) ---

async def _run_tool(
    name: str, binary: str, args: list[str],
    cost: float, timeout: float = 120.0,
) -> ToolResult:
    """Run a CLI tool async, return ToolResult."""
    start = time.time()
    try:
        proc = await asyncio.create_subprocess_exec(
            binary, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        latency = time.time() - start
        if proc.returncode != 0:
            return ToolResult(
                tool=name, query=args[-1] if args else "",
                result="", cost=cost, latency_s=latency,
                error=stderr.decode().strip() or f"exit {proc.returncode}",
            )
        return ToolResult(
            tool=name, query=args[-1] if args else "",
            result=stdout.decode().strip(), cost=cost, latency_s=latency,
        )
    except asyncio.TimeoutError:
        try:
            proc.kill()  # type: ignore[possibly-unbound]
        except Exception:
            pass
        return ToolResult(
            tool=name, query="", result="", cost=cost,
            latency_s=time.time() - start,
            error=f"Timed out after {timeout}s",
        )
    except Exception as e:
        return ToolResult(
            tool=name, query="", result="", cost=cost,
            latency_s=time.time() - start, error=str(e),
        )


async def _run_grok(query: str) -> ToolResult:
    return await _run_tool(
        "grok",
        _find_bin("grok", "~/germline/effectors/grok", "~/bin/grok"),
        [query], cost=0.05,
    )


async def _run_exa(query: str) -> ToolResult:
    return await _run_tool(
        "exa",
        _find_bin("exauro", "~/bin/exauro"),
        ["search", "--n", "5", query], cost=0.01,
    )


async def _run_noesis_search(query: str) -> ToolResult:
    return await _run_tool(
        "noesis_search",
        _find_bin("noesis", "~/.cargo/bin/noesis", "~/bin/noesis"),
        ["search", query], cost=0.006,
    )


async def _run_tavily(query: str) -> ToolResult:
    """Tavily search — wraps rheotaxis engine."""
    start = time.time()
    try:
        from metabolon.organelles.rheotaxis_engine import search_tavily
        result = await asyncio.to_thread(search_tavily, query)
        if result.error:
            return ToolResult(tool="tavily", query=query, result="", cost=0.0,
                              latency_s=time.time() - start, error=result.error)
        parts = []
        if result.answer:
            parts.append(result.answer)
        for r in result.results:
            parts.append(f"**{r.get('title','')}**\n{r.get('url','')}\n{r.get('snippet','')}")
        return ToolResult(tool="tavily", query=query, result="\n\n".join(parts),
                          cost=0.0, latency_s=time.time() - start)
    except Exception as e:
        return ToolResult(tool="tavily", query=query, result="", cost=0.0,
                          latency_s=time.time() - start, error=str(e))


async def _run_serper(query: str) -> ToolResult:
    """Serper search — wraps rheotaxis engine."""
    start = time.time()
    try:
        from metabolon.organelles.rheotaxis_engine import search_serper
        result = await asyncio.to_thread(search_serper, query)
        if result.error:
            return ToolResult(tool="serper", query=query, result="", cost=0.0,
                              latency_s=time.time() - start, error=result.error)
        parts = []
        for r in result.results:
            parts.append(f"**{r.get('title','')}**\n{r.get('url','')}\n{r.get('snippet','')}")
        return ToolResult(tool="serper", query=query, result="\n\n".join(parts),
                          cost=0.0, latency_s=time.time() - start)
    except Exception as e:
        return ToolResult(tool="serper", query=query, result="", cost=0.0,
                          latency_s=time.time() - start, error=str(e))


async def _run_zhipu(query: str) -> ToolResult:
    """ZhiPu web_search_prime MCP — uses Coding Plan MCP quota (4K/mo on Max)."""
    start = time.time()
    api_key = os.environ.get("ZHIPU_API_KEY", "")
    if not api_key:
        return ToolResult(tool="zhipu", query=query, result="", cost=0.0,
                          latency_s=0.0, error="ZHIPU_API_KEY not set")
    try:
        # MCP streamable-http requires init → tools/call with session ID
        import urllib.request

        base = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        # Step 1: Initialize session
        init_body = json.dumps({
            "jsonrpc": "2.0", "id": "init", "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "rheotaxis", "version": "1.0"}}
        }).encode()
        req = urllib.request.Request(base, data=init_body, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            init_text = resp.read().decode()
            session_id = resp.headers.get("Mcp-Session-Id", "")

        # Step 2: Call tool with session
        call_body = json.dumps({
            "jsonrpc": "2.0", "id": "1", "method": "tools/call",
            "params": {
                "name": "web_search_prime",
                "arguments": {"search_query": query}
            }
        }).encode()
        call_headers = {**headers, "Mcp-Session-Id": session_id}
        req2 = urllib.request.Request(base, data=call_body, headers=call_headers)
        with urllib.request.urlopen(req2, timeout=30) as resp2:
            raw = resp2.read().decode()

        # Parse SSE response
        for line in raw.split("\n"):
            if line.startswith("data:"):
                data = json.loads(line[5:])
                content_list = data.get("result", {}).get("content", [])
                text = "\n".join(c.get("text", "") for c in content_list if c.get("type") == "text")
                if text:
                    return ToolResult(tool="zhipu", query=query, result=text,
                                     cost=0.0, latency_s=time.time() - start)

        return ToolResult(tool="zhipu", query=query, result=raw[:500],
                          cost=0.0, latency_s=time.time() - start)
    except Exception as e:
        return ToolResult(tool="zhipu", query=query, result="", cost=0.0,
                          latency_s=time.time() - start, error=str(e))


def _zhipu_search(query: str, model: str = "glm-4-flash") -> str:
    """ZhiPu web search via direct API. Used by mode=glm (GLM-5.1) and as backend (glm-4-flash)."""
    import urllib.request
    api_key = os.environ.get("ZHIPU_API_KEY", "")
    if not api_key:
        raise ValueError("ZHIPU_API_KEY not set")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "tools": [{"type": "web_search", "web_search": {"enable": True}}],
    }).encode()
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


async def _run_firecrawl(query: str) -> ToolResult:
    """Firecrawl search — returns full markdown content, not just snippets."""
    start = time.time()
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        return ToolResult(
            tool="firecrawl", query=query, result="", cost=0.0,
            latency_s=0.0, error="FIRECRAWL_API_KEY not set",
        )
    try:
        import urllib.request
        body = json.dumps({"query": query, "limit": 3}).encode()
        req = urllib.request.Request(
            "https://api.firecrawl.dev/v1/search",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        results = []
        for item in data.get("data", []):
            results.append(f"**{item.get('title','')}**\n{item.get('url','')}\n{item.get('description','')[:300]}")
        return ToolResult(
            tool="firecrawl", query=query, result="\n\n".join(results),
            cost=0.0, latency_s=time.time() - start,
        )
    except Exception as e:
        return ToolResult(
            tool="firecrawl", query=query, result="", cost=0.0,
            latency_s=time.time() - start, error=str(e),
        )


async def _run_jina(query: str) -> ToolResult:
    """Jina search — free tier, uses curl (urllib returns 403 with Bearer auth)."""
    start = time.time()
    api_key = os.environ.get("JINA_API_KEY", "")
    if not api_key:
        return ToolResult(
            tool="jina", query=query, result="", cost=0.0,
            latency_s=0.0, error="JINA_API_KEY not set",
        )
    try:
        import urllib.parse
        encoded = urllib.parse.quote(query)
        proc = await asyncio.create_subprocess_exec(
            "curl", "-s", f"https://s.jina.ai/{encoded}",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Accept: application/json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30.0)
        data = json.loads(stdout.decode())
        results = []
        for item in data.get("data", []):
            results.append(f"**{item.get('title','')}**\n{item.get('url','')}\n{item.get('description','')[:200]}")
        return ToolResult(
            tool="jina", query=query, result="\n\n".join(results),
            cost=0.0, latency_s=time.time() - start,
        )
    except Exception as e:
        return ToolResult(
            tool="jina", query=query, result="", cost=0.0,
            latency_s=time.time() - start, error=str(e),
        )


async def _run_noesis_research(query: str) -> ToolResult:
    return await _run_tool(
        "noesis_research",
        _find_bin("noesis", "~/.cargo/bin/noesis", "~/bin/noesis"),
        ["research", query], cost=0.40, timeout=300.0,
    )


async def _run_websearch(query: str) -> ToolResult:
    claude_bin = _find_bin("claude")
    env = {
        k: v for k, v in os.environ.items()
        if k not in ("CLAUDECODE", "ANTHROPIC_API_KEY")
    }
    start = time.time()
    try:
        proc = await asyncio.create_subprocess_exec(
            claude_bin, "--print",
            f"Use WebSearch to research: {query}. Return only the key findings with source URLs.",
            "--allowedTools", "WebSearch",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120.0)
        latency = time.time() - start
        if proc.returncode != 0:
            return ToolResult(
                tool="websearch", query=query, result="",
                cost=0.0, latency_s=latency, error=f"exit {proc.returncode}",
            )
        return ToolResult(
            tool="websearch", query=query,
            result=stdout.decode().strip(), cost=0.0, latency_s=latency,
        )
    except Exception as e:
        return ToolResult(
            tool="websearch", query=query, result="",
            cost=0.0, latency_s=time.time() - start, error=str(e),
        )


# --- Logging ---

LOG_FILE = Path.home() / ".local" / "share" / "rheotaxis" / "runs.jsonl"


def _log_run(query: str, results: list[ToolResult]) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "total_cost": sum(r.cost for r in results),
        "tools": [asdict(r) for r in results],
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# --- Report ---

def _report(query: str, results: list[ToolResult]) -> str:
    ok = [r for r in results if not r.error]
    errored = [r for r in results if r.error]
    total = len(results)
    failed = len(errored)

    # If majority of backends failed, return error — partial results are unreliable
    if total > 0 and failed > total / 2:
        backend_names = ", ".join(r.tool for r in errored)
        ok_names = ", ".join(r.tool for r in ok) or "none"
        return (
            f"ERROR: rheotaxis degraded — {failed}/{total} backends failed "
            f"({backend_names}). Only {ok_names} returned results. "
            f"Fix the backends before relying on search."
        )

    lines = []
    for r in ok:
        lines.append(f"## {r.tool} ({r.latency_s:.1f}s)")
        lines.append(r.result)
        lines.append("")
    if errored:
        lines.append(f"*{len(errored)} backends errored: {', '.join(r.tool for r in errored)}*")
    return "\n".join(lines)


# --- Orchestrator ---

async def _run_all(query: str) -> list[ToolResult]:
    tasks = [
        _run_grok(query),
        _run_exa(query),
        _run_noesis_search(query),
        _run_tavily(query),
        _run_serper(query),
        _run_zhipu(query),
        _run_jina(query),
        _run_firecrawl(query),
    ]

    raw = await asyncio.gather(*tasks, return_exceptions=True)
    results = []
    for r in raw:
        if isinstance(r, Exception):
            results.append(ToolResult(tool="unknown", query=query, result="", error=str(r)))
        else:
            results.append(r)

    _log_run(query, results)
    return results


# --- MCP Tool ---

# No @tool decorator — elencho is internal plumbing, not a client-facing tool.
# Called by rheotaxis() default mode.
# Public API: _run_all() and _report().
