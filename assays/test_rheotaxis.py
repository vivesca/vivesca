"""Tests for metabolon.enzymes.rheotaxis (decomposed subcommand CLI).

Phase 0 scope: failure-path tests only. The core behavior change from the old
rheotaxis (which raised RuntimeError on any backend error) is that every
backend function must return an error ToolResult cleanly instead of raising.
These tests lock that invariant before ribosome builds the backends.

Success-path tests with HTTP mocks land per-phase alongside each backend port.

Module layout expected (does not exist yet — ribosome builds in Phases 1-5):
    src/metabolon/enzymes/rheotaxis/
        __init__.py      # MCP @tool decorator (removed in Phase 6)
        _common.py       # ToolResult dataclass, shared helpers
        brave.py         # run_brave(query, num=10) -> ToolResult
        serper.py        # run_serper(query, num=10) -> ToolResult
        tavily.py        # run_tavily(query, num=10) -> ToolResult
        jina.py          # run_jina(query, num=10) -> ToolResult
        zhipu.py         # run_zhipu(query, num=10) -> ToolResult
        cli.py           # main(argv) argparse dispatcher

Contract for each run_<backend>(query, num=10) -> ToolResult:
    - Never raises. Returns ToolResult with .error set on any failure.
    - On missing API key: returns ToolResult with .error mentioning the env var.
    - On API/network error: returns ToolResult with .error containing the cause.
    - .tool field matches the backend name.
"""

import importlib

import pytest

BACKENDS = [
    ("brave", "BRAVE_API_KEY"),
    ("serper", "SERPER_API_KEY"),
    ("tavily", "TAVILY_API_KEY"),
    ("jina", "JINA_API_KEY"),
    ("zhipu", "ZHIPU_API_KEY"),
]


def test_tool_result_dataclass_shape():
    """ToolResult must have the expected fields with sensible defaults."""
    common = importlib.import_module("metabolon.enzymes.rheotaxis._common")
    result = common.ToolResult(tool="brave", query="hello", result="some markdown")
    assert result.tool == "brave"
    assert result.query == "hello"
    assert result.result == "some markdown"
    assert result.error is None
    assert result.latency_s >= 0
    assert result.cost >= 0


@pytest.mark.parametrize(("backend", "env_var"), BACKENDS)
def test_run_backend_missing_key_returns_error_not_raises(backend, env_var, monkeypatch):
    """Every backend must return an error ToolResult when its API key is unset.

    This is the core invariant that fixes the old rheotaxis behavior of raising
    RuntimeError on any backend failure — now each backend isolates its own
    failure into a returned ToolResult.
    """
    monkeypatch.delenv(env_var, raising=False)
    module = importlib.import_module(f"metabolon.enzymes.rheotaxis.{backend}")
    run_fn = getattr(module, f"run_{backend}")

    # Must not raise
    result = run_fn("test query")

    assert result is not None
    assert result.tool == backend
    assert result.error is not None, f"{backend} must return error when key missing, not None"
    error_text = result.error.lower()
    assert "not set" in error_text or env_var.lower() in error_text, (
        f"{backend} error message should mention the env var name: got {result.error!r}"
    )


@pytest.mark.parametrize(("backend", "env_var"), BACKENDS)
def test_cli_missing_key_exits_nonzero(backend, env_var, monkeypatch):
    """CLI subcommand must exit non-zero (not 0) when API key is missing.

    Exit code 2 preferred per the plan, but any non-zero is acceptable since
    different argparse dispatchers may choose different codes for this case.
    """
    monkeypatch.delenv(env_var, raising=False)
    cli = importlib.import_module("metabolon.enzymes.rheotaxis.cli")

    with pytest.raises(SystemExit) as exc_info:
        cli.main([backend, "test query"])

    # SystemExit.code can be int or None; int non-zero is what we want
    code = exc_info.value.code
    assert code is not None and code != 0, (
        f"{backend} CLI should exit non-zero on missing key, got {code}"
    )


def test_cli_unknown_subcommand_exits_nonzero():
    """Unknown subcommands must be rejected by argparse with non-zero exit."""
    cli = importlib.import_module("metabolon.enzymes.rheotaxis.cli")
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["nonexistent_backend", "test query"])
    code = exc_info.value.code
    assert code is not None and code != 0


def test_cli_no_args_exits_nonzero():
    """CLI with no arguments must exit non-zero (argparse usage error)."""
    cli = importlib.import_module("metabolon.enzymes.rheotaxis.cli")
    with pytest.raises(SystemExit) as exc_info:
        cli.main([])
    code = exc_info.value.code
    assert code is not None and code != 0


def test_all_backend_modules_expose_run_function():
    """Each backend module must export a run_<backend> callable.

    Sanity check that the module shape matches the CLI dispatcher's
    expectations. Prevents silent drift where a backend file exists but
    names its entry function differently.
    """
    for backend, _ in BACKENDS:
        module = importlib.import_module(f"metabolon.enzymes.rheotaxis.{backend}")
        run_fn = getattr(module, f"run_{backend}", None)
        assert run_fn is not None, f"rheotaxis.{backend} must export run_{backend}"
        assert callable(run_fn), f"run_{backend} must be callable"
