---
name: nexum
description: LinkedIn org research CLI — search people, extract profiles, traverse network graph. Use when researching org structures or mapping teams at scale. NOT for single profile lookups (use linkedin-research) or managing your own profile (use linkedin-profile).
---

# nexum — LinkedIn Org Research CLI

Source: `~/code/nexum/` | Binary: `~/.cargo/bin/nexum`

## Commands

```bash
# Search for people by keyword
nexum search "AIA Hong Kong" "data science AI"

# Extract a profile (name, headline, experience, sidebar)
nexum profile https://www.linkedin.com/in/claudio-caula-8ab319

# Traverse network graph from seed profile
nexum traverse https://www.linkedin.com/in/claudio-caula-8ab319
nexum traverse https://www.linkedin.com/in/claudio-caula-8ab319 --depth 2
```

## Mechanism

1. Shells to `agent-browser open <url>` → `wait` → `snapshot`
2. Pipes snapshot to `claude --dangerously-skip-permissions` headless with extraction prompt
3. `traverse` does BFS via "People also viewed" sidebar URLs up to `--depth N`

## Auth Requirement (Critical)

LinkedIn blocks unauthenticated sessions. Before running any nexum command:

```bash
# In the same tmux window — run once per window
porta inject --browser chrome --domain linkedin.com

# Or set profile env var for persistent cookies
export AGENT_BROWSER_PROFILE=~/.agent-browser-profile-$WINDOW
```

Without auth, the snapshot will be a login wall — Claude extracts nothing useful.

## Gotchas

- **agent-browser commands must be sequential** — multiple calls in a single Bash command cause "Resource temporarily unavailable" daemon errors. nexum calls them sequentially via `std::process::Command`.
- **Claude headless prefix** — uses `env CLAUDECODE= claude --dangerously-skip-permissions` to bypass the nested-claude guard. If this fails, check that `claude` is on PATH.
- **`wait 4000`** not `wait --load networkidle` — LinkedIn networkidle times out. Fixed ms wait is used instead.
- **traverse sidebar URLs** — extracted via simple regex `https://www.linkedin.com/in/` scan on Claude's JSON output. If Claude outputs relative URLs or omits `/in/` prefix, depth 2+ will miss profiles. Inspect output if traverse seems shallow.
- **Search URL encoding** — spaces → `%20`, quotes → `%22`. Only basic chars handled; non-ASCII in keywords will break the URL. Use ASCII keywords only.

## Output Format

`search`: One line per person — `Name | Headline | Location | Profile URL`

`profile`: Structured text block — NAME, HEADLINE, LOCATION, ABOUT, EXPERIENCE list, EDUCATION list, SIDEBAR list

`traverse`: Per-profile JSON blocks, one per profile visited, prefixed with `--- <url> ---`

## Rebuild

```bash
cd ~/code/nexum && cargo install --path .
```
