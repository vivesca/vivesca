# grep -rn: Excluding Commented Lines

## Problem

`grep -v "^\s*#"` doesn't exclude Python comments when used with `grep -rn`, because the output format is:

```
src/apm/foo.py:42:    # some comment
```

The line starts with the filename, not `#`, so `^\s*#` never matches.

## Fix

Match `#` after the line number prefix:

```bash
grep -v ":[0-9]*:\s*#"
```

This correctly filters `filename:linenum:    # comment` lines.

## When This Matters

Any time you're piping `grep -rn` output to filter out comments — common when auditing codebases for live usage of a function/variable.
