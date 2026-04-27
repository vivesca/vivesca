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
- `~/Tonus.md` — what's the post-session state?
- Today's daily note (`~/epigenome/chromatin/Daily/YYYY-MM-DD.md`) — what cytokinesis already captured?
- Recent commits in epigenome + germline (`git log --since=N hours`) — what landed?
- Any new marks filed today (`ls -t ~/epigenome/marks/ | head`)

These are the ground-truth record. Retrospective judges *against* these, not against memory.

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

Specific actionable suggestions for both Terry and CC. Tag each with audience: `[CC]` or `[Terry]` or `[Both]`.

- `[CC]` "Auto-challenge any GREEN-LIGHT / READY / DONE designation I produce, per §10 v2 protocol. Don't wait for Terry to challenge."
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

### 3. Display Final Output to Terry

Display sections 2a–2e inline (don't make Terry open the file). Be honest, specific, brief. Each section <150 words. Total output ≤800 words.

### 4. File the retrospective + commit

`~/epigenome/chromatin/retrospectives/YYYY-MM-DD-HHMM.md` + append grade line to `_grades.md`. Auto-commit to epigenome.

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
