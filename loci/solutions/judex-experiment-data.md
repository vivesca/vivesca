# Judex Experiment Data

Empirical data points for opifex --plan vs alternatives.

## Data Points

### DP-001: thalamus (ai-landscape-review) — 2026-03-13

**Condition:** (A) opifex no planning. Spec hand-written, dispatched directly to Codex. opifex `--plan` was still being built in parallel — planning pipeline was skipped, not tested.

**Spec:** `/tmp/ai-landscape-review-spec-v2.txt` — LangGraph 5-node pipeline, 4 cadences, LaunchAgents.

**Issues found post-build (all caught by human in conversation, not by any automated review):**

| # | Issue | Category | Would planning catch? |
|---|-------|----------|----------------------|
| 1 | All cadences read raw feed — no roll-up architecture | Design judgment | Unknown — this is a "what is this for?" question |
| 2 | Double-feeding same data (lustro log + AI News Log are the same pipe) | Data flow analysis | Plausible — CE research could surface lustro's write target |
| 3 | Wrong weekday in LaunchAgent (6=Sat, not Fri) | Mechanical error | Unlikely — launchd weekday numbering is a gotcha |
| 4 | No dependency chain in scheduling (quarterly before monthly) | Design judgment | Plausible — reasoning review should catch temporal dependencies |
| 5 | Timeout too short for research node (300s with WebSearch) | Operational sizing | Unlikely without execution experience |
| 6 | Weekly at Fri 17:00 HKT misses US business day | Domain knowledge | Plausible — if prompt includes timezone awareness |

**Key insight:** Issues 1 and 4 are "purpose" questions (what is each cadence *for*?). Planning tools are good at structural completeness but weak at design judgment. The spec itself didn't specify roll-up — the planning pipeline can't catch what the spec doesn't ask for.

**Verdict:** Inconclusive — planning was skipped. Need to run the same spec through `--plan` to measure what it would have caught. See DP-002.

---

### DP-002: thalamus — retroactive `--plan` run — 2026-03-14

**Condition:** (B) opifex `--plan` (3-pass Opus) run retroactively against the original spec. Same spec as DP-001, run against `~/code/thalamus/` (which already has the fixes from DP-001).

**Execution results:**

| Pass | Status | Duration | Output |
|------|--------|----------|--------|
| 1. CE Plan | Completed | ~60s | Found 3 minor robustness issues |
| 2. Writing Plans | **Timed out (300s)** | 300s | Prompt too large (spec + CE output) |
| 3. Reasoning Review | **Never ran** | — | Blocked by Pass 2 failure |

**Pass 1 findings:**
- Found: `should_research` exact-match fragility, empty-gather guard, git commit crash handling
- **Missed all 6 design issues** from DP-001
- **Hallucinated:** claimed "correct schedules and roll-up architecture" — actually read the *already-fixed* code and rubber-stamped it
- WebSearch was blocked (nested `claude --print` inside Claude Code)

**Pipeline bugs discovered:**

| # | Bug | Impact |
|---|-----|--------|
| 1 | **Contaminated context** — ran against current project dir, not clean slate | CE plan validated existing code instead of planning from spec. Would miss issues the code already has. |
| 2 | **Pass 2/3 timeout at 300s** — prompt includes full spec + CE output | Writing-plans pass never completes. The planner has the same timeout bug it was supposed to catch in the deliverable. |
| 3 | **WebSearch unavailable nested** — `claude --print` inside CC can't search | "Research" half of CE plan is hollow — no framework docs, no gotcha lookup |

**What the planning pipeline caught:** 3 minor code robustness issues (none of which caused real failures).

**What it missed:** All 6 design/architectural issues (roll-up, double-feed, weekday, dependency chain, timeout, timezone).

**Key insight:** The planning pipeline is a code linter, not a design reviewer. It checks "is this code robust?" not "is this the right architecture?" The 6 issues the human caught were all "purpose" questions — what is each cadence *for*? What is the relationship between data sources? What timezone matters? These require domain context that the planner doesn't have and its prompts don't ask for.

**Additional insight:** The planner itself has the same class of bugs as the deliverable (timeout too short, WebSearch unavailable nested). Recursive irony — but also a signal that operational issues are only discoverable through execution, not through planning.

**Action items:**
1. Fix planner timeout (300s → 600s for passes 2 and 3)
2. Consider: should CE plan pass run against an empty dir, not the current project? (prevents rubber-stamping)
3. Consider: should the planner prompts include "what is each component FOR?" and "what are the data flow relationships?" questions?
4. The 3 robustness issues it found (should_research, empty-gather, git commit) are worth fixing in thalamus

---

### DP-003: thalamus — in-session CE plan (full tooling) — 2026-03-14

**Condition:** CE plan research agents (repo-research-analyst + learnings-researcher) run as in-session subagents with full tool access (file reads, vault search, grep). Same spec as DP-001/002.

**What the research agents surfaced vs the 6 issues:**

| # | Issue | Repo analyst | Learnings researcher | CLI planner (DP-002) |
|---|-------|-------------|---------------------|---------------------|
| 1 | No roll-up architecture | **YES** — identified hierarchy | **YES** — content-consumption pattern | MISSED |
| 2 | Double-feeding same data | **YES** — clarified lustro→News Log | No | MISSED |
| 3 | Wrong weekday in LaunchAgent | No | No | MISSED |
| 4 | No scheduling dependency | PARTIAL | PARTIAL (cron-hygiene) | MISSED |
| 5 | Timeout too short | No | No | MISSED |
| 6 | Weekly misses US EOB | No | No | MISSED |

**Score: 2.5/6 (vs CLI planner's 0/6)**

**Critical distinction:** The research agents *described correct patterns* but didn't explicitly *flag the spec as violating them*. They said "each level synthesizes across lower level" and "lustro = tool, AI News Log = file it writes to" — the information was there, but framed as context, not as warnings. Whether the plan-writing step connects "what the repo does" to "what the spec should do" is the remaining unknown.

**Key insight: the bottleneck is information → action, not information gathering.** The in-session agents surface the right knowledge (roll-up pattern, data flow). The CLI planner surfaces nothing (no file access, no vault). But even with the right information surfaced, the plan needs to *compare* it against the spec and flag contradictions. This is a prompt engineering problem in the plan-writing step, not a tool access problem.

**Verdict:** In-session CE plan research is categorically better than CLI `claude --print` planning. The tool access difference (file reads, vault grep, solutions KB) is the decisive factor. The CLI wrapper is architecturally broken for planning — it's a prompt with no eyes.

**Implications for opifex `--plan`:**
1. The CLI wrapper approach (call `claude --print` 3 times) is fundamentally limited — no tool access means no research value
2. Planning should either run in-session (CE plan skill) or the CLI should be redesigned to pass file contents into the prompt (not just the spec)
3. The plan-writing step needs explicit prompting to compare research findings against the spec and flag contradictions
4. opifex `--plan` in its current form adds ~0 design value — it's a code linter at best

---
