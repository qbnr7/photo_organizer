# 📷 Google Photos Organizer

A local Python script that takes a [Google Takeout](https://takeout.google.com/) zip file and prepares your photos for upload to a photo book app.

## What it does

- **Extracts** your Google Takeout zip file
- **Converts HEIC → JPEG** locally (no cloud services)
- **Renames** every photo with a `YYYYMMDD_HHMMSS_` prefix so photo book apps sort them in the correct chronological order
- **Organizes** photos into month subfolders (e.g. `2025-03/`)
- **Skips video files** (`.mp4`, `.mov`, etc.) including those from Live Photos

## Requirements

- Python 3.10+
- [pillow](https://pypi.org/project/Pillow/)
- [pillow-heif](https://pypi.org/project/pillow-heif/) *(for HEIC conversion)*

### Install dependencies

On most systems:
```bash
pip install pillow pillow-heif
```

On Debian-based systems (including Chromebooks), you may get an `externally-managed-environment` error. Use a virtual environment instead:

```bash
# Create a virtual environment inside your project folder
python3 -m venv venv

# Activate it
source venv/bin/activate

# Now install freely inside the venv
pip install pillow pillow-heif
```

Your terminal prompt will change to show `(venv)` confirming it is active. **Every time you open a new terminal**, activate the venv before running the script:

```bash
cd ~/ImageRenames
source venv/bin/activate
```

## Usage

```bash
python3 organize_photos.py <path-to-zip-file>
```

With a custom output folder:

```bash
python3 organize_photos.py ~/Downloads/takeout-2025.zip -o ~/Desktop/photobook_2025
```

Keep the temporary extracted folder after processing:

```bash
python3 organize_photos.py ~/Downloads/takeout-2025.zip --keep-extracted
```

## Output structure

```
organized_photos_2025/
├── 2025-01/
│   ├── 20250112_143022_IMG_4823.jpg
│   └── 20250128_093511_IMG_4901.jpg
├── 2025-02/
│   └── 20250214_182345_IMG_4967.jpg
└── 2025-03/
    └── ...
```

Because filenames start with a timestamp, uploading a month folder to any photo book app will automatically show photos in the right order.

## Date resolution

The script determines each photo's date in this priority order:

1. **EXIF metadata** (`DateTimeOriginal`) embedded in the photo
2. **Filename pattern** — e.g. Google's `PXL_20250314_183021.jpg` naming
3. **File modification time** as a last resort

## Supported formats

| Format | Notes |
|--------|-------|
| `.jpg` / `.jpeg` | Copied as-is |
| `.png` | Copied as-is |
| `.heic` / `.heif` | Converted to JPEG at 95% quality |
| `.webp` | Copied as-is |
| `.gif` / `.bmp` / `.tiff` | Copied as-is |

Video files (`.mp4`, `.mov`, `.avi`, etc.) are intentionally ignored.

## Notes

- The script never deletes your original zip file
- Duplicate filenames are handled automatically by appending `_1`, `_2`, etc.
- Google Takeout metadata files (`.json`) are ignored
