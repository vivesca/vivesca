---
name: quorate
description: Multi-model deliberation for judgment calls — auto-routes by difficulty. Use when deciding trade-offs, naming, or strategy. "council", "ask llms", "deliberate", "quorate"
aliases: [ask-llms, council, ask llms, consilium]
effort: high
triggers:
  - quorate
  - consilium
  - council
  - ask-llms
  - ask llms
  - deliberation
  - multi-model
  - debate
github_url: https://github.com/terry-li-hm/quorate
user_invocable: true
epistemics: [review, deliberation]
cli_version: 0.1.1
cli_verified: 2026-04-18
runtime: python
---

# Quorate

5 frontier models deliberate on a question, then Gemini judges and Claude critiques. Models see and respond to previous speakers, with a rotating challenger ensuring sustained disagreement. Auto-routes by difficulty.

> Source: `~/code/quorate/`. Extended reference: `~/germline/membrane/receptors/quorate/REFERENCE.md`.

---

## Modes

Modes are subcommands, not flags. `--deep` is a modifier on any subcommand.

| Mode | Command | Cost | Description |
|------|---------|------|-------------|
| Quick | `quorate quick "Q"` | ~$0.10 | Parallel queries, no debate/judge |
| Council | `quorate council "Q"` | ~$0.50 | Full multi-round debate + judge |
| Council deep | `quorate council --deep "Q"` | ~$0.90 | Council + auto-decompose + 2 debate rounds |
| Oxford | `quorate oxford "Q"` | ~$0.40 | Binary for/against debate |
| Red team | `quorate redteam "Q"` | ~$0.20 | Adversarial stress-test |
| Premortem | `quorate premortem "Q"` | ~$0.20 | Assume failure, work backward |
| Discuss | `quorate discuss "Q"` | ~$0.30 | Open roundtable, no judge |

---

## Routing

**Mental model:** `quick` = breadth (surface perspectives), `council` = convergence (stress-test a decision). Before framing the question, scan `topica` triggers — name 1-2 applicable models in the prompt context (e.g., "Noting: this has a sunk-cost + second-order shape").

**Default bias: deep > council > quick.** Career, negotiation, strategy, real consequences → `council --deep`. Reserve `quick` for naming and pure brainstorming.

```
Single correct answer? → Web search or ask Claude directly
Personal preference / physical / visual? → Try it in person
Measurable outcome? → judex (run the experiment)
Need perspectives without debate? → quick
Binary for/against? → oxford
Stress-testing a plan? → redteam
Assume failure, work backward? → premortem
Exploratory, still forming the question? → discuss
Everything else → council --deep (default)
```

---

## Interpreting Results — Confidence Gate

When reviewing quorate output with multiple models disagreeing:

- **Suppress findings below 0.50 confidence** — don't surface noise to the user
- **Retain low-confidence findings as residuals** — if a second model corroborates (even weakly, 0.55+), promote
- **Promote unconditionally** if the finding describes a concrete blocking risk, regardless of confidence
- When models disagree on the same point, present as a **tradeoff** (not dropped, not merged into one winner) — the user decides

## When to Use / Not Use

**Use:** Genuine trade-offs, domain-specific decisions, strategy, stress-testing plans, probabilistic forecasting, code/security audit (`--redteam` with code pasted in).

**Skip:** Single correct answer, personal taste/physical (glasses, food), thinking out loud, already converged, speed matters (60-90s for full council).

---

## Prerequisites

```bash
# API key — already in ~/.zshenv, available in all shells including background
export OPENROUTER_API_KEY=$(security find-generic-password -s openrouter-api-key -a terry -w 2>/dev/null)

# CLI: installed via uv tool install ~/code/quorate
# After code changes: uv tool install --reinstall --from ~/code/quorate quorate
```

---

## Running the Council

### Step 0: Suitability check

**quorate or judex?** If the outcome is measurable (build passes, benchmark faster, quality checkable) → `judex`. Deliberation is for decisions you can't measure.

Check the routing table above. If it falls in "Skip", redirect.

### Step 0.25: Rationale-companion check (mandatory for chromatin/immunity papers)

Before running quorate on any deliverable in `chromatin/immunity/*.md` (Board papers, committee papers, stakeholder artefacts), check for a sibling `*-rationale-annotations*` file:

```bash
# stem = the deliverable's filename without -vN.NN.md
ls /home/vivesca/epigenome/chromatin/immunity/<stem>*rationale-annotations*.md 2>/dev/null
```

