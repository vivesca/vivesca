---
name: histochemistry
description: Evidence before completion claims — verify, read output, then assert.
model: sonnet
epistemics: [build, debug]
---

# Histochemistry — Stain Before Declaring

Histochemistry stains tissue to confirm what's actually there. No stain, no diagnosis.

## Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the command in this message, you cannot claim it passes.

## The Gate

```
1. IDENTIFY — what command proves this claim?
2. RUN — execute it fresh and complete
3. READ — full output, exit code, failure count
4. VERIFY — does output confirm the claim?
5. ONLY THEN — make the claim
```

Skip any step = assertion without evidence.

## What Requires What

| Claim | Requires | Not sufficient |
|-------|----------|----------------|
| Tests pass | Test output: 0 failures | Previous run, "should pass" |
| Build succeeds | Build: exit 0 | Linter passing |
| Bug fixed | Original symptom gone | Code changed, assumed fixed |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags — STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification
- About to commit/push/PR without evidence
- Trusting agent success reports without checking
- "Just this once"

## Patterns

```
CORRECT:  [run test] [see: 34/34 pass] "All tests pass"
WRONG:    "Should pass now" / "Looks correct"

CORRECT:  Agent reports success -> check diff -> verify changes
WRONG:    Trust agent report
```

## Boundary

Applies to ANY positive statement about work state — exact phrases, paraphrases, implications. Evidence before assertions, always.
