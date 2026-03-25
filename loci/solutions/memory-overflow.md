# MEMORY.md Overflow

Entries demoted from MEMORY.md to stay within 150-line budget. Still valid — just infrequent.
Reviewed weekly in `/weekly`. Promote back to MEMORY.md if cited 2+ weeks running.

## Directory Layout
- **Pharos sync:** iMac LaunchAgent (`com.terry.pharos-sync`, every 15min) pushes MEMORY.md to `officina/claude/memory/`. OpenCode symlink details below.

## GARP RAI
- **melete standalone workspace** — binary at `~/code/melete/target/release/melete`, not shared `~/code/target/release/`.

## Credential Isolation
- **`op` in Bash calls:** Each subprocess loses the session. Use `op signin --raw > /tmp/op-session.txt` in terminal, pass via `OP_SESSION_personal`. Biometric-only writes empty file — use master password.

## Development Patterns
- **Cross-tool file format contracts need a roundtrip test.** When Python writes + Rust reads a shared file, test the boundary. Bug: `last_review: String` silently dropped cards written with `null` by a migration script. Fix: `Option<String>` + a parse test with null. Add a test whenever a new writer touches a shared file.

## Claude Code Built-in Commands
- **`/status` and `/context` are TUI-only.** `env -u CLAUDECODE claude -p "/context"` hangs — not runnable headlessly. Use `ccusage blocks` autonomously for token %, cost, time remaining.

## Rust/Codex Delegation Gotchas
- **~/code/Cargo.toml workspace:** consilium, keryx, stips, pondus, deltos must stay in `exclude` list. Without it, `cargo clippy` from those dirs fails with "multiple workspace roots". Add any new standalone Rust CLI to `exclude` immediately after creating it.
- **Codex sandbox blocks crates.io.** Build outside Codex. **`cargo build --release` ≠ `cargo install --path .`** — build updates `target/release/` only; install updates `~/.cargo/bin/`. **Parallel Gemini delegates each adding `[workspace]`** → duplicate key merge conflict. Fix: add `[workspace]` before launching swarm.

## Due App / moneo CLI
- **Due's AppleScript window count = 0.** Due uses non-standard NSPanel/SwiftUI windows — they don't register in AppleScript's window hierarchy. No reliable fix. CloudKit deletions require Due's own UI. Documented limitation; prevention (duplicate guard in `moneo add`) > post-hoc deletion.
- **Due Shortcuts has no delete action.** Actions available: create, mark done, find, edit. Can't script deletion via Shortcuts or AppleScript.
- **Due not syncing to a Mac = app not running.** CloudKit only syncs when Due is open. Fix: `ssh <host> "open -a Due"`. Prefs domain missing = never launched on that machine.
- **`moneo --sync` requires peekaboo permissions.** If it prints "Due editor open — please click Save manually", grant Accessibility + Screen Recording to `/opt/homebrew/bin/peekaboo` in System Settings → Privacy & Security. `peekaboo permissions` check may show stale results — test with a real `--sync` to confirm.

## Publishing Packages
- **`cargo publish` for zero-user personal tools:** auto-publish after `--dry-run` passes. No confirmation needed — dry-run is the safety net.
- **`uv publish`** doesn't read `~/.pypirc`. Use `uvx twine upload dist/*`.
- **`uv tool install --force`:** hook-enforced to require `--reinstall`.

## Rust/Codex Delegation Gotchas
- **Rust regex crate:** No lookahead/lookbehind (`(?=...)` etc). Delegates port these from Python. Always `cargo clippy` after delegation.
- **Codex sandbox blocks crates.io.** `cargo build`/`cargo fetch` fail with DNS errors. Build outside Codex after delegation: `cargo build --release` in normal shell.
- **`cargo build`/`cargo run` may say "Finished" without recompiling** despite source changes. Fix: `cargo clean -p <crate>` then build. Happened 4+ times in pondus session.

