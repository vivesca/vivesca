## mtor coaching (starter template)

### Code Patterns
- **No hallucinated imports.** Only import functions that already exist.
- **Preserve return types.** Don't flatten distinct result classes into one generic.

### Execution Discipline
- **Read the original file fully** before rewriting.
- **Detect your own stalls.** If you've made the same tool call 3+ times with the same result, STOP. Write `STALL: <reason>` to `/tmp/mtor-stall.txt`.
- **After changes, ALWAYS commit.** Uncommitted work is invisible work.
- **Write a reflection after committing.** Create `/tmp/mtor-reflection.md` with 3-5 lines on what was harder than expected.
