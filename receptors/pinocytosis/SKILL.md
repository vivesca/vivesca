---
name: pinocytosis
description: Fetch web content reliably — route by cargo type, fallback chain, session hygiene. "browse", "check this URL", "fetch page"
user_invocable: false
---

# pinocytosis -- web content fetch routing

When fetching content from a URL, follow the routing table at `~/notes/Reference/browser-automation/fetch-routing.md`. Do not improvise.

## Procedure

1. **Pre-flight auth check.** Is the domain in the known-auth list (LinkedIn, X, Google Docs, WeChat, Xiaohongshu) or a known SPA (docsign, docusign, hellosign, pandadoc)? If yes, skip WebFetch — go directly to the right tool.

2. **Route by cargo type:**
   - General web article/docs → WebFetch first
   - JS-rendered SPA → `endocytosis_extract` MCP or agent-browser
   - E-sign / form platform → agent-browser + `eval` to extract form values (WebFetch returns empty forms)
   - WeChat → `summarize --extract-only`
   - Video → `video-digest`
   - Login-required → agent-browser with profile
   - PDF → `pdf-extract`

3. **Follow the fallback chain. Do not skip steps:**
   ```
   WebFetch → Jina Reader → endocytosis_extract → agent-browser → WebSearch → ask user to paste
   ```

4. **Agent-browser hygiene:**
   - Clean lock file before opening: `rm -f ~/.agent-browser-profile/SingletonLock`
   - Always `agent-browser close` when done
   - Sequential over parallel for multi-step extraction
   - Max 2-3 concurrent sessions

5. **Detect silent auth failure.** If WebFetch returns content containing "sign in" / "log in" / "create account", the page is auth-gated — escalate, don't trust the content.

## Principles

- WebFetch is 10x faster than agent-browser. Only escalate on confirmed failure.
- Pre-flight is cheap; retry is expensive.
- Full routing table: `~/notes/Reference/browser-automation/fetch-routing.md`
