---
name: dokime
description: GARP RAI exam quiz with adaptive focus on weak areas. "garp quiz", "quiz me", "rai quiz"
user_invocable: true
model: sonnet
status: retiring
retire_after: 2026-04-04
disable-model-invocation: true
---

# GARP Quiz

Daily quiz skill for GARP RAI exam prep (Apr 4, 2026). Three components:

1. **Skill** (this file) — question generation, evaluation, pedagogy. LLM-judgment work.
2. **CLI** (`melete`) — FSRS scheduling, session planning, atomic state updates. Deterministic work.
3. **Data** — `~/code/epigenome/chromatin/GARP RAI Quiz Tracker.md` (human-readable stats + history) and `~/code/epigenome/chromatin/.garp-fsrs-state.json` (FSRS scheduling state). Source material in `~/code/epigenome/chromatin/GARP RAI Module {1-5} - Raw Content.md`.

**Model: Sonnet.** Formulaic skill — Opus is overkill.

## Trigger

- "garp quiz", "quiz me", "rai quiz", "study quiz"
- `/dokime` or `/dokime 5` (number = question count)
- `/dokime mock` for timed mock exam

## Workflow

### 1. Get Session Plan

Run the CLI to get a complete session plan:

```bash
melete session [N]
```

This outputs:
- Overall stats and phase info
- Recent misses (show these to user as priming)
- Question list with: topic, mode (drill/free-recall/MCQ), accuracy rate, source file + line range, `[drill]` tag if Definition Drills entry exists

**If CLI fails**, fall back: read `~/code/epigenome/chromatin/GARP RAI Quiz Tracker.md` + `~/code/epigenome/chromatin/.garp-fsrs-state.json` manually.

### 2. For Each Question: Read Source → Generate → Present → Evaluate → Record

**Read source material** (read at least two before generating; if a file is missing, skip it and use the next available source):

**IMPORTANT: All source files must be read using absolute paths (`/Users/terry/code/epigenome/chromatin/...`), never `~/code/epigenome/chromatin/...`. Bash grep fails silently on paths with spaces — always use the Read or Grep tool with the full path.**

1. `/Users/terry/code/epigenome/chromatin/GARP RAI Definition Drills.md` — **mandatory when session plan shows `[drill]` tag.** Contains comparison tables, "exam trap" callouts, and "key distinction" sections. Read the relevant section and specifically test the documented trap pattern. **If a drill entry exists and you skip it, the question quality is compromised.**
2. `/Users/terry/code/epigenome/chromatin/GARP RAI Review Questions.md` — official GARP questions closest to exam voice. Search for the relevant module/chapter section and use or adapt these questions before inventing new ones.
3. `/Users/terry/code/epigenome/chromatin/GARP RAI Fairness Scenarios Drill.md` — **mandatory for M3-demographic-parity, M3-predictive-rate-parity, M3-equal-opportunity, M3-equalized-odds, M3-individual-fairness** (the 5 fairness measure topics). 10 curated scenarios with keyed answers. Use these scenarios (or variations) instead of inventing from scratch.
4. `/Users/terry/code/epigenome/chromatin/GARP RAI Practice Exam.md` — exam-style questions (save for mock/ramp phase)
5. Raw content files (from session plan `Read` path) — for generating new questions when sources 1-4 don't cover the topic

**Source selection rule:** For any topic with `[drill]` tag → must read Definition Drills + one other source. For topics without `[drill]` tag → read Review Questions + raw content.

**Before generating:** Read `~/code/epigenome/chromatin/GARP RAI Trap Patterns.md` and grep for the topic. If a pattern entry exists, the question MUST target that exact failure mode — not a generic question on the topic. This step is mandatory, not optional.

**Generate ONE question** based on the mode (CLI labels in parentheses):

