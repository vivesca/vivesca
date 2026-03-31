---
name: mitogen
description: Autonomous bulk improvement campaign — audit gaps, dispatch golem, verify, commit. "go build", "work on everything", "blitz"
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

User says: "go build", "work on everything", "blitz", "keep going while I'm away", or invokes `/mitogen` directly.

## Process

### Phase 1: Find gaps (CC, 1 minute)

Run the cross-reference script directly — no subagents, no exploration specs:

```bash
cd ~/germline && python3 -c "
import os, re
modules = []
for root, dirs, files in os.walk('metabolon'):
    for f in files:
        if f.endswith('.py') and f not in ('__init__.py', '__main__.py'):
            modules.append(os.path.join(root, f))
tests = set(f for f in os.listdir('assays') if f.startswith('test_') and f.endswith('.py'))
def has_test(mod):
    name = mod.split('/')[-1].replace('.py', '')
    candidates = [f'test_{name}.py', f'test_{name}_actions.py', f'test_{name}_substrate.py',
                  f'test_{name}_organelle.py', f'test_sortase_{name}.py',
                  f'test_spending_{name}.py', f'test_lysin_{name}.py',
                  f'test_endocytosis_rss_{name}.py', f'test_scaffold_{name}.py',
                  f'test_{name}_protocol.py', f'test_codons_{name}.py']
    return any(c in tests for c in candidates)
def lines(p):
    with open(p) as f: return sum(1 for _ in f)
for m, l in sorted([(m, lines(m)) for m in modules if not has_test(m) and lines(m) > 50], key=lambda x: -x[1]):
    print(m)
"
```

### Phase 2: Dispatch golem

```bash
golem --batch module1.py module2.py module3.py ...
```

That's it. Golem reads the source, writes tests, runs pytest, fixes failures. No spec files, no sortase, no worktrees.

CC's role: decide what to build, verify results, fix anything golem can't.

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

- **Golem is sequential.** Parallel golem sessions hit SQLite session DB contention (goose shares the DB). Dispatch one at a time.
- **Golem hits max-turns on very large modules.** For 1000+ line modules, use `--max-turns 30`. Or let CC write those tests directly (that IS the high-value judgment work).
- **Golem may not commit.** Check `git status` after batch and commit new files.
- **Don't over-orchestrate.** No spec files, no coaching injection, no worktrees, no test-spec-gen. Just `golem "task"`.

## Anti-patterns

- Don't write specs for golem — just give it a prompt
- Don't use sortase/translocon for test generation — golem is simpler and better
- Don't add guardrails — let golem be autonomous
- Don't use CC for work golem can do — CC judges, golem writes
