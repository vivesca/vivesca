---
title: Package Registry Namespace Squatting
date: 2026-02-20
category: developer-experience
module: package-registries
tags: [npm, pypi, crates-io, github, namespace, branding]
severity: low
---

# Package Registry Namespace Squatting

Reserving package names across registries before building. Useful for brand protection when you have a working project (Compound Engineering) and want to hold adjacent names.

## What Worked

**npm** — Fastest. Minimal `package.json` + empty `index.js`, `npm publish`. No rate limits encountered for 13 packages. Auth via `npm whoami`.

**PyPI** — Requires actual build step. Minimal `pyproject.toml` (hatchling backend) + `__init__.py`, then `uv build && uv publish --token <token>`. One gotcha: `uv publish` does NOT read `~/.pypirc` automatically — must pass `--token` explicitly or it errors with "Missing credentials."

**crates.io** — Most restrictive. Minimal `Cargo.toml` + `src/lib.rs`, `cargo publish --allow-dirty`. **Aggressive rate limiting**: ~5 new crates per window, then 429 with 10-minute cooldown. Publishing 13 crates required 3 batches over ~40 minutes with background retry scripts.

**GitHub orgs** — Web-only creation at `github.com/organizations/plan`. The REST API `POST /orgs` is **enterprise-only** — returns 404 for regular users. Free tier, ~30 seconds each manually.

## Batch Pattern

```bash
# npm — batch all at once, no rate limits
for name in compound-foo compound-bar; do
  cd /tmp/namesquat/npm/$name && npm publish 2>&1 | tail -1
done

# PyPI — build first, then publish with explicit token
PYPI_TOKEN=$(python3 -c "import configparser; c=configparser.ConfigParser(); c.read('$HOME/.pypirc'); print(c['pypi']['password'])")
for name in compound-foo compound-bar; do
  cd /tmp/namesquat/pypi/$name && uv build 2>&1 | tail -1 && uv publish --token "$PYPI_TOKEN" 2>&1 | tail -1
done

# crates.io — must space out, retry on 429
for name in compound-foo compound-bar; do
  cd /tmp/namesquat/crates/$name
  result=$(cargo publish --allow-dirty 2>&1)
  if echo "$result" | grep -q "429"; then
    echo "Rate limited, waiting 11 minutes..."
    sleep 660
    cargo publish --allow-dirty 2>&1
  fi
done
```

## Scaffolding (Python script creates all 3 registries at once)

See session transcript for the `python3 << 'SCRIPT'` that generates `package.json`, `pyproject.toml`, and `Cargo.toml` for N names in one pass.

## Results

13 names × 3 registries = 39 targets. 38/39 claimed (compound-data on PyPI was already taken by someone else). GitHub orgs are manual.

## npm Name-Similarity Blocking

npm rejects unscoped package names that are "too similar" to existing packages. Similarity is checked by stripping punctuation and comparing against all existing names. Example: `lustro` was blocked as too similar to `astro`, `listr`, `listr2`.

**No warning before publish** — the 404 availability check passes, but `npm publish` returns E403. The error message names the conflicting packages and suggests a scoped alternative.

**Workaround:** Publish as `@username/name` with `--access=public`. The scoped name bypasses similarity checks entirely. This is the only option — there's no appeal process.

**Implication for name selection:** Always test with `npm publish --dry-run` before committing to a name. A name that looks available via HTTP 404 check may still be blocked at publish time. PyPI and crates.io don't have this restriction.

## When This Is Appropriate

- You have a **real project** with a real name (not generic squatting)
- Reserving **adjacent brand extensions** (compound-reading, compound-thinking alongside compound-engineering)
- Packages contain actual descriptions pointing to the parent project
- You intend to either use them or deprecate/transfer if someone asks
