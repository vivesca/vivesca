---
name: digest
description: Monthly content digest — extract insights from YouTube channels and other sources. "digest", "monthly digest"
user_invocable: true
---

# Content Digest

Monthly insight extraction from YouTube channels (and extensible to other source types). Fetches recent episodes, extracts transcripts, runs LLM insight extraction, and writes digest notes to the vault.

## Trigger

Use when:
- User says "digest", "monthly digest", "run digest"
- User asks "what has Huberman/Rhonda Patrick covered recently?"
- User asks to catch up on a content creator's recent output
- First of the month for a routine monthly digest

## Prerequisites

- `OPENROUTER_API_KEY` set in environment (for LLM insight extraction)
- `uv` installed (for running Python scripts with deps)
- `deno` installed (for yt-dlp YouTube support)

## Commands

### Run full digest (all sources, last 30 days)

```bash
uv run ~/skills/digest/digest.py
```

### Digest a specific source

```bash
uv run ~/skills/digest/digest.py huberman
uv run ~/skills/digest/digest.py rhonda
```

### Custom lookback period

```bash
uv run ~/skills/digest/digest.py --days 60
```

### Dry run (list episodes without processing)

```bash
uv run ~/skills/digest/digest.py --dry-run
```

### Choose model

```bash
# Default: Gemini Flash (cheap, 1M context)
uv run ~/skills/digest/digest.py --model google/gemini-2.0-flash-001

# Higher quality
uv run ~/skills/digest/digest.py --model anthropic/claude-sonnet-4
```

## Sources

Configured in `~/skills/digest/sources.yaml`. Currently:
- **Huberman Lab** (@hubermanlab) — neuroscience, health protocols
- **FoundMyFitness** (@FoundMyFitness) — Dr. Rhonda Patrick, longevity, nutrition

To add a source, edit `sources.yaml` with:
```yaml
- name: Channel Name
  type: youtube
  handle: "@ChannelHandle"
  vault_path: Category/Name
```

## Output

Digest notes are written to `~/notes/{vault_path}/{Channel Name} - {YYYY-MM} Digest.md` with:
- Episode-by-episode breakdown
- Key insights with evidence quality ratings
- Specific protocols (dose, timing, frequency)
- Contrarian/surprising findings
- Notable quotes

## Tips

- Run `--dry-run` first to see what episodes would be processed
- Full Huberman episodes (~2.5 hrs) produce ~30K word transcripts — Gemini Flash handles this fine
- "Essentials" episodes are repackaged clips; less novel but still useful for key summaries
- Cost: ~$0.01-0.02 per episode with Gemini Flash
- For a single video, use `/summarize` instead — this skill is for batch channel digests
