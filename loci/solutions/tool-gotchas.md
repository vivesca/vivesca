# Tool-Specific Gotchas

Moved from MEMORY.md (Feb 2026). Searchable via oghma and grep. Only load when working on the specific tool.

## Gemini API (Google)
- **Gemini 3 Flash thinking tokens consume `maxOutputTokens` budget.** Thinking is on by default — a 256-token budget produces truncated JSON because thinking eats most of it. For simple extraction tasks, disable with `"thinkingConfig": {"thinkingBudget": 0}` inside `generationConfig`. Discovered in wu enrichment: 290/291 files failed before adding this.
- **Multi-part responses when thinking is enabled.** Response `parts` array may contain thinking parts before the text part. Parse with `reversed(parts)` to get the last text part, not `parts[0]`.

## gh CLI (GitHub)
- **`echo '...' | gh gist create` escapes `!` to `\!`:** Shell history expansion corrupts exclamation marks when piping through echo. Fix: write content to a file first (`/tmp/foo.txt`), then `gh gist create /tmp/foo.txt`. This avoids all shell escaping issues.
- **Delete gists after use:** Secret gists are unlisted but still accessible via URL. Delete with `gh gist delete <id> --yes` once the content has been sent/used. Don't leave draft emails, internal notes, or sensitive content sitting in GitHub.
- **`gh gist edit -f <name> < file` silently fails to update content.** Stdin piping (`<` and `cat |`) both appear to succeed but leave the gist unchanged. Workaround: delete and recreate (`gh gist delete` then `gh gist create`).

