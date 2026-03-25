# Tightening Pass Pattern

After building or reviewing any system, always ask: **"Can it be tighter?"**

## What "tighter" means

- **Single source of truth** for every piece of state (no duplicate files, no stale tables)
- **No manual steps** the CLI/tool can handle (session counts, rating caps)
- **Hard gates** over soft guidance (CLI enforces caps, not just skill instructions)
- **Dead data removed** (tables that nothing updates, config that nothing reads)
- **Symlinks resolved** to one canonical location

## The pattern

1. Build the thing
2. Get it reviewed (parallel: OpenCode for code quality, Codex for design)
3. Fix what the reviews found
4. Ask "can it be tighter?" — repeat until the answer is "no, diminishing returns"
5. Capture the final state

## When it pays off

This session: GARP quiz system went through 4 tightening rounds.

- Round 1 (reviews): MODE_THRESHOLDS aligned, 3 new commands, [drill] tags, timezone fix
- Round 2 (structural): `hard`=correct fix (68%→78% accuracy), acquisition cap in CLI, interleaving, symlink dedup
- Round 3 (cleanup): dead table removed, `rai end` command, FSRS state repaired
- Round 4: nothing left. System is tight.

Each round found real bugs the previous round missed because fixing one thing revealed the next.

## When to stop

When the remaining issues are:
- Cosmetic (naming, ordering)
- Hypothetical (concurrent writes in a single-user CLI)
- Would require new infrastructure for marginal gain

The signal: you can describe what every piece of state does, where it lives, and what updates it. No orphans, no ghosts.

## Check: has the context changed?

Before tightening, ask: "has the environment changed since this was written?" A component that was essential at creation may be redundant now. Example: the wrap skill's learnings scan was the primary capture mechanism — then the `UserPromptSubmit` hook added real-time capture, making 60% of the skill dead weight. The code was correct; the context had shifted. This is harder to spot than bugs because nothing is broken — it just does less than it costs.

## Anti-pattern: tightening without building first

Don't pre-optimize. Build, ship, then tighten. The bugs that matter only surface under real use. The GARP `hard`=incorrect bug lived for weeks unnoticed because it was baked into the initial design — no amount of upfront planning would have caught it. Real quiz sessions did.