- **Strict MCQ** (<60% accuracy, CLI: `drill`): Present MCQ with 4 options. Answer must match the keyed option exactly — no free-text Claude-judged evaluation. This prevents the grading loop (Claude accepting hand-wavy answers → FSRS promoting phantom knowledge). If a Definition Drills entry exists for this topic, test the documented "exam trap" specifically. **After evaluating, ask: "Why is each wrong answer wrong?" — one sentence per distractor. This increases retrieval effort and encoding depth (retrieval practice research: explaining distractors strengthens retention of related concepts).**
- **Matrix/derivation mode** (override for repeated same-scenario misses): If session miss history shows 3+ misses on a topic where the wrong answer was the same each time (same confusion, not just same topic) — skip MCQ entirely. Instead present a concrete 2×2 confusion matrix with numbers and ask the user to derive which fairness measures are satisfied or violated. No options presented — free derivation only. Record as free-recall. This applies especially to M3-fairness-measures when PRP/equalized-odds confusion is the documented failure mode.
- **Free-recall** (60-69%, CLI: `free-recall`): Present a scenario with bolded question. User types answer. "A bank notices equal approval rates but different default rates among approved applicants across groups. **Which fairness measure is violated?**"
- **Maintenance MCQ** (>=70%, CLI: `MCQ`): Lighter touch, spaced review. Present question + A-D options.
- **Hard scenario mode** (override for topics >80% across 3+ sessions, especially M5 governance topics for this candidate): Skip standard MCQ. Present a scenario with an embedded governance/process error and ask: "What went wrong and which principle does it violate?" No options — free-form answer required. E.g., "A bank's CRO approved a new AI credit model for deployment before the model validation team had completed their review. The model outperformed the existing model in backtesting. Identify the governance failure." Tests application, not recognition. Record as free-recall.

All modes are text-only — no `AskUserQuestion`.

**Never bold or visually mark the correct option.** All four options must look identical in formatting — no bold, italics, or other hints that reveal the answer.

**Question quality rubric** (self-check before presenting):
- **One concept per question.** Don't test two things at once — if the user gets it wrong, you need to know exactly which concept failed.
- **One unambiguous keyed answer.** If two options could arguably be correct, rewrite.
- **Scenario-based where possible.** Model stems after the Practice Exam (`/Users/terry/code/epigenome/chromatin/GARP RAI Practice Exam.md`): "A bank uses...", "An analyst is...", "A company is...".
- **No attribution questions.** Never test "who coined X", "which year", or "which institution" — the exam never does this. Historical figures (Turing, Samuel, McCarthy) may appear as *context* only; the answer must turn on a concept.
- **Trap-based distractors:** If Definition Drills has an "exam trap" for this topic, at least one distractor must target that exact trap. E.g., for regularization: "both reduces AND removes features" = Elastic Net, not LASSO.
- **Option format — two valid patterns (both confirmed in Practice Exam):**
  1. **Identify-the-term questions**: options are just the term name, no explanation. E.g., "A. Sensitivity / B. Precision / C. Accuracy / D. Specificity". Use when the question tests whether you can name the right concept.
  2. **Describe-the-behaviour questions**: options are full sentences describing what something does or means. E.g., "A. Judges the morality of an action based on consequences / B. Judges the morality of an action based on adherence to duties and rules / ...". Use when the question tests whether you understand the concept.
  - **NEVER mix**: "Term — [explanation]" in a single option is always wrong. Never write "A. LASSO — removes features via L1 penalty". Either just "LASSO" or just "Removes features via L1 penalty".
- **No "all of the above" / "none of the above"** options — these are lazy and untestable.
- For M2 topics: test label-swap confusion (Ridge/LASSO/Elastic Net, normalization/standardization, self-training/co-training, RNN/LSTM/transformer, value-based/policy-based RL, transductive/inductive SSL, Agentic AI/Generative AI)
- Plausible distractors based on common misconceptions
- Vary stems: "Which of the following...", "A bank is...", "An analyst is..."

**Evaluate** the answer:
- **Ground first:** Before stating Correct/Incorrect on any self-generated question, grep the relevant raw content file or Definition Drills for the keyed answer. Do not assert correctness from general reasoning alone. If the source doesn't clearly support the keyed answer, say so and void the question rather than guess.
- State **Correct** or **Incorrect** (with right answer)
- 2-3 sentence explanation max — **for self-generated questions: mandatory GARP section citation** (e.g., "M4 section 8.6 Unpredictability Issues"); for Practice Exam / Review Questions sourced questions: cite if helpful
- If incorrect: highlight the key distinction missed
- Check `~/code/epigenome/chromatin/GARP RAI Trap Patterns.md` — name the pattern if it matches

After the user answers, infer confidence from their response:
- **C** (confident) — answered without hesitation, didn't hedge
- **U** (unsure) — hedged, qualified, or took a moment
- **G** (guess) — explicitly guessed or said they didn't know

**Record** via CLI (always include `-c`):

```bash
melete record TOPIC RATING -c C|U|G
```

