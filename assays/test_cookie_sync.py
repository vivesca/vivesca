#!/usr/bin/env python3
"""Tests for effectors/cookie-sync — Chrome cookie export/import."""

import hashlib
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

COOKIE_SYNC_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cookie-sync"

# ── Load effector via exec (extensionless script — can't use importlib) ───────

_ns: dict = {"__name__": "cookie_sync", "__file__": str(COOKIE_SYNC_PATH)}
exec(compile(COOKIE_SYNC_PATH.read_text(), str(COOKIE_SYNC_PATH), "exec"), _ns)

# Convenience aliases — these are plain functions, not methods
derive_key = _ns["derive_key"]
decrypt_v10 = _ns["decrypt_v10"]
decrypt_v11 = _ns["decrypt_v11"]
decrypt_cookie_value = _ns["decrypt_cookie_value"]
read_cookies = _ns["read_cookies"]
decrypt_exported_cookies = _ns["decrypt_exported_cookies"]
_samesite_str = _ns["_samesite_str"]
import_cookies = _ns["import_cookies"]
build_parser = _ns["build_parser"]
main = _ns["main"]

# ── Deterministic test key ────────────────────────────────────────────────────

TEST_PASSWORD = b"testpass"
TEST_KEY = hashlib.pbkdf2_hmac("sha1", TEST_PASSWORD, b"saltysalt", 1003, dklen=16)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _encrypt_v10(plaintext: str, key: bytes = TEST_KEY) -> bytes:
    """Encrypt a value using v10 (AES-128-CBC, IV=spaces, PKCS7) like Chrome."""
    from cryptography.hazmat.primitives import padding as sym_padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(b" " * 16))
    encryptor = cipher.encryptor()
    return b"v10" + encryptor.update(padded) + encryptor.finalize()


def _encrypt_v11(plaintext: str, key: bytes = TEST_KEY) -> bytes:
    """Encrypt a value using v11 (AES-128-GCM) like Chrome."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = b"\x00" * 12
    aesgcm = AESGCM(key)
    ct_and_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return b"v11" + nonce + ct_and_tag


def _make_chrome_db(db_path: Path, cookies: list[dict]) -> None:
    """Create a minimal Chrome Cookies SQLite DB at db_path."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE cookies ("
        "host_key TEXT, name TEXT, path TEXT, encrypted_value BLOB, "
        "expires_utc INTEGER, is_secure INTEGER, is_httponly INTEGER, samesite INTEGER)"
    )
    for c in cookies:
        enc = c.get("encrypted_value", b"")
        if isinstance(enc, str):
            enc = enc.encode("utf-8")
        conn.execute(
            "INSERT INTO cookies (host_key, name, path, encrypted_value, expires_utc, "
            "is_secure, is_httponly, samesite) VALUES (?,?,?,?,?,?,?,?)",
            (
                c["host_key"], c["name"], c["path"], enc,
                c.get("expires_utc", 0),
                int(c.get("is_secure", False)),
                int(c.get("is_httponly", False)),
                c.get("samesite", 0),
            ),
        )
    conn.commit()
    conn.close()


# ── Script structure tests ────────────────────────────────────────────────────


class TestCookieSyncScript:
    def test_script_exists(self):
        assert COOKIE_SYNC_PATH.exists()

    def test_script_is_executable(self):
        assert COOKIE_SYNC_PATH.stat().st_mode & 0o111

    def test_script_has_shebang(self):
        first_line = COOKIE_SYNC_PATH.read_text().splitlines()[0]
        assert "python" in first_line.lower()


# ── Unit tests: derive_key ────────────────────────────────────────────────────


class TestDeriveKey:
    def test_derives_16_byte_key(self):
        key = derive_key(b"somepassword")
        assert len(key) == 16

    def test_deterministic(self):
        assert derive_key(b"pass") == derive_key(b"pass")


# ── Unit tests: decrypt ──────────────────────────────────────────────────────


class TestDecryptV10:
    def test_roundtrip(self):
        assert decrypt_v10(_encrypt_v10("hello world"), TEST_KEY) == "hello world"

    def test_empty_string(self):
        assert decrypt_v10(_encrypt_v10(""), TEST_KEY) == ""


class TestDecryptV11:
    def test_roundtrip(self):
        assert decrypt_v11(_encrypt_v11("gcm-value"), TEST_KEY) == "gcm-value"

    def test_empty_string(self):
        assert decrypt_v11(_encrypt_v11(""), TEST_KEY) == ""


class TestDecryptCookieValue:
    def test_none_returns_empty(self):
        assert decrypt_cookie_value(None, TEST_KEY) == ""

    def test_v10_dispatch(self):
        assert decrypt_cookie_value(_encrypt_v10("x"), TEST_KEY) == "x"

    def test_v11_dispatch(self):
        assert decrypt_cookie_value(_encrypt_v11("y"), TEST_KEY) == "y"

    def test_plaintext_passthrough(self):
        assert decrypt_cookie_value(b"plain", TEST_KEY) == "plain"


