# 📷 Google Photos Organizer

A local Python script that takes a [Google Takeout](https://takeout.google.com/) zip file and prepares your photos for upload to a photo book app.

You probably only run this once a year, so this README is a complete step-by-step guide. If you just want the yearly checklist, jump to [Every year: the short version](#every-year-the-short-version).

---

## What it does

- **Extracts** your Google Takeout zip file
- **Converts HEIC → JPEG** on your own computer (no cloud services)
- **Renames** every photo with a `YYYYMMDD_HHMMSS_` prefix so photo book apps sort them in the correct order
- **Sets each file's date** (date modified) to when the photo was taken, so apps that sort by file date also get the right order
- **Organizes** photos into month folders (e.g. `2025-03/`)
- **Skips video files** (`.mp4`, `.mov`, etc.), including the video part of Live Photos

---

## Every year: the short version

Once everything is set up (see [First-time setup](#first-time-setup)), this is all you do each year:

1. **Download your photos** from Google Takeout ([step 1 below](#step-1-download-your-photos-from-google-takeout)).
2. **Open a terminal** and go to the project folder:
   ```bash
   cd ~/ImageRenames
   ```
3. **Get the latest version** of the script:
   ```bash
   git pull
   ```
4. **Turn on the virtual environment:**
   ```bash
   source venv/bin/activate
   ```
5. **Update the libraries** (in case they changed):
   ```bash
   pip install -r requirements.txt
   ```
6. **Clean up last year's leftovers** (if any):
   ```bash
   rm -rf ~/Downloads/takeout_extracted
   ```
7. **Run the script:**
   ```bash
   python3 organize_photos.py ~/Downloads/takeout-XXXX.zip
   ```
   (Replace `takeout-XXXX.zip` with the actual file name.)
8. **Check the result** in `~/Downloads/organized_photos_<year>/` and upload the month folders to your photo book app.
9. **Turn off the virtual environment** when you're done:
   ```bash
   deactivate
   ```

The rest of this guide explains each step in detail.

---

## First-time setup

You only do this once per computer. If the `~/ImageRenames` folder already exists and has a `venv` folder in it, you can skip this section.

### 1. Make sure Python and Git are installed

Open a terminal and run:

```bash
python3 --version
git --version
```

- Python must be **3.10 or newer**.
- If either command says "not found", install them. On a Chromebook (Linux) or Debian/Ubuntu:
  ```bash
  sudo apt update
  sudo apt install python3 python3-venv git
  ```

### 2. Download the project from GitHub (clone)

"Cloning" makes a copy of the project on your computer. This puts it in a folder called `ImageRenames` in your home folder:

```bash
cd ~
git clone https://github.com/qbnr7/photo_organizer.git ImageRenames
cd ~/ImageRenames
```

> If the repository is private, Git will ask you to log in. Use your GitHub username, and for the password use a **personal access token** (GitHub → Settings → Developer settings → Personal access tokens), not your normal password.

### 3. Create a virtual environment

A virtual environment ("venv") is a private folder for this project's Python libraries. It avoids the `externally-managed-environment` error you get on Chromebooks and Debian.

```bash
cd ~/ImageRenames
python3 -m venv venv
source venv/bin/activate
```

Your terminal prompt now starts with `(venv)`. That means it's active.

### 4. Install the libraries

```bash
pip install -r requirements.txt
```

This installs:
- [pillow](https://pypi.org/project/Pillow/): reads and saves images
- [pillow-heif](https://pypi.org/project/pillow-heif/): reads iPhone HEIC photos

Setup is done. 🎉

---

## Getting updates from Git (pull)

If the script has been changed on GitHub since you last used it, `git pull` downloads the changes:

```bash
cd ~/ImageRenames
git pull
```

What you might see:

| Message | What it means |
|---------|---------------|
| `Already up to date.` | Nothing changed. Carry on. |
| A list of changed files | Updates were downloaded. Run `pip install -r requirements.txt` afterwards in case the libraries changed. |
| `Your local changes ... would be overwritten` | You edited a file on your computer. If you don't need your edits, run `git checkout -- .` and then `git pull` again. |
| `fatal: not a git repository` | You're in the wrong folder. Run `cd ~/ImageRenames` first. |

If `ImageRenames` was copied by hand rather than cloned (so `git pull` doesn't work), just clone a fresh copy as in [First-time setup](#2-download-the-project-from-github-clone) and set up the venv again.

---

## Running it each year, step by step

### Step 1: Download your photos from Google Takeout

1. Go to [takeout.google.com](https://takeout.google.com/).
2. Click **Deselect all**, then scroll down and tick only **Google Photos**.
3. (Optional) Click **All photo albums included** to choose only the albums or years you want, e.g. `Photos from 2025`.
4. Click **Next step**.
5. Choose **Export once**, file type **.zip**, and pick a large file size (e.g. **50 GB**) so you get one zip instead of several.
6. Click **Create export**. Google emails you when it's ready (this can take hours).
7. Download the zip to your **Downloads** folder.

> If Google splits the export into several zips (`takeout-...-001.zip`, `-002.zip`, ...), run the script once per zip with the **same** output folder (see [Options](#options)).

### Step 2: Open a terminal and activate the venv

```bash
cd ~/ImageRenames
git pull
source venv/bin/activate
pip install -r requirements.txt
```

You need to run `source venv/bin/activate` **every time you open a new terminal**.

### Step 3: Remove last year's extracted folder

The script always unzips into a folder called `takeout_extracted` next to the zip. If last year's is still there, those photos will be processed again. Remove it first:

```bash
rm -rf ~/Downloads/takeout_extracted
```

### Step 4: Run the script

```bash
python3 organize_photos.py ~/Downloads/takeout-20260115T101500Z-001.zip
```

Tip: type `python3 organize_photos.py ~/Downloads/takeout` and press **Tab** to fill in the file name automatically.

The script will:
1. Unzip the file
2. Process every photo
3. Print how many photos it found per month
4. Ask: `Remove temporary extracted folder? [y/N]`. Type `y` and press Enter to clean up.

### Step 5: Check the result

Your photos are now in `~/Downloads/organized_photos_<this year>/`:

```
organized_photos_2026/
├── 2025-01/
│   ├── 20250112_143022_IMG_4823.jpg
│   └── 20250128_093511_IMG_4901.jpg
├── 2025-02/
│   └── 20250214_182345_IMG_4967.jpg
└── 2025-03/
    └── ...
```

Note that the output folder is named after the year you **run** the script, not the year the photos were taken. Use `-o` to choose a name yourself (see below).

Open a few month folders and check that the photos look right and are in the right month. Then upload the month folders to your photo book app. The photos show up in date order whether the app sorts by **file name**, **date taken** or **file date**: all three match.

> **CEWE tip:** if the photo list has a sort option, choose **name** or **date**. Sorting by name is the safest, because every file name starts with a date, even for screenshots and other images with no date stored inside.

### Step 6: Clean up

```bash
deactivate
```

You can delete the zip file and the output folder once your photo book is done. The script never deletes the original zip.

---

## Options

```bash
python3 organize_photos.py <zip-file> [-o OUTPUT_FOLDER] [--keep-extracted]
```

| Option | What it does |
|--------|--------------|
| `-o`, `--output` | Choose the output folder. Default: `organized_photos_<current year>` next to the zip. |
| `--keep-extracted` | Don't ask about removing the extracted folder; just keep it. |

Example, naming the folder after the photo year:

```bash
python3 organize_photos.py ~/Downloads/takeout-2025.zip -o ~/Downloads/photobook_2025
```

---

## How dates are chosen

For each photo, the script tries these in order:

1. **Date stored inside the photo** (EXIF metadata): the date it was *taken*, not the date it was last edited. This works for HEIC photos too, and the converted JPEGs keep this information.
2. **Date in the file name**, e.g. `PXL_20250314_183021.jpg` or `IMG_20250314_183021.jpg`
3. **The file's last-modified time**, as a last resort

## Supported formats

| Format | Notes |
|--------|-------|
| `.jpg` / `.jpeg` | Copied as-is |
| `.png` | Copied as-is |
| `.heic` / `.heif` | Converted to JPEG at 95% quality |
| `.webp` | Copied as-is |
| `.gif` / `.bmp` / `.tiff` | Copied as-is |

Video files (`.mp4`, `.mov`, `.avi`, etc.) and Google Takeout's `.json` files are ignored.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `externally-managed-environment` when running `pip` | The venv isn't active. Run `source venv/bin/activate` first. |
| `Pillow not found` | Activate the venv, then `pip install -r requirements.txt`. |
| `pillow-heif not found — HEIC files will be skipped` | Same fix as above. |
| `File not found` | Check the zip's path and name. Use **Tab** to autocomplete it. |
| `python3: command not found` | Install Python (see [First-time setup](#1-make-sure-python-and-git-are-installed)). |
| Some photos end up in the wrong month (often the current month) | The script couldn't find a date in the photo or its name and used the file's time instead. This can happen with screenshots or images saved from messages, which often have no date stored. Move those photos by hand. |
| Last year's photos show up again | Delete `~/Downloads/takeout_extracted` before running (Step 3). |

---

## Notes

- The script never deletes your original zip file.
- If two photos would get the same name, it adds `_1`, `_2`, etc.
- Everything runs on your own computer. Nothing is uploaded anywhere.
