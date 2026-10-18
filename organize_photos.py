#!/usr/bin/env python3
"""
Photo Organizer for Google Photos Export
-----------------------------------------
- Extracts a Google Takeout zip file
- Converts HEIC files to JPEG (locally, no cloud)
- Renames all photos with a YYYYMMDD_HHMMSS_ prefix so photo book apps
  sort them correctly by chronological order
- Organizes photos into month subfolders (e.g. 2025-03/)

Usage:
    python3 organize_photos.py <path-to-zip-file> [--output <output-dir>]

Requirements:
    pip install pillow pillow-heif
"""

import argparse
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("❌  Pillow not found. Run: pip install pillow pillow-heif")

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False
    print("⚠️  pillow-heif not found — HEIC files will be skipped.")
    print("   Install with: pip install pillow-heif\n")

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
                        ".webp", ".heic", ".heif"}

# Extensions we want to convert to JPEG
CONVERT_TO_JPEG = {".heic", ".heif"}

# Files to skip (Google Takeout metadata, etc.)
SKIP_PATTERNS = {".json", ".html", ".csv", ".DS_Store", ".Thumbs.db"}


# --------------------------------------------------------------------------- #
# EXIF helpers
# --------------------------------------------------------------------------- #

EXIF_IFD = 0x8769            # sub-block holding the "taken" dates
DATETIME_ORIGINAL = 36867    # when the photo was taken
DATETIME_DIGITIZED = 36868   # when it was digitized (usually the same)
DATETIME = 306               # when the file was last changed


def get_exif_date(path: Path) -> datetime | None:
    """
    Return the photo's date from EXIF, or None if unavailable.
    Prefers the date taken over the date the file was last changed.
    Works for HEIC too (via pillow-heif).
    """
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            exif_ifd = exif.get_ifd(EXIF_IFD)
            candidates = [exif_ifd.get(DATETIME_ORIGINAL),
                          exif_ifd.get(DATETIME_DIGITIZED),
                          exif.get(DATETIME)]
    except Exception:
        return None

    for value in candidates:
        if not value:
            continue
        try:
            # Format: "YYYY:MM:DD HH:MM:SS" (sometimes with trailing junk)
            return datetime.strptime(str(value).strip("\x00 ")[:19],
                                     "%Y:%m:%d %H:%M:%S")
        except ValueError:
            continue
    return None


def get_date_from_filename(name: str) -> datetime | None:
    """
    Try to parse a date from common Google Photos filename patterns.
    e.g. IMG_20250314_183021.jpg  or  PXL_20250314_183021123.jpg
    """
    patterns = [
        r"(\d{4})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})",  # 20250314_183021
        r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})",  # 2025-03-14_18-30-21
    ]
    for pat in patterns:
        m = re.search(pat, name)
        if m:
            try:
                return datetime(*[int(g) for g in m.groups()])
            except ValueError:
                pass
    return None


def get_file_mtime(path: Path) -> datetime:
    """Fall back to the file's modification time."""
    return datetime.fromtimestamp(path.stat().st_mtime)


def best_date(path: Path) -> datetime:
    """Return the best available date for a file, in priority order."""
    return (get_exif_date(path)
            or get_date_from_filename(path.stem)
            or get_file_mtime(path))


# --------------------------------------------------------------------------- #
# File handling
# --------------------------------------------------------------------------- #

def convert_heic_to_jpeg(src: Path, dest_dir: Path) -> Path | None:
    """Convert a HEIC file to JPEG and return the new path."""
    if not HEIC_SUPPORT:
        return None
    dest = dest_dir / (src.stem + ".jpg")
    # Avoid overwriting if the jpeg already exists from a previous run
    if dest.exists():
        dest = dest_dir / (src.stem + "_heic.jpg")
    try:
        with Image.open(src) as img:
            # Keep the photo's metadata (date taken, camera, GPS) in the JPEG
            exif = img.getexif()
            img.convert("RGB").save(dest, "JPEG", quality=95,
                                    exif=exif.tobytes())
        return dest
    except Exception as e:
        print(f"  ⚠️  Could not convert {src.name}: {e}")
        return None


