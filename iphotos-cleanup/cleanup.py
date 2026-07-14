#!/usr/bin/env python3
"""Find photos imported into macOS Photos by given apps (bundle IDs) and
collect them into an album for manual review and deletion.

Works on a copy of Photos.sqlite — the original library is never touched.
Deletion itself is manual by design: open the album in Photos, ⌘A → ⌘⌫
(AppleScript cannot delete media items, and the manual step gives you
final control; deleted items stay in "Recently Deleted" for 30 days).
"""

import argparse
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

APPLE_EPOCH_OFFSET = 978307200  # seconds between 1970-01-01 and Apple's 2001-01-01 epoch
DEFAULT_LIBRARY = Path.home() / "Pictures" / "Photos Library.photoslibrary"
DEFAULT_ALBUM = "🗑 App photos — на удаление"
BATCH_SIZE = 50  # Photos slows down when adding long media-item lists at once

# argv: album name, then UUIDs. Returns comma-separated UUIDs it could not find.
ADD_TO_ALBUM_SCRIPT = """
on run argv
    set albumName to item 1 of argv
    set uuids to rest of argv
    tell application "Photos"
        if not (exists album albumName) then
            make new album named albumName
        end if
        set theAlbum to album albumName
        set found to {}
        set missing to {}
        repeat with u in uuids
            try
                set end of found to (get media item id ((u as text) & "/L0/001"))
            on error
                set end of missing to (u as text)
            end try
        end repeat
        if (count of found) > 0 then
            add found to theAlbum
        end if
    end tell
    set AppleScript's text item delimiters to ","
    return missing as text
end run
"""


def copy_database(library: Path) -> Path:
    """Copy Photos.sqlite (with its WAL/SHM) to a temp dir and return the copy's path."""
    dbdir = library / "database"
    if not (dbdir / "Photos.sqlite").exists():
        sys.exit(f"База не найдена: {dbdir / 'Photos.sqlite'} (том не смонтирован?)")
    tmp = Path(tempfile.mkdtemp(prefix="iphotos-cleanup-"))
    for name in ("Photos.sqlite", "Photos.sqlite-wal", "Photos.sqlite-shm"):
        src = dbdir / name
        if src.exists():
            shutil.copy2(src, tmp / name)
    return tmp / "Photos.sqlite"


def list_apps(db: Path) -> list[tuple[str, int]]:
    with sqlite3.connect(db) as conn:
        return conn.execute(
            """
            SELECT COALESCE(ZIMPORTEDBYBUNDLEIDENTIFIER, '<нет>') , COUNT(*)
            FROM ZADDITIONALASSETATTRIBUTES
            GROUP BY 1 ORDER BY 2 DESC
            """
        ).fetchall()


def find_photos(db: Path, bundle_ids: list[str]) -> list[dict]:
    placeholders = ",".join("?" * len(bundle_ids))
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            f"""
            SELECT ZS.ZUUID, ZA.ZORIGINALFILENAME,
                   strftime('%Y-%m-%d', ZS.ZDATECREATED + {APPLE_EPOCH_OFFSET}, 'unixepoch'),
                   ZA.ZIMPORTEDBYBUNDLEIDENTIFIER
            FROM ZADDITIONALASSETATTRIBUTES ZA
            JOIN ZASSET ZS ON ZS.Z_PK = ZA.ZASSET
            WHERE ZA.ZIMPORTEDBYBUNDLEIDENTIFIER IN ({placeholders})
              AND ZS.ZTRASHEDSTATE = 0
            ORDER BY ZS.ZDATECREATED
            """,
            bundle_ids,
        ).fetchall()
    return [
        {"uuid": r[0], "filename": r[1], "created": r[2], "bundle_id": r[3]}
        for r in rows
    ]


def print_report(photos: list[dict]) -> None:
    if not photos:
        print("Ничего не найдено.")
        return
    by_bundle = Counter(p["bundle_id"] for p in photos)
    print(f"Найдено {len(photos)} фото (без учёта уже удалённых):")
    for bundle, count in by_bundle.most_common():
        print(f"  {bundle}: {count}")
    print("\nПо месяцам:")
    by_month = Counter(p["created"][:7] for p in photos)
    for month in sorted(by_month):
        print(f"  {month}: {by_month[month]}")


def run_applescript_batch(album: str, uuids: list[str]) -> list[str]:
    """Add a batch of UUIDs to the album; return the UUIDs Photos could not find."""
    result = subprocess.run(
        ["osascript", "-", album, *uuids],
        input=ADD_TO_ALBUM_SCRIPT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(f"osascript завершился с ошибкой:\n{result.stderr.strip()}")
    missing = result.stdout.strip()
    return [u for u in missing.split(",") if u]


def make_album(album: str, photos: list[dict]) -> None:
    uuids = [p["uuid"] for p in photos]

    # Probe with a single UUID first: catches a wrong open library or a bad
    # id format before we churn through the full list.
    print(f"Проба на одном снимке ({uuids[0]})...")
    if run_applescript_batch(album, uuids[:1]):
        sys.exit(
            "Пробный снимок не найден в Photos. Скорее всего, открыта другая "
            "библиотека — проверь, что в Photos открыта та, что передана в --library."
        )
    print("Проба прошла, добавляю остальные...")

    missing: list[str] = []
    rest = uuids[1:]
    for i in range(0, len(rest), BATCH_SIZE):
        batch = rest[i : i + BATCH_SIZE]
        missing += run_applescript_batch(album, batch)
        print(f"  {min(i + BATCH_SIZE, len(rest)) + 1}/{len(uuids)}")

    added = len(uuids) - len(missing)
    print(f"\nГотово: {added} фото в альбоме «{album}».")
    if missing:
        by_uuid = {p["uuid"]: p for p in photos}
        print(f"Не добавлено ({len(missing)}):")
        for u in missing:
            p = by_uuid.get(u, {})
            print(f"  {u}  {p.get('filename', '?')}  {p.get('created', '?')}")
    print("\nДля удаления: открой альбом в Photos, ⌘A → ⌘⌫.")


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--bundle-id",
        action="append",
        default=[],
        help="bundle ID приложения-источника (можно несколько раз)",
    )
    parser.add_argument("--album", default=DEFAULT_ALBUM, help="имя альбома")
    parser.add_argument(
        "--library",
        type=Path,
        default=DEFAULT_LIBRARY,
        help="путь к .photoslibrary",
    )
    parser.add_argument(
        "--make-album",
        action="store_true",
        help="создать альбом и добавить найденное (без флага — только отчёт)",
    )
    parser.add_argument(
        "--list-apps",
        action="store_true",
        help="показать все bundle ID с количеством фото и выйти",
    )
    args = parser.parse_args()

    if not args.list_apps and not args.bundle_id:
        parser.error("нужен хотя бы один --bundle-id (или --list-apps)")

    print(f"Копирую базу из {args.library}...")
    db = copy_database(args.library)
    try:
        if args.list_apps:
            for bundle, count in list_apps(db):
                print(f"{count:7d}  {bundle}")
            return

        photos = find_photos(db, args.bundle_id)
        print_report(photos)
        if photos and args.make_album:
            print()
            make_album(args.album, photos)
    finally:
        shutil.rmtree(db.parent, ignore_errors=True)


if __name__ == "__main__":
    main()
