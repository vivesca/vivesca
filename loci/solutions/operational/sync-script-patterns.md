
## rsync --delete + content filtering don't compose (LRN-20260312-001)

**Problem:** If you rsync source → dest with `--delete`, then remove files from dest based on content (e.g. skip stubs), the next rsync run restores the deleted files because they still exist in source.

**Fix:** Always use a staging dir:
1. rsync source → temp (no --delete)
2. Filter/transform files in temp
3. rsync temp → dest (with --delete)

This way, filtered files never reach dest, and --delete only removes files that dropped out of the filtered set. Applied to `~/code/blog/sync-from-vault.sh` Mar 12 2026.
