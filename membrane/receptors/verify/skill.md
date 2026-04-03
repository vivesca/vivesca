---
name: verify
description: "Hard gate: run verification before claiming completion. Evidence before assertions. Applied automatically — not user-invoked."
user_invocable: false
---

# Verify Before Claiming

Evidence before assertions. If you haven't run the command in this message, you cannot claim it passes.

## The Gate

Before ANY completion claim, positive status, or satisfaction expression:

1. **Identify** — what command proves this claim?
2. **Run** — execute it fresh (not from memory, not from a prior turn)
   - If the command cannot run (missing tool/dependency/env), mark verification as blocked and do not claim success.
3. **Read** — full output, exit code, failure count
4. **Confirm** — does the output actually support the claim?
5. **Only then** — state the claim with evidence

## Proportional Verification

Not every task needs a full test suite. Match verification to stakes:

| Stakes | Verify with | Example |
|--------|-------------|---------|
| Production/client code | Full test suite + build + lint | `pytest && pnpm build` |
| Feature branch | Tests for changed code | `pytest tests/test_auth.py` |
| Personal project deploy | Confirm deploy succeeded + spot-check | `vercel --prod` output, load the URL |
| Script/config change | Run it once, check output | `python3 script.py`, read result |
| CSS/UI change | Visual check — screenshot or describe what you see | Deploy, state what changed |

## Common Traps

| Trap | Reality |
|------|---------|
| "Should work now" | Run it |
| "I'm confident" | Confidence is not evidence |
| "Linter passed" | Linter is not the compiler |
| "Agent said success" | Check the diff yourself |
| "Tests passed earlier" | Earlier is not now |
| "Just a typo fix" | Typo fixes break builds constantly |

## Delegation Check

When `/delegate` or subagent completes work:
- Read the diff or changed files — don't trust the agent's summary
- Run verification yourself if the agent didn't include output
- "Agent reports success" is not evidence
- If delegated output is missing/empty, treat as unverified and rerun checks locally.

## Quality Bar

Before marking complete, ask: **"Would a staff engineer approve this?"** Not just "does it work" but "is this the right approach?" Check for:
- Hacky workarounds that should be proper fixes
- Unnecessary complexity that a simpler design would eliminate
- Patterns that diverge from the rest of the codebase without good reason

## Integration Points

- **Before `git commit`**: Have you verified the change works?
- **Before `git push`**: Have you run the test suite?
- **Before claiming a task complete**: Re-read requirements, check each one. Apply staff engineer bar.
- **Before "deployed and working"**: Load the URL, confirm the change is visible
- If deployment URL check fails, report "deploy status unverified" instead of "working."

## Red Flags in Your Own Output

Stop if you catch yourself writing:
- "Great!", "Perfect!", "Done!" before running verification
- "should", "probably", "seems to" about test/build status
- Any positive claim in the same message where you wrote code but didn't run tests

## Example

> Claim to verify: "Auth fix works."  
> Ran: `pytest tests/test_auth.py` (pass), then `pnpm build` (pass).  
> Evidence supports claim; safe to mark complete.
