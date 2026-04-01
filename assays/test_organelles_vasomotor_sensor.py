"""Tests for metabolon.organelles.vasomotor_sensor."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

from metabolon.organelles import vasomotor_sensor


class TestGetOauthToken:
    """Tests for get_oauth_token()."""

    def test_reads_valid_token_from_credentials_file(self, tmp_path):
        """Returns token when credentials file has valid, unexpired token."""
        future_ts = int(datetime.now(UTC).timestamp() * 1000) + 3600000  # 1hr future
        creds_data = {"claudeAiOauth": {"accessToken": "test-token-123", "expiresAt": future_ts}}

        with patch.object(
            vasomotor_sensor, "_CREDENTIALS_FILE", tmp_path / ".credentials.json"
        ):
            (tmp_path / ".credentials.json").write_text(json.dumps(creds_data))
            result = vasomotor_sensor.get_oauth_token()

        assert result == "test-token-123"

    def test_raises_when_token_expired(self, tmp_path):
        """Raises RuntimeError when token is past expiration."""
        past_ts = int(datetime.now(UTC).timestamp() * 1000) - 1000  # 1s ago
        creds_data = {"claudeAiOauth": {"accessToken": "expired-token", "expiresAt": past_ts}}

        with patch.object(
            vasomotor_sensor, "_CREDENTIALS_FILE", tmp_path / ".credentials.json"
        ):
            (tmp_path / ".credentials.json").write_text(json.dumps(creds_data))
            with pytest.raises(RuntimeError, match="expired"):
                vasomotor_sensor.get_oauth_token()

    def test_raises_when_credentials_file_missing(self, tmp_path):
        """Raises RuntimeError when no credentials file and no Keychain fallback."""
        with patch.object(
            vasomotor_sensor, "_CREDENTIALS_FILE", tmp_path / ".credentials.json"
        ):
            with patch.object(vasomotor_sensor.subprocess, "run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                with pytest.raises(RuntimeError, match="No OAuth token found"):
                    vasomotor_sensor.get_oauth_token()

    def test_raises_on_malformed_json(self, tmp_path):
        """Raises RuntimeError when credentials file has invalid JSON."""
        with patch.object(
            vasomotor_sensor, "_CREDENTIALS_FILE", tmp_path / ".credentials.json"
        ):
            (tmp_path / ".credentials.json").write_text("not valid json")
            with pytest.raises(RuntimeError, match="Failed to read"):
                vasomotor_sensor.get_oauth_token()

    def test_fallback_to_keychain_on_missing_file(self, tmp_path):
        """Falls back to macOS Keychain when credentials file missing."""
        future_ts = int(datetime.now(UTC).timestamp() * 1000) + 3600000
        keychain_data = {"claudeAiOauth": {"accessToken": "keychain-token", "expiresAt": future_ts}}

        with patch.object(
            vasomotor_sensor, "_CREDENTIALS_FILE", tmp_path / ".credentials.json"
        ):
            with patch.object(vasomotor_sensor.subprocess, "run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout=json.dumps(keychain_data)
                )
                result = vasomotor_sensor.get_oauth_token()

        assert result == "keychain-token"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "security" in args
        assert "Claude Code-credentials" in args

    def test_keychain_expired_token_raises(self, tmp_path):
        """Raises RuntimeError when Keychain token is expired."""
        past_ts = int(datetime.now(UTC).timestamp() * 1000) - 1000
        keychain_data = {"claudeAiOauth": {"accessToken": "expired", "expiresAt": past_ts}}

        with patch.object(
            vasomotor_sensor, "_CREDENTIALS_FILE", tmp_path / ".credentials.json"
        ):
            with patch.object(vasomotor_sensor.subprocess, "run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout=json.dumps(keychain_data)
                )
                with pytest.raises(RuntimeError, match="Keychain token expired"):
                    vasomotor_sensor.get_oauth_token()


class TestInternalizeUsage:
    """Tests for internalize_usage()."""

    def test_fetches_usage_from_api(self):
        """Makes authenticated request and returns parsed JSON."""
        api_response = {"seven_day": {"utilization": 42.5}, "seven_day_sonnet": {"utilization": 30.0}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(api_response).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(vasomotor_sensor.urllib.request, "urlopen", return_value=mock_response):
            result = vasomotor_sensor.internalize_usage("test-token")

        assert result == api_response

    def test_request_includes_auth_header(self):
        """Request includes Bearer token and required headers."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(vasomotor_sensor.urllib.request, "urlopen", return_value=mock_response) as mock_urlopen:
            vasomotor_sensor.internalize_usage("my-secret-token")

            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            # Normalize header keys to lowercase for comparison
            headers = {k.lower(): v for k, v in request.headers.items()}
            assert headers.get("authorization") == "Bearer my-secret-token"
            assert "oauth-2025-04-20" in headers.get("anthropic-beta", "")

    def test_propagates_http_error(self):
        """Propagates exception when HTTP request fails."""
        with patch.object(
            vasomotor_sensor.urllib.request, "urlopen", side_effect=Exception("network error")
        ):
            with pytest.raises(Exception, match="network error"):
                vasomotor_sensor.internalize_usage("token")


