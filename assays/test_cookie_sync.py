"""Tests for effectors/cookie-sync — Chrome cookie export/import.

cookie-sync is a script — loaded via exec(), never imported.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Load effector via exec (never import) ─────────────────────────────────────

_CS_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cookie-sync"
_CS_CODE = _CS_PATH.read_text()
_ns: dict = {"__name__": "cookie_sync", "__file__": str(_CS_PATH)}
exec(_CS_CODE, _ns)

# Pull names into module-level convenience bindings
SAMESITE_MAP = _ns["SAMESITE_MAP"]
cmd_export = _ns["cmd_export"]
cmd_import = _ns["cmd_import"]
decrypt_cookie_value = _ns["decrypt_cookie_value"]
decrypt_v10 = _ns["decrypt_v10"]
decrypt_v11 = _ns["decrypt_v11"]
get_chrome_key = _ns["get_chrome_key"]
main = _ns["main"]
read_cookies = _ns["read_cookies"]
row_to_dict = _ns["row_to_dict"]

# ── Deterministic test key ────────────────────────────────────────────────────

TEST_PASSWORD = b"test-chrome-safe-storage-key"
TEST_KEY = hashlib.pbkdf2_hmac("sha1", TEST_PASSWORD, b"saltysalt", 1003, dklen=16)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _encrypt_v10(plaintext: str, key: bytes = TEST_KEY) -> bytes:
    """Encrypt a value using v10 (AES-128-CBC) like Chrome would."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7

    iv = b"\x00" * 16  # deterministic for tests
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    return b"v10" + iv + ct


