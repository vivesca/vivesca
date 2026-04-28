# Consilium Reference

Extended reference for prompting tips, model tendencies, research foundations, and follow-up workflow. Linked from `SKILL.md`.

## Prompting Tips

**For draft reviews** (LinkedIn comments, emails, messages, posts):

Always include the source material in the prompt — models can't judge tone, positioning, or reception risk without seeing what the draft responds to. Structure the prompt as:
1. The original post/email/thread being responded to (full text or key excerpts)
2. The drafted response
3. Context about the author's relationship to the recipient and goals
4. Specific review criteria (tone, positioning risk, information leaks, reception)

Mode selection by stakes:
- `--quick` (~$0.10): Internal messages, Slack replies, low-visibility comments
- `--redteam` (~$0.20): Plans or proposals being stress-tested
- `--council --domain <X>` (~$0.50): **Public comments, LinkedIn posts, anything that builds or risks reputation.** Reputation-building content is not a tone check — it needs full deliberation on positioning, strategic value, and network effects. Include `--persona` with career context and goals.

**For social/conversational contexts** (interview questions, networking, outreach):

LLMs over-optimize for thoroughness. Add constraints like:
- "Make it feel like a natural conversation"
- "Something you'd actually ask over coffee"
- "Simple and human, not structured and comprehensive"

**Match context depth to question type:**
- Strategic decisions: provide rich context (full background, constraints, history)
- Social questions: minimal context + clear tone constraints

**For architecture/design questions:**

Provide scale and constraints upfront to avoid premature optimization advice:
- "This is a single-user system" (avoids multi-user concerns)
- "We have 500 notes, not 50,000" (avoids scaling infrastructure)
- "Manual processes are acceptable" (avoids automation overkill)

Without these constraints, council tends to suggest infrastructure for problems that don't exist yet.

**For skill/tool design questions:**

Council optimizes for architecture but often misses input edge cases. Add:
- "What input variations should this handle?" (e.g., URLs vs pasted content)
- "What edge cases might break this?" (e.g., hybrid content types)
- "What would make users reach for a different tool instead?"

**For philosophical/contemplative questions:**

Council excels at finding structural cracks in propositional claims — but blind to teachings that are *instructions* rather than *arguments*. "Look for the self" is a direction to look, not a truth claim. When evaluating non-propositional frameworks (meditation, therapy, coaching), add:
- "Distinguish claims (testable assertions) from pointers (instructions for seeing)"
- "Rate practical utility separately from philosophical coherence"
- `--decompose` works well here — breaks apart the sub-questions that a philosophical system bundles together

Without this framing, council will evaluate a ladder as a floor.

**For domain-specific questions (banking, healthcare, etc.):**

Use `--domain` flag to auto-inject regulatory context:
```bash
consilium "question" --domain banking   # HKMA/MAS/FCA, MRM requirements
consilium "question" --domain healthcare # HIPAA constraints
consilium "question" --domain eu        # GDPR/AI Act considerations
```

---

## Picking Models — How to Read Leaderboards

Two leaderboards, different signals. **Never average them.**

- **LMArena** (`arena.ai/leaderboard/text`) — blind human pairwise preference (Elo). Measures *vibes*: chat fluency, tone, register match. Gameable via verbose hedging.
- **Artificial Analysis** (`artificialanalysis.ai`) — composite of GDPval-AA, τ²-Bench, Terminal-Bench, SciCode, AA-LCR, AA-Omniscience + measured price/latency. Measures *capability and economics*. Composite can mask uneven profiles.

**For quorate panel selection: weight AA ~70%, LMArena ~30%.** Council's job is distinct judgments, not pleasant prose. Reverse for garden/writing.

