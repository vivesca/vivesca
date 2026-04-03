from __future__ import annotations

"""Tests for secretory_vesicle — Telegram export organelle."""

import json
import subprocess
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import metabolon.organelles.secretory_vesicle as sv


# ---------------------------------------------------------------------------
# _html_escape
# ---------------------------------------------------------------------------
class TestHtmlEscape:
    def test_no_special_chars(self):
        assert sv._html_escape("hello world") == "hello world"

    def test_ampersand(self):
        assert sv._html_escape("a & b") == "a &amp; b"

    def test_angle_brackets(self):
        assert sv._html_escape("<tag>") == "&lt;tag&gt;"

    def test_all_combined(self):
        assert sv._html_escape("a<b&c>d") == "a&lt;b&amp;c&gt;d"

    def test_empty_string(self):
        assert sv._html_escape("") == ""


# ---------------------------------------------------------------------------
# _keychain
# ---------------------------------------------------------------------------
class TestKeychain:
    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    def test_returns_stripped_value(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="tok123\n")
        assert sv._keychain("telegram-bot-token") == "tok123"
        mock_run.assert_called_once_with(
            ["security", "find-generic-password", "-s", "telegram-bot-token", "-w"],
            capture_output=True,
            text=True,
        )

    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    def test_raises_on_nonzero_returncode(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        with pytest.raises(ValueError, match="Keychain credential missing"):
            sv._keychain("bogus-service")

    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    def test_raises_on_empty_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="  \n")
        with pytest.raises(ValueError, match="Keychain credential missing"):
            sv._keychain("empty-service")


# ---------------------------------------------------------------------------
# _rate_limit
# ---------------------------------------------------------------------------
class TestRateLimit:
    @patch("metabolon.organelles.secretory_vesicle.time")
    def test_no_sleep_when_lock_missing(self, mock_time, tmp_path):
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            sv._rate_limit()
        mock_time.sleep.assert_not_called()

    @patch("metabolon.organelles.secretory_vesicle.time")
    def test_no_sleep_when_enough_time_elapsed(self, mock_time, tmp_path):
        fake_lock = tmp_path / "deltos.lock"
        fake_lock.touch()
        mock_time.time.return_value = fake_lock.stat().st_mtime + 5
        with patch.object(sv, "_LOCK", fake_lock):
            sv._rate_limit()
        mock_time.sleep.assert_not_called()

    @patch("metabolon.organelles.secretory_vesicle.time")
    def test_sleeps_when_too_soon(self, mock_time, tmp_path):
        fake_lock = tmp_path / "deltos.lock"
        fake_lock.touch()
        mock_time.time.return_value = fake_lock.stat().st_mtime + 0.3
        with patch.object(sv, "_LOCK", fake_lock):
            sv._rate_limit()
        mock_time.sleep.assert_called_once()
        # Should sleep ~0.7s (1 - 0.3)
        slept = mock_time.sleep.call_args[0][0]
        assert 0.6 < slept < 0.8


# ---------------------------------------------------------------------------
# secrete_text
# ---------------------------------------------------------------------------
def _make_urlopen_ok(ok: bool = True, description: str = "") -> MagicMock:
    payload = {"ok": ok}
    if description:
        payload["description"] = description
    raw = json.dumps(payload).encode()
    resp = MagicMock()
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestSecreteText:
    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_sends_text_html_mode(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        mock_urlopen.return_value = _make_urlopen_ok(ok=True)
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            result = sv.secrete_text("Hello <b>world</b>", html=True, label="Bot")
        assert result == "sent"
        # Verify the request was built correctly
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == f"{sv._API_BASE}/botTOKEN/sendMessage"
        body = req.data.decode()
        assert "chat_id=CHATID" in body
        assert "parse_mode=HTML" in body
        assert "Bot" in body

    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_sends_text_pre_mode(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        mock_urlopen.return_value = _make_urlopen_ok(ok=True)
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            result = sv.secrete_text("<script>alert(1)</script>", html=False)
        assert result == "sent"
        req = mock_urlopen.call_args[0][0]
        body = urllib.parse.parse_qs(req.data.decode())["text"][0]
        # In pre mode, text should be HTML-escaped inside <pre> tags
        assert "&lt;script&gt;" in body
        assert "<pre>" in body

    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_label_escaped(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        mock_urlopen.return_value = _make_urlopen_ok(ok=True)
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            sv.secrete_text("body", html=True, label="A&B<tag>")
        body = urllib.parse.parse_qs(mock_urlopen.call_args[0][0].data.decode())["text"][0]
        assert "A&amp;B&lt;tag&gt;" in body

    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_raises_on_telegram_error(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        mock_urlopen.return_value = _make_urlopen_ok(ok=False, description="Bad Request")
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            with pytest.raises(ValueError, match="Telegram error: Bad Request"):
                sv.secrete_text("test")

    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_raises_on_invalid_json(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        resp = MagicMock()
        resp.read.return_value = b"not json"
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            with pytest.raises(ValueError, match="invalid JSON"):
                sv.secrete_text("test")

    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_touches_lock_on_success(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        mock_urlopen.return_value = _make_urlopen_ok(ok=True)
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            sv.secrete_text("test")
        assert fake_lock.exists()


# ---------------------------------------------------------------------------
# secrete_image
# ---------------------------------------------------------------------------
class TestSecreteImage:
    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_sends_photo(self, mock_kc, mock_rl, mock_run, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG\r\n")
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"ok": True})
        )
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            result = sv.secrete_image(str(img))
        assert result == "photo sent"
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "curl"
        assert f"chat_id=CHATID" in cmd
        assert f"photo=@{img}" in cmd
        assert cmd[-1] == f"{sv._API_BASE}/botTOKEN/sendPhoto"

    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_sends_photo_with_caption(self, mock_kc, mock_rl, mock_run, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff")
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"ok": True})
        )
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            result = sv.secrete_image(str(img), caption="My caption")
        assert result == "photo sent"
        cmd = mock_run.call_args[0][0]
        assert "caption=My caption" in cmd

    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_raises_on_missing_file(self, mock_kc, mock_rl, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            with pytest.raises(ValueError, match="File not found"):
                sv.secrete_image("/nonexistent/path/image.png")

    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_raises_on_telegram_error(self, mock_kc, mock_rl, mock_run, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG")
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"ok": False, "description": "Forbidden"}),
        )
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            with pytest.raises(ValueError, match="Telegram error: Forbidden"):
                sv.secrete_image(str(img))

    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_raises_on_invalid_json(self, mock_kc, mock_rl, mock_run, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG")
        mock_run.return_value = MagicMock(returncode=0, stdout="bad json!!!")
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            with pytest.raises(ValueError, match="invalid JSON"):
                sv.secrete_image(str(img))

    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_touches_lock_on_success(self, mock_kc, mock_rl, mock_run, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG")
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"ok": True})
        )
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            sv.secrete_image(str(img))
        assert fake_lock.exists()

    @patch("metabolon.organelles.secretory_vesicle.subprocess.run")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_expands_tilde_in_path(self, mock_kc, mock_rl, mock_run, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"ok": True})
        )
        fake_lock = tmp_path / "deltos.lock"
        # Create a file we can reference with ~-style path
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG")
        with patch.object(sv, "_LOCK", fake_lock):
            # Path with ~ should be expanded; we pass the real path but
            # verify expanduser is called by checking resolve behavior
            with patch.object(Path, "expanduser", return_value=img):
                result = sv.secrete_image("~/photo.png")
        assert result == "photo sent"


