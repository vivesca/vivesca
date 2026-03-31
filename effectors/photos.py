#!/usr/bin/env python3
"""
Quick photo access for Claude Code sessions.

Usage:
    photos.py today                   # Today's photos
    photos.py recent [N]              # Last N photos (default 10, from last 7 days)
    photos.py date YYYY-MM-DD        # Photos from specific date
    photos.py range FROM TO           # Date range
    photos.py export UUID [UUID...]   # Export to ~/tmp/photos/ as JPEG
    photos.py search KEYWORD          # Search by keyword (descriptions, titles, people)

All queries print: uuid (first 8), timestamp, filename, labels.
Export converts HEIC to JPEG for Claude Code's Read tool.

Zero external dependencies — queries Photos.sqlite directly.
"""
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Core Data epoch: 2001-01-01T00:00:00Z
_CD_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
_CD_OFFSET = _CD_EPOCH.timestamp()  # seconds from unix epoch to Core Data epoch

PHOTOS_LIB = Path.home() / "Pictures" / "Photos Library.photoslibrary"
DB_PATH = PHOTOS_LIB / "database" / "Photos.sqlite"
ORIGINALS_DIR = PHOTOS_LIB / "originals"
DERIVATIVES_DIR = PHOTOS_LIB / "resources" / "derivatives"
EXPORT_DIR = Path.home() / "tmp" / "photos"

# HKT = UTC+8
_HKT = timezone(timedelta(hours=8))


def _cd_timestamp(dt: datetime) -> float:
    """Convert a datetime to Core Data timestamp (seconds since 2001-01-01 UTC)."""
    return dt.timestamp() - _CD_OFFSET


def _cd_to_datetime(cd_ts: float) -> datetime:
    """Convert Core Data timestamp to HKT datetime."""
    return datetime.fromtimestamp(cd_ts + _CD_OFFSET, tz=_HKT)


