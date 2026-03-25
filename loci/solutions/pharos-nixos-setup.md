# Pharos (NixOS) Setup & Sync

## Bootstrap

```bash
# First time (from any machine with SSH access)
bash <(ssh mac cat agent-config/scripts/bootstrap.sh)

# Re-run (idempotent)
~/agent-config/scripts/bootstrap.sh --nixos

# NixOS rebuild (separate step, needs sudo)
cd ~/code/pharos && git pull && sudo nixos-rebuild switch --flake .#pharos
```

Daily sync via systemd timer (`agent-sync.timer`, 6am UTC / 2pm HKT) pulls repos + re-runs bootstrap.

## NixOS Gotchas (Hard-Won)

### Shebangs
- **`#!/bin/bash` doesn't exist** on NixOS. Always use `#!/usr/bin/env bash`.

### DNS
- **Tailscale MagicDNS (100.100.100.100) can't resolve public hosts.** Fix: `networking.resolvconf.extraConfig = "append_nameservers='1.1.1.1 8.8.8.8'"` — plain `networking.nameservers` gets overridden by Tailscale's resolvconf priority.

### Memory
- **2GB RAM OOMs on bun/cargo builds.** Add swap: `swapDevices = [{ device = "/swapfile"; size = 2048; }]`

### Rust Toolchain
- **nix `rustup` package, not curl installer.** The curl installer downloads a dynamically linked binary which NixOS can't run. Use `pkgs.rustup` in configuration.nix.
- **`rustup toolchain install stable`** needed after first install — nix rustup package doesn't include a default toolchain.
- **`openssl.dev`** (not `openssl`) for cargo crates that link OpenSSL. Provides headers + pkg-config files.
- **`gcc`** needed for cargo — provides the `cc` linker.
- **`PKG_CONFIG_PATH=/run/current-system/sw/lib/pkgconfig`** must be set for cargo builds to find system libraries.

### npm
- **nix store is read-only.** Use `npm install -g --prefix ~/.local <pkg>`.

### Auth
- **No keychain/secret-service** — headless server has no gnome-keyring. Use env vars in `~/.zshenv.local`.
- **`claude login` needs interactive TTY** — use `CLAUDE_CODE_OAUTH_TOKEN` env var instead.
- **OAuth token location (macOS)** — Keychain under service "Claude Code-credentials", key `claudeAiOauth.accessToken`.

### Config
- **`.gitconfig` credential helpers** — can't hardcode `/opt/homebrew/bin/gh`. Shared `.gitconfig` uses `[include] path = ~/.gitconfig.local`; `install.sh` generates platform-specific credentials.

## Paths
- Claude Code: `~/.local/bin/claude`
- Cargo binaries: `~/.cargo/bin/`
- Node: `/run/current-system/sw/bin/node`
- System packages: `/run/current-system/sw/bin/`
- Bun globals: `~/.bun/bin/`
- uv tools: `~/.local/bin/`
