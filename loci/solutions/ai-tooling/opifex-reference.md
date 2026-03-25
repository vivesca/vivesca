# Opifex Reference

CLI at `~/code/opifex/`. Delegates coding tasks to free AI tools.

## Commands

```bash
opifex exec plan.md -p ~/code/project          # execute plan
opifex exec plan.md -p ~/code/project -b codex  # force backend
opifex exec plan.md -p ~/code/project --decompose  # parallel tasks
opifex route "task description"                 # dry-run routing
opifex log --stats                              # success rates
opifex status                                   # running executions
```

## Routing

| Signal | Tool | Why |
|--------|------|-----|
| Rust/cargo | Codex | Sandbox + DNS |
| Multi-file refactor | Codex | Repo navigation |
| Algorithm/logic | Gemini | Free, high benchmark |
| Boilerplate/scaffold | OpenCode | Free, unlimited |
| Default | Gemini | Best free default |

Fallback: Gemini → Codex → OpenCode.

## Gotchas

- **Codex can't write across worktree boundaries** — `cd` into repo first.
- **Gemini free tier quota shared** — 3+ simultaneous calls burn through it. Mix tools.
- **OpenCode prompt limit ~4K chars** — long plans need splitting.
- Log at `~/.local/share/opifex/log.jsonl`.
