#!/usr/bin/env python3
"""Tests for effectors/cookie-sync — Chrome cookie export/import.

cookie-sync is a script (effectors/cookie-sync), not an importable module.
It is loaded via exec() into isolated namespaces.
"""

import base64
import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SYNC_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cookie-sync"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def ns(tmp_path: Path):
    """Load cookie-sync via exec into an isolated namespace dict."""
    ns_dict: dict = {"__name__": "test_cookie_sync", "__file__": str(SYNC_PATH)}
    source = SYNC_PATH.read_text(encoding="utf-8")
    exec(source, ns_dict)
    return ns_dict


@pytest.fixture()
def fake_cookie_db(tmp_path: Path):
    """Create a minimal Chrome Cookies SQLite DB with test rows."""
    db_path = tmp_path / "Cookies"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            value TEXT,
            encrypted_value BLOB,
            path TEXT,
            expires_utc INTEGER,
            httponly INTEGER,
            is_secure INTEGER,
            samesite INTEGER
        )
        """
    )
    # Plaintext cookie
    conn.execute(
        "INSERT INTO cookies VALUES (?,?,?,?,?,?,?,?,?)",
        (".example.com", "session_id", "abc123", None, "/", 1735689600, 1, 1, 1),
    )
    # Encrypted v10 cookie (fake encrypted blob)
    conn.execute(
        "INSERT INTO cookies VALUES (?,?,?,?,?,?,?,?,?)",
        (".example.com", "secret_token", "", b"v10" + b"\x00" * 32, "/", 1735689600, 0, 0, 0),
    )
    # Different domain
    conn.execute(
        "INSERT INTO cookies VALUES (?,?,?,?,?,?,?,?,?)",
        (".other.com", "other_ck", "other_val", None, "/api", 0, 0, 0, 2),
    )
    conn.commit()
    conn.close()
    return db_path


# ── File structure tests ───────────────────────────────────────────────────


class TestCookieSyncBasics:
    def test_file_exists(self):
        assert SYNC_PATH.exists()
        assert SYNC_PATH.is_file()

    def test_is_python_script(self):
        first_line = SYNC_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/")
        assert "python" in first_line.lower()

    def test_has_docstring(self):
        content = SYNC_PATH.read_text()
        assert '"""' in content

    def test_syntax_valid(self):
        source = SYNC_PATH.read_text()
        compile(source, str(SYNC_PATH), "exec")


# ── CLI tests ───────────────────────────────────────────────────────────────


class TestCLI:
    def test_no_args_returns_1(self, ns):
        assert ns["main"]([]) == 1

    def test_help_does_not_crash(self, ns):
        # --help would SystemExit(0), so test main with unknown subcommand
        assert ns["main"]([]) == 1

    def test_export_missing_db(self, ns, tmp_path):
        """Export should fail gracefully when DB doesn't exist."""
        fake_base = tmp_path / "Chrome"
        fake_base.mkdir()
        with patch.object(ns["sys"], "stderr") as mock_err, patch.object(
            ns, "CHROME_BASE", fake_base
        ):
            rc = ns["cmd_export"](profile="Default", output=tmp_path / "out.json")
        assert rc == 1

    def test_export_with_mocked_key(self, ns, fake_cookie_db, tmp_path):
        """Export reads the mock DB and produces valid JSON."""
        output = tmp_path / "cookies.json"

        # Mock get_chrome_key and decrypt to avoid needing real macOS keychain
        def mock_get_key():
            return b"\x00" * 16

        def mock_decrypt(raw, key):
            if raw and raw.startswith(b"v10"):
                return "decrypted_secret"
            if raw:
                return raw.decode("utf-8", errors="replace")
            return ""

        with (
            patch.object(ns, "get_chrome_key", mock_get_key),
            patch.object(ns, "decrypt_cookie_value", mock_decrypt),
            patch.object(ns, "CHROME_BASE", fake_cookie_db.parent.parent),
            patch.object(ns, "DEFAULT_OUTPUT", output),
        ):
            rc = ns["cmd_export"](profile=fake_cookie_db.parent.name, output=output)

        assert rc == 0
        cookies = json.loads(output.read_text())
        # Should have at least the 2 example.com cookies (v10 may fail decrypt, but mock handles it)
        assert isinstance(cookies, list)
        assert len(cookies) >= 1

    def test_export_domain_filter(self, ns, fake_cookie_db, tmp_path):
        """Domain filter should narrow results."""
        output = tmp_path / "cookies.json"

        def mock_get_key():
            return b"\x00" * 16

        def mock_decrypt(raw, key):
            if raw and raw.startswith(b"v10"):
                return "decrypted"
            if raw:
                return raw.decode("utf-8", errors="replace")
            return ""

        with (
            patch.object(ns, "get_chrome_key", mock_get_key),
            patch.object(ns, "decrypt_cookie_value", mock_decrypt),
            patch.object(ns, "CHROME_BASE", fake_cookie_db.parent.parent),
        ):
            rc = ns["cmd_export"](profile=fake_cookie_db.parent.name, domain="other.com", output=output)

        assert rc == 0
        cookies = json.loads(output.read_text())
        assert all("other.com" in c["domain"] for c in cookies)

    def test_import_missing_file(self, ns, tmp_path):
        """Import should fail for nonexistent file."""
        rc = ns["cmd_import"](tmp_path / "nonexistent.json")
        assert rc == 1

    def test_import_dry_run(self, ns, tmp_path):
        """Import without browser context prints cookies."""
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text(json.dumps([
            {"name": "foo", "value": "bar", "domain": ".test.com", "path": "/"},
        ]))
        rc = ns["cmd_import"](cookies_file)
        assert rc == 0

    def test_import_invalid_json_structure(self, ns, tmp_path):
        """Import should reject non-array JSON."""
        bad = tmp_path / "bad.json"
        bad.write_text('{"not": "an array"}')
        rc = ns["cmd_import"](bad)
        assert rc == 1

    def test_import_into_browser_context(self, ns, tmp_path):
        """Import should call add_cookies on the browser context."""
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text(json.dumps([
            {
                "name": "session",
                "value": "abc",
                "domain": ".example.com",
                "path": "/",
                "expires": 1735689600,
                "httponly": True,
                "secure": True,
                "samesite": "Lax",
            },
        ]))
        mock_ctx = MagicMock()
        rc = ns["cmd_import"](cookies_file, browser_context=mock_ctx)
        assert rc == 0
        mock_ctx.add_cookies.assert_called_once()
        call_args = mock_ctx.add_cookies.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["name"] == "session"
        assert call_args[0]["httpOnly"] is True
        assert call_args[0]["sameSite"] == "Lax"


