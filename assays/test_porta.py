from __future__ import annotations

"""Tests for effectors/porta — web auth gateway for headless automation.

porta is a script — loaded via exec(), never imported.
"""

import json
import sqlite3
import types
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Load effector via exec (never import) ──────────────────────────────────

_PORTA_PATH = Path(__file__).resolve().parents[1] / "effectors" / "porta"
_PORTA_CODE = _PORTA_PATH.read_text()

_mod = types.ModuleType("porta")
_mod.__file__ = str(_PORTA_PATH)
exec(_PORTA_CODE, _mod.__dict__)

# Pull names into test-level convenience bindings
SESSION_DIR = _mod.SESSION_DIR
read_chrome_cookies = _mod.read_chrome_cookies
read_firefox_cookies = _mod.read_firefox_cookies
save_session = _mod.save_session
load_session = _mod.load_session
list_sessions = _mod.list_sessions
delete_session = _mod.delete_session
clear_all_sessions = _mod.clear_all_sessions
format_curl = _mod.format_curl
format_headers = _mod.format_headers
format_json = _mod.format_json
format_dict = _mod.format_dict
format_netscape = _mod.format_netscape
build_parser = _mod.build_parser
main = _mod.main
_decrypt_value = _mod._decrypt_value
_chrome_key = _mod._chrome_key

# ── Helpers ────────────────────────────────────────────────────────────────


def _sample_cookies() -> list[dict]:
    """Return sample cookies for testing."""
    return [
        {
            "domain": ".example.com",
            "name": "session_id",
            "value": "abc123",
            "path": "/",
            "expires": 1735689600.0,
            "secure": True,
            "httponly": True,
            "samesite": "Lax",
        },
        {
            "domain": ".example.com",
            "name": "user_pref",
            "value": "dark_mode",
            "path": "/",
            "expires": 0,
            "secure": False,
            "httponly": False,
            "samesite": "Unspecified",
        },
    ]


def _create_chrome_db(db_path: Path, cookies: list[dict]) -> None:
    """Create a minimal Chrome Cookies SQLite DB at db_path."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            path TEXT,
            encrypted_value BLOB,
            expires_utc REAL,
            is_secure INTEGER,
            is_httponly INTEGER,
            samesite INTEGER
        )
        """
    )
    _chrome_key()
    for c in cookies:
        # Store plaintext (no v10/v11 prefix) for simplicity in most tests
        enc_val = b""
        if c.get("value"):
            enc_val = c["value"].encode("utf-8")
        conn.execute(
            "INSERT INTO cookies (host_key, name, path, encrypted_value, "
            "expires_utc, is_secure, is_httponly, samesite) VALUES (?,?,?,?,?,?,?,?)",
            (
                c["domain"],
                c["name"],
                c.get("path", "/"),
                enc_val,
                c.get("expires", 0),
                int(c.get("secure", False)),
                int(c.get("httponly", False)),
                {"Lax": 1, "Strict": 2, "None": 3}.get(c.get("samesite", ""), 0),
            ),
        )
    conn.commit()
    conn.close()


def _create_firefox_db(db_path: Path, cookies: list[dict]) -> None:
    """Create a minimal Firefox cookies.sqlite DB at db_path."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE moz_cookies (
            host TEXT,
            name TEXT,
            value TEXT,
            path TEXT,
            expiry INTEGER,
            isSecure INTEGER,
            isHttpOnly INTEGER
        )
        """
    )
    for c in cookies:
        conn.execute(
            "INSERT INTO moz_cookies (host, name, value, path, expiry, isSecure, isHttpOnly) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                c["domain"],
                c["name"],
                c["value"],
                c.get("path", "/"),
                int(c.get("expires", 0)),
                int(c.get("secure", False)),
                int(c.get("httponly", False)),
            ),
        )
    conn.commit()
    conn.close()


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def session_dir(tmp_path, monkeypatch):
    """Redirect SESSION_DIR to a temp directory for isolation."""
    fake_dir = tmp_path / "porta_sessions"
    monkeypatch.setattr(_mod, "SESSION_DIR", fake_dir)
    return fake_dir


@pytest.fixture
def chrome_db(tmp_path):
    """Create a temp Chrome profile with sample cookies."""
    base = tmp_path / "chrome"
    db_path = base / "Default" / "Cookies"
    _create_chrome_db(db_path, _sample_cookies())
    return base


