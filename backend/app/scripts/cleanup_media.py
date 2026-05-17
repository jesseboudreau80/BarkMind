#!/usr/bin/env python3
"""
BarkMind Media Cleanup Script

Identifies and optionally removes orphaned media files — files on disk that
have no corresponding case_media record in the database.

Usage:
    # Dry run (report only, no deletions)
    python -m app.scripts.cleanup_media

    # Actually delete orphaned files
    python -m app.scripts.cleanup_media --delete

    # Verbose output
    python -m app.scripts.cleanup_media --verbose

Run from backend/ directory.
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Ensure the backend/ directory is on the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def run_cleanup(delete: bool = False, verbose: bool = False) -> None:
    from app.database import AsyncSessionLocal
    from app.models.case_media import CaseMedia
    from app.services.media_storage import get_storage, LocalStorage
    from sqlalchemy import select

    storage = get_storage()
    if not isinstance(storage, LocalStorage):
        print("Cleanup only supported for LocalStorage backend.")
        return

    print(f"[cleanup] Storage root: {storage.root}")

    # Collect all files on disk
    disk_files: set[str] = set(storage.list_all_files())
    print(f"[cleanup] Files on disk: {len(disk_files)}")

    # Collect all known paths from DB
    db_paths: set[str] = set()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CaseMedia))
        records = result.scalars().all()
        for r in records:
            if r.stored_path:
                db_paths.add(r.stored_path)
            for thumb_path in (r.thumbnails or {}).values():
                if thumb_path:
                    db_paths.add(thumb_path)
            if r.thumbnail_path:
                db_paths.add(r.thumbnail_path)

    print(f"[cleanup] Known DB paths: {len(db_paths)}")

    # Find orphans = disk files not referenced in DB
    # Exclude directories and non-media files (like .gitkeep)
    orphaned: list[str] = []
    skipped: list[str] = []

    for rel_path in sorted(disk_files):
        fname = Path(rel_path).name
        # Skip non-media utility files
        if fname.startswith(".") or not any(
            rel_path.endswith(ext)
            for ext in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm")
        ):
            skipped.append(rel_path)
            continue

        if rel_path not in db_paths:
            orphaned.append(rel_path)
            if verbose:
                print(f"  [orphan] {rel_path}")

    print(f"[cleanup] Skipped non-media files: {len(skipped)}")
    print(f"[cleanup] Orphaned files found: {len(orphaned)}")

    if not orphaned:
        print("[cleanup] Nothing to clean up.")
        return

    if not delete:
        print("[cleanup] Dry run — pass --delete to remove orphaned files.")
        print("[cleanup] Orphaned files:")
        for p in orphaned:
            print(f"  {p}")
        return

    # Delete orphaned files
    deleted = 0
    errors = 0
    for rel_path in orphaned:
        try:
            storage.delete(rel_path)
            deleted += 1
            if verbose:
                print(f"  [deleted] {rel_path}")
        except Exception as exc:
            errors += 1
            print(f"  [error] {rel_path}: {exc}")

    print(f"[cleanup] Deleted: {deleted}  Errors: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser(description="BarkMind media cleanup")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete orphaned files (default: dry run only)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each file found/deleted",
    )
    args = parser.parse_args()
    asyncio.run(run_cleanup(delete=args.delete, verbose=args.verbose))


if __name__ == "__main__":
    main()
