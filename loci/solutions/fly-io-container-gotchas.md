# Fly.io Container Gotchas

## set -e in entrypoint kills the machine

Fly.io restarts the machine when the main process exits non-zero. If your entrypoint has `set -e` and *any* command fails (e.g. Tailscale auth with an expired key), the entire machine crash-loops. Remove `set -e` from Fly entrypoint scripts. Handle errors explicitly with `|| true` or `|| echo "warning"`.

## Persistent volumes shadow build-time user files

If you mount a volume at `/home/terry`, anything installed there during `docker build` (Rust, Bun, user configs) gets overwritten by the empty volume on first boot. Solution: install system tools globally (`/usr/bin`, `/opt/tools`), install user tools in the entrypoint's first-boot block (guarded by a `.bootstrapped` sentinel file).

## Docker COPY layer caching

When you change a file that's COPYed into the image, the build cache may not invalidate if the layer hash matches. Use `--no-cache` to force, or add a build arg with a timestamp to bust the specific layer.

## Tailscale state persistence

`tailscaled --state=/var/lib/tailscale/tailscaled.state` persists auth state. If you used a bad auth key, that state replays on every boot even after fixing the key. Either store state in `/tmp/` (ephemeral) or `rm -f` the state file in the entrypoint before starting tailscaled.

## Singapore capacity

Fly.io Singapore (`sin`) frequently runs out of capacity for `performance-2x` and even `shared-cpu-2x` machines. Tokyo (`nrt`) is more available in APAC.

## Environment variable conflicts

Don't put `ANTHROPIC_API_KEY` in `.zshenv.local` on a machine where Claude Code uses OAuth (Max subscription). The env var takes precedence and triggers an interactive prompt asking which auth to use — breaking `--print` mode and confusing interactive sessions. Only set API keys that the CLIs actually need (OpenRouter, Exa, xAI, etc.).

## Building Rust CLIs from source on Fly.io

All personal Rust CLIs compiled on Linux x86_64 without code changes. The 2-core shared machine builds slowly (~5 min per CLI) but everything works. After building, clean up with:
- `rm -rf ~/code/*/target` (build artifacts, biggest space saver)
- `rm -rf ~/.cargo/registry/{cache,src}` (download cache)
- `rustup component remove rust-docs`
- `go clean -modcache` (if Go tools built)

A 10GB volume holds everything but gets tight after 13 Rust CLIs + gog. Keep disk <80%.
