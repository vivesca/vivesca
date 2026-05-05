---
name: telophase
description: Full session-end cycle — composes /cytokinesis (state consolidation) and /retrospective (judgment about state). The wrap protocol skill. Use when ending a substantive session and want both halves of the wrap fired in sequence. Trigger on "/telophase", "/wrap", "wrap up properly", "full wrap", "end of session".
cli: none
user_invocable: true
context: inline
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Skill
triggers:
  - telophase
  - wrap
  - wrap up properly
  - full wrap
  - end of session
epistemics: [evaluate, learn]
---

# Telophase — Full Session-End Cycle

In biology, telophase is the late phase of mitosis: chromosomes have segregated to opposite poles, the nuclear envelope reforms around each set, the cell prepares to split. The reformation step that lets the daughter cells return to normal interphase activities — preparing for the next cycle.

This skill applies the same hierarchy to session wrap: **telophase = the full session-end reorganisation**, of which cytokinesis (the actual cytoplasmic split + state-consolidation step) is the final mechanical action. The other action is retrospective — the reflection that closes the loop between sessions.

Naming note: `mitosis` is taken (the monthly-review skill, parallel audits across body-system metaphors). Telophase fits the session-wrap function more precisely — it's specifically the *end* of one cycle and *preparation* for the next.

## When to Run

- End of any substantive session (>30 min of work, multiple substantial outputs).
- When Terry says "wrap up", "/wrap", "/telophase", "end of session", "full wrap" without specifying just one half.
- NOT for trivial sessions (<3 substantial exchanges) — neither cytokinesis nor retrospective adds value at that scale.

### Thin-session branch — prefer checkpoint

If the session was a **thin ops session** — pure routing work (file inbound message, log a contact, capture a single artefact, append to an existing thread) with no substantive decisions, no new abstractions, no working-mode discoveries — **prefer `/cytokinesis checkpoint`** to full telophase. Heuristics for "thin":

- Total session duration <30 min
- Output: <5 files, all routine (meeting notes, profile interlinks, daily-note appends)
- No skill edits, no epistemics edits, no mark edits beyond mechanical filing
- No challenges, debates, or convergence work — Terry guided, CC executed
- Retrospective grade trend would be B at best (no compounding strategic gain available)

Why: the retrospective's value is judgment about *substantive* state — what worked in deciding, what failed in convergence, what Terry-pattern emerged. Pure routing sessions don't generate enough signal to fill the five sections meaningfully; the result is padded retrospectives that dilute the grade trend.

**Deterministic pre-flight check (mandatory, replaces "when in doubt, ask"):** before invoking `/cytokinesis`, run `cytokinesis gather` and inspect the `recent_retrospective` gate **plus** the `substantive_arc` signal:

- **`substantive_arc: true`** (commits ≥2 OR new marks ≥1 since prior retrospective) → **run full `/telophase`**. Substance signal overrides the time gate; the slot's work is non-trivial regardless of how recently the prior retrospective filed. **Do NOT override `substantive_arc: true` with chat-context judgment** ("but it feels like a thin polish slot", "21 min ago, two link tweaks"). The deterministic gate's job is precisely to overrule that vibe-based read; if you're tempted to override, default to trusting the gate. The 2026-05-05-1510 instance — recommended checkpoint when gate said full telophase, retrospective was warranted on substance grounds — codifies this. State the gate's reading verbatim when proposing the path; do not editorialise around it.
- **`substantive_arc: false` AND recent retrospective <4h ago** → **default to `/cytokinesis checkpoint`** (skip retrospective) and confirm with Terry:

  > "Recent retrospective filed `<X>h` ago, no substantive arc since (`<C>` commits, `<M>` new marks). Defaulting to thin checkpoint mode (skip retrospective). Confirm: `checkpoint` or `full telophase`?"

- **Otherwise** (no recent retrospective today) → **full `/telophase`** is the default.

