# Rector Reference

Detailed reference material for `/rector`. The skill itself is the decision tree; this doc holds the how-to details.

## Pipeline Diagram

```
┌─ RESEARCH (cheap — Haiku/Sonnet subagents) ──────────────┐
│ CE: learnings-researcher + repo-research-analyst          │
│ → surfaces ~/docs/solutions/ gotchas + codebase patterns  │
│ → run in parallel, ~2min, catches institutional knowledge │
└──────────────────────────────────────────────────────────┘
          ↓ gotchas + patterns feed into spec analysis
┌─ SPEC ANALYSIS (one Opus pass) ──────────────────────────┐
│ CE: spec-flow-analyzer                                    │
│ → gaps in spec (missing error handling, edge cases)       │
│ → assumptions that should be explicit                     │
│ → acceptance criteria (functional + non-functional)       │
│ Skip for: trivial tasks, clear specs with no ambiguity    │
└──────────────────────────────────────────────────────────┘
          ↓ validated spec feeds into plan
┌─ PLANNING (one Opus pass) ───────────────────────────────┐
│ superpowers:writing-plans                                 │
│ → converts research into structured TDD task steps        │
│ → file structure, test-first, exact commands              │
│ → identifies shared artifacts (Phase 1) vs independent    │
│   tasks (Phase 2)                                         │
│ → writes AGENTS.md to repo root (build/test/conventions)  │
└──────────────────────────────────────────────────────────┘
          ↓ plan decomposes into tasks
┌─ EXECUTION (FREE — external tools or in-session) ───────┐
│ External (default): opifex / raw Codex/Gemini/OpenCode    │
│   Phase 1: Build shared artifacts sequentially, commit    │
│   Phase 2: Fan out to lucus worktrees + mixed tools       │
│   Phase 3: Validate each on completion                    │
│   Phase 4: Merge passing branches                         │
│ In-session (when vault context needed):                   │
│   superpowers:subagent-driven-development                 │
│   → fresh subagent per task + two-stage review            │
│   → burns Max20, but shares session context               │
└──────────────────────────────────────────────────────────┘
          ↓ merged code ready for verification
┌─ VERIFY (hard gate — before claiming done) ─────────────┐
│ superpowers:verification-before-completion                │
│ → tests pass (not just "should pass")                     │
│ → binary runs (smoke test real invocation)                │
│ → no regressions (full test suite, not just new tests)    │
│ → evidence in chat (paste output, not "it works")         │
└──────────────────────────────────────────────────────────┘
          ↓ verified code ready for review
┌─ REVIEW (cheap — Sonnet subagents) ─────────────────────┐
│ Route by file type (git diff --stat):                     │
│   .py → kieran-python, .rs → kieran-rust, .ts → kieran-ts│
│   *auth*/*key*/*token* → security-sentinel (always)       │
│ Then: pattern-recognition → code-simplicity (YAGNI last)  │
│ Adversarial pass: "3 most likely production failures"     │
│ Severity tags: Blocker (stops PR) / Major (accept-risk)   │
│   / Minor (optional)                                      │
└──────────────────────────────────────────────────────────┘
          ↓ reviewed code ready for cleanup
┌─ FINISH (branch cleanup + ship) ────────────────────────┐
│ superpowers:finishing-a-development-branch                │
│ → squash/rebase if needed, clean commit messages          │
│ → PR creation (gh pr create)                              │
│ → companion skill + GitHub push                           │
│ Skip for: personal tools on main, no PR workflow          │
└──────────────────────────────────────────────────────────┘
```

## Routing Tables

### Execution routing