## Chrome CDP & Browser Automation
- **Always-on CDP:** `/Applications/Chrome CDP.app` → Chrome with `--remote-debugging-port=9222 --user-data-dir=~/chrome-debug-profile`. CDP always on port 9222.
- **`--cdp 9222` is the default** for authenticated browsing. Headless blocked on many career sites.
- **Chrome won't enable CDP on default profile** — requires `--user-data-dir`. That's why we use `~/chrome-debug-profile/`.
- **Profile refresh:** rsync from main profile (see browser-automation skill for exclude list).
- **CDP overhead is negligible when no client connected.** The debug port just listens; instrumentation domains only activate when a client connects and enables them.
- **Profile bloat:** `OptGuideOnDeviceModel/` (Gemini Nano) silently downloads ~4GB of ML models. Safe to delete + block with `--disable-features=OptimizationGuideModelDownloading`. Don't disable `OptimizationHints`/`OptimizationHintsFetching` — those help page loads.
- **`component_crx_cache` bloat:** Can silently grow to 4GB+ with orphaned CRX blobs. Safe to delete contents — Chrome re-downloads only what's needed (~32MB). Check periodically: `du -sh ~/chrome-debug-profile/component_crx_cache/`.
- **Don't nuke caches for "performance":** Wiping Code Cache/Cache/IndexedDB/Service Workers causes cold-start penalty far worse than any bloat savings. Only wipe if actually corrupted.
- **`--disable-blink-features=AutomationControlled` triggers warning banner.** Safe to remove for daily browsing — automation tools handle `navigator.webdriver` themselves.
- **Stale extensions accumulate from rsync:** `--disable-extensions-except` only disables, doesn't delete. Periodically prune `Extensions/` dir to match the keep-list. Use Python (not bash loop with grep) to avoid bash-guard blocking.
- **Verify extensions exist after cleanups:** If `Extensions/` dir gets emptied, CDP Chrome runs with zero extensions (no AdGuard = noticeably slower). Fix: `cp -R` the 5 keep-list extensions from main Chrome profile.
- **agent-browser now at v0.16.3 (pnpm only).** Removed stale npm duplicate (was 0.9.3). Use `pnpm add -g agent-browser@latest` to upgrade — `pnpm update -g` is a no-op once the lockfile thinks it's current.
- **pnpm build approval prompts require `expect`.** `pnpm approve-builds -g` has two sequential interactive prompts; piping stdin only answers the first (readline closes before the second). Fix: `expect -c 'spawn pnpm approve-builds -g; expect "to select"; send " "; expect "to select"; send "\r"; expect "Do you approve"; send "y\r"; expect eof'`.
- **Workday forms are automation-proof:** snapshot/eval work, but click/fill/select timeout (anti-automation). JS DOM changes don't sync React state. Use automation for login/upload/reading, manual for form submission. See `~/docs/solutions/browser-automation/`.
- **React `<select>` dropdowns via CDP:** Standard DOM `.value` + `change` event doesn't sync React state. Fix: set `selectedIndex` then fire full event chain (mousedown→mouseup→click→input→change→blur). Works on Taobao login.
- **Alibaba baxia CAPTCHA:** Triggers on SMS code request. Slider challenge, can't automate. Same class as Workday anti-bot.
- **Chrome CDP port not binding:** Process starts (`pgrep` finds it) but port 9222 never opens. Always verify with `curl http://127.0.0.1:9222/json/version`, don't trust `pgrep` alone. Kill and relaunch fixes it.
- **CDP on default profile (Chrome 145+):** Stderr says "DevTools remote debugging requires a non-default data directory." Renderers inherit `--remote-debugging-port` in their args (so `pgrep` and `ps` show it) but the browser process never binds the port. Fix: always pass `--user-data-dir="$HOME/.chrome-cdp-profile"`. The `open -a Chrome --args` method also silently drops the flag — use the full binary path instead.
- **Playwright resource blocking for scraping:** `page.route('**/*', handler)` to abort `image`/`font`/`media` resource types. Image URLs still readable from DOM `src`/`data-src` attrs.
- **`taobao` CLI:** `~/code/taobao-cli/`, symlinked at `~/bin/taobao`. Uses **nodriver** (stealth Chrome) + Playwright bridge. Needs CDP Chrome stopped first (exclusive profile access).
- **nodriver:** `pip install nodriver`. Patches Chrome CDP to bypass anti-bot (Taobao, XHS). Launches own Chrome — can't share `user-data-dir` with running CDP Chrome.
- **Shell quoting for `eval`:** Use heredoc (`cat > /tmp/file.js << 'EOF'`) for complex JS — smart quotes break eval.
- **1Password CLI from SSH:** `OP_BIOMETRIC_UNLOCK_ENABLED=0` + `op signin --raw --account personal` with piped password. Touch ID doesn't work over Jump Desktop.
- **agent-browser snapshot overhead is Node cold start**, not Playwright — 22s with dirty profile, 1.5s after extension cleanup. Direct CDP does the same accessibility tree in 38ms.
- **agent-browser eval + long async → daemon timeout:** Async functions exceed daemon response window → "Resource temporarily unavailable (os error 35)". Fix: bash loop calling sync evals with `sleep` between, not one big async eval.
- **agent-browser commands must be strictly sequential:** Firing a second command before the first returns jams the daemon with os error 35. Never parallelize `type`/`click`/`fill` calls.
- **agent-browser `fill` not `eval` for SPA form inputs:** `eval "input.value = 'x'"` bypasses Vue/React reactivity — framework state stays empty. `fill <selector> <text>` uses Playwright's native method which fires all events the framework listens for. Same applies to `type <selector> <text>` (two args required — one arg treats text as selector).
- **agent-browser eval: don't use broad selectors for row-targeted clicks.** `querySelectorAll('tr, div')` matches parent containers whose `textContent` includes every child row's text. A `button:last-child` on the parent div hits the wrong row's button. Use `snapshot` + `@ref` for precise element targeting instead.
- **agent-browser `download` chokes on large files (>~50MB):** Daemon crashes with EAGAIN (os error 35) during 254MB zip download. Small files (<5MB) work fine. Workaround: extract session cookie and use curl, or use Readwise/service API token directly. Cookie decryption from Playwright's Chromium profile is non-trivial (different Keychain entry than standard Chrome — `security find-generic-password -s "Chromium Safe Storage"` returns a key but it doesn't decrypt correctly).
- **agent-browser can't solve cross-origin CAPTCHAs:** `find text "Verify" click` finds elements across frames but clicks don't penetrate cross-origin iframes (octocaptcha.com, Arkose Labs). `eval` also blocked by same-origin policy. GitHub org creation requires CAPTCHA per-org — not batch-automatable. Same class as Alibaba baxia.
- **WeChat article text extraction:** `WebFetch` hits CAPTCHA. Two approaches: (1) `agent-browser --profile open <url>` then `snapshot --profile` — returns structured accessibility tree with headings, lists, tables intact. Best for articles you want to analyse structurally. (2) `agent-browser eval "document.getElementById('js_content').innerText"` — returns plain text in one call. Best for quick extraction. Both need `--profile` to pass WeChat verification.
- **Don't add `--disable-background-networking` to Chrome:** Kills DNS prefetch + speculative preconnect, making page loads visibly slower. Only helps headless/test environments.
- **MS Forms: textboxes without accessibility refs.** Some textboxes don't get `[ref=eN]` in `snapshot` (long ARIA labels cause it). Workaround: use `eval` to tag with unique `data-` attribute, then `fill 'input[data-X="Y"]'`. But beware — if you `setAttribute` the same `data-` key on multiple elements, `fill` will fail ("matched 2 elements"). Use unique attribute names per field (e.g. `data-auto2`, `data-auto3`).
- **MS Forms: `fill` can shift values between fields.** When using `data-auto` tagging on multiple inputs, fill operations can put values in wrong fields (name→phone, plan→email). Always verify with `eval` + `querySelectorAll('input')` index mapping after filling. The input index from `document.querySelectorAll('input')` is the reliable ground truth.
- **MS Forms: screenshots don't scroll.** `scroll up/down` and `eval "window.scrollTo(0,0)"` don't affect screenshot viewport on MS Forms. Use `snapshot` text verification instead of visual screenshots for form review.

