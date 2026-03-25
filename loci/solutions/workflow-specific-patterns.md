# Workflow-Specific Patterns

Reference patterns for specific workflows. Lookup on demand — not needed every turn.

## Browser Scraping

- Chrome CDP requires `--user-data-dir` on macOS — without it, port 9222 silently doesn't bind
- **Use `$HOME/.chrome-debug-profile`** (persistent login) not `/tmp/` (lost on reboot). Alias: `chrome-debug`
- For bulk scraping (>10 pages): write a bash loop + Python parser script, run in background. Zero LLM tokens for the actual work.
- `agent-browser --cdp 9222 snapshot` → content lives between `[level=3]` heading and `Rate Your Confidence` line
- Python extraction pattern: regex on `- paragraph:`, `- text:`, `- strong:`, `- listitem:`, `- emphasis:` prefixes

## PDF Generation

- Chrome headless (`--headless --print-to-pdf`) works for HTML→PDF on macOS when no LaTeX installed
- **Must use `--no-pdf-header-footer`** — default adds URL header + date footer, pushes content to page 2
- Cover letter sweet spot: 11-11.5pt font, line-height 1.5-1.65, padding 60-75px → fills ~80% of A4

## OpenCode Headless Mode

- `opencode run -m opencode/glm-4.7 "prompt"` — use for cron/automation with GLM-4.7 (unlimited via BigModel annual plan)
- Cron scripts in `~/scripts/crons/` deliver weather + Capco briefs to Telegram via `~/scripts/tg-notify.sh`
- Still subject to silent failure on long prompts (>5K chars) — keep prompts focused

## Oghma Maintenance

- **Dedup:** `oghma dedup --threshold 0.92 --execute` (cosine similarity on embeddings, union-find clustering)
- **Noise purge:** `oghma purge-noise --execute` (regex filter for meta-narration, shallow observations)
- Run both periodically — extraction still produces some noise despite improved prompt
- LLM extraction quality: negative examples in prompt ("DO NOT extract these") matter more than positive guidance

## Frontier Council

- **Actual cost ~$0.50/run, not $3.** Old estimator was fiction (`seconds × $0.01`). Now uses OpenRouter `usage.cost`. GPT-5.2 Pro is ~68% of cost. Use for any decision worth >5 min of thought.
- **Background task notification after results shown:** Council runs take 3-7min, sometimes background-complete after results are already presented. Suppress redundant "already read" responses — just stay silent on the late notification.
- **Add constraints to prevent enterprise-grade advice:** Always include "single-user system", "manual processes OK", "simplicity > completeness" or models default to over-architected solutions.

## Physical Store Locations

- **HK mall floor numbers from third-party directories are unreliable.** K11 Musea, Elements, ifc etc. use non-standard numbering (zone names, L vs F vs B). optical852.com listed JINS K11 Musea as "3/F" while launch press said "Level 4" — user couldn't find the store.
- **Verify against Google Maps pin or the mall's own app** before sending someone to a specific floor/shop number. Secondary sources (optical852, hongkong-map, Zaubee) often copy stale or inconsistent data.
- **Always verify store existence from the brand's own store locator** before sending someone there. JINS K11 Musea showed as open on optical852.com and Foursquare but was permanently closed — only the official JINS store locator (JS-rendered, needs agent-browser) reflected reality. Third-party directories lag closures by months/years.
- **JS-rendered store locators:** JINS, OWNDAYS, and many HK retail sites are fully JS-rendered. WebFetch returns nothing useful. Use `agent-browser` to load and snapshot.

## Consilium CLI

- **Shim mismatch:** `uv tool install consilium` puts the package in uv's managed venv, but the mise shim at `~/.local/share/mise/installs/python/3.11.14/bin/consilium` points to system Python 3.11 which can't find the module. Fix: use `uv tool run consilium` instead of bare `consilium`.
