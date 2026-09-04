#!/bin/bash

# ------------------------------------------------------------
# CHANGE SETTINGS AS PER YOUR ENVIRONMENT
# ------------------------------------------------------------

PROJPATH="/home/sysadmin/Projects"
LINUXDEPLOY="$PROJPATH/linuxdeploy-x86_64.AppImage"
VERSION=$(python3.11 -c "from core.config import Config; cfg=Config(); print(cfg.version)")

# LOCAL VARIABLES

VENVPATH="$PROJPATH/filmroll-env"
MAKEPATH="$PROJPATH/filmroll-build"
DISTPATH="$PROJPATH/filmroll-dist"
APPLPATH="$PROJPATH/filmroll-app"
EXECFILE="$PROJPATH/filmroll-x86_64"

# ------------------------------------------------------------
# ENABLE VIRTUAL ENVIRONMENT
# ------------------------------------------------------------

rm -rf $MAKEPATH $DISTPATH $APPLPATH

if [ -d "$VENVPATH" ]; then

echo "Virtual environment exists. Skipping"
source "$VENVPATH/bin/activate"

else

echo "Creating new Virtual environment..."

# Change this line to "python3 -m venv env" if Python 3.11+ is 
# the default version shipped with your distro

python3.11 -m venv "$VENVPATH"

source "$VENVPATH/bin/activate"

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

fi

# ------------------------------------------------------------
# BUILD PROJECT USING PYINSTALLER
# ------------------------------------------------------------

echo "Building project..."

pyinstaller \
--workpath "$MAKEPATH" \
--distpath "$DISTPATH" \
--noconfirm \
--clean \
--onedir \
--windowed \
--add-data "assets:assets" \
--contents-directory "filmroll_files" \
--collect-all ttkbootstrap \
--collect-all PIL \
filmroll.py

# ------------------------------------------------------------
# CREATE APPIMAGE USING LINUXDEPLOY
# ------------------------------------------------------------

echo "Creating AppImage..."

mkdir -p $APPLPATH/usr/bin
mkdir -p $APPLPATH/usr/share/applications
mkdir -p $APPLPATH/usr/share/icons/hicolor/512x512/apps

cat << EOF >> $APPLPATH/filmroll.desktop
[Desktop Entry]
Name=Filmroll
Comment=FUJIFILM Image Archive and Review Tool
Exec=filmroll
Icon=filmroll
Type=Application
Categories=Graphics;Photography;
Terminal=false
StartupWMClass=Filmroll
EOF

cp -a "$DISTPATH/filmroll/." "$APPLPATH/usr/bin/"
cp "$APPLPATH/filmroll.desktop" "$APPLPATH/usr/share/applications/filmroll.desktop"
cp assets/icon.png "$APPLPATH/filmroll.png"
cp assets/icon.png "$APPLPATH/usr/share/icons/hicolor/512x512/apps/filmroll.png"

# DOWNLOAD LINUXDEPLOY IF NOT PRESENT

if [ -f "$LINUXDEPLOY" ]; then
echo "linuxdeploy found"
else
echo "Downloading linuxdeploy..."
wget -P "$PROJPATH/" https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
fi

if [ ! -x "$LINUXDEPLOY" ]; then
sudo chmod +x $LINUXDEPLOY
fi

# EXECUTE LINUXDEPLOY

export LDAI_OUTPUT="$EXECFILE.AppImage"
$LINUXDEPLOY --appdir "$APPLPATH" --output appimage

# CLEANUP EVERYTHINGS
rm -rf "$MAKEPATH" "$DISTPATH" "$APPLPATH"

# ------------------------------------------------------------
# FINAL RELEASE PACKAGE
# ------------------------------------------------------------

# Finally move the output file
mv "$EXECFILE.AppImage" "/home/sysadmin/Public/filmroll-x86_64-${VERSION}.AppImage"