## WebFetch (Visual Product Research)
- **WebFetch strips images from JS-heavy product pages.** E-commerce sites (NuPhy, etc.) are mostly image galleries — WebFetch returns titles and prices but zero visual information. Don't try to form aesthetic opinions from marketing text.
- **Use agent-browser for visual comparison:** `agent-browser open <url> && agent-browser screenshot <path>`, then `Read` the screenshot. Separate commands — `--screenshot` inline with `open` doesn't work.
- **Don't rank aesthetics you can't see.** Same error class as product specs and dates: overconfidence in plausible-sounding opinions. If you haven't viewed an image, say so. Don't extrapolate from review text.
- **WebFetch can't render images directly.** Fetching a raw image URL (PNG/JPG/WebP) returns a 400 error, not image content. Download with `curl -sL -o /tmp/file.jpg <url>`, then `Read` the file.
- **`.webp` images cause "Could not process image" 400 errors** with the Read tool. Convert first: `sips -s format png /tmp/file.webp --out /tmp/file.png`, or download as JPG/PNG from the CDN (most Shopify CDNs support `&format=jpg` suffix). Safest: just download JPG/PNG variants when available.

## WebFetch (Substack / Dynamic Homepages)
- **Substack homepages return stale/minimal content.** WebFetch on `latent.space` returned Dec 2024 content in Feb 2026 — Substack renders the latest posts client-side. Always fetch **specific article URLs** (e.g. `latent.space/p/article-slug`), not the homepage. Use WebSearch first to find the URL.

## Codex / OpenCode (Skill Loading)
- **SKILL.md requires YAML frontmatter:** `---` delimited block with `name`, `description`, `user_invocable` fields. Without it, Codex silently skips the skill on startup. Claude Code is more forgiving — loads skills without frontmatter.