## Active Project Details (lookup-only)
- **photoferry** (`~/code/photoferry`): `~/docs/solutions/photoferry-reference.md` (includes swift-rs FFI gotchas)
- **kindle-extract** (`~/code/kindle-extract`): `~/docs/solutions/kindle-extract-reference.md`
- **Wechat2RSS** (active, `localhost:8001`): `~/docs/solutions/wewe-rss-reference.md`
- **Hexis** full details: v0.1.0 shipped (Phases 1-2). GitHub: `hexis-framework/hexis`. Registries: crates.io `hexis`, PyPI `hexis-framework`. Plan: `~/docs/plans/2026-02-26-feat-hexis-open-source-release-plan.md`.
- **wacli** rebuild: `CGO_ENABLED=1 go build -tags sqlite_fts5`. Fork at `~/wacli/`, PR #79. Homebrew binary at `/opt/homebrew/Cellar/wacli/0.2.0/bin/wacli`.
- **Lustro** (`~/code/lustro`): AI news CLI. Config at `~/.config/lustro/sources.yaml`. Reference: `~/docs/solutions/lustro-reference.md`. Run `lustro check` monthly.

## Photos Access
- **Use osascript first, not photos.py.** photos.py (SQLite direct) breaks when TCC/FDA grants reset. osascript talks to Photos.app via Apple Events and works regardless. See `~/skills/photos/SKILL.md`.
- **iCloud sync lag:** iPhone says "synced" but Mac may not have it yet. `open -a Photos` nudges sync. AirDrop to `~/Downloads/` is instant fallback.
- **Photos DB path works for reading:** `sqlite3 ~/Pictures/Photos\ Library.photoslibrary/database/Photos.sqlite "SELECT ZFILENAME FROM ZASSET ORDER BY ZDATECREATED DESC LIMIT 5;"` → filenames. Then `/usr/bin/find ~/Pictures/Photos\ Library.photoslibrary/originals -name "<UUID>*"` → actual file. But iCloud-only photos won't have a local file — `brctl download` doesn't work on Photos library (not CloudDocs). For real-time phone→Claude photo pipeline: AirDrop is the only reliable path.

## LinkedIn Content Pipeline
- **Content ideas live in `[[LinkedIn Content Ideas]]`.** Praxis.md has one pointer only. Don't create per-post entries.
- **General pattern:** When a vault note tracks a pipeline, TODO should have one recurring pointer, not per-item entries.

## Context Compaction
- **Trust Anthropic's auto-compact default (~83%). Don't override.** `/clear` between tasks, manual `/compact` only when noisy.

## Claude Code Alternative Backends
- **Fallback commands:** `ck` (Kimi K2.5), `cg` (GLM-5) — scripts in `~/bin/`, isolated `$HOME` dirs.
- **`customApiKeyResponses` in `.claude.json`:** Keys stored as last 20 chars. Pre-approve in `approved` array.
- **Isolated HOME required:** Scripts with `export` + `exec` are the clean approach.
- **Full setup:** `~/notes/solutions/Claude Code with Kimi K2 Setup.md`

## Networking Emails
- **Calibrate status in language.** "Compare notes" implies peer-level — inappropriate for senior recipients. Use curiosity framing.
- **LinkedIn slug ≠ GitHub handle:** `terrylihm` (LinkedIn) vs `terry-li-hm` (GitHub). Verify from `~/notes/Personal Details for Applications.md`.

## Work Email Drafts
- **Compliance/FCC emails: start at 3 lines, not 3 paragraphs.** Don't repeat recipient's numbers, don't explain internal mechanics, don't editorialize. Just answer the question.

## Financial / Investing
- **Bank employee brokerage compliance:** Don't open new brokerage accounts while employed at a bank. Wait until after formal employment ends.
- **IBKR HK is the only HK broker with self-service LSE access.** Full analysis in `~/notes/Investing Strategy.md`.

## AI Model Availability
- **Verify API/CLI access before adopting social media model recommendations.** Always test first. Model status → `delegate` skill.
- **Model self-identification is unreliable.** `codex exec` reports "GPT-5" but actual is GPT-5.2.
- **ANTHROPIC_API_KEY can't access Haiku 4.5 (500) or Sonnet 4.5+ (404).** Only Claude 3 Haiku works. Scripts need fallback chains.
- **Gemini 3 Flash preview (Feb 2026).** `gemini-3-flash-preview`. $0.50/$3 per Mtok. 1M context, native audio/video, thinking levels.