Codifies two failure modes:
1. Retrospective 2026-04-28-1450 §2d — over-fire on thin continuation (original gate fixed this).
2. Retrospective 2026-04-28-1620 §2d — under-fire on substantive continuation (shape-only gate over-applied; now resolved via substance signal — `cytokinesis gather` computes commits-since-retro + new-marks-since-retro and exposes `substantive_arc`).

The deterministic gate fires automatically rather than relying on CC noticing post-wrap or substantive-arc signals.

## Workflow

Two skills, run sequentially. Each is a complete skill in its own right; telophase just chains them.

### Step 1 — `/cytokinesis` (state consolidation)

Invoke the cytokinesis skill via the Skill tool. It owns: outstanding work completion, verification pass, §1a six substance-capture questions, audit signal, publish check, housekeeping (anatomy refresh, TODO archive), Tonus rewrite, daily note append, hard gate verify.

Wait for cytokinesis to complete (Tonus + daily note written, all gates DONE except explicit bypasses).

### Step 2 — `/retrospective` (judgment about state)

Invoke the retrospective skill via the Skill tool. It reads the canonical session artefacts (Tonus, daily note, recent commits, new marks) and produces the five-section structured output: What Went Well / What Didn't Go Well / Terry-Pattern Observations / What to Do Differently Next Time / Session Quality Grade.

The retrospective writes its own file to `~/epigenome/chromatin/retrospectives/YYYY-MM-DD-HHMM.md` and appends a grade line to `_grades.md`.

### Step 3 — Display + close

Display the retrospective output inline (per retrospective skill §3). End the wrap.

## Why a Composition Skill, Not a Merge

Cytokinesis and retrospective have different triggers ("wrap up" vs "how did session go") and different verbs (consolidate state vs judge state). Per genome same-trigger-one-skill rule, they stay separate. But 90% of session-end invocations want both. Telophase exists for that 90% case — one trigger, both skills fire.

The 10% case where you want only one:
- Mid-session checkpoint without retrospective: invoke `/cytokinesis` directly.
- Phase-end retrospective without state wrap: invoke `/retrospective` directly.
- Session-end full wrap: invoke `/telophase` (or its `/wrap` alias).

## Wrap-as-Verification, Not Insulation

Continuous capture during the session is the default per genome Session Capture rule. Telophase is verification of continuous capture, not insulation against next-session amnesia. The ideal telophase has nothing left to do — every signal has already been routed to its destination during the session, every correction filed, every state change in Tonus.

If telophase is producing significant new work (filing many late marks, rewriting Tonus from scratch, finding many missed signals), that's a signal the *session* failed at continuous capture — not that the wrap saved you. Treat high telophase output as a session-quality concern, not a wrap-quality success.

This reframes the failure mode: don't fear-drive the wrap. Continuous capture during the session means next session calibrates from Tonus + marks + skills + epistemics regardless of how thorough the wrap was.

## Anti-Patterns

- **Don't duplicate work between the two skills.** Cytokinesis writes Tonus + daily note. Retrospective READS them and judges. If retrospective is rewriting Tonus, something is wrong.
- **Don't skip the gate verification.** Cytokinesis has a hard gate (`cytokinesis verify` returns `all_passed`). Retrospective should not run if cytokinesis bypassed mandatory gates without rationale.
- **Don't fear-drive the wrap.** Continuous capture is the default; telophase is verification. The ideal telophase has nothing left to do.

## Boundaries

- Not a state-transfer skill (use `legatum` for explicit context bequest before session death).
- Not a checkpoint skill (use `/cytokinesis checkpoint` for verification-only mid-session).
- Not a meta-critique-only skill (use `/retrospective` directly for that).
- Not the monthly review (that's `/mitosis` — different skill, different scope, parallel body-system audits).

## See Also

- `cytokinesis` — step 1 of telophase. Standalone for checkpoint mode.
- `retrospective` — step 2 of telophase. Standalone for phase-end critique.
- `mitosis` — monthly review (different skill, name-collision avoided). Parallel audits + cross-domain synthesis.
- `legatum` — explicit context bequest for session death. Different from telophase (which is graceful end).
- Genome §Session Wrap Protocol — codifies the telophase composition.