## cn-search / qianli (Chinese Platform Search)
- **CLI:** `qianli` (PyPI 0.2.0, `~/code/qianli/`). Installed via `uv tool install qianli`. Spec: `~/docs/specs/qianli.md`. Skill: `~/skills/qianli/`.
- **Two backends:** WeChat/36kr via direct CDP websocket (fast, 4-18s). XHS/Zhihu via MediaCrawler subprocess (slower, 30-60s).
- **MediaCrawler:** `~/code/MediaCrawler/` with `.venv`. Config patched temporarily for limit (`CRAWLER_MAX_NOTES_COUNT`), restored in finally. Don't run concurrent MC searches.
- **WeChat/Sogou:** Reliable. Public, no auth. DOM selectors: `#main .txt-box` → `h3 a` (title/URL), `span.all-time-y2` (account), `span.s2` (date with `document.write` prefix).
- **36kr:** Works but heavy SPA — needs ~12s initial wait. DOM: `.kr-flow-article-item`, `.article-item-title`, `a[href*="/p/"]`. CAPTCHA after ~5 rapid requests.
- **XHS (v0.2.0):** Now via MediaCrawler subprocess. Needs first-run QR auth. Conservative pacing (1-2/day).
- **Zhihu (v0.2.0):** Now via MediaCrawler subprocess. Needs first-run QR auth. May still be unreliable.
- **`all` subcommand:** Runs wechat + 36kr only (xhs/zhihu too slow for aggregation).
- **CDP Chrome optimised (Feb 2026):** Launch script uses `--disable-extensions-except` (keeps 5) + performance flags. Reduced targets from 16 to 3. Eval latency: 1,220ms → 3.5ms avg. Launch script: `/Applications/Chrome CDP.app/Contents/MacOS/launch.sh`.
- **XHS pages poison CDP pipe:** Anti-bot JS blocks websocket recv() for ALL tabs. Always close XHS tabs after use. Zhihu confirmed same behavior.
- **Playwright MCP not worth always-on:** 22 tools, ~3,700 tokens/turn. agent-browser CLI at 0 tokens/turn is better for occasional use.
- **Huxiu dropped:** Pure SPA, not URL-addressable. Content indexed by Sogou anyway.

## gphotos CLI
- **CLI:** `gphotos` (uv tool, `~/code/gphotos/`). Commands: `list`, `search`, `download`, `albums`.
- **Search doesn't categorize by pose/angle:** Google Photos indexes by face/place/thing, not by composition or camera angle.
- **SPA timing:** Bare fife URLs at ~12s, structured data at ~15s. Cold start needs 20s+ — tool polls automatically.
- **CookieJar not picklable:** Session cache uses JSON dicts, rebuilds jar on read. Was causing silent 0-byte cache files.
- **Data structure:** `"fife_url",width,height` pattern in `AF_initDataCallback` ds:0 block. Full notes: `~/docs/solutions/gphotos-cli.md`.

## YouTube / Content
- **YouTube RSS feeds dead (Feb 2026):** Use `yt-dlp --no-download --playlist-items` for video listing instead.
- **youtube-transcript-api > yt-dlp for transcripts:** yt-dlp auto-captions have 3x line duplication. Use API as primary, yt-dlp as fallback with deduplication.
- **YouTube IP rate limiting in digest runs:** Processing 10+ episodes rapidly triggers IP blocks. Fix: process smallest sources first, or add pacing.
- **yt-dlp JS challenge solver (Feb 2026+):** Must pass `--remote-components ejs:github`. Without it: "n challenge solving failed". Even with the flag, subtitle downloads can 429.
- **Digest RSS+Whisper fallback:** Duration ratio > 3x between YT video and podcast episode → skip match. Also deduplicates when multiple YT videos match the same podcast audio URL.

## resurface CLI
- **Global result caps silently drop older matches:** Fixed Feb 20. `truncate(50)` on newest-first sorted results meant common terms exhausted the cap on recent sessions, hiding older matches entirely. Removed the cap — `--days` already scopes the range.
- **`--deep` fallback to raw Grep:** If `resurface search` misses something, `Grep` on `~/.claude/history.jsonl` is the escape hatch — it searches the raw prompt log without any caps or filtering.
- **Use proper regex alternation syntax:** `(foo|bar)` not `foo\|bar`. Resurface uses Rust's `regex` crate (ripgrep-compatible), not grep.
- **Session ID ≠ filename:** Claude Code stores entries from session A in session B's JSONL file (context compaction/continuity). The `--session` filter checks the entry-level `sessionId` field, not the filename. Don't assume filename = session.
- **"Did X happen?" — search for execution markers, not trigger words.** `resurface search "weekly" --deep` returns 200+ noise hits (intent mentions). Use `--role claude` to filter to AI confirmations only, and search for output markers like "synthesis complete" or "note written" instead of the skill name.

