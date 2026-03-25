# M3 MacBook Bootstrap — Warm DR Standby
> Gap week: Apr 3–6 | Goal: machine ready to take over if primary fails
> Total estimated time: ~6–8 hours spread across 4 days

---

## Pre-Flight (Before You Begin)

On the **current machine**, run this to refresh the DR snapshot:

```bash
dr-sync         # commits settings, memory, Brewfile to officina/claude-backup
cd ~/officina && git push
```

Verify `~/officina/claude-backup/` contains recent dates for:
- `settings.json`, `settings.local.json`
- `memory/MEMORY.md`
- `zshenv.local` (will be copied, contains secrets via 1Password injection)

---

## DAY 1 — Critical (2–3 hours)
*Shell, secrets, git, Claude Code. Everything else depends on these.*

---

### 1. Xcode CLI Tools (~5 min)
Required before Homebrew and anything that compiles.

```bash
xcode-select --install
```

### 2. Homebrew (~5 min install + deps run in background)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# After install, add to path for this session:
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 3. 1Password + CLI (~10 min)
Secrets flow from 1Password. Install this before anything that needs API keys.

1. Install 1Password from the Mac App Store or [1password.com/downloads](https://1password.com/downloads/)
2. Install the CLI:
   ```bash
   brew install --cask 1password-cli
   ```
3. Sign in and confirm vault access:
   ```bash
   op signin
   op vault list   # confirm "Agents" vault visible
   ```

### 4. Clone officina — the single source of truth (~3 min)

```bash
gh auth login   # or: git clone with HTTPS + PAT if gh not yet installed
git clone https://github.com/terry-li-hm/officina.git ~/officina
git clone https://github.com/terry-li-hm/skills.git ~/skills
git clone https://github.com/terry-li-hm/scripts.git ~/scripts
git clone https://github.com/terry-li-hm/notes.git ~/epigenome/chromatin
```

If `gh` is not yet available, install it first: `brew install gh && gh auth login`

### 5. Shell configuration (~5 min)

```bash
# .zshenv (env vars, Homebrew path, 1Password injection)
cp ~/officina/claude/zshenv.tpl ~/zshenv.tpl    # reference only
# The real .zshenv is in the home dir; copy from current machine via:
scp primary:.zshenv ~/.zshenv

# .zshrc — copy from current machine:
scp primary:.zshrc ~/.zshrc

# Reload:
exec zsh
```

**Alternative if SSH to primary is not available:** The `.zshenv` content is in `~/officina/claude/zshenv.tpl` (1Password references). Manually create `~/.zshenv` mirroring the structure from the primary's `~/.zshenv`:
- Homebrew PATH block (lines 2–8 of primary `.zshenv`)
- `OPENCODE_MODEL`, `GOG_ACCOUNT`, `AGENT_BROWSER_PROFILE` env vars
- 1Password injection block (lines 22–26)
- `TELEGRAM_API_ID=2040` and `TELEGRAM_API_HASH` (public values, safe to hardcode)
- Then: `[ -f ~/.zshenv.local ] && source ~/.zshenv.local`

Create `~/.zshenv.local` with any machine-local overrides (can be empty stub initially — 1Password injection handles API keys via `~/.zshenv`).

### 6. SSH keys (~5 min)

**Option A — copy from primary (preferred):**
```bash
scp primary:~/.ssh/id_ed25519 ~/.ssh/
scp primary:~/.ssh/id_ed25519.pub ~/.ssh/
scp primary:~/.ssh/sky-key ~/.ssh/
scp primary:~/.ssh/sky-key.pub ~/.ssh/
scp primary:~/.ssh/config ~/.ssh/
chmod 600 ~/.ssh/id_ed25519 ~/.ssh/sky-key
mkdir -p ~/.ssh/sockets
```

**Option B — generate fresh key and add to GitHub/servers:**
```bash
ssh-keygen -t ed25519 -C "terry@m3"
gh auth login    # then: gh ssh-key add ~/.ssh/id_ed25519.pub
```

### 7. Git global config (~2 min)

```bash
git config --global user.name "Terry Li"
git config --global user.email "terry@terryli.dev"
git config --global core.pager delta
git config --global interactive.diffFilter "delta --color-only"
git config --global delta.navigate true
git config --global delta.side-by-side true
git config --global delta.line-numbers true
git config --global merge.conflictstyle diff3
git config --global credential.helper osxkeychain
git config --global credential.https://github.com.helper "!/opt/homebrew/bin/gh auth git-credential"
git config --global credential.https://gist.github.com.helper "!/opt/homebrew/bin/gh auth git-credential"
```

Or copy the whole `.gitconfig`:
```bash
scp primary:~/.gitconfig ~/.gitconfig
```

### 8. Core Homebrew packages (~20 min, mostly waiting)

Install the full Brewfile (includes all CLI tools, apps, VS Code extensions):

```bash
brew bundle --file=~/officina/Brewfile
```

Key packages this installs: `mise`, `tmux`, `starship`, `atuin`, `gh`, `git-delta`, `fzf`, `fd`, `bat`, `eza`, `zoxide`, `uv`, `pipx`, `rustup`, `go`, `node`, `bun`, `mosh`, `rclone`, `ollama`, `wacli`, `ghostty`, `1password`, `1password-cli`, `obsidian`, `tailscale`, and all app store apps.

**Note on MAS apps:** `brew bundle` will attempt Mac App Store installs but requires being signed in. If it fails on MAS entries, run `mas signin` first.

### 9. Claude Code (~5 min)

```bash
npm install -g @anthropic-ai/claude-code
```

Verify: `claude --version`

### 10. Wire up officina symlinks (~5 min)

```bash
# Setup all symlinks (.claude/, ~/bin → officina/bin, etc.)
bash ~/officina/scripts/setup-symlinks.sh

# Verify critical links:
ls -la ~/.claude/hooks   # should → officina/claude/hooks
ls -la ~/.claude/skills  # should → ~/skills (or run: ln -sf ~/skills ~/.claude/skills)
ls -la ~/CLAUDE.md       # should → officina/claude/CLAUDE.md
ls -la ~/bin             # should → officina/bin
```

**Note:** `setup-symlinks.sh` references `~/agent-config` as `CONFIG_DIR`. On this machine, that is `~/officina`. The script may need adjustment, or run manually:

```bash
mkdir -p ~/.claude
ln -sf ~/officina/claude/hooks ~/.claude/hooks
ln -sf ~/officina/claude/settings.json ~/.claude/settings.json
ln -sf ~/skills ~/.claude/skills
ln -sf ~/officina/claude/CLAUDE.md ~/CLAUDE.md
ln -sf ~/officina/bin ~/bin
ln -sf ~/officina/claude/agents ~/.claude/agents
ln -sf ~/officina/claude/rules ~/.claude/rules
ln -sf ~/officina/claude/memory ~/.claude/agent-memory
```

### 11. Restore DR backup: settings and memory (~5 min)

```bash
# Settings (already symlinked above via officina)
# Memory files
mkdir -p ~/.claude/projects/-Users-terry/memory
cp ~/officina/claude-backup/memory/* ~/.claude/projects/-Users-terry/memory/
cp ~/officina/claude-backup/settings.local.json ~/.claude/settings.local.json
```

### 12. Verify Claude Code launches (~2 min)

```bash
cd ~
claude
# Check: hooks load, CLAUDE.md visible, skills listed
# Type: /skills  — should list analyze, copia, legatum, etc.
```

**Day 1 complete.** Claude Code is functional with full config and memory.

---

## DAY 2 — Important (2–3 hours)
*Language runtimes, Python/Rust tools, LaunchAgents.*

---

### 13. mise — Python runtime (~5 min)

```bash
# mise is installed via Brewfile
mise install python@3.13
mise use --global python@3.13

# Verify:
python --version   # should be 3.13.x
```

### 14. uv (~2 min, may already be installed)

```bash
# Check: uv --version
# If missing:
brew install uv
# or: curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 15. Rust toolchain (~10 min)

```bash
# rustup is installed via Brewfile
rustup toolchain install stable
rustup default stable

# Verify:
cargo --version
```

### 16. bun (~3 min)

```bash
curl -fsSL https://bun.sh/install | bash
# Reload shell or: export BUN_INSTALL="$HOME/.bun" && export PATH="$BUN_INSTALL/bin:$PATH"
bun --version
```

### 17. Node/npm global tools (~5 min)

```bash
# ccusage — Claude usage monitoring
npm install -g ccusage

# agent-browser
npm install -g agent-browser

# Gemini CLI
npm install -g @google/gemini-cli

# mgrep (semantic search)
npm install -g @mixedbread/mgrep

# qmd (vault query)
bun install -g github:tobi/qmd
```

### 18. uv tool installs — Python CLI suite (~15 min)

These are all the Python tools currently installed on primary:

```bash
uv tool install claude-monitor
uv tool install ruff
uv tool install osxphotos
uv tool install weasyprint
uv tool install yt-dlp

# From local source (clone these repos first):
git clone https://github.com/terry-li-hm/oghma.git ~/code/oghma
git clone https://github.com/terry-li-hm/lustro.git ~/code/lustro

uv tool install ~/code/oghma     # installs: oghma, oghma-mcp
uv tool install ~/code/lustro    # installs: lustro

# Additional tools from code repos (clone as needed):
# ~/code/elencho, ~/code/sopor, ~/code/thalamus, ~/code/qianli,
# ~/code/opifex, ~/code/wu, ~/code/consilium-py, ~/code/crm, etc.
# For each: uv tool install ~/code/<name>
```

Full list of active uv tools from primary:
```
claude-monitor, lustro, oghma, sopor, thalamus, opifex, wu, qianli,
elencho, consilium (py), crm, ruff, osxphotos, weasyprint, yt-dlp,
ai-landscape-review, frontier-council, llm-council, nano-pdf
```

### 19. Rust tools — build from source (~20–30 min)

Key Rust binaries currently in `~/.cargo/bin/` on primary:

```bash
# Clone and build (batch, let run in background):
git clone https://github.com/terry-li-hm/anam.git ~/code/anam && cd ~/code/anam && cargo install --path .
git clone https://github.com/terry-li-hm/synaxis.git ~/code/synaxis && cd ~/code/synaxis && cargo install --path .
git clone https://github.com/terry-li-hm/theoros.git ~/code/theoros && cd ~/code/theoros && cargo install --path .
git clone https://github.com/terry-li-hm/melete.git ~/code/melete && cd ~/code/melete && cargo install --path .
git clone https://github.com/terry-li-hm/noesis.git ~/code/noesis && cd ~/code/noesis && cargo install --path .
git clone https://github.com/terry-li-hm/fasti.git ~/code/fasti && cd ~/code/fasti && cargo install --path .
git clone https://github.com/terry-li-hm/usus.git ~/code/usus && cd ~/code/usus && cargo install --path .
git clone https://github.com/terry-li-hm/nexis.git ~/code/nexis && cd ~/code/nexis && cargo install --path .
git clone https://github.com/terry-li-hm/auceps.git ~/code/auceps && cd ~/code/auceps && cargo install --path .
git clone https://github.com/terry-li-hm/peira.git ~/code/peira && cd ~/code/peira && cargo install --path .
git clone https://github.com/terry-li-hm/deleo ~/code/deleo && cd ~/code/deleo && cargo install --path .
```

From Brewfile: `cargo install adytum`

### 20. Go tools (~5 min)

```bash
go install github.com/simonw/rodney@latest      # from Brewfile
go install github.com/steipete/gogcli/cmd/gog@latest
```

### 21. LaunchAgents (~15 min)

LaunchAgents in `~/Library/LaunchAgents/` fall into three types:

**Type A — symlinks to officina (auto-wired):**
These already exist in `~/officina/launchd/`. After cloning officina, link and load:

```bash
# Link all officina launchd plists
for plist in ~/officina/launchd/com.terry.*.plist ~/officina/launchd/md.obsidian.*.plist; do
  name=$(basename "$plist")
  ln -sf "$plist" ~/Library/LaunchAgents/"$name"
  launchctl load ~/Library/LaunchAgents/"$name"
done
```

Covers: `blog-sync`, `csb-ai-jobs`, `due-backup`, `exocytosis`, `lustro-*`, `nyx-monthly`, `oghma-*`, `oura-sync`, `pharos-sync`, `pondus-monitor`, `qmd-reindex`, `rotate-logs`, `speculor`, `update-coding-tools`, `usus-watch`, `vault-git-backup`, `wacli-sync`, `wewe-rss-health`, `obsidian-sync-headless`

**Type B — copies (manual install required):**
These are standalone plists not in officina. Copy from primary:

```bash
scp primary:~/Library/LaunchAgents/com.terry.nightly.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.circadian-probe.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.due-snapshot.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.forge-spark.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.launchagent-health.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.location-receiver.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.praeco.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.phagocytosis.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.wacli-catchup.plist ~/Library/LaunchAgents/
scp primary:~/Library/LaunchAgents/com.terry.x-feed-lustro.plist ~/Library/LaunchAgents/
# Legatus family:
for agent in legatus-ai-intel legatus-docima-benchmark legatus-git-health legatus-memory-hygiene legatus-morning-dashboard legatus-notes-orphan-scan legatus-solutions-dedup legatus-todo-stale-sweep legatus-vault-health-check; do
  scp primary:~/Library/LaunchAgents/com.terry.$agent.plist ~/Library/LaunchAgents/
done
# ai-landscape family:
for freq in monthly quarterly weekly yearly; do
  scp primary:~/Library/LaunchAgents/com.terry.ai-landscape-$freq.plist ~/Library/LaunchAgents/
done
# Then load them all:
for plist in ~/Library/LaunchAgents/com.terry.*.plist; do
  launchctl load "$plist" 2>/dev/null
done
```

**Type C — phron bots (separate code repo):**
```bash
# These symlink to ~/code/phron/launchd/ — clone and they wire themselves:
git clone https://github.com/terry-li-hm/phron.git ~/code/phron
ln -sf ~/code/phron/launchd/com.phron.bot.plist ~/Library/LaunchAgents/
ln -sf ~/code/phron/launchd/com.phron.nudge.plist ~/Library/LaunchAgents/
ln -sf ~/code/phron/launchd/com.phron.overnight.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.phron.*.plist
```

**Skip on DR standby:** `com.oghma.daemon.plist` — this likely self-installs when oghma runs. Defer until Step 18 is complete.

### 22. Obsidian vault (~5 min)

The vault at `~/epigenome/chromatin` is a git repo with `.obsidian/` config checked in, so plugins, settings, and themes transfer automatically.

1. Open Obsidian → Add vault → `~/epigenome/chromatin`
2. Plugins will show as installed (they live in `~/epigenome/chromatin/.obsidian/plugins/`)
3. Enable community plugins if Obsidian asks (safe mode prompt)
4. For `obsidian-git` plugin: confirm it can push/pull (uses `~/.ssh` keys from Step 6)

**Active plugins:** context-crafter, copilot, copy-document-as-html, dataview, distill, easy-bake, homepage, hot-reload, obsidian-git, obsidian-linter, omnisearch, packup4ai, smart-context, url-into-selection, spaced-repetition, quiet-outline, smart-typography

---

## DAY 3 — Secondary Tools (1–2 hours)
*Everything that makes the workflow smooth but isn't Day 1 blocking.*

---

### 23. Shell quality-of-life

```bash
# atuin — shell history sync (installed via Brewfile)
atuin login      # syncs shell history from primary
atuin sync

# zoxide — smart cd (installed via Brewfile, activated in .zshrc)
# No extra setup needed.

# fzf keybindings (if not already in .zshrc)
$(brew --prefix)/opt/fzf/install --key-bindings --completion --no-update-rc
```

### 24. Claude Code settings.local.json

This file holds personal permissions not tracked in the main settings. Copy from DR backup:

```bash
cp ~/officina/claude-backup/settings.local.json ~/.claude/settings.local.json
```

Contents: `outputStyle` preference and local `permissions` (allow: `Bash(cd:*)`, `Bash(ls:*)`, `Bash(consilium:*)`).

### 25. Shared LLM model registry

```bash
# Copy the shared model config used by fodina-mine, redarguo, etc.
cp primary:~/.config/llm-models.json ~/.config/llm-models.json
# Or it may be in officina already — check:
ls ~/officina/.config/ 2>/dev/null
```

### 26. Synaxis config

```bash
mkdir -p ~/.config/synaxis
cp ~/officina/claude-backup/config/synaxis/config.toml ~/.config/synaxis/config.toml
# Or copy from primary:
scp primary:~/.config/synaxis/config.toml ~/.config/synaxis/
```

### 27. OpenCode

```bash
# opencode is a tap from anomalyco/tap (in Brewfile)
# Config directory:
mkdir -p ~/.config/opencode
ln -sf ~/officina/opencode/opencode.json ~/.config/opencode/opencode.json

# Set OPENCODE_MODEL env var (already in .zshenv):
# export OPENCODE_MODEL="opencode/glm-5"
```

### 28. Starship prompt

```bash
# starship is installed via Brewfile
# Config is already at ~/.config/starship.toml (part of .config/ — copy from primary):
scp primary:~/.config/starship.toml ~/.config/starship.toml
# or it may be a tracked file; check if already cloned via dotfiles/officina
```

### 29. tmux config

```bash
scp primary:~/.tmux.conf ~/.tmux.conf 2>/dev/null || true
# Ghostty terminal app installed via Brewfile — its config:
scp primary:~/.config/ghostty/config ~/.config/ghostty/config 2>/dev/null || true
```

### 30. Keychain secrets migration

These secrets live in the macOS Keychain on primary and are **not** synced via iCloud Keychain for security reasons. They must be manually exported and imported, or re-entered.

Keys managed by `keychain-env` (read in `.zshrc`):

```bash
# On primary — list what's in keychain:
keychain-env --list 2>/dev/null || security find-generic-password -a terry -l claude 2>/dev/null

# On new machine — add each secret:
security add-generic-password -a terry -s <service-name> -w <value>
```

The primary API keys (Anthropic, OpenAI, Google, etc.) are handled by **1Password injection** via `~/.zshenv` → `op inject`. These will work automatically once 1Password CLI is set up (Step 3). The keychain covers legacy keys not yet migrated to 1Password.

### 31. oghma daemon

```bash
# After oghma is installed (Step 18):
oghma daemon install    # or check how the LaunchAgent registers itself
# The plist com.oghma.daemon.plist should appear in ~/Library/LaunchAgents/
```

---

## DAY 4 — Nice to Have (~1 hour)
*Skip entirely if time-constrained; machine is already a functional standby.*

---

### 32. App Store and remaining casks

`brew bundle` handles most of this. Verify the following are installed and logged in:
- **Things 3** (tasks) — verify sync via iCloud
- **Due** (timers) — backup plist loaded in Step 21; verify DB synced
- **Drafts** (inbox) — iCloud sync
- **Jump Desktop** (remote access) — sign in to account
- **WhatsApp** — sign in via QR
- **Telegram Desktop** — sign in (uses `TELEGRAM_API_ID=2040` + `TELEGRAM_API_HASH` from `.zshenv`)

### 33. OrbStack

```bash
# Installed via Brewfile cask
# Open OrbStack → it provisions the Linux VM automatically
# SSH config for orb is auto-added to ~/.orbstack/ssh/config (included in ~/.ssh/config)
```

### 34. wacli (WhatsApp CLI)

```bash
# wacli is installed via steipete tap in Brewfile
# Authenticate:
wacli login
# The LaunchAgents wacli-sync and wacli-catchup (loaded in Step 21) handle automation
```

### 35. Tailscale

```bash
# Installed via Brewfile
# Open System Settings → Tailscale → sign in with same account
# Verify machine appears in Tailscale admin (https://login.tailscale.com/admin/machines)
# pharos should be accessible at its Tailscale IP after login
```

### 36. Micro editor config

```bash
scp primary:~/.config/micro/settings.json ~/.config/micro/settings.json 2>/dev/null || true
```

### 37. Remaining code repos (background, not urgent)

Only clone what you actively need. The full list is `~/code/` (70+ repos). Priority for standby:

```bash
# Already done: oghma, lustro, anam, synaxis, theoros, fasti, phron
# Next tier (if time):
git clone https://github.com/terry-li-hm/elencho.git ~/code/elencho
git clone https://github.com/terry-li-hm/sopor.git ~/code/sopor
git clone https://github.com/terry-li-hm/thalamus.git ~/code/thalamus
git clone https://github.com/terry-li-hm/amicus.git ~/code/amicus
git clone https://github.com/terry-li-hm/pondus.git ~/code/pondus
git clone https://github.com/terry-li-hm/oura.git ~/code/oura
```

---

## Quick Verification Checklist

Run this after Day 2 to confirm the standby is functional:

```bash
# Shell & environment
echo $ANTHROPIC_API_KEY | head -c 10   # should show first 10 chars (not empty)
which claude && claude --version        # Claude Code installed
ls ~/.claude/hooks/ | wc -l            # should be ~50 hooks
ls ~/.claude/skills/ | wc -l           # should be ~35 skills

# Core tools
mise --version
uv --version
cargo --version
bun --version
gh auth status                         # authenticated to GitHub

# Key Python tools
oghma --version 2>/dev/null || echo "oghma: needs build"
anam --version 2>/dev/null || echo "anam: needs build"
fasti --version 2>/dev/null || echo "fasti: needs build"

# Vault
ls ~/epigenome/chromatin | wc -l                     # should have hundreds of notes
ls ~/epigenome/chromatin/.obsidian/plugins | wc -l  # should be ~17 plugins

# LaunchAgents
launchctl list | grep com.terry | wc -l  # should be 30+
```

---

## What Syncs Automatically vs. Manual Transfer

### Syncs automatically (do nothing extra)
| What | How |
|------|-----|
| All API keys | 1Password CLI injection via `~/.zshenv` |
| officina config, hooks, skills | `git clone` in Step 4 |
| Obsidian vault + plugins | `git clone notes` in Step 4 |
| CLAUDE.md, MEMORY.md, rules | officina symlinks in Step 10 |
| Brewfile | officina/Brewfile |

### Manual transfer needed
| What | Method |
|------|--------|
| SSH private keys | `scp primary:~/.ssh/id_ed25519` |
| `.zshenv` (PATH + env structure) | `scp primary:~/.zshenv` or recreate |
| macOS Keychain legacy secrets | `security` CLI, manual re-entry |
| settings.local.json | Copy from officina claude-backup |
| Memory files | Copy from officina claude-backup |
| Standalone LaunchAgent plists | `scp primary:~/Library/LaunchAgents/com.terry.*.plist` |
| synaxis config.toml | Copy from officina claude-backup |
| `.zshrc` | `scp primary:~/.zshrc` |
| tmux/ghostty/starship configs | `scp primary:~/.config/<tool>/` |

### Intentionally left off DR standby
| What | Why |
|------|-----|
| Cursor/code editor state | Not needed for agent workflow |
| Browser cookies/profiles | agent-browser re-authenticates |
| `~/code/` full history | Clone on demand as needed |
| OrbStack VM state | Reprovisioned automatically |
| pgAdmin4 connections | Reconnect manually when needed |
| Telegram session | Re-login via QR code |

---

## Time Estimates by Day

| Day | Tasks | Est. Time |
|-----|-------|-----------|
| Day 1 (Apr 3) | Steps 1–12: Xcode, Homebrew, 1Password, repos, shell, SSH, git, Brewfile, Claude Code, symlinks, DR restore | ~2.5 h |
| Day 2 (Apr 4) | Steps 13–22: Runtimes, uv tools, Rust builds, LaunchAgents, Obsidian | ~2.5 h |
| Day 3 (Apr 5) | Steps 23–31: Shell polish, configs, keychain, oghma daemon | ~1 h |
| Day 4 (Apr 6) | Steps 32–37: Apps, OrbStack, wacli, Tailscale, remaining repos | ~1 h |
| **Total** | | **~7 h** |

**Minimum viable standby (Day 1 only, ~2.5 h):** Claude Code running with full config, hooks, skills, memory, and 1Password-injected API keys. All core workflows functional via shell. LaunchAgents and compiled tools deferred.

---

## Emergency Fast-Path (1 hour, bare minimum)

If you need the machine working in under an hour:

```bash
# 1. Xcode CLI
xcode-select --install

# 2. Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"

# 3. Core tools only
brew install git gh node uv mise

# 4. Claude Code
npm install -g @anthropic-ai/claude-code

# 5. 1Password CLI + auth
brew install --cask 1password-cli && op signin

# 6. Clone config
gh auth login
git clone https://github.com/terry-li-hm/officina.git ~/officina
git clone https://github.com/terry-li-hm/skills.git ~/skills
git clone https://github.com/terry-li-hm/notes.git ~/epigenome/chromatin

# 7. Wire Claude Code
mkdir -p ~/.claude
ln -sf ~/officina/claude/hooks ~/.claude/hooks
ln -sf ~/officina/claude/settings.json ~/.claude/settings.json
ln -sf ~/skills ~/.claude/skills
ln -sf ~/officina/claude/CLAUDE.md ~/CLAUDE.md
ln -sf ~/officina/bin ~/bin
mkdir -p ~/.claude/projects/-Users-terry/memory
cp ~/officina/claude-backup/memory/* ~/.claude/projects/-Users-terry/memory/

# 8. SSH keys from primary
scp primary:~/.ssh/id_ed25519 ~/.ssh/ && chmod 600 ~/.ssh/id_ed25519

# Done. Run: claude
```
