# feat: LLM Council Improvements

## Enhancement Summary

**Deepened on:** 2026-01-20
**Research agents used:** 7 (structured-output, routing, evaluation, python-reviewer, architecture-strategist, simplicity-reviewer, performance-oracle)

### Key Findings

1. **Critical Performance Win:** Parallelize blind phase - reduces 50-100s to 15-25s
2. **Simplification Opportunity:** Current regex consensus detection works; structured output may be over-engineering
3. **Domain Weighting Concern:** Static weights are guesses - equal voices may be the feature, not the bug
4. **Storage Alternative:** JSONL file (5 LOC) vs SQLite (100+ LOC) for a personal CLI tool

### Research Consensus

The research agents produced a **split verdict**:
- **Architecture/Python reviewers:** Proceed with all phases, but with better structure
- **Simplicity reviewer:** Skip all three phases - current tool already works well
- **Performance reviewer:** Prioritize blind phase parallelization over new features

---

## Overview

Enhance the LLM Council skill with three major improvements identified during the council's self-review:

1. **Domain-Aware Weighting** - Models aren't equally capable across question types; route/weight based on domain
2. **Evaluation Harness** - A/B testing vs baselines to validate council provides value over single models
3. **Structured Output Schema** - JSON vote schema to prevent consensus spoofing and enable reliable aggregation

## Problem Statement

The current council implementation treats all 5 models equally regardless of question domain. This misses optimization opportunities:

- Claude excels at code; Gemini at multimodal; GPT at structured reasoning
- No way to prove council beats a single strong model (justifying 5x cost)
- Consensus detection via regex is spoofable and unreliable
- No historical tracking to learn which models perform best per domain

---

## Research Insights: Critical Performance Issue (Pre-Requisite)

### Parallelize Blind Phase First

**Current problem:** Blind phase queries 5 models sequentially (50-100s).
**Solution:** Convert to async parallel execution (15-25s).

```python
import asyncio
import httpx

async def run_blind_phase_parallel(question: str, council_config: list, api_key: str) -> list:
    """Run all blind phase queries in parallel."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120.0,
    ) as client:
        tasks = [
            query_model_async(client, model, messages)
            for name, model, _ in council_config
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

**Impact:** 50% latency reduction. Should be implemented before any new features.

---

## Proposed Solution

### Phase 1: Structured Output Schema (Foundation)

Add Pydantic schemas for council responses to enable reliable parsing and aggregation.

**Schema Definition:**
```python
# council_schema.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal

class ClaimSketch(BaseModel):
    """Blind phase output."""
    model_config = ConfigDict(strict=True, frozen=True)

    position: str = Field(min_length=10, max_length=500, description="Core position in 1-2 sentences")
    claims: list[str] = Field(min_length=1, max_length=5, description="Supporting claims")
    uncertainty: str = Field(min_length=5, max_length=300, description="Key assumption or uncertainty")

    @field_validator("claims")
    @classmethod
    def claims_not_empty_strings(cls, v: list[str]) -> list[str]:
        if any(not claim.strip() for claim in v):
            raise ValueError("Claims cannot be empty strings")
        return [claim.strip() for claim in v]

class DeliberationResponse(BaseModel):
    """Deliberation round output."""
    stance: Literal["AGREE", "DISAGREE", "PARTIAL", "ABSTAIN"] = Field(description="Position on previous speaker")
    reference: str = Field(min_length=1, description="Which speaker(s) being referenced")
    key_point: str = Field(description="Main argument")
    new_consideration: str | None = Field(default=None, description="Novel point not yet raised")
    confidence: float = Field(ge=0, le=1, description="Confidence in position")

class ConsensusVote(BaseModel):
    """Explicit consensus signal."""
    consensus_reached: bool
    agreed_position: str | None = None
    dissenting_points: list[str] = Field(default_factory=list)

    @classmethod
    def from_raw_response(cls, text: str) -> "ConsensusVote | None":
        """Parse from LLM response, returning None if unparseable."""
        import json
        try:
            data = json.loads(text)
            return cls.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            return None
