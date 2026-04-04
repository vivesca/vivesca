---
name: taxis
description: Architecture of the Claude Code enforcement and knowledge system. Consult when adding hooks, rules, or deciding where knowledge lives.
---

# System Design

How the Claude Code setup enforces rules, stores knowledge, and compounds learning. Consult before adding a new hook, rule, or knowledge artifact.

## Architecture Overview

Five layers, three hard gates, two soft gates:

| Layer | Mechanism | Strength | Adds friction? |
|-------|-----------|----------|----------------|
| OS Sandbox | Kernel filesystem/network restrictions | Hard gate | Silent |
| Hooks (19 files, 6 event types) | PreToolUse deny / PostToolUse warn / context inject | Hard gate | Deny or warn |
| Permission rules | settings.json deny/ask/allow | Hard gate | Prompt |
| CLAUDE.md + MEMORY.md | Always in context, every turn | Soft gate | None |
| Skills + Vault | Loaded on demand | Soft gate | None |

Full details: `~/docs/solutions/enforcement-ladder.md`

## When to Hook vs When to Rule

**Hook immediately (first violation)** if ALL of these are true:
- Mechanically enforceable (regex pattern on a Bash command)
- Near-zero false positives (unambiguous signal)
- The deny message can teach the correct alternative

Examples: tool selection (anam not python), command flags (--chat with wacli), dangerous ops (safe_rm before rm -rf).

**MEMORY.md rule first** if ANY of these are true:
- Detection is fuzzy or context-dependent
- Judgment is required (tone, approach, timing)
- No clean Bash command to intercept

Escalate to hook after 2 entries in `~/docs/solutions/rule-violation-log.md`.

**Why lean aggressive on hooks:** Hooks fire on an AI agent, not humans. No morale cost, no workaround culture. The deny message is the teaching mechanism. False positives are cheap — explain and adjust. (Oxford council, Feb 2026.)

## Where Knowledge Lives

| Type | Location | Loaded | Example |
|------|----------|--------|---------|
| Hard rule ("always/never") | CLAUDE.md | Every turn | "Never run tccutil reset" |
| Gotcha ("X breaks when Y") | MEMORY.md | Every turn | "Glob ** on ~ times out" |
| Procedure (trigger + steps) | Skill | On invocation | `/legatum`, `/morning` |
| Deep reference | `~/docs/solutions/` | On lookup | Browser automation patterns |
| Project context | Vault notes | On lookup | `[[Capco Transition]]` |
| Conversation memory | Oghma | Via `cerno` | "What did we discuss about X" |
| Vault semantic search | QMD | Via `cerno` | Note discovery |

**The one-sentence test:** If it fits in one sentence → MEMORY.md. If it has a trigger + multiple steps → skill. If it's deep reference → solutions. See `artifex` for full placement heuristics.

**MEMORY.md budget:** 200-line hard truncation, **80-line target**. Currently ~66 lines. Archive dir: `~/epigenome/marks/archive/`.

**Marks budget:** Active marks target <=350. Currently ~340. Archive for stale/completed/merged marks.

**Three tiers of permanence:**
- **Permanent** — errors I'd repeat weekly without the reminder (date/time, specs, grep scoping). Never demote.
- **Active** — gotchas tied to current projects or tools. Demote when project ends or tool changes.
- **Provisional** — single-incident lessons. If not cited in 4 weeks → archive. Archived marks cited again → promote back.

**Contextual loading (genome rule):** When starting work on a tool/skill/domain, grep marks for the tool/skill name and skim top 2-3 hits. Same pattern as epistemics. Not by remembering, but by looking.

**Weekly review (in `/weekly`):** Mark decay scan — grep session logs for MEMORY.md behavioral marks. 4+ weeks uncited → archive candidate. Cited archive marks → promote back.

**Monthly review (in `/monthly`):** Archive rotation — scan archive for 3+ months uncited → permanent delete. Cited archive marks → promote back.

## Hook Inventory

All hooks live in `~/.claude/hooks/`, configured in `~/.claude/settings.json`. **19 hook files, 27 PreToolUse deny rules + 7 PostToolUse watchers, covering all 6 event types.**

