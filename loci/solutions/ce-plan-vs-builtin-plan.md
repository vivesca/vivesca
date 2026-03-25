# CE Plan vs Built-in Plan Mode

**Decision: Default to `/workflows:plan` for all non-trivial coding tasks.**

## The Experiment

Ran both planners on grapho (multi-command Rust CLI). Built-in `EnterPlanMode` was run first in a prior session; then `/workflows:plan` was run on the same spec. Delta was significant.

## What CE Plan Adds That Built-in Plan Misses

| Area | Built-in plan | CE plan |
|---|---|---|
| Institutional gotchas | None | `learnings-researcher` scans `~/docs/solutions/` |
| Reference project patterns | None | `repo-research-analyst` reads actual code |
| Crate versions | Guessed (dirs = "5") | Verified (dirs = "6") |
| Agent-first output | Not mentioned | Surfaced from `agent-first-cli.md` |
| Implementation ordering | Not specified | Parser tests before commands |
| Codex-specific gotchas | Not mentioned | Surfaced from overflow |

## The Mechanism

CE plan runs two parallel research agents:
- `learnings-researcher` → scans `~/docs/solutions/` for prior art and gotchas
- `repo-research-analyst` → reads reference projects for exact patterns

Built-in plan is a single-model think-through — no KB access, no code reading.

## Cost/Benefit

- Cost: ~2 min of research time (runs in parallel, unattended)
- Benefit: catches gotchas before delegation, not during; compounds with every solution captured in KB

## Rule

`EnterPlanMode` only for:
- Single-file, ≤3 commands, no architecture decisions
- Requires live user decisions mid-plan (back-and-forth)

Everything else → `/workflows:plan`.