@pytest.fixture
def firefox_profile(tmp_path):
    """Create a temp Firefox profile with sample cookies."""
    base = tmp_path / "firefox_profiles"
    profile_dir = base / "xxxxxx.default-release"
    db_path = profile_dir / "cookies.sqlite"
    _create_firefox_db(db_path, _sample_cookies())
    return base


# ── Unit tests: decryption ────────────────────────────────────────────────


class TestDecryptValue:
    def test_none_returns_empty(self):
        assert _decrypt_value(None, b"key") == ""

    def test_plaintext_passthrough(self):
        result = _decrypt_value(b"hello", b"key")
        assert result == "hello"

    def test_v10_decrypts(self):
        from cryptography.hazmat.primitives import padding as sym_padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        key = _chrome_key()
        iv = b" " * 16
        plaintext = b"secret_value"
        padder = sym_padding.PKCS7(128).padder()
        padded = padder.update(plaintext) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encrypted = b"v10" + cipher.encryptor().update(padded) + cipher.encryptor().finalize()
        # Need a fresh encryptor
        enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        ct = enc.update(padded) + enc.finalize()
        encrypted = b"v10" + ct
        result = _decrypt_value(encrypted, key)
        assert result == "secret_value"


class TestChromeKey:
    def test_key_is_16_bytes(self):
        key = _chrome_key()
        assert len(key) == 16

    def test_key_is_deterministic(self):
        assert _chrome_key() == _chrome_key()


# ── Unit tests: read_chrome_cookies ───────────────────────────────────────


class TestReadChromeCookies:
    def test_reads_all_cookies(self, chrome_db):
        with patch.object(_mod, "_chrome_base", return_value=chrome_db):
            cookies = read_chrome_cookies()
        assert len(cookies) == 2
        names = {c["name"] for c in cookies}
        assert names == {"session_id", "user_pref"}

    def test_domain_filter(self, chrome_db):
        with patch.object(_mod, "_chrome_base", return_value=chrome_db):
            cookies = read_chrome_cookies(domain_filter="example")
        assert len(cookies) == 2

    def test_domain_filter_no_match(self, chrome_db):
        with patch.object(_mod, "_chrome_base", return_value=chrome_db):
            cookies = read_chrome_cookies(domain_filter="nonexistent")
        assert len(cookies) == 0

    def test_cookie_shape(self, chrome_db):
        with patch.object(_mod, "_chrome_base", return_value=chrome_db):
            cookies = read_chrome_cookies()
        c = cookies[0]
        for key in (
            "domain",
            "name",
            "value",
            "path",
            "expires",
            "secure",
            "httponly",
            "samesite",
        ):
            assert key in c, f"Missing key: {key}"

    def test_missing_db_returns_empty(self, tmp_path):
        with patch.object(_mod, "_chrome_base", return_value=tmp_path / "nochrome"):
            cookies = read_chrome_cookies()
        assert cookies == []


# ── Unit tests: read_firefox_cookies ──────────────────────────────────────


class TestReadFirefoxCookies:
    def test_reads_cookies(self, firefox_profile):
        with patch.object(_mod, "FIREFOX_BASE_LINUX", firefox_profile):
            cookies = read_firefox_cookies()
        assert len(cookies) == 2
        names = {c["name"] for c in cookies}
        assert names == {"session_id", "user_pref"}

    def test_domain_filter(self, firefox_profile):
        with patch.object(_mod, "FIREFOX_BASE_LINUX", firefox_profile):
            cookies = read_firefox_cookies(domain_filter="example")
        assert len(cookies) == 2

    def test_no_profiles_dir_returns_empty(self, tmp_path):
        with patch.object(_mod, "FIREFOX_BASE_LINUX", tmp_path / "nonexistent"):
            cookies = read_firefox_cookies()
        assert cookies == []


# ── Unit tests: session storage ───────────────────────────────────────────