### Hook Taxonomy

Five kinds of hook, matched to purpose:

| Kind | Mechanism | Output | When to use |
|------|-----------|--------|-------------|
| **Guard** (`-guard.js`) | PreToolUse deny | JSON → block | Mechanically detectable rule with near-zero FP |
| **Watcher** | PostToolUse stderr | Warning | Pattern detection after the fact (loops, budget) |
| **Formatter** (`post-edit-*`) | PostToolUse execSync | Autofix | Language-specific formatting on save |
| **Injector** | UserPromptSubmit stdout | Context | Add info to every prompt (memories, reminders, routing) |
| **Sentinel** | Stop/PreCompact/Notification | Warning/log | Boundary checks (session end, before compaction) |

When adding a new hook, pick the kind first — it determines the event type, output mechanism, and whether it blocks or warns.

### PreToolUse — Guards (4 hooks)

| Hook | Tool | Rules | What it guards |
|------|------|-------|----------------|
| `bash-guard.js` | Bash | 21 | rm without safe_rm, tccutil reset, grep/find on ~, credential exfil, wacli --chat, session JSONL, npm→pnpm, uv --force→--reinstall, pip→uv, public gists, wacli send, force-push main, gog send/reply/forward, bird tweet/post/reply/dm, network exfil (curl POST, scp, nc), secrets in args (API keys, tokens, private keys), agent-browser (localhost, financial, creds in URL), rm vault notes, curl\|bash, **git footguns (reset --hard, clean -f, checkout --, restore .)**, **lazy commit messages** |
| `glob-guard.js` | Glob | 1 | `**` recursive patterns on `/Users/terry` (times out) |
| `write-guard.js` | Write/Edit | 2 | Writes to sensitive files (.secrets, .env, .pypirc, credentials.json, keychain), **past daily notes (immutable records)** |
| `read-guard.js` | Read | 3 | Reads of sensitive files, **lockfiles (pnpm-lock, package-lock, Cargo.lock, etc.)**, **binary/minified files (.sqlite, .min.js, .zip, etc.)** |

**Pattern:** Parse `data.tool_input`, regex match, call `deny(reason)` to block.

```javascript
// Good: high-precision, teaches the alternative
if (/\.claude\/projects\//.test(cmd) && /\.jsonl/.test(cmd)) {
  deny('Use `anam search "query" --deep` instead of hand-parsing session JSONL files.');
}
```

**Design rules:**
- Deny message MUST include the correct alternative (not just "don't do this")
- Test: `echo '{"tool_input":{"command":"..."}}' | node ~/.claude/hooks/bash-guard.js`
- Hooks are cached at session start — edits take effect next session
- Never use `npx` fallbacks in hooks — latency fires on every edit

### PostToolUse — Watchers + Formatters (7 hooks)

| Hook | Matcher | Purpose |
|------|---------|---------|
| `post-edit-format.js` | Edit/Write on `.js/.jsx/.ts/.tsx` | Runs local prettier |
| `post-edit-typecheck.js` | Edit/Write on `.ts/.tsx` | Runs tsc --noEmit (filtered to edited file) |
| `post-edit-python-format.js` | Edit/Write on `.py` | Runs ruff format |
| `post-edit-rust-format.js` | Edit/Write on `.rs` | Runs rustfmt (requires Cargo.toml) |
| `stuck-detector.js` | Edit/Write/Bash/NotebookEdit | Detects loops: same call 3x, same error 2x, A-B alternation 6 steps. Warns via stderr. |
| `memory-budget.js` | Edit/Write on `MEMORY.md` | Counts lines, warns via stderr if >150 |
| `push-reminder.js` | Bash | After `git commit`, warns if ≥3 unpushed commits |

