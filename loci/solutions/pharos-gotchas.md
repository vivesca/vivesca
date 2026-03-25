# Pharos Gotchas

Ubuntu 24.04 LTS on EC2 t3.small (ap-southeast-1). Migrated from NixOS Feb 2026.

## systemd user services have minimal PATH
Services don't source `.zshenv`. Use `pharos-env.sh` wrapper:
- Sets PATH (`.local/bin`, `.cargo/bin`, `.bun/bin`, Nix profile dirs)
- Sources `.zshenv.local` (API keys)
- `exec "$@"` — shebangs work fine on Ubuntu (no .sh detection hack needed)

## systemd user timers need linger
`loginctl enable-linger terry` — without this, user services stop when terry logs out.

## systemd ExecStart eats shell variables
`$VAR` in ExecStart is consumed by systemd's own variable expansion (not bash). Inline scripts with `$()`, `$DISK`, etc. will silently produce empty strings.
Fix: put logic in a separate `.sh` script, call that from ExecStart.

## OnCalendar values must be UTC
HKT = UTC+8. Example: 06:45 HKT = 22:45 UTC (previous day).
`*:0/120` is INVALID for "every 2 hours" — use `0/2:00` instead.

## bun global install may fail silently
`bun install -g "github:tobi/qmd"` reports success but binary doesn't appear in `~/.bun/bin/`.
Fix: clone repo, `npm install`, `npm run build`, `npm link` (with `npm config set prefix ~/.local` first).

## npm needs user prefix
Default npm prefix is `/usr` (requires sudo). Set `npm config set prefix ~/.local` for user installs.
Also set `npm config set script-shell /bin/bash` to avoid shell resolution issues.

## OpenCode is from sst/opencode, not opencode-ai/opencode
- iMac: `brew install opencode` → sst/opencode v1.2.x
- pharos: download `opencode-linux-x64.tar.gz` from github.com/sst/opencode/releases
- `opencode-ai/opencode` is a different project (v0.0.x, different CLI flags)

## OpenCode provider resolution
`zhipuai-coding-plan/glm-5` only works on iMac.
On pharos, use `openrouter/google/gemini-2.0-flash-001` via OPENCODE_MODEL env var.

## oghma dedup needs numpy
`uv tool install oghma --force --with numpy` — numpy isn't a default dependency.

## compound-pplx binary name
Cargo builds `compound-pplx`, not `pplx`. Symlink: `ln -sf ~/.cargo/bin/compound-pplx ~/.local/bin/pplx`.

## Tailscale hostname collisions
Tailscale appends `-1` when hostname collides with existing device. Fix: delete stale devices from admin, then reset node state (`rm /var/lib/tailscale/tailscaled.state`) and rejoin.
No programmatic device management without API key — generate one and store in keychain.

## Tailscale logout is destructive
`tailscale logout` removes the device from the network. Needs re-auth (browser OAuth or auth key). Don't use it to test things.

## SSH via MagicDNS may not resolve
If iMac uses Mullvad exit node, MagicDNS names may not resolve. Use Tailscale IP directly (e.g., `100.72.193.70`) or add to `~/.ssh/config`.

## Swap is essential
t3.small = 2GB RAM. 2GB swap via cloud-init. capco-brief hit 1GB peak memory on t3.micro.

## Stale ControlMaster sockets cache failed auth
If SSH fails once with ControlMaster enabled, the failed connection gets cached in `~/.ssh/sockets/`. Subsequent attempts reuse the dead socket instead of retrying. Fix: `rm ~/.ssh/sockets/<user>@<host>-<port>`.

## Claude Code OAuth token: `/login` may not refresh
On headless servers, `/login` can say "Login successful" without actually refreshing an expired token. Fix: `rm ~/.claude/.credentials.json` then `/login` again for a fresh OAuth flow.

## Claude Code memory path differs by OS
macOS: `~/.claude/projects/-Users-terry/memory/MEMORY.md`
Linux: `~/.claude/projects/-home-terry/memory/MEMORY.md`
No sync mechanism — manual copy when needed.

## NixOS migration reference
See `~/code/epigenome/chromatin/NixOS vs Nix-on-Ubuntu for Agent Machines.md` for the full comparison and why we moved.
