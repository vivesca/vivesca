# Verify Gate

Evidence before assertions. Run the check, read the output, then claim.

## Pattern

```
1. Do the work
2. Run verification command (test, lint, build, curl, diff)
3. READ the output — don't assume success from exit code
4. Only then claim done
```

## Rules

- Never claim "done" or "passing" without pasting evidence.
- Exit code 0 is necessary but not sufficient. Read the actual output.
- If verification fails, diagnose before retrying. Don't loop blindly.
- The verification command must test what you changed, not just that the system runs.

## Anti-patterns

- "Tests pass" without showing which tests ran
- "Deployed successfully" without checking the URL returns 200
- "Fixed the bug" without reproducing the original failure first
- Checking exit code but not output (35 STILL STALE and calling it done)

## When to use

Every skill that produces a testable outcome. Baked into: TDD, censor, contract, verification, mitogen review gates. Reference from any skill that ends with "verify."

## Source

Codified as superpowers:verification-before-completion. Regulon rules: verify-verify-your-own-verify-step, verify-no-placeholder-markers.