## AI Model Evaluation
- **Haiku researcher agents can hang indefinitely** on web-heavy tasks. Sonnet more reliable. Stop after 2 check-ins.
- **Eval sources:** `~/docs/solutions/ai-model-evaluation-sources.md` — Arena, AA, SWE-rebench, LiveBench.

## Delegation Patterns (details)
- Provide exact file paths, line numbers, code snippets — never ask delegated models to explore.
- **External delegates outperform Claude Task haiku agents for code generation.** They read the codebase first. Haiku agents: 3/6 compile errors. External: 3/3 clean.
- **Gemini CLI rate-limits aggressively** — "exhausted capacity" errors. Use `-y` flag.
- **Cross-model routing:** `~/docs/solutions/cross-model-routing-guide.md`.
- **Grok CLI** (`~/bin/grok`): `grok "query"`, `grok --x-only "query"`, `grok --no-search "query"`. ~$0.02/search.

## Twitter/X
- **`bird` CLI** (`/opt/homebrew/bin/bird`): `bird user-tweets <handle> -n 10 --plain`. Also: `read`, `replies`, `search`, `thread`. Uses Chrome cookies.
- **Impersonator handles are common.** Verify with a web search before adding to lustro. E.g. `@ChipHuyen` is a K-pop fan; real Chip Huyen is `@chipro`. Always check first tweet content before trusting a handle.

## Claude Model Gotchas (extended)
- **ccusage weekly cap estimate drifts with API pricing changes.** The cap is internal token units, not dollars. Recalibrate after pricing changes.
- **Agent Teams = Opus-exclusive.** Switch models before large parallel orchestration.
- **Opus 4.6 behavioural risk:** Exhibited self-interested negotiation in Vending Bench eval. Monitor in agentic systems.

## Demoted 2026-03-16

- **Seed skills proactively with real data.** Don't wait for three occurrences. First example should be a case that actually happened — theoretical examples don't test the rule.
- **Rename tasks: sweep all layers before declaring done.** For skill renames: (1) directory, (2) SKILL.md `name:` frontmatter, (3) hooks (url-skill-router + any PostToolUse), (4) vault references, (5) MEMORY.md/CLAUDE.md. For general renames: code, config, LaunchAgents, log files, cache paths. Don't stop at the obvious.
- **Verify restaurant/venue is open before recommending.** Locofama showed as "Closed for now 休業中" on Instagram — recommended it without checking. Always verify current operating status, not just address/reviews.

## Behavioral Patterns (infrequent)
- **Plans that add "memory" to tools: stress-test the enforcement mechanism first.** If enforcement is just "skill tells Claude to do it," it won't stick.
- **Don't default to Western-familiar options.** Verify evidence hierarchy (酸枣仁 had more RCTs than chamomile).
- **Don't soften physical/factual descriptions.** State what you see.
- **Verify advice provenance: vendor docs vs community blogs.** Check vendor first. Case study: `~/docs/solutions/verify-advice-provenance.md`.
- **Press coverage pricing can be stale.** Always check vendor pricing page.
- **Tech choices: optimise for product, not developer ease.** Rust CLI > Python CLI.
- **When user shares product links, open and verify them.** Use `agent-browser --profile`, don't guess from URLs.
- **Don't dismiss lower-level work.** Sophistication gap ≠ nothing to learn.
- **Auto-generated context files hurt agent performance.** Curation is the point (Latent Space, Feb 2026).
- **obra/superpowers:** Cherry-picked TDD table, 3-fix rule, spec compliance. Quarterly glance only.

## CLAUDE.md Features
- **`@import` syntax:** `@path/to/file` in CLAUDE.md inlines that file. Use when CLAUDE.md exceeds ~250 lines or to share rules across projects.