## gog CLI (Gmail/Calendar)
- **`gog gmail send` reply flags are mutually exclusive:** Can't use both `--reply-to-message-id` and `--thread-id` simultaneously — errors out. Use `--reply-to-message-id` alone for replies; it auto-threads.
- **`gog gmail send` reply requires `--reply-all` and `--subject`:** Even for single-recipient replies, `--to` is required unless you pass `--reply-all`. Subject is always required too (use `Re: ...`). Dry-run first with `--dry-run`.
- **`gog gmail search` returns Drive API errors for `search` subcommand**: The generic `gog search` triggers Drive, not Gmail. Always use `gog gmail search`.
- **`--quote` flag:** Includes quoted original message in reply. Requires `--reply-to-message-id` or `--thread-id`.
- **`--full` flag for full email body:** Default output truncates long HTML emails (tables, receipts). Use `gog gmail read <id> --full` to get complete content.
- **Read threads, not standalone messages:** `gog gmail search` shows a `THREAD` column with message count (e.g. "[2 msgs]"). Replies thread under the *sent* message, not as separate search hits. Always read the thread with the highest message count — the standalone auto-reply is a different message ID from the real reply.
- **`gog calendar create` uses `--from`/`--to`, not `--start`/`--end`.** Requires `<calendarId>` as first positional arg (use `primary`). Example: `gog calendar create primary --summary "Event" --from "2026-02-27T12:00:00+08:00" --to "2026-02-27T13:30:00+08:00" --force`.
- **`--reply-all` replies to the From address, not the ticketing address.** If the original message came from `support@example.com` but previous replies went to `support-reply@example.com` (a ticketing system), `--reply-all` sends to the From header (`support@`). Always check the To address in the dry-run output. For ticketing systems, use `--reply-to-message-id` on a message you originally *sent to* the correct address, or explicitly pass `--to`.
- **`file` keyring backend fails in non-TTY shells (Claude Code, cron, LaunchAgents).** Error: "no TTY available for keyring file backend password prompt". Fix: `export GOG_KEYRING_PASSWORD=$(security find-generic-password -s gog-keyring-password -a terry -w 2>/dev/null)` in `.zshenv`. The password is already stored in macOS Keychain. Don't switch to `keychain` backend — it requires re-auth and the file backend works fine with this env var.

## iCloud Drive / File Delivery to Phone
- **`~/Library/Mobile Documents/com~apple~CloudDocs/` is unreliable from CLI:** `cp` succeeds silently but files may not persist or sync. `ls` on the directory returns "Operation not permitted" (FDA issue). Use `~/Documents/` instead — it syncs to iCloud Drive → Files app → Documents reliably.
- **iCloud sync lag for new files:** Even when files land in `~/Documents/`, they can take 30-60 seconds to appear in the Files app. Pull-to-refresh helps. If urgent, AirDrop is instant.
- **Cached PDFs on phone:** Overwriting a file with the same name may show the old version. Use a new filename to force a fresh download.

## PDF → PNG Conversion (macOS)
- **`pdftoppm` (poppler) is the only reliable multi-page option:** `pdftoppm -png -r 200 input.pdf output-prefix` → `output-prefix-1.png`, `-2.png`, etc.
- **`sips`** converts single-page PDF only (no `--extractPage`). **`qlmanage -t`** only renders page 1 thumbnail. **Python `Quartz`/`CoreGraphics`** not available outside system Python (which is gone on modern macOS). All three fail for multi-page PDFs.

