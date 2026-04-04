"""Tests for effectors/photos.py — CLI subprocess tests + exec-based unit tests."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "photos.py"


# ── Helpers ───────────────────────────────────────────────────────────


def run(*args: str) -> subprocess.CompletedProcess[str]:
    """Run photos.py with given args, capture output."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


def _load_ns() -> dict:
    """Exec photos.py into a namespace for unit-testing pure functions."""
    ns: dict = {"__name__": "photos_test", "__file__": str(SCRIPT)}
    exec(SCRIPT.read_text(), ns)
    return ns


def _make_db(tmp_path: Path) -> Path:
    """Create a minimal Photos.sqlite with test data and return its path.

    Creates ``tmp_path/database/Photos.sqlite`` to match the real layout.
    """
    db_dir = tmp_path / "database"
    db_dir.mkdir()
    db_path = db_dir / "Photos.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE ZASSET (
            Z_PK INTEGER PRIMARY KEY, ZUUID TEXT, ZDATECREATED REAL,
            ZDIRECTORY TEXT, ZFILENAME TEXT, ZUNIFORMTYPEIDENTIFIER TEXT,
            ZWIDTH INTEGER, ZHEIGHT INTEGER,
            ZTRASHEDSTATE INTEGER DEFAULT 0, ZHIDDEN INTEGER DEFAULT 0,
            ZKIND INTEGER DEFAULT 0
        );
        CREATE TABLE ZADDITIONALASSETATTRIBUTES (
            Z_PK INTEGER PRIMARY KEY, ZASSET INTEGER,
            ZORIGINALFILENAME TEXT, ZTITLE TEXT, ZASSETDESCRIPTION INTEGER
        );
        CREATE TABLE ZASSETDESCRIPTION (
            Z_PK INTEGER PRIMARY KEY, ZLONGDESCRIPTION TEXT
        );
        CREATE TABLE ZDETECTEDFACE (
            Z_PK INTEGER PRIMARY KEY, ZASSETFORFACE INTEGER,
            ZPERSONFORFACE INTEGER
        );
        CREATE TABLE ZPERSON (
            Z_PK INTEGER PRIMARY KEY, ZDISPLAYNAME TEXT, ZFULLNAME TEXT
        );
        CREATE TABLE ZINTERNALRESOURCE (
            Z_PK INTEGER PRIMARY KEY, ZASSET INTEGER,
            ZRESOURCETYPE INTEGER, ZDATASTORESUBTYPE INTEGER,
            ZLOCALAVAILABILITY INTEGER
        );
        """
    )
    # Insert test data.
    # Use the module's own converter to get the right CD timestamp.
    _ns0 = _load_ns()
    _HKT = timezone(timedelta(hours=8))
    _cd_timestamp = _ns0["_cd_timestamp"]
    cd_ts = _cd_timestamp(datetime(2025, 6, 15, 12, 0, 0, tzinfo=_HKT))
    cd_ts2 = _cd_timestamp(datetime(2025, 6, 16, 12, 0, 0, tzinfo=_HKT))

    # Photo 1: normal, local
    conn.execute(
        "INSERT INTO ZASSET (Z_PK,ZUUID,ZDATECREATED,ZDIRECTORY,ZFILENAME,"
        "ZUNIFORMTYPEIDENTIFIER,ZWIDTH,ZHEIGHT,ZTRASHEDSTATE,ZHIDDEN,ZKIND) "
        "VALUES (1,'aaa11111-bb22-cc33-dd44-ee5566778899',?,"
        "'0/A','IMG_0001.heic','public.heif',4032,3024,0,0,0)",
        (cd_ts,),
    )
    # Photo 2: next day, trashed -> should be filtered
    conn.execute(
        "INSERT INTO ZASSET (Z_PK,ZUUID,ZDATECREATED,ZDIRECTORY,ZFILENAME,"
        "ZUNIFORMTYPEIDENTIFIER,ZWIDTH,ZHEIGHT,ZTRASHEDSTATE,ZHIDDEN,ZKIND) "
        "VALUES (2,'bbb22222-cc33-dd44-ee55-ff6677889900',?,"
        "'0/B','IMG_0002.jpeg','public.jpeg',1920,1080,1,0,0)",
        (cd_ts2,),
    )
    # Photo 3: hidden -> should be filtered
    conn.execute(
        "INSERT INTO ZASSET (Z_PK,ZUUID,ZDATECREATED,ZDIRECTORY,ZFILENAME,"
        "ZUNIFORMTYPEIDENTIFIER,ZWIDTH,ZHEIGHT,ZTRASHEDSTATE,ZHIDDEN,ZKIND) "
        "VALUES (3,'ccc33333-dd44-ee55-ff66-007788990011',?,"
        "'0/C','IMG_0003.heic','public.heif',4032,3024,0,1,0)",
        (cd_ts,),
    )
    # Photo 4: ZKIND=1 (video) -> filtered
    conn.execute(
        "INSERT INTO ZASSET (Z_PK,ZUUID,ZDATECREATED,ZDIRECTORY,ZFILENAME,"
        "ZUNIFORMTYPEIDENTIFIER,ZWIDTH,ZHEIGHT,ZTRASHEDSTATE,ZHIDDEN,ZKIND) "
        "VALUES (4,'ddd44444-ee55-ff66-0077-118899001122',?,"
        "'0/D','MOV_0001.mov','com.apple.quicktime-movie',1920,1080,0,0,1)",
        (cd_ts,),
    )

    # Additional attributes for photo 1
    conn.execute(
        "INSERT INTO ZADDITIONALASSETATTRIBUTES "
        "(Z_PK,ZASSET,ZORIGINALFILENAME,ZTITLE,ZASSETDESCRIPTION) "
        "VALUES (1,1,'IMG_0001.heic','Sunset',1)"
    )
    conn.execute(
        "INSERT INTO ZASSETDESCRIPTION (Z_PK,ZLONGDESCRIPTION) VALUES (1,'A beautiful sunset')"
    )

    # Person + face for photo 1
    conn.execute(
        "INSERT INTO ZPERSON (Z_PK,ZDISPLAYNAME,ZFULLNAME) VALUES (1,'Alice','Alice Smith')"
    )
    conn.execute("INSERT INTO ZDETECTEDFACE (Z_PK,ZASSETFORFACE,ZPERSONFORFACE) VALUES (1,1,1)")

    # Internal resource (local availability) for photo 1
    conn.execute(
        "INSERT INTO ZINTERNALRESOURCE "
        "(Z_PK,ZASSET,ZRESOURCETYPE,ZDATASTORESUBTYPE,ZLOCALAVAILABILITY) "
        "VALUES (1,1,0,1,1)"
    )

    conn.commit()
    conn.close()
    return db_path


def _load_ns_with_db(tmp_path: Path) -> dict:
    """Load photos.py namespace with DB_PATH patched to temp DB."""
    db_path = _make_db(tmp_path)
    ns = _load_ns()
    # Patch constants so PhotosDB finds our test database and dirs stay in tmp
    ns["DB_PATH"] = db_path
    ns["PHOTOS_LIB"] = tmp_path
    ns["ORIGINALS_DIR"] = tmp_path / "originals"
    ns["DERIVATIVES_DIR"] = tmp_path / "resources" / "derivatives"
    return ns


# ── CLI tests (subprocess) ───────────────────────────────────────────


class TestCLIHelp:
    def test_no_args_prints_usage(self):
        r = run()
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_dash_h(self):
        r = run("-h")
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_double_dash_help(self):
        r = run("--help")
        assert r.returncode == 0
        assert "Usage:" in r.stdout


class TestCLIUnknownCommand:
    def test_unknown_cmd_shows_error(self):
        r = run("foobar")
        assert r.returncode == 0
        assert "Unknown command: foobar" in r.stdout

    def test_unknown_cmd_shows_usage(self):
        r = run("xyz")
        assert "Usage:" in r.stdout


class TestCLIMissingDB:
    """Valid commands attempt DB open, which fails without a Photos Library."""

    def test_today_no_db(self):
        r = run("today")
        assert r.returncode == 1
        assert "Error:" in r.stderr

    def test_recent_no_db(self):
        r = run("recent")
        assert r.returncode == 1

    def test_date_no_db(self):
        r = run("date", "2025-01-01")
        assert r.returncode == 1

    def test_range_no_db(self):
        r = run("range", "2025-01-01", "2025-01-02")
        assert r.returncode == 1

    def test_search_no_db(self):
        r = run("search", "cat")
        assert r.returncode == 1


# ── Pure-function unit tests (exec) ──────────────────────────────────


class TestTimestampConversion:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.ns = _load_ns()

    def test_cd_epoch_is_zero(self):
        epoch = datetime(2001, 1, 1, tzinfo=UTC)
        assert self.ns["_cd_timestamp"](epoch) == 0.0

    def test_cd_roundtrip(self):
        _HKT = timezone(timedelta(hours=8))
        dt = datetime(2025, 6, 15, 14, 30, 0, tzinfo=_HKT)
        cd_ts = self.ns["_cd_timestamp"](dt)
        dt_back = self.ns["_cd_to_datetime"](cd_ts)
        assert dt_back == dt

    def test_positive_after_epoch(self):
        dt = datetime(2025, 1, 1, tzinfo=UTC)
        assert self.ns["_cd_timestamp"](dt) > 0

    def test_to_datetime_tz_is_hkt(self):
        result = self.ns["_cd_to_datetime"](0.0)
        _HKT = timezone(timedelta(hours=8))
        assert result.tzinfo == _HKT

    def test_offset_approx_978307200(self):
        assert abs(self.ns["_CD_OFFSET"] - 978307200.0) < 1.0


class TestPrintPhotos:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.ns = _load_ns()
        self.print_photos = self.ns["print_photos"]

    def test_empty_list(self, capsys):
        self.print_photos([])
        out = capsys.readouterr().out
        assert "Found 0 items" in out

    def test_single_photo_uuid_truncated(self, capsys):
        uuid = "abcdef01" + "23456789" * 3 + "ab"
        self.print_photos([{"ZUUID": uuid, "ZDATECREATED": 0.0}])
        out = capsys.readouterr().out
        assert "Found 1 items" in out
        assert "abcdef01" in out
        # Should NOT contain the full UUID
        assert uuid[8:] not in out

    def test_no_timestamp_shows_question_mark(self, capsys):
        self.print_photos([{"ZUUID": "12345678abcd", "ZDATECREATED": None}])
        out = capsys.readouterr().out
        assert "  ?  " in out

    def test_people_in_labels(self, capsys):
        self.print_photos(
            [
                {
                    "ZUUID": "aaaabbbb",
                    "ZDATECREATED": 100000.0,
                    "people": "Alice, Bob",
                    "ZTITLE": "Beach",
                }
            ]
        )
        out = capsys.readouterr().out
        assert "Alice" in out
        assert "Bob" in out
        assert "Beach" in out

    def test_no_labels_placeholder(self, capsys):
        self.print_photos([{"ZUUID": "cccddddd", "ZDATECREATED": 50000.0}])
        out = capsys.readouterr().out
        assert "(no labels)" in out

    def test_icloud_indicator(self, capsys):
        """local_avail != 1 should show [iCloud]."""
        self.print_photos([{"ZUUID": "eeeeffff", "ZDATECREATED": 0.0, "local_avail": 0}])
        out = capsys.readouterr().out
        assert "[iCloud]" in out

    def test_description_shown(self, capsys):
        self.print_photos(
            [{"ZUUID": "gggghhhh", "ZDATECREATED": 0.0, "description": "A nice photo"}]
        )
        out = capsys.readouterr().out
        assert "A nice photo" in out

    def test_description_2Q_suppressed(self, capsys):
        """Description exactly '2Q' should not be shown."""
        self.print_photos([{"ZUUID": "iiiijjjj", "ZDATECREATED": 0.0, "description": "2Q"}])
        out = capsys.readouterr().out
        assert "2Q" not in out


class TestConstants:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.ns = _load_ns()

    def test_export_dir_under_home(self):
        assert self.ns["EXPORT_DIR"].is_relative_to(Path.home())

    def test_db_path_name(self):
        assert self.ns["DB_PATH"].name == "Photos.sqlite"

    def test_originals_dir_name(self):
        assert self.ns["ORIGINALS_DIR"].name == "originals"


# ── PhotosDB unit tests with in-memory test database ─────────────────


class TestPhotosDB:
    """Test PhotosDB queries against a minimal test database."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.ns = _load_ns_with_db(tmp_path)
        self.db = self.ns["PhotosDB"]()

    def teardown_method(self):
        if hasattr(self, "db"):
            self.db.close()

    def test_query_date_range_finds_photo(self):
        _HKT = timezone(timedelta(hours=8))
        start = datetime(2025, 6, 15, tzinfo=_HKT)
        end = datetime(2025, 6, 16, tzinfo=_HKT)
        rows = self.db.query_date_range(start, end)
        # Only photo 1 matches (photo 2 is next day, 3 is hidden, 4 is video)
        assert len(rows) == 1
        assert rows[0]["ZUUID"] == "aaa11111-bb22-cc33-dd44-ee5566778899"

    def test_query_date_range_excludes_trashed(self):
        _HKT = timezone(timedelta(hours=8))
        start = datetime(2025, 6, 15, tzinfo=_HKT)
        end = datetime(2025, 6, 17, tzinfo=_HKT)
        rows = self.db.query_date_range(start, end)
        uuids = [r["ZUUID"] for r in rows]
        assert "bbb22222-cc33-dd44-ee55-ff6677889900" not in uuids  # trashed

    def test_query_date_range_excludes_hidden(self):
        _HKT = timezone(timedelta(hours=8))
        start = datetime(2025, 6, 14, tzinfo=_HKT)
        end = datetime(2025, 6, 17, tzinfo=_HKT)
        rows = self.db.query_date_range(start, end)
        uuids = [r["ZUUID"] for r in rows]
        assert "ccc33333-dd44-ee55-ff66-007788990011" not in uuids  # hidden

    def test_query_date_range_excludes_videos(self):
        _HKT = timezone(timedelta(hours=8))
        start = datetime(2025, 6, 14, tzinfo=_HKT)
        end = datetime(2025, 6, 17, tzinfo=_HKT)
        rows = self.db.query_date_range(start, end)
        uuids = [r["ZUUID"] for r in rows]
        assert "ddd44444-ee55-ff66-0077-118899001122" not in uuids  # video

    def test_query_date_range_empty(self):
        _HKT = timezone(timedelta(hours=8))
        start = datetime(1999, 1, 1, tzinfo=_HKT)
        end = datetime(1999, 1, 2, tzinfo=_HKT)
        rows = self.db.query_date_range(start, end)
        assert rows == []

    def test_query_recent(self):
        # Use a very wide day range to catch our test data
        rows = self.db.query_recent(days=365 * 30, limit=10)
        assert len(rows) >= 1
        uuids = [r["ZUUID"] for r in rows]
        assert "aaa11111-bb22-cc33-dd44-ee5566778899" in uuids

    def test_query_recent_respects_limit(self):
        rows = self.db.query_recent(days=365 * 30, limit=0)
        assert len(rows) == 0

    def test_search_by_title(self):
        rows = self.db.search("Sunset")
        assert len(rows) == 1
        assert rows[0]["ZUUID"] == "aaa11111-bb22-cc33-dd44-ee5566778899"

    def test_search_by_description(self):
        rows = self.db.search("beautiful")
        assert len(rows) == 1

    def test_search_by_person(self):
        rows = self.db.search("Alice")
        assert len(rows) == 1

    def test_search_case_insensitive(self):
        rows = self.db.search("sunset")
        assert len(rows) == 1

    def test_search_no_match(self):
        rows = self.db.search("nonexistent_query_xyz")
        assert rows == []

    def test_resolve_uuid_full(self):
        full = "aaa11111-bb22-cc33-dd44-ee5566778899"
        assert self.db.resolve_uuid(full) == full

    def test_resolve_uuid_prefix(self):
        assert self.db.resolve_uuid("aaa11111") == "aaa11111-bb22-cc33-dd44-ee5566778899"

    def test_resolve_uuid_no_match(self):
        assert self.db.resolve_uuid("zzz99999") is None

    def test_get_by_uuid(self):
        full = "aaa11111-bb22-cc33-dd44-ee5566778899"
        row = self.db.get_by_uuid(full)
        assert row is not None
        assert row["ZUUID"] == full
        assert row["ZTITLE"] == "Sunset"

    def test_get_by_uuid_not_found(self):
        assert self.db.get_by_uuid("nonexistent-uuid") is None

    def test_people_joined(self):
        full = "aaa11111-bb22-cc33-dd44-ee5566778899"
        row = self.db.get_by_uuid(full)
        assert row is not None
        assert "Alice" in (row.get("people") or "")

    def test_local_availability(self):
        full = "aaa11111-bb22-cc33-dd44-ee5566778899"
        row = self.db.get_by_uuid(full)
        assert row is not None
        assert row.get("local_avail") == 1


