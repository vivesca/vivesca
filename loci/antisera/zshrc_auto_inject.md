---
name: .zshrc auto-injection by package managers
description: Tools like pnpm auto-append PATH blocks to .zshrc — clean up on contact
---

Package managers (pnpm, bun, cargo) auto-inject PATH and env var blocks into `.zshrc` during install/update. This silently breaks non-interactive shells (SSH commands, cron, LaunchAgents).

**Detection:** After any `pnpm install -g`, `bun install`, or similar global tool install, check if `.zshrc` was modified. Move any new PATH/env exports to `.zshenv`.

**The comment guard** at the top of `.zshrc` ("NO PATH or env exports here") should catch human/LLM editors, but package manager scripts ignore it.