- If `melete record` fails → note inline ("Would have recorded: TOPIC / RATING -c X") and continue. Reconcile at end of session with `melete reconcile`.
- `melete stats` and `melete end` flag topics where confidence=C + rating=again (overconfidence blind spots).
- **If a question was invalid** (wrong topic, bad question, attribution-style) → immediately run `melete void TOPIC` to remove the record before continuing. Use `--dry-run` first to confirm. Old entries (pre-snapshot) won't restore card state — just re-record on the next valid question.

Rating inference (from answer quality, no menu):
- **MISS** (wrong) → `again`
- **OK but brief/incomplete** → `hard`
- **OK solid** → `good`
- **OK instant/detailed** → `easy`
- **Acquisition cap:** Enforced by CLI — `good`/`easy` automatically capped to `hard` when topic is <60%. No need to manually cap; just pass the natural rating and the CLI handles it.

### 3. After Last Question

```bash
melete end
```

- If `melete end` fails → manually note "Session count not incremented — run `melete reconcile` after."

This increments the session count in the tracker. Then:
- Show score (e.g., "3/5 — 60%"), weak areas, next focus
- If any new mistake patterns emerged, append to `~/code/epigenome/chromatin/GARP RAI Trap Patterns.md`

## Rapid-Fire Mode

Trigger: user says "rapid fire", or after 2+ label-swap misses in same session.

One-line description → user names the concept. 5-8 questions, no FSRS recording. Source from `GARP RAI Definition Drills.md` (concept distinctions) and `GARP RAI Glossary.md` (acronyms). Example:

```
**R1.** Equal true positive rates across groups?  →  Equal opportunity
**R2.** L1 penalty, can zero out coefficients?  →  LASSO
**R3.** Local, model-agnostic, fits simple model around one prediction?  →  LIME
```

## Mock Exam Mode

Trigger: `/dokime mock` or "mock exam"

- 20 questions, 30 minutes, all MCQ regardless of topic accuracy
- Mixed topics weighted toward M3/M4/M5, no two consecutive from same module
- No explanations during mock — just "Noted." after each answer
- Track time every 5 questions. At 30 min: stop, unanswered = MISS
- Debrief after: score, all misses with explanations, weakest module, trend vs overall rate

## Key Files

- **Quiz tracker:** `~/code/epigenome/chromatin/GARP RAI Quiz Tracker.md`
- **FSRS state:** `~/code/epigenome/chromatin/.garp-fsrs-state.json`
- **Review questions:** `~/code/epigenome/chromatin/GARP RAI Review Questions.md` — official GARP questions, first choice for sourcing
- **Fairness scenarios:** `~/code/epigenome/chromatin/GARP RAI Fairness Scenarios Drill.md` — 10 curated scenarios with keyed answers
- **Definition drills:** `~/code/epigenome/chromatin/GARP RAI Definition Drills.md` — comparison tables + exam traps for weak topics
- **Practice exam:** `~/code/epigenome/chromatin/GARP RAI Practice Exam.md`
- **Trap patterns:** `~/code/epigenome/chromatin/GARP RAI Trap Patterns.md`
- **Glossary:** `~/code/epigenome/chromatin/GARP RAI Glossary.md` — acronyms (useful for rapid-fire)
- **Raw content:** `~/code/epigenome/chromatin/GARP RAI Module {1-5} - Raw Content.md` — verbatim from GARP portal, verified complete Mar 2026
- **GARP portal:** `https://garplearning.benchprep.com/app/rai26` — login flow + navigation gotchas: `~/code/vivesca/loci/solutions/garp-portal-navigation.md`
- **CLI:** `melete` — `session`, `record`, `end`, `today`, `due`, `stats`, `topics`, `coverage`, `reconcile`

## Boundaries

- Do NOT explain concepts beyond 2–3 sentences per question — this is a quiz, not a lecture.
- Do NOT skip FSRS recording to "save time" — phantom knowledge is worse than no session.
- Do NOT run in mock mode unless explicitly triggered — it disables explanations and disrupts normal FSRS flow.

## Notes

- Keep explanations concise — quiz, not lecture
- One session = one conversation (context snowballs)
- `/compact` between sessions if doing multiple in one conversation
- **Check before nagging:** Before suggesting "do a GARP quiz" in any daily/todo/morning rundown, run `melete today` and check if quota is met. If met, skip the suggestion. The `melete session` command also shows a quota banner automatically.