class TestFindOriginal:
    @pytest.fixture(autouse=True)
    def _load(self, tmp_path):
        self.ns = _load_ns()
        # Create fake originals directory
        orig = tmp_path / "originals" / "0/A"
        orig.mkdir(parents=True)
        (orig / "IMG_0001.heic").write_bytes(b"\x00")
        self.ns["ORIGINALS_DIR"] = tmp_path / "originals"

    def test_find_existing(self):
        result = self.ns["_find_original"]("fake-uuid", "0/A", "IMG_0001.heic")
        assert result is not None
        assert result.name == "IMG_0001.heic"

    def test_find_missing(self):
        result = self.ns["_find_original"]("fake-uuid", "0/Z", "missing.heic")
        assert result is None


class TestFindDerivative:
    @pytest.fixture(autouse=True)
    def _load(self, tmp_path):
        self.ns = _load_ns()
        # Create fake derivative directories
        deriv_a = tmp_path / "resources" / "derivatives" / "a"
        deriv_a.mkdir(parents=True)
        uuid = "aaa11111-bb22-cc33-dd44-ee5566778899"
        (deriv_a / f"{uuid}_1_102_o.jpeg").write_bytes(b"\x00")
        self.ns["DERIVATIVES_DIR"] = tmp_path / "resources" / "derivatives"

    def test_find_2048_derivative(self):
        uuid = "aaa11111-bb22-cc33-dd44-ee5566778899"
        result = self.ns["_find_derivative"](uuid)
        assert result is not None
        assert "102_o" in result.name

    def test_fallback_1024_derivative(self, tmp_path):
        # Remove the 2048 version, create 1024 version
        uuid = "aaa11111-bb22-cc33-dd44-ee5566778899"
        deriv_a = tmp_path / "resources" / "derivatives" / "a"
        (deriv_a / f"{uuid}_1_102_o.jpeg").unlink()
        (deriv_a / f"{uuid}_1_105_c.jpeg").write_bytes(b"\x00")
        result = self.ns["_find_derivative"](uuid)
        assert result is not None
        assert "105_c" in result.name

    def test_no_derivative(self):
        result = self.ns["_find_derivative"]("zzzzzzzz-nope")
        assert result is None


class TestExportPhotos:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.ns = _load_ns_with_db(tmp_path)
        self.export_dir = tmp_path / "export"
        self.ns["EXPORT_DIR"] = self.export_dir
        # Create a fake original JPEG file for photo 1
        orig_dir = tmp_path / "originals" / "0" / "A"
        orig_dir.mkdir(parents=True)
        (orig_dir / "IMG_0001.heic").write_bytes(b"\x00" * 100)
        self.ns["ORIGINALS_DIR"] = tmp_path / "originals"
        self.ns["DERIVATIVES_DIR"] = tmp_path / "resources" / "derivatives"

    def test_export_unknown_uuid(self, capsys):
        db = self.ns["PhotosDB"]()
        try:
            self.ns["export_photos"](db, ["zzz99999"])
            out = capsys.readouterr().out
            assert "No match" in out
        finally:
            db.close()

    def test_export_creates_directory(self, capsys):
        assert not self.export_dir.exists()
        db = self.ns["PhotosDB"]()
        try:
            # UUID that exists but no local file (falls through to "not available")
            self.ns["export_photos"](db, ["aaa11111"])
            assert self.export_dir.exists()
        finally:
            db.close()