class TestReadFallback:
    """Tests for _read_fallback()."""

    def test_returns_none_when_no_files_exist(self, tmp_path):
        """Returns (None, None) when no history files exist."""
        with patch.object(vasomotor_sensor, "HISTORY_FILE", tmp_path / "history.jsonl"):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "watch.jsonl"):
                result = vasomotor_sensor._read_fallback()

        assert result == (None, None)

    def test_reads_latest_entry_from_history_file(self, tmp_path):
        """Returns most recent entry and age from history file."""
        now = datetime.now(UTC)
        ts = now.isoformat()
        entry = {"ts": ts, "metrics": {"seven_day": {"utilization": 50}}}
        history_file = tmp_path / "history.jsonl"
        history_file.write_text('{"ts": "old"}\n' + json.dumps(entry) + '\n')

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "watch.jsonl"):
                result_entry, age = vasomotor_sensor._read_fallback()

        assert result_entry == entry
        assert age is not None
        assert age >= 0

    def test_falls_back_to_watch_log(self, tmp_path):
        """Falls back to WATCH_LOG when HISTORY_FILE missing."""
        now = datetime.now(UTC)
        ts = now.isoformat()
        entry = {"ts": ts, "weekly_pct": 60}
        watch_file = tmp_path / "watch.jsonl"
        watch_file.write_text(json.dumps(entry) + '\n')

        with patch.object(vasomotor_sensor, "HISTORY_FILE", tmp_path / "history.jsonl"):
            with patch.object(vasomotor_sensor, "WATCH_LOG", watch_file):
                result_entry, age = vasomotor_sensor._read_fallback()

        assert result_entry == entry

    def test_handles_empty_file(self, tmp_path):
        """Returns (None, None) for empty history file."""
        history_file = tmp_path / "history.jsonl"
        history_file.write_text("")

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "watch.jsonl"):
                result = vasomotor_sensor._read_fallback()

        assert result == (None, None)

    def test_handles_malformed_json(self, tmp_path):
        """Skips malformed entries and returns valid one."""
        history_file = tmp_path / "history.jsonl"
        history_file.write_text('invalid json\n{"ts": "' + datetime.now(UTC).isoformat() + '"}\n')

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "watch.jsonl"):
                result_entry, _ = vasomotor_sensor._read_fallback()

        assert result_entry is not None


