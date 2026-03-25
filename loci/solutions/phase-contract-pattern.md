# Phase Contract Pattern

**LRN-20260306-001** — Formalized multi-phase subagent orchestration with strict JSON contracts.

Source: jeremylongshore/claude-code-plugins-plus-skills orchestration doc + Anthropic's building-effective-agents guide.

## The Problem

Monolithic prompts for complex tasks suffer from:
- **Attention dilution** — model attends to 60k tokens at once, quality degrades
- **Context pollution** — early reasoning artifacts corrupt later steps
- **No recovery** — failure at step 4 means restart from step 1
- **No verification** — can't inspect intermediate work

## The Pattern

Split work into isolated phases. Each phase gets a **fresh context** with only what it needs, produces a **file artifact** + **JSON summary**, and the orchestrator validates the contract before proceeding.

```
Phase 1 (fresh context, 8k tokens)
  → report_1.md + JSON summary
    ↓
Phase 2 (fresh context, reads JSON from P1)
  → report_2.md + JSON summary
    ↓
Phase 3 (fresh context, reads JSON from P2)
  → final output
```

## Contract Structure

Every phase agent must return exactly:

```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/NN-report.md",
  "phase_data": {
    "key_metric": "value",
    "findings": ["...", "..."]
  }
}
```

On failure:
```json
{
  "status": "failed",
  "error": "What went wrong",
  "partial_work": "/path/to/partial-output.md"
}
```

**If status is `"failed"`, the pipeline stops immediately.** Restart from that phase, not from the beginning.

## Phase Agent Prompt Template

```
# Phase N: [Name]

## Input Contract
You will receive:
- `session_dir`: Absolute path to write your report
- `previous_outputs`: JSON from prior phases (paste inline)

## Procedure
[Step-by-step instructions — be explicit, no ambiguity]

## Output Contract

### File
Write a markdown report to: `{session_dir}/0N-report-name.md`

Required sections: Summary, Detailed Findings, Key Takeaways

### JSON Return
Return ONLY this JSON (no prose after):
{
  "status": "complete",
  "report_path": "...",
  "phase_data": { ... }
}
```

## When to Use This Pattern

Use phase contracts when:
- Task has 3+ sequential steps where each step depends on the previous
- Individual steps are complex enough to dilute attention if combined
- You want fail-fast gates (stop on first phase failure, not at the end)
- Recovery matters — you may need to restart mid-pipeline

Skip phase contracts for:
- Simple 1-2 step tasks
- Parallel independent work (use `lucus` swarm instead)
- Tasks where context accumulation is an advantage (e.g. incremental code review)

## Integration with Existing Workflow

In `rector`:
1. CE plan decomposes the work into phases
2. Each phase becomes a Task subagent with a contract
3. Orchestrator validates JSON output before launching the next phase
4. On failure: surface the phase report, fix the issue, rerun that phase only

**vs. lucus swarm:** Phase contracts are for *sequential* dependent work. Lucus swarm is for *parallel* independent work. These are complementary — a complex task might use both (parallel data-gathering phases feeding a sequential synthesis pipeline).

## Example: 3-Phase Code Analysis

```bash
# Phase 1: inventory (Haiku — fast, cheap)
# Prompt: "List all public API methods in src/. Output JSON: {methods: [...]}"
# Output: phase1-inventory.md + JSON

# Phase 2: scoring (Sonnet)
# Prompt: "Given these methods (paste JSON from P1), score each for complexity. Output JSON: {scores: [...]}"
# Output: phase2-scores.md + JSON

# Phase 3: recommendations (Sonnet)
# Prompt: "Given scores (paste JSON from P2), write refactor recommendations."
# Output: phase3-recommendations.md
```

Each runs as a background Task. Orchestrator checks status before launching next phase.

## References
- [Building Effective Agents — Anthropic](https://www.anthropic.com/research/building-effective-agents)
- [jeremylongshore orchestration pattern](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/blob/main/workspace/lab/ORCHESTRATION-PATTERN.md)
- Related: `~/skills/delegate/SKILL.md` (tool routing), `~/skills/lucus/SKILL.md` (worktrees for parallel phases)
