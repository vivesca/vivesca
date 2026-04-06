---
name: heuretes
effort: high
description: >-
  Agent research org — run a hierarchical team of AI agents on open-ended research or
  exploration tasks. Chief orchestrator + parallel junior agents on git worktrees.
  Use when the task is investigative/exploratory rather than well-specified implementation.
  Inspired by Karpathy's nanochat agent research org pattern (Mar 2026).
triggers:
  - "research agents"
  - "agent org"
  - "parallel research"
  - "heuretes"
  - "explore this with agents"
---

# heuretes — Agent Research Org

Use this when you have an **open-ended research question** (not a spec-driven coding task).
Examples: "what's the best approach to X?", "explore these 3 options and tell me which wins", "find out why Y is slow", "survey what others are doing about Z".

For well-specified coding tasks, use `rector` + CE plan instead.

## When to Use

| Use heuretes | Use rector |
|---|---|
| Open-ended question, unknown answer | Known goal, needs implementation plan |
| Multiple plausible approaches to compare | Single best approach already chosen |
| Result is a recommendation or insight | Result is working code or a file |
| You want agents to discover something | You want agents to build something |

## The 80/20 Rule (Karpathy)

> "80% of the time: work in the setup you're comfortable with that actually works.
> 20% of the time: explore the next level up even if it doesn't work yet."

Don't run heuretes for everything. Reserve it for genuinely open questions.

## Autonomous vs Monitored

The trend toward long-running autonomous agents is real — but Karpathy runs his research org **long-running but watched**, not fire-and-forget. The deciding factor is whether the **correctness signal is fast and cheap**:

| Signal type | Mode | Example |
|---|---|---|
| Automated eval (loss, test pass) | Autonomous — fire and forget | nanochat perf loop, CI test runs |
| Human judgment required | Monitored — check findings as they land | Research synthesis, experiment comparison |
| No clear success criterion | Human-led short sessions | Architecture decisions, creative direction |

**Rule: automate where you can verify cheaply. Monitor where you can't.**

For us: TaskCreate + TaskOutput covers monitoring without a tmux grid. Read findings as they land; TaskStop if a track goes sideways.

---

## Org Structure

```
You (human) — scientific judgment, question framing, result review
    |
    Chief Orchestrator (Claude Opus, this session)
    — decomposes question into parallel research tracks
    — assigns tracks to junior agents
    — synthesises results, merges wins, discards noise
        |
        ├── Junior Agent A (Claude/Codex, own worktree)
        ├── Junior Agent B (Claude/Codex, own worktree)
        └── Junior Agent C (Claude/Codex, own worktree)
```

**Key insight (Karpathy):** Agents are excellent at well-scoped investigation but bad at open-ended experiment design. The human must provide the scientific framing — what to vary, what to hold constant, what counts as a win.

---

## Setup

### 1. Frame the research question

Before spinning up agents, write down:
- **Question**: what exactly are you trying to find out?
- **Tracks**: 2–4 parallel angles to investigate (agents handle one each)
- **Success criterion**: what answer/output would satisfy you?
- **Scope cap**: max time or token budget per agent

Bad framing: "research AI agent frameworks"
Good framing: "compare LangGraph vs raw Claude Tasks for our use case: parallel web research with vault writes. Criterion: which produces cleaner output with less prompt overhead?"

### 2. Spin up worktrees (if code is involved)

```bash
# One worktree per research track
lucus new research/track-a
lucus new research/track-b
lucus new research/track-c
```

For pure research (no code changes), skip worktrees — use `/tmp/research-{track}/` as scratch.

### 3. Write the brief for each junior agent

Each junior gets a file: `/tmp/research-{track}/brief.md`

Template:
```markdown
# Research Brief: [Track Name]

## Question
[Specific sub-question for this track]

## Your task
[Concrete investigation steps — web search, read docs, test X, compare Y]

## What to produce
[Exact output format: comparison table / prose summary / code snippet / benchmark numbers]

## Constraints
- Max: [time/tokens]
- Do NOT: [scope exclusions]
- Hold constant: [what to keep fixed for comparability]

## Write results to
/tmp/research-[track]/findings.md
```

### 4. Launch agents

Via Task (background):
```
TaskCreate: Research track A — [brief summary]
```

Or via tmux panes for visibility (Karpathy style):
```bash
# New pane per agent — you can watch and intervene
tmux split-window -h "env CLAUDECODE= claude --dangerously-skip-permissions -p \"$(cat /tmp/research-a/brief.md)/""
```

### 5. Monitor and synthesise

As results come in, read `/tmp/research-{track}/findings.md` per agent.

Chief synthesises:
- What did each track find?
- Where do findings converge? Where do they conflict?
- Apply `trutina` for conflicting evidence.
- What's the answer to the original question?

---

## Known Failure Modes (from Karpathy)

| Agent failure | Human intervention needed |
|---|---|
| Doesn't control for confounders | You specify what to hold constant in brief |
| Runs "more = better" variations | You define the comparison axis explicitly |
| No baseline established | You mandate a baseline in the brief |
| Spurious wins (bigger model trains slower = lower loss) | You review results critically, not just accept them |
| Ideas lack originality | You supply the creative hypothesis; agent tests it |

**Rule:** Agents implement and test. Humans generate hypotheses and judge validity.

---

## Communication Pattern

No shared state between junior agents. All comms via files:
- Input: `brief.md` (written by chief before launch)
- Output: `findings.md` (written by junior when done)
- Handoff: chief reads all `findings.md` and synthesises

This is simpler and more reliable than agents talking to each other.

---

## After the Research

1. Write synthesis to vault: `analyze` skill or direct vault note
2. If a clear winner emerged → feed into `rector` for implementation
3. Update `karpathy-agent-research-org.md` with what worked/didn't
4. Ask: *"did this agent org config produce results efficiently? what would I change?"* — this is the meta-benchmark

---

## Reference

- Karpathy's tweets: https://x.com/karpathy/status/2027521323275325622
- Solutions KB: `~/docs/solutions/ai-tooling/karpathy-agent-research-org.md`
- nanochat repo: https://github.com/karpathy/nanochat