class TestSessionStorage:
    def test_save_and_load(self, session_dir):
        cookies = _sample_cookies()
        path = save_session("testsvc", ".test.com", cookies, source="chrome")
        assert path.exists()
        loaded = load_session("testsvc")
        assert loaded is not None
        assert loaded["service"] == "testsvc"
        assert loaded["domain"] == ".test.com"
        assert loaded["cookie_count"] == 2
        assert len(loaded["cookies"]) == 2
        assert loaded["source"] == "chrome"

    def test_load_nonexistent(self, session_dir):
        assert load_session("nope") is None

    def test_list_sessions(self, session_dir):
        save_session("svc1", ".a.com", _sample_cookies())
        save_session("svc2", ".b.com", _sample_cookies())
        sessions = list_sessions()
        assert len(sessions) == 2
        names = {s["service"] for s in sessions}
        assert names == {"svc1", "svc2"}

    def test_list_empty_dir(self, session_dir):
        assert list_sessions() == []

    def test_list_missing_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "SESSION_DIR", tmp_path / "nope")
        assert list_sessions() == []

    def test_delete_session(self, session_dir):
        save_session("delme", ".d.com", _sample_cookies())
        assert delete_session("delme") is True
        assert load_session("delme") is None

    def test_delete_nonexistent(self, session_dir):
        assert delete_session("ghost") is False

    def test_clear_all(self, session_dir):
        save_session("a", ".a.com", _sample_cookies())
        save_session("b", ".b.com", _sample_cookies())
        count = clear_all_sessions()
        assert count == 2
        assert list_sessions() == []

    def test_clear_all_empty(self, session_dir):
        count = clear_all_sessions()
        assert count == 0

    def test_session_file_is_valid_json(self, session_dir):
        save_session("jsoncheck", ".j.com", _sample_cookies())
        path = session_dir / "jsoncheck.json"
        data = json.loads(path.read_text())
        assert "captured_at" in data
        assert "cookies" in data
        # Verify captured_at is parseable
        datetime.fromisoformat(data["captured_at"])


# ── Unit tests: export formatters ─────────────────────────────────────────


class TestFormatCurl:
    def test_basic(self):
        cookies = [{"name": "a", "value": "1"}, {"name": "b", "value": "2"}]
        result = format_curl(cookies)
        assert result == "a=1; b=2"

    def test_empty(self):
        assert format_curl([]) == ""


class TestFormatHeaders:
    def test_basic(self):
        cookies = [{"name": "sid", "value": "xyz"}]
        result = format_headers(cookies, ".example.com")
        assert result == "Cookie: sid=xyz"


class TestFormatJson:
    def test_basic(self):
        cookies = [{"name": "k", "value": "v"}]
        result = format_json(cookies)
        parsed = json.loads(result)
        assert parsed == cookies


class TestFormatDict:
    def test_basic(self):
        cookies = [{"name": "a", "value": "1"}, {"name": "b", "value": "2"}]
        result = format_dict(cookies)
        parsed = json.loads(result)
        assert parsed == {"a": "1", "b": "2"}


class TestFormatNetscape:
    def test_basic(self):
        cookies = [
            {
                "domain": ".example.com",
                "path": "/",
                "secure": True,
                "expires": 1735689600,
                "name": "sid",
                "value": "abc",
            }
        ]
        result = format_netscape(cookies)
        assert "# HTTP Cookie File" in result
        assert ".example.com" in result
        assert "sid" in result
        assert "abc" in result
        assert "TRUE" in result  # secure flag


# ── CLI tests ─────────────────────────────────────────────────────────────


