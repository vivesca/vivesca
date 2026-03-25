---
name: x-twitter
description: Read and search X/Twitter using the bird CLI. "check tweets", "search X"
user_invocable: false
github_url: https://github.com/steipete/bird
github_hash: d3dd4a0
---

# X/Twitter Access

Read tweets, search, and monitor accounts using the `bird` CLI (steipete/bird).

## Trigger

Use when:
- User asks "what did @X post?" or "check Karpathy's tweets"
- User wants to search X for a topic
- User asks for AI news from Twitter/X
- User wants to read a specific tweet or thread

## Prerequisites

- `bird` CLI installed (`/opt/homebrew/bin/bird`)
- Authenticated via Chrome cookies (`--cookie-source chrome`)
- Logged in as @zkMingLi

## Commands

All commands need `--cookie-source chrome` for auth.

### Read a Tweet
```bash
bird read <tweet-url-or-id> --cookie-source chrome
```

### Get User's Recent Tweets
```bash
bird user-tweets <handle> -n 10 --cookie-source chrome
```

### Search Tweets
```bash
bird search "query" -n 20 --cookie-source chrome
```

### Get Thread/Conversation
```bash
bird thread <tweet-url-or-id> --cookie-source chrome
```

### Check Mentions
```bash
bird mentions -n 10 --cookie-source chrome
```

### Get Bookmarks
```bash
bird bookmarks -n 20 --cookie-source chrome
```

### AI/Trending News
```bash
bird news --ai-only -n 10 --cookie-source chrome
```

### Home Timeline
```bash
bird home -n 20 --cookie-source chrome
```

### Check Auth
```bash
bird whoami --cookie-source chrome
```

## Common Handles for AI News

- `@karpathy` — Andrej Karpathy (AI research, LLMs)
- `@emollick` — Ethan Mollick (AI in business/education)
- `@swyx` — swyx (AI engineering, Smol AI)
- `@simonw` — Simon Willison (AI tools, LLMs)
- `@xlr8harder` — Jim Fan (NVIDIA, robotics)
- `@DrJimFan` — Jim Fan alt
- `@hardmaru` — David Ha (AI research)
- `@ilovetypescript` — Matt Pocock (AI + TypeScript)

## Output Format

bird returns structured output with:
- Tweet text (full, untruncated)
- Author handle and display name
- Timestamp
- Media URLs (images/videos)
- Quote tweets (nested)
- Tweet URL

## Cautions

- **Read-only recommended**: Posting can trigger bot detection
- **Rate limits**: Don't fetch too many tweets too quickly
- **Cookie expiry**: If auth fails, user needs to re-login to X in Chrome
- **SSH/tmux Keychain failure**: `bird --cookie-source chrome` fails over SSH/tmux because macOS Keychain requires GUI security context. Error: "Failed to read macOS Keychain (Chrome Safe Storage): exit 36". **Fallback**: Use Claude in Chrome `get_page_text` to extract tweet text directly from the page.

## Integration with AI News Skill

The `/ai-news` skill can use this for X account scanning in deep mode. Accounts are configured in `/Users/terry/skills/ai-news/sources.yaml`.

## Example Workflows

### Check what AI researchers are saying
```bash
bird user-tweets karpathy -n 5 --cookie-source chrome
bird user-tweets emollick -n 5 --cookie-source chrome
```

### Search for topic
```bash
bird search "Claude Code tips" -n 10 --cookie-source chrome
```

### Read a specific thread
```bash
bird thread https://x.com/karpathy/status/123456789 --cookie-source chrome
```