def _encrypt_v11(plaintext: str, key: bytes = TEST_KEY) -> bytes:
    """Encrypt a value using v11 (AES-128-GCM) like Chrome would."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = b"\x00" * 12  # deterministic for tests
    aesgcm = AESGCM(key)
    ct_and_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return b"v11" + nonce + ct_and_tag


def _create_cookie_db(db_path: Path, cookies: list[dict]) -> None:
    """Create a minimal Chrome Cookies SQLite DB at db_path."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            value TEXT,
            encrypted_value BLOB,
            path TEXT,
            expires_utc REAL,
            httponly INTEGER,
            is_secure INTEGER,
            samesite INTEGER
        )
        """
    )
    for c in cookies:
        conn.execute(
            "INSERT INTO cookies (host_key, name, value, encrypted_value, path, "
            "expires_utc, httponly, is_secure, samesite) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                c["host_key"],
                c["name"],
                c.get("value", ""),
                c.get("encrypted_value", b""),
                c.get("path", "/"),
                c.get("expires_utc", 0),
                int(c.get("httponly", False)),
                int(c.get("is_secure", False)),
                c.get("samesite", 0),
            ),
        )
    conn.commit()
    conn.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cookie_db(tmp_path):
    """Create a temporary Chrome-style cookies DB with sample data."""
    db_path = tmp_path / "Chrome" / "Default" / "Cookies"
    cookies = [
        {
            "host_key": ".example.com",
            "name": "session_id",
            "value": "",
            "encrypted_value": _encrypt_v10("abc123"),
            "path": "/",
            "expires_utc": 1735689600.0,
            "httponly": True,
            "is_secure": True,
            "samesite": 1,
        },
        {
            "host_key": ".other.com",
            "name": "pref",
            "value": "lang=en",
            "encrypted_value": b"",
            "path": "/",
            "expires_utc": 0,
            "httponly": False,
            "is_secure": False,
            "samesite": 0,
        },
        {
            "host_key": ".secure.org",
            "name": "token_v11",
            "value": "",
            "encrypted_value": _encrypt_v11("gcm-secret"),
            "path": "/api",
            "expires_utc": 9999999999.0,
            "httponly": True,
            "is_secure": True,
            "samesite": 2,
        },
    ]
    _create_cookie_db(db_path, cookies)
    return tmp_path


# ── Unit tests: decrypt ──────────────────────────────────────────────────────


class TestDecryptV10:
    def test_decrypts_v10_cookie(self):
        encrypted = _encrypt_v10("hello world")
        result = decrypt_v10(encrypted, TEST_KEY)
        assert result == "hello world"

    def test_decrypts_empty_string(self):
        encrypted = _encrypt_v10("")
        result = decrypt_v10(encrypted, TEST_KEY)
        assert result == ""


class TestDecryptV11:
    def test_decrypts_v11_cookie(self):
        encrypted = _encrypt_v11("gcm-value")
        result = decrypt_v11(encrypted, TEST_KEY)
        assert result == "gcm-value"

    def test_decrypts_empty_string(self):
        encrypted = _encrypt_v11("")
        result = decrypt_v11(encrypted, TEST_KEY)
        assert result == ""


class TestDecryptCookieValue:
    def test_none_returns_empty(self):
        assert decrypt_cookie_value(None, TEST_KEY) == ""

    def test_v10_dispatches(self):
        encrypted = _encrypt_v10("dispatched")
        assert decrypt_cookie_value(encrypted, TEST_KEY) == "dispatched"

    def test_v11_dispatches(self):
        encrypted = _encrypt_v11("dispatched-gcm")
        assert decrypt_cookie_value(encrypted, TEST_KEY) == "dispatched-gcm"

    def test_plaintext_passthrough(self):
        assert decrypt_cookie_value(b"plain-text", TEST_KEY) == "plain-text"


class TestSameSiteMap:
    def test_known_values(self):
        assert SAMESITE_MAP[0] == "None"
        assert SAMESITE_MAP[1] == "Lax"
        assert SAMESITE_MAP[2] == "Strict"

    def test_unknown_defaults_none(self):
        assert SAMESITE_MAP.get(99, "None") == "None"


# ── Integration: read_cookies ────────────────────────────────────────────────


class TestReadCookies:
    def test_reads_all_cookies(self, cookie_db):
        db_path = cookie_db / "Chrome" / "Default" / "Cookies"
        rows = read_cookies(db_path)
        assert len(rows) == 3
        names = {r["name"] for r in rows}
        assert names == {"session_id", "pref", "token_v11"}

    def test_domain_filter(self, cookie_db):
        db_path = cookie_db / "Chrome" / "Default" / "Cookies"
        rows = read_cookies(db_path, domain_filter="example")
        assert len(rows) == 1
        assert rows[0]["name"] == "session_id"
        assert rows[0]["domain"] == ".example.com"

    def test_row_shape(self, cookie_db):
        db_path = cookie_db / "Chrome" / "Default" / "Cookies"
        rows = read_cookies(db_path)
        row = rows[0]
        for key in ("domain", "name", "value", "encrypted_value", "path", "httponly", "secure", "samesite"):
            assert key in row, f"Missing key: {key}"


# ── Integration: cmd_export ──────────────────────────────────────────────────


class TestCmdExport:
    def test_exports_json(self, cookie_db, tmp_path):
        output = tmp_path / "out.json"
        with patch.object(_ns["cookie_sync"], "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_ns["cookie_sync"], "get_chrome_key", return_value=TEST_KEY):
            rc = cmd_export(output=output)
        assert rc == 0
        cookies = json.loads(output.read_text())
        assert len(cookies) == 3
        by_name = {c["name"]: c for c in cookies}
        assert by_name["session_id"]["value"] == "abc123"
        assert by_name["pref"]["value"] == "lang=en"
        assert by_name["token_v11"]["value"] == "gcm-secret"

    def test_export_domain_filter(self, cookie_db, tmp_path):
        output = tmp_path / "filtered.json"
        with patch.object(_ns["cookie_sync"], "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_ns["cookie_sync"], "get_chrome_key", return_value=TEST_KEY):
            rc = cmd_export(domain="other", output=output)
        assert rc == 0
        cookies = json.loads(output.read_text())
        assert len(cookies) == 1
        assert cookies[0]["name"] == "pref"

    def test_export_missing_db(self, tmp_path):
        output = tmp_path / "missing.json"
        fake_base = tmp_path / "nochrome"
        with patch.object(_ns["cookie_sync"], "CHROME_BASE", fake_base):
            rc = cmd_export(output=output)
        assert rc == 1

    def test_export_creates_parent_dirs(self, cookie_db, tmp_path):
        output = tmp_path / "deep" / "nested" / "cookies.json"
        with patch.object(_ns["cookie_sync"], "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_ns["cookie_sync"], "get_chrome_key", return_value=TEST_KEY):
            rc = cmd_export(output=output)
        assert rc == 0
        assert output.exists()

    def test_export_json_has_no_encrypted_value_key(self, cookie_db, tmp_path):
        output = tmp_path / "clean.json"
        with patch.object(_ns["cookie_sync"], "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_ns["cookie_sync"], "get_chrome_key", return_value=TEST_KEY):
            rc = cmd_export(output=output)
        assert rc == 0
        cookies = json.loads(output.read_text())
        for c in cookies:
            assert "encrypted_value" not in c


# ── Integration: cmd_import ──────────────────────────────────────────────────


class TestCmdImport:
    def test_import_dry_run(self, tmp_path, capsys):
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text(json.dumps([
            {"name": "sid", "value": "v1", "domain": ".x.com", "path": "/"},
        ]))
        rc = cmd_import(cookies_file)
        assert rc == 0
        captured = capsys.readouterr()
        assert "sid" in captured.out
        assert "1 cookies" in captured.out

    def test_import_with_browser_context(self, tmp_path):
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text(json.dumps([
            {
                "name": "sid", "value": "v1", "domain": ".x.com", "path": "/",
                "expires": 1735689600.0, "httponly": True, "secure": True,
                "samesite": "Lax",
            },
        ]))
        mock_ctx = MagicMock()
        rc = cmd_import(cookies_file, browser_context=mock_ctx)
        assert rc == 0
        mock_ctx.add_cookies.assert_called_once()
        pw_cookies = mock_ctx.add_cookies.call_args[0][0]
        assert len(pw_cookies) == 1
        assert pw_cookies[0]["name"] == "sid"
        assert pw_cookies[0]["httpOnly"] is True
        assert pw_cookies[0]["secure"] is True
        assert pw_cookies[0]["sameSite"] == "Lax"

    def test_import_missing_file(self, tmp_path):
        rc = cmd_import(tmp_path / "nope.json")
        assert rc == 1

    def test_import_invalid_json_structure(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"not": "a list"}))
        rc = cmd_import(bad)
        assert rc == 1

    def test_import_playwright_cookie_shape(self, tmp_path):
        """Verify the Playwright cookie dict shape has the right keys."""
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text(json.dumps([
            {
                "name": "a", "value": "b", "domain": ".c.com", "path": "/",
                "expires": 0, "httponly": False, "secure": False,
                "samesite": "None",
            },
        ]))
        mock_ctx = MagicMock()
        rc = cmd_import(cookies_file, browser_context=mock_ctx)
        assert rc == 0
        pw_cookie = mock_ctx.add_cookies.call_args[0][0][0]
        assert "name" in pw_cookie
        assert "value" in pw_cookie
        assert "domain" in pw_cookie
        assert "path" in pw_cookie
        # expires=0 should NOT be in the cookie
        assert "expires" not in pw_cookie


# ── CLI: main() ──────────────────────────────────────────────────────────────


class TestMain:
    def test_no_args_returns_1(self, capsys):
        rc = main([])
        assert rc == 1

    def test_export_via_cli(self, cookie_db, tmp_path):
        output = tmp_path / "cli_out.json"
        with patch.object(_ns["cookie_sync"], "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_ns["cookie_sync"], "get_chrome_key", return_value=TEST_KEY):
            rc = main(["export", "--output", str(output)])
        assert rc == 0
        assert output.exists()

    def test_export_with_profile(self, cookie_db, tmp_path):
        output = tmp_path / "prof_out.json"
        with patch.object(_ns["cookie_sync"], "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_ns["cookie_sync"], "get_chrome_key", return_value=TEST_KEY):
            rc = main(["export", "--profile", "Default", "--output", str(output)])
        assert rc == 0

    def test_import_via_cli(self, tmp_path):
        cookies_file = tmp_path / "cli_cookies.json"
        cookies_file.write_text(json.dumps([
            {"name": "k", "value": "v", "domain": ".d.com", "path": "/"},
        ]))
        rc = main(["import", str(cookies_file)])
        assert rc == 0
