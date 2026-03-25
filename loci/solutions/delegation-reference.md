# Delegation Reference

Operational reference for delegation troubleshooting and model gotchas.
**Routing decisions → `rector` Step 3.** This doc is for when things go wrong.

## Key Gotchas (top of mind)

- **OpenCode model:** Always `opencode/glm-5` — matches `$OPENCODE_MODEL` env var. `zhipuai-coding-plan/glm-5` key was revoked (Mar 6); new key works with `opencode` provider only.
- **Gemini free tier quota:** Shared across parallel calls. Launching 3+ Gemini delegates simultaneously burns through it in one burst. Mix tools to avoid: Gemini (algorithmic) + Codex (multi-file) + OpenCode (boilerplate).
- **OpenCode lean config:** `OPENCODE_HOME=~/.opencode-lean` — skips MCPs, cuts startup from 60s → 15s
- **OpenCode prompt hard limit:** ~4K chars. Over limit → exits 0, writes nothing (silent fail)
- **Codex headless:** `codex exec --skip-git-repo-check --full-auto "prompt"` — bare `codex` needs TTY
- **Codex write access:** Even with `--sandbox danger-full-access`, Codex scopes writes to its CWD. Always `cd ~/code/<repo> && codex exec ...` — launching from a different dir (e.g. `~/skills/`) blocks writes to the target repo.
- **Codex + lucus worktrees:** Codex's `apply_patch` rejects writes to paths outside CWD. If CWD is `docima.db-backends` (worktree), it can't write to `docima` (main). This is expected — worktree isolation works. But if the prompt references the main repo path, Codex tries to write there and fails. Fix: ensure all paths in the prompt match the worktree CWD, or use Claude subagents instead (they respect the worktree path).
- **Never use `&` with `run_in_background: true`** — double-backgrounds, output pipe breaks silently
- **Commit plan before `lucus new`** — worktrees only see committed history

## Stolen Patterns (Specula 2026-03)

- **Dual-model pipeline** (Cursor): Heavy architect model plans → light editor applies changes. We already do this (Opus plans, Sonnet/Codex/Gemini executes). Make it explicit: ALWAYS use different models for planning vs execution.
- **CodeAct style** (Manus/OpenHands): When delegating complex multi-file operations, prompt delegates to "write a Python script that does X" instead of step-by-step tool calls. Code as action format enables conditionals, loops, debugging.
- **Edit format matters** (Aider): Unified diff 3x better than SEARCH/REPLACE. Instruct delegates to use diff format. "Present edits as data for a program, not instructions for a human."
- **Retrieval-first subagent** (Windsurf/SWE-grep): >60% of first delegate turn is gathering context. For large repos, run a retrieval-only Explore agent first (cheap, Haiku) and pass structured findings to the execution delegate.
- **JSON state files** (Anthropic three-agent harness): For multi-session rector tasks, use JSON (not Markdown) for state tracking between sessions. Models are less likely to corrupt JSON than Markdown.
- **Flexible patching** (Aider): LLM output is always imperfect. Design for it — never assume clean diff output. The patching/verification layer is the reliability layer, not the model.

## Monitoring Progress

**OpenCode:**
```bash
ls -lt ~/.local/share/opencode/storage/session/   # find latest session
# then read session JSON for output
```

**Codex:**
```bash
codex resume --last
# or check the output file specified in your prompt
```

**Gemini:** Output prints to stdout — check the background task output file.

## Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Exits 0, no files changed | OpenCode prompt >5K chars | Shorten prompt, remove inline content |
| Timeout after 5min | Task too small or too vague | Give more specific instructions or do it directly |
| Hangs indefinitely | GLM-5 connection stall | Kill and write directly; use `run_in_background` |
| Codex hangs >5min, no output | Sandbox can't read files outside workdir | Bundle reference files into `/tmp/` first |
| Gemini "quota exceeded" | Hit 1500 RPD or 120 RPM | Wait or switch to OpenCode/Codex |
| Gemini 429 `MODEL_CAPACITY_EXHAUSTED` | Flash preview limited capacity | Auto-retries. If persistent: `gemini -p "..." --yolo -m gemini-3-pro` |
| Gemini no file changes | Sandbox blocked writes | Ensure `--yolo` flag is set |
| Empty output with `&` | Double-backgrounded | Use Bash tool's `run_in_background: true` only |
| Wrong files modified | Ambiguous paths | Use absolute paths, specify exact method/line |
| Gemini promotes optional deps to main | Sees `import X`, decides project needs X | Always `git diff pyproject.toml` / `Cargo.toml` after Gemini delegates. Revert unwanted dep changes before next delegate. |
| Codex "stdin is not a terminal" | Bare `codex` instead of `codex exec` | Use `codex exec --skip-git-repo-check --full-auto` |
| OpenCode rejects file reads | Sandboxes to project root | Bundle files: `cat file1 file2 > /tmp/bundle.md` first |
| OpenCode doesn't overwrite output | Writes to new session | Delete target output files before launching, or use unique names |

If OpenCode fails twice: escalate to Gemini (`gemini -p "..." --yolo`) or Codex.

## Model Notes