class TestSenseUsage:
    """Tests for sense_usage()."""

    def test_returns_live_usage_when_api_succeeds(self, tmp_path):
        """Returns usage from API with stale_age=None."""
        future_ts = int(datetime.now(UTC).timestamp() * 1000) + 3600000
        creds_data = {"claudeAiOauth": {"accessToken": "token", "expiresAt": future_ts}}
        api_response = {"seven_day": {"utilization": 40}}

        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps(creds_data))
        history_file = tmp_path / "history.jsonl"

        with patch.object(vasomotor_sensor, "_CREDENTIALS_FILE", creds_file):
            with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
                mock_response = MagicMock()
                mock_response.read.return_value = json.dumps(api_response).encode()
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)

                with patch.object(vasomotor_sensor.urllib.request, "urlopen", return_value=mock_response):
                    usage, stale = vasomotor_sensor.sense_usage()

        assert usage == api_response
        assert stale is None

    def test_falls_back_to_cache_on_api_failure(self, tmp_path):
        """Returns cached data with age when API fails."""
        history_file = tmp_path / "history.jsonl"
        now = datetime.now(UTC)
        entry = {
            "ts": now.isoformat(),
            "metrics": {
                "seven_day": {"utilization": 55, "resets_at": "2025-01-01"},
                "seven_day_sonnet": {"utilization": 40, "resets_at": "2025-01-01"},
            },
        }
        history_file.write_text(json.dumps(entry) + '\n')

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "watch.jsonl"):
                with patch.object(vasomotor_sensor, "get_oauth_token", side_effect=RuntimeError("no token")):
                    usage, stale = vasomotor_sensor.sense_usage()

        assert usage["seven_day"]["utilization"] == 55
        assert usage["seven_day_sonnet"]["utilization"] == 40
        assert stale is not None

    def test_raises_when_both_live_and_cache_fail(self, tmp_path):
        """Raises RuntimeError when API fails and no cache available."""
        with patch.object(vasomotor_sensor, "HISTORY_FILE", tmp_path / "history.jsonl"):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "watch.jsonl"):
                with patch.object(vasomotor_sensor, "get_oauth_token", side_effect=RuntimeError("no token")):
                    with pytest.raises(RuntimeError, match="Live API failed.*no cached data"):
                        vasomotor_sensor.sense_usage()

    def test_normalizes_legacy_cache_format(self, tmp_path):
        """Handles legacy cache format with weekly_pct/sonnet_pct keys."""
        history_file = tmp_path / "history.jsonl"
        now = datetime.now(UTC)
        entry = {"ts": now.isoformat(), "weekly_pct": 70, "sonnet_pct": 35}
        history_file.write_text(json.dumps(entry) + '\n')

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "watch.jsonl"):
                with patch.object(vasomotor_sensor, "get_oauth_token", side_effect=RuntimeError("fail")):
                    usage, _ = vasomotor_sensor.sense_usage()

        assert usage["seven_day"]["utilization"] == 70
        assert usage["seven_day_sonnet"]["utilization"] == 35


class TestBudgetStatus:
    """Tests for budget_status()."""

    def test_returns_safe_below_threshold(self):
        """Returns SAFE when utilization below threshold_safe."""
        usage = {"seven_day": {"utilization": 30}, "seven_day_sonnet": {"utilization": 20}}
        assert vasomotor_sensor.budget_status(usage) == "SAFE"

    def test_returns_caution_between_safe_and_caution(self):
        """Returns CAUTION when utilization between safe and caution thresholds."""
        usage = {"seven_day": {"utilization": 55}, "seven_day_sonnet": {"utilization": 10}}
        assert vasomotor_sensor.budget_status(usage) == "CAUTION"

    def test_returns_warning_between_caution_and_warning(self):
        """Returns WARNING when utilization between caution and warning thresholds."""
        usage = {"seven_day": {"utilization": 75}, "seven_day_sonnet": {"utilization": 10}}
        assert vasomotor_sensor.budget_status(usage) == "WARNING"

    def test_returns_danger_above_warning(self):
        """Returns DANGER when utilization above warning threshold."""
        usage = {"seven_day": {"utilization": 90}, "seven_day_sonnet": {"utilization": 10}}
        assert vasomotor_sensor.budget_status(usage) == "DANGER"

    def test_uses_max_of_both_metrics(self):
        """Uses maximum of seven_day and seven_day_sonnet."""
        usage = {"seven_day": {"utilization": 20}, "seven_day_sonnet": {"utilization": 88}}
        assert vasomotor_sensor.budget_status(usage) == "DANGER"

    def test_accepts_tuple_input(self):
        """Handles tuple input from sense_usage()."""
        usage = {"seven_day": {"utilization": 60}, "seven_day_sonnet": {"utilization": 10}}
        assert vasomotor_sensor.budget_status((usage, 30)) == "CAUTION"

    def test_handles_missing_keys(self):
        """Returns SAFE when keys are missing."""
        assert vasomotor_sensor.budget_status({}) == "SAFE"
        assert vasomotor_sensor.budget_status({"seven_day": {}}) == "SAFE"


