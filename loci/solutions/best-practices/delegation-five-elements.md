---
module: Delegation
date: 2026-02-04
problem_type: best_practice
component: delegation
symptoms:
  - "Delegate produces wrong output"
  - "Multiple round-trips to clarify requirements"
  - "Work needs significant revision"
root_cause: missing_context
resolution_type: process_change
severity: medium
tags: [delegation, opencode, codex, prompts, mollick]
---

# Effective task delegation with five elements

## Source

From Ethan Mollick's [Management as AI Superpower](https://www.oneusefulthing.org/p/management-as-ai-superpower).

## The Five Elements

A good delegation prompt includes:

### 1. Goal & Motivation

What to achieve and why. The "why" helps the delegate make judgment calls.

```
Goal: Create a skill for checking HK weather alerts
Why: So morning briefings can warn about typhoons/rainstorms
```

### 2. Boundaries

What's allowed vs. off-limits. Prevents scope creep and unsafe operations.

```
Allowed: Read from HKO API, write to ~/skills/
Off-limits: No external API keys, no browser automation
```

### 3. Acceptance Criteria

Definition of "done". Specific, verifiable conditions.

```
Done when:
- Skill returns current temperature
- Skill returns active warnings (if any)
- Works from command line: `/hko`
```

### 4. Intermediate Checkpoints

Show outline/draft before full execution. Catches misalignment early.

```
Before implementing:
1. Show proposed file structure
2. Show API endpoints you'll use
3. Get approval, then proceed
```

### 5. Self-Check List

What to verify before submitting. Eliminates round-trip inspection.

```
Before returning:
- [ ] Run the skill and show output
- [ ] Verify no hardcoded paths
- [ ] Check skill frontmatter is valid
```

## Self-Verification Pattern

Where possible, give the agent a way to verify its own work:
- Test commands to run
- Expected output format
- API keys for validation (if needed)

This eliminates a round-trip of human inspection.

## Example Prompt

```
Create a skill for HK weather alerts.

Goal: Morning briefings should warn about typhoons/rainstorms.
Boundaries: Use HKO public API only. No browser automation.
Done when: `/hko` returns current temp + any active warnings.

Checkpoint: Show me the API endpoints and file structure before coding.

Self-check:
- Run the skill and show sample output
- Verify frontmatter has name, description
- Confirm no hardcoded API keys
```