If a rationale-annotations file exists, **load it as additional context**:
- `quorate council --context <body>,<rationale> "..."` (multi-context if CLI supports)
- OR explicitly summarise the rationale's "non-negotiable" / decision-log "reversal cost: zero" entries in the prompt: *"The following items survived prior knockout passes and are constitutionally defended — do not reverse without strong reason: [list]."*

Also state the document's **register** in the prompt:
- *"This is a constitutional Board endorsement paper — Recommendation grants authority abstractly, body should match the abstract level, operating-model paper handles concrete gates."*
- vs. a regular committee paper, operating-model paper, or technical brief — different register, different anchoring discipline.

**Why mandatory:** without the rationale layer, the council reads the surface text only and applies its default (regular committee paper) anchoring discipline. Three failure modes documented as of 2026-04-28: SOFTEN-the-power-claim against a constitutional grant; DELETE buyer-leverage as redundant when it carries Board-aspiration; ANCHOR a body sentence that preempts the reserved follow-up paper. All three are predictable artefacts of running quorate without the rationale companion. Per `feedback_council_without_rationale_file.md` (PROTECTED, confirmed=2 with n=3-doesn't-revisit + template-confusion extension).

**N=3 doesn't revisit.** Three cold-read reviewers without rationale file proposing the same fix is the *predicted* output of diagnostic-only-consensus, not new evidence. Bar to revisit a chromatin-defended position: reviewer WITH rationale file, OR a rationale-layer-novel attack. Routine convergence-without-context = pattern, not signal.

### Step 0.5: Propose mode

Tell the user which mode and why (one line), then confirm. Don't run until confirmed.

> "Strategic question with real consequences — I'd use **--deep --xpol**. Good?"

### Step 1: Run — always backgrounded

```bash
# Council with context file
quorate council --deep --context ~/path/to/context.md "question" > ~/tmp/quorate-name.txt 2>&1

# Quick parallel query
quorate quick "question" > ~/tmp/quorate-name.txt 2>&1
```

**Available flags** (run `quorate <subcommand> --help` for current list):
- `--context <file>` — attach a file as context
- `--deep / --no-deep` — enable deep mode (auto-decompose + extra rounds)
- `--json / --no-json` — machine-parseable output

**Always `run_in_background: true`** on the Bash tool. Redirect to `~/tmp/` and read after completion.

**Timing:** `quick` takes ~30-40s. `council` takes 2-5 min. `council --deep` takes 3-7 min. Don't kill early.

**Retrieving output:** quorate uses SilentOutput when piped. Always redirect to `~/tmp/` and `cat` after:
```bash
cat ~/tmp/quorate-name.txt
```

**Don't retry if seemingly stuck.** One background job per query.

### Step 3: Parse and present

After completion:
1. Read `[DECISION]` line as quick signal
2. Read vault file in `~/epigenome/chromatin/Councils/`
3. Synthesize: decision + key reasoning + dissents + cost
4. **Never dump raw transcript into context**

If `--vault` was used but file is missing in `~/epigenome/chromatin/Councils/`, treat run as partial.

---

## Known Issues

- **OPENROUTER_API_KEY in background shells** — fixed: key in `~/.zshenv`. No inline fetch needed.
- **CLI can go stale after code changes.** `uv tool install --reinstall --from ~/code/quorate quorate`
- **Model timeouts** (historically DeepSeek/GLM) — partial outputs add noise but council still works.
- **Before adding any new model:** run `quorate quick "name a color" > ~/tmp/quorate-speedtest.txt` and check per-model timings. >60s = doesn't belong.
- **Two spend streams:** OpenRouter (`stips`) + OpenAI direct. Responses API models bypass OpenRouter.
- **402 = OpenRouter out of credits.** Tell Terry to top up. Do not retry.
- **403 on a new model = allowlist-gated.** Test before upgrading.

---

## Reference

Extended docs in `~/germline/membrane/receptors/quorate/REFERENCE.md`:
- Prompting tips (drafts, social, architecture, philosophical, domain-specific)
- Model tendencies table
- Flag compatibility matrix
- Follow-up workflow + vault template
- Cost & ROI
- Key lessons
- Research foundations (Surowiecki, Tetlock, Nemeth, CIA ACH)
- Recent features changelog

---

## See Also

- Repository: https://github.com/terry-li-hm/quorate
- Related: `/judex` (measurable outcomes), `/ask-llms` (alias)
- Lessons: `[[Frontier Council Lessons]]`
- Research: `~/docs/solutions/multi-llm-deliberation-research.md`
