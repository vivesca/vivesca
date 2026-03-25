# Periodic Task Hygiene: LaunchAgents on macOS

All periodic tasks migrated from cron to LaunchAgents (Feb 2026). Plists tracked in `~/agent-config/launchd/`, symlinked to `~/Library/LaunchAgents/`.

## Why LaunchAgents Over Cron

| | Cron | LaunchAgent |
|---|---|---|
| Missed while asleep | Silently skipped | Fires on wake |
| Job status | Dig through logs | `launchctl list \| grep com.terry` (PID + exit code) |
| Environment | Shared, minimal PATH | Per-job `EnvironmentVariables` |
| Config format | Dense one-liners | Self-documenting plist per job |

## The Incident That Triggered Migration

**Feb 2026:** `ai-news-daily.py` silently failed for 3+ days. Crontab called `/usr/bin/python3` (system Python 3.9) but `trafilatura` was only installed under mise Python 3.13. No error notification — just stale data in the AI News Log.

**Detection:** Manual check of `~/.cache/lustro/state.json` timestamps + `~/logs/cron-lustro.log` showed repeated `ModuleNotFoundError` tracebacks.

**Immediate fix:** Converted to `uv run --script` with PEP 723 inline deps:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["feedparser", "requests", "trafilatura", "pyyaml", "beautifulsoup4"]
# ///
```

**Structural fix:** Migrated all 14 jobs to LaunchAgents since the underlying problem (cron's minimal environment) affects every job.

## Patterns That Still Apply

### 1. Silent Redundancy Creep

Jobs overlap over time. Fix: quarterly review via `/cron` skill.

### 2. Graceful-Degradation Masking Broken Core

If a job's primary capability needs unavailable infra (browser, auth session), the fallback pretends things work. Either fix or kill.

**Heuristic:** If a job has never used its primary path in 5+ runs, the fallback IS the feature.

### 3. Python Scripts: Use `uv run --script` for Third-Party Deps

System Python (`/usr/bin/python3`, 3.9) has a minimal package set. Scripts needing third-party packages should use PEP 723 inline deps with `uv run --script`. Stdlib-only scripts can safely use `/usr/bin/python3`.

### 4. uv tool Packages Need `--with` for Optional Deps

`uv tool install oghma` doesn't include numpy. Fix: `uv tool install oghma --force --reinstall --with numpy`.

### 5. Stale Binary Paths After Reinstall

Every silent failure pattern is the same: a binary path valid at setup time, invalidated by reinstall. After any `uv tool install`, `brew upgrade`, or mise version change:

```bash
grep -r "old/path" ~/agent-config/launchd/ ~/Library/LaunchAgents/
```

## Audit Checklist

When reviewing periodic tasks:

- [ ] All ProgramArguments use absolute paths
- [ ] Test each job: run the ProgramArguments manually
- [ ] Check `launchctl list | grep com.terry` for non-zero exit codes
- [ ] Python scripts with third-party deps use `uv run --script`
- [ ] Optional deps present (`--with numpy`, etc.)
- [ ] Plists in `~/agent-config/launchd/` match what's loaded

## Related

- `~/docs/solutions/tool-gotchas.md` — Python environment gotchas
- `~/docs/solutions/content-consumption-architecture.md` — AI news pipeline overview
- `/cron` skill — quick listing of all agents
