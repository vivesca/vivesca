---
name: mitogen
description: Dispatch golem for any build task — bulk campaigns or single features. "build", "implement", "dispatch", "go build", "blitz", "batch"
model: opus
user_invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
context: inline
epistemics: [audit, delegate, verify]
---

# /mitogen — Autonomous Bulk Dispatch Campaign

Biology: a mitogen is a signal that triggers rapid cell proliferation. `/mitogen` is the signal that tells the organism to mass-produce improvements autonomously.

## When to trigger

User says: "build", "implement", "dispatch", "spec this", "batch", "go build", "blitz", "keep going while I'm away", or invokes `/mitogen` directly.

**Two modes:**
- **Directed** — user specifies what to build → skip to Phase 2
- **Autonomous** — user says "blitz" / "work on everything" → Phase 1 audit first

## Process

### Phase 1: Identify work (CC judgment)

CC decides what needs doing. Examples:
- **Test gaps**: cross-reference `metabolon/` vs `assays/` (use Glob/Grep or inline script)
- **Refactoring**: read code, identify targets
- **Reliability**: find modules missing error handling
- **Consulting readiness**: assess what's missing for Capco

CC produces a task list. Each task = one golem prompt.

### Phase 2: Dispatch golem

```bash
# Tests
golem --batch module1.py module2.py module3.py

# Any task
golem "Refactor X to extract Y into a separate module"
golem "Add error handling to all MCP tools in metabolon/enzymes/"
golem "Read chromatin/X and write a summary to loci/Y"
```

Golem reads, writes, runs, fixes. No spec files, no sortase, no worktrees.

CC's role: decide what to build, verify results, fix anything golem can't.

Excess tasks that can't run now → add to `loci/golem-queue.md`. The queue is drained by golem-daemon or by `/circadian` morning dispatch.

### Phase 3: Verify + commit

```bash
uv run pytest --co -q | tail -3          # count
uv run pytest assays/test_new*.py -q     # verify new files
git add assays/test_*.py && git commit
```

### Phase 4: Report

```
## Mitogen Report
- Tests before/after: X → Y (+Z)
- New test files: [list]
- Pass rate: N/N
- Failures fixed: N
```

## Golem

`golem` = headless Claude Code + GLM-5.1 via ZhiPu (free, unlimited).

```bash
golem "any task"                          # single prompt
golem --batch mod1.py mod2.py             # sequential test generation
golem --max-turns 30 "complex task"       # more turns for big modules
```

CC's tools (Read, Write, Edit, Bash) with no size limits, no session DB contention, 200K context, 131K max output.

## Gotchas

- **Cap concurrent golems at 4-5.** ZhiPu API rate limits at ~10+ concurrent. 19 golems → 429 across all sessions. 4-5 is the sweet spot.
- **Golem hits max-turns on complex tasks.** Test-only tasks fit in 20 turns. Feature tasks (read + implement + test + verify) need `--max-turns 30`. 1000+ line modules need `--max-turns 40`.
- **Golem may not commit.** Check `git status` after batch and commit new files.
- **Don't over-orchestrate.** No spec files, no coaching injection, no worktrees, no test-spec-gen. Just `golem "task"`.

## Anti-patterns

- Don't write specs for golem — just give it a prompt
- Don't use sortase/translocon for test generation — golem is simpler and better
- Don't add guardrails — let golem be autonomous
- Don't use CC for work golem can do — CC judges, golem writes
