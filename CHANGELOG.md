All notable changes to Filmroll are documented here.
## [0.6.1] - 2026-09-18

### Fixed
- Multiple minor UI related issues fixed

### Changed
- Issue #9 delivered
- Issue #10 delivered
- Performance improvement
- Memory handling is improved 
- multiprocessing is improved
- Application lifecycle manageemnt improved

## [0.6.0] - 2026-09-10

### Fixed
- Multiple navigation issues
- Migrate legacy archives to newer version
- Glitches in multi-process handling
- Application icon now appearing correctly
- Occassionally configuration file was not saving properly
- On Windows Enter button on gallery was not working properly
- Progressbar in the status area is now more prominent
- Application crash protection
- raw image was showing wrong histogram - now fixed

### Changed
- Updated archive schema
- Look and feel of dialogs is now in sync with main theme
- Build Previews 
- Rebuild All Previews
- Export Jpegs feature now allows resizing and adding border and metadata
- Instead of default System Messageboxes, Themed Messageboxes is introduced
- Performance Improvement
- About Statement
- In single image Loupe mode histogram display will turn off if in Loupe window 
  when browsing left right to increase browsing speed. It will also turnoff if changing to a different display mode
  like jpg to raw etc
- Computation of histogram is now asynchronus thereby allowing faster browsing

## [0.5.4] - 2026-09-06

### Fixed
- Issue #4 Exit application by File -> Exit does not exit the app and hangs in memory.
- Issue #5 Rating filter is not preserved while refreshing
- Issue #6 Changes made on a copied archive file writes to the original archive file
- Issue #7 When Loupe view is not open, changing rating on thumbnail makes the program throw exception
- Issue #8 On Ubuntu Numpad Keys and Zooming shortucuts not working

### Changed

- Instead on a separate Convert menu under file, the File -> Open is 
  modified to automatically handle the legacy binary archives.
- Instead of filtering on exact focal length, which often comes as 23.2, 34.8 while using zoom lenses, 
  focal lengths will be grouped in to a range [low - high]. That way focal lengths like 22.8, 23 and 
  23.5 all comes under the 23mm group. (Planned Feature 001)

## [0.5.3] - 2026-09-04

### Fixed

- Issue #2 Zoom is not working properly when there are fewer images
- Issue #3 Gallery allows vertical scrolling when content does not fill viewport

## [0.5.2] - 2026-09-03

### Fixed

- Issue #1 Arrow Keys on Loupe view not working.

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

- Initial release