## Behavioral Patterns
- **Verify the bug exists before proposing fixes.** Reproduce with clean methodology.
- **Polishing trap:** Past ship threshold → say "send it." See `~/docs/solutions/patterns/polishing-trap.md`.
- **Don't fold to pushback without verifying.** Research first, push back with facts.
- **Verify mechanism before writing learnings.** Source-review first, write once correctly.
- **CLI naming: always consilium, never propose names directly.** If scope changes mid-naming, re-run consilium with updated context — don't suggest names yourself.

## Skills Architecture
- **`/weekly` includes `/ai-review`.** Don't suggest separately.

## Development Patterns
- **Correction detector hook — killed.** Don't re-implement. Manual rule is higher-signal.
- **TDD rationalizations:** `~/docs/solutions/tdd-rationalizations.md`.
- **Spec compliance as a distinct review pass.** Separate from code quality review.
- **Writing a Python script → pause and ask "is this a feature gap?"** Check: does this belong as a flag or command in an existing tool? Common signals: post-processing output, pre-processing input, orchestrating multiple calls, working around missing functionality. If yes, add it to the tool. Script first is fine as a spike; the question is whether to graduate it.

## Consilium Gotchas
- **`--context` fixed in v0.4.3** — was silently dropped in `--quick` mode. Now works. Plain concatenation, no labels.
- **`--deep` council**: some models still ask for content if it's very long — fold critical content into the question arg as a fallback.

## General Gotchas
- **CNCBI email is Outlook/Exchange, not Gmail.** `gog gmail` won't work for CNCBI emails — check vault notes instead.
- **Background Task agents unreliable.** Re-check early. Ignore late notifications.
- **Wait for the pain.** Don't formalize until 3+ failures.

## Credential Isolation
- **Manulife HK portal:** username `terrylihm` (not email). Cloudflare-blocked — can't automate, check on phone.

## Shell Gotchas
- **`PYTHONUNBUFFERED=1`** required for `nohup` log visibility.
- **pnpm global PATH:** `~/Library/pnpm` not always in PATH. Install in both npm and pnpm.
- **Symlinked scripts:** `Path(__file__).resolve().parent` for actual directory.
- **`uv tool install` snapshots binary** — source changes don't auto-reflect. After editing a `uv tool install`-ed package source (e.g. oghma), run `uv tool install --editable .` to pick up changes.

## Vercel Agent-Browser Cookie Auth
- **Chrome → agent-browser cookie bridge:** Extract with `browser_cookie3.chrome(domain_name=...)`, inject via Playwright `ctx.add_cookies()`. HttpOnly cookies can't be injected via JS eval — must use Playwright Python API.
- **Profile lock:** Kill existing agent-browser session before launching Playwright directly against `~/.agent-browser-profile`. `SingletonLock` can be deleted manually.
- **Vercel auth:** Cookie names to extract: `authorization`, `vercel_session_id`, `isLoggedIn`, `teamsCache`, `userCache`. Use `authorization` (URL-decoded Bearer token) for Vercel REST API calls.
- **Vercel deployment protection:** `ssoProtection` field on `PATCH /v9/projects/{name}?teamId=...`. Set `{"ssoProtection": {"deploymentType": "preview"}}` to protect previews.

## Demoted 2026-03-05
- **`importlib.machinery.SourceFileLoader`** — correct way to import a Python script with no `.py` extension in pytest. `spec_from_file_location` returns `None` spec without explicit loader.

## AppleScript + display sleep
- **AppleScript `System Events` clicks fail when display is sleeping.** Prefix any AppleScript UI interaction with `caffeinate -u -t 1` + `sleep 0.5` to wake the display first. Already baked into `moneo --sync`.

## Railway
- **CLI session expires during long background tasks** (~15+ min). Token in `~/.railway/config.json` goes stale. Fix: `railway login` (browser OAuth) before next deploy.
- **Railway volumes dont auto-seed from Dockerfile `COPY`** — volume overrides baked-in data. Fresh volume = empty DB. Run `python3 tools/seed_corpus.py` after attaching a new volume to any Railway project.
- **`OPENCODE_MODEL` env var in `.zshenv` overrides script defaults.** Changing the queue script default does nothing if env var is set. After revoking a ZhipuAI key, update `.zshenv` too.

