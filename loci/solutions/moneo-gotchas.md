# moneo gotchas

## Use UUID or pattern for rm/edit, not numeric index

`moneo rm <index>` used to silently delete whatever was at that display position. Display indices shift after each deletion, so batch operations would hit the wrong items. **Fixed Mar 20:** moneo now shows UUID prefixes in `moneo ls` and accepts them in `rm`/`edit`. Numeric indices still work but require confirmation.

Prefer: `moneo rm "Daily epistula"` (pattern) or `moneo rm v1gaB76W` (UUID prefix).
Avoid: `moneo rm 5` (index — shifting, fragile).

## Pattern matching in rm is substring, case-insensitive

`moneo rm "epistula"` matches any reminder containing "epistula". Good for targeting. Be specific enough to avoid multi-match.
