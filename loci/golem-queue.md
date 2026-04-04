### Pending
- [ ] `golem [t-langfuse01] [mcp,langfuse,audit] --provider zhipu --max-turns 15 "Add Langfuse audit tracing to the vivesca MCP server. Every tool call should create a Langfuse trace.
- [ ] `golem [t-phoenix01] [mcp,phoenix,audit,otel] --provider zhipu --max-turns 15 "Add Arize Phoenix as a second observability backend alongside Langfuse in the vivesca MCP server.
- [ ] `golem [t-auditlog01] [audit,logging,cron] --provider zhipu --max-turns 15 "Build a daily log rotation + git backup script for vivesca MCP audit logs.

## What to build

Create `~/germline/effectors/audit-rotate` (Python, executable) that:

1. Rotates JSONL logs from ~/.local/share/vivesca/ into date-stamped files:
   - requests.jsonl -> ~/epigenome/chromatin/audit/requests-YYYY-MM-DD.jsonl
   - signals.jsonl -> ~/epigenome/chromatin/audit/signals-YYYY-MM-DD.jsonl
   - infections.jsonl -> ~/epigenome/chromatin/audit/infections-YYYY-MM-DD.jsonl

2. Rotation logic:
   - Read current JSONL, split entries by date (from "ts" field in each JSON line)
   - Append entries to the correct date-stamped file in audit/
   - Truncate the source JSONL after successful copy (keep it as active log for today)
   - If date-stamped file already exists, append (idempotent re-runs are safe)
   - Create ~/epigenome/chromatin/audit/ directory if missing

3. After rotation, git commit the new/updated files:
   - cd ~/epigenome && git add chromatin/audit/ && git commit -m "audit: rotate logs YYYY-MM-DD"
   - Skip commit if no changes (git diff --cached --quiet)

4. Add a supercronic entry or document the cron line:
   - Run daily at 23:55 HKT
   - Line: `55 15 * * * /home/terry/germline/effectors/audit-rotate` (15:55 UTC = 23:55 HKT)

## Key details
- Source logs: ~/.local/share/vivesca/requests.jsonl, signals.jsonl, infections.jsonl (see metabolon/locus.py for exact paths)
- Each line is JSON with a "ts" field (ISO-8601)
- Destination: ~/epigenome/chromatin/audit/
- The rotated files are immutable once written (append-only per date, never modified after rotation)
- signal-history.jsonl should NOT be rotated (it is already an archive)

## Tests
Write assays/test_audit_rotate.py:
- Test: entries split correctly by date from ts field
- Test: source truncated after rotation (only today's entries remain)
- Test: idempotent -- running twice does not duplicate entries
- Test: missing source files handled gracefully (no crash)
- Test: git commit skipped when no changes

## Constraints
- ASCII only
- Never lose log entries -- copy first, truncate after verify
- Use fcntl lock on source files during rotation (prevent concurrent writes)
- Keep it simple -- single script, no external deps beyond stdlib"`

## Context

t-langfuse01 creates `metabolon/audit.py` with Langfuse tracing. This task adds Phoenix as a second backend so both receive tool call traces. The audit module should support multiple backends simultaneously.

## What to build

1. Refactor `metabolon/audit.py` to support multiple audit backends:
   - `AuditBackend` protocol/ABC with `record(tool_name, args, result, latency_ms, outcome, error)`
   - `LangfuseBackend` — wraps existing Langfuse code from t-langfuse01
   - `PhoenixBackend` — new, sends traces to Arize Phoenix
   - `get_audit_backends() -> list[AuditBackend]` — returns all configured backends (based on env vars)
   - `record_tool_trace()` iterates all backends, never lets one failure block others

