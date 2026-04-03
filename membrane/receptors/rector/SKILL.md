---
name: rector
description: Structured on-ramp for delegate-first dev work. Use at the start of any coding task. Runs solutions KB check → research → spec analysis → plan → delegate → verify → review → finish.
triggers:
  - rector
  - build
  - port
  - fix
  - refactor
  - implement
  - do it
user_invocable: true
---

# /rector — Delegate-First Dev Workflow

Orchestrate here, execute elsewhere. Full reference: `~/docs/solutions/rector-reference.md`

## Triggers

- `/rector <task description>` — start a coding task the right way
- `/rector --yolo <task>` — skip plan review (personal tools, low blast radius)
- Proactively when user asks to build, port, fix, refactor, or add a feature
- **After consilium/brainstorm/design discussion when user says "implement", "build", "do it"** — prior discussion is NOT a plan, always start here

## Steps

### −1. Should we build at all?

**Default: yes.** Bias toward building, not scripting. If a task will recur even twice, build a proper tool (CLI, skill). Build cost is low (delegated), purge cost is near-zero (`deleo`). The question isn't "is this worth a CLI?" — it's "would I write this script again?"

| Signal | Action |
|--------|--------|
| Will run this logic >1 time | Build a proper CLI or skill |
| Ad-hoc data wrangling, truly once | Inline Python/bash is fine |
| Unsure | Default to building — purge cost is `deleo`, rewrite cost is an hour |

### 0. Pre-flight

- **Data governance:** can this code leave the machine? No `.env`, secrets, proprietary code.
- **Parallel sessions?** → `lucus new <branch>` first.
- **Naming?** → HARD GATE: name before code. Check registry availability (PyPI/crates.io). See `artifex`.
- **Agent-readiness:** (1) build/test <30s? (2) heavy magic (ORM, metaclasses)? (3) errors explicit? Fix before delegating.

### 1. Solutions KB check

```bash
cerno "<topic or tool name>"
```

### 1.5. Scope checkpoint

If >30 min exploring with no code/delegation started → flag it. One sentence: "We've been exploring for [X] min — the primary deliverable is [Y]. Continue or build?"

**Context reset:** If session >90 min or context >60% → suggest dump state to `/tmp/<project>-handoff.md` + `/clear`.

### 2. Choose weight class

| Task size | Use |
|-----------|-----|
| **Trivial** (≤20 lines, no existing code touched) | Build directly in-session |
| Single-file, live user decisions needed | `EnterPlanMode` → delegate |
| **New project** (blank repo) | `superpowers:brainstorming` → `superpowers:writing-plans` → delegate |
| **Spec already written** | Skip to delegation with spec as prompt |
| **Multi-file, existing codebase** | Full pipeline (below) — default for non-trivial builds |
| Needs vault context mid-execution | `/slfg` or `subagent-driven-development` |
| Unclear requirements | `/workflows:brainstorm` first |

**`--yolo` mode:** Skip plan review when ALL of: personal tool, blast radius = only Terry, spec is clear, no architecture decisions. CE research still runs.

**HARD GATE — EnterPlanMode only when:** single file, no new types/enums, no propagating signature changes, user must make live decisions.

### The Full Pipeline

> **Planning theory:** consult `bouleusis` skill when designing plans — goal clarity, simulation depth, failure modes, commitment timing.

```
RESEARCH → SPEC ANALYSIS → PLAN → EXECUTE → VERIFY → REVIEW → FINISH
```

**1. Research** (cheap, parallel subagents):
- `learnings-researcher` + `repo-research-analyst` — surfaces KB gotchas + codebase patterns

**2. Spec analysis** (one Opus pass):
- Gaps, assumptions, acceptance criteria. Skip for trivial/clear specs.

**3. Planning** (one Opus pass — consult `mandatum` for spec quality and decomposition depth):
- `superpowers:writing-plans` — TDD tasks, file structure, exact commands
- Write `AGENTS.md` to repo root (build/test/conventions for context-free delegates: Codex, Gemini, OpenCode)
- If the project needs Claude Code-specific context (session rules, skill references, vault pointers), write a separate `CLAUDE.md` — don't symlink to AGENTS.md. Different audiences, different content.
- For multi-session projects: start `claude-progress.txt` (append-only log)

