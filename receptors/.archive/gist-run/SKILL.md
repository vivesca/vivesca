---
name: gist-run
description: Reference for packaging commands as runnable secret gists. Consult when Claude can't execute directly (sudo, sandbox, multi-step).
user_invocable: false
---

# Gist Run

When commands can't run inside Claude Code (sudo, sandbox restrictions, user needs to run on another machine), package them as a secret GitHub gist and provide a one-liner.

## Pattern

### 1. Create the gist

```bash
gh gist create --public=false -f "descriptive-name.sh" - <<'EOF'
#!/bin/bash
# What this does
your commands here
EOF
```

### 2. Give the user a one-liner

```bash
# Without sudo
gh gist view GIST_ID -r | bash

# With sudo
gh gist view GIST_ID -r | sudo bash
```

## When to Use

- Commands requiring `sudo` (system LaunchAgents, /etc changes)
- Multi-line scripts user needs to copy to mobile (Blink)
- Commands blocked by Claude Code sandbox (crontab writes, etc.)
- Anything longer than 2-3 lines that user needs to run manually

## Notes

- Always use `--public=false` (secret gist)
- Use a descriptive filename (`cleanup-adobe.sh` not `script.sh`)
- Heredoc with `'EOF'` (quoted) to prevent variable expansion
- Gist URL is shareable but unlisted — fine for personal use