**Pre-swap checklist:**
1. Check the *sub-benchmark* matching the use case (LiveCodeBench for coding, GPQA for reasoning, GDPval-AA for economic value), not the rollup.
2. Read AA's verbosity stat — `tokens_generated >> 2x avg` = council token cost inflates. (V4 Pro example: 190M vs 45M avg.)
3. Cross-check capability/preference split. AA-high + Arena-low = capable but unloved (good for council). AA-low + Arena-high = pleasant but shallow.
4. **Family diversity over peak score** — adding a model from a family already in panel is a wasted slot regardless of rank. Per `finding_deliberation_panel_monoculture.md`.
5. Speedtest before commit: `quorate quick "name a color"` with candidate pinned. >60s/model = doesn't belong.

Full table in `~/epigenome/marks/finding_leaderboard_weighting_for_panel_selection.md`.

---

## Model Tendencies

| Model | Role | Tendency | Useful For |
|-------|------|----------|------------|
| **GPT-5.5** | M1 (OpenAI) | Practical, implementation-focused; AA Index leader (60) | Actionable steps |
| **Claude Opus 4.7** | M2 (Anthropic) | Balanced, expert judgment | Strategic depth |
| **Grok 4.20** | M3 (xAI) | Contrarian, challenges consensus | Stress-testing ideas |
| **Kimi K2.6** | M4 (Moonshot) | Top open-source on AA Index; reasoning-heavy MoE | Technical + Chinese-lineage perspective |
| **GLM-5.1** | M5 (Zhipu) | Strategic, pragmatic (best-validated CN model) | Business decisions |
| **Mimo v2.5 Pro** | M6 (Xiaomi) | AA Index 54 — tied with Kimi K2.6 as top open-source | Distinct lineage, frontier tier |
| **Gemini 3.1 Pro** | Judge (Google) | Technical synthesis, systems thinking | Final judgment |
| **Claude Opus 4.7** | Critique (Anthropic) | Independent review of judge synthesis | Catching judge gaps |

*Config source of truth: `~/code/quorate/src/quorate/config.py:94-99`. Update this table after any swap.*

**Default challenger:** GPT (rotates each round). Grok is naturally contrarian regardless, so GPT as explicit challenger gives two sources of pushback.

**Override:** `--challenger gemini` (architecture), `--challenger grok` (max pushback).

---

## Flag Compatibility

| Flag | council | quick | discuss | socratic | oxford | redteam | solo |
|------|---------|-------|---------|----------|--------|---------|------|
| `--format json` | yes | yes | **no** | **no** | **no** | **no** | **no** |
| `--challenger` | yes | **no** | **no** | **no** | **no** | **no** | **no** |
| `--followup` | yes | **no** | **no** | **no** | **no** | **no** | **no** |
| `--rounds` | no | no | yes | yes | no | no | no |
| `--motion` | no | no | no | no | yes | no | no |
| `--roles` | no | no | no | no | no | no | yes |
| `--decompose` | yes | no | no | no | no | no | no |
| `--xpol` | yes | no | no | no | no | no | no |

---

## Follow-Up Workflow (Steps 5-6)

After presenting the council's recommendation:

**Options to offer:**
1. **Create tasks** — Add action_items to task list via TaskCreate
2. **Save to vault** — Already handled if `--vault` was used. Manual template:

```markdown
---
date: {date}
type: decision
question: "{question}"
status: pending
decision: "{decision}"
confidence: {confidence}
participants: {from meta.models_used}
tags:
  - decision
  - consilium
---

**Related:** [[Capco Transition]] | [[Job Hunting]]

## Decision
{decision}

## Reasoning
{reasoning_summary}

## Dissents
{for each dissent: - **{model}:** {concern}}

## Action Items
{for each action: - [ ] {action}}

---
*Council convened: {date} | {models count} models | {rounds} rounds | ~${cost}*
```

3. **Draft messages** — Draft follow-up messages based on action_items
4. **Just note it** — No further action needed

---

## Cost & ROI

- ~$0.60 for full discuss mode. Worth it when genuinely novel insights emerge. Diminishing returns on second pass of same topic.
- **2 novel insights per council = good; 0 = should have used `--quick`.**
- **Tone/networking review = good ROI.** Substack comment review caught "unguided AI" phrasing that could read as "consultant advocates shipping AI without governance" in banking context — reputational risk invisible to the drafter.
- **Framing bias:** 6/6 unanimity in quick mode is a red flag — means the prompt is one-sided, not that the answer is obvious. Always include "Option: fix the existing thing" for deprecation/migration decisions. No council will challenge the frame you give them — the user has to. See [[Frontier Council Lessons]].

