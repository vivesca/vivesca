---
name: waking-up
description: Waking Up meditation transcripts — catalog, transcribe, search, enrich. "waking up", "wu", "transcribe meditation"
user_invocable: true
---

# Waking Up Transcripts

Manage the Waking Up meditation transcript pipeline via the `wu` CLI (`~/code/wu/`).

## Trigger

Use when:
- User says "waking up", "wu", "transcribe", "meditation transcripts"
- Any question about the Waking Up catalog, audio IDs, or transcript status

## Project Status

**Complete.** 1,314 transcripts across 54 teachers, 107 packs, 67 traditions. All enriched with metadata (tradition, summary, key_concepts). Organized into pack folders with MOC.

93 transcripts still have `teacher: "Unknown"` — these are multi-teacher Conversations where teacher can't be determined from pack data alone.

## Quick Commands

```bash
# Catalog management
wu refresh                    # fetch latest catalog via GraphQL API (needs JWT)
wu refresh --token <jwt>      # one-off with explicit token
wu catalog                    # show catalog stats (1,831 courses, types)
wu catalog <file.json>        # import new courses dump (legacy browser extraction)

# Discovery
wu new                        # show untranscribed content grouped by type
wu new --type talk            # filter to specific type
wu new --json-out             # output as batch-ready JSON
wu search "Alan Watts"        # search by title/slug
wu search "zen" --type talk   # filter by content type
wu info <audio_id>            # show metadata + vault status for a UUID

# Transcription
wu transcribe <audio_id>                          # auto-resolve title/teacher/pack
wu transcribe <id> "Title" --teacher "Name"       # explicit metadata
wu transcribe <id> --enrich                       # transcribe + add LLM metadata
wu batch <file.json> --model gemini-3-flash -c 3  # batch run
wu enrich                     # add tradition/summary/key_concepts via Gemini
wu digest                     # generate per-transcript digests (core argument, quotes, takeaway)
wu digest --dry-run           # preview without modifying files
wu digest --concurrency 5     # parallel processing
wu digest --force             # regenerate existing digests
wu digest --limit 10          # process only N files

# Guides & synthesis
wu guide --teacher "Alan Watts"    # single teacher guide
wu guide --teachers                # all teachers with ≥5 transcripts
wu guide --tradition "Zen"         # single tradition guide
wu guide --traditions              # all canonical tradition groups
wu themes                          # discover cross-cutting themes
wu themes --dry-run                # preview themes without generating notes
wu practice                        # generate organized practice guide

# Maintenance
wu status <file.json>         # show batch progress
wu rename --dry-run           # preview placeholder renames
wu rename                     # apply renames
wu review                     # list transcripts most likely to contain errors
wu estimate <file.json>       # estimate transcription cost
```

## Key Paths

- **Repo:** `~/code/wu/`
- **Vault transcripts:** `~/notes/Waking Up/` (107 pack folders + Uncategorized)
- **MOC:** `~/notes/Waking Up/Waking Up MOC.md`
- **Audio cache:** `~/.cache/waking-up-audio/`
- **Catalog data:** `data/all_courses.json`, `data/audio_id_mapping.json`
- **Pack data:** `data/packs.json` (129 packs), `data/pack_courses.json` (scraped pack→course mapping)
- **Progress note:** `~/notes/Waking Up Transcription Progress.md`

## Transcription Backends

| Model | CLI flag | Notes |
|-------|----------|-------|
| Gemini 3 Flash (direct API) | `gemini-3-flash` (default) | Best quality, GOOGLE_API_KEY, File API upload |
| Gemini 2.5 Flash | `gemini-2.5-flash` | Fallback when 3 Flash returns empty `parts` |
| OpenRouter | `or:gemini-3-flash` | Bypasses RECITATION filter. Auto-splits >20MB into 15-min chunks |
| Deepgram Nova-3 | `nova-3` | Original backend, DEEPGRAM_API_KEY |

**Model selection:** Use `gemini-3-flash` for most content. Use `or:gemini-3-flash` for copyright-adjacent content (meditation scripts, poetry, sacred texts) that triggers Gemini's RECITATION filter.

## Audio Download

Two CDN paths:
- **HLS segments:** `d3amht9bmq5z6a.cloudfront.net/courses/audios/{UUID}/hls/` — most content
- **Direct M4A:** `d2uk1wgjryl0y1.cloudfront.net/show_episodes/` — Episode content (Work in Progress Show)

The CLI tries direct URL first (from `audio.url` in catalog), falls back to HLS segment discovery.

## Metadata Tools (one-off scripts in repo root)

- `scrape_packs.py` — Scrapes pack→course mapping from WU web app via agent-browser. Requires active browser session with auth cookie.
- `update_metadata.py` — Updates teacher/pack frontmatter in vault transcripts and moves files into pack folders. Supports `--dry-run`.

## Error Handling

- **RECITATION block:** Switch to `or:gemini-3-flash` (OpenRouter bypasses Google's copyright filter)
- **No segments found:** Try direct URL download — Episode content uses different CDN
- **502/524 on OpenRouter:** File too large for base64 — auto split-and-concatenate handles this for >20MB
- **Empty `parts` from Gemini:** Model-level issue, not quota. Fallback to `gemini-2.5-flash`
- **ffmpeg not found:** `brew install ffmpeg`

## Technical Notes

- **GraphQL endpoint:** `https://api.wakingup.com/api/graphql` — used by `wu refresh`
- **Auth:** JWT stored in Keychain (`waking-up-jwt`), env var (`WAKING_UP_JWT`), or `--token` flag. No Bearer prefix.
- **Store JWT:** `security add-generic-password -s waking-up-jwt -a terry -w '<jwt>'`
- **Required headers:** `app-client: web`, `app-build: 951`, `app-version: 3.19.1`, `timezone: 28800`
- **Content query returns ALL courses** — no pagination needed
- **Introspection disabled** — field discovery by trial/error
- **Valid Course fields:** `title`, `hash`, `slug`, `type`, `description`, `subtitle`, `id`, `audio { id url length }`, `image { ... }`
- **Pack→course relationships not in GraphQL** — must scrape from web app via `scrape_packs.py`
- **Auto split-and-concatenate:** Built into CLI. `or:*` models auto-split >20MB files into 15-min ffmpeg chunks. No re-encoding.
- `maxOutputTokens: 65536` required — Gemini defaults to ~8192 without it

Full gotchas: `~/docs/solutions/stt-api-gotchas.md`
Full progress: `~/notes/Waking Up Transcription Progress.md`

## Distillation System

**Complete (Feb 2026).** Four layers, all idempotent with `--force` to regenerate:

| Layer | Command | Output | Count |
|-------|---------|--------|-------|
| Digests | `wu digest` | `## Digest` sections in vault files | 1,314 |
| Guides | `wu guide --teachers/--traditions` | `Guides/` folder | 60 (47 teacher + 13 tradition) |
| Themes | `wu themes` | `Themes/` folder | 15 emergent themes |
| Practice | `wu practice` | `Practice Guide.md` | 1 (from 637 sources) |

- Layers 2-4 read digests (Layer 1 output), not raw transcripts
- LLM JSON parsing: always strip trailing commas before `json.loads()` — `re.sub(r",\s*([}\]])", r"\1", text)`
- Large teachers (>50 digests): two-pass chunking (summarize chunks, then synthesize)
- Tradition dedup: 67 raw labels → 12 canonical groups via hardcoded `TRADITION_GROUPS` dict
- Full pattern: `~/docs/solutions/cascading-llm-summarization.md`
