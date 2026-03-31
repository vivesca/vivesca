from __future__ import annotations
"""Tests for effectors/cookie-sync — Chrome cookie export/import.

cookie-sync is a script — loaded via exec(), never imported.
"""


import base64
import hashlib
import json
import sqlite3
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Load effector via exec (never import) ─────────────────────────────────────

_CS_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cookie-sync"
_CS_CODE = _CS_PATH.read_text()

# Create a proper module-like namespace for patch.object to work
_mod = types.ModuleType("cookie_sync")
_mod.__file__ = str(_CS_PATH)
exec(_CS_CODE, _mod.__dict__)

# Pull names into test-level convenience bindings
CHROME_BASE = _mod.CHROME_BASE
DEFAULT_OUTPUT = _mod.DEFAULT_OUTPUT
SAMESITE_MAP = _mod.SAMESITE_MAP
V10_PREFIX = _mod.V10_PREFIX
V11_PREFIX = _mod.V11_PREFIX
derive_key = _mod.derive_key
decrypt_v10 = _mod.decrypt_v10
decrypt_v11 = _mod.decrypt_v11
decrypt_cookie_value = _mod.decrypt_cookie_value
decrypt_exported_cookies = _mod.decrypt_exported_cookies
read_cookies = _mod.read_cookies
build_parser = _mod.build_parser
main = _mod.main

# ── Deterministic test key ────────────────────────────────────────────────────

TEST_PASSWORD = b"test-chrome-safe-storage-key"
TEST_KEY = derive_key(TEST_PASSWORD)

# v10 uses IV = b" " * 16 (Chrome convention on macOS)
V10_IV = b" " * 16


# ── Helpers ───────────────────────────────────────────────────────────────────


def _encrypt_v10(plaintext: str, key: bytes = TEST_KEY) -> bytes:
    """Encrypt a value using v10 (AES-128-CBC) like Chrome would."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7

    padder = PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(V10_IV))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    return V10_PREFIX + ct


def _encrypt_v11(plaintext: str, key: bytes = TEST_KEY) -> bytes:
    """Encrypt a value using v11 (AES-128-GCM) like Chrome would."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = b"\x00" * 12  # deterministic for tests
    aesgcm = AESGCM(key)
    ct_and_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return V11_PREFIX + nonce + ct_and_tag


def _create_cookie_db(db_path: Path, cookies: list[dict]) -> None:
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
    for c in cookies:
        conn.execute(
            "INSERT INTO cookies (host_key, name, path, encrypted_value, "
            "expires_utc, is_secure, is_httponly, samesite) VALUES (?,?,?,?,?,?,?,?)",
            (
                c["host_key"],
                c["name"],
                c.get("path", "/"),
                c.get("encrypted_value", b""),
                c.get("expires_utc", 0),
                int(c.get("is_secure", False)),
                int(c.get("is_httponly", False)),
                c.get("samesite", 0),
            ),
        )
    conn.commit()
    conn.close()


def _sample_cookies() -> list[dict]:
    """Return sample cookie rows for the test DB."""
    return [
        {
            "host_key": ".example.com",
            "name": "session_id",
            "encrypted_value": _encrypt_v10("abc123"),
            "path": "/",
            "expires_utc": 1735689600.0,
            "is_httponly": True,
            "is_secure": True,
            "samesite": 1,
        },
        {
            "host_key": ".other.com",
            "name": "pref",
            "encrypted_value": b"",
            "path": "/",
            "expires_utc": 0,
            "is_httponly": False,
            "is_secure": False,
            "samesite": 0,
        },
        {
            "host_key": ".secure.org",
            "name": "token_v11",
            "encrypted_value": _encrypt_v11("gcm-secret"),
            "path": "/api",
            "expires_utc": 9999999999.0,
            "is_httponly": True,
            "is_secure": True,
            "samesite": 2,
        },
    ]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cookie_db(tmp_path):
    """Create a temporary Chrome-style cookies DB with sample data."""
    db_path = tmp_path / "Chrome" / "Default" / "Cookies"
    _create_cookie_db(db_path, _sample_cookies())
    return tmp_path


# ── Unit tests: derive_key ────────────────────────────────────────────────────


class TestDeriveKey:
    def test_deterministic(self):
        assert derive_key(b"password") == derive_key(b"password")

    def test_16_bytes(self):
        assert len(derive_key(b"password")) == 16

    def test_different_passwords(self):
        assert derive_key(b"a") != derive_key(b"b")


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
        assert SAMESITE_MAP[-1] == "None"
        assert SAMESITE_MAP[0] == "Unspecified"
        assert SAMESITE_MAP[1] == "Lax"
        assert SAMESITE_MAP[2] == "Strict"
        assert SAMESITE_MAP[3] == "None"


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
        for key in ("domain", "name", "path", "value", "expires", "secure", "httpOnly", "sameSite"):
            assert key in row, f"Missing key: {key}"

    def test_encrypted_value_is_base64(self, cookie_db):
        db_path = cookie_db / "Chrome" / "Default" / "Cookies"
        rows = read_cookies(db_path)
        enc_row = [r for r in rows if r["_encrypted"]][0]
        # value should be valid base64
        base64.b64decode(enc_row["value"])

    def test_plaintext_cookie_has_empty_value(self, cookie_db):
        db_path = cookie_db / "Chrome" / "Default" / "Cookies"
        rows = read_cookies(db_path)
        plain = [r for r in rows if r["name"] == "pref"][0]
        assert plain["value"] == ""
        assert plain["_encrypted"] is False


