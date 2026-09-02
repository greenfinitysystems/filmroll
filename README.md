## Screenshots

### Archive & Thumbnail View

Filmroll provides a fast, thumbnail-based view of an image archive, with
ratings, photographic metadata and previews visible directly in the grid.

![Filmroll Archive](screenshots/archive.png)

### Loupe & Image Review

Open an image for detailed inspection with metadata, histogram, rating,
zoom and navigation controls.

![Filmroll Loupe](screenshots/loupe.png)

### Compare

Select up to four images and review them side-by-side with synchronized
navigation and inspection.

![Filmroll Compare](screenshots/compare.png)

### Fujifilm Metadata & Film Simulation

Filmroll exposes Fujifilm-specific shooting information directly alongside
the images, including film simulation, white balance and fine-tuning,
Dynamic Range, tone and colour settings, Color Chrome effects, sharpness,
clarity, grain and noise reduction. RGB histograms are also available
during image review.

![Fujifilm Metadata and Film Simulation](screenshots/fujifilm-metadata.png)

### Metadata Filtering

Filter an archive using photographic metadata such as camera, lens,
focal length, aperture, ISO and film simulation.

![Filmroll Metadata Filter](screenshots/filter.png)

## Important Note
--
If you simply want to use Filmroll, download the latest pre-built release from GitHub release page. You only need to clone this repository if you want to access, inspect, modify or build the source code.

## Python Environment on Powershell
---
Please note: If we have a old filmrollenv folder - delete it first. Otherwose there may be conflicting python versions.
~~~
cd [filroll folder]
python -m venv env
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process
.\env\Scripts\activate
pip --version
pip install pyinstaller
python -m pip cache purge (sometimes the poip install refuses to run. We need to clean the cache)
pip install -r requirements.txt
~~~

## Compiling Filmroll for Windows
---
~~~
python -m PyInstaller `
--noconfirm `
--clean `
--onedir `
--windowed `
--add-data "assets;assets" `
--contents-directory "filmroll_files" `
--collect-all ttkbootstrap `
filmroll.py
~~~

## Change this settings if you donot have xrawstudio installed on your computer
"xrawstudio_path": "C:\\Program Files\\FUJIFILM X RAW STUDIO\\FUJIFILM_X_RAW_STUDIO.exe",
