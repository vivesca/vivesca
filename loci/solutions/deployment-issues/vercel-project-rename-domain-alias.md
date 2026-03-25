# Vercel project rename: CLI deprecated, API required, domain not auto-added

## Problem

Renaming a Vercel project to get a cleaner `.vercel.app` URL requires multiple steps that aren't obvious.

## What doesn't work

- `vercel --name newname` — deprecated flag, ignored
- `vercel project rm` — doesn't accept `--yes`, interactive only

## What works

1. **Rename via API:**
   ```bash
   TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/Library/Application Support/com.vercel.cli/auth.json'))['token'])")
   curl -X PATCH "https://api.vercel.com/v9/projects/old-name" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "new-name"}'
   ```

2. **Add the new `.vercel.app` domain** (not automatic after rename):
   ```bash
   curl -X POST "https://api.vercel.com/v9/projects/new-name/domains" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "new-name.vercel.app"}'
   ```

3. **Update local `.vercel/project.json`** — change `projectName`

4. **Redeploy** — `vercel --prod` to activate the new alias

## Key gotcha

The rename alone doesn't create `newname.vercel.app`. You must explicitly add it as a domain via the API. Without step 2, the new URL returns 404.

## Auth token location (macOS)

`~/Library/Application Support/com.vercel.cli/auth.json` — not the commonly-guessed `~/.local/share/` or `~/.config/` paths.

---

# Vercel dual-project domain split: naked vs www serve different deployments

## Problem (ERR-20260307-001)

After adding a custom domain to a project, the naked domain (`consilium.sh`) and `www` subdomain can end up pointing at **two separate Vercel projects** — one current, one stale. New routes return 200 on `www` but 404 on the naked domain.

## Diagnosis

```bash
vercel alias ls | grep consilium
# Reveals: consilium.sh → old-deployment-id (different project)
#          www.consilium.sh → current-deployment-id
```

Also visible via `vercel project ls` — two projects with overlapping domain coverage.

## Fix

1. Remap the stale alias to the current deployment:
   ```bash
   vercel alias set <current-deployment-id>.vercel.app consilium.sh
   ```

2. Prevent recurrence — add `alias` array to `vercel.json` so every `vercel --prod` claims both:
   ```json
   {
     "alias": ["consilium.sh", "www.consilium.sh"]
   }
   ```

## Root cause

A second Vercel project (`consilium-site`) was created at some point and claimed `consilium.sh`. When `consilium-web` was deployed, it only aliased `www.consilium.sh`. The two projects diverged silently.
