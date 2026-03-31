"""Tests for effectors/photos.py — photo access script."""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "photos.py"

# ─── Load the effector script into an isolated namespace ──────────────────────

_NS: dict = {}
exec(open(SCRIPT).read(), _NS)

_cd_timestamp = _NS["_cd_timestamp"]
_cd_to_datetime = _NS["_cd_to_datetime"]
_print_photos = _NS["print_photos"]
_PhotosDB = _NS["PhotosDB"]
_export_photos = _NS["export_photos"]
_find_original = _NS["_find_original"]
_find_derivative = _NS["_find_derivative"]
_CD_EPOCH = _NS["_CD_EPOCH"]
_CD_OFFSET = _NS["_CD_OFFSET"]
_HKT = _NS["_HKT"]


# ─── Minimal Photos.sqlite schema ────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ZASSET (
    Z_PK INTEGER PRIMARY KEY,
    ZUUID TEXT,
    ZDATECREATED REAL,
    ZDIRECTORY TEXT,
    ZFILENAME TEXT,
    ZUNIFORMTYPEIDENTIFIER TEXT,
    ZWIDTH INTEGER,
    ZHEIGHT INTEGER,
    ZKIND INTEGER,
    ZTRASHEDSTATE INTEGER DEFAULT 0,
    ZHIDDEN INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ZADDITIONALASSETATTRIBUTES (
    Z_PK INTEGER PRIMARY KEY,
    ZASSET INTEGER,
    ZORIGINALFILENAME TEXT,
    ZTITLE TEXT,
    ZASSETDESCRIPTION INTEGER
);
CREATE TABLE IF NOT EXISTS ZASSETDESCRIPTION (
    Z_PK INTEGER PRIMARY KEY,
    ZLONGDESCRIPTION TEXT
);
CREATE TABLE IF NOT EXISTS ZDETECTEDFACE (
    Z_PK INTEGER PRIMARY KEY,
    ZASSETFORFACE INTEGER,
    ZPERSONFORFACE INTEGER
);
CREATE TABLE IF NOT EXISTS ZPERSON (
    Z_PK INTEGER PRIMARY KEY,
    ZDISPLAYNAME TEXT,
    ZFULLNAME TEXT
);
CREATE TABLE IF NOT EXISTS ZINTERNALRESOURCE (
    Z_PK INTEGER PRIMARY KEY,
    ZASSET INTEGER,
    ZRESOURCETYPE INTEGER,
    ZDATASTORESUBTYPE INTEGER,
    ZLOCALAVAILABILITY INTEGER
);
"""


def _cd_ts_for(dt: datetime) -> float:
    """Helper: produce a Core Data timestamp for a given datetime."""
    return dt.timestamp() - _CD_OFFSET


def _seed_db(db_path: Path, rows: list[dict]) -> None:
    """Insert photo rows into the test database.

    Each row dict may contain keys:
        uuid, date_created (datetime), directory, filename, uti,
        width, height, original_filename, title, description,
        people (list[str]), local_avail
    """
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA_SQL)

    for i, r in enumerate(rows, start=1):
        uuid = r.get("uuid", f"aaaaaaaa-0000-0000-0000-{i:012d}")
        cd_ts = _cd_ts_for(r["date_created"]) if "date_created" in r else 0.0
        directory = r.get("directory", "A")
        filename = r.get("filename", f"{uuid}.heic")
        uti = r.get("uti", "public.heic")
        width = r.get("width", 4032)
        height = r.get("height", 3024)

        conn.execute(
            "INSERT INTO ZASSET (Z_PK, ZUUID, ZDATECREATED, ZDIRECTORY, ZFILENAME, "
            "ZUNIFORMTYPEIDENTIFIER, ZWIDTH, ZHEIGHT, ZKIND, ZTRASHEDSTATE, ZHIDDEN) "
            "VALUES (?,?,?,?,?,?,?, ?,0,?,?)",
            (i, uuid, cd_ts, directory, filename, uti, width, height,
             r.get("trashed", 0), r.get("hidden", 0)),
        )

        orig_fname = r.get("original_filename", filename)
        title = r.get("title")
        desc_text = r.get("description")
        people = r.get("people", [])
        local_avail = r.get("local_avail", 1)

        desc_pk = i
        conn.execute(
            "INSERT INTO ZASSETDESCRIPTION (Z_PK, ZLONGDESCRIPTION) VALUES (?,?)",
            (desc_pk, desc_text),
        )
        conn.execute(
            "INSERT INTO ZADDITIONALASSETATTRIBUTES "
            "(Z_PK, ZASSET, ZORIGINALFILENAME, ZTITLE, ZASSETDESCRIPTION) "
            "VALUES (?,?,?,?,?)",
            (i, i, orig_fname, title, desc_pk),
        )

        for j, person_name in enumerate(people, start=1):
            person_pk = i * 100 + j
            conn.execute(
                "INSERT OR IGNORE INTO ZPERSON (Z_PK, ZDISPLAYNAME, ZFULLNAME) VALUES (?,?,?)",
                (person_pk, person_name, person_name),
            )
            conn.execute(
                "INSERT INTO ZDETECTEDFACE (Z_PK, ZASSETFORFACE, ZPERSONFORFACE) VALUES (?,?,?)",
                (i * 100 + j, i, person_pk),
            )

        conn.execute(
            "INSERT INTO ZINTERNALRESOURCE "
            "(Z_PK, ZASSET, ZRESOURCETYPE, ZDATASTORESUBTYPE, ZLOCALAVAILABILITY) "
            "VALUES (?,?,0,1,?)",
            (i, i, local_avail),
        )

    conn.commit()
    conn.close()


# ─── Sample data ──────────────────────────────────────────────────────────────

_SAMPLE_ROWS = [
    {
        "uuid": "abcdef01-2222-3333-4444-555566667777",
        "date_created": datetime(2025, 6, 15, 12, 0, 0, tzinfo=_HKT),
        "directory": "A",
        "filename": "abcdef01_1.heic",
        "uti": "public.heic",
        "original_filename": "IMG_5001.heic",
        "title": "Beach Sunset",
        "description": "Golden hour at the coast",
        "people": ["Alice", "Bob"],
        "local_avail": 1,
    },
    {
        "uuid": "bcdef012-3333-4444-5555-666677778888",
        "date_created": datetime(2025, 6, 14, 9, 30, 0, tzinfo=_HKT),
        "directory": "B",
        "filename": "bcdef012_1.jpeg",
        "uti": "public.jpeg",
        "original_filename": "IMG_5000.jpeg",
        "title": "Morning Coffee",
        "description": None,
        "people": [],
        "local_avail": 1,
    },
    {
        "uuid": "cdef0123-4444-5555-6666-777788889999",
        "date_created": datetime(2025, 5, 1, 8, 0, 0, tzinfo=_HKT),
        "directory": "C",
        "filename": "cdef0123_1.heic",
        "uti": "public.heic",
        "original_filename": "IMG_4000.heic",
        "title": None,
        "description": "Office desk photo",
        "people": ["Charlie"],
        "local_avail": 0,  # iCloud only
    },
    {
        # Trashed — should not appear in normal queries
        "uuid": "dead0000-0000-0000-0000-000000000000",
        "date_created": datetime(2025, 6, 15, 1, 0, 0, tzinfo=_HKT),
        "directory": "D",
        "filename": "dead_trash.heic",
        "uti": "public.heic",
        "original_filename": "trashed.heic",
        "trashed": 1,
        "local_avail": 1,
    },
    {
        # Hidden — should not appear in normal queries
        "uuid": "beef0000-0000-0000-0000-000000000000",
        "date_created": datetime(2025, 6, 15, 2, 0, 0, tzinfo=_HKT),
        "directory": "E",
        "filename": "beef_hidden.heic",
        "uti": "public.heic",
        "original_filename": "hidden.heic",
        "hidden": 1,
        "local_avail": 1,
    },
]


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def photos_db(tmp_path, monkeypatch):
    """Create a temporary Photos.sqlite and return a connected PhotosDB."""
    db_file = tmp_path / "Photos.sqlite"
    _seed_db(db_file, _SAMPLE_ROWS)
    monkeypatch.setitem(_NS, "DB_PATH", db_file)
    db = _PhotosDB()
    yield db
    db.close()


# ─── Script-level tests ──────────────────────────────────────────────────────


class TestScriptBasics:
    def test_script_exists(self):
        assert SCRIPT.exists()
        assert SCRIPT.is_file()

    def test_no_syntax_errors(self):
        import ast
        ast.parse(open(SCRIPT).read())


# ─── Core Data timestamp helpers ─────────────────────────────────────────────


class TestCdTimestamp:
    def test_epoch_is_2001_01_01(self):
        assert _CD_EPOCH == datetime(2001, 1, 1, tzinfo=timezone.utc)

    def test_cd_offset_value(self):
        # 2001-01-01 00:00:00 UTC as Unix timestamp
        assert _CD_OFFSET == 978307200.0

    def test_roundtrip(self):
        dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=_HKT)
        cd = _cd_timestamp(dt)
        result = _cd_to_datetime(cd)
        assert result == dt

    def test_roundtrip_utc_midnight(self):
        dt = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        cd = _cd_timestamp(dt)
        # HKT is UTC+8, so midnight UTC = 8am HKT
        result = _cd_to_datetime(cd)
        expected = datetime(2025, 1, 1, 8, 0, 0, tzinfo=_HKT)
        assert result == expected

    def test_cd_epoch_returns_zero(self):
        dt = datetime(2001, 1, 1, tzinfo=timezone.utc)
        assert _cd_timestamp(dt) == 0.0

    def test_cd_to_datetime_positive(self):
        # 1 second after Core Data epoch = 2001-01-01 00:00:01 UTC = 08:00:01 HKT
        dt = _cd_to_datetime(1.0)
        expected_hkt = datetime(2001, 1, 1, 8, 0, 1, tzinfo=_HKT)
        assert dt == expected_hkt

    def test_cd_to_datetime_negative(self):
        # 1 second before Core Data epoch = 2000-12-31 23:59:59 UTC = 2001-01-01 07:59:59 HKT
        dt = _cd_to_datetime(-1.0)
        expected_hkt = datetime(2001, 1, 1, 7, 59, 59, tzinfo=_HKT)
        assert dt == expected_hkt


# ─── print_photos ─────────────────────────────────────────────────────────────


class TestPrintPhotos:
    def test_empty_list(self, capsys):
        _print_photos([])
        out = capsys.readouterr().out
        assert "Found 0 items" in out

    def test_single_photo(self, capsys):
        cd_ts = _cd_ts_for(datetime(2025, 6, 15, 12, 0, 0, tzinfo=_HKT))
        photos = [{
            "ZUUID": "abcdef01-2222-3333-4444-555566667777",
            "ZDATECREATED": cd_ts,
            "ZFILENAME": "photo.heic",
            "ZORIGINALFILENAME": "IMG_5001.heic",
            "description": "A nice photo",
            "people": "Alice, Bob",
            "ZTITLE": "Beach",
            "local_avail": 1,
        }]
        _print_photos(photos)
        out = capsys.readouterr().out
        assert "Found 1 items" in out
        assert "abcdef01" in out
        assert "2025-06-15 12:00:00" in out
        assert "Alice, Bob" in out
        assert "Beach" in out
        assert "A nice photo" in out

    def test_no_labels_shows_no_labels(self, capsys):
        cd_ts = _cd_ts_for(datetime(2025, 6, 15, 12, 0, 0, tzinfo=_HKT))
        photos = [{
            "ZUUID": "aaaa0000-0000-0000-0000-000000000000",
            "ZDATECREATED": cd_ts,
            "ZFILENAME": "photo.heic",
            "ZORIGINALFILENAME": "IMG.heic",
            "description": None,
            "people": None,
            "ZTITLE": None,
            "local_avail": 1,
        }]
        _print_photos(photos)
        out = capsys.readouterr().out
        assert "(no labels)" in out

    def test_icloud_indicator(self, capsys):
        photos = [{
            "ZUUID": "aaaa0000-0000-0000-0000-000000000000",
            "ZDATECREATED": 0.0,
            "ZFILENAME": "p.heic",
            "local_avail": 0,
        }]
        _print_photos(photos)
        out = capsys.readouterr().out
        assert "[iCloud]" in out

    def test_no_icloud_indicator_when_local(self, capsys):
        photos = [{
            "ZUUID": "aaaa0000-0000-0000-0000-000000000000",
            "ZDATECREATED": 0.0,
            "ZFILENAME": "p.heic",
            "local_avail": 1,
        }]
        _print_photos(photos)
        out = capsys.readouterr().out
        assert "[iCloud]" not in out

    def test_no_date_shows_question_mark(self, capsys):
        photos = [{
            "ZUUID": "aaaa0000-0000-0000-0000-000000000000",
            "ZDATECREATED": None,
            "ZFILENAME": "p.heic",
        }]
        _print_photos(photos)
        out = capsys.readouterr().out
        assert "?" in out

    def test_description_2Q_suppressed(self, capsys):
        """The literal string '2Q' is a common meaningless default — suppressed."""
        photos = [{
            "ZUUID": "aaaa0000-0000-0000-0000-000000000000",
            "ZDATECREATED": 0.0,
            "ZFILENAME": "p.heic",
            "description": "2Q",
        }]
        _print_photos(photos)
        out = capsys.readouterr().out
        assert '"2Q"' not in out


# ─── PhotosDB queries ────────────────────────────────────────────────────────


class TestPhotosDBDateRange:
    def test_returns_matching_photos(self, photos_db):
        start = datetime(2025, 6, 14, 0, 0, 0, tzinfo=_HKT)
        end = datetime(2025, 6, 16, 0, 0, 0, tzinfo=_HKT)
        results = photos_db.query_date_range(start, end)
        uuids = {r["ZUUID"] for r in results}
        assert "abcdef01-2222-3333-4444-555566667777" in uuids
        assert "bcdef012-3333-4444-5555-666677778888" in uuids
        assert "cdef0123-4444-5555-6666-777788889999" not in uuids

    def test_excludes_trashed(self, photos_db):
        start = datetime(2025, 6, 14, 0, 0, 0, tzinfo=_HKT)
        end = datetime(2025, 6, 16, 0, 0, 0, tzinfo=_HKT)
        results = photos_db.query_date_range(start, end)
        uuids = {r["ZUUID"] for r in results}
        assert "dead0000-0000-0000-0000-000000000000" not in uuids

    def test_excludes_hidden(self, photos_db):
        start = datetime(2025, 6, 14, 0, 0, 0, tzinfo=_HKT)
        end = datetime(2025, 6, 16, 0, 0, 0, tzinfo=_HKT)
        results = photos_db.query_date_range(start, end)
        uuids = {r["ZUUID"] for r in results}
        assert "beef0000-0000-0000-0000-000000000000" not in uuids

    def test_empty_range(self, photos_db):
        start = datetime(2020, 1, 1, 0, 0, 0, tzinfo=_HKT)
        end = datetime(2020, 1, 2, 0, 0, 0, tzinfo=_HKT)
        results = photos_db.query_date_range(start, end)
        assert results == []

    def test_ordered_desc(self, photos_db):
        start = datetime(2025, 6, 1, 0, 0, 0, tzinfo=_HKT)
        end = datetime(2025, 6, 30, 0, 0, 0, tzinfo=_HKT)
        results = photos_db.query_date_range(start, end)
        dates = [r["ZDATECREATED"] for r in results]
        assert dates == sorted(dates, reverse=True)


class TestPhotosDBRecent:
    def test_returns_recent_within_days(self, photos_db, monkeypatch):
        fake_now = datetime(2025, 6, 15, 23, 59, 0, tzinfo=_HKT)
        # _NS['datetime'] is already the datetime class (script imports it from datetime module)
        # Create subclass that overrides now
        class MockDateTime(_NS['datetime']):
            @classmethod
            def now(cls, tz=None):
                return fake_now
        # Copy over other class attributes to preserve behavior
        for attr in dir(_NS['datetime']):
            if not attr.startswith('_') and attr not in ('now', '__dict__'):
                setattr(MockDateTime, attr, getattr(_NS['datetime'], attr))
        monkeypatch.setitem(_NS, 'datetime', MockDateTime)
        results = photos_db.query_recent(days=7, limit=10)
        uuids = {r["ZUUID"] for r in results}
        assert "abcdef01-2222-3333-4444-555566667777" in uuids
        assert "bcdef012-3333-4444-5555-666677778888" in uuids
        assert "cdef0123-4444-5555-6666-777788889999" not in uuids

    def test_respects_limit(self, photos_db, monkeypatch):
        fake_now = datetime(2025, 6, 15, 23, 59, 0, tzinfo=_HKT)
        # _NS['datetime'] is already the datetime class (script imports it from datetime module)
        # Create subclass that overrides now
        class MockDateTime(_NS['datetime']):
            @classmethod
            def now(cls, tz=None):
                return fake_now
        # Copy over other class attributes to preserve behavior
        for attr in dir(_NS['datetime']):
            if not attr.startswith('_') and attr not in ('now', '__dict__'):
                setattr(MockDateTime, attr, getattr(_NS['datetime'], attr))
        monkeypatch.setitem(_NS, 'datetime', MockDateTime)
        results = photos_db.query_recent(days=30, limit=1)
        assert len(results) <= 1


class TestPhotosDBSearch:
    def test_search_by_description(self, photos_db):
        results = photos_db.search("Golden hour")
        assert len(results) == 1
        assert results[0]["ZUUID"] == "abcdef01-2222-3333-4444-555566667777"

    def test_search_by_title(self, photos_db):
        results = photos_db.search("Morning Coffee")
        assert len(results) == 1
        assert results[0]["ZUUID"] == "bcdef012-3333-4444-5555-666677778888"

    def test_search_by_person_name(self, photos_db):
        results = photos_db.search("Alice")
        assert len(results) >= 1
        uuids = {r["ZUUID"] for r in results}
        assert "abcdef01-2222-3333-4444-555566667777" in uuids

    def test_search_case_insensitive(self, photos_db):
        results = photos_db.search("golden hour")
        assert len(results) == 1

    def test_search_no_match(self, photos_db):
        results = photos_db.search("xyzzy_nonexistent")
        assert results == []

    def test_search_respects_limit(self, photos_db):
        results = photos_db.search("photo", limit=1)
        assert len(results) <= 1


class TestPhotosDBResolveUUID:
    def test_full_uuid_returns_self(self, photos_db):
        full = "abcdef01-2222-3333-4444-555566667777"
        assert photos_db.resolve_uuid(full) == full

    def test_short_prefix_resolves(self, photos_db):
        result = photos_db.resolve_uuid("abcdef01")
        assert result == "abcdef01-2222-3333-4444-555566667777"

    def test_no_match_returns_none(self, photos_db):
        assert photos_db.resolve_uuid("zzzzzzzz") is None


class TestPhotosDBGetByUUID:
    def test_existing_uuid(self, photos_db):
        result = photos_db.get_by_uuid("abcdef01-2222-3333-4444-555566667777")
        assert result is not None
        assert result["ZUUID"] == "abcdef01-2222-3333-4444-555566667777"
        assert result["ZORIGINALFILENAME"] == "IMG_5001.heic"

    def test_nonexistent_uuid(self, photos_db):
        assert photos_db.get_by_uuid("00000000-0000-0000-0000-000000000000") is None


class TestPhotosDBClose:
    def test_close_idempotent(self, photos_db):
        photos_db.close()
        photos_db.close()


# ─── File-resolution helpers ─────────────────────────────────────────────────


class TestFindOriginal:
    def test_existing_file(self, tmp_path, monkeypatch):
        originals = tmp_path / "originals"
        (originals / "A").mkdir(parents=True)
        (originals / "A" / "photo.heic").write_bytes(b"\x00")
        monkeypatch.setitem(_NS, "ORIGINALS_DIR", originals)

        result = _find_original("uuid", "A", "photo.heic")
        assert result == originals / "A" / "photo.heic"

    def test_missing_file(self, tmp_path, monkeypatch):
        originals = tmp_path / "originals"
        originals.mkdir()
        monkeypatch.setitem(_NS, "ORIGINALS_DIR", originals)

        result = _find_original("uuid", "Z", "nonexistent.heic")
        assert result is None


class TestFindDerivative:
    def test_2048_derivative(self, tmp_path, monkeypatch):
        derivs = tmp_path / "derivatives"
        uuid = "a" * 36
        (derivs / uuid[0]).mkdir(parents=True)
        dpath = derivs / uuid[0] / f"{uuid}_1_102_o.jpeg"
        dpath.write_bytes(b"\x00")
        monkeypatch.setitem(_NS, "DERIVATIVES_DIR", derivs)

        result = _find_derivative(uuid)
        assert result == dpath

    def test_1024_fallback(self, tmp_path, monkeypatch):
        derivs = tmp_path / "derivatives"
        uuid = "b" * 36
        (derivs / uuid[0]).mkdir(parents=True)
        dpath = derivs / uuid[0] / f"{uuid}_1_105_c.jpeg"
        dpath.write_bytes(b"\x00")
        monkeypatch.setitem(_NS, "DERIVATIVES_DIR", derivs)

        result = _find_derivative(uuid)
        assert result == dpath

    def test_prefers_2048_over_1024(self, tmp_path, monkeypatch):
        derivs = tmp_path / "derivatives"
        uuid = "c" * 36
        (derivs / uuid[0]).mkdir(parents=True)
        p102 = derivs / uuid[0] / f"{uuid}_1_102_o.jpeg"
        p105 = derivs / uuid[0] / f"{uuid}_1_105_c.jpeg"
        p102.write_bytes(b"\x00")
        p105.write_bytes(b"\x00")
        monkeypatch.setitem(_NS, "DERIVATIVES_DIR", derivs)

        result = _find_derivative(uuid)
        assert result == p102

    def test_no_derivative(self, tmp_path, monkeypatch):
        derivs = tmp_path / "derivatives"
        derivs.mkdir()
        monkeypatch.setitem(_NS, "DERIVATIVES_DIR", derivs)

        result = _find_derivative("d" * 36)
        assert result is None


# ─── export_photos ────────────────────────────────────────────────────────────


class TestExportPhotos:
    def _make_db(self, tmp_path, monkeypatch) -> _PhotosDB:
        db_file = tmp_path / "Photos.sqlite"
        _seed_db(db_file, [_SAMPLE_ROWS[1]])  # JPEG photo
        monkeypatch.setitem(_NS, "DB_PATH", db_file)
        return _PhotosDB()

    def test_export_jpeg_original(self, tmp_path, monkeypatch):
        db = self._make_db(tmp_path, monkeypatch)
        export_dir = tmp_path / "export"
        monkeypatch.setitem(_NS, "EXPORT_DIR", export_dir)
        # Create the original file on disk
        originals = tmp_path / "originals"
        (originals / "B").mkdir(parents=True)
        (originals / "B" / "bcdef012_1.jpeg").write_bytes(b"\xff\xd8\xff\xe0fake")
        monkeypatch.setitem(_NS, "ORIGINALS_DIR", originals)

        _export_photos(db, ["bcdef012-3333-4444-5555-666677778888"])
        out_files = list(export_dir.glob("*.jpeg"))
        assert len(out_files) == 1
        assert out_files[0].name == "IMG_5000.jpeg"
        db.close()

    def test_export_unknown_uuid_prints_warning(self, tmp_path, monkeypatch, capsys):
        db = self._make_db(tmp_path, monkeypatch)
        export_dir = tmp_path / "export"
        monkeypatch.setitem(_NS, "EXPORT_DIR", export_dir)

        _export_photos(db, ["00000000"])
        out = capsys.readouterr().out
        assert "No match" in out or "not found" in out
        db.close()

    def test_creates_export_dir(self, tmp_path, monkeypatch):
        db = self._make_db(tmp_path, monkeypatch)
        export_dir = tmp_path / "new_export"
        monkeypatch.setitem(_NS, "EXPORT_DIR", export_dir)
        _export_photos(db, ["00000000"])
        assert export_dir.exists()
        db.close()


# ─── main() CLI ───────────────────────────────────────────────────────────────


class TestMainCLI:
    def _make_db(self, tmp_path, monkeypatch) -> Path:
        db_file = tmp_path / "Photos.sqlite"
        _seed_db(db_file, _SAMPLE_ROWS)
        monkeypatch.setitem(_NS, "DB_PATH", db_file)
        return db_file

    def test_no_args_shows_docstring(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "Quick photo access" in out

    def test_unknown_command(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "explode"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "Unknown command: explode" in out

    def test_date_command(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "date", "2025-06-15"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "abcdef01" in out

    def test_date_command_no_arg(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "date"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_range_command(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "range", "2025-06-13", "2025-06-15"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "abcdef01" in out
        assert "bcdef012" in out

    def test_range_command_no_args(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "range"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_search_command(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "search", "Beach"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "abcdef01" in out

    def test_search_command_no_keyword(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "search"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_export_command_no_uuids(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["photos.py", "export"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_today_command(self, tmp_path, monkeypatch, capsys):
        self._make_db(tmp_path, monkeypatch)
        fake_now = datetime(2025, 6, 15, 14, 0, 0, tzinfo=_HKT)
        # _NS['datetime'] is already the datetime class (script imports it from datetime module)
        # Create subclass that overrides now
        class MockDateTime(_NS['datetime']):
            @classmethod
            def now(cls, tz=None):
                return fake_now
        # Copy over other class attributes to preserve behavior
        for attr in dir(_NS['datetime']):
            if not attr.startswith('_') and attr not in ('now', '__dict__'):
                setattr(MockDateTime, attr, getattr(_NS['datetime'], attr))
        monkeypatch.setitem(_NS, 'datetime', MockDateTime)
        monkeypatch.setattr(sys, "argv", ["photos.py", "today"])
        _NS["main"]()
        out = capsys.readouterr().out
        assert "abcdef01" in out
