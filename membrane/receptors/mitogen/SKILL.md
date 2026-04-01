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

### Phase 0: Check daemon on soma (every session start)

**Soma is the primary compute.** All golems run there, not on the iMac.

```bash
ssh soma 'source ~/.env.fly && cd ~/germline && python3 effectors/golem-daemon status'
ssh soma 'cd ~/germline && git status --short | head -20'
ssh soma 'cd ~/germline && python3 effectors/golem-daemon stats'
```

If on soma directly:
```bash
python3 effectors/golem-daemon status
python3 effectors/golem-daemon stats
git log --oneline -10
```

**Never run full pytest from CC.** With 14k+ tests it takes 5+ minutes, and on soma multiple CC instances compete for output files. Use `golem-daemon stats` for pass/fail signal. For targeted checks, run single-file: `uv run pytest assays/test_specific.py -q`.

If daemon produced work since last session: review, commit, push. Then write next batch.

**Delegate everything possible to golems on soma** — including pytest runs, failure diagnosis, and verification. CC is the scheduler, not the executor.

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

**Prose is not golem work.** Consulting cards, case studies, briefings, playbooks, positioning papers — these are single-turn prose generation that any model can do inline in seconds. Golem's value is multi-turn tool loops (read → edit → test → fix). Never send "write a 600-word card" through golem — generate it on-demand in CC when actually needed, with live conversation context. Golem queue = tool-dependent tasks only.

**Prep for people, not domains.** When prepping for a deadline, identify the 2-3 specific people the user will meet. Write tasks that serve those interactions — not generic domain knowledge that sits unread.

CC writes fully-specified entries to `loci/golem-queue.md`. Each entry has provider, turns, and complete prompt baked in. CC does the thinking — golems do the labor.

### Phase 2: Write the queue

**Task types:**
- **Fix** — read failing test, read source, diagnose, fix, verify. `--max-turns 30`.
- **Build** — create new effector/feature/module + tests. `--max-turns 50`.
- **Test** — write tests for existing module. `--batch` or `--max-turns 30`.
- **NOT golem work** — prose generation, consulting content, briefs, cards. Generate inline in CC.

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

### Phase 3: Dispatch (on soma)

**All dispatch happens on soma via golem-daemon.** CC writes tasks to `loci/golem-queue.md`, golem-daemon drains them with per-provider concurrency limits (zhipu:8, infini:1, volcano:16).

**golem-daemon runs as a supervisor program on soma.** It polls the queue file, runs concurrent golem subprocesses, marks tasks done/failed, and handles rate-limit cooldowns automatically.

```bash
# Check daemon status
python3 effectors/golem-daemon status

# Start/stop manually (supervisor handles this normally)
python3 effectors/golem-daemon start
python3 effectors/golem-daemon stop

# Stats and maintenance
python3 effectors/golem-daemon stats
python3 effectors/golem-daemon retry-all   # re-queue all [!] as [ ]
python3 effectors/golem-daemon clean       # remove old [x]/[!] entries
```

**From iMac/Blink — write queue remotely, daemon picks up automatically:**
```bash
ssh soma 'cat >> ~/germline/loci/golem-queue.md << "EOF"
- [ ] `golem --provider zhipu --max-turns 40 "task..."`
EOF'
```

No need to trigger dispatch — daemon polls continuously. CC writes judgment into the queue from anywhere; golem-daemon executes even when CC is offline.

> **Experimental backends:** Hatchet (`effectors/hatchet-golem/`) and Temporal (`effectors/temporal-golem/`) exist as reference implementations. They add distributed coordination (useful if OCI becomes a second worker node) but have setup friction. See `finding_hatchet_self_hosted_issues.md` for known bugs. Don't use in production until the action listener subprocess issue is resolved.

### Phase 4: Verify + commit (on soma)

**Don't run full pytest as verification.** Delegate that to a golem or check `golem-daemon stats`. CC verifies by sampling: pick 2-3 changed test files and run them individually.

```bash
# Check what golems produced
cd ~/germline && git status --short | head -30
python3 effectors/golem-daemon stats

# Sample-verify (not full suite)
uv run pytest assays/test_one_changed_file.py -q

# Commit
git add -A && git status --short   # review
git commit -m "mitogen: ..."
```

From iMac:
```bash
ssh soma 'cd ~/germline && python3 effectors/golem-daemon stats'
ssh soma 'cd ~/germline && git add -A && git commit -m "golem: batch output" && git push'
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

| Provider | Model | TTFB | golem-daemon limit | Auth | Notes |
|----------|-------|------|--------------------|------|-------|
| ZhiPu (default) | GLM-5.1 | 380ms | 8 | ANTHROPIC_API_KEY | Most reliable (48% pass). Use for all critical work. |
| Infini | deepseek-v3.2 | 2.6s | 4 | ANTHROPIC_API_KEY | Good coder (78% pass). 1000 req/5hr plan limit — exhausts on mass dispatch. |
| Volcano | ark-code-latest | 11s | 16 | ANTHROPIC_AUTH_TOKEN | HK->Tokyo->SJC routing. Background/overflow only. |
| Gemini | gemini-3.1-pro | ~1s | 4 | GOOGLE_API_KEY | Uses `gemini` CLI, not claude. Momentary quota resets quickly. |
| Codex | gpt-5.3-codex | ~2s | 4 | OPENAI_API_KEY | Uses `codex exec` CLI. Needs `--dangerously-bypass-approvals-and-sandbox`. |

**Total concurrent budget: ~36 golems across 5 providers.** golem-daemon manages concurrency and rate-limit cooldowns automatically.

Priority for perishable work: ZhiPu > Gemini > Infini. Overflow: Volcano, Codex.
Provider quotas recover naturally — Infini resets every 5hr, Volcano resets on a schedule. Don't panic on quota exhaustion; golem-daemon's cooldown handles it.

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
- **Don't run full pytest from CC** — 14k+ tests = 5+ min, output files get cleaned by competing CC instances. Use `golem-daemon stats` for signal, single-file pytest for spot checks, and queue fix-golems for diagnosis
- Don't dedicate CC time to diagnosing test failures — queue a golem with "run pytest, grep errors, fix" and let it do the work