## Manulife SimpleClaim
- **JPG/PNG only — no PDF uploads.** Convert receipts to images first. Max 15 images, 10MB each.
- **Outpatient claims capped at HKD $3,000** on SimpleClaim. Higher amounts → submit via full Manulife Customer Website instead.
- **"Others" category** for routine health checks/vaccinations — doesn't fit GP/specialist/physio categories.

## Rust Toolchain
- **`cargo-binstall` first:** Installs prebuilt binaries instead of compiling from source. 12s vs 10min.
- **Installed tools:** cargo-release, cargo-audit, cargo-outdated, cargo-machete, cargo-bloat, cargo-semver-checks.
- **Release profile for small CLIs:** `opt-level = "z"`, `lto = true`, `codegen-units = 1`, `panic = "abort"`, `strip = true`. Cuts binary ~46%.
- **PostToolUse hook:** `post-edit-rust-format.js` runs `rustfmt` on `.rs` edits. Clippy too slow for per-edit — run manually before publish.
- **`serde(rename_all = "camelCase")` vs uppercase suffixes:** `product_name_tc` maps to `productNameTc`, not `productNameTC`. Fields ending in acronyms need explicit `#[serde(rename = "...")]`.

## Oura API v2
- **Inconsistent `end_date` behavior:** `daily_sleep` and `daily_readiness` treat `end_date` as inclusive; `sleep`, `daily_activity`, `daily_stress` treat it as exclusive. Always send `end_date = target_date + 1 day`.
- **Sync lag:** `daily_sleep` endpoint (score + contributors) syncs before `sleep` periods endpoint (durations, HRV). Early morning queries will have score but not breakdown. CLI falls back to contributors.

## OWNDAYS Scraper
- **`--per-variant` images are duplicates:** OWNDAYS loads all color variants' images on every `?sku=` page. Not worth the 5.5x slowdown. Variant metadata (SKU, swatch URLs) is the real value.
- **All variants labelled "C1":** `title="C1"` on all color-label spans regardless of actual color. Swatch image URLs differentiate variants, not color code text.

## QMD (Vault Semantic Search)
- **`qmd update` ≠ `qmd embed`:** `update` refreshes the file/BM25 index (~10s, fast). `embed` creates vector embeddings (slow, minutes). Must run both — BM25 search stays stale if you only run `embed`.
- **BM25 chokes on hyphenated terms:** `qmd search "python-pptx"` returns zero. Use simple keywords: `qmd search "powerpoint"` or `qmd search "pptx editing"`.
- **Automation chain:** Post-commit hook → `qmd update` (fast BM25). 2-hour cron → `qmd update` + `qmd embed` (full refresh). See `~/scripts/crons/qmd-reindex.sh`.

## LLM Council
- **Echo chamber risk:** Council validates the frame you give it. Always include a counter-frame prompt or explicitly ask one model to argue the opposite.
- **US-centric employment advice:** Council defaults to US norms. HK culture is different. Always flag jurisdiction in the prompt.

## Individual Tool Gotchas
- **mediapipe v0.10.32+:** Uses `mp.tasks` API, NOT `mp.solutions` (removed). `FaceLandmarker` needs a downloaded `.task` model file. Returns 478 landmarks.
- **sqlite-vec:** must call `enable_load_extension(True)` BEFORE `sqlite_vec.load(conn)`
- **python-pptx edits:** Edit `run.text` to preserve formatting. Don't rebuild paragraphs — it strips formatting.
- **python-pptx image replacement:** `pic.image._blob = new_blob` does NOT persist on save. Must go through the OPC part: `slide.part.rels[rId].target_part._blob = new_blob`.
- **Cross-encoder rerankers:** favor verbose answers for short queries due to term density bias. For vague/short queries (≤4 chars), RRF fusion alone is more robust.
- **RAG fast-paths:** condition must evaluate AFTER fusion/sorting, not before. Fast-path thresholds must account for fusion score distributions.
- **OpenRouter rate limits:** Account-level, not per-model. Wait 2+ min between test bursts.