# ── Unit tests: _samesite_str ─────────────────────────────────────────────────


class TestSameSiteStr:
    @pytest.mark.parametrize("val,expected", [
        (-1, "None"), (0, "Unspecified"), (1, "Lax"), (2, "Strict"),
        (3, "None"), (99, "Unspecified"),
    ])
    def test_mapping(self, val, expected):
        assert _samesite_str(val) == expected


# ── Unit tests: read_cookies ──────────────────────────────────────────────────


class TestReadCookies:
    def test_reads_all_cookies(self, tmp_path):
        db = tmp_path / "Cookies"
        _make_chrome_db(db, [
            {"host_key": ".example.com", "name": "sid", "path": "/",
             "encrypted_value": b"v10" + b"\x00" * 16},
            {"host_key": ".other.com", "name": "lang", "path": "/",
             "encrypted_value": b"plain"},
        ])
        cookies = read_cookies(db)
        assert len(cookies) == 2
        assert cookies[0]["name"] == "sid"
        assert cookies[1]["domain"] == ".other.com"

    def test_domain_filter(self, tmp_path):
        db = tmp_path / "Cookies"
        _make_chrome_db(db, [
            {"host_key": ".example.com", "name": "sid", "path": "/", "encrypted_value": b"x"},
            {"host_key": ".other.com", "name": "lang", "path": "/", "encrypted_value": b"y"},
        ])
        cookies = read_cookies(db, domain_filter="example")
        assert len(cookies) == 1
        assert cookies[0]["domain"] == ".example.com"

    def test_empty_db(self, tmp_path):
        db = tmp_path / "Cookies"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE cookies (host_key TEXT, name TEXT, path TEXT, "
            "encrypted_value BLOB, expires_utc INTEGER, is_secure INTEGER, "
            "is_httponly INTEGER, samesite INTEGER)"
        )
        conn.commit()
        conn.close()
        assert read_cookies(db) == []

    def test_value_is_base64_encoded(self, tmp_path):
        raw = b"\x01\x02\x03"
        db = tmp_path / "Cookies"
        _make_chrome_db(db, [
            {"host_key": ".example.com", "name": "t", "path": "/", "encrypted_value": raw},
        ])
        import base64
        cookies = read_cookies(db)
        assert cookies[0]["value"] == base64.b64encode(raw).decode("ascii")

    def test_empty_encrypted_value(self, tmp_path):
        db = tmp_path / "Cookies"
        _make_chrome_db(db, [
            {"host_key": ".example.com", "name": "t", "path": "/", "encrypted_value": b""},
        ])
        cookies = read_cookies(db)
        assert cookies[0]["value"] == ""
        assert cookies[0]["_encrypted"] is False


# ── Unit tests: decrypt_exported_cookies ──────────────────────────────────────


class TestDecryptExportedCookies:
    def test_decrypts_v10_cookie(self):
        import base64
        b64_val = base64.b64encode(_encrypt_v10("secret")).decode("ascii")
        cookies = [{"domain": ".x.com", "name": "c", "path": "/",
                     "value": b64_val, "_encrypted": True}]
        result = decrypt_exported_cookies(cookies, TEST_KEY)
        assert result[0]["value"] == "secret"
        assert "_encrypted" not in result[0]

    def test_skips_unencrypted(self):
        cookies = [{"domain": ".x.com", "name": "c", "path": "/",
                     "value": "hello", "_encrypted": False}]
        result = decrypt_exported_cookies(cookies, TEST_KEY)
        assert result[0]["value"] == "hello"
        assert "_encrypted" not in result[0]


# ── CLI tests ─────────────────────────────────────────────────────────────────


