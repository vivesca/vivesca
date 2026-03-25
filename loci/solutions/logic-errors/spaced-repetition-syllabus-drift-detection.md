---
title: "Spaced Repetition Syllabus Drift — Silent Coverage Gaps in GARP RAI Quiz System"
problem_type: logic-error
component: "rai.py CLI, .garp-fsrs-state.json, GARP RAI Quiz Tracker.md, Definition Drills.md"
symptoms: "No error signal. System scheduled known topics for 33 sessions while 3 syllabus sections went completely untracked."
tags: [spaced-repetition, coverage-audit, silent-gap, fsrs, exam-prep]
date_solved: 2026-02-24
severity: high
---

# Spaced Repetition Syllabus Drift — Silent Coverage Gaps

## Problem

The GARP RAI quiz system (FSRS spaced repetition, 33 sessions, 199 questions) had been running without errors — but was missing coverage for 8% of the exam syllabus. Three entire syllabus sections had no tracked FSRS topic, and three algorithms within tracked topics had no drill entries.

**No failure signal.** The scheduler kept surfacing known topics. The gap was only discovered through a manual cross-reference audit prompted by an offhand "should we check coverage?" question.

## Gaps Found

| Gap | Type | Impact |
|-----|------|--------|
| M3 §8 Global Challenges (economic risks, inequality, misinformation) | Missing FSRS topic | Exam LO #9 completely untested |
| M5 §7 Implementation (model implementation, adaptation, misinterpretation) | Missing FSRS topic | Exam prep checklist item untested |
| M5 §8 Governance Framework Recommendations (BIS survey) | Missing FSRS topic | Distinct chapter with specific recommendations |
| KNN (M2 §4.3) | Missing drill entry within M2-regression-classification | Explicit curriculum chapter, no practice depth |
| SVM (M2 §4.4) | Missing drill entry within M2-regression-classification | Explicit curriculum chapter, no practice depth |
| Autoencoders (M2 §4.6) | Missing drill entry within M2-neural-networks | Explicit curriculum chapter, no practice depth |

## Root Cause

**No single source of truth linking syllabus to tracked topics.** Topics were added organically during quiz sessions. The FSRS state file and quiz tracker only know about topics that have been reviewed — they have no concept of "what should exist." The system optimises for *scheduling existing cards*, not *validating completeness*.

## Investigation Method

1. `rai.py topics` → exported all 34 tracked topics
2. `grep "^## "` on all 5 module raw content files → extracted every syllabus section heading
3. Read Exam Prep file for official Learning Objectives (authoritative testable scope)
4. Built mapping table: each syllabus section → which tracked topic covers it (or "NOT COVERED")
5. Delegated independent cross-check to scout subagent for verification
6. Identified 3 complete gaps + 3 algorithm depth gaps

## Solution

### Separate FSRS cards for missing Learning Objectives

Added 3 new topics to `.garp-fsrs-state.json` (FSRS `Card()` initialisation) and `GARP RAI Quiz Tracker.md` (0/0 rows). These represent syllabus sections with their own Learning Objectives — they need independent spaced repetition scheduling.

### Drill entries for algorithm depth gaps

Added 2 Definition Drills entries (KNN/SVM/Decision Trees comparison table + Autoencoders table) within parent topics. These get tested when the parent topic surfaces — no separate FSRS card needed.

### Key decision: bundle vs. split

- **Separate FSRS cards:** When a gap maps to an exam Learning Objective with no parent topic. Without a card, FSRS can never schedule it.
- **Drill entries within parent:** When the gap is depth within an already-tracked topic. Adding more cards dilutes focus; drill entries add practice without fragmenting the deck.

With 38 days to exam and 6 topics already below 60%, adding 3 cards (not 6) was the right call — close the real gaps without deck bloat.

## Prevention

### 1. Hardcode the syllabus as source of truth

Add a `SYLLABUS` list to `rai.py` — all 37 topics. The coverage audit checks tracked topics against this list. One-time setup, catches future drift immediately.

### 2. Add a `rai coverage` command

```
$ rai coverage
Syllabus: 37 topics | Tracked: 37 | Coverage: 100%

NEVER ATTEMPTED (0 sessions):
  (none)

LOW COVERAGE (<3 attempts):
  M3-global-challenges: 1 attempt (0%)
  M5-implementation: 2 attempts (50%)
```

### 3. Three audit triggers

- **After initial seeding:** Verify 100% presence before first quiz session
- **Phase transitions:** At session 10/20/30, verify all topics have been seen at least once
- **2 weeks before exam:** Final coverage audit — any 0-attempt topic is a red flag

### 4. General SRS drift pattern

Silent coverage gaps emerge in any SRS system where the topic list is managed separately from the source material:
- Scheduler only sees what's been added — it can't know what's missing
- High-accuracy topics get deprioritised, creating the illusion of broad coverage
- Monthly audits against the authoritative source (syllabus, curriculum, spec) are the cheapest prevention

## Related

- `~/docs/solutions/spaced-repetition-mode-selection.md` — mode selection (drill/free-recall/MCQ) based on accuracy tier
- `~/docs/solutions/garp-rai-cli-audit-fixes.md` — prior CLI audit (11 bug fixes, data integrity)
- `~/code/vivesca-terry/chromatin/GARP RAI Exam Prep.md` — official Learning Objectives and exam weights
- `~/code/vivesca-terry/chromatin/GARP RAI Definition Drills.md` — drill entries including new KNN/SVM/Autoencoder tables