---

## Key Lessons

See `[[Frontier Council Lessons]]` for full usage lessons. Critical ones:

- **Add constraints upfront** — models default to enterprise-grade without "this is a POC" / "single-user" / "speed > perfection"
- **Include real metrics** for optimization questions, not just descriptions
- **Trust the judge's framing over its action list** — it diagnoses well but over-aggregates prescriptions
- **Challenger round is the highest-value component** — GPT-5.2 as explicit challenger consistently produces the best single insight
- **Iterative councils beat single deep runs** — second pass on same topic goes deeper with sharper framing
- **Blind phase often produces agreement, not debate** — the real value comes from challenger + judge
- **Front-load constraints in the question** — "this must work for HKMA-regulated banks" produces tighter output than "how should banks govern AI?"
- **Critic phase catches real gaps** — the Gemini critique of the judge's synthesis frequently identifies tactical errors

---

## Research Foundations

Consilium's architecture is grounded in group deliberation research. Full synthesis with 21 papers: `~/docs/solutions/multi-llm-deliberation-research.md`.

**Why the blind phase matters most** (Surowiecki, Delphi, Tetlock): Independence before exposure is the single most validated principle. The blind phase captures independent positions before herding kicks in.

**Why the challenger works** (Nemeth 2001): Assigned devil's advocates produce bolstering, not reconsideration. Consilium mitigates this by framing the challenger with questions (not assertions) and different epistemic priors — but the limitation is real.

**Why convergence is a strong signal** (Tetlock/GJP): When independent agents with different models/priors agree, the evidence is multiplicative. The judge should extremize convergent conclusions.

**Exception — regulatory/domain-specific groupthink:** Unanimous alarm on a technical/regulatory concern is a red flag, not a strong signal. All models share training data from the same domain literature. When all agents converge on a named regulatory concept (SR 11-7, BCBS 239, MAS AIRM), check whether the reasoning is *independently derived* or *shared framing from training data*.

**Why sycophancy is the #1 risk** (ICLR 2025, ACL 2025): Multi-agent debate produces "correct-to-incorrect" flips that exceed improvements. Position changes without new evidence are sycophancy, not reasoning.

**Why the judge uses ACH** (Heuer/CIA): Analysis of Competing Hypotheses — list competing conclusions, evaluate evidence against each, eliminate rather than confirm.

**What consilium can't fix** (MAD literature): Most of the apparent value of multi-agent debate comes from generating multiple independent samples, not from the debate itself. Consilium's real value is divergent thinking — not convergent reasoning (math, facts).

---

## Recent Features

- **Gemini as judge + Claude as M2** (Mar 2026): All 6 frontier labs now in council. `CONSILIUM_MODEL_JUDGE` env var restores Opus as judge. `CONSILIUM_MODEL_M2` env var overrides M2.
- **`--effort low|medium|high`** (Mar 2026): Per-phase reasoning budget. Blind phase uses configured effort; debate steps down one level; judge always uses High.
- **Blind claims for judge** (v0.5.1): Judge receives raw blind-phase claims before debate transcript — enables sycophantic drift detection.
- **Confidence extraction** (v0.5.1): Parses "Confidence: N/10" from each panelist's last response.
- **Response order randomization** (v0.5.1): Shuffles other speakers' responses per panelist per round.
- **Fallacy-Oversight rubric** (v0.5.1): Gemini critique checks for unsupported premises, invalid inferences, false dichotomies, correlation-causation conflation.
- **Context compression** (v0.1.4+): Multi-round debates compress prior rounds via Llama 3.3 70B. Use `--thorough` to disable.
- **Challenger dissent protection** (v0.1.5+): If the challenger is actively dissenting, consensus early exit is blocked.