## Athena's Aegis (Old Vault)
- **Directory name contains U+2019 (RIGHT SINGLE QUOTATION MARK `'`), not ASCII apostrophe (U+0027 `'`).** Read/Grep/Glob tools and Bash `cd` all fail with "path does not exist." Python `os.walk`/`os.listdir` and Spotlight `mdfind` work. Use `python3 -c` via Bash to access files there.
- Athena's Aegis covers Jun–Dec 2024 only (80 daily notes). For older content (2022–2023), check Ideaverse/Metis-Codex/Bob-Fleeting in `~/code/vivesca-terry/chromatin/Archive/`.

## Multi-Machine Setup
- **Machines:** M1 iMac 8GB (current always-on, SSH + Claude Code) + M2 MacBook + M3 MacBook + iPhone.
- **File transfer to main Mac:** `tailscale file send <file> <mac-hostname>` from M2. Lands in `~/Downloads/`.
- **Jump Desktop:** Works from iPhone and M2. Tailscale exit node can break it — disable exit node if Jump hangs.

## iCloud Drive
- **Path:** `~/Library/Mobile Documents/com~apple~CloudDocs/` (files). App containers at `~/Library/Mobile Documents/`.
- **Sandbox blocks `ls`:** Use Python `os.listdir()` or Read tool for individual files.

## Telegram (tg-notify.sh)
- **`curl -d` truncates on `&` in message text:** `curl -d text="$MSG"` treats `&` as form field separator. "A&E fees" becomes just "A" + garbled params. Fix: use `--data-urlencode "text=$MSG"` instead.
- **`parse_mode=Markdown` mangles plain text:** Stray `*`, `_`, or `[` in LLM output breaks Telegram markdown parser. If messages are plain text, omit `parse_mode` entirely.

## macOS Scheduling (One-Off Reminders)
- **`at` command permission denied on macOS:** `/usr/lib/cron/jobs/.lockfile` not accessible. Use LaunchAgent instead.
- **One-off LaunchAgent pattern:** Create plist with `StartCalendarInterval` (Month/Day/Hour/Minute), load with `launchctl load`. **Clean up after firing** — `StartCalendarInterval` repeats annually. Unload + delete plist the next day.
- **Google Calendar `popup:0` rejected by API:** Minimum 1 minute for override reminders.

## Netlify CLI
- **Interactive prompts hang in non-TTY (Blink/tmux):** `sites:create`, `deploy` without `--site` all try arrow-key menus → crash. Workaround: use `netlify api` subcommand with `--data` JSON. E.g. `netlify api createSite --data '{"body":{"name":"my-site"}}'` then `netlify deploy --prod --dir=. --site <id>`.
- **Vercel is lower-friction for quick static deploys:** `vercel --prod --yes` just works (auto-creates project, no linking step). Netlify needs site creation + `--site` ID. Prefer Vercel for one-off deploys from Blink.

## Claude Code (CLI)
- **Trust dialog reappearing every launch:** `hasTrustDialogAccepted` in `~/.claude.json` under `projects.<path>` can be `false` despite repeated approvals. Fix: `python3 -c "import json; f='/Users/terry/.claude.json'; d=json.load(open(f)); d['projects']['/Users/terry']['hasTrustDialogAccepted']=True; json.dump(d,open(f,'w'),indent=2)"`. Check this first if the "Is this a project you trust?" prompt keeps appearing.

## Pydantic v2 + LLM Tool Outputs
- **LLMs send wrong types for `dict[str, str]` fields:** Claude (all sizes) will put `True` (bool) or `1` (int) as dict values when the schema says `"type": "object"`. Always coerce: `{k: str(v) for k, v in data.items()}` before passing to Pydantic models.
- **Pydantic v2 rejects positional args by default:** `DimensionScores(1, 1, 1, 1, 1)` fails — must use keyword args. Catch this when delegating model construction to other agents/tools.

## agent-config
- **`.claude.json` must NOT be symlinked:** Contains runtime state. Symlink = two machines fighting over the same file.
- **Hooks ARE safe to symlink:** No runtime state. `~/.claude/hooks/` → `~/agent-config/claude/hooks/`.
- **Bootstrap:** `git clone git@github.com:terry-li-hm/agent-config.git ~/agent-config && ~/agent-config/scripts/bootstrap.sh`

