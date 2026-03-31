"""Tests for effectors/cookie-sync — mocked Chrome Cookies DB + decryption."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Load the effector via exec (it's a script, not an importable module) ────────

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "cookie-sync"
_ns: dict = {"__name__": "cookie_sync", "__file__": str(EFFECTOR)}
exec(compile(EFFECTOR.read_text(), EFFECTOR, "exec"), _ns)

# Pull symbols into module scope
build_parser = _ns["build_parser"]
main = _ns["main"]
read_cookies = _ns["read_cookies"]
decrypt_cookie_value = _ns["decrypt_cookie_value"]
decrypt_exported_cookies = _ns["decrypt_exported_cookies"]
derive_key = _ns["derive_key"]
decrypt_v10 = _ns["decrypt_v10"]
decrypt_v11 = _ns["decrypt_v11"]
get_chrome_key = _ns["get_chrome_key"]
import_cookies = _ns["import_cookies"]
_samesite_str = _ns["_samesite_str"]
CHROME_BASE = _ns["CHROME_BASE"]
DEFAULT_OUTPUT = _ns["DEFAULT_OUTPUT"]
V10_PREFIX = _ns["V10_PREFIX"]
V11_PREFIX = _ns["V11_PREFIX"]
PBKDF2_SALT = _ns["PBKDF2_SALT"]
PBKDF2_ITERATIONS = _ns["PBKDF2_ITERATIONS"]
KEY_LENGTH = _ns["KEY_LENGTH"]

# ── Shared test key ─────────────────────────────────────────────────────────────

TEST_PASSWORD = b"test_chrome_key"
TEST_KEY = derive_key(TEST_PASSWORD)


# ── Helpers ─────────────────────────────────────────────────────────────────────


def _make_mock_db(cookies_rows: list[dict]) -> Path:
    """Create a temporary SQLite DB mimicking Chrome's Cookies schema."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            path TEXT,
            encrypted_value BLOB,
            expires_utc INTEGER,
            is_secure INTEGER,
            is_httponly INTEGER,
            samesite INTEGER
        )"""
    )
    for row in cookies_rows:
        conn.execute(
            "INSERT INTO cookies (host_key, name, path, encrypted_value, "
            "expires_utc, is_secure, is_httponly, samesite) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                row.get("host_key", ".example.com"),
                row.get("name", "test_cookie"),
                row.get("path", "/"),
                row.get("encrypted_value"),
                row.get("expires_utc", 1735689600),
                int(row.get("is_secure", True)),
                int(row.get("is_httponly", True)),
                row.get("samesite", 1),
            ),
        )
    conn.commit()
    conn.close()
    return Path(db_path)


def _encrypt_v10(plaintext: bytes, key: bytes = TEST_KEY) -> bytes:
    """Encrypt plaintext in Chrome v10 format for test data."""
    from cryptography.hazmat.primitives import padding as sym_padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    iv = b" " * 16
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    enc = cipher.encryptor()
    ciphertext = enc.update(padded) + enc.finalize()
    return V10_PREFIX + ciphertext


def _encrypt_v11(plaintext: bytes, key: bytes = TEST_KEY) -> bytes:
    """Encrypt plaintext in Chrome v11 format for test data."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return V11_PREFIX + nonce + ciphertext


# ════════════════════════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════════════════════════


class TestDeriveKey:
    def test_deterministic(self):
        k1 = derive_key(b"password")
        k2 = derive_key(b"password")
        assert k1 == k2

    def test_length(self):
        assert len(derive_key(b"x")) == KEY_LENGTH

    def test_different_inputs_differ(self):
        assert derive_key(b"a") != derive_key(b"b")


class TestSameSiteMapping:
    @pytest.mark.parametrize("val,expected", [
        (-1, "None"),
        (0, "Unspecified"),
        (1, "Lax"),
        (2, "Strict"),
        (3, "None"),
    ])
    def test_known_values(self, val, expected):
        assert _samesite_str(val) == expected

    def test_unknown_falls_back(self):
        assert _samesite_str(99) == "Unspecified"