def unique_dest(dest: Path) -> Path:
    """Append _1, _2, … to avoid overwriting an existing file."""
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while True:
        candidate = dest.parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def safe_copy(src: Path, dest: Path, date: datetime) -> None:
    """Copy src to dest and set the copy's file date to the photo's date."""
    dest = unique_dest(dest)
    shutil.copy2(src, dest)
    # Unzipping and HEIC conversion give files today's date. Set it to the
    # photo's date so apps that sort by file date get the right order too.
    timestamp = date.timestamp()
    os.utime(dest, (timestamp, timestamp))


# --------------------------------------------------------------------------- #
# Main pipeline
# --------------------------------------------------------------------------- #

def extract_zip(zip_path: Path, extract_dir: Path) -> None:
    print(f"📦  Extracting {zip_path.name} …")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    print("    Done.\n")


def organize(extract_dir: Path, output_dir: Path) -> dict[str, int]:
    """
    Walk extract_dir, process each image, and copy it into output_dir.
    Returns a dict of {month_folder: count}.
    """
    summary: dict[str, int] = {}
    tmp_dir = output_dir / "_heic_converted"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    all_files = [
        p for p in extract_dir.rglob("*")
        if p.is_file() and p.suffix.lower() not in SKIP_PATTERNS
        and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    print(f"🔍  Found {len(all_files)} media files to process.\n")

    converted = skipped = 0

    for src in all_files:
        ext = src.suffix.lower()

        # ── 1. HEIC → JPEG conversion ──────────────────────────────────────
        if ext in CONVERT_TO_JPEG:
            converted_path = convert_heic_to_jpeg(src, tmp_dir)
            if converted_path is None:
                skipped += 1
                continue
            working = converted_path
        else:
            working = src

        # ── 2. Determine best date ─────────────────────────────────────────
        # Always read the original file: a freshly converted JPEG has
        # today's modification time, which would be wrong.
        date = best_date(src)

        # ── 3. Build destination filename with timestamp prefix ─────────────
        timestamp = date.strftime("%Y%m%d_%H%M%S")
        month_label = date.strftime("%Y-%m")
        new_name = f"{timestamp}_{working.name}"

        month_dir = output_dir / month_label
        month_dir.mkdir(parents=True, exist_ok=True)

        dest = month_dir / new_name
        safe_copy(working, dest, date)

        summary[month_label] = summary.get(month_label, 0) + 1
        converted += 1

    # Clean up temp dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n✅  Processed {converted} files  |  ⚠️  Skipped {skipped} files\n")
    return summary


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Organize a Google Photos Takeout zip into dated folders."
    )
    parser.add_argument("zip_file", help="Path to the Takeout .zip file")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: same folder as zip, named organized_photos_YYYY)"
    )
    parser.add_argument(
        "--keep-extracted", action="store_true",
        help="Keep the temporary extracted folder after processing"
    )
    args = parser.parse_args()

    zip_path = Path(args.zip_file).expanduser().resolve()
    if not zip_path.exists():
        sys.exit(f"❌  File not found: {zip_path}")

    base = zip_path.parent
    extract_dir = base / "takeout_extracted"
    output_dir = Path(args.output).expanduser().resolve() if args.output \
                 else base / f"organized_photos_{datetime.now().year}"

    print("=" * 55)
    print("  📷  Photo Organizer")
    print("=" * 55)
    print(f"  Source zip : {zip_path}")
    print(f"  Output     : {output_dir}")
    print(f"  HEIC support: {'✅ yes' if HEIC_SUPPORT else '❌ no (pip install pillow-heif)'}")
    print("=" * 55 + "\n")

    extract_zip(zip_path, extract_dir)
    summary = organize(extract_dir, output_dir)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("📂  Photos per month:")
    for month in sorted(summary):
        print(f"    {month}: {summary[month]} photos")
    total = sum(summary.values())
    print(f"\n    Total: {total} photos")
    print(f"\n📁  Saved to: {output_dir}\n")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if not args.keep_extracted:
        answer = input("🗑️   Remove temporary extracted folder? [y/N] ").strip().lower()
        if answer == "y":
            shutil.rmtree(extract_dir)
            print("    Removed.")

    print("\n🎉  All done! Import the month folders into your photo book app.")
    print("    Files are named YYYYMMDD_HHMMSS_… so they sort chronologically.\n")


if __name__ == "__main__":
    main()
