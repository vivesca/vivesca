# Waking Up API

## GraphQL Endpoint

```
POST https://api.wakingup.com/api/graphql
```

### Required Headers

```
accept: application/json
content-type: application/json
app-client: web
app-build: 951
app-version: 3.19.1
timezone: 28800
authorization: <JWT from STYXKEY-token cookie>
```

No `Bearer` prefix — just the raw JWT.

### Auth

Login via email verification (terry.li.hm@gmail.com). JWT is in the `STYXKEY-token` cookie after login. Token appears long-lived (issued 2020, still valid 2026).

### Key Queries

**Get ALL courses (1,831 items, single query, no pagination):**
```graphql
{ content { courses { title hash slug type audio { id url length } } } }
```

**Get single course by code (the short hash like CEAD4C):**
```graphql
{ course(code: "CEAD4C") { title hash slug type audio { id url length } } }
```

### Valid Fields

- **Course:** `title`, `hash`, `slug`, `type`, `description`, `subtitle`, `id` (numeric), `audio { ... }`, `image { ... }`
- **Audio:** `id` (UUID), `url` (direct m4a/mp3 URL), `length` (seconds)
- **Content:** `courses`, `tags`

### Notes

- Introspection disabled (`__schema` / `__type` blocked)
- Field discovery by trial and error — "Cannot query field" = doesn't exist
- App is Next.js App Router (RSC streaming) — no `__NEXT_DATA__`
- Audio UUIDs are NOT in the page DOM — only available via API or HLS URL
- `course_hash` (short codes like `CEAD4C`) ≠ `pack_hash` (like `PA4E72`)
- The `content` query with no args returns the global catalog, not just "current" content

### False Positive UUIDs

When scraping via browser interceptor, analytics/tracker UUIDs match the UUID regex pattern. Verify by checking HLS segments — real audio returns 200, false positives return 403:
```
curl -so /dev/null -w "%{http_code}" "https://d3amht9bmq5z6a.cloudfront.net/courses/audios/{UUID}/hls/segment_128_00000.ts"
```

## Reference

- Repo: `~/repos/waking-up-transcripts/` (private GitHub)
- Full catalog dump: `all_courses.json` (1,831 entries)
- Mapping: `audio_id_mapping.json`
