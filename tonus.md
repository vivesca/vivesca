# Tonus
<!-- Max 15 lines. Full overwrite at each /wrap. Stale after 24h. -->
<!-- Dual-ledger: Facts = what we know. Progress = where we are. -->

## Facts (established)
- **Capco Day 1: Apr 8 (Tuesday). Tomorrow.**
- **Test-first dispatch policy live.** mtor gate rejects build tasks without test file reference. CC writes tests, ribosome implements.
- **mtor resilience spec written.** SHA gate, auto-heal, chaining — dispatched. v2+v3 stall detector tests written.
- **Stall root cause found:** not stalls — fast failures (TypeError, CancelledError) with no log written. Log-write fix + workflow timeout approved and merged.
- **`/blitz` skill created.** North-star-driven work discovery. Interactive (discuss) + autopilot (routine). Replaces mitogen's autonomous mode.

## Progress (active)
- [done] Overnight stall diagnosis + worker restart + ganglion sync (9 commits merged)
- [done] Test-first gate in mtor dispatch.py + coaching update
- [done] TTY detection for mtor bare invocation, pyright config for test files
- [done] Zombie workflow killed (terminate vs cancel gap found)
- [running] 7 mtor tasks: auto-heal, Langfuse deploy, terminate cmd, standalone config, chaperone test gate, rheotaxis routing, scan module
- [running] 3 new dispatches: task ID (harness+model+slug), v2 stall detector, v3 stall trace
- [parked] soma germline dirty: cli.py, dispatch.py, pyproject.toml, polysome/pyproject.toml, mitogen, blitz, 4 test files — needs commit
- [parked] SHA gate + chaining rejected (stall detector killed them) — re-dispatch after v2 detector lands
<!-- last checkpoint: 07/04/2026 ~13:20 HKT (cytokinesis full) -->
