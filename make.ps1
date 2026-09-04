# ------------------------------------------------------------
# CHANGE SETTINGS AS PER YOUR ENVIRONMENT
# ------------------------------------------------------------

$PROJPATH = "C:\Users\Bibhas\Documents\Projects\filmroll"
$MAKEPATH = "$PROJPATH\build"
$DISTPATH = "C:\Users\Bibhas\Documents\filmroll"
$VERSION = python -c "from core.config import Config; cfg=Config(); print(cfg.version)"

# ------------------------------------------------------------
# ENABLE VIRTUAL ENVIRONMENT
# ------------------------------------------------------------

# $VENVPATH = "$PROJPATH\env"
# Write-Output "Creating new Virtual environment..."
# python -m venv "$VENVPATH"
# . "$VENVPATH\Scripts\Activate.ps1"
# python -m pip install --upgrade pip
# pip install -r requirements.txt
# pip install pyinstaller

# ------------------------------------------------------------
# BUILD PROJECT USING PYINSTALLER
# ------------------------------------------------------------

# PowerShell way to safely delete folders if they exist
if (Test-Path $MAKEPATH) { Remove-Item -Recurse -Force $MAKEPATH }
if (Test-Path $DISTPATH) { Remove-Item -Recurse -Force $DISTPATH }

Write-Output "Building project..."

pyinstaller `
--workpath "$MAKEPATH" `
--distpath "$DISTPATH" `
--noconfirm `
--clean `
--onedir `
--windowed `
--add-data "assets;assets" `
--contents-directory "filmroll_files" `
--collect-all ttkbootstrap `
--collect-all PIL `
filmroll.py

if (Test-Path $MAKEPATH) { Remove-Item -Recurse -Force $MAKEPATH }

# ------------------------------------------------------------
# FINAL RELEASE PACKAGE
# ------------------------------------------------------------

Copy-Item "RELEASE.md" "$DISTPATH\filmroll\RELEASE.md"
Compress-Archive -Path "$DISTPATH\filmroll\*" -DestinationPath "$DISTPATH\filmroll-${VERSION}.zip" -Force
