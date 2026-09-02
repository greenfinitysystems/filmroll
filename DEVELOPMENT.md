# Instructions for Developers
## Setting up Development environment
Minimum required Python version for Filmroll to run is 3.11 or above.

### 1. Clone the Repository

If you want to obtain the Filmroll source code using Git, open a terminal (in Linux) or PowerShell window (Windows 11) and execute:

~~~bash
git clone https://github.com/greenfinitysystems/filmroll.git
~~~

Then move into the Filmroll directory:
~~~bash
cd filmroll
~~~
You can then follow the development environment instructions below for your operating system.

## 2a. Development Environment on Windows 11
note: If an old env folder exists within filmroll, delete it first. Otherwise, there may be conflicts between Python versions.
~~~bash
python -m venv env
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\env\Scripts\activate
pip --version
python -m pip cache purge (sometimes the pip install refuses to run. We need to clean the cache)
pip install -r requirements.txt
~~~

## 2b. Development Environment on Ubuntu
Setting up development environment on Linux varies slightly based upon what is the default version of Python the Linux distribution originally shipped with. Verify your python version
~~~bash
python3.11 --version
~~~

### (i). Python version >= 3.11 (Example: Ubuntu 24.04 LTS Desktop or above)
By default Ubuntu 24.04 onwards have Python >= 3.11.
~~~bash
sudo apt update
sudo apt install software-properties-common
sudo apt install python3-venv python3-tk
~~~

Ensure new Python version and create a Python virtual environment
~~~bash
python3 --version
python3 -m venv env
~~~

### (ii). Python version < 3.11 (Example: Older Ubuntu 22.04.5 LTS Desktop)
By default Ubuntu 22.04.5 have Python 3.10. Install Python 3.11 from deadsnakes ppa.
~~~bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt policy python3.11
sudo apt install python3.11 python3.11-venv python3.11-tk
~~~

Ensure new Python version and create a Python virtual environment
~~~bash
python3.11 --version
python3.11 -m venv env
~~~

### 3. Setup Dependencies and Libraries
~~~bash
source env/bin/activate
python --version
python -m pip install --upgrade pip
pip install -r requirements.txt
~~~

### 4. Run Filmroll directly from development environment
While you are inside filmroll folder and filmroll virtual environment
~~~bash
python filmroll.py
~~~

## 5. Build Filmroll as Standalone Executable

### 5a. Build for Windows
---
~~~bash
pip install pyinstaller

python -m PyInstaller `
--noconfirm `
--clean `
--onedir `
--windowed `
--add-data "assets;assets" `
--contents-directory "filmroll_files" `
--collect-all ttkbootstrap `
--collect-all PIL `
filmroll.py
~~~

After successful build filmroll can be tested by double clicking on {path-to-filmroll-folder}\dist\filmroll\filmroll.exe

### 5b. Build for Linux

Filmroll should be built on Linux using a Linux environment. PyInstaller is platform-specific, so a Linux build must be performed on Linux.

The following example uses Ubuntu 22.04 LTS with Python 3.11. Before building, make sure the Python shared library is installed:

~~~bash
sudo apt update
sudo apt install libpython3.11
~~~

Clean any previous folders and run pyinstaller

~~~bash
pip install pyinstaller

rm -rf build dist

pyinstaller \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --add-data "assets:assets" \
    --contents-directory "filmroll_files" \
    --collect-all ttkbootstrap \
    --collect-all PIL \
    filmroll.py
~~~

After a successful build, the application can be tested with:

~~~bash
./dist/filmroll/filmroll
~~~

### 6. Building the Linux AppImage

**After successfully building Filmroll with PyInstaller**, proceed to create the AppImage using `linuxdeploy`.

Download the LinuxDeploy AppImage from the official LinuxDeploy GitHub releases page and make it executable. Then create the AppDir structure and package Filmroll as an AppImage. The resulting AppImage can be tested directly without installation.

**Example Desktop Entry**
~~~
[Desktop Entry]
Name=Filmroll
Comment=FUJIFILM Image Archive and Review Tool
Exec=filmroll
Icon=icon
Type=Application
Categories=Graphics;Photography;
Terminal=false
~~~

Copy binaries to AppDir

~~~bash
rm -rf AppDir
mkdir -p AppDir/usr/bin
cp -a dist/filmroll/. AppDir/usr/bin/
~~~

Copy the desktop entry and icons to desired locations

~~~bash
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/512x512/apps
cp filmroll.desktop AppDir/
cp filmroll.desktop AppDir/usr/share/applications/filmroll.desktop
cp assets/icon.png AppDir
cp assets/icon.png AppDir/usr/share/icons/hicolor/512x512/apps/icon.png
~~~

Finally run linuxdeploy to create the AppImage

~~~bash
./linuxdeploy-x86_64.AppImage --appdir AppDir --output appimage
~~~
