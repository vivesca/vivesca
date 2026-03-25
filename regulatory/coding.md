---
paths:
  - "**/*.rs"
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.go"
  - "**/*.toml"
  - "**/*.json"
---

## Implementation Quality

- **Demand elegance.** Non-trivial changes: "is there a more elegant way?" Hacky fix → "knowing everything I know now, implement the elegant solution."
- **Staff engineer bar.** Does it work AND is it the right way?
- **README sync.** Config changes → update README in same commit.

## Verification (Code-Specific)

Before ANY completion claim on code:

1. Identify the proving command
2. Run it fresh (not from memory)
3. Read full output + exit code
4. Confirm output supports claim

| Stakes | Verify with |
|--------|-------------|
| Production/client | Full test suite + build + lint |
| Feature branch | Tests for changed code |
| Script/config | Run once, check output |

**Delegation:** Read the diff yourself. "Agent reports success" is not evidence.

## Delegate-First Coding

`/nucleation` on-ramp for non-trivial coding. Trivial (<50 lines, clear spec): build in-session. `code-delegate-warn.js` hard-blocks >20 lines in `~/code/`.