# ---------------------------------------------------------------------------
# Transport-level cooldown (_is_cooled_down / secrete_text cooldown_key)
# ---------------------------------------------------------------------------
class TestCooldown:
    def test_first_call_not_cooled(self, tmp_path):
        fake_cooldown = tmp_path / "cooldowns.json"
        with patch.object(sv, "_COOLDOWN_FILE", fake_cooldown):
            assert not sv._is_cooled_down("test-key", 3600)

    def test_second_call_cooled(self, tmp_path):
        fake_cooldown = tmp_path / "cooldowns.json"
        with patch.object(sv, "_COOLDOWN_FILE", fake_cooldown):
            assert not sv._is_cooled_down("test-key", 3600)
            assert sv._is_cooled_down("test-key", 3600)

    def test_different_keys_independent(self, tmp_path):
        fake_cooldown = tmp_path / "cooldowns.json"
        with patch.object(sv, "_COOLDOWN_FILE", fake_cooldown):
            assert not sv._is_cooled_down("key-a", 3600)
            assert not sv._is_cooled_down("key-b", 3600)
            assert sv._is_cooled_down("key-a", 3600)

    def test_expired_cooldown_allows_resend(self, tmp_path):
        import hashlib
        import time

        fake_cooldown = tmp_path / "cooldowns.json"
        key = hashlib.md5(b"expired-key").hexdigest()
        old_stamp = {key: time.time() - 7200}  # 2h ago
        fake_cooldown.write_text(json.dumps(old_stamp))
        with patch.object(sv, "_COOLDOWN_FILE", fake_cooldown):
            # 1h cooldown, 2h since last send -> not cooled
            assert not sv._is_cooled_down(key, 3600)

    def test_stale_entries_pruned(self, tmp_path):
        import time

        fake_cooldown = tmp_path / "cooldowns.json"
        old_stamps = {"old-key": time.time() - 200000}  # >48h ago
        fake_cooldown.write_text(json.dumps(old_stamps))
        with patch.object(sv, "_COOLDOWN_FILE", fake_cooldown):
            sv._is_cooled_down("new-key", 3600)
            stamps = json.loads(fake_cooldown.read_text())
            assert "old-key" not in stamps
            assert "new-key" in stamps

    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_secrete_text_returns_throttled(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID"]
        mock_urlopen.return_value = _make_urlopen_ok(ok=True)
        fake_cooldown = tmp_path / "cooldowns.json"
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_COOLDOWN_FILE", fake_cooldown):
            with patch.object(sv, "_LOCK", fake_lock):
                result1 = sv.secrete_text("test", cooldown_key="ck", cooldown_seconds=3600)
                result2 = sv.secrete_text("test", cooldown_key="ck", cooldown_seconds=3600)
        assert result1 == "sent"
        assert result2 == "throttled"
        # urlopen should only be called once (second was throttled)
        assert mock_urlopen.call_count == 1

    @patch("metabolon.organelles.secretory_vesicle.urllib.request.urlopen")
    @patch("metabolon.organelles.secretory_vesicle._rate_limit")
    @patch("metabolon.organelles.secretory_vesicle._keychain")
    def test_no_cooldown_without_key(self, mock_kc, mock_rl, mock_urlopen, tmp_path):
        mock_kc.side_effect = ["TOKEN", "CHATID", "TOKEN", "CHATID"]
        mock_urlopen.return_value = _make_urlopen_ok(ok=True)
        fake_lock = tmp_path / "deltos.lock"
        with patch.object(sv, "_LOCK", fake_lock):
            result1 = sv.secrete_text("test")
            result2 = sv.secrete_text("test")
        assert result1 == "sent"
        assert result2 == "sent"
        assert mock_urlopen.call_count == 2
