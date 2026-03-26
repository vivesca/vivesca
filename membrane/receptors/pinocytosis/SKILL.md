---
name: pinocytosis
description: Fetch web content reliably — route by cargo type, fallback chain, session hygiene. "browse", "check this URL", "fetch page"
user_invocable: false
---

# pinocytosis -- web content fetching

Fetches content from a URL. For web search, use noesis.

## CLI

```bash
pinocytosis <url>              # URL → defuddle → agent-browser eval
pinocytosis --screenshot <url> # Screenshot to ~/tmp/
pinocytosis --json <url>       # Structured output
```

## When the skill adds judgment

The CLI handles 90% of cases. Invoke skill logic only for:

1. **Pre-flight auth detection.** Known auth-gated domains (LinkedIn, X, Google Docs, WeChat, Xiaohongshu, DocuSign) — skip defuddle, go straight to agent-browser with session/profile.
2. **Silent auth failure.** If extracted text contains "sign in" / "log in" / "create account", the CLI returns empty — escalate to agent-browser with profile.
3. **Content type routing.** Video → `video-digest`. PDF → `pdf-extract`. WeChat → `summarize --extract-only`. These bypass the standard chain.

## Fallback chain (encoded in CLI)

```
defuddle --markdown (fast, clean)
  ↓ empty, short, or auth-gated
agent-browser close → open → wait → eval innerText
  ↓ failed
error (ask user to paste)
```

## What dissolved into this

- **pseudopod** — was "deep page ingestion." Now just `pinocytosis <url>`.
- **WebFetch** — CC built-in, still available but pinocytosis CLI is preferred (defuddle is cleaner).
- **defuddle skill** — now a backend inside pinocytosis.

## MCP tools (unchanged)

- `endocytosis_extract` — agent-browser wrapper (tools/pseudopod.py)
- `endocytosis_screenshot` — page capture
- `endocytosis_check_auth` — auth state detection

These stay as MCP tools for agents that need them directly.
