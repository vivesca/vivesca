# Thalamus Domain-Agnostic Refactor

**Goal:** Extract all domain-specific content from thalamus into a `DomainConfig` object. Pipeline engine stays untouched. Multiple domains become just config.

## Core Design

A `DomainConfig` dataclass carries all domain-specific content:

```python
@dataclass
class DomainConfig:
    id: str                        # "ai" | "thinkers"
    display_name: str              # "AI Landscape" | "Thinkers"
    articles_dir: Path             # source articles
    landscape_dir: Path            # output vault dir
    index_path: Path               # top-level index note
    db_path: Path                  # DuckDB for analytics/traces
    git_commit_prefix: str         # "ai-landscape" | "thinkers"
    extraction_lens: str           # persona + dimensions
    extraction_json_spec: str      # JSON field list for prompt
    gap_focus_areas: list[str]     # bullets for gap analysis
    quality_gate_criteria: list[str]
    daily_summary_persona: str
    synthesis_templates: dict[str, str]  # period → template
    garden_topic_filter: str
    garden_publishing_enabled: bool
    card_fields_to_render: list[str]
    primary_so_what_field: str     # "banking_so_what" | "decision_lens"
    citation_check_enabled: bool
```

## New File Structure

```
src/thalamus/domain/
    __init__.py     # exports DomainConfig, load_domain, DOMAINS
    config.py       # DomainConfig dataclass
    ai.py           # current AI/banking content → AI_DOMAIN
    thinkers.py     # new: decision quality frame → THINKERS_DOMAIN
```

## What's Domain-Specific (Audit)

| Module | Domain-coupled content |
|--------|----------------------|
| prompts.py | CHECKLIST_LENS, all 7 build_* functions have hardcoded banking persona, Capco/HSBC framing, JSON schema fields |
| extract.py | REGULATORY_SIGNAL_WORDS, flag_inferred_regulations(), format_extractions_as_text() renders banking fields |
| write.py | Card YAML frontmatter, snapshot titles ("AI Landscape"), inline card rendering |
| analytics.py | DuckDB schema columns (governance_action, consulting_use), DEFAULT_DB path |
| pipeline.py | Git commit prefix, DuckDB path hardcoded |
| garden.py | Topic filter mentions "AI, banking, consulting" |

## Thinkers Domain Design

**Extraction lens:** "You are extracting insights for a generalist reader building a personal decision-making framework. Focus on: mental models, decision heuristics, cognitive biases, contrarian positions, applicability to career/strategy/investing/life design."

**Sources:** Naval, Sivers, Morgan Housel, Shane Parrish, Annie Duke, Rolf Dobelli

**Extraction fields** (replacing banking fields):
- `mental_model`: core model or heuristic
- `decision_lens`: how this changes a decision
- `contrarian`: what conventional wisdom this challenges
- `applicability`: domains where this applies
- `quotable`: most memorable line

**Gap focus areas:**
- New essays/books from target thinkers
- Counterarguments to ideas in corpus
- Adjacent thinkers in complexity, systems, behavioural economics
- Evidence from psychology/neuroscience
- Real-world case studies testing a heuristic

**Content source (v1):** Manually seeded `~/.cache/thinkers-articles/`. Proper feed integration deferred.

## Implementation Steps (13)

1. Create `domain/config.py` — DomainConfig dataclass
2. Create `domain/ai.py` — move all hardcoded content from prompts.py
3. Create `domain/thinkers.py` — new domain config
4. Create `domain/__init__.py` — registry + load_domain()
5. Refactor `prompts.py` — all build_* accept DomainConfig
6. Refactor `extract.py` — pass domain, gate citation check
7. Refactor `gaps.py` + `synthesise.py` — pass domain through
8. Refactor `write.py` — parameterise titles, card fields
9. Refactor `analytics.py` — add domain column, use domain.db_path
10. Refactor `pipeline.py` — wire DomainConfig through everything
11. Refactor `cli.py` — add `--domain` flag (default: "ai")
12. Update `smoke.py` — accept domain
13. Update `garden.py` — gate on domain.garden_publishing_enabled

**Dependency chain:** Steps 1-4 first, then 5-9 in parallel, then 10-13.

## Backwards Compatibility

- `--domain ai` is default → LaunchAgent unchanged
- Existing DuckDB preserved (ai.py points to same path)
- `domain VARCHAR DEFAULT 'ai'` column added to tables
- 83 existing tests pass by injecting AI_DOMAIN

## Deferred (v2)

- TOML/YAML domain configs (Python files are simpler for 2 domains)
- Auto-discovery of domains from directory
- Per-domain lustro feed config
- Shared base card schema + domain extensions