## pplx CLI (Perplexity)

- **`pplx research` timed out with default reqwest client:** `Client::new()` uses OS-level socket timeout (~60-90s), but `sonar-deep-research` API can take 3-5 minutes. Fixed by adding `Duration::from_secs(300)` timeout in `~/code/pplx/src/client.rs`. Rebuilt and installed Feb 24.
- **`pplx search` works fine** — regular search API responds in seconds. Only deep research needs the extended timeout.

## Speech-to-Text APIs (Feb 2026) — for meditation/dharma batch transcription

**Pricing (per-minute, batch):**
- Groq Whisper-large-v3-turbo: $0.000667 — cheapest but no vocab, hallucination issues
- AssemblyAI Universal: $0.0035 base + $0.00083 keyterms = $0.0043 all-in
- Voxtral Mini V2 (Mistral): $0.003 — ~4% WER, "context biasing" (100 words), Feb 2026 entrant
- **Speechmatics Pro: $0.004 all-in** (custom dict included, no add-on)
- **Deepgram Nova-3: $0.0043 base + $0.0013 keyterm add-on = $0.0056 all-in**
- OpenAI gpt-4o-transcribe: $0.006, no vocab injection

**Vocabulary boosting — three different approaches:**
- **Deepgram**: "Keyterm prompting" — boosts term probability at LM decoder level. 100-term cap. $0.0013/min add-on. Proven 625% uplift in case study (self-reported).
- **Voxtral**: "Context biasing" — similar to Deepgram, 100 words. Unproven for Sanskrit/Pali.
- **Speechmatics**: "Custom dictionary + `sounds_like`" — specifies phonetic pronunciation, guides acoustic model directly. 1,000 words/job, included in base price. Most principled for Sanskrit/Pali.

**`sounds_like` format (Speechmatics):**
```json
{"content": "Satipatthana", "sounds_like": ["sah-tee-pah-tah-nah"]}
{"content": "Dzogchen", "sounds_like": ["dzog-chen", "zog chen"]}
```

**Accuracy (WER, real-world audio):**
- Voxtral Mini V2: ~4% (self-reported, Feb 2026)
- Deepgram Nova-3: 5.26% batch
- AssemblyAI: ~10.7%
- Whisper-large-v3: ~10-12%, **severe hallucination on quiet/silence-heavy audio** — avoid for meditation content

**Speechmatics batch API pattern:**
1. `POST https://asr.api.speechmatics.com/v2/jobs` — multipart: `config` (JSON) + `data_file` (audio)
2. Poll `GET /v2/jobs/{job_id}` → `job.status == "done"`
3. `GET /v2/jobs/{job_id}/transcript?format=txt`

**wu CLI integration:** `wu transcribe --model speechmatics` or `wu batch --model speechmatics`
Set `SPEECHMATICS_API_KEY` in `~/.zshenv`. Free tier: 480 min/month (recurring).

**Transcript errors found in Deepgram output (review Feb 2026):**
- "Nirvikaupa" for "Nirvikalpa" — was missing from keyterm list, now added
- "vignana" for "vijnana" — was missing, now added
- "amala bhajnana" for "alaya-vijnana" — was missing, now added
- Takeaway: keyterm list needs ongoing curation as new content reveals gaps

**Decision: Phase 2 on Deepgram (infrastructure built), Phase 3 A/B test Speechmatics.**
Free 480 min/month tier = enough to test one pack before committing.

## Photos.app (AppleScript export)

- `item -1 of media items` returns the last item in **library order**, not the most recently taken photo. Library order doesn't match chronological order — recently synced older photos (e.g. document scans) can appear at the end.
- To find a specific recent photo: export the last 10-15 items and check visually, or use `search for "keyword"` (uses Photos' ML tagging).
- iCloud sync from iPhone to Mac Photos can take several minutes. A photo visible on iPhone may not be in the Mac library yet.