class TestCLI:
    def test_no_command_returns_1(self, capsys):
        assert main([]) == 1

    def test_export_missing_db(self, tmp_path):
        with patch.object(_ns["__builtins__"]["type"], "__init__", lambda *a, **k: None):
            pass  # no-op, just checking patch mechanism
        # Patch CHROME_BASE inside the module namespace
        _ns["CHROME_BASE"] = tmp_path / "nonexistent"
        try:
            assert main(["export"]) == 1
        finally:
            _ns["CHROME_BASE"] = _ns["Path"].home() / "Library" / "Application Support" / "Google" / "Chrome"

    def test_export_no_decrypt(self, tmp_path):
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "sid", "path": "/",
             "encrypted_value": b"plain"},
        ])
        out = tmp_path / "out.json"
        _ns["CHROME_BASE"] = tmp_path
        _ns["DEFAULT_OUTPUT"] = out
        try:
            assert main(["export", "--no-decrypt"]) == 0
        finally:
            _ns["CHROME_BASE"] = _ns["Path"].home() / "Library" / "Application Support" / "Google" / "Chrome"
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["name"] == "sid"

    def test_export_with_domain_filter(self, tmp_path):
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "sid", "path": "/", "encrypted_value": b"a"},
            {"host_key": ".other.com", "name": "lang", "path": "/", "encrypted_value": b"b"},
        ])
        out = tmp_path / "out.json"
        _ns["CHROME_BASE"] = tmp_path
        _ns["DEFAULT_OUTPUT"] = out
        try:
            assert main(["export", "--no-decrypt", "--domain", "example"]) == 0
        finally:
            _ns["CHROME_BASE"] = _ns["Path"].home() / "Library" / "Application Support" / "Google" / "Chrome"
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["domain"] == ".example.com"

    def test_export_with_decrypt(self, tmp_path):
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        enc_blob = _encrypt_v10("secret_value")
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "sid", "path": "/",
             "encrypted_value": enc_blob},
        ])
        out = tmp_path / "out.json"
        _ns["CHROME_BASE"] = tmp_path
        _ns["DEFAULT_OUTPUT"] = out
        original_gck = _ns["get_chrome_key"]
        _ns["get_chrome_key"] = lambda: TEST_KEY
        try:
            assert main(["export"]) == 0
        finally:
            _ns["CHROME_BASE"] = _ns["Path"].home() / "Library" / "Application Support" / "Google" / "Chrome"
            _ns["get_chrome_key"] = original_gck
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["value"] == "secret_value"

    def test_export_creates_output_dirs(self, tmp_path):
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        _make_chrome_db(db_dir / "Cookies", [])
        out = tmp_path / "deep" / "nested" / "cookies.json"
        _ns["CHROME_BASE"] = tmp_path
        _ns["DEFAULT_OUTPUT"] = out
        try:
            assert main(["export", "--no-decrypt"]) == 0
        finally:
            _ns["CHROME_BASE"] = _ns["Path"].home() / "Library" / "Application Support" / "Google" / "Chrome"
        assert out.exists()

    def test_import_missing_file(self, tmp_path):
        assert main(["import", str(tmp_path / "nope.json")]) == 1

    def test_import_calls_playwright(self, tmp_path):
        cj = tmp_path / "cookies.json"
        cj.write_text(json.dumps([{"name": "c", "domain": ".x.com", "path": "/", "value": "v"}]))
        fake = MagicMock()
        original = _ns["import_cookies"]
        _ns["import_cookies"] = fake
        try:
            assert main(["import", str(cj)]) == 0
        finally:
            _ns["import_cookies"] = original
        fake.assert_called_once()
        assert fake.call_args[0][0] == cj

    def test_import_browser_choice(self, tmp_path):
        cj = tmp_path / "cookies.json"
        cj.write_text("[]")
        fake = MagicMock()
        original = _ns["import_cookies"]
        _ns["import_cookies"] = fake
        try:
            assert main(["import", str(cj), "--browser", "firefox"]) == 0
        finally:
            _ns["import_cookies"] = original
        assert fake.call_args[1]["browser_type"] == "firefox" or fake.call_args[0][1] == "firefox"

    def test_custom_profile(self, tmp_path):
        profile_dir = tmp_path / "Profile1"
        profile_dir.mkdir()
        _make_chrome_db(profile_dir / "Cookies", [
            {"host_key": ".example.com", "name": "c", "path": "/", "encrypted_value": b"v"},
        ])
        out = tmp_path / "out.json"
        _ns["CHROME_BASE"] = tmp_path
        _ns["DEFAULT_OUTPUT"] = out
        try:
            assert main(["export", "--no-decrypt", "--profile", "Profile1"]) == 0
        finally:
            _ns["CHROME_BASE"] = _ns["Path"].home() / "Library" / "Application Support" / "Google" / "Chrome"
        data = json.loads(out.read_text())
        assert len(data) == 1


# ── Integration: roundtrip ────────────────────────────────────────────────────


class TestRoundtrip:
    def test_export_decrypt_roundtrip(self, tmp_path):
        enc_blob = _encrypt_v10("my_secret_cookie")
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "token", "path": "/",
             "encrypted_value": enc_blob, "is_secure": 1, "is_httponly": 1, "samesite": 1},
        ])
        out = tmp_path / "cookies.json"
        _ns["CHROME_BASE"] = tmp_path
        _ns["DEFAULT_OUTPUT"] = out
        original_gck = _ns["get_chrome_key"]
        _ns["get_chrome_key"] = lambda: TEST_KEY
        try:
            assert main(["export"]) == 0
        finally:
            _ns["CHROME_BASE"] = _ns["Path"].home() / "Library" / "Application Support" / "Google" / "Chrome"
            _ns["get_chrome_key"] = original_gck

        data = json.loads(out.read_text())
        assert len(data) == 1
        c = data[0]
        assert c["value"] == "my_secret_cookie"
        assert c["name"] == "token"
        assert c["domain"] == ".example.com"
        assert c["secure"] is True
        assert c["httpOnly"] is True
        assert c["sameSite"] == "Lax"
        assert "_encrypted" not in c
