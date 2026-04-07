---
name: blitz
description: CC-driven work discovery — analyze organism, propose high-impact tasks, write tests, dispatch via mtor. Interactive (discuss) or autopilot (routine fixes).
triggers:
  - "/blitz"
  - "blitz"
  - "find work"
  - "what needs building"
  - "scan and dispatch"
---

# blitz — proactive work generation

CC analyzes the organism, proposes high-impact tasks, writes tests, dispatches via mtor.

## Modes

### Interactive (default): `/blitz`

CC-driven judgment, not CLI-driven grep. The best tasks come from understanding the system, not scanning for TODOs.

1. **Read North Star.md** — the 6 enduring priorities. Every task must trace back to one.
2. **Reason backward**: which north star is most underserved right now? What organism capability would move it? Career (Capco Day 1 context), health (sleep/gym tools), financial (tracking), family (scheduling) — before system meta-work.
3. **Analyze organism**: what's broken, fragile, or missing that blocks a north star? Think "what would make priority X easier" not "what TODO comments exist."
4. **Supplement with `mtor scan`**: mechanical gaps (missing tests, broken health checks) — secondary to north-star reasoning.
5. **Present**: propose 5-10 tasks, each tagged with which north star it serves. Pure meta-work (#6) limited to ~30% of tasks. Explain WHY each matters.
6. **Discuss**: user pushes back, reprioritizes, adds their own. This is a conversation.
7. **Execute**: for each approved task, CC writes `assays/test_<task>.py`, commits, dispatches.

**Anti-pattern: meta-spiral.** If all proposed tasks are system improvements (#6), stop and ask: "Is the system actually blocking a real north star, or am I polishing tools?" North Star.md is explicit: meta-work that doesn't measurably improve north star throughput is waste.

### Autopilot: `/blitz --auto`

Mechanical only — CC judgment tasks need human discussion.

1. Run `mtor scan` — mechanical gaps only
2. Auto-approve: `health`, `broken`, or `coverage` with priority >= 3
3. Skip: `stale`, `todo`, anything needing taste
4. CC writes tests → dispatch
5. Report what was dispatched and skipped

## Constraints

- NEVER dispatch without writing tests first
- Each test file must be committed before dispatch
- Autopilot only approves routine fixes — new features always need human selection
- Read North Star.md before prioritizing (align tasks with goals)
- Maximum 10 dispatches per blitz (prevent runaway)

## Example session

```
> /blitz

Scanning organism...
Found 7 tasks:

  [1] ★★★★★ BROKEN  cytokinesis: cyclopts import fails after partial migration
  [2] ★★★★☆ COVERAGE mtor deploy: no tests for deploy subcommand  
  [3] ★★★☆☆ COVERAGE rheotaxis: no test coverage for backend routing
  [4] ★★★☆☆ HEALTH   soma-watchdog: health check returns 503
  [5] ★★☆☆☆ TODO     translocase.py:445 # TODO: add retry backoff
  [6] ★★☆☆☆ STALE    mark feedback_goose_dispatch.md: 45 days old
  [7] ★☆☆☆☆ TODO     cli.py:200 # TODO: add --since to stats

Approve which tasks? (numbers, "all", or "n"):
> 1,2,3

Writing tests for 3 tasks...
  ✓ assays/test_cytokinesis_import.py (3 tests)
  ✓ assays/test_deploy.py (4 tests)
  ✓ assays/test_rheotaxis_routing.py (5 tests)

Dispatching...
  → ribosome-zhipu-a1b2c3d4: cytokinesis import fix
  → ribosome-zhipu-e5f6g7h8: mtor deploy tests
  → ribosome-zhipu-i9j0k1l2: rheotaxis routing

3 tasks dispatched. Check with: mtor list --status RUNNING
```