# ── Decrypt helpers ─────────────────────────────────────────────────────────


class TestDecryptHelpers:
    def test_decrypt_none_returns_empty(self, ns):
        key = b"\x00" * 16
        assert ns["decrypt_cookie_value"](None, key) == ""

    def test_decrypt_plaintext_passthrough(self, ns):
        key = b"\x00" * 16
        assert ns["decrypt_cookie_value"](b"hello", key) == "hello"

    def test_samesite_map(self, ns):
        m = ns["SAMESITE_MAP"]
        assert m[0] == "None"
        assert m[1] == "Lax"
        assert m[2] == "Strict"
        assert m[3] == "Lax"


# ── read_cookies tests ─────────────────────────────────────────────────────


class TestReadCookies:
    def test_reads_all_rows(self, ns, fake_cookie_db):
        rows = ns["read_cookies"](fake_cookie_db)
        assert len(rows) == 3

    def test_domain_filter(self, ns, fake_cookie_db):
        rows = ns["read_cookies"](fake_cookie_db, domain_filter="example")
        assert len(rows) == 2
        assert all("example" in r["domain"] for r in rows)

    def test_row_has_expected_keys(self, ns, fake_cookie_db):
        rows = ns["read_cookies"](fake_cookie_db)
        expected = {"domain", "name", "value", "encrypted_value", "path", "expires", "httponly", "secure", "samesite"}
        assert set(rows[0].keys()) == expected

    def test_row_types(self, ns, fake_cookie_db):
        rows = ns["read_cookies"](fake_cookie_db)
        r = rows[0]
        assert isinstance(r["domain"], str)
        assert isinstance(r["httponly"], bool)
        assert isinstance(r["secure"], bool)
        assert isinstance(r["samesite"], str)


# ── Integration-style: export -> import round-trip ─────────────────────────


class TestRoundTrip:
    def test_export_then_import(self, ns, fake_cookie_db, tmp_path):
        """Full round trip: export to JSON, then import (dry run)."""
        output = tmp_path / "cookies.json"

        def mock_get_key():
            return b"\x00" * 16

        def mock_decrypt(raw, key):
            if raw and raw.startswith(b"v10"):
                return "decrypted_secret"
            if raw:
                return raw.decode("utf-8", errors="replace")
            return ""

        with (
            patch.object(ns, "get_chrome_key", mock_get_key),
            patch.object(ns, "decrypt_cookie_value", mock_decrypt),
            patch.object(ns, "CHROME_BASE", fake_cookie_db.parent.parent),
        ):
            ns["cmd_export"](profile=fake_cookie_db.parent.name, output=output)

        assert output.exists()
        cookies = json.loads(output.read_text())
        assert len(cookies) >= 2

        # Re-import dry run
        rc = ns["cmd_import"](output)
        assert rc == 0

        # Re-import with mock browser context
        mock_ctx = MagicMock()
        rc = ns["cmd_import"](output, browser_context=mock_ctx)
        assert rc == 0
        mock_ctx.add_cookies.assert_called_once()
        loaded = mock_ctx.add_cookies.call_args[0][0]
        assert len(loaded) == len(cookies)
