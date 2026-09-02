All notable changes to Filmroll are documented here.

## [0.5.1] - 2026-09-03

### Changed

- Configuration and log files are now stored outside the application
  bundle, allowing Filmroll to operate correctly from read-only
  packaged environments such as AppImage.

### Added

- Linux support with AppImage distribution.
- Linux configuration and log directory at `~/.config/filmroll/`.
- Linux-compatible mouse-wheel handling in Loupe.
- Linux build and packaging support.
- Cross-platform writable configuration and log storage.

### Fixed

- Fixed mouse-wheel events on Linux/X11 being handled by the ThumbnailGrid
  while the Loupe window was active.
- Fixed AppImage startup failure caused by Filmroll attempting to write
  `filmroll.log` into the read-only AppImage mount.
- Fixed packaged application configuration being written to the
  PyInstaller application directory.
- Improved cross-platform handling of Filmroll configuration and log files.

### Packaging

- Added Linux AppImage build.
- Windows packaged application remains supported.
- PyInstaller packaging updated to include required Pillow components.

### Compatibility

- Windows: supported
- Linux: supported via AppImage
- Minimum Python version for source/development builds: Python 3.11

## [0.5.0] - 2026-08-02