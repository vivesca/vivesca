---
name: pinocytosis
description: Fetch web content reliably — route by cargo type, fallback chain, session hygiene. "browse", "check this URL", "fetch page"
user_invocable: false
---

# pinocytosis -- web content ingestion

Single entrypoint for all web content. CLI handles the deterministic fallback chain. Skill adds judgment only for routing edge cases.

## CLI

```bash
pinocytosis <url>              # URL → defuddle → agent-browser eval
pinocytosis -s <query>         # Quick web search (Perplexity sonar)
pinocytosis -s -d <query>      # Deep search (Perplexity sonar-pro)
pinocytosis --screenshot <url> # Screenshot to ~/tmp/
pinocytosis --json <url>       # Structured output
```

## When the skill adds judgment

The CLI handles 90% of cases. Invoke skill logic only for:

1. **Pre-flight auth detection.** Known auth-gated domains (LinkedIn, X, Google Docs, WeChat, Xiaohongshu, DocuSign) — skip defuddle, go straight to agent-browser with session/profile.
2. **Search tier selection.** Quick (`-s`) for factual lookups. Deep (`-s -d`) only when synthesis quality justifies ~$0.01. Research tier (`chemotaxis_research` MCP tool) only when depth justifies ~$0.40.
3. **Silent auth failure.** If extracted text contains "sign in" / "log in" / "create account", the CLI returns empty — escalate to agent-browser with profile.
4. **Content type routing.** Video → `video-digest`. PDF → `pdf-extract`. WeChat → `summarize --extract-only`. These bypass the standard chain.

## Fallback chain (encoded in CLI)

```
defuddle (fast, clean markdown)
  ↓ empty or auth-gated
agent-browser close → open → wait → eval innerText
  ↓ failed
error (ask user to paste)
```

## What dissolved into this

- **pseudopod** — was "deep page ingestion." Now just `pinocytosis <url>`.
- **noesis** — was "search tiering." Now `pinocytosis -s` / `-s -d` + judgment for tier selection.
- **WebFetch** — CC built-in, still available but pinocytosis CLI is preferred (defuddle is cleaner).
- **defuddle skill** — the Obsidian skill taught how to use defuddle CLI. Now it's just a backend inside pinocytosis.

## MCP tools (unchanged)

- `endocytosis_extract` — agent-browser wrapper (tools/pseudopod.py)
- `endocytosis_screenshot` — page capture
- `endocytosis_check_auth` — auth state detection
- `chemotaxis_search/ask/research` — Perplexity API (tools/noesis.py)

These stay as MCP tools for agents that need them directly. The CLI and skill are the preferred interface.
