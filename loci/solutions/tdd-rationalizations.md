# TDD Rationalizations Reference

Cherry-picked from [obra/superpowers](https://github.com/obra/superpowers) TDD skill (Feb 2026).

Not a hard gate — reference for when working on testable production code where TDD discipline matters.

## The Core Rule

Write the test first. Watch it fail. Write minimal code to pass. If you wrote code before the test, delete it and start over.

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing — you never saw it catch the bug. |
| "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" Different questions. |
| "Already manually tested" | Ad-hoc != systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is technical debt. |
| "Keep as reference, write tests first" | You'll adapt it. That's testing after. Delete means delete. |
| "Need to explore first" | Fine. Throw away exploration, start with TDD. |
| "Test hard = skip it" | Hard to test = hard to use. Listen to the test — simplify the design. |
| "TDD will slow me down" | TDD is faster than debugging. |
| "Manual test faster" | Manual doesn't prove edge cases. You'll re-test every change. |
| "Existing code has no tests" | You're improving it. Add tests for the code you're changing. |

## When TDD Applies

- Production services, libraries, shared code
- Bug fixes (write failing test reproducing the bug first)
- Refactoring (tests prove behaviour preserved)

## When TDD Doesn't Apply

- Throwaway scripts and prototypes
- Configuration files
- Generated code
- Quick automation/glue scripts (most of Terry's daily work)

## Red-Green-Refactor

1. **RED:** Write one failing test showing what should happen
2. **Verify RED:** Run it. Confirm it fails for the right reason (feature missing, not typo)
3. **GREEN:** Write simplest code to pass the test. Nothing extra.
4. **Verify GREEN:** Run it. All tests pass, output clean.
5. **REFACTOR:** Remove duplication, improve names. Keep tests green.
6. **Repeat.**
