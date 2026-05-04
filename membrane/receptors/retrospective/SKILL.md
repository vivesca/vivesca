---
name: retrospective
description: Post-session meta-critique. Run AFTER /cytokinesis to assess session quality, surface failure modes, observe Terry-pattern signals, and propose what to do differently next time. NOT for state consolidation (that's cytokinesis). Trigger on "/retrospective", "how did the session go", "session review", "self-assess this session", "what could we have done better".
cli: none
user_invocable: true
context: inline
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
triggers:
  - retrospective
  - how did the session go
  - session review
  - self-assess this session
  - what could we have done better
  - meta-critique
epistemics: [evaluate, learn, judge]
---

# Retrospective — Post-Session Meta-Critique

> Cytokinesis consolidates state. Retrospective consolidates *judgment about state* — what went well, what failed, what patterns emerged in the working mode, what to do differently next time. Two skills, two clean passes, run sequentially at session end.

The genome's autopoiesis principle ("detection → self-repair → self-generation") needs a feedback loop FROM CC TO Terry, not just CC consolidating session outputs. Without retrospective, the session ends with files committed and Tonus updated, but the *quality of the session itself* — and any improvements either party could make — is unobserved. Over time, sessions plateau or drift in ways neither party notices.

This skill closes that loop.

## When to Run

- **Always after `/cytokinesis`** in a wrap sequence — cytokinesis first (state), retrospective second (judgment about state).
- On demand mid-session if a phase finished and Terry wants quality assessment before moving on.
- NOT for trivial sessions (<3 substantial exchanges) — return immediately with "session too short to assess meaningfully."

## Workflow

### 1. Read the canonical session artefacts

Don't try to re-derive everything from chat memory. Read:
- `~/epigenome/chromatin/Tonus.md` — what's the post-session state?
  - **PRE-FLIGHT (mandatory):** scan Tonus `<!-- light append YYYY-MM-DD ~HH:MM -->` blocks from the past 12 hours BEFORE forming any claim about workspace state. Synapse injection ≠ comprehension — appends are the freshest substance signal and live near the bottom of a long file; CC's failure mode is to skim past them. Run `grep -A3 "light append" ~/epigenome/chromatin/Tonus.md | tail -60` if needed. Codifies the failure caught in retrospective 2026-04-28-2145 §2b: v0.21 light-append at 22:30 was loaded, in context, unread — produced 18th-instance assert-before-verifying with NEW shape (self-context blindness, not external-source negligence).
  - **Recent commits in active project domain:** before claiming what an in-flight artefact contains, run `git log --oneline -10 --since="12 hours ago"` in the relevant repo. Tonus loads substance; commits load *current state*. Both signals required at retrospective entry.
- Today's daily note (`~/epigenome/chromatin/Daily/YYYY-MM-DD.md`) — what cytokinesis already captured?
- Recent commits in epigenome + germline (`git log --since=N hours`) — what landed?
- Any new marks filed today (`ls -t ~/epigenome/marks/ | head`)

These are the ground-truth record. Retrospective judges *against* these, not against memory.

### 1.5 Cross-session pattern check (mandatory)

Single-session retrospectives can't see drift. Each session captures "this happened again" and routes a confirmed-count bump; none of them sees the pattern across retrospectives. **Read the last 3-5 retrospective files before drafting §2.**

```bash
ls -t ~/epigenome/chromatin/retrospectives/2026-*.md | head -5
tail -20 ~/epigenome/chromatin/retrospectives/_grades.md
```

Scan their §2b ("What Didn't Go Well") and §2d ("What to Do Differently") sections. Apply two checks:

**Check A — Recurring failure mode.** If the same root cause appears in §2b across 2+ recent sessions, escalate. Per-session marks aren't deterring it. Escalation paths (pick the strongest that fits):
- (a) Edit the relevant skill's SKILL.md to add a pre-emptive check at the trigger.
- (b) Add a deterministic gate in cytokinesis or a hook (synapse/axon/dendrite).
- (c) Sharpen the existing feedback mark with a more concrete trigger ("paste the verbatim sentence" beats "verify the source") and bump `protected: true`.
- (d) If (a)-(c) all fail, file a finding tagging it as "mark not deterring; needs deterministic enforcement" — the next mitosis cycle picks it up.

**Check B — Grade trend.** Read the last ~5 grades from `_grades.md`. If the trend is descending (A → B → B → B-), name the drift in §2b and identify the underlying cause. Drift across sessions on the same day usually indicates fatigue, scope creep, or a working-mode issue that single-session retrospectives won't surface.

State Check A and Check B findings inline in §2b ("What Didn't Go Well") with the cross-session evidence ("this is the 3rd retrospective today flagging X"). Don't quietly absorb them into §2d — make the recurrence visible.

**Failure mode this prevents:** retrospective protocol is self-blind. Each session's retrospective files cleanly, but the same recurring issue surfaces session after session because no retrospective compares itself to the previous ones. The 2026-04-27 verify-source pattern hit exactly this — fired reactively in 3+ sessions, captured each time, never escalated to deterministic gate. §1.5 closes the loop.

### 2. Five-section structured output

Produce a markdown file at `~/epigenome/chromatin/retrospectives/YYYY-MM-DD-HHMM.md` with five sections in this order:

#### 2a. What Went Well

Specific concrete instances, not generic praise. Each entry has a *why* — what made it work, transferable lesson if any.

- "Six-principal knockout dispatch in single batch. Why: parallel execution, independent contexts, ~30 min total. Transferable: when you have N independent reads of the same artefact, batch dispatch beats sequential."
- NOT: "Good collaboration today."

#### 2b. What Didn't Go Well

Honest CC self-criticism. What failed, what was inefficient, what nearly went wrong. Each entry has a *root cause* and a *what would prevent recurrence*.

- "I filed GREEN-LIGHT autonomously in a previous session without challenging — caused this session's reopen and 18-blocker discovery. Root cause: §10 v1 didn't have the bidirectional pressure-test. Prevention: §10 v2 (just shipped) closes this; verify it fires next time."
- NOT: "Things could have been better."

#### 2c. Terry-Pattern Observations

What did Terry do this session that's worth noting as a *pattern*, not a one-off? Both positive and negative. **Caveat:** these are observations for Terry's consideration, not corrections — Terry knows his own work better than CC does.

- "Pattern: Terry's instinct to challenge GREEN-LIGHT was load-bearing. Without that challenge, 18 BLOCKINGGs would have shipped to HSBC. Observation: when CC files a designation autonomously (GREEN-LIGHT, READY, DONE), Terry's challenge instinct catches the over-confidence — but only fires sometimes. Worth flagging this as a deliberate practice."
- "Pattern: Terry asked for the working mode to be codified ('we together become one organism'). Repeated meta-design questions across this session — unusually high meta-density. Observation: this session was a working-mode-design session as much as a paper session. Output reflects that."

#### 2d. What to Do Differently Next Time

Specific actionable suggestions for both Terry and CC. Tag each with audience: `[Claude Code]` or `[Terry]` or `[Both]`.

- `[Claude Code]` "Auto-challenge any GREEN-LIGHT / READY / DONE designation I produce, per §10 v2 protocol. Don't wait for Terry to challenge."
- `[Both]` "When meta-design density is high in a session, consider running quorate on the design itself — multiple model perspectives on the working-mode design beats single-CC + single-Terry."
- `[Terry]` "Mobile Obsidian setup is parked but would have saved 15 min of GitHub-URL friction this morning. Consider one-time investment."

#### 2e. Session Quality Grade

Single letter + 1-sentence justification. Rubric:

- **A** — Session shipped substantial work + crystallised reusable patterns + co-organism convergence worked + no near-misses
- **B** — Session shipped work + some learning + minor friction
- **C** — Session shipped work but no compounding gain
- **D** — Session burned time without shipping or learning
- **F** — Session went backwards (regressed previous work, broke things, lost trust)

Track grades in `~/epigenome/chromatin/retrospectives/_grades.md` (one line per session: date, grade, link to file). Trend matters more than any single grade.

**Slot duration caveat (added 2026-04-28-1538).** For short slots (<30 min), grade against compounding-gain-per-minute, not absolute output. A 17-min slot that cleanly grafts 3 patterns + files 1 finding is high-leverage-density even though absolute substance is low. Rubric application: drop one tier from the substance bar and replace with a clean-execution-density bar. Failure mode this prevents: B+ default for any slot under the substance threshold regardless of how cleanly it executed, which mis-incentivises long-slot framings of small-but-clean work.

### 3. Route §2d findings to durable form (mandatory, BEFORE display)

**§2d "What to Do Differently" items must be routed to durable artefacts the same turn — not left as text in the retrospective file requiring Terry to prompt.** A retrospective that surfaces "[Claude Code] do X" and stops there is a retrospective that did 50% of its job. The other 50% is making "do X" something a future session will actually encounter.

#### 3a. Ask Terry's question, then walk the layer hierarchy as the answer (mandatory)

For each `[Claude Code]` and `[Both]` item in §2d, the **orienting question** is Terry's, asked verbatim multiple times across the 28 Apr 2026 retrospective batch:

> **"Can we do something to make us more likely to do differently next time?"**

This is not rhetorical and not optional. It is the meta-question that sharpens routing. State it explicitly to yourself before routing each item, then answer it by walking the layer hierarchy below — most-likely-to-deter to least-likely-to-deter, in order.

**Two decisions this question discriminates, not one:** (a) **ship-now vs park-as-observation** — before the layer choice, there's a prior decision about whether to ship at all. Default-to-park ("marginal — one over-fire isn't yet a pattern", "ship if recurs") is the cheapest write at this layer too, and is the pattern Terry caught on 2026-04-28-1620 when items 2 and 3 of that retrospective's §2d were initially parked rather than shipped. The question fires here first: would shipping now make us more likely to do differently? If yes — ship. (b) **which layer** — once shipping, walk the hierarchy below. Both decisions face the same default-to-cheapest-write failure mode; the question discriminates against both. If you find yourself writing "park as observation, ship if recurs" without first running this test, you're failing at decision (a). Recurrence is not the threshold for shipping; expected-leverage is.

Per genome **"Hooks > programs > skills > prompts"**, mark filing is the *lowest-leverage* answer to Terry's question — it's a prompt to remember, which is what failed previously. Marks alone do not deter; this is documented (`finding_assert_before_verifying_pattern_needs_gate_28apr.md` confirmed=5, 11+ retrospectives in 24h with mark-only routing not deterring recurrence). The layer hierarchy is the answer **most likely** to make next time different:

1. **Could a hook (synapse/axon/dendrite) intercept this?** If the failure happens at a deterministic trigger point (specific tool call, specific user-message shape, specific session event), a hook can prevent it without LLM judgment. Highest leverage. Note: load-bearing hook edits need Terry's eyes per genome.
2. **Could a CLI gate fire this deterministically?** If the failure is "CC didn't notice X at decision time", extend an existing CLI (`cytokinesis gather`, `proteome search`, etc.) to compute X and surface it as a PENDING gate. Cytokinesis Gate 8 (`recent_retrospective`, added 2026-04-28) is the canonical example — judgment moved to deterministic check.
3. **Could a skill edit add a pre-flight check at the trigger?** If the failure is "the skill's instructions didn't account for case Y", edit the skill's SKILL.md to add the case explicitly with a deterministic check (read this gate, grep this file, count this thing) — not just narrative prose.
4. **Otherwise → mark.** A mark is the right answer when (a) the trigger is genuinely fuzzy (no deterministic detection exists), (b) the failure is a judgment-call regression that needs surface activation, or (c) the lesson is too new to know what shape the deterministic gate would take.

State the chosen layer inline in §2d as you display it: each item ends with `→ hook: <path>` / `→ CLI gate: <effector>:<gate>` / `→ skill edit: <path>` / `→ mark: <path>`. The hierarchy itself is the discriminator — Terry sees which layer absorbed the lesson, not just where it landed.

**Failure mode this prevents (NEW, 2026-04-28-1450; sharpened 2026-04-28-1530):** CC defaults to mark routing because marks are the cheapest write. The hierarchy walk is Terry's meta-question — "can we do something to make us more likely to do differently next time?" — codified as a mandatory pre-routing step so CC asks it without Terry's prompt. **The question is now the section's orienting prompt**, not a parenthetical: when entering §3a, the first thing CC does is state Terry's question, then answer it by walking the hierarchy. The 11+ retrospectives in 24h flagging assert-before-verifying — all routed to marks first, then escalated to gate later — would have routed straight to gate had this question been the discriminator at first capture.

#### 3b. Concrete routing table (after hierarchy walk picks a layer)

- **Recurring CC reflex miss** (verbosity, anomaly investigation, etc.) → first try CLI gate or skill edit per §3a; mark is the fallback.
- **Cross-skill working method** → epistemics file in `~/epigenome/chromatin/euchromatin/epistemics/` with `situations:` tags + `skills:` bridge. Marks alone don't fire on grep across skills; epistemics do.
- **Specific skill behavior change** → edit that skill's SKILL.md directly. Skills > marks for instructions that should fire by trigger.
- **Hook candidate detected via §3a #1** → propose to Terry (load-bearing hook edits need eyes); file as Tonus parked if not Terry-confirmed.
- **Ops / tooling discovery** → `marks/finding_*.md`.

`[Terry]` items go in the retrospective display only — Terry decides if they become anything more.

**Original failure mode this prevents:** CC produces §2d, displays it, files the retrospective, ends the wrap. Findings sit in a single file no future session reads. Next session repeats the same mistake; Terry has to point out the gap before CC routes the lessons. The 2026-04-27-1122 retrospective hit exactly this — three actionable findings sat as text until Terry asked "nothing we identified for improving future sessions?" The retrospective protocol must close this loop autonomously.

**Cap:** route the top 3 `[Claude Code]`/`[Both]` items. Routing every minor observation creates noise; the top three are the ones that change behavior. Park the rest in the retrospective text only.

State the routing inline in §2d as you display it: each item ends with `→ filed: <path>` or `→ skill edit: <path>` or `→ epistemics: <path>`. Terry sees the action with the finding, not the finding alone.

#### 3c. In-session action scan (mandatory)

After §3a/§3b routing, scan §2d items for **in-session action implications** — situations where the lesson directly applies to a deferred question, current artefact state, or carry-forward note in this session's Tonus or daily.

For each item ask: "Does this lesson apply to anything in *this* session's open state, not just future sessions?" Concrete shapes:

- **§2d says "should have done X mid-session"** → if X is still doable now (a quick call, a skill edit, a Tonus refinement), do it now. Don't file "should have done X" as future-only learning if the action is still cheap and reversible.
- **§2d says "ask Terry about Y when stuck"** → if a carry-forward in this session's Tonus is exactly the "stuck" situation Y describes, pre-load the specific Terry-question into Tonus so next session opens with the question already framed, not with the unsolved analytical loop.
- **§2d says "propagate lesson to skill Z"** → if the routing applied the lesson to skill A but the same lesson applies to skill Z, propagate now in the same wrap turn.
- **§2d says "test the new gate fires"** → if the gate is testable synthetically (CLI gate runnable, skill-edit grep-checkable), test now and confirm in §2d as `→ tested: <result>`.

State each in-session action inline in §2d with `→ applied: <what>` or `→ pre-loaded into Tonus: <what>`.

**Failure mode this prevents:** retrospective routes §2d to durable artefacts (Layer-3 enforcement) but treats them as future-only — future sessions will encounter the lesson when situations match. The current session's *open* state goes un-acted-on. The lesson sits as text in a file no future session reads until the trigger fires; meanwhile the carry-forward question that the lesson directly answers gets deferred to next session in vague form. Codifies failure caught in retrospective 2026-05-04-1955: Item 3's "ask Terry to state the arc when stuck on ordering" was filed as epistemics but not applied to the deferred safety-within-governance question, even though that question is exactly the "stuck on ordering" situation. The action gap was visible at wrap; only Terry's challenge surfaced it.

### 4. Display Final Output to Terry

Display sections 2a–2e inline (don't make Terry open the file). Be honest, specific, brief. Each section <150 words. Total output ≤800 words. §2d items must show their routing destination per §3.

### 5. File the retrospective + commit

`~/epigenome/chromatin/retrospectives/YYYY-MM-DD-HHMM.md` + append grade line to `_grades.md`. Auto-commit to epigenome. The §3 routing artefacts (marks, skill edits, epistemics) get their own commits per "atomic commits" genome rule — don't bundle.

## Anti-Patterns

- **Generic praise.** "Good session, nothing to improve" = useless. If the session was genuinely flawless, say so once and move on; don't pad.
- **Sycophantic Terry-pattern observations.** "Terry made great calls all session" — if true, flag the *one* call that was sharpest, don't blanket. If not true, say what you saw honestly.
- **CC-self-flagellation.** Equally useless. Honest assessment ≠ performative humility. If CC did well, say so; if CC failed, say what specifically and why.
- **Repeating cytokinesis output.** Cytokinesis lists what was done; retrospective judges *how well* it was done. If you're re-listing files committed, you're doing cytokinesis-not-retrospective.
- **Suggestions Terry can't action.** "Be more careful next time" is not actionable. "Add a pre-commit hook that checks X" is.
- **Skipping the grade.** The single letter forces honest assessment. Without it, retrospective drifts into hedged "things were complicated" prose. Grade first, justify briefly.

## Boundaries

- **Not a postmortem of bugs.** Use `etiology` for root-cause-of-bug analysis. Retrospective is whole-session quality.
- **Not a substitute for cytokinesis.** Retrospective doesn't write Tonus, doesn't append daily note, doesn't run housekeeping. Run `/cytokinesis` first.
- **Not for ongoing work.** Retrospective happens at *end* of session/phase. For mid-session quality checks, use `examen` (premise audit) or `redarguo` (one-line adversarial challenge).

## See Also

- `cytokinesis` — runs first; consolidates state. Retrospective judges what cytokinesis consolidated.
- `examen` — premise audit; mid-task, not end-of-session.
- `autophagy` — coach mode; mid-task pushback.
- `feedback_co_organism_convergence_higher_confidence.md` — the working-mode principle this skill operationalises (Terry instinct + CC critique → higher-confidence position).
- `induction` §10 v2 — three-layer rule capture; retrospective findings can produce candidate rules that get methylated via this protocol.
