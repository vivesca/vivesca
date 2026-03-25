---
name: vault-search
description: Deep search the Obsidian vault with term expansion. Use when simple grep misses relevant content or when searching broad topics.
user_invocable: false
---

# Vault Search

Comprehensive vault search that expands terms and checks multiple locations.

## When to Use

- Simple grep returned few/no results but you suspect content exists
- Searching a broad topic (e.g., "interview", "AML", "strategy")
- Need to find all related notes, not just exact matches

## Search Strategy

### 1. Check the Index First

Read `[[Vault Index]]` to identify which section/hub notes are relevant.

### 2. Expand Search Terms

| Topic | Also Search |
|-------|-------------|
| interview | prep, Q&A, story, reframe, behavioral |
| job | hunting, pipeline, applied, role, recruiter |
| AML | alert, compliance, FCC, transaction monitoring |
| chatbot | agent-assist, call centre, web chat |
| negotiation | exit, salary, comp, offer, package |
| AI | agentic, GenAI, LLM, model, ML |
| story | STAR, example, project, evidence |

### 3. Search Locations

```bash
# Top-level notes
grep -il "term" ~/notes/*.md

# Key subdirectories
grep -ril "term" ~/notes/Articles/
grep -ril "term" ~/notes/memory/
grep -ril "term" ~/notes/patterns/
```

### 4. Check Hub Notes

For any topic, check its hub notes (listed in Vault Index) which link to related content.

| Topic | Hub Notes |
|-------|-----------|
| Job hunting | Active Pipeline, Job Hunting, Job Hunting - Applied Archive |
| Interviews | Interview Q&A Bank, Core Story Bank, Interview Reframes & Scripts |
| Stories | Core Story Bank, The AML Alert Prioritisation Story, The call centre story |
| Strategy | Exit Negotiation Strategy, Compensation Floor and Framing |
| AI concepts | Agentic AI, Agent Architecture and Context |

### 5. Follow Links

After finding initial matches, check their `[[wikilinks]]` for related content.

## Output Format

```markdown
## Search: [topic]

### Direct Matches
- [[Note 1]] — brief description
- [[Note 2]] — brief description

### Related (via hub notes)
- [[Note 3]] — found via [[Hub Note]]

### Subdirectories
- Articles/relevant-article.md
- memory/relevant-memory.md
```

## Anti-Patterns

- **Don't grep the entire vault recursively** — too slow, too much noise
- **Don't stop at first match** — related content often scattered
- **Don't ignore subdirectories** — Articles/, memory/, patterns/ have useful content

## Related Skills

- `vault-pathfinding` — Standard file paths and conventions
- `skills-design` — How skills reference vault content