2. Phoenix integration:
   - `pip install arize-phoenix-otel openinference-instrumentation` 
   - Phoenix uses OpenTelemetry spans. Create a span per tool call with:
     - span name = tool_name
     - attributes: tool.name, tool.args (PII-redacted), tool.result (truncated), tool.latency_ms, tool.outcome
   - Phoenix collector URL from env: PHOENIX_COLLECTOR_URL (default http://localhost:6006)
   - If PHOENIX_COLLECTOR_URL not set, skip Phoenix backend

3. Update `metabolon/membrane.py` SensoryMiddleware to use `get_audit_backends()` instead of direct Langfuse client

## Key files
- metabolon/audit.py — refactor to multi-backend (created by t-langfuse01, extend it)
- metabolon/membrane.py — update to use get_audit_backends()

## Dependencies
- Depends on t-langfuse01 completing first
- Add arize-phoenix-otel and openinference-instrumentation to deps

## Tests
- Extend assays/test_langfuse_audit.py or create assays/test_phoenix_audit.py
- Test: Phoenix backend creates OTel span with correct attributes
- Test: Multiple backends fire independently (one failure does not block others)
- Test: Backends skipped when env vars not set

## Constraints
- ASCII only
- Never break existing tool call flow
- Each backend is optional and independent
- PII redaction applies to all backends (reuse same sanitize function)"`

## What to build

1. Create `metabolon/audit.py` with:
   - `get_langfuse_client()` -- reads LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST from env. Returns None if not configured.
   - `record_tool_trace(client, tool_name, args, result, latency_ms, outcome, error)` -- creates a Langfuse trace + span per tool call. Skips silently if client is None. Calls client.flush() after. Redacts PII from args (email bodies, message content -- keep action/tool names).

2. Integrate into `metabolon/membrane.py` SensoryMiddleware:
   - Initialize Langfuse client in `__init__`
   - Call `record_tool_trace()` in the `finally` block of `on_call_tool()`, after the existing RequestLogger and Stimulus logging (around line 205)
   - Never let Langfuse errors break tool calls -- wrap in try/except like existing logging

3. Add `langfuse>=4.0.0` to dependencies (pyproject.toml or requirements)

4. Store Langfuse keys in env vars (LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST).

## Langfuse trace structure

trace = client.trace(name="mcp-tool-call", metadata={"tool": tool_name, "server": "vivesca"})
span = trace.span(name=tool_name, input=sanitized_args, output=truncated_result, metadata={"latency_ms": latency_ms, "outcome": outcome, "error": error})
client.flush()

## PII redaction

Redact values for keys matching: body, message, content, password, secret, token, key. Replace with "[REDACTED]". Keep action, tool, query, url, name keys.

## Tests

Tests already written at `assays/test_langfuse_audit.py`. All 8 tests must pass. Run: cd ~/germline && python -m pytest assays/test_langfuse_audit.py -v

## Key files
- metabolon/membrane.py -- SensoryMiddleware (lines 125-257), add Langfuse call in finally block
- metabolon/server.py -- existing RequestLogger pattern to follow
- metabolon/audit.py -- NEW file to create
- assays/test_langfuse_audit.py -- tests (already written)

## Constraints
- ASCII only in all output
- Never break existing tool call flow
- Langfuse is optional -- if keys not set, everything works as before"`
- [ ] `golem --max-turns 15 "Fix three shell-safety bugs in ~/germline/effectors/golem. READ the file first. Bug 1 -- ZSH GLOB: queue entries like golem [t-a82f01] fail because zsh expands brackets as glob. Fix: add --task and --tag flags to the while loop at line 166. --task TASKID sets GOLEM_TASK_ID (same as the bracket parser does), --tag TAGNAME sets new env var GOLEM_TASK_TAG. Keep the existing bracket regex (lines 157-163) for backwards compat with programmatic callers that quote properly. Bug 2 -- SECOND BRACKET DROPPED: queue entries have a second bracket alias e.g. [t-phenotype] but only the first is parsed. After the existing bracket block (line 163), add a loop: while next arg matches bracket pattern, if it looks like a hex ID set GOLEM_TASK_ID, if it looks like a name set GOLEM_TASK_TAG. Add task_tag to the JSON log line at ~line 524. Bug 3 -- NON-ASCII CORRUPTION: em-dashes and curly quotes in prompts get mangled to ??? when passed through shell argv. Add a sanitize step after the prompt is captured (~line where prompt is assembled): replace em-dash with --, en-dash with -, curly quotes with straight quotes, and any remaining non-ASCII with space. Use sed or bash parameter expansion. Test: (a) run golem --task t-test01 --tag t-fix --max-turns 1 echo hello and verify env vars, (b) create a temp file with em-dash in a golem prompt, verify it gets sanitized. Commit with message 'golem: shell-safe task IDs, tag parsing, and ASCII sanitization'. (retry)"`
- [!] `golem [t-a82f01] [t-phenotype] --provider zhipu --max-turns 15 "Improve tmux tab renaming in ~/germline/membrane/cytoskeleton/phenotype_rename.py. READ the file first (155 lines). Currently extracts first 3 content words after stopword filtering. Improve the algorithm while keeping it fully deterministic (no LLM): (1) FILE PATHS — detect tokens containing / or ~ or ending in .py/.md/.js/.sh etc. Extract the basename (stem without extension), split snake_case parts. Prioritize these tokens. (2) ACTION VERBS — move fix/debug/refactor/deploy/build/test/update/migrate/revert from STOP set to a new ACTION set. If the first content word is an action verb, keep it as the first token in the label (e.g. fix-rheotaxis not just rheotaxis). (3) SNAKE_CASE/CamelCase SPLITTING — before stopword filtering, split tokens on _ and on camelCase boundaries (re.sub(r'([a-z])([A-Z])', r'\1 \2', word)). Each part enters the word pool individually. (4) QUOTED STRINGS — extract text inside single or double quotes first. If found, use quoted content as the primary token source. (5) Keep existing slash-command logic unchanged. (6) Keep 20-char truncation. Priority order for token selection: quoted strings > file basenames > action verb + next content words > plain content words. Test: cd ~/germline && uv run pytest assays/test_phenotype_rename.py -x -q. All 16 tests must pass (13 currently pass, 3 file-path tests are the new contract). Commit with message 'phenotype_rename: smarter token extraction for tmux tab names'. (retry)"`
- [!] `golem [t-4376dc] [t-dispatch01] --provider zhipu --max-turns 50 "Build the golem_dispatch MCP enzyme at ~/germline/metabolon/enzymes/golem_dispatch.py. READ the existing golem_queue.py enzyme at ~/germline/metabolon/enzymes/golem_queue.py for the pattern (FastMCP @tool, EffectorResult/Secretion types, QueueResult). READ the spec at ~/germline/loci/plans/temporal-direct-dispatch.md for full requirements. READ ~/germline/effectors/temporal-golem/cli.py for the Temporal client pattern (connect to TEMPORAL_HOST, start_workflow, list_workflows). The enzyme must: (1) import temporalio.client and connect to TEMPORAL_HOST env var (default ganglion:7233). (2) Expose actions: dispatch (single task), batch (multiple specs as JSON), status (workflow_id), list (limit), cancel (workflow_id). (3) Use _start_workflow, _get_workflow_status, _list_workflows, _cancel_workflow as internal async helpers called via asyncio.run(). (4) Register as @tool(name='golem_dispatch'). (5) Return QueueResult with output string and data dict, or EffectorResult on error. (6) Import GolemDispatchWorkflow from temporal-golem workflow.py — use sys.path.insert to add ~/germline/effectors/temporal-golem/. Test: cd ~/germline && uv run pytest assays/test_golem_dispatch_enzyme.py -x -q. All tests must pass. Commit with message 'golem_dispatch: MCP enzyme for direct Temporal dispatch'. (retry)"`
- [!] `golem [t-e01d4e] [t-syncheck01] --provider zhipu --max-turns 15 "Add a golem script syntax pre-check to ~/germline/effectors/temporal-golem/worker.py. READ the file first. In the run_golem_task activity function, BEFORE running the golem subprocess, add a syntax check: run subprocess.run(['bash', '-n', str(GOLEM_SCRIPT)], capture_output=True, timeout=5). If it returns non-zero exit code, skip the golem run entirely and return a result dict with exit_code=-1, success=False, stderr='golem script has syntax error: <stderr output>'. This prevents cascading failures when golem is broken. Add test test_golem_syntax_precheck to ~/germline/assays/test_temporal_dispatch.py: mock subprocess.run to return exit_code=2 for bash -n, verify the activity returns immediately without running golem. Test: cd ~/germline && uv run pytest assays/test_temporal_dispatch.py -x -q. Commit with message 'temporal: golem syntax pre-check before dispatch'. (retry)"`

- [!] `golem [t-3444cd] [t-regcap2] --provider zhipu --max-turns 25 "Execute the spec at ~/germline/loci/plans/regulatory-capture-v2.md — read it fully first. The current broken scraper is at ~/germline/effectors/regulatory-capture — read it to understand the structure, then rewrite per the spec. The BRDR page content is plain text extractable via urllib (no Playwright needed). Test: cd ~/germline && uv run pytest assays/test_regulatory_capture.py -x -q. Commit with message 'regulatory-capture: rebuild for BRDR, add relevance filter and dedup'. (retry)"`
- [!] `golem [t-4839b6] [t-evident02] --provider zhipu --max-turns 15 "Execute the spec at ~/germline/loci/plans/golem-article-analysis-training.md — this is batch 2 with the revised structured extraction format (Use cases, Talent moves, Peer benchmarks, Narrative, Quotable). Read the spec fully, then process each of the 5 briefs. Commit with message 'golem: evident batch 2 structured extraction'. (retry)"`
- [!] `golem [t-bbbeaa] [t-qdefault] --provider zhipu --max-turns 20 "Execute the spec at ~/germline/loci/plans/golem-queue-by-default.md — read it first, then implement all three changes. The golem script is at ~/germline/effectors/golem, the worker at ~/germline/effectors/temporal-golem/worker.py, tests at ~/germline/assays/test_temporal_dispatch.py. Read all three fully before making changes. Test: cd ~/germline && uv run pytest assays/test_temporal_dispatch.py -x -q. Commit with message 'golem: queue by default, --direct for immediate execution'. (retry)"`
- [!] `golem [t-1c1752] [t-evident01] --provider zhipu --max-turns 15 "Execute the spec at ~/germline/loci/plans/golem-article-analysis-training.md — read it first, then process each of the 5 Evident briefs per the instructions. Read the reference card at ~/epigenome/chromatin/chemosensory/cards/2026-03-28_synced_fa02b788.md for quality calibration. This is a training run to test article analysis quality — follow the card format and verification steps exactly. (retry)"`
- [x] `golem [t-f4fb0d] [t-gmail01] [t-batchfetch] --provider zhipu --max-turns 15 "Optimize search() in ~/germline/metabolon/organelles/gmail.py to use batch API instead of N+1 individual get() calls. READ the file first. Currently search() calls messages().list() then loops over results calling messages().get() one at a time. Use googleapiclient.http.BatchHttpRequest to fetch all messages in parallel (batch of up to 100). Keep the same return format — one line per message from _format_message(). Also add pagination support: if the list response contains 'nextPageToken', keep fetching until max_results is reached or no more pages. Same for threads=True mode — batch the threads().get() calls. Test: cd ~/germline && uv run pytest assays/test_gmail_organelle.py -x -q. All 13 existing tests must still pass. Commit with message 'gmail: batch fetch and pagination for search'."`
- [!] `golem [t-63011d] [t-gmail02] [t-htmlstrip] --provider zhipu --max-turns 10 "Improve HTML stripping in _decode_body() in ~/germline/metabolon/organelles/gmail.py. READ the file first. Current approach uses re.sub(r'<[^>]+>', ' ', html) which leaves <style> and <script> content visible. Fix: (1) Remove <style>...</style> and <script>...</script> blocks entirely (re.sub with re.DOTALL). (2) Replace <br>, <br/>, </p>, </div>, </tr> with newlines before stripping other tags. (3) Collapse multiple newlines to max 2. Keep html_mod.unescape() call. Test: cd ~/germline && uv run pytest assays/test_gmail_organelle.py -x -q. The test_html_only_strips_tags test must still pass, plus add a new test test_html_strips_style_script that verifies <style> and <script> content is removed. Commit with message 'gmail: improve HTML tag stripping'. (retry)"`
- [!] `golem [t-6bbe50] [t-gmail03] [t-attachsend] --provider zhipu --max-turns 15 "Fix attachment support in send_email() in ~/germline/metabolon/organelles/gmail.py. READ the file first. Currently when attachments is provided, it creates MIMEMultipart and attaches MIMEText(body) but never attaches the actual files. Fix: for each path in attachments, read the file, guess MIME type with mimetypes.guess_type(), create the appropriate MIMEBase part, base64-encode the payload, add Content-Disposition header, and attach to msg_mime. Add a new test in assays/test_gmail_organelle.py: test_send_with_attachment — create a temp .txt file, call send_email with it as attachment, verify the MIME message contains the file content. Test: cd ~/germline && uv run pytest assays/test_gmail_organelle.py -x -q. Commit with message 'gmail: implement file attachment in send_email'. (retry)"`
- [!] `golem [t-533251] [t-endofix] --provider zhipu --max-turns 25 "Fix remaining invoke_organelle references in two test files. READ metabolon/enzymes/endosomal.py first — it now calls gmail.search(), gmail.get_thread(), gmail.archive(), gmail.mark_read(), gmail.create_label(), gmail.send_email(), and endosomal_organelle.classify() directly instead of the old invoke_organelle(gog, args) wrapper. The tests still mock invoke_organelle which no longer exists. Files to fix: (1) assays/test_enzymes_endosomal.py — 19 remaining monkeypatch.setattr(mod, 'invoke_organelle', ...) calls in TestSearch, TestThread, TestArchive, TestMarkRead, TestLabel, TestSend, TestFilter classes. Replace each with the appropriate mod.gmail.X mock. Tests that assert CLI arg lists like ['gmail', 'search', 'is:unread', '--plain'] must change to assert the mock was called with the right Python args (e.g. mock_search.assert_called_with('is:unread')). (2) assays/test_endosomal_enzyme.py — tests use mock_invoke_organelle fixture (now aliased to mock_gmail). Update test assertions from mock_invoke_organelle.assert_called_once() to mock_gmail.search.assert_called_once() etc. The autouse fixture in test_enzymes_endosomal.py already mocks the new API correctly — use it as reference. Run: cd ~/germline && uv run pytest assays/test_enzymes_endosomal.py assays/test_endosomal_enzyme.py -x -q. Target: 0 failures. Commit with message 'fix: update endosomal tests to mock gmail API instead of invoke_organelle'. (retry)"`

- [x] `golem [t-e04a28] --provider zhipu --max-turns 10 "Add Telegram alert on repeated Temporal connection failures in ~/germline/effectors/temporal-golem/dispatch.py. READ the file first. In poll_loop(), after the line that logs CRITICAL for 5+ consecutive connection failures, call the efferens MCP tool or shell out to send a Telegram message. Use subprocess.Popen(['python3', '-c', 'from metabolon.organelles.telegram import send_message; send_message(\"[soma] temporal-dispatch: Temporal server unreachable after 5+ poll cycles\")'], cwd=os.path.expanduser('~/germline')) with a 10s timeout, fire-and-forget (don't block the poll loop). Only send once per failure streak — add a boolean _conn_alert_sent that resets when consecutive_conn_failures resets to 0. Test: add test_conn_failure_telegram_alert to assays/test_temporal_dispatch.py — mock subprocess.Popen and verify it's called after 5 OSError exceptions in the poll loop, and NOT called again until failures reset. Run: cd ~/germline && uv run pytest assays/test_temporal_dispatch.py -x -q. Commit with message 'temporal: telegram alert on connection failure streak'. (retry)"`
- [!] `golem [t-3dd62b] --provider zhipu --max-turns 5 "Strip (retry) suffix from task prompts before dispatch in ~/germline/effectors/temporal-golem/dispatch.py. READ parse_pending_tasks(). After the prompt is extracted (~line 349, after the re.sub chain), add: prompt = re.sub(r'\s*\(retry\)\s*', '', prompt). This prevents the literal string (retry) from being sent to GLM as part of the task description. Test: add test_retry_suffix_stripped to assays/test_temporal_dispatch.py — write a queue file with a (retry) task, call parse_pending_tasks(), assert the returned prompt does not contain '(retry)'. Run: cd ~/germline && uv run pytest assays/test_temporal_dispatch.py -x -q. Commit with message 'temporal: strip (retry) from prompts before dispatch'."`

### Completed

- [x] t-a68919 (gather1) — cytokinesis gather report
- [x] t-a869e4 — golem-daemon early kill for rate-limited subprocesses
- [x] t-c5c3ee — soma-health CPU check
- [x] t-744a2b — golem-daemon dedup guard
- [x] t-be76a0 (postgate) — temporal post-golem verification gate
- [x] t-61b002 (timeout2) — golem wall-limit to prevent SIGTERM
- [x] t-df1e60 (resume2) — temporal partial-progress detection
- [x] t-c5eef9 (pollfix) — temporal poller stalling fix
- [x] t-ca2248 (cachfix) — temporal stale failure cache fix
- [x] t-ff66cc (gitsync) — temporal auto git sync
- [x] t-2e1979, t-39661e, t-b08088, t-246f7e, t-2fea4f, t-5c27ea — DROPPED/superseded

## Extract shared Google auth module

**Context:** `gmail.py` and `circadian_clock.py` both have near-identical `_get_credentials()`, `service()`, `GOG_TOKEN_FILE`, thread lock patterns. Same OAuth client, same token.json, different scopes. Inelegant duplication.

**Task:** Create `metabolon/organelles/google_auth.py`:
- Single `_get_credentials(scopes)` function — env vars (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`) or fallback to `~/.config/vivesca/token.json` (rename from gog)
- `get_service(api, version, scopes)` — cached per (api, version) tuple, thread-safe, auto-refresh
- Copy token.json from `~/.config/gog/token.json` to `~/.config/vivesca/token.json`, symlink old path for backwards compat

Then refactor both organelles:
- `gmail.py`: replace `_get_credentials`, `service()`, imports with `from .google_auth import get_service; svc = get_service("gmail", "v1", GMAIL_SCOPES)`
- `circadian_clock.py`: same pattern with `("calendar", "v3", CALENDAR_SCOPES)`
- Remove `GOG_TOKEN_FILE`, `_service_lock`, `_cached_service` from both — all in google_auth now

**Test:** `python3 -c "from metabolon.organelles.gmail import service; print(service())"` and `python3 -c "from metabolon.organelles.circadian_clock import service; print(service())"` both work. Then restart vivesca and verify `circadian list` MCP tool still works.

**Files:** `metabolon/organelles/google_auth.py` (new), `metabolon/organelles/gmail.py` (edit), `metabolon/organelles/circadian_clock.py` (edit)

## Add description/location support to circadian_clock.schedule_event

**Context:** `schedule_event()` only takes title, date, time, duration. The MCP enzyme (`circadian.py`) passes description and location but logs "description ignored by circadian_clock". Had to use manual API call to add description to GARP exam event.

**Task:** Add optional `description` and `location` params to `schedule_event()` in `metabolon/organelles/circadian_clock.py`. Add them to the `body` dict if provided. Update the MCP enzyme in `metabolon/enzymes/circadian.py` to pass them through instead of logging "ignored".

**Test:** `python3 -c "from metabolon.organelles.circadian_clock import schedule_event; eid = schedule_event('Test', '2026-04-20', '10:00', description='test desc', location='Home'); print(eid)"` — then verify event has description via `scheduled_events_json('2026-04-20')`. Delete the test event after.

**Files:** `metabolon/organelles/circadian_clock.py` (edit), `metabolon/enzymes/circadian.py` (edit)

## Retire fasti Rust binary

**Context:** fasti is a Rust binary (`~/.cargo/bin/fasti`) that wraps gog CLI for calendar operations. Now that `circadian_clock.py` uses direct Google Calendar API and the MCP `circadian` tool works, fasti is redundant. The `fasti` skill still references it.

**Task:**
1. Update `membrane/receptors/fasti/SKILL.md` to route through MCP `circadian` tool instead of the fasti binary
2. Remove the symlink `~/germline/effectors/fasti -> ~/.cargo/bin/fasti`
3. `cargo uninstall fasti` if installed
4. Check if any other skills/hooks reference `fasti` CLI and update them to use MCP circadian

**Test:** Run `/fasti list` or equivalent — should work via MCP, not the binary.

**Files:** `membrane/receptors/fasti/SKILL.md` (edit), `effectors/fasti` (delete symlink)

- [!] `golem [t-99c328] --max-turns 20 "Expand navigator MCP tool (~/germline/metabolon/enzymes/navigator.py) to expose more agent-browser CLI features. READ navigator.py first. Also read npm package agent-browser-mcp source (https://github.com/minhlucvan/agent-browser-mcp) for schema design reference. Current state: 3 actions (extract, screenshot, check_auth) wrapping agent-browser CLI via _run_ab(). Add: (1) screenshot — add optional viewport (w,h,scale) and device (name) params, run 'agent-browser set viewport/device' before capture. (2) Rename extract to navigate, keep extract as alias. (3) click — css_selector param, runs 'agent-browser click SELECTOR'. (4) fill — css_selector + value, runs 'agent-browser fill SELECTOR VALUE'. (5) eval — js param, runs 'agent-browser eval JS', returns result. (6) resize — width/height/scale, runs 'agent-browser set viewport'. (7) snapshot — runs 'agent-browser snapshot', returns a11y tree. (8) check_auth — keep as-is. Keep _run_ab() pattern and porta integration. Update MCP param schema. Don't break existing callers. Write tests in ~/germline/assays/test_navigator.py. Test: run tests. Commit with message 'navigator: expose full agent-browser feature set via MCP'. (retry)"`
- [ ] `golem [t-6d273e] --max-turns 15 "Add provider round-robin to golem batch dispatch. READ ~/germline/effectors/golem first — find the fallback chain logic. Current behavior: cascade (zhipu until exhausted -> volcano until exhausted -> infini). Fix: when dispatching multiple tasks, rotate providers round-robin (task 1 -> zhipu, task 2 -> volcano, task 3 -> infini, task 4 -> zhipu...). Add a GOLEM_ROTATION=round-robin env var (default off for backwards compat). When set, the dispatch loop assigns providers cyclically from the available provider list instead of cascading. Test: add test in ~/germline/assays/ that verifies round-robin assignment. Commit with message 'golem: round-robin provider rotation for batch dispatch'."`
- [x] `golem [t-70a35e] --max-turns 15 "Build golem queue MCP tool as a new enzyme at ~/germline/metabolon/enzymes/golem_queue.py. READ ~/germline/loci/golem-queue.md first to understand the format — it's a markdown file with '### Pending' section containing '- [ ]' / '- [x]' / '- [!]' entries, each wrapping a golem command. The MCP tool should expose these actions: (1) list — parse golem-queue.md, return pending/completed/failed tasks with IDs and short descriptions. (2) add — takes task_id, provider (default zhipu), max_turns (default 15), prompt. Appends a properly formatted '- [ ] golem [ID] ...' entry to Pending section. Uses fcntl lock per feedback_queue_write_lock.md. (3) remove — takes task_id, removes the entry. (4) status — takes task_id, returns its checkbox state and prompt. (5) complete — takes task_id, changes '- [ ]' to '- [x]'. (6) fail — takes task_id, changes '- [ ]' to '- [!]'. Queue path: ~/germline/loci/golem-queue.md. Register as FastMCP tool following the pattern in other enzymes. Test: ~/germline/assays/test_golem_queue_enzyme.py — test add/list/remove/complete against a temp queue file. Commit with message 'golem-queue: MCP tool for queue management'. (retry)"`
- [ ] `golem [t-3422b1] --max-turns 15 "Add quota reservation to golem preflight checks. READ ~/germline/effectors/golem first — find the rate-limit/preflight section. Current: dispatches until provider is exhausted, then falls back. Fix: (1) Read rate-limit log to estimate remaining quota per provider. (2) Add GOLEM_RESERVE_SLOTS=3 env var — if remaining slots for a provider <= reserve, skip it for batch dispatch (still available for ad-hoc). (3) Add GOLEM_BATCH_CAP=30 env var — max tasks per batch run, prevents exhausting all providers. Log skipped providers and remaining quota. Test: add test that verifies batch cap and reserve logic. Commit with message 'golem: quota reservation and batch cap for provider scheduling'."`

