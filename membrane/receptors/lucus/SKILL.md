---
name: lucus
description: "Git worktree manager for parallel AI agent sessions. Use when starting a new feature/fix that needs isolation from other Claude Code / Codex / Gemini sessions running on the same repo."
user_invocable: false
---

# lucus — Git Worktree Manager

Repo: `~/code/lucus` | crates.io: `lucus` | Phase 1 shipped 2026-03-02

## When to use

Whenever running **parallel AI agent sessions** on the same repo. Each session gets its own worktree — no staging conflicts, no dirty index surprises from `git add -A` in another session.

## Core commands

```bash
lucus new feat/auth          # create worktree + branch at ../{repo}.{branch}
lucus list                   # all worktrees: branch, path, ahead/behind, uncommitted
lucus switch feat/auth       # cd into worktree (requires shell wrapper — see Setup)
lucus remove feat/auth       # tear down worktree + delete branch
lucus remove feat/auth --force  # force-remove even with uncommitted/untracked files
lucus query feat/auth        # print path only (used internally by shell wrapper)
```

## Setup (one-time)

```bash
lucus init zsh               # writes shell function to ~/.zshrc
source ~/.zshrc              # activate in current shell
```

The shell wrapper is needed for `lucus switch` to actually `cd` — a binary can't change the parent shell's directory on its own.

## Config

`~/.config/lucus/config.toml` — created on first use with defaults:

```toml
[worktree]
path_template = "../{repo}.{branch}"   # worktrees land as siblings of the repo
default_branch = "main"

[hooks]
post_create = []       # blocking hooks run after worktree creation
post_create_bg = []    # background hooks (fire and forget)
pre_remove = []
post_remove = []

[files]
# Glob patterns relative to repo root to copy into each new worktree.
# Default (empty): auto-discovers and copies all .env* files in repo root.
copy = [".env", ".env.local", ".env.test"]
```

### .env file copying

`lucus new` automatically copies all `.env*` files from the repo root into the new worktree. Delegates (Codex, Gemini, OpenCode) running in the worktree get the right secrets without manual setup.

- Missing `.env*` files are silently skipped — not an error
- Override which files are copied via `[files] copy` in config
- Non-recursive: only repo root, not subdirectories

### .gitignore management

If the worktree path template places worktrees **inside** the repo (e.g. `.worktrees/{branch}`), `lucus new` automatically adds the parent dir to the repo's `.gitignore` — preventing worktree contents from appearing as untracked files. Write is idempotent (only adds if not already present).

Default template (`../repo.branch`) puts worktrees **outside** the repo — no `.gitignore` changes are made in that case.

## Output

- TTY: coloured human table
- Non-TTY / `--json`: NDJSON (one object per line, `jq`-friendly)

## Symbolic shortcuts (Phase 2+)

```bash
lucus switch -   # previous worktree
lucus switch ^   # default branch
lucus switch @   # current worktree
```

## Gotchas

- **`lucus merge` does not exist yet** (Phase 3). To merge a worktree branch back: `git merge <branch> --no-ff` from the main repo, then `git worktree remove --force <path>`. Don't call `lucus merge` — it errors.
- `lucus remove` fails with uncommitted/untracked files — `--force` flag is **not yet implemented**. Use `git worktree remove --force <path>` directly as workaround.
- `lucus switch` requires the shell wrapper (`lucus init zsh`) to actually `cd`
- Worktrees land at `../{repo}.{branch}` by default — sibling directories of the source repo
- `.gitignore` management only triggers for in-repo path templates — default template is outside the repo, no changes made
- `git2::Worktree` has no `.open()` — use `Repository::open(wt.path())` (fixed in Phase 1)
- Codex sandbox blocks crates.io DNS — always `cargo build` outside the sandbox
- OpenCode sandbox blocks writes outside its worktree — can't update `~/skills/` from an OpenCode delegate

## Roadmap

- **Phase 2 (v0.3.0):** `lucus new "natural language prompt"` → Haiku generates branch name, persists task to `.lucus/tasks/`. Progressive list rendering (rayon + indicatif). Per-project `.lucus.toml`. `lucus remove --force` flag.
- **Phase 3 (v0.4.0):** `lucus merge`, `lucus status`, `lucus clean`, tmux integration, shell completions.
