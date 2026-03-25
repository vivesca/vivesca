# Verify Through the Deployed Path

**Rule:** After fixing a bug in a system that runs via cron/CLI/service, always verify through the exact entry point production uses — not by calling the function directly in Python.

## Why

Functions have different behavior when called with default parameters vs when called from a pipeline that passes parameters explicitly. Testing `gather_daily()` (no args) exercises the default `today=None` path. But the cron runs `thalamus --period daily` → `run_pipeline()` → `gather_daily(today=date.today())` — the `today` parameter is always populated, so the default never fires.

**Burned twice:** Mar 17-18, 2026. Fixed `gather_daily` default to subtract 1 day. Verified by calling `gather_daily()` directly — worked. Cron ran at 3am, passed `today=date.today()` explicitly, bypassed the fix entirely. 4 more days of silent failure.

## The Heuristic

After fixing any code that runs via a scheduled/automated path:

1. Find the exact command the cron/service runs (check the plist/systemd/crontab)
2. Run that exact command manually
3. If the fix works via direct function call but NOT via the CLI — the fix is in the wrong layer

## Applies To

- LaunchAgent plist commands (`uv run --project ... thalamus --period daily`)
- Systemd timers
- Any CLI wrapper around library code
- Webhook handlers
- CI/CD pipeline steps