| Signal | Tool | Why |
|--------|------|-----|
| Needs repo navigation, test loops, multi-file | **Codex** | Best developer (Terminal-Bench #1) |
| **Rust (any)** | **Codex `--sandbox danger-full-access`** | Default for Rust. Lifts DNS block, `cargo build` works. `codex exec --sandbox danger-full-access --full-auto "..."` |
| **Rust — Codex budget exhausted or code is sensitive** | **Gemini CLI** | Fallback. Runs locally, no code leaves machine. `cd ~/code/<project> && gemini -m gemini-3.1-pro-preview -p "..." --yolo` |
| Algorithmic, isolated logic, "write X that does Y" | **Gemini CLI** | AA index 57 (beats Opus 4.6 at 53), free. `gemini -m gemini-3.1-pro-preview -p "..." --yolo` |
| Bulk ops, boilerplate, routine refactoring | **OpenCode** | Free, unlimited |
| Task failed 3+ times from **reasoning difficulty** | **→ Opus in-session** | Escalation only, switch back after |
| Task failed from **sandbox constraint** (DNS, build, write access) | **→ Switch tool laterally** | Codex DNS failure → Gemini; OpenCode write block → Codex. Not a reasoning problem. |
| **Rust complex bug (diagnosis only)** | **Codex → Gemini handoff** | Codex navigates + diagnoses; Gemini builds/verifies locally. Pass Codex output as context to Gemini. |
| Routing uncertain despite benchmarks | **Run `judex` experiment** | Parallel Codex+Gemini → real evidence → update routing |

### Review routing (by file type)

Route reviewers based on `git diff --stat` output instead of running all four every time:

| File pattern | Reviewer |
|-------------|----------|
| `*.py` | kieran-python-reviewer |
| `*.rs` | kieran-rust-reviewer |
| `*.ts`, `*.tsx` | kieran-typescript-reviewer |
| `*auth*`, `*key*`, `*token*`, `*secret*` | security-sentinel (always) |
| Any change | pattern-recognition-specialist (spec compliance) |
| Last pass | code-simplicity-reviewer (YAGNI check) |

### Execution method decision tree

| Method | When | Cost |
|--------|------|------|
| **Parallel delegation** (opifex / raw Codex/Gemini/OpenCode) | Default. Self-contained specs, no vault context needed | Free |
| **superpowers:subagent-driven-development** | Tasks need session context, or plan has many small interdependent steps | Max20 (Sonnet subagents) |
| **Agent Teams** (TeamCreate) | True coordination needed — shared API design, exploratory refactor, unknown-scope bugs | Max20 |
| **`/slfg`** | Fully autonomous, no decomposition needed, vault context required | Max20 (heavy) |

### Language defaults

| Language | Default tool | Caveats |
|----------|-------------|---------|
| Rust | **Codex `--sandbox danger-full-access`** (default) / Gemini (fallback) | `--full-auto` alone keeps `workspace-write` sandbox which blocks DNS/cargo. Rust regex: no lookahead. |
| Python | Gemini or OpenCode | Use `uv` not pip. Single-file scripts: `uv run --script` shebang. |
| TypeScript | Codex or Gemini | pnpm, not npm. |
| Shell scripts | OpenCode | New `~/bin/` scripts must be Python (bash-guard). |

## Context Packaging Checklist

Delegates need to be self-sufficient:
- [ ] Absolute file paths (let delegate read, don't inline full files)
- [ ] Error output if debugging (trim to relevant lines)
- [ ] Constraints ("don't modify X", "keep existing patterns")
- [ ] Verification command ("run `cargo test` to verify")
- [ ] Anti-placeholder: "Implement fully. No stubs, no TODOs, no simplified versions."
- [ ] Prompt length: OpenCode hard limit ~4K chars, Codex ~8K chars safe
- [ ] **Patch receipt request:** "End your response with: Files touched: [...], Commands run: [...], Tests added: [...], Risks: [...]"
- [ ] **File ownership** (parallel only): "You own files X, Y, Z. Do NOT modify any other files."

## Agent-Readiness Pre-flight

Before delegating to existing codebases, check:
1. **Does build/test run in <30s?** Slow tooling is the #1 agent performance killer.
2. **Is there heavy "magic"?** (ORM, DI, metaclasses, pytest fixtures) — #1 hallucination trigger.
3. **Are errors explicit or swallowed?** Silent failures waste agent cycles.

If any answer is bad, add mitigation to the delegation prompt (explicit build steps, flag magic patterns, add error checking).

Source: [Armin Ronacher](https://lucumr.pocoo.org/2025/6/12/agentic-coding/)

## Parallel Delegation Pipeline

### Step 1 — Decompose
For each task, capture:
```
name:        short-kebab-name
spec:        full self-contained prompt (include file paths, constraints, verification cmd)
lang:        rust | python | typescript | other
validation:  cargo build && cargo test | uv run pytest | pnpm test | <custom>
```

### Step 2 — Auto-route (no asking)
Route each task by signal (see routing table). Report inline: "→ feature-a: Codex (Rust), feature-b: Gemini (new logic), feature-c: OpenCode (boilerplate)"

### Step 3 — Create worktrees + launch all in parallel
```bash
lucus new <task-a-branch>
lucus new <task-b-branch>

# Launch all simultaneously (Bash tool run_in_background: true for each)
cd <worktree-a> && codex exec --sandbox danger-full-access --full-auto "<spec-a>"
cd <worktree-b> && gemini -m gemini-3.1-pro-preview -p "<spec-b>" --yolo
```

### Step 4 — Validate as each completes
Don't wait for all — validate on notification:
```bash
cd <worktree-X> && <validation_cmd>
# Pass (exit 0): ✓, run git diff --stat
# Fail (exit ≠ 0): ✗, capture last 20 lines of error
```

### Step 5 — Summary + merge
```
Pipeline complete: N/M tasks passed
✓ feature-a   Codex    3 files   cargo test passed    2m14s
✗ feature-b   Gemini   —         build failed         3m02s
```
Merge passing branches (`lucus merge <branch>`). For failures: show error, propose retry with different delegate / fix in-session / skip. Wait for Terry's call.

## External Agent Teams Pattern

Opus orchestrates in-session (only cost), free tools execute in parallel worktrees:

```
Opus (orchestrator, in-session)
  ├── Phase 1: Build shared artifacts (sequential)
  │   └── Write shared code (embeddings.py, types, interfaces)
  │   └── Commit — worktrees only see committed history
  │
  ├── Phase 2: Fan out independent tasks (parallel)
  │   ├── lucus new task-a → Codex (multi-file)
  │   ├── lucus new task-b → Gemini (algorithmic)
  │   └── lucus new task-c → OpenCode (boilerplate)
  │
  ├── Phase 3: Validate as each completes
  │   ├── Check pyproject.toml for dep pollution
  │   ├── git diff --stat for scope creep
  │   └── Run tests
  │
  └── Phase 4: Merge passing branches, retry failures with different tool
```

**Fallback chain:**
```
Gemini 429 (quota) → Codex or OpenCode
Codex sandbox block → Gemini (runs locally) or Sonnet subagent
OpenCode auth fail → Gemini or Codex
All three down → Sonnet subagent (last resort, burns Max20)
```

**Tool diversity rule:** Never launch 3+ delegates to the same provider simultaneously.

## Parallel Delegation vs Agent Teams

Parallel delegation = **fan-out/fan-in**. Decompose → launch independent workers → collect results → merge. Workers never talk to each other. Map-reduce pattern. Works for 90% of tasks.

Agent Teams = **true coordination**. Agents share context, can message each other mid-task, adapt based on what others discover. Costs Max20.

**When Agent Teams actually helps:**

| Scenario | Why parallel delegation fails | Agent Teams adds |
|----------|------------------------------|-----------------|
| **Shared API/schema design** | Each agent invents its own interface → merge conflict | Agents negotiate the interface together |
| **Exploratory refactor** | Can't pre-decompose what you haven't understood yet | Agents discover the decomposition as they go |
| **Cross-cutting concern** | Each agent makes different choices → inconsistent | One agent sets the pattern, others follow |
| **Bug with unknown scope** | Can't assign to one agent without knowing where | Agents investigate in parallel, share findings |
| **Design feedback loop** | Parallel worker discovers issue, can't change others | Agent flags issue, team adapts |

## Phase Contract Pattern

For sequential dependent phases: `~/docs/solutions/phase-contract-pattern.md`
- Each phase runs as a fresh-context subagent → produces a file artifact + JSON summary
- Orchestrator validates JSON contract before launching next phase
- On `"status": "failed"` → stop and restart from that phase

## AGENTS.md Artifact

After CE plan runs, write a short `AGENTS.md` to repo root containing:
- Build commands (`uv run pytest`, `cargo build`)
- Test commands
- Key conventions from CLAUDE.md / CE research
- KB gotchas discovered during research

This persists across sessions — future delegates get tribal knowledge without re-running research.

Source: [AGENTS.md standard](https://github.com/agentsmd/agents.md)

## Multi-Session Progress Log

For projects spanning multiple sessions, maintain `claude-progress.txt` (append-only):
```
## YYYY-MM-DD HH:MM — [session summary]
- Completed: [what was done]
- Blocked: [what's stuck]
- Next: [what to do next session]
```

Prevents session amnesia. Source: [Anthropic long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Context Reset Trigger

If session >90 min or context >60%, suggest:
1. Dump state to `/tmp/<project>-handoff.md`
2. `/clear` and restart with the handoff file
3. Prevents late-session context degradation

## Review Severity Classification

Review agents tag each finding:
- **Blocker** — stops the PR. Must fix before merge.
- **Major** — needs documented accept-risk if not fixed.
- **Minor** — optional improvement. Fix or skip.

Add to reviewer prompts: "Classify each issue as Blocker, Major, or Minor."

## Adversarial Review Pass

After collaborative review (kieran, pattern-recognition), run one more pass:

> "You are a hostile production environment. Find the three most likely ways this code will fail in production. Consider: race conditions, resource exhaustion, edge cases in real data, deployment assumptions, dependency failures."

Collaborative and adversarial review surface different issues.

## Systematic Debugging

When delegation fails repeatedly, don't just switch tools:
1. **Reproduce** — get the exact error, not a summary
2. **Isolate** — is it the tool, the prompt, the code, or the environment?
3. **Hypothesize** — one theory at a time, test it
4. **Fix** — minimal change that addresses root cause
5. **Verify** — confirm fix AND no regressions

| Failure pattern | Likely cause | Action |
|----------------|-------------|--------|
| Same error across 2+ tools | Prompt or spec issue | Fix the spec, not the tool |
| Tool-specific error | Tool constraint (sandbox, DNS, auth) | Switch tool laterally |
| Works locally, fails in delegate | Environment difference | Add env setup to prompt |
| Passes but wrong output | Spec ambiguity | Add explicit constraints/examples to prompt |
| 3+ failed attempts | Architecture problem | Stop delegating, diagnose in-session |

## Troubleshooting Quick Reference

- OpenCode silent fail → prompt >4K chars
- Codex hangs → bundle files into `/tmp/` first
- Codex write blocked → launched from wrong CWD; always `cd ~/code/<repo> && codex exec ...`
- Gemini no file changes → missing `--yolo`
- Double-backgrounded → never use `&` with `run_in_background: true`
- After Codex → always `git add && git commit` manually (sandbox blocks `.git`)
- Gemini promotes optional deps to main deps — always check pyproject.toml/Cargo.toml
- Gemini executes live mutations during testing — brief with test fixture or accept side effects

## Key Lessons (Empirical)

**Planning needs eyes — CLI wrappers don't work.** Tested (judex DP-001→003): `claude --print` planning scored 0/6 design issues (no tool access). In-session CE plan scored 2.5/6. Planning that can't see the codebase is a code linter at best. `opifex --plan` killed 2026-03-14.

**CE plan beats built-in plan.** CE runs `learnings-researcher` + `repo-research-analyst` in parallel — surfacing `~/docs/solutions/` gotchas and codebase patterns. Built-in plan misses institutional knowledge entirely.

**Challenge the premise before building.** Ask "what can this do that the existing approach can't?" before implementing features. Especially for CLI wrappers around agent-loop tasks.

## Launch Commands Reference

```bash
# opifex (auto-routes)
opifex exec /tmp/plan.txt -p ~/code/<project>
opifex exec /tmp/plan.txt -p ~/code/<project> -b codex --test-command "uv run pytest"

# Codex — MUST cd first
cd ~/code/<repo> && codex exec --skip-git-repo-check --full-auto "<prompt>"

# Gemini — MUST cd first
cd ~/code/<project> && gemini -m gemini-3.1-pro-preview -p "<prompt>" --yolo

# OpenCode
OPENCODE_HOME=~/.opencode-lean opencode run -m opencode/glm-5 --title "<title>" "<prompt>"

# plan-exec (zero Max20)
plan-exec /tmp/task-spec.txt -p ~/code/project
```
Use Bash tool's `run_in_background: true` — not shell `&`.

## Post-Delegate Checklist

After any delegate completes:
1. `head -12 pyproject.toml` — dep pollution
2. `git diff --stat` — scope creep
3. Run tests
4. Check for AGENTS.md updates needed

## File Ownership in Parallel Delegation

When decomposing tasks for parallel execution, explicitly list which files each delegate owns:

```
Task A owns: src/auth.py, src/models/user.py, tests/test_auth.py
Task B owns: src/api/routes.py, tests/test_routes.py
```

Add to each delegation prompt: "You own files X, Y, Z. Do NOT modify any other files."

Prevents scope creep and merge conflicts even within worktree isolation. Catches the case where two delegates independently decide to "helpfully" update a shared utility.

Source: [wshobson/agents](https://github.com/wshobson/agents), [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration)

## Reaction Routing (Auto-Retry on Failure)

When a delegate fails validation (Step 4), instead of waiting for human input on every failure:

1. Capture the last 30 lines of error output
2. Re-launch the **same delegate** on the **same worktree** with the error appended to the original prompt:
   ```
   [Original spec]

   --- PREVIOUS ATTEMPT FAILED ---
   Error output:
   [error lines]

   Fix the issue and verify with: [validation_cmd]
   ```
3. Allow **one** automatic retry per task. If retry also fails → escalate to human.

This eliminates the human relay step for common failures (missing import, typo, wrong flag). The human only sees failures that survived one self-correction attempt.

Source: [ComposioHQ/agent-orchestrator](https://github.com/ComposioHQ/agent-orchestrator) — YAML reaction rules route CI failures back to owning agent automatically.

## Wave-Based Dependency Execution

For complex projects where some tasks depend on others but not all are sequential:

```
Wave 1 (sequential): shared types, interfaces, config
  → commit
Wave 2 (parallel):   feature-a, feature-b, feature-c (all independent, all depend on Wave 1)
  → validate each, merge passing
Wave 3 (sequential): integration tests, API wiring (depends on Wave 2 outputs)
  → commit
```

Make waves explicit in the plan. Each wave has:
- **Dependencies:** which prior waves must complete
- **Parallelism:** which tasks within the wave are independent
- **Gate:** validation that must pass before next wave starts

This is a refinement of the Phase 1/Phase 2 pattern — makes dependency structure visible and auditable.

Source: [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration)