### Gemini 3.1 Pro
- Auto-routed by Gemini CLI (complex → 3.1 Pro, simple → 3 Flash)
- 120 RPM, 1500 RPD. One prompt = multiple API requests internally — budget ~250-500 actual prompts/day
- Strengths: AA Intelligence Index #1, LiveCodeBench Elo 2887, GPQA Diamond 94.3%
- Weaknesses: High TTFT (~31s), very verbose, trails Claude on real-world agentic tasks (GDPval-AA: Gemini 1317 vs Opus 1606)
- Force model: `gemini -p "..." --yolo -m gemini-3.1-pro-preview`

### GLM-5 (OpenCode)
- Model string: `zhipuai-coding-plan/glm-5`
- GLM-4.7 available as fallback if GLM-5 regresses

### Codex (GPT-5.3 Codex)
- Terminal-Bench #1 developer
- 128K+ context — give it full specs, large diffs, no prompt length concern
- Sandbox blocks `.git` writes — cannot commit. Run `git add && git commit` manually after

### Prompt Budget
```bash
echo -n "your prompt" | wc -c   # count before sending
```
- OpenCode: ~4K chars hard limit
- Codex: no practical limit
- Gemini: generous (1M context)

## Post-Codex Quick Review

Codex writes structurally correct code but misses cross-cutting concerns. Before smoke test, scan `git diff` for:
- Shared state ownership (flag set by one method, reset by another)
- Missing timing on parallel result loops (hardcoded `0` elapsed)
- `.unwrap()` on non-static results
- Missing output paths (JSON `Report` struct often forgotten when adding fields)

## PII Masking

Prompts with personal info → mask via `~/skills/.archive/pii-mask/mask.py` before sending.
```bash
uv run mask.py --dry-run "text"   # preview
```
Skip for: Claude Code prompts (same trust boundary), code-only prompts, PII essential to the task.

## Compound Engineering on Delegated Tools

- **Codex + CE:** Works. Include "Follow compound-engineering review patterns" in prompt. Codex reads CLAUDE.md for tool mapping.
- **OpenCode + CE:** Constrained by 4K prompt limit + project-root sandbox. Best for single-file CE tasks.
- After skill changes: `/agent-sync` to propagate to `~/.codex/skills/` and `~/.opencode-lean/skills/`.

## Claude headless invocation (nested from Claude Code)

```bash
# CORRECT — no --output-dir (flag doesn't exist)
env CLAUDECODE= claude --dangerously-skip-permissions -p "$(cat /tmp/prompt.txt)"

# WRONG — fails with "unknown option '--output-dir'"
env CLAUDECODE= claude --dangerously-skip-permissions -p "..." --output-dir /some/path
```

The working dir for the agent defaults to wherever you launch from. To scope an agent to a worktree, cd into it in the prompt instructions — don't use flags.

## Friction: Background Codex delegation makes tmux tab go idle
**Date:** 2026-03-10
**Context:** Delegating moneo Rust rewrite to Codex with run_in_background: true
**What went wrong:** Terminal goes quiet, tmux marks tab as idle — no visible signal that work is in progress
**Resolution:** Run Codex synchronously (foreground) by omitting run_in_background — session blocks but tmux stays active
**Prevention:** Default to foreground Codex delegation. Only use background when genuinely need to do other work in parallel in the same session.

## Codex Background Dispatch (ERR-20260312-001)

**Codex from Claude Code background tasks:**
- `codex exec --full-auto` works (legatus uses this)
- `codex -m o3 "prompt"` fails with "stdin is not a terminal" — interactive mode needs TTY
- `-a never` flag conflicts with `--dangerously-bypass-approvals-and-sandbox` in config — don't combine
- Sandbox `workspace-write` can't write outside workdir — use `danger-full-access` for tasks that `cp` to `~/bin/`
- Working invocation: `codex exec --skip-git-repo-check --sandbox danger-full-access --full-auto "prompt"`

## ERR-20260312-002: Scheduled legatus runs produce empty output (since Mar 11)

**Root cause (layer 1):** LaunchAgent plists didn't source `.zshenv`. Fixed: `~/bin/legatus-env` wrapper (sources `.zshenv` then exec's legatus). All plists updated.

**Root cause (layer 2 — the real bug):** `.zshenv` line 23 had `${TMPDIR:-/tmp}op-env-cache.sh`. When `TMPDIR` is unset (launchd context), this evaluates to `/tmpop-env-cache.sh` (missing slash between `/tmp` and filename). The op-env-cache silently fails to load → no API keys exported → backends exit with 0 output. Fixed: changed fallback to `${TMPDIR:-/tmp/}` with trailing slash.

**Evidence:** `env -i` simulation with both fixes confirmed `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` all SET.

**Note:** Scheduled runs have NEVER produced real output since switching to individual LaunchAgents. Both fixes were needed.

## LRN-20260313-001: TMPDIR fallback needs trailing slash

**Pattern:** `${TMPDIR:-/tmp}filename` → `/tmpfilename` when TMPDIR unset (launchd, cron, clean env). Fix: `${TMPDIR:-/tmp/}filename`. TMPDIR in interactive shells always ends with `/` so the bug is invisible until you hit a non-interactive context. Check any `.zshenv`/`.zshrc` that concatenates paths with TMPDIR fallback.
