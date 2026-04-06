---
name: quorum
description: Multi-model deliberation for judgment calls. "council", "ask llms"
aliases: [ask-llms, council, ask llms]
effort: high
user_invocable: true
runtime: python
organelle: metabolon.organelles.quorum
---

# Consilium

5 frontier models deliberate on a question, then Gemini judges and Claude critiques. Auto-routes by difficulty.

> Source: `~/germline/effectors/quorum`. Extended reference: `~/germline/membrane/receptors/quorum/REFERENCE.md`.

---

## Modes

| Mode | Flag | Cost | Description |
|------|------|------|-------------|
| Auto (default) | *(none)* | varies | Opus classifies difficulty, picks quick or council |
| Quick | `--quick` | ~$0.10 | Parallel queries, no debate/judge |
| Council | `--council` | ~$0.50 | Full multi-round debate + judge |
| Deep | `--deep` | ~$0.90 | Council + auto-decompose + 2 debate rounds |
| Deep + xpol | `--deep --xpol` | ~$1.05 | Deepest — cross-pollination pass after debate |

**Other modes:** `--redteam` (~$0.20), `--premortem` (~$0.20), `--forecast` (~$0.25), `--oxford` (~$0.40), `--discuss` (~$0.30), `--socratic` (~$0.30), `--solo` (~$0.40)
**Quick adversarial:** `--redteam` replaces the former `/proofreading` skill. Use for fast idea stress-testing without full council overhead.

---

## Routing

**Default bias: deep > council > quick.** Career, negotiation, strategy, real consequences → `--deep`. Reserve `--quick` for naming and pure brainstorming.

```
Single correct answer? → Web search or ask Claude directly
Personal preference / physical / visual? → Try it in person
Need perspectives without debate? → --quick
Binary for/against? → --oxford
Stress-testing a plan? → --redteam
Assume failure, work backward? → --premortem
Probabilistic answer? → --forecast
Exploratory, still forming the question? → --discuss or --socratic
Everything else → --deep (default)
```

**Frame the question with a lens:**

| If the question involves... | Name this lens |
|---|---|
| Saying yes to something | Opportunity cost |
| Sunk investment | Sunk cost |
| Planning or launching | Premortem |
| System/process change | Second-order effects |
| Evaluating evidence | Base rates |
| "All evidence agrees" | Confirmation bias |
| Stakeholder dynamics | Incentives |

**Narrative diagnostic:** Predictive question (what will happen?) → `--forecast` or `--council` with probability request. Explanatory question (why is this true?) → `--discuss` or `--socratic`. Mixing produces answers that sound like one but act as the other.

---

## When to Use / Not Use

**Use:** Genuine trade-offs, domain decisions, strategy, stress-testing plans, probabilistic forecasting, code/security audit (`--redteam`).

**Skip:** Single correct answer, personal taste/physical, thinking out loud, already converged, speed matters.

---

## Running the Council

**Step 1: Propose mode** — tell the user which mode and why (one line), then confirm. Don't run until confirmed.

**Step 2: Run — always backgrounded**

```bash
quorum "question" --mode council

# With prompt file (avoids shell quoting issues)
quorum --prompt-file /tmp/prompt.txt --mode council

# Batch/agent-test runs (--quick --quiet)
quorum --quick --quiet --domain banking -o ~/germline/loci/antisera/agent-tests/<name>.md "..."
```

- Auto-saves to `~/epigenome/chromatin/Councils/`. Use `--no-save` to suppress. Never `--output /tmp/` — wiped on reboot.
- **Always `run_in_background: true`** on the Bash tool.
- All panelists are flat-rate CLIs — no per-token cost, no rate limits from OpenRouter.

**Output retrieval** — quorum detects pipes and uses SilentOutput; redirect to `~/tmp/` and read after:

```bash
quorum "..." --quick > ~/tmp/consi-<name>.txt 2>&1
# after task completes:
cat ~/tmp/consi-<name>.txt
```

**Step 3: Parse and present** — read `[DECISION]` line, read chromatin file in `~/epigenome/chromatin/Councils/`, synthesize: decision + key reasoning + dissents + cost. Never dump raw transcript into context.

---

## Common Flags

```bash
--persona "context"     # Personal context injected into prompts
--domain banking        # Regulatory context (banking|healthcare|eu|fintech|bio)
--context "hint"        # Context hint for the judge
--challenger gemini     # Assign contrarian role (council mode only)
--decompose             # Break complex question into sub-questions first
--rounds 3              # Rounds for --discuss or --socratic
--followup              # Interactive drill-down after judge (council only)
--effort high           # Reasoning effort: low|medium|high
--format json           # Machine-parseable output (council + quick only)
--share                 # Upload to secret Gist
--thorough              # Skip consensus early exit + context compression
```

---

## Session Management

```bash
quorum --sessions    # List recent sessions
quorum --stats       # Cost breakdown
quorum --watch       # Live tail (rich formatted)
quorum --tui         # TUI with phase/cost/time
quorum --view "career"   # View session matching term
quorum --search "career" # Search all session content
quorum --doctor      # Check API keys and connectivity
```

---

## Gotchas

- All panelists are flat-rate CLIs (CC Max, Gemini, Codex, Goose/Droid via ZhiPu plan). Zero per-token cost.
- **Before adding any new model:** run speed test (`quorum --quick "name a color"`) — any model >60s doesn't belong.
- **`--format json`**, `--challenger`, `--followup` are council/quick only.

---

## Reference

Extended docs in `~/germline/membrane/receptors/quorum/REFERENCE.md`: prompting tips, model tendencies, flag compatibility matrix, follow-up workflow, cost & ROI, research foundations.