# ── Integration: decrypt_exported_cookies ─────────────────────────────────────


class TestDecryptExportedCookies:
    def test_decrypts_all(self, cookie_db):
        db_path = cookie_db / "Chrome" / "Default" / "Cookies"
        rows = read_cookies(db_path)
        result = decrypt_exported_cookies(rows, TEST_KEY)
        by_name = {c["name"]: c for c in result}
        assert by_name["session_id"]["value"] == "abc123"
        assert by_name["pref"]["value"] == ""
        assert by_name["token_v11"]["value"] == "gcm-secret"

    def test_removes_encrypted_flag(self, cookie_db):
        db_path = cookie_db / "Chrome" / "Default" / "Cookies"
        rows = read_cookies(db_path)
        result = decrypt_exported_cookies(rows, TEST_KEY)
        for c in result:
            assert "_encrypted" not in c


# ── CLI: export ───────────────────────────────────────────────────────────────


class TestExportCLI:
    def test_export_writes_json(self, cookie_db, tmp_path):
        output = tmp_path / "out.json"
        with patch.object(_mod, "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_mod, "get_chrome_key", return_value=TEST_KEY):
            rc = main(["export", "--output", str(output)])
        assert rc == 0
        cookies = json.loads(output.read_text())
        assert len(cookies) == 3

        by_name = {c["name"]: c for c in cookies}
        assert by_name["session_id"]["value"] == "abc123"
        assert by_name["token_v11"]["value"] == "gcm-secret"

    def test_export_domain_filter(self, cookie_db, tmp_path):
        output = tmp_path / "filtered.json"
        with patch.object(_mod, "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_mod, "get_chrome_key", return_value=TEST_KEY):
            rc = main(["export", "--domain", "other", "--output", str(output)])
        assert rc == 0
        cookies = json.loads(output.read_text())
        assert len(cookies) == 1
        assert cookies[0]["name"] == "pref"

    def test_export_missing_db(self, tmp_path):
        output = tmp_path / "missing.json"
        fake_base = tmp_path / "nochrome"
        with patch.object(_mod, "CHROME_BASE", fake_base):
            rc = main(["export", "--output", str(output)])
        assert rc == 1

    def test_export_creates_parent_dirs(self, cookie_db, tmp_path):
        output = tmp_path / "deep" / "nested" / "cookies.json"
        with patch.object(_mod, "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_mod, "get_chrome_key", return_value=TEST_KEY):
            rc = main(["export", "--output", str(output)])
        assert rc == 0
        assert output.exists()

    def test_export_no_decrypt(self, cookie_db, tmp_path):
        output = tmp_path / "raw.json"
        with patch.object(_mod, "CHROME_BASE", cookie_db / "Chrome"):
            rc = main(["export", "--no-decrypt", "--output", str(output)])
        assert rc == 0
        cookies = json.loads(output.read_text())
        # Encrypted cookies should have base64 values, no _encrypted flag
        for c in cookies:
            assert "_encrypted" not in c
        # The session_id cookie was encrypted, so value should be base64
        enc = [c for c in cookies if c["name"] == "session_id"][0]
        raw = base64.b64decode(enc["value"])
        assert raw[:3] == V10_PREFIX

    def test_export_no_encrypted_value_in_output(self, cookie_db, tmp_path):
        output = tmp_path / "clean.json"
        with patch.object(_mod, "CHROME_BASE", cookie_db / "Chrome"), \
             patch.object(_mod, "get_chrome_key", return_value=TEST_KEY):
            rc = main(["export", "--output", str(output)])
        assert rc == 0
        cookies = json.loads(output.read_text())
        for c in cookies:
            assert "_encrypted" not in c


# ── CLI: import ───────────────────────────────────────────────────────────────


class TestImportCLI:
    def test_import_missing_file(self, tmp_path):
        rc = main(["import", str(tmp_path / "nope.json")])
        assert rc == 1

    def test_import_calls_playwright(self, tmp_path):
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text(json.dumps([
            {"name": "k", "value": "v", "domain": ".d.com", "path": "/"},
        ]))
        with patch.object(_mod, "import_cookies") as mock_imp:
            rc = main(["import", str(cookies_file)])
        assert rc == 0
        mock_imp.assert_called_once()
        assert mock_imp.call_args[0][0] == cookies_file


# ── CLI: general ──────────────────────────────────────────────────────────────


class TestMainCLI:
    def test_no_args_returns_1(self):
        rc = main([])
        assert rc == 1

    def test_unknown_command_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent"])
        assert exc_info.value.code == 2

    def test_build_parser_returns_parser(self):
        parser = build_parser()
        assert parser.prog == "cookie-sync"
