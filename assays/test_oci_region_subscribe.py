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


@patch(f"{_mod['__name__']}.oci")
def test_get_subscribed_regions_parses_data(mock_oci):
    """get_subscribed_regions extracts region-key from JSON data."""
    mock_oci.return_value = (0, json.dumps({"data": [
        {"region-key": "PHX"},
        {"region-key": "IAD"},
        {"region-key": "KIX"},
    ]}), "")
    assert get_subscribed_regions() == ["PHX", "IAD", "KIX"]


@patch(f"{_mod['__name__']}.oci")
def test_get_subscribed_regions_empty_data(mock_oci):
    """get_subscribed_regions returns [] when data is empty."""
    mock_oci.return_value = (0, json.dumps({"data": []}), "")
    assert get_subscribed_regions() == []


@patch(f"{_mod['__name__']}.oci")
def test_get_subscribed_regions_nonzero_rc(mock_oci):
    """get_subscribed_regions returns [] on non-zero exit code."""
    mock_oci.return_value = (1, "", "error")
    assert get_subscribed_regions() == []


@patch(f"{_mod['__name__']}.oci")
def test_get_subscribed_regions_bad_json(mock_oci):
    """get_subscribed_regions returns [] on malformed JSON."""
    mock_oci.return_value = (0, "not json", "")
    assert get_subscribed_regions() == []


@patch(f"{_mod['__name__']}.oci")
def test_get_subscribed_regions_passes_tenancy(mock_oci):
    """get_subscribed_regions passes TENANCY as --tenancy-id."""
    mock_oci.return_value = (0, json.dumps({"data": []}), "")
    get_subscribed_regions()
    mock_oci.assert_called_once_with(
        "iam", "region-subscription", "list", "--tenancy-id", TENANCY
    )


# ── subscribe_region() ───────────────────────────────────────────────


@patch(f"{_mod['__name__']}.oci")
def test_subscribe_region_success(mock_oci):
    """subscribe_region returns (True, 'OK') on rc=0."""
    mock_oci.return_value = (0, '{"ok": true}', "")
    ok, msg = subscribe_region("KIX")
    assert ok is True
    assert msg == "OK"


@patch(f"{_mod['__name__']}.oci")
def test_subscribe_region_payg_not_active(mock_oci):
    """subscribe_region detects TenantCapacityExceeded."""
    mock_oci.return_value = (1, "", "Error: TenantCapacityExceeded in region KIX")
    ok, msg = subscribe_region("KIX")
    assert ok is False
    assert msg == "PAYG not active yet"


@patch(f"{_mod['__name__']}.oci")
def test_subscribe_region_other_error(mock_oci):
    """subscribe_region returns truncated error for other failures."""
    mock_oci.return_value = (1, "", "Some other error occurred")
    ok, msg = subscribe_region("SYD")
    assert ok is False
    assert msg == "Some other error occurred"


@patch(f"{_mod['__name__']}.oci")
def test_subscribe_region_truncates_long_error(mock_oci):
    """subscribe_region truncates error message to 100 chars."""
    long_err = "E" * 200
    mock_oci.return_value = (1, "", long_err)
    ok, msg = subscribe_region("ICN")
    assert ok is False
    assert len(msg) == 100


@patch(f"{_mod['__name__']}.oci")
def test_subscribe_region_passes_region_key(mock_oci):
    """subscribe_region passes --region-key correctly."""
    mock_oci.return_value = (0, "{}", "")
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


@patch(f"{_mod['__name__']}.notify")
@patch(f"{_mod['__name__']}.get_subscribed_regions", return_value=["PHX", "KIX", "SYD", "ICN"])
def test_main_all_subscribed(mock_regions, mock_notify, capsys):
    """main() exits cleanly when all target regions are already subscribed."""
    main()
    captured = capsys.readouterr()
    assert "All target regions already subscribed!" in captured.out
    mock_notify.assert_called_once_with("OCI: All regions subscribed (KIX/SYD/ICN)")


# ── main() — canary succeeds, subscribes rest ────────────────────────


