"""Assays for dendrite.py mod_context_rot_marker — observational error telemetry.

Test scaffolds match `spec-context-rot-hook.md` §Tests. Ribosome implements per spec.
Tests use monkeypatch to redirect log path to tmp_path and exercise the module
function directly with synthetic PostToolUse payloads.
"""

import pytest


@pytest.fixture
def captured_log(tmp_path, monkeypatch):
    """Redirect context-rot.log to tmp_path. Return the log file path."""
    del tmp_path, monkeypatch
    pytest.skip("Ribosome implements: monkeypatch the log path constant in dendrite.py")


def test_success_does_not_log(captured_log):
    """Payload with no error indicator → log is empty/absent."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_is_error_true_logs_invocation_error(captured_log):
    """tool_response.is_error=True → tool_invocation_error."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_nonzero_exit_code_logs_result_error(captured_log):
    """exit_code=1, no is_error → tool_result_error."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_timeout_classified(captured_log):
    """stderr 'Command timed out after 30s' → timeout."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_stderr_error_pattern_logs(captured_log):
    """stderr 'Error: file not found', no is_error/exit_code → tool_result_error."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_log_format_tsv_four_fields(captured_log):
    """Log line has exactly 4 tab-separated fields, ISO-8601 timestamp parses."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_session_id_propagated(captured_log):
    """session_id='abc123' in payload → log line contains 'abc123'."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_session_id_missing_uses_unknown(captured_log):
    """session_id missing → log line contains 'unknown'."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_hook_never_raises(captured_log):
    """Pathological payload (None, missing keys, non-dict response) → no exception."""
    del captured_log
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")


def test_directory_created_if_missing(tmp_path, monkeypatch):
    """Log path's parent directory does not exist → first call creates it."""
    del tmp_path, monkeypatch
    pytest.skip("Ribosome implements per spec-context-rot-hook.md")
