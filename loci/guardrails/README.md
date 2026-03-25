# Agent Guardrails

Preventive controls for agent safety and security. Each guardrail addresses a specific footgun discovered through real usage.

## Shell Guardrails

Source these in `~/.zshrc` or install via `scripts/setup-symlinks.sh`.

| Guardrail | File | Purpose |
|-----------|------|---------|
| No Public Gists | `shell/no-public-gists.sh` | Blocks `gist -p` and `gh gist create -p` to prevent accidental public exposure |

## Adding New Guardrails

When you hit a footgun:

1. Create the guardrail script in appropriate folder (`shell/`, `claude/`, etc.)
2. Document the "why" in comments — what failed, when, what it prevents
3. Add to this README
4. Update `scripts/setup-symlinks.sh` if auto-install needed
5. Commit and push

## Install

```bash
# Source individual guardrails
source ~/agent-config/guardrails/shell/no-public-gists.sh

# Or add to ~/.zshrc for persistence
echo 'source ~/agent-config/guardrails/shell/no-public-gists.sh' >> ~/.zshrc
```
