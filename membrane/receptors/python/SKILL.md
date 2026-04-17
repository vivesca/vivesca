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

**Name via quorate (mandatory):**

```bash
consilium "Name a new Python CLI tool that does X. Latin or Greek preferred. Check PyPI availability." --quick
```

Check PyPI availability: `pip index versions <name>` or search pypi.org. Name collision = full rename cost.

### Full CLI checklist (canonical vivesca shape)

Every mature package in the organism (`porin`, `mtor`, `cyclin`, `roster`) has these pieces. Apply all of them when starting any new CLI that's more than a single file:

1. **`src/<name>/__init__.py`** — single-file package lives here; grows into submodules later if needed
2. **`assays/` not `tests/`** — biology-first naming. Flat structure, one file per concern
3. **`CLAUDE.md` at repo root** — architecture diagram, command table, conventions, gotchas, testing commands. See template below
4. **Dynamic version** via `[tool.hatch.version]` reading `__version__` from `__init__.py` — single source of truth
5. **`[project.urls]`** — at least `Homepage` and `Repository`; optional `Config` / `Issues`
6. **`[tool.pyright]` with `executionEnvironments`** — silences unused-fixture info hints on `assays/` at config level; no inline `# type: ignore`
7. **`.pre-commit-config.yaml`** with the standard bundle (see below)
8. **`porin` + `cyclopts`** — every command takes `--json` emitting a porin envelope
9. **Hypothesis property tests** for any command with invariants (diff, filter, aggregate)
10. **Golden-path integration test** that runs every command in sequence against fake data
11. **Conventional commits** — `feat:` / `fix:` / `refactor:` / `test:` / `docs:` / `chore:`
12. **Atomic commits** — never `git add -A`, always stage specific files

### pyproject.toml template (full shape)

```toml
[project]
name = "<name>"
dynamic = ["version"]
description = "<one line>"
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
authors = [{ name = "Terry Li" }]
keywords = ["<domain>", "cli"]
dependencies = [
  "cyclopts>=4.0",
  "porin>=0.3",
]

[project.urls]
Homepage = "https://github.com/terry-li-hm/<name>"
Repository = "https://github.com/terry-li-hm/<name>"

[project.scripts]
<name> = "<name>:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.version]
path = "src/<name>/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["src/<name>"]

[dependency-groups]
dev = [
  "hypothesis>=6.0",
  "pytest>=9.0",
  "ruff>=0.7",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "B", "UP", "RUF", "SIM"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"

[tool.pytest.ini_options]
testpaths = ["assays"]
pythonpath = ["src"]

[tool.pyright]
include = ["src/<name>"]
executionEnvironments = [
  { root = "assays", reportMissingImports = "none", reportUnusedParameter = "none" },
]
```

Put `__version__ = "0.1.0"` at the top of `src/<name>/__init__.py` and `[tool.hatch.version]` reads it. Bump there, everywhere else follows.

### Pre-commit bundle (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.10
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: detect-private-key

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest -q
        language: system
        pass_filenames: false
        stages: [pre-commit]
```

**Optional sensitive-term guard.** If the repo deals with employer or client data, add a `pygrep` hook blocking the sensitive term (case-insensitive). Use a single-char class in the regex so the hook config itself doesn't self-trigger:

```yaml
  - repo: local
    hooks:
      - id: no-sensitive-term
        name: "Block sensitive term in tracked content"
        language: pygrep
        entry: '(?i)c[a]pco'  # change to your term; single-char class avoids self-trigger
        types: [text]
        exclude: '^\.pre-commit-config\.yaml$'
```

Install with `pre-commit install` after first commit.

### CLAUDE.md template

Every new repo gets a `CLAUDE.md` at the root, modeled on `mtor/CLAUDE.md` and `roster/CLAUDE.md`. Sections:

1. **One-paragraph intro** — what it is, who uses it (usually just you), private or public
2. **Architecture** — ASCII diagram of data flow and directory layout
3. **Commands** — markdown table of every `app.command`, one-line purpose each
4. **Conventions** — 3-8 rules specific to this codebase (e.g., "every command builds its own filtered view `r`", "column names always through `_q()` quoter")
5. **Code patterns to match when adding a command** — numbered recipe for the most common extension
6. **Gotchas** — learned-the-hard-way pitfalls. One bullet per incident (matplotlib backend, ruff RUF001 unicode hyphens, pre-commit hook self-trigger, etc.)
7. **Testing** — commands to run the full gate: `uv run pytest`, `ruff check`, `pre-commit run --all-files`
8. **Install** — on a fresh machine, how to get from git clone to working CLI
9. **Related** — links to sibling repos (config repo, private companion, etc.)
10. **Commit style** — conventional prefixes + `Co-Authored-By` trailer

Exemplar: https://github.com/terry-li-hm/roster/blob/master/CLAUDE.md

### First commit

```bash
git init
git add -A  # allowed ONCE at project init before there's anything sensitive
git commit -m "feat: initial scaffold"
pre-commit install
gh repo create <name> --private --source=. --push
```

After this, every commit uses explicit file paths, never `git add -A`.

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

### Testing patterns (three layers)

Any CLI that passes a handful of commands through real data should carry three kinds of test. Hand-written tests alone let drift-through-understanding bugs slip in — they only cover cases you thought to write.

**1. Hand-written unit tests per command** — one file per concern (`test_<command>.py`), one function per edge case. Happy path + one failure path + one missing-data path is the floor. Use fixtures (`tmp_path`, `monkeypatch`) to isolate.

**2. Hypothesis property-based tests for invariants.** For any command with a mathematical invariant (filter monotonicity, set-partition laws, aggregation sums), generate random valid inputs and assert the invariant holds. Catches logic errors hand-written tests miss because you only write tests for failure modes you already understand.

```python
from hypothesis import HealthCheck, given, settings, strategies as st

@given(old=_roster_list(), new=_roster_list())
@settings(max_examples=40, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_diff_partition_invariants(old, new):
    """Joiners, leavers, and stayers always form a valid partition."""
    joiners = {r.id for r in new} - {r.id for r in old}
    leavers = {r.id for r in old} - {r.id for r in new}
    stayers = {r.id for r in old} & {r.id for r in new}
    assert joiners.isdisjoint(leavers)
    assert joiners.isdisjoint(stayers)
    assert leavers.isdisjoint(stayers)
```

Add `hypothesis>=6.0` to dev deps, and `.hypothesis/` to `.gitignore` — it's the shrinking database, local state only.

**3. Golden-path integration test.** Single test that runs every command in sequence against a small fake dataset. If wiring between commands breaks, this fails before unit tests do. Don't scrape output — assert filesystem side effects (files exist, sizes correct) and exit codes.

```python
def test_golden_path_every_command_runs_in_sequence(data_dir, tmp_path):
    roster.init(force=False, json=False)
    roster.snapshot(src_csv, force=False, json=False)
    roster.list_(json=False)
    roster.diff(from_=None, to=None, filter_="none", json=False)
    # ... every command in sequence
    out_csv = tmp_path / "slice.csv"
    roster.export(snapshot=None, filter_="none", out=out_csv, json=False)
    assert out_csv.exists()
```

See `~/code/roster/assays/test_properties.py` for the canonical shape.

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

## Motifs
- [verify-gate](../motifs/verify-gate.md)
