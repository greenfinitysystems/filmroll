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
If an old env folder exists within filmroll, delete it first. Otherwise, there may be conflicts between Python versions. If you are using visual studio terminal Execution policy is automatical setup when the terminal is opened for the first time. In other situations turn it on by executing the following command.
~~~bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
~~~

~~~bash
python -m venv env
.\env\Scripts\activate
~~~

## 2b. Development Environment on Ubuntu
Setting up development environment on Linux varies slightly based upon what is the default version of Python the Linux distribution originally shipped with. Verify your python version
~~~bash
python3 --version
~~~

### (i). Python version >= 3.11 (Example: Ubuntu 24.04 LTS Desktop or above)
By default Ubuntu 24.04 onwards have Python >= 3.11. No separate Python installation is necessary.
Just create the virtual environment.
~~~bash
sudo apt update
sudo apt install -y software-properties-common python3-venv python3-tk
python3 -m venv env
source env/bin/activate
~~~

### (ii). Python version < 3.11 (Example: Older Ubuntu 22.04.5 LTS Desktop)
Ubuntu 22.04.5 have Python 3.10. Install Python 3.11 from deadsnakes ppa first.
Then create the virtual environment
~~~bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y software-properties-common install python3.11 python3.11-venv python3.11-tk
python3.11 -m venv env
source env/bin/activate
~~~

### 3. Setup Dependencies and Libraries
At times the pip install refuses to run due to cached versions. We may need to clean the cache
~~~bash
python -m pip install --upgrade pip
python -m pip cache purge
pip install -r requirements.txt
~~~

### 4. Run Filmroll from development environment
While you are inside filmroll folder and filmroll virtual environment
~~~bash
python filmroll.py
~~~

## 5. Build Filmroll as Standalone Executable

Install pyinstaller

~~~bash
pip install pyinstaller
~~~

### 5a. Build for Windows
---

Run pyinstaller

~~~bash
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

Filmroll should be built on Linux using a Linux environment. PyInstaller is platform-specific, so a Linux build must be performed on Linux. The following example uses Ubuntu 22.04 LTS Virtual machine with Python 3.11 installed following step 2b(ii). Before building, make sure the correct Python shared library is installed. If you have specifically installed python3.11, the libpython3.11 library may be missing in your system. Installit by running the foloowing command.

~~~bash
sudo apt install -y libpython3.11
~~~

Run pyinstaller

~~~bash
pip install pyinstaller
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

### 6. Building the Linux AppImage

**After successfully building Filmroll with PyInstaller**, proceed to create the AppImage using `linuxdeploy`.

Download the LinuxDeploy AppImage from the official LinuxDeploy GitHub releases page and make it executable. Then create the AppDir structure and package Filmroll as an AppImage. The resulting AppImage can be tested directly without installation.

### 7. Automation Scripts
The following scripts may be considered as an example and **starting point** for Windows / Ubuntu Linux build automation. It assumes that the **developer already completed** necessary steps to install Python 3.11+ and other dependencies as stated above in step 1, 2 and 3.

- [Windows 11](make.ps1)
- [Ubuntu Linux](make.sh)
