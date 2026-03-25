---
name: quorum
description: Multi-model deliberation for judgment calls — auto-routes by difficulty. Full council (~$0.50), quick parallel (~$0.10), red team (~$0.20). Use for decisions, trade-offs, naming, strategy. NOT for factual research (use elencho or WebSearch).
aliases: [ask-llms, council, ask llms]
github_url: https://github.com/terry-li-hm/quorum
user_invocable: true
cli_version: 0.5.1
cli_verified: 2026-03-03
runtime: rust
---

# Consilium

5 frontier models deliberate on a question, then Gemini judges and Claude critiques. Auto-routes by difficulty.

> Source: `~/code/quorum/`. Extended reference: `~/code/vivesca/receptors/quorum/REFERENCE.md`.

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

**Step 2: Run — always backgrounded, always `--vault` for deep/council runs**

```bash
quorum "question" --deep --vault

# With prompt file (avoids shell quoting issues)
quorum --prompt-file /tmp/prompt.txt --deep --vault

# Batch/agent-test runs (--quick --quiet)
quorum --quick --quiet --domain banking -o ~/code/vivesca/loci/solutions/agent-tests/<name>.md "..."
```

- `--vault` auto-saves to `~/epigenome/chromatin/Councils/` with Obsidian Sync. Never `--output /tmp/` — wiped on reboot.
- **Always `run_in_background: true`** on the Bash tool.
- Running 4+ parallel `--council` hits OpenRouter rate limits — use `--quick` for parallel batch runs.

**Output retrieval** — quorum detects pipes and uses SilentOutput; redirect to `~/tmp/` and read after:

```bash
quorum "..." --quick > ~/tmp/consi-<name>.txt 2>&1
# after task completes:
cat ~/tmp/consi-<name>.txt
```

**Step 3: Parse and present** — read `[DECISION]` line, read vault file in `~/epigenome/chromatin/Councils/`, synthesize: decision + key reasoning + dissents + cost. Never dump raw transcript into context.

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

- **402** = OpenRouter out of credits — tell Terry to top up at openrouter.ai/credits. Don't retry.
- **403 on new model** = access restricted. Test before using: `quorum --quick --quiet "test" 2>&1 | grep -i "403\|error"`.
- **Two spend streams:** OpenRouter (`stips`) + OpenAI direct (`platform.openai.com/usage`). Responses API models bypass OpenRouter and burn the direct OPENAI_API_KEY. Keep OpenAI direct budget cap at $20.
- **Before adding any new model:** run speed test (`quorum --quick --quiet "name a color"`) — any model >60s doesn't belong. Run `pondus check "<model>"` to verify pricing; `-pro` reasoning variants can cost 10–12× more than base.
- **Strip PII from personal/family prompts.** OpenRouter routes to 6+ third-party providers. Use roles ("my son", "my wife") not names.
- **`--format json`**, `--challenger`, `--followup` are council/quick only. Binary can go stale after code changes: `cd ~/code/quorum && cargo build --release`.

---

## Reference

Extended docs in `~/code/vivesca/receptors/quorum/REFERENCE.md`: prompting tips, model tendencies, flag compatibility matrix, follow-up workflow, cost & ROI, research foundations.
