# Agent Loop Design Patterns

Reference patterns observed in well-built agent systems. Useful for Capco advisory and building custom agents.

**Source:** virattt/dexter (15.8K stars), OpenHands (64K stars), gpt-researcher (25K stars), Claude Code internals.

## 1. Soft Limits + Similarity Detection (Anti-Looping)

**Problem:** Agents retry the same failing tool call, burning tokens.

**Pattern:** Track per-tool call counts and query similarity. Inject warnings into prompts — don't hard-block.

- Count calls per tool per query (suggested limit: 3)
- Jaccard word-overlap similarity on query strings (threshold: 0.7)
- When limit hit: inject warning text suggesting the agent try a different tool or proceed with what it has
- Never block — the LLM might have a good reason for retry

**Why soft > hard:** Hard blocks cause the agent to hallucinate workarounds. Soft warnings let the LLM make an informed decision.

## 2. Meta-Tool Routing (Agent-in-Agent)

**Problem:** Too many tools overwhelms the outer agent's decision-making.

**Pattern:** Bundle related tools behind a single "router" tool that uses a secondary LLM call.

1. Outer agent calls `domain_search(query: "natural language")`
2. Inner LLM has N sub-tools bound, picks the right ones
3. Selected sub-tools execute in parallel
4. Combined result returned as single response

**Tradeoffs:** Extra LLM call adds latency + cost. Worth it when sub-tool count > 5-6. Keeps outer agent loop simple.

## 3. Append-Only Scratchpad

**Problem:** Agent state gets messy across iterations. Hard to debug.

**Pattern:** JSONL append-only log as single source of truth.

- Each entry: `{ type, timestamp, toolName?, args?, result? }`
- Never modify — only append new entries
- Context clearing is in-memory only (JSONL preserved for debugging)
- Final answer generation can reload full history from disk

**Benefits:** Debuggable (just `cat` the file), resilient to crashes, audit trail for evals.

## 4. Threshold-Based Context Clearing

**Problem:** Tool results accumulate and blow the context window.

**Pattern:** Estimate tokens after each iteration. When over threshold, clear oldest N tool results but keep most recent.

- No inline summarization during reasoning (lossy)
- Cleared results marked in-memory, not deleted from scratchpad
- Final answer gets ALL results reloaded (context only needs to fit for final generation)

**Key insight:** Context management and persistence are separate concerns. The LLM doesn't need everything in context — but the system needs everything on disk.

## 5. Skills as Markdown Checklists

**Problem:** Complex multi-step workflows (DCF valuation, security audits) need structure.

**Pattern:** SKILL.md files with YAML frontmatter + markdown body containing step-by-step instructions with fallback logic.

- LLM invokes via a `skill` tool
- Skill instructions loaded into context on demand (not always in system prompt)
- Each skill runs at most once per query (dedup check)
- Steps include cross-validation and reasonableness checks

**Why markdown > code:** LLMs follow markdown checklists more reliably than coded workflow engines. The "program" is the prompt.

## 6. Stuck Detection with Concrete Thresholds (from OpenHands)

**Problem:** Agents get stuck in loops — same action repeated, alternating patterns, error retry spirals.

**Pattern:** Track recent tool calls and fire warnings at calibrated thresholds.

| Pattern | Threshold | Recovery |
|---|---|---|
| Same action + same result | 4x | Suggest different approach |
| Same action + error | 3x | Force strategy change |
| Agent self-monologue | 3x | Truncate and restart |
| Alternating A-B-A-B | 6 steps | Break with different strategy |
| Condensation loop | 10x | Hard stop |

**Implementation notes:**
- Compare actions ignoring PIDs in shell output (process IDs change between runs)
- In interactive mode, only scan since last user message
- Recovery can truncate history to the loop start point, not just the last message
- Adopted for Claude Code as PostToolUse hook: `~/.claude/hooks/stuck-detector.js`

## 7. Event-Sourced State (from OpenHands)

**Problem:** Agent state is mutable and hard to debug. Can't replay sessions.

**Pattern:** Every action and observation is an append-only Event with sequential IDs. "State" is a thin projection on top of the event log.

