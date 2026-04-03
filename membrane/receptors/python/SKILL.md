---
name: python
description: "Python development — new script/package scaffold, uv workflow, PyPI publish checklist. Use when starting or publishing Python work."
user_invocable: true
triggers:
  - python
  - new
  - dev
  - publish
  - scaffold
  - package
  - pypi
  - uv
---

# Python

Three modes: **new** (scaffold), **dev** (daily workflow), **publish** (PyPI checklist). Pick the one that matches where you are.

## Triggers

- `/python new <name>` — scaffold a new script or package
- `/python dev` — daily workflow reminders
- `/python publish` — PyPI publish checklist
- `/python` with no args — ask which mode

---

## Mode: New

### What are you building?

| Type | Use when |
|------|----------|
| **Single-file script** | Personal automation, LaunchAgent, one-off CLI |
| **Package** | Publishing to PyPI, multi-file, reusable library |

---

### Single-file script

Shebang for all standalone scripts:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "httpx",
#   "rich",
# ]
# ///
```

- **`.zshenv` not `.zshrc`** for env vars (sourced in non-interactive shells)
- **LaunchAgent scripts must use `uv run --script`** — never `.venv/bin/python` (breaks on uv upgrades). Must include `--python 3.13`.
- **`PYTHONUNBUFFERED=1`** in plist environment for log visibility under `nohup`
- **Symlinked scripts:** use `Path(__file__).resolve().parent` to get real directory, not symlink location

---

### Package (PyPI / multi-file)

```bash
uv init <name>          # creates pyproject.toml, src layout
cd <name>
uv add httpx rich       # add deps
```

**pyproject.toml essentials:**

```toml
[project]
name = "<name>"
version = "0.1.0"
description = "<one line>"
requires-python = ">=3.13"
license = { text = "MIT" }

[project.scripts]
<name> = "<name>:main"   # CLI entry point

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Name via consilium (mandatory):**

```bash
consilium "Name a new Python CLI tool that does X. Latin or Greek preferred. Check PyPI availability." --quick
```

Check PyPI availability: `pip index versions <name>` or search pypi.org. Name collision = full rename cost.

---

## Mode: Dev

### Commands

```bash
uv run <script.py>            # run with inline deps resolved
uv add <package>              # add dep (updates pyproject.toml + lockfile)
uv remove <package>           # remove dep
uv upgrade                    # upgrade all deps
uv sync                       # sync venv to lockfile
ruff check .                  # lint
ruff check . --fix            # auto-fix
ruff format .                 # format
```

### Testing

```bash
uv run pytest                 # run tests
uv run pytest -x              # stop on first failure
uv run pytest --tb=short      # concise tracebacks (prefer over default)
uv run pytest -n auto         # parallel (requires pytest-xdist)
```

**Recommended pytest plugins:**

```bash
uv add --dev pytest-cov pytest-xdist pytest-asyncio pytest-mock
```

- `pytest-cov` — coverage reports (`--cov=src --cov-report=term-missing`)
- `pytest-xdist` — parallel test runs (`-n auto`)
- `pytest-asyncio` — async test support; add `asyncio_mode = "auto"` to `pyproject.toml`
- `pytest-mock` — mocker fixture (cleaner than `unittest.mock`)

**`asyncio_mode` config (if using pytest-asyncio):**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**Don't mix pytest-asyncio and pytest-anyio** — they conflict.

### Type checking

```bash
uv add --dev pyright          # recommended for new projects
uv run pyright                # run type check
```

- **pyright** — recommended over mypy for new projects (faster, stricter, better LSP)
- **mypy** — still valid for existing codebases with mypy config
- **ty** (Astral, Dec 2025) and **pyrefly** (Meta) — emerging Rust-based alternatives; not production-ready yet, watch them

### Dependency health

```bash
uv add --dev deptry
uv run deptry .               # find unused/missing deps
```

### Tool install

```bash
uv tool install <name>               # install CLI tool globally
uv tool install --reinstall <name>   # update (--reinstall enforced by hook)
```

