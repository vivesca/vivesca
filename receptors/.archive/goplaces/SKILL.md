---
name: goplaces
description: Query Google Places API for text search, place details, and reviews. Use when user asks about places, restaurants, businesses, or locations.
user_invocable: false
github_url: https://github.com/steipete/goplaces
---

# goplaces

Google Places API (New) CLI. Human output by default, `--json` for scripts.

## Prerequisites

- `goplaces` CLI installed: `brew install steipete/tap/goplaces`
- `GOOGLE_PLACES_API_KEY` environment variable set

## Commands

### Search Places

```bash
# Basic search
goplaces search "coffee" --limit 5

# Filter by rating and open status
goplaces search "coffee" --open-now --min-rating 4 --limit 5

# Location bias
goplaces search "pizza" --lat 40.8 --lng -73.9 --radius-m 3000

# Pagination
goplaces search "pizza" --page-token "NEXT_PAGE_TOKEN"
```

### Resolve Place Name

```bash
goplaces resolve "Soho, London" --limit 5
```

### Get Place Details

```bash
# Basic details
goplaces details <place_id>

# Include reviews
goplaces details <place_id> --reviews
```

### JSON Output

```bash
goplaces search "sushi" --json
```

## Notes

- `--no-color` or `NO_COLOR=1` disables ANSI color
- Price levels: 0..4 (free to very expensive)
- Type filter sends only the first `--type` value (API limitation)
