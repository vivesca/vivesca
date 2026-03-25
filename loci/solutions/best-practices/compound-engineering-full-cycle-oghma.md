---
module: Workflow
date: 2026-02-05
problem_type: best_practice
component: delegation
symptoms:
  - "Multi-step feature development across planning, implementation, review"
  - "Need to ship clean code for public packages"
  - "Want to leverage delegation tiers effectively"
root_cause: mental_model_error
resolution_type: process_change
severity: medium
tags: [compound-engineering, delegation, codex, opencode, review-agents, pypi, full-cycle]
---

# Full Compound Engineering Cycle (Oghma Case Study)

## Context

Oghma v0.2.0 to v0.3.0 development showcased a complete compound engineering cycle: Plan -> Implement -> Review -> Cleanup -> Ship. This pattern is reusable for any non-trivial feature.

## The Full Cycle Pattern

```
1. PLAN (background)
   └─ Task agent runs Plan workflow while user does other things
   └─ Output: detailed implementation plan in docs/plans/

2. IMPLEMENT (Codex)
   └─ Delegate complex architectural work to Codex
   └─ Multiple files, migrations, new modules

3. REVIEW (parallel agents)
   └─ Run 2+ review agents simultaneously via Task tool
   └─ code-simplicity-reviewer + pattern-recognition-specialist
   └─ Catches issues before shipping

4. CLEANUP (Codex)
   └─ Single Codex invocation with all review findings
   └─ Batch fixes are more efficient than iterative

5. SHIP
   └─ Version bump, changelog, publish
   └─ For PyPI: trusted publishing via GitHub Actions
```

## Delegation Tiers in Practice

| Task Type | Delegate | Why |
|-----------|----------|-----|
| Config edits, git ops, simple fixes | OpenCode | Free, unlimited, good enough |
| Architecture, multi-file features | Codex | Smarter, handles complexity |
| Planning, review orchestration | Background Task | Doesn't block user |
| Judgment calls, vault access | Claude Code | Needs context + user interaction |

### When to escalate to Codex

- Feature spans 3+ files with interdependencies
- Migrations or schema changes involved
- Review findings require coordinated fixes
- OpenCode failed after 2-3 attempts

### When OpenCode suffices

- Single-file edits
- Git operations (commit, push, branch)
- MCP config syncing
- Running commands, tests

## Common Code Issues to Avoid

From review agents on Oghma v0.3.0 (~50 LOC removed):

### 1. Abstract Base Classes for Single Implementation

**Bad:**
```python
class BaseEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]: ...

class OpenAIEmbedder(BaseEmbedder):
    def embed(self, texts): ...
```

**Good:** Just have `OpenAIEmbedder`. Add ABC when you have 2+ implementations.

### 2. Duplicate Rate Limiting

**Bad:** Rate limiting in both `OpenAIEmbedder` and `HybridSearchEngine`

**Good:** Single rate limiter at the lowest layer (embedder). Caller doesn't need to know.

### 3. Scattered Fallback Logic

**Bad:** 5 different places checking `if embedding_failed: use_keyword_search()`

**Good:** One `search()` method that handles fallback internally.

### 4. Missing Factory Methods

**Bad:**
```python
config = yaml.load(...)
embedder = OpenAIEmbedder(
    api_key=config.get("api_key"),
    model=config.get("model", "text-embedding-3-small"),
    ...
)
```

**Good:**
```python
embedder = create_embedder(config)
# or
embed_config = EmbedConfig.from_dict(config)
```

### 5. Magic Numbers Without Constants

**Bad:** `if len(results) > 20:`

**Good:**
```python
MAX_RESULTS = 20
if len(results) > MAX_RESULTS:
```

### 6. Silent Exceptions

**Bad:**
```python
try:
    embed()
except Exception:
    pass  # Fall back to keyword
```

**Good:**
```python
try:
    embed()
except Exception as e:
    logger.warning(f"Embedding failed, using keyword search: {e}")
```

## PyPI Trusted Publishing Checklist

For publishing Python packages via GitHub Actions without API tokens:

### GitHub Actions Workflow

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]
  workflow_dispatch:  # Manual trigger

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi  # Required
    permissions:
      id-token: write  # Required for trusted publishing
      contents: read

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No api-token needed with trusted publishing
```

### PyPI Configuration

1. Go to PyPI project settings > Publishing
2. Add trusted publisher:
   - Owner: `your-github-username`
   - Repository: `repo-name`
   - Workflow: `publish.yml`
   - Environment: `pypi`

### GitHub Environment

1. Settings > Environments > New environment: `pypi`
2. Optional: Add protection rules (required reviewers)

### Common Issues

- **Missing `environment: pypi`** - Trusted publishing fails silently
- **Missing `id-token: write`** - Can't generate OIDC token
- **Wrong workflow name on PyPI** - Must match filename exactly
- **Branch protection** - Release events only trigger on default branch

## Review Agent Selection

For public packages, run at minimum:

| Agent | Catches |
|-------|---------|
| `code-simplicity-reviewer` | YAGNI violations, unnecessary abstractions |
| `pattern-recognition-specialist` | Anti-patterns, inconsistencies |

For security-sensitive code, add `security-sentinel`.

## Timing

Full cycle for Oghma v0.3.0 (vector search + PyPI):
- Plan: ~5 min (background)
- Implement: ~15 min (Codex)
- Review: ~3 min (parallel agents)
- Cleanup: ~8 min (Codex)
- Ship: ~5 min (Actions)

Total: ~35 min for a significant feature with clean code.

## Related

- [[Delegation Five Elements]] - Effective task prompts
- [[Compound Engineering Personal Setup]] - Initial setup
- Oghma repo: https://github.com/terrylinhaochen/oghma