```

#### Research Insights: Structured Output

**Best Practices (from OpenRouter docs):**
- Use `response_format: {"type": "json_schema", "json_schema": {...}}` with `strict: true`
- Set `additionalProperties: false` to prevent hallucinated fields
- Include descriptions for all properties to guide the model

**Model Support Matrix:**
| Model | Structured Output Support |
|-------|---------------------------|
| Claude Opus 4.5 | Yes (via structured-outputs-2025-11-13 header) |
| GPT-5.2 | Yes (native) |
| Gemini 3 Pro | Yes (via OpenRouter) |
| Grok 4 | Partial (may need prompt fallback) |
| Kimi K2 | Partial (may need prompt fallback) |

**Fallback Strategy (from research):**
```python
async def query_with_schema(model: str, messages: list, schema: type[BaseModel]) -> BaseModel | str:
    """Query with structured output, falling back gracefully."""
    # Try structured first
    try:
        response = await query_model_async(
            model=model,
            messages=messages,
            response_format={"type": "json_schema", "json_schema": schema.model_json_schema()}
        )
        return schema.model_validate_json(response)
    except ValidationError:
        # Retry with explicit schema in prompt
        messages_with_schema = messages + [{
            "role": "user",
            "content": f"Respond with valid JSON matching: {schema.model_json_schema()}"
        }]
        response = await query_model_async(model=model, messages=messages_with_schema)
        try:
            return schema.model_validate_json(response)
        except ValidationError:
            return response  # Return raw string as fallback
```

**Simplification Counter-Argument:**
> "The current 22-line `detect_consensus()` function works fine. 'Consensus spoofing' is a theoretical threat that hasn't happened. Prose is the feature, not the bug."

**Recommendation:** Implement structured output as opt-in (`--structured` flag), not default. Monitor whether it actually improves reliability before making it default.

---

### Phase 2: Domain-Aware Weighting

Route questions to appropriate model weights based on domain classification.

**Domain Taxonomy (Updated with LMArena data):**
| Domain | Description | Model Affinities (Jan 2026 benchmarks) |
|--------|-------------|----------------------------------------|
| `code` | Programming, debugging, code review | Claude Opus 4.5 (#1 SWE-bench) > GPT > Gemini |
| `math_reasoning` | Logic, math, proofs | Gemini 3 Pro (GPQA 91.9%) > GPT > Claude |
| `creative` | Writing, brainstorming | Gemini 3 Pro (#1 LMArena Creative) > Claude > GPT |
| `expert` | Hard prompts, nuanced decisions | Claude Opus 4.5 (#1 LMArena Expert) > Claude Sonnet |
| `general` | Default, no special weighting | Equal weights |

#### Research Insights: Domain Routing

**RouteLLM Paper Findings (ICLR 2025):**
- 85% cost reduction on MT-Bench while maintaining 95% quality
- Routers trained on one model pair generalize to others
- Keyword-based classification achieves ~70% accuracy; embedding-based ~85%

**Recommended Classification (Performance-Optimized):**
```python
# <1ms keyword matching (use this, not LLM classification)
DOMAIN_KEYWORDS = {
    "code": {"python", "javascript", "function", "debug", "api", "class", "bug", "error"},
    "math_reasoning": {"prove", "calculate", "equation", "probability", "derive"},
    "creative": {"write", "story", "poem", "brainstorm", "creative", "imagine"},
    "expert": {"architecture", "system", "design", "scale", "tradeoff", "decision"},
}

def classify_domain_fast(question: str) -> tuple[str, float]:
    """Fast keyword-based classification (<1ms)."""
    words = set(question.lower().split())
    scores = {domain: len(words & keywords) for domain, keywords in DOMAIN_KEYWORDS.items()}
    if max(scores.values()) == 0:
        return "general", 0.5
    best = max(scores, key=scores.get)
    return best, scores[best] / (sum(scores.values()) + 1)
```

**Simplification Counter-Argument:**
> "The whole point of a council is *diverse perspectives*, not weighted voting toward pre-determined experts. Static weights are made-up numbers with no data behind them."

**Alternative Approach:** Instead of weighted voting, just add domain context to judge prompt:
```python
# Simpler: One prompt tweak, no infrastructure
if args.context:
    judge_prompt += f"\n\nContext: This is a {args.context} question."
