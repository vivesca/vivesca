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

**Philosophy: build fast, break things, evolve fast.** Features > tests. Fix broken things. Ship iteratively. Tests follow building, not the other way around.

## When to trigger

User says: "build", "implement", "dispatch", "spec this", "batch", "go build", "blitz", "keep going while I'm away", or invokes `/mitogen` directly.

**Two modes:**
- **Directed** — user specifies what to build → skip to Phase 2
- **Autonomous** — user says "blitz" / "work on everything" → Phase 1 audit first

## Process

### Phase 0: Check daemon on gemmule (every session start)

**Gemmule is the primary compute.** All golems run there, not on the iMac.

```bash
ssh gemmule 'source ~/.env.fly && cd ~/germline && python3 effectors/golem-daemon status'
ssh gemmule 'cd ~/germline && git status --short | head -20'
ssh gemmule 'cd ~/germline && uv run pytest --co -q 2>&1 | tail -3'
```

If daemon produced work since last session: review, commit, push. Then write next batch.

**Delegate everything possible to golems on gemmule** — including pytest runs, failure diagnosis, and verification. CC is the scheduler, not the executor.

### Phase 1: What matters? (CC judgment — do this BEFORE queuing)

**Stop and think:** what is the most impactful work right now? Check:
- **Tonus.md** — what's active, what's perishable, what deadline is next?
- **Calendar** — what's coming in 1-7 days that needs prep?
- **Broken things** — what's failing that blocks real usage?
- **User's last request** — did they ask for something specific?

Then prioritize:
1. **Perishable** — deadlines, prep work, things that lose value if delayed. Queue first.
2. **Fixes** — broken tests, regressions, bugs. Heal second.
3. **Compound infra** — improvements to the dispatch system itself. Multiplies future output.
4. **Features** — new capabilities, effectors. Build when slots are free.
5. **Tests** — coverage for untested modules. Fill remaining slots.

**Tests are filler, not the main course.** Never fill the entire queue with test generation. Always reserve slots for fixes and builds. Ask: "If I could only dispatch 5 tasks, which 5 would move the needle most?"

CC writes fully-specified entries to `loci/golem-queue.md`. Each entry has provider, turns, and complete prompt baked in. CC does the thinking — golems do the labor.

### Phase 2: Write the queue

**Task types:**
- **Fix** — read failing test, read source, diagnose, fix, verify. `--max-turns 30`.
- **Build** — create new effector/feature/module + tests. `--max-turns 50`.
- **Test** — write tests for existing module. `--batch` or `--max-turns 30`.

**Group related tasks into operons** — tasks that share context run in one golem session:

```markdown
#### Fix operon — sortase test failures
- [ ] `golem --provider zhipu --max-turns 30 "Read assays/test_sortase_actions.py. Run it. Read the source it tests. Fix all failures. Run pytest on the file. Iterate until green."`

#### Build — new effector
- [ ] `golem --provider infini --max-turns 50 "Create effectors/some-tool as Python..."`

#### Test batch
- [ ] `golem --provider zhipu --batch mod1.py mod2.py`
```

Operons save context-building time and produce coherent cross-module designs. Group when:
- Two modules share concepts (both about coverage, both about dispatch)
- One module consumes the other's output
- Changes need to be consistent across files

Keep standalone when tasks have no shared context.

### Phase 3: Dispatch (on gemmule)

**All dispatch happens on gemmule via SSH.** CC writes the queue, pushes to git, gemmule daemon picks it up.

**Option A — CC dispatches directly on gemmule:**
```bash
ssh gemmule 'source ~/.env.fly && cd ~/germline && bash effectors/golem --provider infini --max-turns 50 "task..."' &
```

**Option B — Write queue locally, push, daemon drains on gemmule:**
```bash
# 1. Write tasks to loci/golem-queue.md locally
# 2. Push
cd ~/germline && git add loci/golem-queue.md && git commit -m "queue: new tasks" && git push
# 3. Pull on gemmule and restart daemon
ssh gemmule 'cd ~/germline && git pull --ff-only && python3 effectors/golem-daemon stop; python3 effectors/golem-daemon start'
```

**Option C — Write queue directly on gemmule via SSH:**
```bash
ssh gemmule 'cat >> ~/germline/loci/golem-queue.md << "EOF"
- [ ] `golem --provider zhipu --max-turns 40 "task..."`
EOF'
ssh gemmule 'cd ~/germline && python3 effectors/golem-daemon stop; python3 effectors/golem-daemon start'
```

**The daemon runs on gemmule 24/7** — supervisor auto-restarts it. CC writes judgment into the queue from anywhere (iMac, Blink, gemmule tmux). Daemon executes even when CC is offline.

### Phase 4: Verify + commit (on gemmule)

```bash
ssh gemmule 'cd ~/germline && uv run pytest --co -q 2>&1 | tail -3'
ssh gemmule 'cd ~/germline && git add -A && git commit -m "golem: batch output" && git push'
```

Or if interactive, commit directly:
```bash
cd ~/germline && git add -A && git status --short   # review
git commit -m "mitogen: ..."
```

### Phase 5: Report

```
## Mitogen Report
- Tests before/after: X → Y (+Z)
- Failures fixed: N
- New features: [list]
- New test files: [list]
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
