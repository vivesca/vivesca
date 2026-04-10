---
id: REQ-20260410-001
title: Soma-primary + Mac-DR migration plan
tags: [soma, mac, dr, infra, oscillators, supercronic]
status: phase-0-complete
---

# Soma-Primary with Mac Hot-DR

**Goal:** Soma owns all schedulable workloads as primary. Mac is a hot-DR site — same jobs loaded, gated by `soma-alive-check`, exit early when soma is up, take over when soma fails. Sub-minute recovery, zero drift.

## Current state (Apr 10 2026)

| | Mac | Soma |
|---|---|---|
| Scheduled jobs | **52 LaunchAgents** (49 via `oscillators/`, 3 standalone) | **0** (crontab stub only, no daemon) |
| Supervisor processes | — | 3 (vivesca MCP, soma-watchdog, temporal-dispatch) |
| Volume | Local | 40GB (extended Apr 10, 24% used) |
| Health check | — | TCP:22 via Fly (added Apr 10) |
| Secret pipeline | `~/.zshenv.secrets` + `op-resolve-secrets` LaunchAgent | `~/.zshenv.secrets` + `~/.cache/env-secrets.sh` (already working) |

## Classification

### MUST-STAY-MAC (8 jobs) — platform-dependent

These jobs cannot run on soma. They remain Mac-exclusive and are **never** gated by `soma-alive-check`.

| Job | Why |
|---|---|
| `cookie-bridge` (standalone plist) | Reads Chrome cookies via macOS keychain |
| `op-resolve-secrets` (standalone plist) | 1Password biometric unlock is macOS-only |
| `soma-pull` (standalone plist) | Pulls files FROM soma TO Mac (must run on receiver) |
| `due-backup` | Backs up Due.app sqlite (Mac app) |
| `launchagent-health` | Monitors macOS LaunchAgents |
| `location-receiver` | HTTP endpoint for Mac CoreLocation data |
| `wacli-sync` | `wacli` requires Mac's WhatsApp desktop client |
| `mcp` (vivesca serve on Mac) | Provides MCP endpoint for local Mac Claude sessions. *Could* be removed if all Claude runs over SSH to soma, but keeping it as Mac-local MCP is cheap. |

### MIGRATE-TO-SOMA (41 jobs) — portable, no Mac deps

These move to soma supercronic. Mac keeps the plist as hot-DR (runs the same command but gated by `soma-alive-check`).

**Content ingestion (5 jobs):**
- `endocytosis-breaking`, `endocytosis-daily`, `endocytosis-digest`, `endocytosis-monthly-digest`
- `x-feed-lustro` (Twitter/X feed processing)

**Knowledge work / reviews (17 jobs):**
- `transduction-daily`, `transduction-weekly`, `transduction-monthly`, `transduction-quarterly`, `transduction-yearly`, `transduction-phronesis-weekly` (6)
- `interphase-close`, `interphase-weekly`, `interphase-monthly` (3)
- `consolidation-weekly`, `methylation`, `mismatch-repair`, `mismatch-repair-weekly` (4)
- `circadian-probe`, `complement`, `demethylase`, `immunosurveillance` (4)

**Monitors / health (7 jobs):**
- `respirometry` (every 5m), `pulse` (every 30m), `pondus-monitor` (daily)
- `inflammasome` (hourly), `mitosis` (hourly), `mitosis-checkpoint` (30m), `perfusion` (2x/day)

**Data sync (4 jobs):**
- `oura-sync` + `sopor` (likely dedup — both run `sopor sync`)
- `pharos-sync`, `phenotype-sync`

**Content publishing (2 jobs):**
- `blog-sync` (garden → chromatin → blog)
- `exocytosis` (garden publish)

**Maintenance (6 jobs):**
- `chromatin-backup`, `rotate-logs`, `logrotate`
- `qmd-reindex`, `update-coding-tools`, `wewe-rss-health`

**Scheduled work (2 jobs):**
- `csb-ai-jobs` (Friday noon job scan)
- `nightly` (daily nightly sweep)