## Railway (demoted 2026-03-06 — infrequent)
- **CLI session expires during long background tasks** (~15+ min). Token in `~/.railway/config.json` goes stale. Fix: `railway login` (browser OAuth) before next deploy.
- **Railway volumes don't auto-seed from Dockerfile `COPY`** — volume overrides baked-in data. Fresh volume = empty DB. Run `python3 tools/seed_corpus.py` after attaching a new volume to any Railway project.
- **`OPENCODE_MODEL` env var in `.zshenv` overrides script defaults.** Changing the queue script default does nothing if env var is set. After revoking a ZhipuAI key, update `.zshenv` too.

## Hooks Architecture
- **Hook side-effects on mtime kill dependent logic silently.** If hook A writes/touches a file, any staleness check on that file's mtime in the same or later hook will always see it as "fresh." Example: `stampNowMd()` in `pre-compact.js` touched NOW.md, making the 2h staleness warning a no-op. When adding file-write actions to a hook, audit all existing checks on that file's mtime.
- **Bank eStatements:** iCloud Drive root, not `~/Downloads`.
- **Manulife portal:** `individuallogin.manulife.com.hk/thf/auth/signIn` — login uses **username** (not email). `myservices.manulife.com.hk` is NXDOMAIN (retired). Claims CLI: `salus claims`. Credentials: 1Password Personal → "Manulife" (username + password fields).

## Demoted from MEMORY.md (Mar 2026)
- **Manulife portal:** `individuallogin.manulife.com.hk/thf/auth/signIn` — username=`TERRYLIHM`, password in 1Password Personal → "Manulife". MFA via email OTP. Claims CLI: `salus claims`. Claims URL: `.../tfm/eclaim/myClaim`. Angular buttons need mousedown+mouseup+click sequence.
- **gog OTP threads:** `gog gmail show <id>` returns first message only. Use `gog gmail thread get <id>` for all messages. OTP = bold 6-digit number; `Ref: XXXXXX` at end is NOT the OTP.

## Demoted Mar 2026
- **Codex misses JSON serialization paths.** Adds fields to internal structs + human output but forgets the JSON `Report` struct. After delegation that adds data fields: audit ALL output paths (human + JSON + any other serializers).
- **`EnterPlanMode` ≠ CE plan.** `EnterPlanMode` is ONLY for trivial tasks requiring live user decisions mid-plan. Any task touching existing architecture → `/ce:plan`. "It's only 20 lines" is not a reason to skip CE plan.

## Manulife portal (demoted 2026-03-08)
- **Manulife portal:** `individuallogin.manulife.com.hk` — username=`TERRYLIHM`, password in 1Password Personal → "Manulife". MFA OTP via email. Claims CLI: `salus claims`. Angular buttons need mousedown+mouseup+click.

## Demoted 2026-03-08 (budget trim)
- **Consilium background redirect:** Don't launch multiple consilium background jobs for the same query. Output files vanish before you can read them. Always redirect: `consilium "..." > ~/tmp/consi.txt 2>&1`. Then `cat ~/tmp/consi.txt` — never rely on TaskOutput (120s timeout < consilium's ~150s runtime).
- **gog gmail send/reply:** See `stilus` skill. Sent messages may not appear in Sent folder on Mail.app — confirm delivery via recipient reply or thread count.

## gog gotchas
- **`gog gmail raw <id>` returns nothing** — command appears unsupported (v0.11.0). Use `gog gmail read <id> -j` to get the full payload including base64-encoded HTML body parts. Extract URLs/images with Python + base64.urlsafe_b64decode.

