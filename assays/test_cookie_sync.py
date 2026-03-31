#!/usr/bin/env python3
"""Tests for effectors/cookie-sync — Chrome cookie export/import."""

import base64
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

import pytest

COOKIE_SYNC_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cookie-sync"

# ── Module loading ─────────────────────────────────────────────────────────────

_MOD_CACHE: dict = {}


def _load():
    if _MOD_CACHE:
        return _MOD_CACHE["mod"]
    import importlib.util

    spec = importlib.util.spec_from_file_location("cookie_sync", COOKIE_SYNC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _MOD_CACHE["mod"] = mod
    return mod


# ── Helpers ────────────────────────────────────────────────────────────────────

# AES-128-CBC with IV=b' '*16, key derived from "testpass" via PBKDF2
_TEST_PASSWORD = b"testpass"
_TEST_KEY = hashlib.pbkdf2_hmac("sha1", _TEST_PASSWORD, b"saltysalt", 1003, dklen=16)
_PLAINTEXT = b"cookie_value_here"


def _aes_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt with AES-128-CBC, IV=spaces, PKCS7 padding. Returns v10-prefixed ciphertext."""
    from Crypto.Cipher import AES

    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len] * pad_len)
    cipher = AES.new(key, AES.MODE_CBC, b" " * 16)
    return b"v10" + cipher.encrypt(padded)


def _make_chrome_db(db_path: Path, cookies: list[dict]) -> None:
    """Create a minimal Chrome Cookies SQLite DB for testing."""
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
            (c["host_key"], c["name"], c["path"], enc, c.get("expires_utc", 0),
             int(c.get("is_secure", False)), int(c.get("is_httponly", False)),
             c.get("samesite", 0)),
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


# ── Unit tests: decryption helpers ─────────────────────────────────────────────


class TestDeriveKey:
    def test_derives_16_byte_key(self):
        mod = _load()
        key = mod.derive_encryption_key(b"somepassword")
        assert len(key) == 16

    def test_deterministic(self):
        mod = _load()
        k1 = mod.derive_encryption_key(b"pass")
        k2 = mod.derive_encryption_key(b"pass")
        assert k1 == k2


class TestDecryptCookieValue:
    def test_unencrypted_passthrough(self):
        mod = _load()
        result = mod.decrypt_cookie_value(b"plain_value", _TEST_KEY)
        assert result == "plain_value"

    def test_v10_roundtrip(self):
        encrypted = _aes_encrypt(_PLAINTEXT, _TEST_KEY)
        assert encrypted[:3] == b"v10"
        mod = _load()
        result = mod.decrypt_cookie_value(encrypted, _TEST_KEY)
        assert result == _PLAINTEXT.decode("utf-8")

    def test_invalid_padding_returns_best_effort(self):
        # 3 bytes of v10 + 16 bytes of garbage (no valid PKCS7 padding)
        mod = _load()
        bad = b"v10" + os.urandom(16)
        result = mod.decrypt_cookie_value(bad, _TEST_KEY)
        assert isinstance(result, str)


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
        mod = _load()
        cookies = mod.read_cookies(db)
        assert len(cookies) == 2
        assert cookies[0]["name"] == "sid"
        assert cookies[1]["domain"] == ".other.com"

    def test_domain_filter(self, tmp_path):
        db = tmp_path / "Cookies"
        _make_chrome_db(db, [
            {"host_key": ".example.com", "name": "sid", "path": "/", "encrypted_value": b"x"},
            {"host_key": ".other.com", "name": "lang", "path": "/", "encrypted_value": b"y"},
        ])
        mod = _load()
        cookies = mod.read_cookies(db, domain_filter="example")
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
        mod = _load()
        cookies = mod.read_cookies(db)
        assert cookies == []

    def test_value_is_base64(self, tmp_path):
        raw = b"\x01\x02\x03"
        db = tmp_path / "Cookies"
        _make_chrome_db(db, [
            {"host_key": ".example.com", "name": "test", "path": "/",
             "encrypted_value": raw},
        ])
        mod = _load()
        cookies = mod.read_cookies(db)
        assert cookies[0]["value"] == base64.b64encode(raw).decode("ascii")


# ── Unit tests: decrypt_exported_cookies ──────────────────────────────────────


class TestDecryptExportedCookies:
    def test_decrypts_v10_cookie(self):
        encrypted_blob = _aes_encrypt(b"secret", _TEST_KEY)
        b64_val = base64.b64encode(encrypted_blob).decode("ascii")
        cookies = [{"domain": ".example.com", "name": "c", "path": "/",
                     "value": b64_val, "_encrypted": True}]
        mod = _load()
        result = mod.decrypt_exported_cookies(cookies, _TEST_KEY)
        assert result[0]["value"] == "secret"
        assert "_encrypted" not in result[0]

    def test_skips_unencrypted(self):
        cookies = [{"domain": ".x.com", "name": "c", "path": "/",
                     "value": "hello", "_encrypted": False}]
        mod = _load()
        result = mod.decrypt_exported_cookies(cookies, _TEST_KEY)
        assert result[0]["value"] == "hello"


# ── Unit tests: _samesite_str ─────────────────────────────────────────────────


class TestSameSiteStr:
    @pytest.mark.parametrize("val,expected", [
        (-1, "None"), (0, "Unspecified"), (1, "Lax"), (2, "Strict"),
        (3, "None"), (99, "Unspecified"),
    ])
    def test_mapping(self, val, expected):
        mod = _load()
        assert mod._samesite_str(val) == expected


# ── Unit tests: CLI ────────────────────────────────────────────────────────────


class TestCLI:
    def test_no_command_returns_1(self):
        mod = _load()
        assert mod.main([]) == 1

    def test_export_missing_db(self, tmp_path, monkeypatch):
        mod = _load()
        monkeypatch.setattr(mod, "CHROME_BASE", tmp_path / "nonexistent")
        assert mod.main(["export"]) == 1

    def test_export_success(self, tmp_path, monkeypatch):
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "sid", "path": "/",
             "encrypted_value": b"plain"},
        ])
        out = tmp_path / "out.json"

        mod = _load()
        monkeypatch.setattr(mod, "CHROME_BASE", tmp_path)
        monkeypatch.setattr(mod, "DEFAULT_OUTPUT", out)
        # Skip decryption — no keychain on Linux
        assert mod.main(["export", "--no-decrypt"]) == 0
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["name"] == "sid"

    def test_export_with_domain_filter(self, tmp_path, monkeypatch):
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "sid", "path": "/", "encrypted_value": b"a"},
            {"host_key": ".other.com", "name": "lang", "path": "/", "encrypted_value": b"b"},
        ])
        out = tmp_path / "out.json"

        mod = _load()
        monkeypatch.setattr(mod, "CHROME_BASE", tmp_path)
        monkeypatch.setattr(mod, "DEFAULT_OUTPUT", out)
        assert mod.main(["export", "--no-decrypt", "--domain", "example"]) == 0
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["domain"] == ".example.com"

    def test_export_with_decrypt(self, tmp_path, monkeypatch):
        """Full export with mocked keychain returns decrypted cookie."""
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        enc_blob = _aes_encrypt(b"secret_value", _TEST_KEY)
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "sid", "path": "/",
             "encrypted_value": enc_blob},
        ])
        out = tmp_path / "out.json"

        mod = _load()
        monkeypatch.setattr(mod, "CHROME_BASE", tmp_path)
        monkeypatch.setattr(mod, "DEFAULT_OUTPUT", out)
        monkeypatch.setattr(mod, "get_chrome_key", lambda: _TEST_PASSWORD)
        assert mod.main(["export"]) == 0
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["value"] == "secret_value"

    def test_export_output_dir_created(self, tmp_path, monkeypatch):
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        _make_chrome_db(db_dir / "Cookies", [])
        out = tmp_path / "deep" / "nested" / "cookies.json"

        mod = _load()
        monkeypatch.setattr(mod, "CHROME_BASE", tmp_path)
        monkeypatch.setattr(mod, "DEFAULT_OUTPUT", out)
        assert mod.main(["export", "--no-decrypt"]) == 0
        assert out.exists()

    def test_import_missing_file(self, tmp_path):
        mod = _load()
        assert mod.main(["import", str(tmp_path / "nope.json")]) == 1

    def test_import_calls_playwright(self, tmp_path, monkeypatch):
        cookies = [{"name": "c", "domain": ".x.com", "path": "/", "value": "v"}]
        cj = tmp_path / "cookies.json"
        cj.write_text(json.dumps(cookies))

        called = {}

        def fake_import_cookies(cookies_path, browser_type="chromium"):
            called["path"] = cookies_path
            called["browser"] = browser_type

        mod = _load()
        monkeypatch.setattr(mod, "import_cookies", fake_import_cookies)
        assert mod.main(["import", str(cj)]) == 0
        assert called["path"] == cj
        assert called["browser"] == "chromium"

    def test_import_with_browser_choice(self, tmp_path, monkeypatch):
        cj = tmp_path / "cookies.json"
        cj.write_text("[]")

        called = {}

        def fake_import_cookies(cookies_path, browser_type="chromium"):
            called["browser"] = browser_type

        mod = _load()
        monkeypatch.setattr(mod, "import_cookies", fake_import_cookies)
        assert mod.main(["import", str(cj), "--browser", "firefox"]) == 0
        assert called["browser"] == "firefox"

    def test_custom_profile(self, tmp_path, monkeypatch):
        profile_dir = tmp_path / "Profile1"
        profile_dir.mkdir()
        _make_chrome_db(profile_dir / "Cookies", [
            {"host_key": ".example.com", "name": "c", "path": "/", "encrypted_value": b"v"},
        ])
        out = tmp_path / "out.json"

        mod = _load()
        monkeypatch.setattr(mod, "CHROME_BASE", tmp_path)
        monkeypatch.setattr(mod, "DEFAULT_OUTPUT", out)
        assert mod.main(["export", "--no-decrypt", "--profile", "Profile1"]) == 0
        data = json.loads(out.read_text())
        assert len(data) == 1


# ── Integration: roundtrip ────────────────────────────────────────────────────


class TestRoundtrip:
    def test_export_decrypt_roundtrip(self, tmp_path, monkeypatch):
        """Encrypt a value via AES, store in mock DB, export, verify decrypted output."""
        db_dir = tmp_path / "Default"
        db_dir.mkdir()
        enc_blob = _aes_encrypt(b"my_secret_cookie", _TEST_KEY)
        _make_chrome_db(db_dir / "Cookies", [
            {"host_key": ".example.com", "name": "token", "path": "/",
             "encrypted_value": enc_blob, "is_secure": 1, "is_httponly": 1, "samesite": 1},
        ])
        out = tmp_path / "cookies.json"

        mod = _load()
        monkeypatch.setattr(mod, "CHROME_BASE", tmp_path)
        monkeypatch.setattr(mod, "DEFAULT_OUTPUT", out)
        monkeypatch.setattr(mod, "get_chrome_key", lambda: _TEST_PASSWORD)
        assert mod.main(["export"]) == 0

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
