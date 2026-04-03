---
name: linkedin-research
description: >
  Research OTHER people on LinkedIn — profile lookup, team mapping, org research.
  NOT for managing your own profile (use linkedin-profile skill for that).
  Triggers: "look up X on LinkedIn", "find Y's profile", "who works at Z", "org chart".
user_invocable: false
---

# LinkedIn People Research

## When to Consult

- Finding someone's LinkedIn profile
- Extracting profile details (experience, education, skills)
- Mapping team/org structure from LinkedIn

## CLI First

For bulk or structured research (multiple profiles, org traversal), use **`nexum`** instead of manual agent-browser:

```bash
nexum search "AIA Hong Kong" "data science AI"   # find people
nexum profile <url>                               # extract one profile
nexum traverse <url> --depth 1                   # BFS network graph
```

Requires LinkedIn auth first: `porta inject --browser chrome --domain linkedin.com`
See `nexum` skill for full reference.

## Manual Search Strategy (Waterfall)

For one-off lookups when nexum isn't needed:

1. **Name + company + site:linkedin.com** — default first attempt
2. **Role/title + company + site:linkedin.com** — when name search fails (privacy-gated names show as "Simon E.")
3. **`pplx search`** — better platform indexing than WebSearch
4. **`agent-browser` extraction** — when URL is known but content needed

Search engines index the *display name*, not the vanity URL slug. If someone's profile shows "Simon E." to non-connections, no amount of name variation will find them. Pivot to title/role immediately.

**Example pivot:**
```
# Fails — privacy-gated display name
"Simon Eltringham" HSBC site:linkedin.com

# Works — headline text is rarely abbreviated
HSBC "Director" "Responsible AI" "Risk Solutions" site:linkedin.com
```

## Profile Extraction

- `WebFetch` → HTTP 999 (always blocked by LinkedIn)
- **LinkedIn requires `--headed` mode always.** Headless is blocked even with valid cookies/profile. `porta inject` does NOT work — LinkedIn fingerprints the browser, not just cookies.
- `agent-browser --headed open <url>` → `snapshot` → grep for data
- Scroll + re-snapshot for experience/education sections below the fold
- Key fields: headline, location, current company, experience list, education

### Auto-Login Pattern (1Password)

If cookies are expired, automate login instead of waiting for user:
```bash
agent-browser close
agent-browser --headed open "https://www.linkedin.com/login"
# Get creds from 1Password (two LinkedIn items — use ID)
op item get tlahsscuctajs753gkddj6re4i --vault Agents --fields username --reveal
op item get tlahsscuctajs753gkddj6re4i --vault Agents --fields password --reveal
agent-browser fill "#username" "<email>"
agent-browser fill "#password" '<password>'
agent-browser click "[type=submit]"
# Verify: get url should show /feed/
```
Session persists within the same headed session. Closing and reopening headed also works. Headless never works.

### My Network Search

To find all 1st connections at a company:
```bash
agent-browser --headed open "https://www.linkedin.com/search/results/people/?keywords=<Company>&network=%5B%22F%22%5D&origin=FACETED_SEARCH"
agent-browser snapshot 2>&1 | grep "• 1st"
```
Don't use `currentCompany` filter with company IDs — LinkedIn's IDs are hard to guess and often wrong.

## Org Chart Mapping

- Search multiple team members → cross-reference titles/dates → infer hierarchy
- Title signals: "Group" > "Director" > "Manager"; "Lead" implies team ownership
- Mark unverified reporting lines with `[?]`
- Save to vault with ASCII chart format (established pattern in Capco notes)

### Network Graph Traversal

Keyword search misses people whose titles don't reflect their work (common in consulting — "Principal Consultant" managing an AI engagement). Mine the sidebar from known profiles instead:

1. Open a known profile via `agent-browser` (already doing this for extraction)
2. The snapshot includes **"People also viewed"** and **"People you may know from [Company]"** sections — extract names and URLs
3. Follow those links to discover colleagues keyword search would miss
4. Repeat from the most relevant new profiles for 1-2 hops

This data is free — it's already in the snapshot. Don't discard it.

**Limitation:** Sidebar results are LinkedIn's algorithm, not a complete org chart. One message to an insider ("who else should I know?") is still faster for a complete team list.

## Gotchas

- LinkedIn abbreviates surnames for non-connections ("Simon E.")
- **Initials-only display names:** Some users set their name to initials (e.g., "H Y LI" instead of "Ho Yin Li"). Google and WebSearch won't match full-name queries to these profiles. If external search draws a blank for someone you know exists, try searching initials on LinkedIn directly via agent-browser before concluding the account is deactivated.
- The existing `agoras` skill is for **content** (posts/comments) — this skill is for **research**
- Profile data from snapshots may be incomplete — check "Show all X experiences" expand links
- **Never run two `agent-browser open` calls in parallel for LinkedIn** — they share one browser instance; the second open overwrites the first. Always run sequentially.
- **`agent-browser get text body` returns raw 370KB+ HTML** — useless for LinkedIn. Always use `snapshot` + grep instead.
- **`/details/experience/` URL doesn't work** — redirects to generic LinkedIn page. Stick to the main profile URL and use snapshot to extract experience.
- **`--profile` flag ignored if daemon already running** — warning appears but it still works if the existing daemon is already authenticated. Not a blocker.
- **`recent-activity/all/` works** for reading someone's public posts — useful for gauging communication style and recent focus areas before a meeting.
