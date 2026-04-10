---
id: LRN-20260410-001
title: Fly VM freeze detection and recovery
tags: [fly, soma, infra, health-check, watchdog]
---

# Fly VM Freeze Detection

## Problem

Soma (Fly app, 20GB volume, performance-2x) froze silently from **Apr 7 → Apr 10 2026** — three days of downtime before anyone noticed. Fly's machine list still showed `state=started` the whole time; only Tailscale pings revealed the VM was a zombie.

The freeze reoccurred after the first fix (`finding_uv_cache_volume_freeze.md`) because the fix was incomplete: the watchdog's cache pruning was reactive (triggered by disk pressure) and used `rglob()` for size calculation, which hangs on stressed I/O.

## Root cause chain

1. `uv` + `pre-commit` caches grew unchecked to ~1.3GB combined
2. Disk filled to **1.4GB free** on 20GB volume (~93% full)
3. Watchdog entered `DISK WARN` state and tried to clean — but:
   - `clean_temps()` only removed pytest dirs + `__pycache__`, freed <50MB
   - Cache pruning code existed but used `rglob("*")` for size check → hangs forever on near-full stressed ext4
   - Result: `DISK WARN: 1.4GB → 1.4GB (cleaned 0)`
4. I/O stall → kernel unresponsive → VM frozen
5. **No Fly health check configured** → Fly's control plane didn't know → no auto-restart
6. **Watchdog alerts only fired at CRIT** (disk < 1GB), but disk never crossed that threshold → no deltos ping during the 3-day freeze

## Fix (three layers)

### Layer 1: Fly health check (the safety net)

Add TCP check on the internal SSH port to `fly.toml`. If sshd stops accepting connections, the VM is frozen — Fly auto-restarts on failing health checks.

```toml
[[services]]
  internal_port = 22
  protocol = 'tcp'
  [[services.ports]]
    port = 10022
  [[services.tcp_checks]]
    grace_period = '60s'
    interval = '30s'
    timeout = '5s'
```

Deploy with existing image (no rebuild needed):
```bash
fly deploy -c fly.toml --image registry.fly.io/<app>:deployment-<current-tag>
```

Verify: `fly status -a soma` should show `1 total, 1 passing` under CHECKS.

### Layer 2: Grow volume (remove chronic pressure)

20GB is too tight for a Python + Node + Rust + AI-tools dev VM. Extend in-place:
```bash
fly volumes extend <vol-id> -s 40 -a <app>
```
No restart needed. Costs ~$1.50/mo extra. Was the highest leverage per-dollar fix.

### Layer 3: Proactive cache pruning (fix the watchdog)

In `soma-watchdog`:

1. **Run `prune_caches()` every cycle**, not only on disk pressure — I/O is already slow by the time you notice
2. **Use `du -sb` with 15s timeout**, never `Path.rglob()` — rglob hangs on stressed filesystems
3. **Per-cache budgets**: uv 300MB, pre-commit 300MB, npm 500MB, opencode 500MB, claude 400MB, cargo/registry 400MB
4. **Alert at WARN, not just CRIT** — soft failures persist for days otherwise. WARN dedup at 60min, CRIT at 15min
5. **Never prune playwright or `.local/share/uv`** — those hold runtime-needed binaries

See `~/germline/effectors/soma-watchdog` for reference implementation.

## Deployment technique: reuse existing image

`fly deploy` rebuilds by default. To push a config change (e.g. new health check) without a full rebuild:

```bash
# Get current image tag
fly status -a soma | grep Image

# Deploy config change with --image
fly deploy -c fly.toml --image registry.fly.io/<app>:<current-tag>
```

Avoids dependency churn and 10-minute build times.

## Diagnostic commands

Before blaming Fly infra, check these:

```bash
# Is the VM actually responsive?
tailscale ping soma
fly ssh console -a soma -C "uptime"

# Is disk full?
fly ssh console -a soma -C "df -h"

# What's using space?
fly ssh console -a soma -C "sh -c 'du -sh /home/vivesca/.[!.]*/ | sort -rh | head -15'"

# Is watchdog actually running?
fly ssh console -a soma -C "sh -c 'tail -20 /home/vivesca/tmp/soma-watchdog.log'"

# Did metrics capture the ramp?
fly ssh console -a soma -C "sh -c 'tail -20 /home/vivesca/.local/share/vivesca/soma-resources.jsonl'"
```

If `cpu_1m` is spiking while `mem_pct` stays low and `disk_free_gb` is dropping → **I/O stall, not OOM**. Check caches first.

## Gotchas

- **`fly ssh console -C` doesn't handle pipes/redirects directly** — wrap in `sh -c '...'` or commands like `df -h && uptime` will error out
- **Supervisor + Python `HOME`**: supervisor config sets `environment=HOME="/home/vivesca"` but Python's `Path.home()` can still fall back to passwd. Use `Path(os.environ.get("HOME", Path.home()))` for belt-and-suspenders
- **`fly volumes extend` is in-place** — no restart needed, works live
- **Port 6080 was configured in `fly.toml` as a service but nothing listened** — `fly deploy` warned about it. Dead config from a previous VNC attempt; leaving it for now but worth cleaning
