# Machine Mirror Steps

Partial Claude Code environment mirror to a secondary Mac. Done once (M3, Feb 2026).

## Prerequisites

- Tailscale (both machines on same tailnet)
- Homebrew on target
- Cargo on target
- SSH access (`ssh <tailscale-hostname>`)

## Steps

### 1. Core tools (brew)

```bash
brew install uv node pnpm gh
brew link --overwrite pnpm  # if conflict with npm-installed pnpm
```

### 2. GitHub auth (interactive — needs device code)

```bash
gh auth login -h github.com -p https -w
# Enter code at github.com/login/device
```

### 3. Clone repos

```bash
cd ~
gh repo clone terry-li-hm/agent-config
gh repo clone terry-li-hm/skills
```

### 4. Symlinks

```bash
mv ~/bin ~/bin.bak 2>/dev/null || true
ln -sf ~/agent-config/bin ~/bin

mkdir -p ~/.claude/projects/-Users-terry/memory
mkdir -p ~/.claude/hooks

ln -sf ~/skills ~/.claude/skills
ln -sf ~/agent-config/claude/hooks ~/.claude/hooks
ln -sf ~/agent-config/claude/memory/MEMORY.md ~/.claude/projects/-Users-terry/memory/MEMORY.md
cp ~/agent-config/claude/settings.json ~/.claude/settings.json
```

### 5. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
# Auth on first interactive run: `claude`
```

### 6. Python/Rust CLIs

| Tool | Install method | Notes |
|------|---------------|-------|
| gog | `brew install gogcli` | Gmail/Calendar CLI |
| pplx | `cargo install compound-perplexity` then `ln -sf ~/.cargo/bin/compound-pplx ~/.cargo/bin/pplx` | Crate name ≠ binary name |
| oghma | `uv tool install oghma` | Conversation memory |
| qmd | bun global (custom script) | Skip — cerno wraps it. Or install bun + `bun install -g qmd` |

### 7. Post-setup (first direct session)

- `claude` auth (device code flow)
- API keys for gog, pplx, oghma — stored in Keychain on primary machine, not portable. Set up per-machine.

## Keeping in sync

LaunchAgent `com.terryli.cc-sync` on M3 pulls both repos every 4 hours + on login:
- `git -C ~/agent-config pull --ff-only`
- `git -C ~/skills pull --ff-only`

Log: `/tmp/cc-sync.log`. Uses `--ff-only` so local changes won't cause conflicts (just skips).

Plist: `~/Library/LaunchAgents/com.terryli.cc-sync.plist`

## What's NOT mirrored (by design)

- LaunchAgents / cron automation (iMac-as-server)
- Wechat2RSS, Lustro, ai-news pipeline (stateful services)
- MCP servers
- Full Keychain entries
- agent-browser profile