- Events: `{ id, timestamp, source (AGENT/USER/ENV), cause (ref to triggering event) }`
- Pub/sub with per-subscriber thread pools (slow subscriber can't block others)
- State snapshot separate from event log — snapshot for fast resume, log for replay
- Schema migrations via `__setstate__` for backward compatibility

**Two-store persistence:**
- Event store (JSONL, source of truth, never deleted)
- State snapshot (pickle/JSON, fast resume, excludes history)
- History reconstructed from event store on reload

**Key insight:** Session resume needs a compact snapshot. Session debugging needs the full log. These are different files with different lifecycles.

## 8. Condenser Strategies (from OpenHands)

**Problem:** `/compact` is manual and one-size-fits-all.

**Pattern:** Pluggable condenser strategies with different tradeoffs:

- **NoOp** — pass-through (for short sessions)
- **LLM Summarizing** — keep first N + last M events, LLM-summarize the middle using a cheaper model. Triggers at event count threshold (e.g., 120), not every turn.
- **Amortized Forgetting** — same windowing without LLM cost
- **Recent Events** — pure sliding window
- **Pipeline** — chain multiple condensers in sequence

**Why threshold-triggered > turn-triggered:** Fires at fixed event count, not every step. This preserves the unchanged prefix for prompt caching between condensation events. Claimed: quadratic → linear cost growth.

## 9. Three-Tier LLM Routing (from gpt-researcher, validated)

**Problem:** Using the same model for all tasks wastes money or quality.

**Pattern:** Route sub-tasks to different model tiers:

- **Mini** (cheap/fast) — sub-query generation, classification, formatting
- **Standard** — research execution, tool calling, synthesis
- **Reasoning** (expensive/slow) — planning, validation, final answer

**Already implemented in Claude Code as:** Haiku (lookups) → Sonnet (analysis) → Opus (judgment). gpt-researcher independently arrived at the same tiers. Validates the approach.

## 10. Hard-Gated Verification via SubagentStop Hook (from Trellis "Ralph Loop")

**Problem:** Check/review agents claim "all checks pass" without actually running them — soft prompt instructions aren't reliable.

**Pattern:** A SubagentStop hook intercepts when the check agent tries to exit. The hook either:
- Runs programmatic verify commands (from config) and blocks exit if any fail, OR
- Scans agent output for completion markers (`{REASON}_FINISH`) and blocks until all are present

Safety: max iteration counter (default 5) prevents infinite loops. State persisted to disk with timeout-based reset.

**Implementation (Trellis `ralph-loop.py`):**
1. Hook fires on `SubagentStop` event for the `check` agent only
2. Reads `worktree.yaml` for `verify:` commands (e.g., `pnpm lint`, `pnpm typecheck`)
3. If verify commands configured → runs them, blocks exit on failure with error output
4. If no verify commands → reads `check.jsonl` for expected completion markers, blocks until all found in agent output
5. State file (`.ralph-state.json`) tracks iterations per task, auto-resets on task change or 30min timeout

**Why this matters:** This is genuine hook enforcement — the agent mechanically cannot exit the loop until verification passes. Contrast with prompt-based "you must verify before finishing" which agents routinely skip. The hook decides `allow` or `block` — the agent has no say.

**Adoption note:** Requires the surrounding task system (`.current-task`, `check.jsonl`, `worktree.yaml`). Not trivially portable, but the pattern is: use SubagentStop hooks as hard gates for quality, not just PostToolUse for formatting.

**Source:** mindfold-ai/Trellis (2.5K stars, Feb 2026). Evaluated and skipped wholesale adoption (team-oriented, project-scoped, Opus-heavy), but this enforcement pattern is the cleanest implementation of "hooks > prompts for quality gates."

## 11. Declarative Per-Agent Context Manifests (from Trellis)

**Problem:** Orchestrator agents bloat their prompts trying to pass the right context to each subagent, or subagents waste tokens re-reading files they don't need.

**Pattern:** Each task declares what context each agent type needs in a jsonl manifest file:
- `implement.jsonl` — specs the implement agent needs
- `check.jsonl` — specs + check criteria for the check agent
- `debug.jsonl` — specs + error context for the debug agent

Each line: `{"file": "path/to/spec.md", "reason": "TypeCheck"}` (or `"type": "directory"` for entire dirs).

A PreToolUse hook intercepts `Task` tool calls, reads the relevant jsonl, loads all referenced files, and rewrites the subagent's prompt with full context injected. The dispatch agent stays "dumb" — it just says "implement the feature" and the hook handles context assembly.

**Benefits:**
- Dispatch prompt stays tiny (no context passing logic)
- Each agent gets exactly the specs it needs (no over/under-injection)
- Context is data-driven (edit a jsonl, not prompt templates)
- Adding a new spec to a task = one line in a jsonl, not prompt surgery

**Adoption note:** The jsonl-as-manifest idea could improve compound-engineering's context passing to review agents. Currently, review agents either get everything or rely on the orchestrator to curate. A declarative manifest per review type would be cleaner.

## Pull Beats Push for Routine Automation

**Pattern:** When automating routine information delivery (daily alerts, status digests, health summaries), pull rituals beat push notifications.

**Why:** Push interrupts at data-ready time, which rarely aligns with the human's receptive state. Pull rituals (run when winding down, morning coffee, commute) meet the human when they're already in "receive" mode.

**Example (hesper arc):** Built a 9:30pm Telegram push for evening briefing. User tested it — "Jeff Law and jobs not important." Simplified to calendar-only, then "just a skill before bed." Deleted the push binary entirely; added `fasti list tomorrow` as Step 1 of the quies wind-down skill.

**Rule of thumb:** Push = urgency (health alerts, system failures, time gates). Pull = routine (job alerts, sleep data, daily brief). If missing it has real cost → push. If it's background context → pull.

**Corollary:** Build cost is near-zero when delegated. Don't over-architect the push infrastructure — if the pull version satisfies the real need, the complexity was never justified.
