---
name: nucleation
description: On-ramp for coding tasks -- KB check, research, plan, delegate. Not quick edits.
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

# /nucleation -- Delegate-First Dev Workflow

Orchestrate here, execute elsewhere. Full reference: `~/epigenome/chromatin/immunity/rector-reference.md`

## Triggers

- `/nucleation <task description>` -- start a coding task the right way
- `/nucleation --yolo <task>` -- skip plan review (personal tools, low blast radius)
- Proactively when user asks to build, port, fix, refactor, or add a feature
- **After quorum/transcription/design discussion when user says "implement", "build", "do it"** -- prior discussion is NOT a plan, always start here

## Steps

### -1. Should we build at all?

**Default: yes.** Bias toward building, not scripting. If a task will recur even twice, build a proper tool (CLI, skill). Build cost is low (delegated), purge cost is near-zero (`deleo`).

| Signal | Action |
|--------|--------|
| Will run this logic >1 time | Build a proper CLI or skill |
| Ad-hoc data wrangling, truly once | Inline Python/bash is fine |
| Unsure | Default to building |

### 0. Pre-flight

- **Data governance:** can this code leave the machine? No `.env`, secrets, proprietary code.
- **Parallel sessions?** -> `lucus new <branch>` first.
- **Naming?** -> HARD GATE: name before code. Check registry availability (PyPI/crates.io).
- **Agent-readiness:** (1) build/test <30s? (2) heavy magic (ORM, metaclasses)? (3) errors explicit? Fix before delegating.

### 1. Solutions KB check

```bash
receptor-scan "<topic or tool name>"
```

### 1.5. Scope checkpoint

If >30 min exploring with no code/delegation started -> flag it.

**Context reset:** If session >90 min or context >60% -> suggest dump state to `/tmp/<project>-handoff.md` + `/clear`.

### 2. Choose weight class

| Task size | Use |
|-----------|-----|
| **Trivial** (<=20 lines, no existing code touched) | Build directly in-session |
| Single-file, live user decisions needed | `EnterPlanMode` -> delegate |
| **New project** (blank repo) | `/transcription` -> `/specification` -> `sortase exec` |
| **Spec already written** | Skip to `sortase exec` with spec as prompt |
| **Multi-file, existing codebase** | Full pipeline (below) -- default for non-trivial builds |
| Needs chromatin context mid-execution | In-session with plan mode |
| Unclear requirements | `/transcription` first |

**`--yolo` mode:** Skip plan review when ALL of: personal tool, blast radius = only Terry, spec is clear, no architecture decisions.

**HARD GATE -- EnterPlanMode only when:** single file, no new types/enums, no propagating signature changes, user must make live decisions.

### The Full Pipeline

```
RESEARCH -> SPECIFICATION -> SORTASE EXEC -> VERIFY -> REVIEW -> FINISH
```

**1. Research** (cheap, parallel -- prefer translocon for codebase recon):
- `translocon --build <project> "<recon prompt>"` -- free codebase understanding
- Check `~/germline/loci/antisera/` for prior learnings matching the domain
- Use translocon for "read and summarize the code"; CC subagents only when judgment is needed mid-research

**2. Specification** (one Opus pass -- `/specification`):
- Foldability assessment, disordered region detection, implicit constraint inference
- Write dispatch-ready spec to `~/germline/loci/plans/<name>.md`
- Spec quality gate: all sections score 4+ before proceeding
- Write `AGENTS.md` to repo root if needed (build/test/conventions for context-free delegates)

**3. Execution** (FREE by default -- route through sortase):
- **HARD GATE: Do NOT use in-session agents for implementation.** The whole point of writing a spec is so a context-free delegate can execute it.
- **Always route through sortase** for logging and feedback:
  ```bash
  sortase exec ~/germline/loci/plans/<name>.md -p <project-dir> -b <backend> \
    --verbose --test-command "<test>"
  ```
- Backend selection: `-b goose` (default, fastest), `-b gemini` (boilerplate), `-b codex` (Rust, hard bugs)
- **One task per delegation.** 3 tasks = 3 delegates.
- **Fallback:** if sortase fails (infra, not task), fall back to raw CLI -- but note the logging gap.

**4. Verify** (hard gate -- evidence before assertions):
- [ ] Tests pass -- paste actual output, not "it works"
- [ ] Binary runs -- smoke test real invocation
- [ ] No regressions -- full test suite, not just new tests
- [ ] Matches spec -- re-read requirement, compare
- Evidence must be in chat. "Should pass now" is not evidence.
- If something fails, diagnose before retrying. Consult `~/germline/loci/antisera/` for known patterns.

**5. Review** -- triage depth before running anything:

| Tier | When | Steps |
|------|------|-------|
| **Full** | Auth/creds/security, new architecture, new external API | File-type reviewers -> adversarial pass -> simplicity check |
| **Standard** | New logic, multi-file, unfamiliar domain | File-type reviewers -> severity tags |
| **Quick scan** | Routine boilerplate, config, single-file | Read diff, flag blockers only |
| **Spot-check** | Tests pass + existing pattern + trivial change | Skim diff, done |

**Routing (first match wins):** path contains auth/cred/secret/token/key -> Full. New module/data model/cross-service API -> Full. New algorithm or >3 files -> Standard. Tests pass + existing pattern + small -> Spot-check. Default -> Quick scan.

**6. Finish:**
- Clean commits, PR if warranted (`gh pr create`)
- **Propagation check:** Did the change require updating other files? Sweep:
  - Skills: `grep -rl "COMPONENT" ~/germline/membrane/receptors/*/SKILL.md`
  - Memory: `grep -rl "COMPONENT" ~/.claude/projects/-Users-terry/memory/`
  - Hooks: `grep -rl "COMPONENT" ~/germline/membrane/cytoskeleton/`
- If new CLI: add to `~/germline/proteome.md`
- If replacing old tool: run tool-replacement checklist
- If non-obvious solve: capture in `~/germline/loci/antisera/<topic>.md`

### Companion skill

If you just built a new CLI or tool, create `~/germline/membrane/receptors/<name>/SKILL.md` in this session -- gotchas are freshest now.

## Hard Rules

- **Prior discussion != plan.** Always run receptor-scan + research first.
- **Non-trivial delegation requires `/specification`.** Not an ad-hoc prompt.
- **Never write non-trivial code in-session** without proposing delegation first.
- **One task per delegation.** 3 tasks = 3 delegates.
- **Don't inline full files.** Give paths, let delegates read.
- **Write tests** for any non-trivial fix or feature.
- **Challenge the premise.** "What can this do that the existing approach can't?"
- **Review `git diff --stat`** after delegates -- they touch extra files.
- **Evidence before completion claims.** Run the verification, paste the output.

## Language Selection

**Default: Python.** Rust only when: CPU-bound, startup speed, extending existing Rust tool. Capco/client = always Python.

## Troubleshooting

See `~/epigenome/chromatin/immunity/rector-reference.md` for: routing tables, launch commands, context packaging, systematic debugging, parallel delegation.