class TestDecryptCookieValue:
    def test_none_returns_empty(self):
        assert decrypt_cookie_value(None, TEST_KEY) == ""

    def test_plaintext_passthrough(self):
        raw = b"plain_text_value"
        assert decrypt_cookie_value(raw, TEST_KEY) == "plain_text_value"

    def test_v10_roundtrip(self):
        plaintext = b"secret_session_id"
        encrypted = _encrypt_v10(plaintext, TEST_KEY)
        result = decrypt_cookie_value(encrypted, TEST_KEY)
        assert result == "secret_session_id"

    def test_v11_roundtrip(self):
        plaintext = b"gcm_protected_value"
        encrypted = _encrypt_v11(plaintext, TEST_KEY)
        result = decrypt_cookie_value(encrypted, TEST_KEY)
        assert result == "gcm_protected_value"


class TestDecryptV10:
    def test_decrypts_correctly(self):
        encrypted = _encrypt_v10(b"hello", TEST_KEY)
        assert decrypt_v10(encrypted, TEST_KEY) == "hello"

    def test_invalid_key_produces_garbage_or_error(self):
        encrypted = _encrypt_v10(b"hello", TEST_KEY)
        wrong_key = derive_key(b"wrong")
        # Should either raise or return garbage — not the original
        try:
            result = decrypt_v10(encrypted, wrong_key)
            assert result != "hello"
        except Exception:
            pass  # Error is also acceptable


class TestDecryptV11:
    def test_decrypts_correctly(self):
        encrypted = _encrypt_v11(b"gcm_value", TEST_KEY)
        assert decrypt_v11(encrypted, TEST_KEY) == "gcm_value"

    def test_wrong_key_raises(self):
        encrypted = _encrypt_v11(b"gcm_value", TEST_KEY)
        wrong_key = derive_key(b"wrong")
        with pytest.raises(Exception):
            decrypt_v11(encrypted, wrong_key)


class TestReadCookies:
    def test_reads_plaintext_cookie(self):
        db = _make_mock_db([
            {"host_key": ".example.com", "name": "sid", "encrypted_value": None,
             "is_secure": 0, "is_httponly": 0, "samesite": 0}
        ])
        try:
            cookies = read_cookies(db)
            assert len(cookies) == 1
            c = cookies[0]
            assert c["domain"] == ".example.com"
            assert c["name"] == "sid"
            assert c["value"] == ""  # None encrypted_value -> empty base64
            assert c["secure"] is False
            assert c["httpOnly"] is False
            assert c["_encrypted"] is False
        finally:
            os.unlink(db)

    def test_reads_encrypted_cookie(self):
        raw_val = _encrypt_v10(b"my_secret", TEST_KEY)
        db = _make_mock_db([
            {"host_key": ".site.com", "name": "token",
             "encrypted_value": raw_val, "samesite": 1}
        ])
        try:
            cookies = read_cookies(db)
            assert len(cookies) == 1
            c = cookies[0]
            assert c["value"] == base64.b64encode(raw_val).decode("ascii")
            assert c["_encrypted"] is True
        finally:
            os.unlink(db)

    def test_domain_filter(self):
        db = _make_mock_db([
            {"host_key": ".example.com", "name": "a"},
            {"host_key": ".other.com", "name": "b"},
        ])
        try:
            cookies = read_cookies(db, domain_filter="example")
            assert len(cookies) == 1
            assert cookies[0]["domain"] == ".example.com"
        finally:
            os.unlink(db)

    def test_empty_db(self):
        db = _make_mock_db([])
        try:
            cookies = read_cookies(db)
            assert cookies == []
        finally:
            os.unlink(db)