## Blink Shell / tmux
- **Aliases don't work in Blink's local shell.** Use Settings → Keyboard → Custom Presses. Full setup + tmux one-tap: `~/docs/solutions/blink-shell-setup.md`. Search online for Blink config — non-standard shell.
- **Alt/Meta broken in Blink.** `Ctrl-a` prefix only. iPhone: letters-only keybinds.
- **tmux gotchas:** no `monitor-activity`, no `monitor-bell` (both cause tab flagging/vibration from background jobs), no `pane-focus-in refresh-client` (vibration). Idle-alert pattern: `monitor-activity off` + `monitor-silence 30` + `visual-silence off` (colour flag only, no flash). **tmux-notify is macOS no-op** — uses libnotify (Linux) + visual bells; don't use as replacement for `monitor-silence`.

## Shell Gotchas (infrequent)
- **op-inject cache: use `-s` not `-f`.** `[ ! -f "$cache" ]` treats empty files as "done" — if inject fails silently, it leaves an empty file and never retries. Always use `[ ! -s "$cache" ]` (non-empty) for any cache-or-generate pattern.

## Taobao / agent-browser
- **Taobao/Tmall:** `agent-browser eval` for login. Full: `taobao` skill.
- **agent-browser gotchas** (chaining, LinkedIn, session isolation, --headed) → `nauta` skill.

## Consilium
- 402/403/GPT-5.4-Pro slowness → see `consilium` skill Known Issues section.

## macOS TCC / Permissions
- **FDA ≠ AppData.** `kTCCServiceSystemPolicyAllFiles` (Full Disk Access, system DB) does NOT suppress `kTCCServiceSystemPolicyAppData` ("access data from other apps", user DB). They are separate services in separate databases. A recurring popup despite FDA = check user TCC db: `sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "SELECT service, client, auth_value FROM access WHERE client LIKE '%<name>%';"`. **Clicking Allow may not stick** (stays auth_value=5 in macOS 26) — force-set: `UPDATE access SET auth_value=2 WHERE service='kTCCServiceSystemPolicyAppData' AND client LIKE '%<name>%';`
- **TCC symlink resolution:** System Settings resolves symlinks when adding FDA — adding `~/bin/moneo` silently deduplicates to `~/officina/bin/moneo`. Launchd uses the symlink path at runtime. Fix: point LaunchAgent plist directly at the real binary path.

## crates.io Name Candidates
- Ready to publish: `exauro`, `caelum`. Not ready (personal hardcoding): `graphis`, `auspex`, `amicus`.
- **`gog gmail search "-in:inbox"` crashes** — the leading `-` is parsed as a CLI flag. Use `NOT in:inbox` instead: `gog gmail search "NOT in:inbox newer_than:7d"`. (ERR-20260311-001)
- **`cora email archive` doesn't reliably remove INBOX** — after archiving, verify with `gog gmail search "in:inbox"`. If still present, fall back to `gog gmail thread modify <id> --remove INBOX`. Cora/Action and silent-miss-sweep emails were never indexed by Cora so `cora email archive` fails entirely for those. (ERR-20260311-002)

## TCC permissions (demoted 2026-03-13)
- **TCC "Allow" popup ≠ Full Disk Access.** Clicking Allow on "moneo would like to access data from other apps" grants `kTCCServiceSystemPolicyAppData` only. LaunchAgents accessing sandboxed app containers (e.g. Due) need `kTCCServiceSystemPolicyAllFiles` — must be added manually in System Settings → Privacy & Security → Full Disk Access. Verify via: `sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "SELECT client,service,auth_value FROM access WHERE client LIKE '%moneo%'"`

## op CLI gotchas (demoted 2026-03-13)
- **Rate limit ≈ 50 items/window** — detect "Too many requests", wait 60s, retry (backoff wastes attempts); add 30s pause every 50 items in bulk loops. Background tasks can't receive stdin — any scriptable CLI needs `--yes`/`-y` to skip confirmation.

## rmcp 0.16 gotchas (demoted from MEMORY.md 2026-03-12)
- Parameters lives at handler::server::wrapper::Parameters (not tool). Tool fn signature: fn foo(&self, params: Parameters<T>) -> String — not destructuring, returns String directly. rusqlite &str won't .into() a Value — use Value::Text(s.to_owned()).
- **PostToolUse hooks fire on Read calls** if they check `tool_input.file_path` — Read also has that field. Always gate with `tool_name not in ("edit", "multiedit", "write")` at the top of any write-triggered hook.

