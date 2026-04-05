---
name: evolvo
description: Scan Claude Code session JSONL to extract wrap outputs and compute quality stats. Use when reviewing session output quality for skill-review. "wrap quality", "session review", "evolvo"
triggers: [wrap quality, session review, skill-review step 5, multi-wrap, evolvo]
---

# evolvo

Rust CLI that reads `~/.claude/projects/-home-terry-germline/*.jsonl`, extracts `─── Wrap` blocks, and produces stats + a spread sample for quality review.

## Install

Binary at `~/bin/evolvo`.

## Usage

```bash
evolvo                    # 30-day window, 15-sample spread
evolvo --stats-only       # stats block only
evolvo --days 90          # extend window to 90 days
evolvo --sample 5         # smaller sample
```

## Output

```
Sessions scanned:     5161
Total wrap outputs:    340
Unique sessions:       252
Multi-wrap sessions:    57 (23%)
Date range: 2026-02-27 – 2026-03-07

=== 2026-03-03 [2d79de5d] ===
─── Wrap ──────────
...
```

## Quality rubric (use during skill-review Step 5)

| Signal | Healthy | Flag if |
|--------|---------|---------|
| Narrative specificity | Names tools, decisions, outcomes | Generic ("light session", "routine") |
| Multi-wrap rate | <15% | >25% — skip gate not firing |
| Pre-wrap block | ⚠/✓ mix | Always "all clear" |
| Step 4 boilerplate | Silent skip or specific | "Nothing new" repeated in sample |

## Gotchas

- Session IDs are first 8 chars of the JSONL filename stem.
- Deduplication keeps one wrap per session (latest mtime) in the sample spread.