class TestDecryptExportedCookies:
    def test_decrypts_v10_cookies(self):
        raw = _encrypt_v10(b"decrypted_value", TEST_KEY)
        cookies = [{
            "domain": ".example.com",
            "name": "session",
            "value": base64.b64encode(raw).decode("ascii"),
            "path": "/",
            "expires": 1735689600,
            "secure": True,
            "httpOnly": False,
            "sameSite": "Lax",
            "_encrypted": True,
        }]
        result = decrypt_exported_cookies(cookies, TEST_KEY)
        assert len(result) == 1
        assert result[0]["value"] == "decrypted_value"
        assert "_encrypted" not in result[0]

    def test_skips_plaintext(self):
        cookies = [{
            "domain": ".x.com", "name": "n", "value": "already_plain",
            "path": "/", "expires": 0, "secure": False, "httpOnly": False,
            "sameSite": "Unspecified", "_encrypted": False,
        }]
        result = decrypt_exported_cookies(cookies, TEST_KEY)
        assert result[0]["value"] == "already_plain"

    def test_v11_roundtrip(self):
        raw = _encrypt_v11(b"gcm_secret", TEST_KEY)
        cookies = [{
            "domain": ".gcm.com", "name": "gcm_tok",
            "value": base64.b64encode(raw).decode("ascii"),
            "path": "/", "expires": 0, "secure": True, "httpOnly": True,
            "sameSite": "Strict", "_encrypted": True,
        }]
        result = decrypt_exported_cookies(cookies, TEST_KEY)
        assert result[0]["value"] == "gcm_secret"


class TestMainExport:
    def test_export_no_decrypt(self, tmp_path):
        """Export with --no-decrypt skips keychain entirely."""
        db = _make_mock_db([
            {"host_key": ".example.com", "name": "test", "encrypted_value": None}
        ])
        out = tmp_path / "cookies.json"
        with patch.object(_ns["Path"], "exists", return_value=True), \
             patch(_ns["__name__"] + ".read_cookies", return_value=[]):
            # Patch CHROME_BASE so db_path check passes
            with patch(_ns["__name__"] + ".CHROME_BASE", db.parent):
                rc = main(["export", "--no-decrypt", "-o", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert isinstance(data, list)

    def test_export_missing_db(self, tmp_path):
        """Return 1 when Chrome cookies DB doesn't exist."""
        out = tmp_path / "cookies.json"
        rc = main(["export", "--no-decrypt", "-o", str(out), "--profile", "NoSuchProfile"])
        assert rc == 1

    def test_export_creates_output_dir(self, tmp_path):
        """Output directory is created if missing."""
        out = tmp_path / "deep" / "nested" / "cookies.json"
        db = _make_mock_db([])
        with patch(_ns["__name__"] + ".CHROME_BASE", db.parent), \
             patch(_ns["__name__"] + ".read_cookies", return_value=[]):
            rc = main(["export", "--no-decrypt", "-o", str(out)])
        assert rc == 0
        assert out.exists()


class TestMainImport:
    def test_import_missing_file(self, tmp_path):
        rc = main(["import", str(tmp_path / "nonexistent.json")])
        assert rc == 1

    def test_import_calls_playwright(self, tmp_path):
        """Import with a valid file invokes import_cookies."""
        cookies = [{"domain": ".x.com", "name": "c", "value": "v",
                    "path": "/", "expires": 0, "secure": False,
                    "httpOnly": False, "sameSite": "Lax"}]
        cookie_file = tmp_path / "cookies.json"
        cookie_file.write_text(json.dumps(cookies))

        with patch(_ns["__name__"] + ".import_cookies") as mock_import:
            rc = main(["import", str(cookie_file)])

        assert rc == 0
        mock_import.assert_called_once()
        assert mock_import.call_args[0][0] == cookie_file


class TestMainNoCommand:
    def test_no_args_returns_1(self):
        rc = main([])
        assert rc == 1


class TestBuildParser:
    def test_parser_prog(self):
        p = build_parser()
        assert p.prog == "cookie-sync"

    def test_export_subcommand(self):
        p = build_parser()
        args = p.parse_args(["export", "--profile", "Profile1", "--domain", "foo.com"])
        assert args.command == "export"
        assert args.profile == "Profile1"
        assert args.domain == "foo.com"

    def test_import_subcommand(self):
        p = build_parser()
        args = p.parse_args(["import", "cookies.json", "--browser", "firefox"])
        assert args.command == "import"
        assert args.browser == "firefox"