## Demoted 2026-03-14 (MEMORY.md audit)
- **"Good catch" → skill update.** Whenever you write "good catch" in a response, immediately propose a concrete skill patch. Saying it without fixing it is half a loop.
- **Check current state before analyzing feasibility.** "What's already set up?" before "what would it take?"
- **Grep matches ≠ synthesis.** When vault grep returns status lines, always read surrounding context before concluding.
- **Fleet-wide questions → discover first.** For any "all our X" question, enumerate via `ls`/`Glob` before acting.
- **3+ failed fixes = question the architecture, not the fix.** Run `cerno` first.
- **Recovering tool credentials: map files first, grep second.** Check `~/.config/`, `~/.toolname/`, `~/Library/Application Support/` before grepping.
- **Unfamiliar terms → WebSearch first, ask never.** Includes unknown words in user messages.
- **Tool/env var not behaving → check the changelog first.**
- **Product/brand claims → include source URL.** No URL = `[unverified]`.
- **Search before verdict on factual claims.** Don't state a position without data.
- **Read the relevant skill BEFORE `--help` or web search.**
- **Don't punt safe local commands.** Only pause for external/destructive.
- **Manual web tasks → provide full clickable URL** (`https://...`).
- **Test hooks/scripts immediately after writing.**
- **Don't punt to the user.** Exhaust programmatic options first.
- **MEMORY.md ≠ notebook.** Reference data → vault. Operational gotchas only.
- **Challenge the premise before building.** Test: "what can this do that the existing approach can't?"
- **"Is there a way that doesn't rely on me?"** — forcing function for eliminating deferred checks.
- **Research before contact — JS-gated sites too.** defuddle → agent-browser → only then contact.
- **`com.apple.provenance` xattr → SIGKILL on `git add`.** Binaries built in `/tmp/` acquire this. Fix: `.gitignore`.

## "Credit balance is too low" full diagnosis (demoted 2026-03-14)
- Two distinct causes: (1) from nested `claude` in interactive session = **5-minute window saturated**, not weekly cap. Fix: stagger launches or wait for window reset. (2) from `claude --print` = **API key billing, not subscription**. Confirmed bug (GH #5143, #3040, closed "Not Planned" Jan 2026, unfixed as of v2.0.76): `--print`/headless mode ignores Max subscription OAuth, falls back to `ANTHROPIC_API_KEY` if set in env. Fix for any script: `env -u ANTHROPIC_API_KEY claude --print ...`. Root cause on this machine: `~/.zshenv.tpl` line 7 injects `ANTHROPIC_API_KEY` into every shell session.

## Opus quota validation — one-time check (demoted 2026-03-18)
- Opus+coding weeks hit 44–54% weekly. Check `/status` Wed Mar 18 after one full Opus-default week; revert to Sonnet-default if %>40%.
- Promo ends Mar 28. Retest clean week Apr 1 (already in Praxis.md).

## External docs lens — CNCBI-specific (demoted 2026-03-18)
- Strip narrative, keep procedural. For anything going to CNCBI: only "do this" / "look here." See `memory/feedback_external_docs_lens.md`. Expires when CNCBI exit complete (~Apr 6).

## Symlink Loops When Moving Config to Git
**Burned:** `cp ~/.claude/hooks/*.py ~/officina/claude/hooks/` copied symlinks (which pointed TO officina) INTO officina, creating self-referencing loops. Every hook broke with "Too many levels of symbolic links."
**Fix:** Use `cp -L` to dereference symlinks, or `git checkout HEAD` to restore real files from git history.
**Hookable:** No — this is a one-time migration, not a recurring pattern.

## CC Hook Format: matcher + hooks array
**Burned:** Added hooks to settings.json with `{"command": "..."}` format. CC requires `{"matcher": "", "hooks": [{"type": "command", "command": "..."}]}`. Session wouldn't start until fixed.
**Fix:** Always use the matcher + hooks array format. Empty matcher = match all events.
