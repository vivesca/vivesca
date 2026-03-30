---
name: nucleation
description: On-ramp for coding tasks — KB check, research, plan, delegate. Not quick edits.
user_invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
context: fork
epistemics: [build, delegate]
---

# /nucleation — Delegate-First Dev Workflow

Orchestrate here, execute elsewhere. Full reference: `~/epigenome/chromatin/immunity/rector-reference.md`

## Triggers

- `/nucleation <task description>` — start a coding task the right way
- `/nucleation --yolo <task>` — skip plan review (personal tools, low blast radius)
- Proactively when user asks to build, port, fix, refactor, or add a feature
- **After quorum/transcription/design discussion when user says "implement", "build", "do it"** — prior discussion is NOT a plan, always start here

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
- **Naming?** → HARD GATE: name before code. Check registry availability (PyPI/crates.io). See `[[knowledge-structure]]`.
- **Agent-readiness:** (1) build/test <30s? (2) heavy magic (ORM, metaclasses)? (3) errors explicit? Fix before delegating.

### 1. Solutions KB check

```bash
receptor-scan "<topic or tool name>"
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
| Needs chromatin context mid-execution | `subagent-driven-development` |
| Unclear requirements | `/compound-engineering:ce-transcription` first |

**`--yolo` mode:** Skip plan review when ALL of: personal tool, blast radius = only Terry, spec is clear, no architecture decisions. CE research still runs.

**HARD GATE — EnterPlanMode only when:** single file, no new types/enums, no propagating signature changes, user must make live decisions.

### The Full Pipeline

> **Planning theory:** consult [[planning-theory]] reference doc when designing plans — goal clarity, simulation depth, failure modes, commitment timing.

```
RESEARCH → SPEC ANALYSIS → PLAN → EXECUTE → VERIFY → REVIEW → FINISH
```

**1. Research** (cheap, parallel — prefer droid explore for codebase recon):
- `droid exec -m glm-4.7 --cwd <project> "<recon prompt>"` — free codebase understanding
- `learnings-researcher` + `repo-research-analyst` — surfaces KB gotchas + codebase patterns
- Use droid for "read and summarize the code"; CC subagents only when judgment is needed mid-research

**2. Spec analysis** (one Opus pass):
- Gaps, assumptions, acceptance criteria. Skip for trivial/clear specs.

**3. Planning** (one Opus pass — see [[delegation-theory]] for spec quality and decomposition depth):
- `superpowers:writing-plans` — TDD tasks, file structure, exact commands
- Write `AGENTS.md` to repo root (build/test/conventions for context-free delegates: Codex, Gemini, Goose)
- If the project needs Claude Code-specific context (session rules, skill references, chromatin pointers), write a separate `CLAUDE.md` — don't symlink to AGENTS.md. Different audiences, different content.
- For multi-session projects: start `claude-progress.txt` (append-only log)

**4. Execution** (FREE by default — NEVER use in-session agents for implementation):
- **Planning pattern:** ReWOO → CodeAct → ReAct hybrid (stolen from production consensus). Plan cheaply with variable placeholders (Opus reasoning), execute as code (delegate to Codex/Gemini), fall back to interactive (in-session ReAct) only on delegate failure. Gets token efficiency until something breaks, then gracefully degrades.
- **Edit format matters:** instruct delegates to use unified diff format over SEARCH/REPLACE where possible. Aider benchmarked: 3x success rate. Diff format = "data for a program" (rigid); SEARCH/REPLACE = "instructions for a human" (flexible, lazier).
- **HARD GATE: Do NOT use in-session general-purpose agents for coding.** The whole point of writing a detailed plan is so a context-free delegate can execute it. In-session agents burn Max20 tokens for work external tools do for free.
- **Always route through sortase** — even single-task delegations. This ensures every execution is logged for the feedback loop.
  ```bash
  # Write spec to file, then:
  sortase exec /tmp/<name>-plan.md -p <project-dir> -b <backend> --test-command "<test>"
  ```
- Backend selection: `-b gemini` (default/boilerplate), `-b codex` (Rust, hard bugs), `-b goose` (bulk ops, GLM-5.1). Details: `rector-reference.md`
- **Fallback:** if sortase fails (infra issue, not task issue), fall back to raw CLI (`gemini -p "$(cat /tmp/plan.md)"`) — but note the gap in logging.
- **In-session subagents** (`subagent-driven-development`): ONLY when chromatin context or live user decisions are needed mid-execution — not as a convenience shortcut.
- **Agent Teams** (TeamCreate): when true coordination needed (shared API design, exploratory refactor, unknown-scope bugs) — see `~/epigenome/chromatin/immunity/rector-reference.md` for decomposition, topology, and parallelism heuristics

**5. Verify** (hard gate — if something fails, consult [[debugging-theory]] reference doc before shotgunning fixes):
- [ ] Tests pass — paste actual output
- [ ] Binary runs — smoke test real invocation
- [ ] No regressions — full test suite
- [ ] Matches spec — re-read requirement, compare
- Evidence must be in chat. "It works" is not evidence.

**6. Review** — triage depth before running anything:

| Tier | When | Steps |
|------|------|-------|
| **Full** | Auth/creds/security, new architecture, new external API | All sub-steps below |
| **Standard** | New logic, multi-file, unfamiliar domain | File-type subagents → Critic → Severity tags |
| **Quick scan** | Routine boilerplate, config, single-file cosmetic | Read diff — flag Blockers only, no subagents |
| **Spot-check** | Tests pass + no new patterns + trivial change | Verify tests, skim diff — done |

**Routing (first match wins):** path contains auth/cred/secret/token/key → Full. New module/data model/cross-service API → Full. New algorithm or >3 files → Standard. Tests pass + existing pattern + small change → Spot-check. Default → Quick scan.

Full-tier steps (Sonnet subagents, routed by file type):
- `.py` → kieran-python, `.rs` → kieran-rust, `*auth*` → security-sentinel always
- Then: pattern-recognition → code-simplicity (YAGNI last, see [[simplification]] for essential vs accidental complexity)
- **Critic pass** (stolen from Devin's Planner/Coder/Critic pipeline): dedicated adversarial review that pressure-tests for security vulnerabilities and logic errors before shipping. Not the same agent that wrote the code — fresh context, no commitment bias.
- **Adversarial pass:** "3 most likely production failures"
- **Simplicity diagnostic:** "Where did the complexity go?" Every simplification moves complexity somewhere — into the caller, a future edge case, a config file, a convention that must be documented. Name where it landed. If the answer is "nowhere", the complexity was accidental and the simplification is clean. If it landed on the user or caller, that's a trade-off worth flagging, not hiding.
- **Severity tags:** Blocker (stops PR) / Major (accept-risk) / Minor (optional)

**7. Finish:**
- Clean commits, PR creation (`gh pr create`), companion skill + GitHub push
- If new CLI built: add to `~/germline/proteome.md`. If replacing old tool: run `~/epigenome/chromatin/immunity/patterns/tool-replacement-checklist.md`.
- Skip for: personal tools on main, single-commit changes

### 5. Companion skill + GitHub repo

Create `~/germline/membrane/receptors/<name>/SKILL.md` in the same session — gotchas are freshest now.

```bash
mkdir -p ~/germline/membrane/receptors/<name>
# write SKILL.md, then:
cd ~/germline && git add membrane/receptors/<name>/SKILL.md && git commit -m "feat: add <name> skill" && git push
```

GitHub backup every session: `cd ~/code/<name> && git push` (or `gh repo create terry-li-hm/<name> --private --source . --push`).

### 6. Compound (if non-obvious solve)

`/compound-engineering:ce-compound` — captures learnings in `~/germline/loci/antisera/`.

## Hard Rules

- **Prior discussion ≠ plan.** Always run receptor-scan + research first.
- **No freestyle specs.** Non-trivial delegation requires a plan (`superpowers:writing-plans` or `EnterPlanMode`), not an ad-hoc prompt in `/tmp/`. The trivial exception (≤20 lines, single file) still applies. Burned: transduction daily cadence spec had rollup format gaps that a structured planning pass would have caught.
- **Never write non-trivial code in-session** without proposing delegation first.
- **One task per delegation.** 3 tasks = 3 delegates.
- **Don't inline full files.** Give paths, let delegates read.
- **Write tests** for any non-trivial fix or feature.
- **Challenge the premise.** "What can this do that the existing approach can't?"
- **Review `git diff --stat`** after Gemini delegates — it touches extra files.
- **Planning needs eyes.** CLI wrappers (`claude --print`) can't plan — no tool access. Planning stays in-session.

## Language Selection

**Default: Python.** Rust only when: CPU-bound, startup speed, extending existing Rust tool. Capco/client = always Python. Full: `~/epigenome/chromatin/immunity/rust-vs-python-heuristic.md`.

## Troubleshooting

See `~/epigenome/chromatin/immunity/rector-reference.md` for: routing tables, launch commands, context packaging checklist, systematic debugging, troubleshooting quick reference, parallel delegation pipeline details, Agent Teams patterns, post-delegate checklist.

Also: `~/epigenome/chromatin/immunity/delegation-reference.md` for tool-specific gotchas.

## Boundaries

- Do NOT execute substantial implementation directly in-session except when delegation is blocked.
- Do NOT skip planning because prior discussion exists.
- Stop after orchestration, delegation, review routing, and companion-skill capture.
