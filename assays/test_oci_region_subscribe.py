from __future__ import annotations

"""Tests for oci-region-subscribe — PAYG activation poller + region subscriber."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _load_module():
    """Load the effector by exec-ing its Python body (skip shebang)."""
    source = (Path.home() / "germline/effectors/oci-region-subscribe").read_text()
    ns: dict = {"__name__": "oci_region_subscribe"}
    exec(source, ns)
    return ns


_mod = _load_module()
oci = _mod["oci"]
get_subscribed_regions = _mod["get_subscribed_regions"]
subscribe_region = _mod["subscribe_region"]
notify = _mod["notify"]
main = _mod["main"]
TENANCY = _mod["TENANCY"]
REGIONS = _mod["REGIONS"]
ENV = _mod["ENV"]


# ── Constants ────────────────────────────────────────────────────────


def test_tenancy_is_ocid():
    """TENANCY starts with 'ocid1.tenancy'."""
    assert TENANCY.startswith("ocid1.tenancy.")


def test_target_regions():
    """REGIONS contains KIX, SYD, ICN."""
    assert REGIONS == ["KIX", "SYD", "ICN"]


def test_env_suppresses_label_warning():
    """ENV sets SUPPRESS_LABEL_WARNING."""
    assert ENV["SUPPRESS_LABEL_WARNING"] == "True"


# ── oci() helper ─────────────────────────────────────────────────────


@patch("subprocess.run")
def test_oci_calls_subprocess_with_args(mock_run):
    """oci() passes arguments to subprocess.run correctly."""
    mock_run.return_value = subprocess.CompletedProcess([], 0, "out", "")
    rc, out, err = oci("iam", "region-subscription", "list", "--tenancy-id", "x")
    mock_run.assert_called_once()
    args = mock_run.call_args
    assert args[0][0] == ["oci", "iam", "region-subscription", "list", "--tenancy-id", "x"]
    assert args[1]["capture_output"] is True
    assert args[1]["text"] is True
    assert args[1]["timeout"] == 300


@patch("subprocess.run")
def test_oci_returns_exit_code_and_output(mock_run):
    """oci() returns (returncode, stdout, stderr)."""
    mock_run.return_value = subprocess.CompletedProcess([], 42, "some out", "some err")
    rc, out, err = oci("test")
    assert rc == 42
    assert out == "some out"
    assert err == "some err"


# ── get_subscribed_regions() ─────────────────────────────────────────


def test_get_subscribed_regions_parses_data():
    """get_subscribed_regions extracts region-key from JSON data."""
    mock_oci = MagicMock(return_value=(0, json.dumps({"data": [
        {"region-key": "PHX"},
        {"region-key": "IAD"},
        {"region-key": "KIX"},
    ]}), ""))
    with patch.dict(_mod, {"oci": mock_oci}):
        assert get_subscribed_regions() == ["PHX", "IAD", "KIX"]


def test_get_subscribed_regions_empty_data():
    """get_subscribed_regions returns [] when data is empty."""
    mock_oci = MagicMock(return_value=(0, json.dumps({"data": []}), ""))
    with patch.dict(_mod, {"oci": mock_oci}):
        assert get_subscribed_regions() == []


def test_get_subscribed_regions_nonzero_rc():
    """get_subscribed_regions returns [] on non-zero exit code."""
    mock_oci = MagicMock(return_value=(1, "", "error"))
    with patch.dict(_mod, {"oci": mock_oci}):
        assert get_subscribed_regions() == []


def test_get_subscribed_regions_bad_json():
    """get_subscribed_regions returns [] on malformed JSON."""
    mock_oci = MagicMock(return_value=(0, "not json", ""))
    with patch.dict(_mod, {"oci": mock_oci}):
        assert get_subscribed_regions() == []


def test_get_subscribed_regions_passes_tenancy():
    """get_subscribed_regions passes TENANCY as --tenancy-id."""
    mock_oci = MagicMock(return_value=(0, json.dumps({"data": []}), ""))
    with patch.dict(_mod, {"oci": mock_oci}):
        get_subscribed_regions()
    mock_oci.assert_called_once_with(
        "iam", "region-subscription", "list", "--tenancy-id", TENANCY
    )


# ── subscribe_region() ───────────────────────────────────────────────


def test_subscribe_region_success():
    """subscribe_region returns (True, 'OK') on rc=0."""
    mock_oci = MagicMock(return_value=(0, '{"ok": true}', ""))
    with patch.dict(_mod, {"oci": mock_oci}):
        ok, msg = subscribe_region("KIX")
    assert ok is True
    assert msg == "OK"


def test_subscribe_region_payg_not_active():
    """subscribe_region detects TenantCapacityExceeded."""
    mock_oci = MagicMock(return_value=(1, "", "Error: TenantCapacityExceeded in region KIX"))
    with patch.dict(_mod, {"oci": mock_oci}):
        ok, msg = subscribe_region("KIX")
    assert ok is False
    assert msg == "PAYG not active yet"


def test_subscribe_region_other_error():
    """subscribe_region returns truncated error for other failures."""
    mock_oci = MagicMock(return_value=(1, "", "Some other error occurred"))
    with patch.dict(_mod, {"oci": mock_oci}):
        ok, msg = subscribe_region("SYD")
    assert ok is False
    assert msg == "Some other error occurred"


def test_subscribe_region_truncates_long_error():
    """subscribe_region truncates error message to 100 chars."""
    long_err = "E" * 200
    mock_oci = MagicMock(return_value=(1, "", long_err))
    with patch.dict(_mod, {"oci": mock_oci}):
        ok, msg = subscribe_region("ICN")
    assert ok is False
    assert len(msg) == 100


def test_subscribe_region_passes_region_key():
    """subscribe_region passes --region-key correctly."""
    mock_oci = MagicMock(return_value=(0, "{}", ""))
    with patch.dict(_mod, {"oci": mock_oci}):
        subscribe_region("SYD")
    mock_oci.assert_called_once_with(
        "iam", "region-subscription", "create",
        "--tenancy-id", TENANCY, "--region-key", "SYD"
    )


# ── notify() ─────────────────────────────────────────────────────────


@patch("subprocess.run")
def test_notify_calls_deltos(mock_run):
    """notify() calls deltos with the message."""
    notify("hello world")
    mock_run.assert_called_once_with(
        ["deltos", "hello world"], capture_output=True, timeout=10
    )


@patch("subprocess.run", side_effect=Exception("no deltos"))
def test_notify_swallows_exception(mock_run):
    """notify() silently ignores failures."""
    notify("this should not raise")


# ── main() — all regions already subscribed ──────────────────────────


def test_main_all_subscribed(capsys):
    """main() exits cleanly when all target regions are already subscribed."""
    mock_get = MagicMock(return_value=["PHX", "KIX", "SYD", "ICN"])
    mock_notify = MagicMock()
    with patch.dict(_mod, {"get_subscribed_regions": mock_get, "notify": mock_notify}):
        main()
    captured = capsys.readouterr()
    assert "All target regions already subscribed!" in captured.out
    mock_notify.assert_called_once_with("OCI: All regions subscribed (KIX/SYD/ICN)")


# ── main() — canary succeeds, subscribes rest ────────────────────────


def test_main_canary_success_subscribes_rest(capsys):
    """main() subscribes all regions when canary (first needed) succeeds."""
    mock_get = MagicMock(side_effect=[
        ["PHX"],                          # first call: only PHX subscribed
        ["PHX", "KIX", "SYD", "ICN"],    # final call after subscribing
    ])
    mock_sub = MagicMock(side_effect=[
        (True, "OK"),   # KIX canary
        (True, "OK"),   # SYD
        (True, "OK"),   # ICN
    ])
    mock_notify = MagicMock()
    mock_sleep = MagicMock()
    with patch.dict(_mod, {
        "get_subscribed_regions": mock_get,
        "subscribe_region": mock_sub,
        "notify": mock_notify,
        "time": MagicMock(sleep=mock_sleep, strftime=MagicMock(return_value="2026-01-01 00:00:00")),
    }):
        main()
    captured = capsys.readouterr()
    assert "SUBSCRIBED" in captured.out
    assert "Final regions" in captured.out
    mock_notify.assert_called()


# ── main() — partial failure ─────────────────────────────────────────


def test_main_partial_failure(capsys):
    """main() handles partial subscription failures gracefully."""
    mock_get = MagicMock(side_effect=[
        ["PHX"],                         # first call
        ["PHX", "KIX", "SYD", "ICN"],   # final call
    ])
    mock_sub = MagicMock(side_effect=[
        (True, "OK"),           # KIX canary succeeds
        (False, "quota error"), # SYD fails
        (True, "OK"),           # ICN succeeds
    ])
    mock_notify = MagicMock()
    mock_sleep = MagicMock()
    mock_time = MagicMock(sleep=mock_sleep, strftime=MagicMock(return_value="2026-01-01 00:00:00"))
    with patch.dict(_mod, {
        "get_subscribed_regions": mock_get,
        "subscribe_region": mock_sub,
        "notify": mock_notify,
        "time": mock_time,
    }):
        main()
    captured = capsys.readouterr()
    assert "quota error" in captured.out
    assert "Done." in captured.out


# ── main() — PAYG not active, no --loop ──────────────────────────────


def test_main_payg_not_active_no_loop(capsys):
    """main() exits 1 when PAYG not active without --loop."""
    mock_get = MagicMock(return_value=["PHX"])
    mock_sub = MagicMock(return_value=(False, "PAYG not active yet"))
    with patch.dict(_mod, {
        "get_subscribed_regions": mock_get,
        "subscribe_region": mock_sub,
        "time": MagicMock(strftime=MagicMock(return_value="2026-01-01 00:00:00")),
    }):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "PAYG not active" in captured.out


# ── main() — --help flag ─────────────────────────────────────────────


def test_main_help(capsys):
    """main() with --help prints docstring and exits 0."""
    with patch.object(sys, "argv", ["oci-region-subscribe", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Poll for PAYG activation" in captured.out


def test_main_h_flag(capsys):
    """main() with -h also prints help and exits 0."""
    with patch.object(sys, "argv", ["oci-region-subscribe", "-h"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0


# ── main() — --loop retries on PAYG not active ───────────────────────


def test_main_loop_retries_then_succeeds(capsys):
    """main() --loop retries on PAYG failure, then succeeds."""
    mock_get = MagicMock(side_effect=[
        ["PHX"],                         # attempt 1: PAYG not active
        ["PHX"],                         # attempt 2: PAYG not active
        ["PHX"],                         # attempt 3: PAYG now active
        ["PHX", "KIX", "SYD", "ICN"],   # final check
    ])
    mock_sub = MagicMock(side_effect=[
        (False, "PAYG not active yet"),  # attempt 1
        (False, "PAYG not active yet"),  # attempt 2
        (True, "OK"),                    # KIX canary attempt 3
        (True, "OK"),                    # SYD
        (True, "OK"),                    # ICN
    ])
    mock_sleep = MagicMock()
    mock_notify = MagicMock()
    mock_time = MagicMock(sleep=mock_sleep, strftime=MagicMock(return_value="2026-01-01 00:00:00"))
    with patch.dict(_mod, {
        "get_subscribed_regions": mock_get,
        "subscribe_region": mock_sub,
        "notify": mock_notify,
        "time": mock_time,
    }):
        with patch.object(sys, "argv", ["oci-region-subscribe", "--loop"]):
            main()
    captured = capsys.readouterr()
    assert "Attempt 1" in captured.out
    assert "Attempt 2" in captured.out
    assert "Attempt 3" in captured.out
    assert "SUBSCRIBED" in captured.out
    # 2 retries at 300s + 2 inter-region delays at 2s = 4 sleep calls total
    sleep_calls = list(mock_sleep.call_args_list)
    retry_calls = [c for c in sleep_calls if c == call(300)]
    assert len(retry_calls) == 2  # two 5-min retry sleeps


# ── main() — one region already subscribed ───────────────────────────


def test_main_partial_already_subscribed(capsys):
    """main() only subscribes regions not already in the list."""
    mock_get = MagicMock(side_effect=[
        ["PHX", "KIX"],                  # KIX already done
        ["PHX", "KIX", "SYD", "ICN"],   # final
    ])
    mock_sub = MagicMock(side_effect=[
        (True, "OK"),   # SYD (first needed)
        (True, "OK"),   # ICN
    ])
    mock_notify = MagicMock()
    mock_sleep = MagicMock()
    mock_time = MagicMock(sleep=mock_sleep, strftime=MagicMock(return_value="2026-01-01 00:00:00"))
    with patch.dict(_mod, {
        "get_subscribed_regions": mock_get,
        "subscribe_region": mock_sub,
        "notify": mock_notify,
        "time": mock_time,
    }):
        main()
    # subscribe_region called only for SYD and ICN (KIX already in)
    assert mock_sub.call_count == 2
    calls = [c[0][0] for c in mock_sub.call_args_list]
    assert calls == ["SYD", "ICN"]
