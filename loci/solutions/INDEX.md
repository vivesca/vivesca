# Solutions KB Index

Auto-generated. 110 files across 22 categories.

Re-generate: `python3 ~/scripts/generate-solutions-index.py`

## General (46)

- **agent browser local files** — `agent-browser open "file:///path/to/file.html"` fails — it silently upgrades `file://` to `https://file///...` which hi
- **aml terminology cv** — In AML/FinCrime compliance, "suppressing alerts" implies hiding suspicious activity from regulators — literally a compli
- **browser automation comparison** — | Operation | Direct CDP | Playwright Python | agent-browser CLI |
- **cdsw code comprehension via llm** — Writing keyword-matching scripts to extract answers from CDSW codebase produces too much noise. Each iteration returns "
- **claude code custom subagents guide** — Create a subagent only when **at least two** of these properties provide clear value:
- **claude code extension mechanisms** — Six ways to extend Claude Code. Each has a sweet spot. Using the wrong one wastes tokens or adds friction.
- **cncbi technical notes** — > Remove this file after Mar 16 2026 (last day at CNCBI).
- **colorblind safe palettes** — Blue + purple is one of the most commonly confused pairings under protanopia/deuteranopia. Both shift toward similar per
- **consilium streaming gotchas** — Previously, `query_model()` with `stream=verbose` checked `is_thinking_model()` and fell back to non-streaming. Since AL
- **content extraction text before media** — For any content pipeline (podcast digests, article summarization, etc.), always check if **text** is available before do
- **debugging patterns** — Distilled from [obra/superpowers](https://github.com/obra/superpowers) systematic-debugging skill.
- **deepgram nova3 transcription** — The `deepgram-sdk` v5.x completely restructured its API. `PrerecordedOptions` no longer exists as an import. The SDK exp
- **discontinued product specs research** — When a product is fully discontinued (removed from manufacturer site, delisted from Shopify API, never archived by Wayba
- **editing pptx programmatically** — Consolidated from 4 files (Feb 2026 CV editing sessions).
- **foodorder today menu scraping** — How to extract menus from 世通線上自助點餐系統 (foodorder.today POS) via CDP.
- **github pages 404 build mode** — After enabling GitHub Pages via `gh api`, the site returns 404 even though the repo has an `index.html` on main.
- **gmail html attachment virus block** — Attaching an HTML file with a large inline `<script>` block (e.g., embedded SheetJS ~950KB) to a Gmail message triggers 
- **gphotos cli** — CLI tool accessing Google Photos via Chrome CDP, bypassing the dead Photos Library API (readonly scope killed Mar 2025).
- **headshot cropping linkedin** — LinkedIn displays profile photos as a square upload, shown as a circle. Cropping a portrait headshot to a square require
- **hk tram api dead** — The old endpoint `https://www.hktramways.com/nextTram/geteat.php?stop_code=10W` is non-functional. TLS handshake succeed
- **image conversion heic tif to jpg** — ```bash
- **interview learnings** — Giselle (recruiter) pitched DBS Data Governance role as "technical GenAI person to challenge the team." Alison (hiring m
- **job application forms** — Keep a secret GitHub gist with role descriptions, deduplicated skills, and comp expectations. Update after any content c
- **llm agent cost quadratic** — **Source:** "Expensively Quadratic: The LLM Agent Cost Curve" (blog.exe.dev, Feb 2026)
- **mcp vs cli enterprise** — > Created: 2026-02-14
- **oghma session start injection** — Oghma has 10K+ memories but only ~20 are always in context (MEMORY.md). The remaining 201-10,000 are only accessible if 
- **owndays model review** — **Created:** 2026-02-14
- **package registry namespace squatting** — Reserving package names across registries before building. Useful for brand protection when you have a working project (
- **pdf form editing preview gotcha** — When editing fillable PDF forms in macOS Preview, changing one field can silently corrupt adjacent fields. Observed: edi
- **pypdf fill form fields** — Need to programmatically fill fillable PDF forms (e.g. ISACA Verification of Attendance forms).
- **pypi placeholder gotcha** — When securing a PyPI name with a minimal placeholder (0.0.1), `uv tool install <name>` installs the placeholder — which 
- **researcher agent date verification** — Delegated researcher agents confidently misattribute events from Year N-1 to Year N when anniversary coverage appears in
- **rust toolchain setup** — Last updated: 2026-02-15
- **shopify scraping** — Any Shopify store exposes a public JSON API — no auth, no API key needed.
- **skill cli boundary pattern** — When a skill needs both LLM judgment and deterministic logic (scheduling, state management, library access), split into 
- **spaced repetition mode selection** — During GARP RAI quiz session, user failed an MCQ on fairness measures (M3-fairness-measures, 44% accuracy) despite sayin
- **subagent isolation for heavy outputs** — Skills/workflows that run tools returning 10K+ tokens of raw data (chat history, large file reads, search results) bloat
- **synthetic assurance pattern** — When organisations require humans to demonstrate understanding of AI-generated outputs (for compliance, audit, or govern
- **tool gotchas** — Moved from MEMORY.md (Feb 2026). Searchable via oghma and grep. Only load when working on the specific tool.
- **vercel deploy gotchas** — `git push origin main` to GitHub does NOT guarantee Vercel auto-deploys. The Doumei project doesn't have GitHub integrat
- **vercel dev lan testing** — `vercel dev` only binds to `localhost` — no `--listen 0.0.0.0` support. To test from a phone on the same Wi-Fi:
- **waking up api** — ```
- **web scraper parent link pattern** — Modern blog card layouts (Anthropic, Google DeepMind, likely others) wrap the entire card in an `<a>` tag with headings 
- **webfetch sibling cascade error** — When multiple `WebFetch` calls are made in the same tool-call block and one returns a non-2xx status (e.g. 404), **all s
- **workflow specific patterns** — Reference patterns for specific workflows. Lookup on demand — not needed every turn.
- **wrap skill daily note path bug** — The wrap skill wrote session logs to `~/code/vivesca-terry/chromatin/Daily/YYYY-MM-DD.md` but the vault stores daily notes flat at `~/code/vivesca-terry/chromatin/YYY

## Ai Tooling (7)

- **anthropic sdk vs agent sdk** — **Date:** 2026-02-20
- **llm council judge over aggregation** — The frontier-council judge (Claude Opus 4.5) correctly *diagnoses* the situation but *prescribes* too many actions. In a
- **mcp fastmcp lifespan context access** — When using FastMCP's lifespan pattern to share state (e.g., database connections) with tool handlers, the yielded dict i
- **openclaw emfile skill watcher crash** — OpenClaw gateway crashes on startup with `EMFILE: too many open files` errors. The gateway process cannot start, prevent
- **opencode delegation library internals** — When delegating a fix that requires understanding an external library's API (e.g., MCP SDK's Context object), OpenCode/G
- **rust rewrite decisions** — Only rewrite in Rust if the tool is **CPU-bound or startup-sensitive**. Most of Terry's toolkit is I/O/network-bound — R
- **workflows compound missing agents** — Running `/workflows:compound` fails when Claude tries to spawn parallel subagents. The skill describes launching special

## Best Practices (9)

- **compound engineering full cycle oghma** — Oghma v0.2.0 to v0.3.0 development showcased a complete compound engineering cycle: Plan -> Implement -> Review -> Clean
- **compound engineering personal setup** — The compound-engineering plugin from Every provides powerful knowledge compounding — each solved problem makes future pr
- **compound engineering plugin architecture** — The compound-engineering plugin has three component types that serve different purposes:
- **delegation five elements** — From Ethan Mollick's [Management as AI Superpower](https://www.oneusefulthing.org/p/management-as-ai-superpower).
- **multi agent deliberation design** — Multi-agent deliberation systems (where multiple LLMs debate a question) suffer from premature convergence. LLMs are tra
- **multi tool ai architecture scout command centre** — With 5 AI coding tools (Claude Code, OpenCode, Codex, Cursor Agent, OpenClaw), it's unclear how they relate. Without exp
- **polling daemon dedup pattern** — When a daemon polls files for changes (by mtime/size), detects a change, and re-processes the **entire file** — every ex
- **qmd oghma complementary search** — Two local search systems serve AI agents via MCP:
- **token budget audit claude code** — Claude Code sessions carry significant hidden token overhead from the system prompt — CLAUDE.md, git status, MCP server 

## Browser Automation (7)

- **agent browser cdp gotchas** — - v0.5.0 produced `Resource temporarily unavailable (os error 35)` on 8GB Macs under memory pressure
- **agent browser fill vs type** — When using `agent-browser type` on React input fields, the text appears visually but React's internal state doesn't upda
- **agent browser refs shift** — After any `agent-browser` action (click, fill, scroll), the element refs in the snapshot become stale. Using old refs ta
- **agent browser what works** — Tested Feb 2026 on Manulife Workday (v0.9.3, Chrome CDP port 9222, 8GB Mac).
- **password reset via cli** — Reusable chain for resetting forgotten passwords without leaving the terminal.
- **workday anti automation** — Workday career portals (e.g., Manulife `careers.manulife.com`) resist browser automation:
- **xhs requires browser for extraction** — Building an XHS post extractor, the Python script (`requests` + BeautifulSoup) found

## Claude Config (2)

- **ce plugin file locations** — Finding Compound Engineering skill and command source files takes multiple attempts. The plugin is installed via the mar
- **post tool blocking validators** — Pattern from disler/claude-code-hooks-mastery.

## Data Recovery (1)

- **opencode playwright snapshot recovery** — Content extracted via OpenCode + Playwright was saved to `/tmp` files that got deleted. The vault notes only had placeho

## Data Visualization (1)

- **accuracy metrics no data vs zero** — When plotting accuracy metrics (e.g., thumbs up/down feedback), months with **no feedback data** were displayed as **0% 

## Deployment Issues (1)

- **vercel project rename domain alias** — Renaming a Vercel project to get a cleaner `.vercel.app` URL requires multiple steps that aren't obvious.

## Developer Experience (3)

- **gemini 3 flash high config CLI 20260126** — The user wanted to ensure that `opencode` defaults to the **Gemini 3 Flash High** variant. While `opencode` supports a `
- **obsidian vault docs integration System 20260126** — The user wanted to ensure their growing technical knowledge base (`docs/solutions`, `plans`, etc.) was both version-cont
- **opencode hide tool calls** — The OpenCode CLI (powered by gemini-3-flash or other models) displays `tool_call` lines by default (e.g., `tool_call: re

## Frontend Issues (1)

- **safari welcome ordering** — Adding a new welcome line without updating the delays array caused `NaN` timeouts in Safari, which reordered the UI. Com

## Integration Issues (6)

- **gog gmail attachment out flag** — ```bash
- **lfg namespace and sync robustness** — 1. Running `/lfg` failed because the command template hardcoded a legacy namespace `/ralph-wiggum:ralph-loop`.
- **linkedin api cookie auth dead** — Attempted to use the `linkedin-api` Python library (powering OpenClaw's popular `linkedin-cli` skill) to access LinkedIn
- **multi tool history support HistorySkill 20260126** — The existing `history` skill was designed exclusively for Claude Code, scanning only `~/.claude/history.jsonl`. This cre
- **oura mcp initialization OpenCode 20260126** — When attempting to use Oura tools in OpenCode, the following error is returned:
- **tavily mcp invalid api key** — When calling `tavily_tavily_search`, the tool returned:

## Logic Errors (5)

- **diagnose before fixing** — Spent a session flip-flopping on a fix (raw table query → revert → raw table again) because we guessed at the root cause
- **hardcoded project references compound plugin 20260126** — The `compound-docs` skill and related workflows contained hardcoded references to "CORA" (Every's internal project). Thi
- **opencode alias hardcoded model brittleness** — The `o` alias (and related `oc`, `or`) for `opencode` hardcoded a specific model (`opencode/gemini-3-flash`) and variant
- **opencode tui redirection interference 20260126** — The shell alias `o` (an alias for `opencode`) was broken. When invoked, it would either fail to start the TUI correctly 
- **tui interruption shell process substitution developer tools 20260126** — The shell alias `o` (an alias for `opencode`) was broken. When invoked, it would either fail to start the TUI correctly 

## Patterns (7)

- **council routing** — Questions with cognitive, social, or behavioural dimensions have more hidden angles than technical questions. Claude und
- **critical patterns** — **ALWAYS check this file before starting work.** These patterns prevent catastrophic or high-severity issues.
- **cron hygiene** — Two patterns to watch for when reviewing scheduled jobs:
- **llm extraction negative examples** — When building LLM extraction/classification pipelines, negative examples reduce noise more than positive examples improv
- **mcp vs cli vs skill** — Build in this order:
- **polishing trap** — Internal documents with known audiences don't need perfection. Set a ship threshold before starting, not after the 5th e
- **tool constraints over behavioral rules** — > Source: LLM Council deliberation on memory system improvements (2026-02-19)

## Performance Issues (2)

- **mandatory search guard shadow binaries** — tags: [agent-safety, shell-scripting, search-performance]
- **slow root search CLITools 20260126** — date: 2026-01-26

## Runtime Errors (1)

- **brittle vision library failure visual browser skill 20260126** — The `visual-browser` skill, initially implemented using the high-level `browser-use` library, consistently failed with a

## Shell (1)

- **grep rn comment exclusion** — `grep -v "^\s*#"` doesn't exclude Python comments when used with `grep -rn`, because the output format is:

## Skills (3)

- **anthropic skill authoring best practices** — Extracted from official Anthropic documentation, bundled in obra/superpowers.
- **archive article url content archival** — When archiving web articles to Obsidian, external image URLs eventually break (link rot). Need a way to download images 
- **reference skill antipattern** — Reference skills (non-user-invocable, `user_invocable: false`) were designed to separate guidance from action — e.g., `c

## Test Failures (1)

- **oghma v040 release test fixes** — During the Oghma v0.4.0 release, the full test suite revealed multiple failures and one infinite hang caused by behavior

## Testing Patterns (1)

- **persistent test caching 40x speedup 20260126** — The test suite was taking over 2 minutes, creating a slow feedback loop during development. Every test run was making li

## Tooling (1)

- **claude code rate limit history extraction** — Claude Code Max plan has undisclosed weekly limits. Users hit limits without knowing:

## Troubleshooting (2)

- **macos login items removal** — Unwanted applications (AutoGLM and Comet) were launching automatically on system startup. Standard investigation methods
- **opencode startup log suppression CLI 20260126** — Every time the `opencode` CLI (or its alias `o`) is invoked, an informational log message is printed to `stderr` during 

## Workflow Issues (2)

- **check vault before asking** — Claude asks Terry "who is X?" or "what's the context for Y?" when the answer is already in the vault. This wastes Terry'
- **oghma mcp orchestration pattern** — User wants feature work to progress but has competing high-priority tasks (BGV docs, resignation letter, interview prep)