**Pattern:** Read-only (can't deny). Use `console.error()` for warnings, `execSync()` for formatters.

### UserPromptSubmit — Injectors (4 hooks)

| Hook | Purpose |
|------|---------|
| `auto-learning.sh` | Reminds to capture non-obvious learnings |
| `oghma-session-inject.py` | Injects top Oghma memories + project CONTEXT.md for cwd (debounced 30min) |
| `url-skill-router.py` | Detects URLs, routes to domain-specific skills (LinkedIn, X, Taobao) |
| `time-gate.js` | After 9pm HKT, suggests /daily via stderr |

**Pattern:** `stdout` = injected into conversation. `stderr` = informational only.

### Stop — Sentinels (2 hooks)

| Hook | Purpose |
|------|---------|
| `session-end-reminder.js` | Suggests /daily (after 9pm) or /retro (daytime) |
| `dirty-repos.js` | Warns about uncommitted changes in officina, skills, notes |

### PreCompact — Sentinel (1 hook)

| Hook | Purpose |
|------|---------|
| `pre-compact.js` | Warns about dirty repos + stale NOW.md (>24h) before context is lost |

### Notification — Sentinel (1 hook)

| Hook | Purpose |
|------|---------|
| `notification-logger.js` | Logs background task notifications to `~/logs/notification-log.jsonl` |

## Hook Effectiveness vs Activity

**Hook fires ≠ effective hook.** A deny log only tells you the hook is active. Effectiveness requires knowing what happened *after* the deny:

- **Decay rate** — same rule firing less each week → rule being internalized (teacher). Constant rate → permanent guardrail. Both are fine, but know which you have.
- **Recidivism** — same rule fires 2+ times within minutes → deny message is unclear or the alternative is hard. Fix the message.
- **Zero fires** — either working perfectly or dead code. Verify with a test occasionally.

All 4 guards log to `~/logs/hook-fire-log.jsonl`. `/weekly` step 9 surfaces decay trends.

## Enforcement Anti-Patterns

- **Rule without enforcement path:** "Be concise" in MEMORY.md with no way to detect violations. Either accept it's advisory or find a hookable proxy.
- **Hook without deny message:** Silent blocks confuse the agent. Always explain what to do instead.
- **Duplicated rules:** Same rule in MEMORY.md AND a skill AND solutions. Pick one canonical location, reference from others.
- **MEMORY.md bloat:** Budget is ~150 lines (120 current). Aggressive hooks *reduce* MEMORY.md pressure by moving enforcement to a hard gate. Overflow → `~/docs/solutions/memory-overflow.md`.
- **Soft rule for a hard problem:** If the same MEMORY.md rule gets violated twice, it's proven that soft guidance isn't enough. Don't add a third line to MEMORY.md — build a hook.
- **Over-engineering hooks for one-time mistakes:** Not every error is a pattern. If it won't recur, don't hook it.

## Learning Capture Flow

```
Discovery during session
    ↓
UserPromptSubmit hook reminds: "capture non-obvious learnings"
    ↓
Route to most specific location:
    Tool gotcha → ~/docs/solutions/
    Cross-session context → MEMORY.md
    Skill workflow → the skill's SKILL.md
    Rule violation → ~/docs/solutions/rule-violation-log.md
    ↓
/legatum meta-sweep catches anything missed
    ↓
Weekly /skill-review checks for staleness
```

## Compounding Patterns

- **Instance → Pattern → Principle:** Most learnings stop at instance. Explicitly ask "is this a pattern?" after the third occurrence.
- **Promote Oghma hits to MEMORY.md:** If cerno surfaces the same Oghma memory 3+ times, it's stable enough for MEMORY.md.
- **Demote stale MEMORY.md entries:** Weekly review in `/weekly`. Two weeks uncited → demote to overflow. Overflow cited 2+ weeks → promote back.
- **Hook as MEMORY.md pressure relief:** Every rule that graduates to a hook is one fewer line competing for attention in MEMORY.md.

## See Also

- `~/docs/solutions/enforcement-ladder.md` — full ladder with examples
- `~/docs/solutions/rule-violation-log.md` — violation tracking
- `~/skills/artifex/SKILL.md` — how to design skills
- `~/epigenome/chromatin/Councils/LLM Council - Hook-First Enforcement - 2026-02-27.md` — Oxford debate on hook aggressiveness
