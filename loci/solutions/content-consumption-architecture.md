# Content Consumption Architecture

Personal information architecture patterns, discovered through three consilium sessions (Feb 2026).

## Routing Rule

When adding a new content source, ask: **"scan or study?"**

- **Notification value** (know it exists) → `/lustro` scanner (daily, free)
- **Deep processing value** (absorb and apply) → `/digest` (monthly, LLM-assisted)
- **Both** → add to both. A source in both systems is not a conflict — it's intentional.

Example: Dwarkesh blog posts in `/lustro` for "new episode dropped"; Dwarkesh transcripts in `/digest` for deep synthesis.

## Key Patterns

### Notification vs Consumption

Distinguish between *knowing something exists* and *processing its content*. The scanner's job is awareness; the processor's job is understanding. Conflating these leads to either delayed awareness (moving scan-worthy sources to batch processing) or shallow understanding (trying to deeply process everything at scan time).

### Architecture Seduction

When a council identifies a correct conceptual distinction (e.g., processing mode vs. topic), there is a strong gravitational pull to refactor existing working systems to reflect that distinction structurally. For personal tooling with small scale (single user, <100 sources), the correct response is usually: adopt the distinction as a *mental model for future decisions* while making *minimal tactical fixes* to current systems. Threshold for refactoring: "Am I unable to do something I need to do?" not "Is the current organization theoretically suboptimal?"

### Artifact-Then-Validate

When proposing a new AI-mediated workflow, don't prescribe manual validation sprints before building. Instead: (1) identify the minimum infrastructure prerequisite, (2) build the smallest concrete artifact that tests the paradigm, (3) spot-check that artifact against primary sources. Critiquing a real output is faster and more revealing than simulating one manually. Reserve "measure first" for team/enterprise contexts where build costs are high.

## AI Thematic Digest

Monthly evidence-grounded synthesis of AI developments, purpose-built for banking AI advisory.

**Architecture:**
- Cron (`ai-news-daily.py`) archives Tier 1 article full text to `~/.cache/lustro-articles/` via trafilatura
- `ai-digest.py` (uv script) runs monthly: loads cached articles + news log, identifies 5-8 thematic clusters, produces per-theme evidence briefs via Gemini Flash
- Output: `~/epigenome/chromatin/AI & Tech/YYYY-MM AI Thematic Digest.md`

**Evidence brief format:**
- Claims → primary sources with quotes
- Derivative echo count (how many sources just reposted the same thing)
- Evidence quality rating (primary research / industry report / expert opinion / derivative)
- Open questions
- Banking/Capco implications

Not narrative essays — those go stale. Evidence briefs stay useful as reference.

## System Map

| System | Purpose | Cadence | LLM Cost | Output |
|---|---|---|---|---|
| `/lustro` | Professional awareness | Daily cron (free) + on-demand synthesis | Zero (cron) / session (synthesis) | Ephemeral log + article cache |
| `/digest` | Deep learning | Monthly batch | ~$0.01-0.02/episode | Persistent vault notes |
| `ai-digest.py` | Professional reference | Monthly batch | ~$0.05-0.15/month | Evidence briefs in vault |

## Subscription Evaluation Gotchas

### Substack/Beehiiv RSS often bypasses paywalls

Newsletter platforms gate content on the *web* but expose full text in the *RSS feed*. Verified examples:
- **Ben's Bites** (`bensbites.com/feed`) — full newsletter content despite paid tier
- **Latent Space** (`api.substack.com/feed/podcast/1084089.rss`) — full transcripts + show notes

Before paying for a newsletter subscription, test the RSS feed first. If the cron already gets full content via RSS, the paid tier's value is community/archive access only — not the content itself.

### "Paid perk" may already be free elsewhere

Latent Space advertises "weekday full AINews" as a paid benefit ($80/yr), but the same content is freely available at news.smol.ai (swyx's public site). Cross-reference before subscribing.

## Source: Three consilium sessions

- [LLM Council - Unified Digest - 2026-02-21](~/epigenome/chromatin/Councils/LLM%20Council%20-%20Unified%20Digest%20-%202026-02-21.md) — Option B won (keep separate)
- [LLM Council - Content System Axis - 2026-02-21](~/epigenome/chromatin/Councils/LLM%20Council%20-%20Content%20System%20Axis%20-%202026-02-21.md) — Processing mode vs topic
- [LLM Council - AI Mediated Reading - 2026-02-21](~/epigenome/chromatin/Councils/LLM%20Council%20-%20AI%20Mediated%20Reading%20-%202026-02-21.md) — "Claude reads everything" paradigm