@patch(f"{_mod['__name__']}.time.sleep")
@patch(f"{_mod['__name__']}.notify")
@patch(f"{_mod['__name__']}.get_subscribed_regions")
@patch(f"{_mod['__name__']}.subscribe_region")
def test_main_canary_success_subscribes_rest(mock_sub, mock_regions, mock_notify, mock_sleep, capsys):
    """main() subscribes all regions when canary (first needed) succeeds."""
    mock_regions.side_effect = [
        ["PHX"],          # first call: only PHX subscribed
        ["PHX", "KIX", "SYD", "ICN"],  # final call after subscribing
    ]
    mock_sub.side_effect = [
        (True, "OK"),     # KIX canary
        (True, "OK"),     # SYD
        (True, "OK"),     # ICN
    ]
    main()
    captured = capsys.readouterr()
    assert "SUBSCRIBED" in captured.out
    assert "Final regions" in captured.out
    mock_notify.assert_called()


@patch(f"{_mod['__name__']}.time.sleep")
@patch(f"{_mod['__name__']}.notify")
@patch(f"{_mod['__name__']}.get_subscribed_regions")
@patch(f"{_mod['__name__']}.subscribe_region")
def test_main_partial_failure(mock_sub, mock_regions, mock_notify, mock_sleep, capsys):
    """main() handles partial subscription failures gracefully."""
    mock_regions.side_effect = [
        ["PHX"],                         # first call
        ["PHX", "KIX", "SYD", "ICN"],   # final call
    ]
    mock_sub.side_effect = [
        (True, "OK"),           # KIX canary succeeds
        (False, "quota error"), # SYD fails
        (True, "OK"),           # ICN succeeds
    ]
    main()
    captured = capsys.readouterr()
    assert "quota error" in captured.out
    assert "Done." in captured.out


# ── main() — PAYG not active, no --loop ──────────────────────────────


@patch(f"{_mod['__name__']}.get_subscribed_regions", return_value=["PHX"])
@patch(f"{_mod['__name__']}.subscribe_region", return_value=(False, "PAYG not active yet"))
def test_main_payg_not_active_no_loop(mock_sub, mock_regions, capsys):
    """main() exits 1 when PAYG not active without --loop."""
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


@patch(f"{_mod['__name__']}.time.sleep")
@patch(f"{_mod['__name__']}.notify")
@patch(f"{_mod['__name__']}.get_subscribed_regions")
@patch(f"{_mod['__name__']}.subscribe_region")
def test_main_loop_retries_then_succeeds(mock_sub, mock_regions, mock_notify, mock_sleep, capsys):
    """main() --loop retries on PAYG failure, then succeeds."""
    mock_regions.side_effect = [
        ["PHX"],                         # attempt 1: PAYG not active
        ["PHX"],                         # attempt 2: PAYG not active
        ["PHX"],                         # attempt 3: PAYG now active
        ["PHX", "KIX", "SYD", "ICN"],   # final check
    ]
    mock_sub.side_effect = [
        (False, "PAYG not active yet"),  # attempt 1
        (False, "PAYG not active yet"),  # attempt 2
        (True, "OK"),                    # KIX canary attempt 3
        (True, "OK"),                    # SYD
        (True, "OK"),                    # ICN
    ]
    with patch.object(sys, "argv", ["oci-region-subscribe", "--loop"]):
        main()
    captured = capsys.readouterr()
    assert "Attempt 1" in captured.out
    assert "Attempt 2" in captured.out
    assert "Attempt 3" in captured.out
    assert "SUBSCRIBED" in captured.out
    mock_sleep.assert_called_with(300)
    assert mock_sleep.call_count == 2  # two retries


# ── main() — one region already subscribed ───────────────────────────


@patch(f"{_mod['__name__']}.time.sleep")
@patch(f"{_mod['__name__']}.notify")
@patch(f"{_mod['__name__']}.get_subscribed_regions")
@patch(f"{_mod['__name__']}.subscribe_region")
def test_main_partial_already_subscribed(mock_sub, mock_regions, mock_notify, mock_sleep, capsys):
    """main() only subscribes regions not already in the list."""
    mock_regions.side_effect = [
        ["PHX", "KIX"],                  # KIX already done
        ["PHX", "KIX", "SYD", "ICN"],   # final
    ]
    mock_sub.side_effect = [
        (True, "OK"),   # SYD (first needed)
        (True, "OK"),   # ICN
    ]
    main()
    # subscribe_region called only for SYD and ICN (KIX already in)
    assert mock_sub.call_count == 2
    calls = [c[0][0] for c in mock_sub.call_args_list]
    assert calls == ["SYD", "ICN"]
