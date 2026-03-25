# Railway Deployment Reference

## Debugging Builds

**Always read the build log before diagnosing locally.** `railway up` prints a build log URL — open it. Or:

```bash
railway up --detach                          # deploy, get deployment ID
railway logs --build <deployment_id>         # stream build log
railway logs                                 # stream runtime log
railway status                               # current deployment state
```

Silent failures that only show in build logs:
- `apt-get install` of a renamed/missing package (exits 0 but package not installed)
- Python import errors at container startup (WeasyPrint, Pillow system deps)
- `uv sync` resolution failures

## Deploying

```bash
railway login                                # browser OAuth — expires; re-run if 401
railway up --detach                          # deploy current dir, non-blocking
railway up                                   # deploy + stream logs (blocking)
railway open                                 # open dashboard in browser
```

## Logs

```bash
railway logs                                 # runtime logs (last 100 lines)
railway logs --build <id>                    # build log for specific deployment
railway logs -n 200                          # more lines
```

## Environment / Variables

```bash
railway variables                            # list all env vars for current service
railway variables set KEY=value              # set a variable
railway variables delete KEY                 # delete a variable
```

## Volumes

Railway volumes are persistent across restarts but **wiped on volume re-creation**.

- Check if volume is mounted: `railway variables` → look for volume mount path
- If data is lost after deploy: the volume may have been detached and re-created
- Always have a seed script ready: `python3 tools/seed_corpus.py`

## Gotchas

- **`railway login` expires.** If you get 401/403 on `railway up`, re-login.
- **Debian Bookworm package renames.** `python:3.11-slim` uses Bookworm (since ~2024). Package names changed: `libgdk-pixbuf2.0-0` → `libgdk-pixbuf-2.0-0`. Check Bookworm package names at packages.debian.org before adding apt deps.
- **WeasyPrint / system lib deps.** Top-level `import weasyprint` crashes app startup if `libgobject-2.0-0` is missing. Use lazy import inside the function that needs it.
- **`uv sync --frozen` for reproducible builds.** Pins exact versions from `uv.lock`. Without `--frozen`, uv may resolve newer versions that break things.
- **Volume data survives restarts but not re-deploys that recreate the volume.** Test with `railway logs` after deploy to confirm data is still there.
- **Cold start latency.** Railway free/hobby tier sleeps services after inactivity. First request after sleep can take 10–30s. Always warmup before a demo.
- **HTTP timeout is tight.** Railway's default request timeout is ~30s for some plan tiers. Long-running operations (LLM extraction, embedding) need a client-side timeout longer than Railway's.

## Dockerfile Patterns

```dockerfile
# Use uv for reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Bookworm apt packages (not Bullseye names)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libgobject-2.0-0 \
    && rm -rf /var/lib/apt/lists/*
```

## Related

- Lacuna-specific: `~/skills/lacuna/SKILL.md`
- Bookworm package rename: `~/docs/solutions/operational/dockerfile-debian-bookworm.md`