```

**Recommendation:** Start with simple `--context` flag for judge prompt. Only implement weighted voting if you have data showing it helps.

---

### Phase 3: Evaluation Harness

A/B testing framework to compare council vs baseline models.

#### Research Insights: LLM-as-Judge Best Practices

**From LangSmith/Promptfoo research:**

1. **Ditch 1-10 scales** - Use discrete categories: `Fully Correct`, `Partial`, `Incorrect`
2. **Force chain-of-thought** - Judge must reason before scoring
3. **Use comparative ranking** - A/B comparison reduces bias vs absolute scoring
4. **Set temperature=0** - For consistency across evaluations

**Recommended Judge Prompt Pattern (G-Eval):**
```python
def judge_comparison(question: str, council_answer: str, baseline_answer: str) -> dict:
    """Compare council vs baseline with structured judgment."""
    prompt = f"""
    Compare these two answers to the question.

    Question: {question}

    Answer A (Council): {council_answer}
    Answer B (Baseline): {baseline_answer}

    Evaluate on:
    1. Correctness: Is the answer factually accurate?
    2. Completeness: Does it address all aspects?
    3. Clarity: Is it well-organized and clear?

    First, analyze each answer step-by-step.
    Then output JSON: {{"winner": "A"|"B"|"tie", "reasoning": "...", "scores": {{"A": 1-5, "B": 1-5}}}}
    """
    return judge_model.generate(prompt, temperature=0)
```

#### Storage: SQLite vs JSONL

**Simplification Insight:**
> "This is a personal CLI tool run a few times per week. You don't need a database."

**JSONL Alternative (5 LOC vs 100+ LOC):**
```python
# At end of run_council():
import json
from pathlib import Path

history_file = Path.home() / ".council_history.jsonl"
with history_file.open("a") as f:
    f.write(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "question": question[:200],
        "consensus_reached": converged,
        "domain": domain,
    }) + "\n")
```

**If SQLite is needed, add these optimizations:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_runs_timestamp ON council_runs(timestamp DESC);
CREATE INDEX idx_runs_domain ON council_runs(domain);
CREATE INDEX idx_responses_run ON model_responses(run_id);

-- Use WAL mode for better performance
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- Add cascade delete
run_id TEXT REFERENCES council_runs(id) ON DELETE CASCADE
```

**Recommendation:** Start with JSONL. Only add SQLite if you're actually doing batch analysis.

---

## Technical Approach

### Architecture (Revised)

**Simplest viable approach:**
```
council.py (existing)
  + async blind phase (performance fix)
  + --context flag for judge (domain hint)
  + JSONL history append (optional)
```

**Full approach (if proceeding with all phases):**
```
llm-council/
├── council.py              # CLI entry point (thin)
├── core/
│   ├── schema.py          # Pydantic models
│   ├── router.py          # Domain classification
│   └── consensus.py       # Consensus detection
├── storage/
│   └── sqlite.py          # SQLite implementation
└── evaluation/
    ├── harness.py         # A/B testing
    └── judge.py           # LLM-as-judge
```

### Implementation Phases (Revised Order)

Per architecture review, recommended order is:

1. **Phase 0 (Pre-req):** Parallelize blind phase - immediate 50% latency win
2. **Phase 1:** Storage (JSONL or SQLite) - enables tracking for later phases
3. **Phase 2:** Domain routing with simple `--context` first
4. **Phase 3:** Structured output (opt-in, not default)
5. **Phase 4:** Evaluation harness (only if validating council value)

#### Phase 0: Async Blind Phase (1 session)

```python
# Convert synchronous to async
import asyncio

def main():
    # ... existing CLI parsing
    result = asyncio.run(run_council_async(args))
```

**Files to modify:**
- `council.py:59-127` - Convert `query_model()` to async
- `council.py:431-465` - Convert `run_blind_phase()` to parallel

#### Phase 1: Structured Output (2-3 sessions)

1. Add `council_schema.py` with Pydantic models
2. Modify `query_model()` to optionally request JSON output
3. Add retry logic for schema validation failures
4. Add `--structured` flag (default: False initially)

#### Phase 2: Domain Routing (2-3 sessions)

1. Add keyword-based domain classifier
2. Add `--context` flag for judge prompt
3. (Optional) Add weighted voting if data supports it

#### Phase 3: Evaluation Harness (3-4 sessions)

1. Add JSONL or SQLite storage
2. Implement baseline runner (parallel with council)
3. Add LLM-as-judge comparison
4. Add `--eval` flag

---