**`uv tool install --force` is hook-blocked** — must use `--reinstall`.

### Agent-native design

If the script will be called by agents (not just humans):

```python
import sys

is_tty = sys.stdout.isatty()

if is_tty:
    # Pretty output: colours, progress bars, tables (rich)
else:
    # Plain output: newline-delimited, no ANSI, machine-parseable
```

TTY = human signal. Non-TTY = agent consumer. Design for both.

---

## Mode: Publish (PyPI)

### Pre-publish checklist

```bash
ruff check .                  # zero lint errors
ruff format --check .         # formatting clean
uv run pyright                # type check (if pyright configured)
uv run deptry .               # unused/missing deps
uv run pytest                 # tests pass
uv build                      # builds dist/ — check for errors
```

### Publish (manual)

```bash
uvx twine upload dist/*       # NOT uv publish — it doesn't read ~/.pypirc
```

**`uv publish` doesn't read `~/.pypirc`** — always use `uvx twine upload dist/*` for manual publish.

### Publish (CI — Trusted Publishing)

For GitHub Actions, skip `.pypirc` entirely. Use [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) — no API token needed:

```yaml
- uses: astral-sh/setup-uv@v5
- run: uv sync --locked
- run: uv build
- uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://upload.pypi.org/legacy/
```

Configure once on PyPI: project → Publishing → Add publisher (GitHub repo + workflow name).

### After publish

```bash
pip install <name>            # verify clean install from PyPI
uv tool install <name>        # verify CLI entry point works
```

Bump version in `pyproject.toml` before publishing. `uv` doesn't have a `cargo-release` equivalent — bump manually or use `bump2version`.

---

## Gotchas

### uv
- **`uv publish` ignores `~/.pypirc`** — use `uvx twine upload dist/*` (manual) or Trusted Publishing (CI)
- **`uv tool install --force` hook-blocked** — use `--reinstall`
- **`--extra-index-url` semantics differ from pip** — uv prefers the primary index; private packages need to be on the primary or use `[[tool.uv.sources]]` in `pyproject.toml`
- **`UV_COMPILE_BYTECODE=1`** — set this in production/serverless deploys (Docker, Lambda); uv skips bytecode compilation by default for speed, but cold starts suffer without it
- **Strict `.whl` validation** — uv rejects wheels that pip accepts. If a dep fails: `uv add --no-binary <pkg>` to force source build, or pin an older version
- **`uv sync --locked`** — use in CI (fails if lockfile is out of sync); plain `uv sync` will update

### ruff
- **Not a full pylint replacement** — ruff lacks cross-file semantic analysis. Catches most issues; deep logic errors need manual review
- **Trailing comma edge case** — ruff's formatter differs from Black on trailing commas in some multi-line expressions; don't blindly adopt both formatters in the same project
- **`preview = true` in CI** — don't. Preview rules are unstable and will break CI on ruff upgrades. Keep `preview` off in `pyproject.toml`

### General
- **LaunchAgent + uv** — use `uv run --script` with `--python 3.13`; never `.venv/bin/python`
- **`.zshenv` not `.zshrc`** — env vars for non-interactive shells (cron, LaunchAgent, agent shells)
- **`PYTHONUNBUFFERED=1`** — required for `nohup` log visibility
- **Symlinked scripts** — `Path(__file__).resolve().parent` for actual directory
- **Package manager** — always `uv`, never `pip install` directly into global env. pnpm for Node.
- **Credential access in agent shells** — keychain locked in separate security session. Use `_keychain("service-name")` helper; `security` commands don't inherit unlocks from tmux

## Rust vs Python: when to use which

- **Rust:** CLI tools others install, performance-critical, single binary distribution, crates.io
- **Python:** Prototyping, AI/ML (PyTorch/numpy), glue code, LaunchAgents, anything uv-heavy
- **Key insight:** "Python is faster to write" is irrelevant when Claude writes it. Optimise for the end product.
