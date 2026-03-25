---
title: Claude Code Rate Limit History Extraction
category: tooling
tags: [claude-code, rate-limits, usage-tracking, ccusage]
symptoms:
  - Need to know when weekly limit resets
  - Want to calibrate actual weekly cap
  - Hitting limits without warning
  - Usage tools don't show limit history
module: claude-code
date: 2026-02-02
---

# Claude Code Rate Limit History Extraction

## Problem

Claude Code Max plan has undisclosed weekly limits. Users hit limits without knowing:
- What the actual cap is (Anthropic doesn't publish it)
- When they previously hit limits
- Their personal reset time

Existing tools (ccusage, claude-monitor) show token usage but not limit events.

## Discovery

Claude Code stores rate limit events in local conversation logs at:
```
~/.claude/projects/-Users-*/*.jsonl
```

Each rate limit event is logged with:
```json
{
  "timestamp": "2026-01-30T23:28:30.573Z",
  "message": {
    "content": [{"type": "text", "text": "You've hit your limit · resets 6pm (Asia/Hong_Kong)"}]
  },
  "error": "rate_limit",
  "isApiErrorMessage": true
}
```

## Solution

### Quick extraction (bash)

```bash
grep -rh '"text":"You'\''ve hit your limit' ~/.claude/projects/-Users-*/*.jsonl 2>/dev/null | \
  grep -o '"timestamp":"[^"]*"\|"text":"[^"]*"' | paste - - | sort -u | tail -10
```

### Contributed to ccusage

PR submitted: https://github.com/ryoppippi/ccusage/pull/838

New command: `ccusage limits`
- Parses all JSONL files for rate limit events
- Infers Weekly vs 5-hour limit type
- Supports `--limit N`, `--since YYYYMMDD`, `--json`

## Calibration Result

Using actual limit hits:
- **Jan 23**: Hit limit, reset "Jan 24 at 6pm" → Weekly limit
- **Jan 30**: Hit limit, reset "6pm" (Saturday) → Weekly limit

Calculated actual cap: **~$800 equiv** (vs community estimate of $600)

## Key Learnings

1. **Local logs contain data no API exposes** — Always check what's stored locally
2. **Calibrate from actual events** — Real limit hits beat Reddit estimates
3. **Reset times are personalized** — Based on when you started using, not a global time
4. **Two limit layers exist**:
   - 5-minute rolling window (~220K tokens for Max20)
   - Weekly cap (~$800 equiv, resets Saturday 6pm for this user)

## Prevention

- Track usage with `ccusage daily` or `cu` alias
- Monitor with calibrated thresholds:
  - ✅ Safe: <$480 (60%)
  - ⚠️ Caution: $480-600 (75%)
  - 🟠 Warning: $600-720 (90%)
  - 🔴 Danger: >$720

## Related

- `/usage` skill — Incorporates this discovery
- Issue #146 on ccusage — Reset time detection discussion
- PR #838 on ccusage — `limits` command contribution