class TestStatusCLI:
    def test_status_no_sessions(self, session_dir, capsys):
        rc = main(["status"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No sessions stored" in out

    def test_status_with_sessions(self, session_dir, capsys):
        save_session("testsvc", ".test.com", _sample_cookies())
        rc = main(["status"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "testsvc" in out
        assert "cookies=" in out and out.count("testsvc") >= 1


class TestLoginCLI:
    def test_login_captures_cookies(self, session_dir, chrome_db, capsys):
        with patch.object(_mod, "_chrome_base", return_value=chrome_db):
            rc = main(["login", "example", "--domain", "example.com"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Captured 2 cookies" in out
        loaded = load_session("example")
        assert loaded is not None
        assert loaded["cookie_count"] == 2

    def test_login_no_cookies(self, session_dir, tmp_path):
        empty_chrome = tmp_path / "chrome"
        with patch.object(_mod, "_chrome_base", return_value=empty_chrome):
            rc = main(["login", "nothing", "--domain", "void.com"])
        assert rc == 1

    def test_login_default_domain_is_service(self, session_dir, chrome_db, capsys):
        with patch.object(_mod, "_chrome_base", return_value=chrome_db):
            rc = main(["login", "example.com"])
        assert rc == 0
        loaded = load_session("example.com")
        assert loaded["domain"] == "example.com"


class TestExportCLI:
    def test_export_curl(self, session_dir, capsys):
        save_session("svc", ".svc.com", _sample_cookies())
        rc = main(["export", "--service", "svc", "--format", "curl"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "session_id=abc123" in out
        assert "user_pref=dark_mode" in out

    def test_export_json(self, session_dir, capsys):
        save_session("svc", ".svc.com", _sample_cookies())
        rc = main(["export", "--service", "svc", "--format", "json"])
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert len(parsed) == 2

    def test_export_dict(self, session_dir, capsys):
        save_session("svc", ".svc.com", _sample_cookies())
        rc = main(["export", "--service", "svc", "--format", "dict"])
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["session_id"] == "abc123"

    def test_export_headers(self, session_dir, capsys):
        save_session("svc", ".svc.com", _sample_cookies())
        rc = main(["export", "--service", "svc", "--format", "headers"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out.startswith("Cookie:")

    def test_export_netscape(self, session_dir, capsys):
        save_session("svc", ".svc.com", _sample_cookies())
        rc = main(["export", "--service", "svc", "--format", "netscape"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "# HTTP Cookie File" in out

    def test_export_missing_service(self, session_dir):
        rc = main(["export", "--service", "ghost"])
        assert rc == 1

    def test_export_default_format_is_curl(self, session_dir, capsys):
        save_session("svc", ".svc.com", _sample_cookies())
        rc = main(["export", "--service", "svc"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "=" in out  # curl format uses name=value


class TestInjectCLI:
    def test_inject_from_chrome(self, session_dir, chrome_db, capsys):
        with patch.object(_mod, "_chrome_base", return_value=chrome_db):
            rc = main(["inject", "--browser", "chrome", "--domain", "example.com"])
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert len(parsed) == 2

    def test_inject_no_cookies(self, session_dir, tmp_path):
        empty = tmp_path / "chrome"
        with patch.object(_mod, "_chrome_base", return_value=empty):
            rc = main(["inject", "--browser", "chrome", "--domain", "x.com"])
        assert rc == 1


class TestRunCLI:
    def test_run_from_stored_session(self, session_dir, capsys):
        save_session("svc", ".svc.com", _sample_cookies())
        rc = main(["run", "--domain", "svc.com"])
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert len(parsed) == 2

    def test_run_no_cookies_anywhere(self, session_dir, tmp_path):
        with (
            patch.object(_mod, "_chrome_base", return_value=tmp_path / "nope"),
            patch.object(_mod, "FIREFOX_BASE_LINUX", tmp_path / "nope2"),
        ):
            rc = main(["run", "--domain", "void.com"])
        assert rc == 1


class TestClearCLI:
    def test_clear_service(self, session_dir, capsys):
        save_session("delme", ".d.com", _sample_cookies())
        rc = main(["clear", "--service", "delme"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Cleared session 'delme'" in out
        assert load_session("delme") is None

    def test_clear_nonexistent(self, session_dir):
        rc = main(["clear", "--service", "ghost"])
        assert rc == 1

    def test_clear_all(self, session_dir, capsys):
        save_session("a", ".a.com", _sample_cookies())
        save_session("b", ".b.com", _sample_cookies())
        rc = main(["clear", "--all"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Cleared 2 session(s)" in out

    def test_clear_no_args(self, session_dir):
        rc = main(["clear"])
        assert rc == 1


class TestMainCLI:
    def test_no_args_returns_1(self, capsys):
        rc = main([])
        assert rc == 1

    def test_build_parser(self):
        parser = build_parser()
        assert parser.prog == "porta"

    def test_help_exits_cleanly(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0


# ── Subprocess tests ──────────────────────────────────────────────────────


class TestSubprocess:
    """Run porta as a subprocess to test end-to-end."""

    def test_help(self):
        import subprocess

        result = subprocess.run(
            [str(_PORTA_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "porta" in result.stdout
        assert "status" in result.stdout
        assert "login" in result.stdout
        assert "export" in result.stdout

    def test_status_subprocess(self):
        import subprocess

        result = subprocess.run(
            [str(_PORTA_PATH), "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        # Either "No sessions stored" or a session list
        assert "session" in result.stdout.lower() or "Sessions" in result.stdout

    def test_clear_nonexistent_subprocess(self):
        import subprocess

        result = subprocess.run(
            [str(_PORTA_PATH), "clear", "--service", "nosuchsvc_xyz"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "No session found" in result.stderr

    def test_export_missing_subprocess(self):
        import subprocess

        result = subprocess.run(
            [str(_PORTA_PATH), "export", "--service", "ghost999"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