**Uncategorized — needs deeper look (1 job):**
- `speculor` (LinkedIn alerts — may need browser cookies, verify before migrating)

**Total: 41 jobs to migrate.** Some may deduplicate (e.g. `oura-sync`/`sopor`, `rotate-logs`/`logrotate`).

## Migration pattern (per job)

1. **Add to soma crontab** (`~/germline/loci/crontab`):
   ```
   0 6 * * * soma-cron-wrap transduction-daily /bin/zsh -c 'source ~/.zshenv && transduction --period daily'
   ```
2. **Test on soma** by running the command manually first:
   ```
   ssh soma "soma-cron-wrap transduction-daily <cmd>"
   ```
3. **Reload supercronic** on soma:
   ```
   supervisorctl -s unix:///tmp/supervisor.sock restart supercronic
   ```
4. **Wrap the Mac plist command** with `soma-alive-check` gate — script becomes:
   ```bash
   #!/bin/bash
   if /Users/terry/germline/effectors/soma-alive-check; then
     exit 0  # soma is alive, DR standby
   fi
   exec <original-command>
   ```
   Done by editing each plist to call the wrapper, OR by writing a single `dr-gate` effector that takes the original command as args.
5. **Verify**: soma runs the job (cron-runs.jsonl has the entry), Mac plist runs and immediately exits (logs `soma alive, standby`).

## Infrastructure (Phase 1 — complete this turn)

- [x] **supercronic** installed at `/home/vivesca/.local/bin/supercronic` (v0.2.29, linux-amd64)
- [x] **soma-cron-wrap** wrapper script — sources env, runs command, logs to `cron-runs.jsonl`
- [x] **soma-alive-check** — DR gate with Tailscale + Fly fallback
- [ ] **supercronic supervisor entry** — added to `supervisor.conf`, deployed, restarted
- [ ] **Pilot job** — migrate ONE job end-to-end (recommend `rotate-logs`, Sunday-only, low-stakes)
- [ ] **Verify pilot** — soma runs, Mac gated out

## Open questions

1. **Which Mac plists should NOT be DR-gated?** A few are Mac-only-forever (cookie-bridge etc.) and keep running normally. Others (transduction, etc.) should always defer to soma when available. Clear so far.
2. **How to handle "should run on both" cases?** E.g. log rotation — both Mac and soma have their own logs. Keep `rotate-logs` on Mac (rotates Mac logs), soma gets its own log rotator. These are NOT the same job; they don't overlap.
3. **Speculor secrets** — does it need Chrome cookies for LinkedIn? If yes, stays on Mac or uses cookie-bridge from soma. Needs per-job investigation.
4. **Real-time sync vs batch sync** — several jobs run every 5m (respirometry, blog-sync, pharos-sync, phenotype-sync). At that cadence, running on both Mac and soma is wasteful. DR-gate keeps Mac cost near zero.

## Phase roadmap

- **Phase 0 — Audit + plan**: DONE (this doc)
- **Phase 1 — Infra**: supercronic installed, wrappers created, pilot pending
- **Phase 2 — Bulk migration**: 41 jobs. Batch by category. Per-job test. Multi-session.
- **Phase 3 — Mac DR gating**: Wrap each migrated plist with `soma-alive-check`. Single session.
- **Phase 4 — Runbook + DR drill**: Document failover path, intentionally freeze soma, verify Mac takes over, restore.

## Risk register

- **Secrets drift**: Soma's `env-secrets.sh` must have the same vars Mac does. Verify before migrating each job.
- **Path translation**: Every `/Users/terry/` → `/home/vivesca/`. Mise python paths differ. Homebrew paths (`/opt/homebrew/`) don't exist on soma.
- **Job overlap during migration**: If a job runs on both sides during the transition, it may do the work twice (email sends, LinkedIn posts). Sequence is: soma starts running → verify → then add DR gate to Mac. In that window, Mac still runs without gate. For notify-type jobs, disable Mac BEFORE adding to soma.
- **Supercronic stall**: Like temporal-dispatch before it, supercronic can stall silently. Add a watchdog probe in soma-watchdog.
