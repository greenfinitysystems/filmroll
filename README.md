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
