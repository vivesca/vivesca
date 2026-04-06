# mtor API Reference

> **mtor** — architect-implementer dispatch for AI coding agents.
> Smart model plans, cheap model builds.

Version **0.1.0** · MIT license · requires Python ≥ 3.11

---

## Table of Contents

1. [CLI Commands](#cli-commands)
   - [mtor-pkg run](#mtor-pkg-run)
   - [mtor-pkg log](#mtor-pkg-log)
   - [mtor-pkg doctor](#mtor-pkg-doctor)
2. [Configuration (`mtor.toml`)](#configuration-mtortoml)
3. [Python API — Public Classes](#python-api--public-classes)
   - [MtorConfig](#mtorconfig)
   - [ProviderConfig](#providerconfig)
   - [ProviderCommand](#providercommand)
   - [TaskResult](#taskresult)
   - [LogEntry](#logentry)
   - [StallSignal](#stallsignal)
4. [Python API — Functions](#python-api--functions)
   - [Worker](#worker)
   - [Providers](#providers)
   - [Log](#log)
   - [Dispatch](#dispatch)
   - [Stall Detection](#stall-detection)
   - [Coaching Injection](#coaching-injection)
   - [Reflection Capture](#reflection-capture)
5. [Architecture Overview](#architecture-overview)

---

## CLI Commands

All commands are available via the `mtor-pkg` entry point or `python -m mtor`.

### `mtor-pkg run`

Run a single coding task on an AI provider.

```
mtor-pkg run PROMPT [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `PROMPT` | yes | The task description to send to the agent |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--provider` | `-p` | auto-routed | Force a specific provider by name |
| `--config` | `-c` | auto-discovered | Path to a `mtor.toml` config file |

**Behavior:**

1. Loads config (from `--config`, `./mtor.toml`, or `~/.config/mtor/mtor.toml`).
2. Classifies the prompt into a task type (`explore`, `bugfix`, `test`, or `build`) via keyword matching.
3. Routes to the best provider unless `--provider` is given.
4. Prepends coaching notes (if configured) to the prompt.
5. Executes the provider's CLI harness in a subprocess.
6. Detects stalls, captures reflections, counts files created.
7. Appends a JSONL entry to the log file.
8. Prints a JSON summary to stdout and exits with the provider's exit code.

**Output (stdout, JSON):**

```json
{
  "ok": true,
  "provider": "zhipu",
  "duration": 42,
  "files_created": 3,
  "stall": "none",
  "task_type": "build",
  "routed_provider": "zhipu",
  "reflection": "clean run — would add type hints next time"
}
```

**Exit codes:** propagated from the provider subprocess. `124` = timeout, `127` = harness not found.

---

### `mtor-pkg log`

Query the structured task log.

```
mtor-pkg log [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--count` | `-n` | 20 | Number of recent entries to show |
| `--stalls` | — | off | Show only stalled tasks |
| `--reflections` | — | off | Show only tasks with reflections |
| `--stats` | — | off | Print aggregate statistics as JSON |
| `--config` | `-c` | auto-discovered | Path to a `mtor.toml` config file |

**Tabular output** (default):

```
2025-04-06T14:22:01Z  zhipu      OK                   42s  files=3
2025-04-06T14:30:15Z  droid      FAIL(stall=built-nothing) 180s  files=0
```

**Stats output** (`--stats`):

```json
{
  "total": 45,
  "success": 38,
  "failed": 7,
  "stalled": 3,
  "avg_duration": 67,
  "success_rate": "84%"
}
```

---

### `mtor-pkg doctor`

Validate configuration and check that API keys are set.

```
mtor-pkg doctor [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | auto-discovered | Path to a `mtor.toml` config file |

**Output (stdout, JSON):**

```json
{
  "ok": true,
  "coaching_file": "/home/user/germline/coaching.md",
  "providers": [
    {
      "provider": "zhipu",
      "model": "glm-5.1",
      "harness": "claude",
      "has_key": true
    }
  ]
}
```

---

## Configuration (`mtor.toml`)

mtor reads a TOML config file from (in order): the `--config` path, `./mtor.toml`, or `~/.config/mtor/mtor.toml`.

```toml
[mtor]
default_provider = "zhipu"
workdir = "."
log_file = "mtor.jsonl"
coaching_file = "coaching.md"

[providers.zhipu]
url = "https://open.bigmodel.cn/api/paas/v4"
model = "glm-5.1"
key_env = "ZHIPU_API_KEY"
concurrency = 4
harness = "claude"

[providers.droid]
url = "https://api.openai.com/v1"
model = "gpt-4.1"
key_env = "OPENAI_API_KEY"
harness = "codex"

[providers.goose]
url = "https://api.anthropic.com"
model = "claude-sonnet-4-20250514"
key_env = "ANTHROPIC_API_KEY"
harness = "goose"

[providers.gemini]
url = "https://generativelanguage.googleapis.com"
model = "gemini-2.5-pro"
key_env = "GEMINI_API_KEY"
harness = "gemini"

[hooks]
pre_task = "echo 'starting task'"
post_task = "echo 'task done'"
```

### Section Reference

#### `[mtor]` — Runtime settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_provider` | string | first provider defined | Provider to use when auto-routing fails |
| `workdir` | string | `"."` | Working directory for subprocess execution |
| `log_file` | string | `"mtor.jsonl"` | Path to the JSONL task log |
| `coaching_file` | string | `null` | Path to a markdown file prepended to every prompt |

#### `[providers.<name>]` — Provider endpoints

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `url` | string | required | API base URL |
| `model` | string | required | Model identifier |
| `key_env` | string | `"<NAME>_API_KEY"` | Environment variable holding the API key |
| `concurrency` | int | `4` | Max parallel tasks for this provider |
| `harness` | string | `"claude"` | CLI harness type: `claude`, `codex`, `gemini`, `goose`, or `droid` |

#### `[hooks]` — Lifecycle hooks (optional)

String values; shell commands run at the named lifecycle point. Currently reserved for future use.

---

## Python API — Public Classes

### `MtorConfig`

*(module: `mtor.config`)*

Top-level configuration container. Loaded from `mtor.toml`.

```python
from mtor.config import MtorConfig

cfg = MtorConfig.load()                    # auto-discover
cfg = MtorConfig.load(Path("mtor.toml"))   # explicit path
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `coaching_file` | `Path \| None` | `None` | Coaching notes to prepend to prompts |
| `workdir` | `Path` | `Path.cwd()` | Subprocess working directory |
| `log_file` | `Path` | `Path("mtor.jsonl")` | JSONL log path |
| `providers` | `dict[str, ProviderConfig]` | `{}` | Named provider configurations |
| `default_provider` | `str` | `""` | Fallback provider name |
| `hooks` | `dict[str, str]` | `{}` | Lifecycle hook commands |

**Class methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `load` | `(path: Path \| None = None) -> MtorConfig` | Find and parse config. Falls back through `path → ./mtor.toml → ~/.config/mtor/mtor.toml → empty`. |

---

### `ProviderConfig`

*(module: `mtor.config`)*

A single LLM provider endpoint.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Provider identifier (matches TOML key) |
| `url` | `str` | required | API base URL |
| `model` | `str` | required | Model identifier |
| `key_env` | `str` | required | Env var name for the API key |
| `concurrency` | `int` | `4` | Max parallel tasks |
| `harness` | `str` | `"claude"` | CLI harness: `claude`, `codex`, `gemini`, `goose`, `droid` |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `api_key` | `str \| None` | Reads `os.environ[self.key_env]`. `None` if unset. |

---

### `ProviderCommand`

*(module: `mtor.providers`)*

Resolved CLI command ready for `subprocess.run`.

| Field | Type | Description |
|-------|------|-------------|
| `args` | `list[str]` | CLI arguments (e.g. `["claude", "--print", ...]`) |
| `env` | `dict[str, str]` | Full environment including API keys |
| `timeout` | `int` | Wall-clock timeout in seconds |

---

### `TaskResult`

*(module: `mtor.worker`)*

Outcome of a single task execution.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `str` | required | Provider name that ran the task |
| `exit_code` | `int` | required | Subprocess exit code |
| `duration_seconds` | `int` | required | Wall-clock runtime |
| `output` | `str` | required | Combined stdout + stderr |
| `files_created` | `int` | `0` | Files added/modified (via `git diff`) |
| `reflection` | `str \| None` | `None` | Worker self-reflection text |
| `stall` | `StallSignal` | `StallSignal("none", "")` | Detected stall |
| `timestamp` | `str` | `""` | ISO 8601 UTC timestamp |

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_log_entry` | `() -> dict` | Serialize to a flat dict for JSONL logging |

---

### `LogEntry`

*(module: `mtor.log`)*

A single deserialized log line.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `str` | ISO 8601 UTC |
| `provider` | `str` | Provider name |
| `duration` | `int` | Seconds |
| `exit_code` | `int` | Process exit code |
| `files_created` | `int` | Files changed |
| `reflection` | `str` | Reflection text |
| `stall` | `str` | Stall type string |
| `tail` | `str` | Last 200 chars of output |

**Class methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `from_dict` | `(data: dict) -> LogEntry` | Construct from a deserialized JSON object |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `succeeded` | `bool` | `exit_code == 0` |
| `is_stalled` | `bool` | `stall` is not `""` or `"none"` |

---

### `StallSignal`

*(module: `mtor.stall`)*

A classified stall event.

| Field | Type | Description |
|-------|------|-------------|
| `stall_type` | `str` | `"none"`, `"self-reported"`, `"monologue"`, or `"built-nothing"` |
| `detail` | `str` | Human-readable explanation |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_stalled` | `bool` | `stall_type != "none"` |

---

## Python API — Functions

### Worker

*(module: `mtor.worker`)*

#### `run_task`

```python
def run_task(prompt: str, provider: ProviderConfig, config: MtorConfig) -> TaskResult
```

Execute a coding task on a provider. Steps:

1. Inject coaching notes into the prompt.
2. Build the provider CLI command.
3. Run as a subprocess with stdin=/dev/null.
4. Count files created via `git diff`.
5. Capture reflection and stall reports from `/tmp/`.
6. Return a `TaskResult`.

Raises no exceptions — all failures are captured in `TaskResult.exit_code`.

#### `log_result`

```python
def log_result(result: TaskResult, log_file: Path) -> None
```

Append a JSONL entry to `log_file`. Creates parent directories as needed.

---

### Providers

*(module: `mtor.providers`)*

#### `build_command`

```python
def build_command(provider: ProviderConfig, prompt: str, timeout: int = 7200) -> ProviderCommand
```

Build the CLI invocation for a given harness type. Sets appropriate environment variables and flags for each supported harness:

| Harness | CLI command | Key env var |
|---------|------------|-------------|
| `claude` | `claude --print --dangerously-skip-permissions -p <prompt>` | `ANTHROPIC_API_KEY` |
| `codex` | `codex exec --dangerously-bypass-approvals-and-sandbox <prompt>` | `OPENAI_API_KEY` |
| `gemini` | `gemini --sandbox=false --yolo -p <prompt>` | `GEMINI_API_KEY` |
| `goose` | `goose run -q --no-session --provider anthropic --model <model> -t <prompt>` | `ANTHROPIC_API_KEY` |
| `droid` | `droid exec --auto full -m <model> <prompt>` | `<NAME>_API_KEY` |

Raises `ValueError` if `api_key` is unset or the harness is unknown.

---

### Log

*(module: `mtor.log`)*

#### `read_log`

```python
def read_log(log_file: Path, limit: int = 50) -> list[LogEntry]
```

Read the last `limit` entries from a JSONL log file. Returns `[]` if the file doesn't exist. Malformed lines are skipped silently.

#### `filter_stalls`

```python
def filter_stalls(entries: list[LogEntry]) -> list[LogEntry]
```

Return only entries where `is_stalled` is `True`.

#### `filter_reflections`

```python
def filter_reflections(entries: list[LogEntry]) -> list[LogEntry]
```

Return only entries with non-empty `reflection` text.

#### `summary_stats`

```python
def summary_stats(entries: list[LogEntry]) -> dict
```

Compute aggregate statistics. Returns:

```python
{
    "total": int,
    "success": int,
    "failed": int,
    "stalled": int,
    "avg_duration": int,      # seconds
    "success_rate": str,      # e.g. "84%"
}
```

When `entries` is empty, returns zeros (no `success_rate` key).

---

### Dispatch

*(module: `mtor.dispatch`)*

#### `detect_task_type`

```python
def detect_task_type(prompt: str) -> str
```

Classify a prompt by keyword matching. Returns one of: `"explore"`, `"bugfix"`, `"test"`, or `"build"` (default).

| Task type | Trigger keywords |
|-----------|-----------------|
| `explore` | `how does`, `find `, `search `, `what is`, `explain`, `where is`, `list all`, `show me` |
| `bugfix` | `fix `, `bug`, `broken`, `error `, `failing`, `crash`, `regression` |
| `test` | `write test`, `add test`, `test for`, `coverage` |
| `build` | *(anything else)* |

#### `ROUTE_TO_PROVIDER`

Default routing table:

```python
{
    "explore": "droid",
    "bugfix":  "goose",
    "build":   "zhipu",
    "test":    "zhipu",
}
```

#### `ROUTE_PATTERNS`

The keyword patterns used by `detect_task_type`. Dict of `task_type → list[str]`.

---

### Stall Detection

*(module: `mtor.stall`)*

#### `detect_stall`

```python
def detect_stall(
    *,
    exit_code: int,
    duration_seconds: int,
    output_length: int,
    files_created: int,
    self_report: str | None = None,
) -> StallSignal
```

Classify a task outcome. Decision tree:

| Condition | `stall_type` | Description |
|-----------|-------------|-------------|
| `self_report` is non-empty | `"self-reported"` | Worker wrote to `/tmp/mtor-stall.txt` |
| `exit_code == 0` | `"none"` | Task succeeded |
| `files_created == 0` and `duration > 60s` and `output > 5000` and `duration > 300s` | `"monologue"` | Agent talked a lot but built nothing |
| `files_created == 0` and `duration > 60s` | `"built-nothing"` | Agent ran but produced no files |
| Otherwise | `"none"` | Generic failure, no stall pattern |

#### `format_stall_marker`

```python
def format_stall_marker(provider: str, signal: StallSignal, duration: int) -> str
```

Format a one-line stall marker string for logging: `RIBOSOME_STALL: provider=... type=... duration=... signal=...`.

---

### Coaching Injection

*(module: `mtor.coaching`)*

#### `inject_coaching`

```python
def inject_coaching(prompt: str, coaching_file: Path | None) -> str
```

If `coaching_file` exists and is non-empty, wrap its contents in `<coaching-notes>` tags and prepend to `prompt`. Returns `prompt` unchanged if the file is missing or empty.

---

### Reflection Capture

*(module: `mtor.reflection`)*

#### `capture_reflection`

```python
def capture_reflection(reflection_path: Path = REFLECTION_FILE) -> str | None
```

Read and delete `/tmp/mtor-reflection.md`. Returns content or `None` if missing/empty. The file is always unlinked after reading.

#### `capture_stall_report`

```python
def capture_stall_report(stall_path: Path = STALL_FILE) -> str | None
```

Read and delete `/tmp/mtor-stall.txt`. Same semantics as `capture_reflection`.

**Default paths:**

| Constant | Value |
|----------|-------|
| `REFLECTION_FILE` | `/tmp/mtor-reflection.md` |
| `STALL_FILE` | `/tmp/mtor-stall.txt` |

---

## Architecture Overview

```
                    mtor.toml
                       │
                       ▼
                  ┌──────────┐
                  │ MtorConfig│
                  └────┬─────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
    ▼                  ▼                  ▼
┌────────┐      ┌───────────┐      ┌──────────┐
│dispatch│      │ coaching  │      │ providers│
│        │──────│  .inject  │      │ .build_  │
│detect_ │      └───────────┘      │ command  │
│task_   │                         └────┬─────┘
│type    │                              │
└───┬────┘                              ▼
    │                           ┌──────────────┐
    │                           │ subprocess   │
    │                           │ (harness CLI)│
    │                           └──────┬───────┘
    │                                  │
    │           ┌──────────────────────┤
    │           ▼                      ▼
    │     ┌──────────┐          ┌───────────┐
    │     │  stall   │          │reflection │
    │     │ .detect_ │          │ .capture_ │
    │     │  stall   │          │  reflection│
    │     └────┬─────┘          └─────┬─────┘
    │          │                      │
    │          ▼                      ▼
    │       ┌────────────────────────────┐
    └──────►│       TaskResult           │
            └────────────┬───────────────┘
                         │
                         ▼
                   ┌───────────┐
                   │  log.py   │
                   │  mtor.jsonl│
                   └───────────┘
```

**Data flow:**

1. **Config** is loaded from `mtor.toml`.
2. **Dispatch** classifies the prompt into a task type and routes to a provider.
3. **Coaching** injects feedback notes before the prompt reaches the agent.
4. **Providers** build the CLI command for the target harness.
5. **Worker** runs the subprocess, counts files, captures reflections and stalls.
6. **Log** appends a JSONL entry for downstream analysis.

**Key design decisions:**

- **No exceptions from `run_task`.** All failure modes are captured in `TaskResult.exit_code`.
- **JSONL log format.** One JSON object per line, append-only, no locking required.
- **File-based reflection.** Workers write to `/tmp/` files which are consumed and deleted by the host. This decouples the agent process from the orchestrator.
- **Keyword-based dispatch.** Routing uses simple substring matching — no LLM calls for classification, keeping latency at zero.