class PhotosDB:
    """Thin read-only wrapper around Photos.sqlite."""

    def __init__(self) -> None:
        if not DB_PATH.exists():
            print(f"Error: Photos database not found at {DB_PATH}", file=sys.stderr)
            sys.exit(1)
        uri = f"file:{DB_PATH}?mode=ro"
        self.conn = sqlite3.connect(uri, uri=True)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def _base_query(self) -> str:
        """Base SELECT + JOINs for photo queries."""
        return """
            SELECT
                a.ZUUID,
                a.ZDATECREATED,
                a.ZDIRECTORY,
                a.ZFILENAME,
                a.ZUNIFORMTYPEIDENTIFIER AS uti,
                a.ZWIDTH,
                a.ZHEIGHT,
                aa.ZORIGINALFILENAME,
                aa.ZTITLE,
                d.ZLONGDESCRIPTION AS description,
                (SELECT GROUP_CONCAT(p.ZDISPLAYNAME, ', ')
                 FROM ZDETECTEDFACE df
                 JOIN ZPERSON p ON p.Z_PK = df.ZPERSONFORFACE
                 WHERE df.ZASSETFORFACE = a.Z_PK
                   AND p.ZDISPLAYNAME IS NOT NULL
                   AND p.ZDISPLAYNAME != ''
                ) AS people,
                (SELECT ir.ZLOCALAVAILABILITY
                 FROM ZINTERNALRESOURCE ir
                 WHERE ir.ZASSET = a.Z_PK AND ir.ZRESOURCETYPE = 0 AND ir.ZDATASTORESUBTYPE = 1
                 LIMIT 1
                ) AS local_avail
            FROM ZASSET a
            LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.ZASSET = a.Z_PK
            LEFT JOIN ZASSETDESCRIPTION d ON d.Z_PK = aa.ZASSETDESCRIPTION
        """

    def _base_where(self) -> str:
        """Standard filters: not trashed, not hidden, photos only."""
        return "WHERE a.ZTRASHEDSTATE = 0 AND a.ZHIDDEN = 0 AND a.ZKIND = 0"

    def query_date_range(self, start: datetime, end: datetime) -> list[dict]:
        """Query photos within a date range (inclusive start, exclusive end)."""
        cd_start = _cd_timestamp(start)
        cd_end = _cd_timestamp(end)
        sql = f"""
            {self._base_query()}
            {self._base_where()}
              AND a.ZDATECREATED >= ? AND a.ZDATECREATED < ?
            ORDER BY a.ZDATECREATED DESC
        """
        rows = self.conn.execute(sql, (cd_start, cd_end)).fetchall()
        return [dict(r) for r in rows]

    def query_recent(self, days: int = 7, limit: int = 10) -> list[dict]:
        """Query most recent N photos from the last `days` days."""
        now = datetime.now(tz=_HKT)
        start = now - timedelta(days=days)
        cd_start = _cd_timestamp(start)
        sql = f"""
            {self._base_query()}
            {self._base_where()}
              AND a.ZDATECREATED >= ?
            ORDER BY a.ZDATECREATED DESC
            LIMIT ?
        """
        rows = self.conn.execute(sql, (cd_start, limit)).fetchall()
        return [dict(r) for r in rows]

    def search(self, keyword: str, limit: int = 20) -> list[dict]:
        """Search photos by description, title, original filename, or person name."""
        pattern = f"%{keyword}%"
        sql = f"""
            {self._base_query()}
            {self._base_where()}
              AND (
                d.ZLONGDESCRIPTION LIKE ? COLLATE NOCASE
                OR aa.ZTITLE LIKE ? COLLATE NOCASE
                OR aa.ZORIGINALFILENAME LIKE ? COLLATE NOCASE
                OR EXISTS (
                    SELECT 1
                    FROM ZDETECTEDFACE df2
                    JOIN ZPERSON p2 ON p2.Z_PK = df2.ZPERSONFORFACE
                    WHERE df2.ZASSETFORFACE = a.Z_PK
                      AND (p2.ZDISPLAYNAME LIKE ? COLLATE NOCASE
                       OR p2.ZFULLNAME LIKE ? COLLATE NOCASE)
                )
              )
            ORDER BY a.ZDATECREATED DESC
            LIMIT ?
        """
        rows = self.conn.execute(sql, (pattern, pattern, pattern, pattern, pattern, limit)).fetchall()
        return [dict(r) for r in rows]

    def resolve_uuid(self, prefix: str) -> str | None:
        """Resolve a short UUID prefix to a full UUID."""
        if len(prefix) >= 36:
            return prefix
        sql = """
            SELECT ZUUID FROM ZASSET
            WHERE ZUUID LIKE ? AND ZTRASHEDSTATE = 0
            LIMIT 1
        """
        row = self.conn.execute(sql, (f"{prefix}%",)).fetchone()
        return row["ZUUID"] if row else None

    def get_by_uuid(self, uuid: str) -> dict | None:
        """Get a single photo by full UUID."""
        sql = f"""
            {self._base_query()}
            WHERE a.ZUUID = ?
        """
        row = self.conn.execute(sql, (uuid,)).fetchone()
        return dict(row) if row else None


def print_photos(photos: list[dict]) -> None:
    """Print photo listing in standard format."""
    print(f"Found {len(photos)} items\n")
    for p in photos:
        uuid = (p.get("ZUUID") or "?")[:8]
        cd_ts = p.get("ZDATECREATED")
        if cd_ts is not None:
            dt = _cd_to_datetime(cd_ts)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date_str = "?"
        fname = p.get("ZORIGINALFILENAME") or p.get("ZFILENAME") or "?"
        desc = p.get("description") or ""
        people = p.get("people") or ""
        title = p.get("ZTITLE") or ""

        # Build label string from available metadata
        labels = []
        if people:
            labels.extend(people.split(", "))
        if title:
            labels.append(title)
        label_str = ", ".join(labels) if labels else "(no labels)"

        desc_str = f'  "{desc}"' if desc and desc != "2Q" else ""

        # Local availability indicator
        avail = p.get("local_avail")
        avail_str = "" if avail == 1 else "  [iCloud]" if avail is not None else ""

        print(f"  {uuid}  {date_str}  {fname}  [{label_str}]{desc_str}{avail_str}")


def _find_original(uuid: str, directory: str, filename: str) -> Path | None:
    """Find the original file for a photo."""
    path = ORIGINALS_DIR / directory / filename
    if path.exists():
        return path
    return None


def _find_derivative(uuid: str) -> Path | None:
    """Find a derivative JPEG for a photo (2048px preferred, 1024px fallback)."""
    prefix = uuid[0]
    deriv_dir = DERIVATIVES_DIR / prefix

    # Preferred: 2048px derivative
    path_102 = deriv_dir / f"{uuid}_1_102_o.jpeg"
    if path_102.exists():
        return path_102

    # Fallback: 1024px derivative
    path_105 = deriv_dir / f"{uuid}_1_105_c.jpeg"
    if path_105.exists():
        return path_105

    return None


