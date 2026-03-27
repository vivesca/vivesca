---
name: replication
description: Hierarchical agent research org for open-ended exploration on git worktrees.
triggers:
  - "research agents"
  - "agent org"
  - "parallel research"
  - "heuretes"
  - "explore this with agents"
context: fork
epistemics: [research, delegate]
---

# heuretes — Agent Research Org

Use for **open-ended research questions** — "what's the best approach to X?", "explore these 3 options", "find out why Y is slow". For well-specified coding tasks, use `rector` + CE plan instead.

## When to Use

| Use heuretes | Use rector |
|---|---|
| Open-ended question, unknown answer | Known goal, needs implementation plan |
| Multiple plausible approaches to compare | Single best approach already chosen |
| Result is a recommendation or insight | Result is working code or a file |

## Autonomous vs Monitored

| Signal type | Mode | Example |
|---|---|---|
| Automated eval (loss, test pass) | Autonomous — fire and forget | perf loop, CI test runs |
| Human judgment required | Monitored — check findings as they land | Research synthesis, comparison |
| No clear success criterion | Human-led short sessions | Architecture decisions |

**Rule: automate where you can verify cheaply. Monitor where you can't.**

TaskCreate + TaskOutput covers monitoring. Read findings as they land; TaskStop if a track goes sideways.

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

Agents are excellent at well-scoped investigation but bad at open-ended experiment design. The human must provide the scientific framing — what to vary, what to hold constant, what counts as a win.

---

## Setup

### 1. Frame the research question

Before spinning up agents, define:
- **Question**: what exactly are you trying to find out?
- **Tracks**: 2–4 parallel angles (one agent each)
- **Success criterion**: what answer would satisfy you?
- **Scope cap**: max time or token budget per agent

Bad: "research AI agent frameworks"
Good: "compare LangGraph vs raw Claude Tasks for parallel web research with vault writes — which produces cleaner output with less prompt overhead?"

### 2. Spin up worktrees (if code is involved)

```bash
lucus new research/track-a
lucus new research/track-b
```

For pure research (no code), skip worktrees — use `/tmp/research-{track}/` as scratch.

### 3. Write the brief for each junior agent

Each junior gets `/tmp/research-{track}/brief.md`:

```markdown
# Research Brief: [Track Name]

## Question
[Specific sub-question for this track]

## Your task
[Concrete steps — web search, read docs, test X, compare Y]

## What to produce
[Exact output: comparison table / prose summary / benchmark numbers]

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

Or tmux panes for visibility:
```bash
tmux split-window -h "env CLAUDECODE= claude --dangerously-skip-permissions -p \"$(cat /tmp/research-a/brief.md)\""
```

### 5. Monitor and synthesise

Read `/tmp/research-{track}/findings.md` as results land. Chief synthesises: what each track found, where findings converge/conflict, final answer. Write synthesis to vault; clear winner → feed into `rector` for implementation. Ask: "did this agent org config produce results efficiently?" — that's the meta-benchmark.

No shared state between juniors. All comms via files: `brief.md` in, `findings.md` out.

---

## Known Failure Modes

| Agent failure | Human intervention |
|---|---|
| Doesn't control for confounders | Specify what to hold constant in brief |
| Runs "more = better" variations | Define comparison axis explicitly |
| No baseline established | Mandate a baseline in the brief |
| Spurious wins | Review results critically, not just accept them |
| Ideas lack originality | Supply the creative hypothesis; agent tests it |

**Rule: agents implement and test. Humans generate hypotheses and judge validity.**
