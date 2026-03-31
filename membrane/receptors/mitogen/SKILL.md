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

### Phase 0: Check daemon (every session start)

```bash
golem-daemon status                       # running? how many pending?
cd ~/germline && git status --short       # uncommitted golem output?
uv run pytest --co -q | tail -3           # test count
```

If daemon produced work since last session: review, commit, report delta. Then write next batch.

### Phase 1: Identify work (CC judgment)

CC decides what needs doing. Examples:
- **Test gaps**: cross-reference `metabolon/` vs `assays/`
- **Features**: read queue, identify gaps
- **Consulting readiness**: assess what's missing for Capco

CC writes fully-specified entries to `loci/golem-queue.md`. Each entry has provider, turns, and complete prompt baked in. CC does the thinking — golems do the labor.

### Phase 2: Write the queue

**Group related tasks into operons** — tasks that share context run in one golem session:

```markdown
#### Coverage operon — test coverage tooling
- [ ] `golem --provider infini --max-turns 50 "Read validator.py AND complement.py. Add check_test_coverage to validator. Add coverage_summary to complement. Write tests for both. Run pytest. Fix failures."`

#### Standalone
- [ ] `golem --provider volcano --max-turns 50 "Create effectors/capco-prep..."`
```

Operons save context-building time and produce coherent cross-module designs. Group when:
- Two modules share concepts (both about coverage, both about dispatch)
- One module consumes the other's output
- Changes need to be consistent across files

Keep standalone when tasks have no shared context.

### Phase 3: Dispatch

**Option A — CC dispatches directly** (interactive session):
```bash
golem --provider infini --max-turns 50 "task..."   # run_in_background: true
```

**Option B — golem-daemon drains the queue** (persistent, survives CC exit):
```bash
golem-daemon start   # reads queue, dispatches, marks done
golem-daemon status  # check progress
golem-daemon stop    # halt
```

**Use the daemon when:** CC is about to exit, overnight batch, "keep going while I'm away". The daemon's value is persistence, not intelligence — CC writes the judgment into the queue, daemon executes even when CC is offline.

**Use CC dispatch when:** interactive session, need to verify and iterate quickly.

### Phase 4: Verify + commit

```bash
uv run pytest --co -q | tail -3          # count
uv run pytest assays/test_new*.py -q     # verify new files
git add assays/test_*.py && git commit
```

### Phase 5: Report

```
## Mitogen Report
- Tests before/after: X → Y (+Z)
- New test files: [list]
- Pass rate: N/N
- Failures fixed: N
```

## Golem

`golem` = headless Claude Code dispatched across multiple providers.

```bash
golem "any task"                          # ZhiPu default
golem --provider infini "task"            # Infini (deepseek-v3.2)
golem --provider volcano "task"           # Volcano (ark-code-latest)
golem --batch mod1.py mod2.py             # sequential test generation
golem --test mod.py                       # single module test gen
golem --max-turns 50 "complex task"       # more turns for big modules
golem --full "task needing MCP"           # non-bare mode
```

### Provider config

| Provider | Model | TTFB | Concurrent limit | Auth |
|----------|-------|------|-----------------|------|
| ZhiPu (default) | GLM-5.1 | 380ms | 4-5 | ANTHROPIC_API_KEY |
| Infini | deepseek-v3.2 | 2.6s | 6-7 | ANTHROPIC_API_KEY |
| Volcano | ark-code-latest | 11s | 8+ (degrades) | ANTHROPIC_AUTH_TOKEN |

**Total concurrent budget: ~18-20 golems across all 3 providers.**

Priority: ZhiPu (fast) > Infini (good coder, decent speed) > Volcano (slow but high concurrency).

## Gotchas

- **Default turns: 50.** Test-only tasks need ~30. Feature tasks (read + implement + test + fix) need 50. 1000+ line modules may need more.
- **`--dangerously-skip-permissions` is in the golem script.** Without it, models ask for permission instead of using tools. Never remove it.
- **Golem may not commit.** Check `git status` after batch and commit new files.
- **Don't over-orchestrate.** No spec files, no coaching injection, no worktrees. Just `golem "task"`.
- **Volcano routes HK→Tokyo→SJC.** Structural, unfixable. Use for background/overflow only.
- **Infini coding plan models:** deepseek-v3.2 (2.6s, best), glm-5 (7s), glm-4.5-air (1.8s fast but weaker). kimi-k2.5/glm-4.7 are thinking models (68s), avoid.

## Anti-patterns

- Don't babysit golems — let them write+test+fix, check the final count
- Don't dispatch related tasks separately — group into operons
- Don't use CC for work golem can do — CC judges, golem writes
- Don't use shell `&` for background — use Bash tool's `run_in_background: true`
- Don't rely on shell aliases in scripts — they don't expand