**4. Execution** (FREE by default — NEVER use in-session agents for implementation):
- **HARD GATE: Do NOT use in-session general-purpose agents for coding.** The whole point of writing a detailed plan is so a context-free delegate can execute it. In-session agents burn Max20 tokens for work external tools do for free.
- **Always route through opifex** — even single-task delegations. This ensures every execution is logged for the feedback loop.
  ```bash
  # Write spec to file, then:
  opifex exec /tmp/<name>-plan.md -p <project-dir> -b <backend> --test-command "<test>"
  ```
- Backend selection: `-b gemini` (default/boilerplate), `-b codex` (Rust, hard bugs), `-b opencode` (bulk). Details: `rector-reference.md`
- **Fallback:** if opifex fails (infra issue, not task issue), fall back to raw CLI (`gemini -p "$(cat /tmp/plan.md)"`) — but note the gap in logging.
- **In-session subagents** (`subagent-driven-development`): ONLY when vault context or live user decisions are needed mid-execution — not as a convenience shortcut.
- **Agent Teams** (TeamCreate): when true coordination needed (shared API design, exploratory refactor, unknown-scope bugs)

**5. Verify** (hard gate — if something fails, consult `diagnosis` skill before shotgunning fixes):
- [ ] Tests pass — paste actual output
- [ ] Binary runs — smoke test real invocation
- [ ] No regressions — full test suite
- [ ] Matches spec — re-read requirement, compare
- Evidence must be in chat. "It works" is not evidence.

**6. Review** (Sonnet subagents, routed by file type):
- `.py` → kieran-python, `.rs` → kieran-rust, `*auth*` → security-sentinel always
- Then: pattern-recognition → code-simplicity (YAGNI last, consult `parsimonia` for essential vs accidental complexity)
- **Adversarial pass:** "3 most likely production failures"
- **Severity tags:** Blocker (stops PR) / Major (accept-risk) / Minor (optional)

**7. Finish:**
- Clean commits, PR creation (`gh pr create`), companion skill + GitHub push
- Skip for: personal tools on main, single-commit changes

### 5. Companion skill + GitHub repo

Create `~/skills/<name>/SKILL.md` in the same session — gotchas are freshest now.

```bash
mkdir -p ~/skills/<name>
# write SKILL.md, then:
cd ~/skills && git add <name>/SKILL.md && git commit -m "feat: add <name> skill" && git push
```

GitHub backup every session: `cd ~/code/<name> && git push` (or `gh repo create terry-li-hm/<name> --private --source . --push`).

### 6. Compound (if non-obvious solve)

`/workflows:compound` — captures learnings in `~/docs/solutions/`.

## Hard Rules

- **Prior discussion ≠ plan.** Always run cerno + research first.
- **No freestyle specs.** Non-trivial delegation requires a plan (`superpowers:writing-plans` or `EnterPlanMode`), not an ad-hoc prompt in `/tmp/`. The trivial exception (≤20 lines, single file) still applies. Burned: theoria daily cadence spec had rollup format gaps that a structured planning pass would have caught.
- **Never write non-trivial code in-session** without proposing delegation first.
- **One task per delegation.** 3 tasks = 3 delegates.
- **Don't inline full files.** Give paths, let delegates read.
- **Write tests** for any non-trivial fix or feature.
- **Challenge the premise.** "What can this do that the existing approach can't?"
- **Review `git diff --stat`** after Gemini delegates — it touches extra files.
- **Planning needs eyes.** CLI wrappers (`claude --print`) can't plan — no tool access. Planning stays in-session.

## Language Selection

**Default: Python.** Rust only when: CPU-bound, startup speed, extending existing Rust tool. Capco/client = always Python. Full: `~/docs/solutions/rust-vs-python-heuristic.md`.

## Troubleshooting

See `~/docs/solutions/rector-reference.md` for: routing tables, launch commands, context packaging checklist, systematic debugging, troubleshooting quick reference, parallel delegation pipeline details, Agent Teams patterns, post-delegate checklist.

Also: `~/docs/solutions/delegation-reference.md` for tool-specific gotchas.

## Boundaries

- Do NOT execute substantial implementation directly in-session except when delegation is blocked.
- Do NOT skip planning because prior discussion exists.
- Stop after orchestration, delegation, review routing, and companion-skill capture.
