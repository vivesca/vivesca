---
name: usage
description: Check Claude Code Max plan usage stats and token consumption. "usage", "token usage", "how much have I used", "quota"
triggers:
  - usage
  - ccusage
  - token usage
  - cost
  - spending
  - quota
  - rate limit
  - /status
user_invocable: true
---

# Claude Code Usage Check

Check token usage and equivalent costs for Claude Code Max plan.

## Quick Commands

```bash
# Current month daily breakdown with model mix
ccusage daily -s $(date +%Y%m01) --breakdown

# Monthly summary
ccusage monthly

# Per-session breakdown
ccusage session -s $(date +%Y%m01)

# Live monitoring (run in separate terminal)
claude-monitor --plan max20
```

## Procedure

### Standard usage check
1. Run `ccusage daily -s $(date +%Y%m01) --breakdown` for current month with model breakdown
2. Summarize key stats:
   - Total tokens used this month
   - Equivalent API cost (for context on value extracted)
   - Daily average
   - Model mix (Opus vs Haiku vs Sonnet)
3. Calculate weekly usage (see below)
4. If user wants live tracking, suggest running `claude-monitor --plan max20` in a separate terminal

### When Terry posts /status output (calibration trigger)
1. Extract the weekly all-models % and Sonnet % from the pasted output
2. Run ccusage since last Friday to get week-to-date dollar equiv:
   ```bash
   ccusage daily -s <last_friday_YYYYMMDD> --json | python3 -c "
   import json,sys; d=json.load(sys.stdin)
   total=sum(x['totalCost'] for x in d['daily'])
   print(f'Week-to-date: \${total:.2f}')
   "
   ```
3. Calculate implied cap: `total / (pct / 100)`
4. Add new row to the Calibration Data table in this skill
5. Report: current week %, implied cap, and safety status

## Max Plan Context

| Plan | Monthly Cost | Token Allowance |
|------|--------------|-----------------|
| Max5 | $100 | ~88K tokens/5min window |
| Max20 | $200 | ~220K tokens/5min window |

