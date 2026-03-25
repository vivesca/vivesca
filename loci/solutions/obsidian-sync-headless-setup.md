# Obsidian Sync Headless Client

**Date:** 2026-02-28
**Status:** Running (open beta, v1.0.0)

## What

Official headless client for Obsidian Sync (`obsidian-headless` npm package, CLI: `ob`). Syncs vaults without the desktop app. Announced 2026-02-27.

## Requirements

- Node.js 22+
- Obsidian Sync subscription
- E2E encryption password (if vault is encrypted)

## Installation

```bash
npm install -g obsidian-headless
ob login                    # interactive — prompts for email/password/MFA
ob sync-list-remote         # find vault name/ID
cd ~/code/epigenome/chromatin
ob sync-setup --vault "Notes" --device-name "iMac-headless"  # prompts for E2E password
ob sync                     # one-shot test
ob sync --continuous        # daemon mode
```

## iMac LaunchAgent

Plist: `~/agent-config/launchd/md.obsidian.sync-headless.plist` (symlinked to `~/Library/LaunchAgents/`).

- Runs `ob sync --continuous --path /Users/terry/code/epigenome/chromatin`
- `KeepAlive: true` — auto-restarts on crash
- `RunAtLoad: true` — starts on login
- Log: `~/Library/Logs/obsidian-sync-headless.log`

### Management

```bash
launchctl list | grep obsidian              # check status
tail -f ~/Library/Logs/obsidian-sync-headless.log  # watch logs
launchctl stop md.obsidian.sync-headless    # stop
launchctl start md.obsidian.sync-headless   # start
launchctl unload ~/Library/LaunchAgents/md.obsidian.sync-headless.plist  # disable
```

## Desktop App Sync Disabled

Set `"sync": false` in `~/code/epigenome/chromatin/.obsidian/core-plugins.json` to avoid duplicate syncing. The headless daemon handles it. To re-enable desktop sync (e.g., travelling): flip back to `true` and restart Obsidian.

## Key Commands

| Command | Purpose |
|---|---|
| `ob login` | Auth (or `OBSIDIAN_AUTH_TOKEN` env var for servers) |
| `ob sync-list-remote` | List remote vaults |
| `ob sync-setup` | Link local dir to remote vault |
| `ob sync --continuous` | Watch-mode daemon |
| `ob sync-config` | Conflict strategy, file filters, excluded folders |
| `ob sync-status` | Current sync state |
| `ob sync-unlink` | Disconnect vault |

## Obsidian App Management

Obsidian is now managed by Homebrew (`brew install --cask obsidian`). Previously installed manually (no package manager). Updated 1.8.10 → 1.12.4 on 2026-02-28.

- Update: `brew upgrade --cask obsidian`
- First install over existing app required `--force` (and quitting Obsidian first)
- v1.12.4 includes the `obsidian` CLI, Bases, and better agent support

## Gotchas

- **E2E encrypted vaults:** `sync-setup` fails silently with "Failed to validate password" if no password provided. Pass `--password` or let it prompt interactively.
- **Two sync clients on same vault:** Works fine (Obsidian Sync handles multi-device), but redundant. Disable desktop sync if running headless.
- **Linux config path differs:** `~/.config/obsidian-headless/` (not `~/.obsidian-headless/`). Uses `XDG_CONFIG_HOME` if set.
- **Auth tokens are device-specific:** Cannot copy `auth_token` between machines. Must `ob login` on each device. Interactive prompts may not work over SSH — use `--email`/`--password` flags.
- **Broken symlinks crash sync:** If vault contains symlinks to machine-specific paths (e.g., `/Users/terry/...` on a Linux box), sync crashes with ENOENT on `mkdir`. Fix symlinks to use correct local paths before starting sync.
- **Initial sync takes minutes on large vaults:** The first run checks every file. New changes from other devices won't appear until the initial check completes.
- **Linux:** Works but no file birthtime preservation (native addon only for macOS/Windows).
- **npm 403 on package page:** Package exists but npmjs.com may block web fetch. Use `npm view obsidian-headless` to check.
- **Beta:** v1.0.0 as of 2026-02-28. Watch for breaking changes.

## Pharos (NixOS EC2)

**Status:** Running (systemd service, continuous sync).

### Setup

```bash
npm install -g obsidian-headless    # installs to ~/.local/bin/ob
ob login --email <email> --password <pass> [--mfa <code>]
ob sync-setup --vault "Notes" --device-name "Pharos" --path /home/terry/notes
```

### Config paths (Linux)

Linux uses `~/.config/obsidian-headless/` (not `~/.obsidian-headless/`):
- Auth: `~/.config/obsidian-headless/auth_token`
- Sync config: `~/.config/obsidian-headless/sync/<vaultId>/config.json`
- State DB: `~/.config/obsidian-headless/sync/<vaultId>/state.db`

### systemd service

File: `~/.config/systemd/user/obsidian-sync.service`

```ini
[Unit]
Description=Obsidian Headless Sync
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/terry/scripts/pharos-env.sh ob sync --continuous --path /home/terry/notes
Restart=on-failure
RestartSec=30
Environment=NODE_NO_WARNINGS=1

[Install]
WantedBy=default.target
```

Management:
```bash
systemctl --user start obsidian-sync
systemctl --user status obsidian-sync
journalctl --user -u obsidian-sync -f   # watch logs
systemctl --user restart obsidian-sync
```

### vault-git-backup: commit-only mode

With Obsidian Sync handling cross-device sync, `vault-git-backup.sh` on Pharos was stripped to commit-only (no push/fetch/rebase). This eliminates push races with the Mac's Obsidian Git plugin. Mac still pushes to GitHub as offsite backup.

### Auth token gotcha

Auth tokens are device-specific — cannot copy from another machine. Must `ob login` on each device. Interactive prompts may not work over SSH; use `--email`/`--password` flags.

## References

- [Changelog](https://obsidian.md/changelog/2026-02-27-sync/)
- [Docs](https://help.obsidian.md/sync/headless)
- [GitHub](https://github.com/obsidianmd/obsidian-headless)
- [kepano on use cases](https://x.com/kepano/status/2027485552451432936)
