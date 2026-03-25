# AI Tool Git Identity via Alias Env Vars

## Problem

Multiple AI coding tools (Codex, OpenCode, Claude Code) share the same machine and inherit the global `~/.gitconfig` identity. All commits look like they came from the same author.

## Solution

Inject `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL` at the alias level in `.zshrc`. These env vars override `~/.gitconfig` for all child processes, so any `git commit` the tool runs gets the correct identity — no need for `--author` flags or tool-specific config.

```zsh
# Global: Terry Li (for Claude Code, manual commits)
git config --global user.name "Terry Li"
git config --global user.email "terry@terryli.dev"

# Per-tool override via alias env vars
alias codex="GIT_AUTHOR_NAME='Codex' GIT_AUTHOR_EMAIL='codex@openai.com' \
  GIT_COMMITTER_NAME='Codex' GIT_COMMITTER_EMAIL='codex@openai.com' \
  codex --dangerously-bypass-approvals-and-sandbox"

alias o="GIT_AUTHOR_NAME='OpenCode' GIT_AUTHOR_EMAIL='opencode@local' \
  GIT_COMMITTER_NAME='OpenCode' GIT_COMMITTER_EMAIL='opencode@local' \
  opencode"
```

## Why This Works

- `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars take priority over `.gitconfig`
- Set at alias level = propagates to all child processes within that session
- No changes needed in the AI tool's config (neither Codex nor OpenCode have native git identity settings)
- Claude Code uses the global config (Terry Li) since it's orchestrated by the user

## Gotchas

- Only applies to shells that source `.zshrc` (interactive). Scripts launched by cron/launchd won't have the aliases.
- New tmux tabs need `source ~/.zshrc` or a fresh shell to pick up changes.
- If a tool is invoked by its full path (`/opt/homebrew/bin/opencode`) instead of the alias, it bypasses the override.

## Discovered

2026-02-22. All photoferry commits (17) showed as "OpenCode" because global git config was set to OpenCode and Codex inherited it.
