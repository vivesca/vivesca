---
name: consilium
description: Multi-model deliberation for judgment calls — auto-routes by difficulty. Use when deciding trade-offs, naming, or strategy. "council", "ask llms", "deliberate"
aliases: [ask-llms, council, ask llms]
effort: high
triggers:
  - consilium
  - council
  - ask-llms
  - ask llms
  - deliberation
  - multi-model
  - debate
github_url: https://github.com/terry-li-hm/consilium
user_invocable: true
epistemics: [review, deliberation]
cli_version: 0.5.1
cli_verified: 2026-03-03
runtime: rust
---

# Consilium

5 frontier models deliberate on a question, then Gemini judges and Claude critiques. Models see and respond to previous speakers, with a rotating challenger ensuring sustained disagreement. Auto-routes by difficulty.

> Source: `~/code/consilium/`. Site: [consilium.sh](https://consilium.sh). Extended reference: `~/skills/consilium/REFERENCE.md`.

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

**Mental model:** `--quick` = breadth (surface perspectives), `--council` = convergence (stress-test a decision). Before framing the question, scan `topica` triggers — name 1-2 applicable models in the prompt context (e.g., "Noting: this has a sunk-cost + second-order shape").

**Default bias: deep > council > quick.** Career, negotiation, strategy, real consequences → `--deep`. Reserve `--quick` for naming and pure brainstorming.

```
Single correct answer? → Web search or ask Claude directly
Personal preference / physical / visual? → Try it in person
Measurable outcome? → judex (run the experiment)
Need perspectives without debate? → --quick
Binary for/against? → --oxford
Stress-testing a plan? → --redteam
Assume failure, work backward? → --premortem
Probabilistic answer? → --forecast
Exploratory, still forming the question? → --discuss or --socratic
Everything else → --deep (default)
```

---

## Interpreting Results — Confidence Gate

When reviewing consilium output with multiple models disagreeing:

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

# Binary: ~/.local/bin/consilium → ~/code/consilium/target/release/consilium
# After code changes: cd ~/code/consilium && cargo build --release
```

---

## Running the Council

### Step 0: Suitability check

**consilium or judex?** If the outcome is measurable (build passes, benchmark faster, quality checkable) → `judex`. Deliberation is for decisions you can't measure.

Check the routing table above. If it falls in "Skip", redirect.

### Step 0.5: Propose mode

Tell the user which mode and why (one line), then confirm. Don't run until confirmed.

> "Strategic question with real consequences — I'd use **--deep --xpol**. Good?"

### Step 1: Gather context (for career/strategic decisions)

```bash
consilium "Should I accept this offer?" \
  --deep \
  --persona "Principal Consultant at Capco, ex-CNCBI Head of DS, HK market" \
  --domain banking \
  --vault
```

### Step 2: Run — always backgrounded, always `--vault`

```bash
# Standard invocation
consilium "question" --deep --vault

# With prompt file (avoids shell quoting issues for long prompts)
consilium --prompt-file /tmp/prompt.txt --deep --vault
```

**`--vault` is mandatory for:** any `--deep`, `--council`, or architecture/review run. Auto-saves to `~/epigenome/chromatin/Councils/` with Obsidian Sync backup. Never use `--output /tmp/...` — `/tmp` doesn't survive reboot.

**For `--quick --quiet` batch/agent-test runs:** use `-o ~/docs/solutions/agent-tests/<name>.md` — skips Obsidian sync but survives session end. Pattern: `consilium --quick --quiet --domain banking -o ~/docs/solutions/agent-tests/proposal-architect.md "..."`

**`--quick` vs `--council` in background:** Running 4+ parallel `--council` sessions hits OpenRouter rate limits (20+ concurrent API calls). Use `--quick` for parallel batch runs; `--council` for single focused deliberations.

**Always `run_in_background: true`** on the Bash tool. Watch live: `consilium --watch` or `--tui` in another tmux tab.

**Timing:** `--quick` takes ~30-40s (6 parallel model queries). `--council` takes 2-5 min (multiple rounds + judge). Don't kill a `--quick` run before 45s — it's not hung, just waiting for all models.

**Retrieving output:** When running from CC background with pipes (`2>&1 | tail`), consilium detects the pipe and uses SilentOutput — the pipe gets nothing until the session file path prints at the end. Always redirect to `~/tmp/` and read with `cat`:
```bash
consilium "..." --quick > ~/tmp/consi-<name>.txt 2>&1
# then after task completes:
cat ~/tmp/consi-<name>.txt
```
Never use TaskOutput alone to retrieve consilium results — it will timeout and the output file in `/private/tmp` will vanish. `~/tmp/` survives the session.

**Don't retry if seemingly stuck.** One background job per query. If TaskOutput times out, just `cat ~/tmp/consi-<name>.txt` — the job is likely still running or already done.

### Step 3: Parse and present

After completion:
1. Read `[DECISION]` line as quick signal
2. Read vault file in `~/epigenome/chromatin/Councils/`
3. Synthesize: decision + key reasoning + dissents + cost
4. **Never dump raw transcript into context**

If `--vault` was used but file is missing in `~/epigenome/chromatin/Councils/`, treat run as partial.

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
--no-save               # Don't auto-save to ~/.consilium/sessions/
```

---

## Session Management

```bash
consilium --sessions              # List recent sessions
consilium --stats                 # Cost breakdown
consilium --watch                 # Live tail (rich formatted)
consilium --tui                   # TUI with phase/cost/time
consilium --view "career"         # View session matching term
consilium --search "career"       # Search all session content
consilium --doctor                # Check API keys and connectivity
```

---

## Known Issues

- **`--vault` is mandatory for background/overnight runs.** Never `/tmp` — wiped on reboot. `--vault` → `~/epigenome/chromatin/Councils/` with Obsidian Sync.
- **OPENROUTER_API_KEY in background shells** — fixed: key in `~/.zshenv`. No inline fetch needed.
- **Binary can go stale after code changes.** `cd ~/code/consilium && cargo build --release`
- **Model timeouts** (historically DeepSeek/GLM) — partial outputs add noise but council still works.
- **`--format json` only works with council and quick modes.** Other modes output prose only.
- **`--challenger` and `--followup` are council-only.**
- **GPT-5.4-Pro removed from council (LRN-20260308-001).** Real latency: 907s per call. Responses API models are incompatible with council timeouts. Current M1 = `gpt-5.2-pro` (3.6s). Kimi also removed — connection failures, replaced by DeepSeek-V3.2. Full notes: `~/docs/solutions/consilium-api-latency-benchmark.md`.
- **Before adding any new model to the council:** run `consilium --quick --quiet "name a color" > ~/tmp/consi-speedtest.txt` and check per-model timings. Any model >60s does not belong in rotation. Also run `pondus check "<model>" --format table` to verify pricing — `-pro` reasoning variants can cost 10-12x more than base.
- **Two spend streams to monitor:** OpenRouter (`stips`) + OpenAI direct (`platform.openai.com/usage`). Responses API models (gpt-5.4-pro etc.) bypass OpenRouter and burn the direct OPENAI_API_KEY — invisible in stips. Keep OpenAI direct budget cap at $20.
- **402 = OpenRouter out of credits.** Tell Terry to top up at openrouter.ai/credits. Do not retry or proceed.
- **403 on a new model = access restricted (allowlist-gated).** Test before upgrading: `consilium --quick --quiet "test" 2>&1 | grep -i "403\|error"`. Swap to an available model or remove from rotation.

---

## Reference

Extended docs in `~/skills/consilium/REFERENCE.md`:
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

- Repository: https://github.com/terry-li-hm/consilium
- Related: `/judex` (measurable outcomes), `/ask-llms` (alias)
- Lessons: `[[Frontier Council Lessons]]`
- Research: `~/docs/solutions/multi-llm-deliberation-research.md`
