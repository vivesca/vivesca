# GitHub Pages 404: workflow vs legacy build mode

## Problem

After enabling GitHub Pages via `gh api`, the site returns 404 even though the repo has an `index.html` on main.

## Cause

Pages defaults to "workflow" build mode (GitHub Actions) when enabled via API. If there's no `.github/workflows/` deploying pages, nothing gets built.

## Fix

Switch to legacy (branch-based) mode:

```bash
gh api repos/OWNER/REPO/pages -X PUT -f "build_type=legacy" -f "source[branch]=main" -f "source[path]=/"
```

Then trigger a build manually:

```bash
gh api repos/OWNER/REPO/pages/builds -X POST
```