## Acceptance Criteria

### Functional Requirements

- [ ] Blind phase runs in parallel (async)
- [ ] Structured output schema defined (opt-in via `--structured`)
- [ ] Domain classification works via keywords
- [ ] `--context` flag adds domain hint to judge
- [ ] Run history stored (JSONL or SQLite)
- [ ] `--eval` produces council vs baseline comparison

### Non-Functional Requirements

- [ ] Parallel blind phase: <25s (down from 50-100s)
- [ ] Schema parsing adds <500ms latency (when enabled)
- [ ] Storage overhead <1MB per 100 runs
- [ ] Graceful fallback when schema fails
- [ ] No breaking changes to existing CLI

### Quality Gates

- [ ] Test async blind phase with all 5 models
- [ ] Verify structured output works with Claude, GPT, Gemini (core 3)
- [ ] Confirm rate limit handling works under parallel load
- [ ] Validate storage queries perform acceptably

---

## Dependencies & Risks

### Dependencies

| Dependency | Purpose | Risk |
|------------|---------|------|
| Pydantic | Schema validation | Low - already indirect dep |
| httpx (async) | Parallel HTTP | Low - already in use |
| SQLite | Run storage | Low - Python stdlib |
| OpenRouter structured output | JSON mode | Medium - model support varies |

### Risks (Updated with Research)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Models don't follow schema | Medium | High | Tiered fallback: structured → prompt-based → raw |
| Domain weights don't improve quality | High | Medium | Start with `--context` hint only; validate before weights |
| Storage grows unbounded | Low | Low | JSONL is trivial to prune; SQLite: 90-day retention |
| Rate limits under parallel load | Medium | Medium | Per-model semaphores; exponential backoff |
| Over-engineering a personal tool | High | Medium | Start with JSONL not SQLite; `--structured` opt-in |

### Newly Identified Risks (from research)

| Risk | Mitigation |
|------|------------|
| Fallback providers (Google AI Studio, Moonshot) don't support structured output | Document support matrix; graceful fallback to prompt-based |
| Schema version drift in stored data | Add schema version to storage; handle migration |
| Judge bias from domain context | A/B test with/without domain in judge prompt |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Blind phase latency | <25s | Wallclock (was 50-100s) |
| Schema compliance rate | >90% | % of responses parsing (when --structured) |
| Domain classification accuracy | >70% | Keyword match vs user-provided domain |
| Implementation velocity | 6-8 sessions | Time to async + storage + eval |

---

## Simplification Decision Point

Before implementing Phases 1-3, consider the simplicity reviewer's argument:

> "The current tool is already good. Don't framework it."

**Minimum Viable Improvements (3 sessions total):**
1. ✅ Parallelize blind phase (huge win, low effort)
2. ✅ Add `--context` flag for judge prompt (5 LOC)
3. ✅ Add JSONL history append (5 LOC)
4. ✅ Add `--cost` flag to print token estimate (10 LOC)

**Full Implementation (8-10 sessions):**
Only proceed if you actually need:
- Structured output parsing
- Weighted voting
- A/B evaluation infrastructure

---

## Future Considerations

1. **Dynamic weight learning** - Adjust weights based on historical performance
2. **Custom domain definitions** - User-defined domains with custom weights
3. **Promptfoo integration** - Export evaluations for external analysis
4. **Model cost optimization** - Route cheap questions to faster models
5. **Confidence calibration** - Track if stated confidence matches actual quality

---

## References

### Internal
- Current implementation: `/Users/terry/skills/llm-council/council.py`
- SKILL.md: `/Users/terry/skills/llm-council/SKILL.md`

### External
- OpenRouter structured outputs: https://openrouter.ai/docs/guides/features/structured-outputs
- Pydantic: https://docs.pydantic.dev/
- Instructor pattern: https://python.useinstructor.com/
- RouteLLM paper: https://arxiv.org/abs/2403.12031
- LangSmith evaluation: https://docs.smith.langchain.com/evaluation

### Research
- Model benchmarks: https://lmarena.ai (Chatbot Arena)
- Domain routing: https://github.com/lm-sys/RouteLLM
- Multi-agent consensus: AutoGen MathAggregator pattern
- Voting vs Consensus paper: ACL 2025 (voting +13.2% on reasoning, consensus +2.8% on knowledge)