class TestRecordBreath:
    """Tests for record_breath()."""

    def test_appends_to_history_file(self, tmp_path):
        """Appends JSONL entry with timestamp and metrics."""
        history_file = tmp_path / "history.jsonl"
        usage = {"seven_day": {"utilization": 45}, "seven_day_sonnet": {"utilization": 30}}

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            vasomotor_sensor.record_breath(usage)

        content = history_file.read_text().strip()
        entry = json.loads(content)
        assert "ts" in entry
        assert entry["metrics"]["seven_day"]["utilization"] == 45
        assert entry["metrics"]["seven_day_sonnet"]["utilization"] == 30

    def test_creates_parent_directory(self, tmp_path):
        """Creates parent directory if missing."""
        history_file = tmp_path / "subdir" / "history.jsonl"
        usage = {"seven_day": {"utilization": 50}}

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            vasomotor_sensor.record_breath(usage)

        assert history_file.exists()

    def test_only_includes_present_keys(self, tmp_path):
        """Only includes keys that are present in usage dict."""
        history_file = tmp_path / "history.jsonl"
        usage = {"seven_day": {"utilization": 50}}  # no sonnet

        with patch.object(vasomotor_sensor, "HISTORY_FILE", history_file):
            vasomotor_sensor.record_breath(usage)

        entry = json.loads(history_file.read_text())
        assert "seven_day" in entry["metrics"]
        assert "seven_day_sonnet" not in entry["metrics"]


class TestFormatAge:
    """Tests for _format_age()."""

    def test_formats_seconds(self):
        """Formats age under a minute as seconds."""
        assert vasomotor_sensor._format_age(30) == "30s ago"

    def test_formats_minutes(self):
        """Formats age under an hour as minutes."""
        assert vasomotor_sensor._format_age(90) == "1m ago"
        assert vasomotor_sensor._format_age(180) == "3m ago"

    def test_formats_hours(self):
        """Formats age under a day as hours."""
        assert vasomotor_sensor._format_age(7200) == "2h ago"

    def test_formats_days(self):
        """Formats age over a day as days."""
        assert vasomotor_sensor._format_age(172800) == "2d ago"


class TestSerializeStatus:
    """Tests for serialize_status()."""

    def test_serializes_full_usage(self):
        """Returns complete status dict with all fields."""
        usage = {
            "seven_day": {"utilization": 65, "resets_at": "2025-01-15T00:00:00Z"},
            "seven_day_sonnet": {"utilization": 40},
            "five_hour": {"utilization": 10},
        }
        result = vasomotor_sensor.serialize_status(usage)

        assert result["status"] == "CAUTION"
        assert result["weekly_pct"] == 65.0
        assert result["sonnet_pct"] == 40.0
        assert result["session_pct"] == 10.0
        assert result["stale"] is False
        assert result["stale_label"] is None
        assert result["resets_at"] == "2025-01-15T00:00:00Z"

    def test_marks_stale_with_age(self):
        """Sets stale=True and provides stale_label when age given."""
        usage = {"seven_day": {"utilization": 30}}
        result = vasomotor_sensor.serialize_status(usage, stale_age=120)

        assert result["stale"] is True
        assert result["stale_label"] == "2m ago"

    def test_handles_missing_five_hour(self):
        """Sets session_pct to None when five_hour missing."""
        usage = {"seven_day": {"utilization": 50}, "seven_day_sonnet": {"utilization": 30}}
        result = vasomotor_sensor.serialize_status(usage)

        assert result["session_pct"] is None


class TestSense:
    """Tests for sense() top-level entry point."""

    def test_returns_serialized_status(self, tmp_path):
        """Returns serialized status on success."""
        future_ts = int(datetime.now(UTC).timestamp() * 1000) + 3600000
        creds_data = {"claudeAiOauth": {"accessToken": "token", "expiresAt": future_ts}}
        api_response = {"seven_day": {"utilization": 40}}

        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps(creds_data))

        with patch.object(vasomotor_sensor, "_CREDENTIALS_FILE", creds_file):
            with patch.object(vasomotor_sensor, "HISTORY_FILE", tmp_path / "h.jsonl"):
                mock_response = MagicMock()
                mock_response.read.return_value = json.dumps(api_response).encode()
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)

                with patch.object(vasomotor_sensor.urllib.request, "urlopen", return_value=mock_response):
                    result = vasomotor_sensor.sense()

        assert result["status"] == "SAFE"
        assert result["weekly_pct"] == 40.0
        assert "error" not in result

    def test_returns_error_dict_on_failure(self, tmp_path):
        """Returns dict with error key on any exception."""
        with patch.object(vasomotor_sensor, "HISTORY_FILE", tmp_path / "h.jsonl"):
            with patch.object(vasomotor_sensor, "WATCH_LOG", tmp_path / "w.jsonl"):
                with patch.object(vasomotor_sensor, "get_oauth_token", side_effect=RuntimeError("no token")):
                    result = vasomotor_sensor.sense()

        assert "error" in result
        assert "no token" in result["error"]