def export_photos(db: PhotosDB, uuids: list[str]) -> None:
    """Export photos to ~/tmp/photos/ as JPEG."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    for raw_uuid in uuids:
        full_uuid = db.resolve_uuid(raw_uuid)
        if not full_uuid:
            print(f"  [!] No match for UUID prefix: {raw_uuid}")
            continue

        photo = db.get_by_uuid(full_uuid)
        if not photo:
            print(f"  [!] Photo not found: {full_uuid}")
            continue

        orig_fname = photo.get("ZORIGINALFILENAME") or photo.get("ZFILENAME") or full_uuid
        # Output filename: original name stem + .jpeg
        out_stem = Path(orig_fname).stem
        out_path = EXPORT_DIR / f"{out_stem}.jpeg"

        directory = photo.get("ZDIRECTORY") or full_uuid[0]
        filename = photo.get("ZFILENAME") or f"{full_uuid}.heic"
        uti = photo.get("uti") or ""

        # Tier 1: Original HEIC -> sips conversion
        original = _find_original(full_uuid, directory, filename)
        if original and "heic" in uti.lower():
            result = subprocess.run(
                ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92",
                 str(original), "--out", str(out_path)],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                size_kb = out_path.stat().st_size / 1024
                print(f"  {out_stem}.jpeg  ({size_kb:.0f}KB)  [converted from HEIC]")
                continue
            else:
                print(f"  [!] sips failed for {orig_fname}: {result.stderr.strip()}", file=sys.stderr)
                # Fall through to derivative

        # Tier 2: Original JPEG -> copy
        if original and "jpeg" in uti.lower():
            shutil.copy2(original, out_path)
            size_kb = out_path.stat().st_size / 1024
            print(f"  {out_stem}.jpeg  ({size_kb:.0f}KB)  [copied original]")
            continue

        # Tier 3: Derivative exists -> copy with note
        derivative = _find_derivative(full_uuid)
        if derivative:
            shutil.copy2(derivative, out_path)
            size_kb = out_path.stat().st_size / 1024
            suffix = derivative.name.split("_")[-1]  # e.g. "102_o.jpeg" or "105_c.jpeg"
            print(f"  {out_stem}.jpeg  ({size_kb:.0f}KB)  [derivative, reduced resolution]")
            continue

        # Nothing available locally
        print(f"  [!] {orig_fname}: not available locally (iCloud only?)")

    print(f"\nExported to {EXPORT_DIR}/")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1]
    db = PhotosDB()

    try:
        if cmd == "today":
            now = datetime.now(tz=_HKT)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            photos = db.query_date_range(start, end)
            print_photos(photos)

        elif cmd == "recent":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            photos = db.query_recent(days=7, limit=n)
            print_photos(photos)

        elif cmd == "date":
            if len(sys.argv) < 3:
                print("Usage: photos.py date YYYY-MM-DD")
                return
            date_str = sys.argv[2]
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=_HKT)
            start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            photos = db.query_date_range(start, end)
            print_photos(photos)

        elif cmd == "range":
            if len(sys.argv) < 4:
                print("Usage: photos.py range FROM TO")
                return
            start = datetime.strptime(sys.argv[2], "%Y-%m-%d").replace(tzinfo=_HKT)
            end = datetime.strptime(sys.argv[3], "%Y-%m-%d").replace(tzinfo=_HKT)
            end = end.replace(hour=23, minute=59, second=59)
            photos = db.query_date_range(start, end)
            print_photos(photos)

        elif cmd == "export":
            if len(sys.argv) < 3:
                print("Usage: photos.py export UUID [UUID...]")
                return
            print(f"Exporting to {EXPORT_DIR}/\n")
            export_photos(db, sys.argv[2:])

        elif cmd == "search":
            if len(sys.argv) < 3:
                print("Usage: photos.py search KEYWORD")
                return
            keyword = " ".join(sys.argv[2:])
            photos = db.search(keyword)
            print_photos(photos)

        else:
            print(f"Unknown command: {cmd}")
            print(__doc__)

    finally:
        db.close()


if __name__ == "__main__":
    main()