**User self-check:** `/status` in the Claude Code prompt shows exact usage % and reset times directly (Claude cannot run this — it's an interactive UI command).

## Usage Counters (/status)

Max20 has **four independent counters** visible via `/status`:

| Counter | Scope | Reset Cycle | Notes |
|---------|-------|-------------|-------|
| Session | Per-session | ~4pm HKT daily | Least important — resets frequently |
| Weekly (all models) | Opus + Sonnet + Haiku | Friday ~11am HKT | **Primary limiter** |
| Weekly (Sonnet only) | Sonnet usage only | Friday ~3pm HKT | Separate Sonnet quota |
| Extra usage | Monthly spend cap | 1st of month | $50 hard cap, shows $/$ spent |

**How the counters interact** ([source](https://github.com/anthropics/claude-code/issues/12487)):
- Sonnet usage counts against **both** "Sonnet only" AND "All models"
- Opus usage counts against "All models" **only**
- When "All models" hits 100%, everything is blocked — even if "Sonnet only" shows 2%
- The Sonnet cap is a **ceiling** (prevents filling all-models quota with cheaper Sonnet tokens), not a separate pool

## Weekly Limit Tracking (All Models)

**The weekly cap is in Anthropic's internal token units — NOT dollars.** ccusage dollar-equiv is a proxy that varies significantly by model mix.

### Calibration Data

| Date | Era | ccusage equiv | /status % | Implied cap | Mix |
|------|-----|--------------|-----------|-------------|-----|
| Early Feb 2026 | Opus 4.5 | $470-490 | 44% | ~$1,070-1,115 | Opus-heavy |
| Early Feb 2026 | Opus 4.5 | $200-260 | 20% | ~$1,000-1,300 | Opus-heavy |
| Feb 25, 2026 | Opus 4.6 | ~$717-767 | 54% | ~$1,330-1,420 | Opus-heavy |
| Mar 8, 2026 | Sonnet 4.6 | ~$392-421 | 13% | ~$3,000-3,200 | Sonnet-only |

### Cap Estimates by Model Mix

| Dominant model | Implied dollar-equiv cap | Notes |
|---------------|--------------------------|-------|
| **Opus 4.6** | ~**$1,350** | Well-calibrated (3 data points) |
| **Sonnet 4.6** | ~**$3,000+** | 1 data point (Mar 2026) — directional only |
| Mixed | Interpolate | Sonnet shifts cap higher |

**Key insight:** Anthropic's internal weights treat Opus as ~2-3x heavier than Sonnet, vs. the 1.67x public API price ratio. Don't use the $1,350 cap when running Sonnet-dominant sessions.

### Calibration Protocol — When /status Data Is Posted

**Whenever Terry posts /status output → invoke this skill and run:**
```bash
ccusage daily -s <last_friday_YYYYMMDD> --json | python3 -c "
import json,sys; d=json.load(sys.stdin)
total=sum(x['totalCost'] for x in d['daily'])
print(f'Week-to-date: \${total:.2f}')
"
```
Then: `implied_cap = ccusage_total / (status_pct / 100)`. Add new row to calibration table above.

### Status Thresholds

| % Used | Opus-equiv | Sonnet-equiv | Status |
|--------|-----------|--------------|--------|
| 0-50% | $0-675 | $0-1,500 | Safe |
| 50-70% | $675-945 | $1,500-2,100 | Caution |
| 70-85% | $945-1,148 | $2,100-2,550 | Warning |
| 85%+ | $1,148+ | $2,550+ | Danger |

**To calculate weekly %:** Find last Friday ~11am HKT (all models reset), sum ccusage cost since then, divide by appropriate cap for current model mix.

## Model Mix & Cost (Feb 2026 baseline)

**Opus dominates but Sonnet share growing.** `/model` shows Opus 4.6 as "Default (recommended)" for Max users. Shifting to Sonnet is a cost lever for quota management, not a quality correction.

**Full month (Feb 1-25):**

| Model | Daily Avg | % of Total | Role |
|-------|-----------|------------|------|
| Opus | ~$138 | 90% | Primary — all interactive work |
| Sonnet | ~$12 | 8% | Subagents, compound-engineering, routine tasks |
| Haiku | ~$1 | <1% | Lookups only |

**Monthly run rate:** ~$153/day equiv → ~$4,600/month (23x the $200 plan cost).

**Model transition visible in data:**
- Opus 4.5 → 4.6: ~Feb 6
- Sonnet 4.5 → 4.6: ~Feb 18

**Sonnet 4.6 adoption (post-Feb 18):**
- Before: Sonnet $0-2/day
- After: Sonnet $5-48/day (highly variable — $48 on Feb 21 was an outlier)
- Opus share dropped from 96% to ~85% on Sonnet-heavy days

**Daily variance is 4x:** $84 (Feb 7) to $364 (Feb 2). Heavy days are nearly all Opus-dominant.

**Cache efficiency:** Cache read tokens are ~25x cache create tokens. Compaction and context reuse working well.

**Cost lever:** Opus 4.6 is ~1.67x more expensive per token than Sonnet 4.6 ($5/$25 vs $3/$15). Each $100 of Opus work shifted to Sonnet saves ~$40 equiv. A 30% shift would save ~$17/day → ~$117/week (~9% of weekly cap). Meaningful but not transformative — the pricing gap closed significantly with Opus 4.5+.

## Extra Usage

$50/month cap. Tracks **actual API-equivalent spend**, not ccusage equiv. Resets 1st of month. Once depleted, likely rate-limited until reset. Monitor via `/status`.

**What triggers it:** Extended context (>200K tokens in a request), which bills all tokens at premium rates ($10/$37.50 Opus, $6/$22.50 Sonnet per Mtok). Context compaction is the primary way to avoid this.

**Feb 2026 observation:** $13.97 spent by Feb 25 (28%). Correlates with heavy Opus sessions — likely auto-compaction occasionally crossing 200K before kicking in. Not yet a constraint but worth monitoring on heavy weeks.

## Aliases

- `cu` — Quick current month daily view
- `cm` — Launch live monitor
