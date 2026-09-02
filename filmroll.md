# Filmroll — User Help
## Version 0.5.0

Filmroll is a FUJIFILM-focused image transfer, archival and metadata-review application.

It is designed around a simple idea: **keep the photographic capture together, review it efficiently, reject what you do not want, and send selected originals to a dedicated RAW editor when required.**

Filmroll is an archive and review tool rather than a replacement for a RAW developer.

---

# 1. Understanding Filmroll

## Archives

An **Archive** is the physical folder managed by Filmroll. It contains your imported photographs and the Filmroll archive file.

A newly created archive has this general structure:

```text
FILMROLL-YYYYMMDDHHMMSS/
├── 1-raw/
├── 2-tif/
├── 3-jpg/
├── 4-low/
└── 9-bin/
    ├── raw/
    ├── tif/
    └── jpg/
```

The archive's database is stored as:

```text
Filmroll.far
```

The `.far` file contains the catalogue, metadata and Filmroll-specific review information.

## Stacks

A **Stack** represents one photographic capture.

A Stack can contain:

- RAW (`.RAF`)
- JPEG (`.JPG` / `.JPEG`)
- TIFF (`.TIF` / `.TIFF`)
- Filmroll preview (`LOW`)

For example, a RAW and JPEG recorded by the camera for the same capture are kept together rather than treated as unrelated photographs.

---

# 2. Photographic Identity

Filmroll creates a photographic Identity from camera metadata.

For FUJIFILM files, the Identity is constructed using:

- Camera body serial number
- Date/time of original capture
- FUJIFILM sequence information when available

A typical Identity looks like:

```text
2DA17223-20260724-060946
```

If the camera reports a sequence number, it can appear as:

```text
2DA17223-20260802-094007-2
```

This Identity is used to associate RAW, JPEG, TIFF and preview representations belonging to the same capture.

Filmroll treats this as a practical photographic identity; it is not intended as a mathematically guaranteed globally unique identifier.

---

# 3. Creating an Archive

Choose:

**File → New...**

Select a folder in which Filmroll should create the archive.

Filmroll creates the archive directory and its standard subfolders, then saves the initial archive file.

You can subsequently change the archive title and description through:

**File → Properties...**

---

# 4. Opening and Saving

## Open

Choose:

**File → Open...**

Select a Filmroll `.far` archive.

## Save

Choose:

**File → Save**

or press:

**Ctrl+S**

Filmroll saves the current archive state, including:

- Stack information
- Ratings
- Rejection state
- Notes
- Archive metadata

## Save As

Choose:

**File → Save As...**

This creates a new archive file at the selected location.

## Close

Choose:

**File → Close**

Filmroll checks for unsaved changes before closing.

---

# 5. Archive Format

Filmroll 0.5.0 stores current `.far` archives using JSON serialization through `jsonpickle`.

This replaces the older direct Python-pickle archive format.

Older Filmroll archives created with the legacy format can still be opened through the conversion workflow.

## Converting a legacy archive

Choose:

**File → Convert...**

Select the old `.far` archive.

Filmroll opens the legacy archive and saves a converted archive in the current format. The converted file is given a `-json` suffix before the `.far` extension.

Keep the original legacy archive until you have confirmed that the converted archive opens correctly.

---

# 6. Importing Photographs

Filmroll supports:

- FUJIFILM RAW: `.RAF`
- JPEG: `.JPG`, `.JPEG`
- TIFF: `.TIF`, `.TIFF`

There are two import methods.

## Add Files

Choose:

**File → Add Files...**

Select individual image files.

## Import Folder

Choose:

**File → Import Folder...**

Select a folder containing photographs.

Filmroll examines the files, reads their metadata, creates or updates Stacks, copies the files into the archive and generates Filmroll previews when required.

Do not import a folder that is inside the current Filmroll archive.

---

# 7. Filmroll Previews

Filmroll uses a dedicated LOW representation for fast browsing.

When a suitable JPEG is available, Filmroll prefers the JPEG for preview generation. RAW files are used as a fallback when a JPEG is unavailable.

Previews are stored in:

```text
4-low/
```

The preview is normally generated once and then reused.

This allows the thumbnail grid to remain responsive even with large RAW files.

---

# 8. Thumbnail Grid

The Thumbnail Grid is the main archive browsing view.

Only the thumbnails needed for the visible portion of the grid are rendered. This keeps navigation responsive even in large archives.

A thumbnail may show:

- Selection outline
- Active-image outline
- Rating star
- Rejected indicator

A rejected photograph is visibly dimmed and marked with an `✕`.

---

# 9. Selecting Photographs

## Single selection

Click a thumbnail.

## Multiple selection

Hold **Ctrl** while clicking thumbnails.

## Range selection

Hold **Shift** and click another thumbnail.

## Select all visible photographs

Press:

**Ctrl+A**

This selects the photographs currently visible after filtering.

---

# 10. Navigating the Thumbnail Grid

Use:

- **Left / Right / Up / Down** — move through photographs
- **Home** — first photograph
- **End** — last photograph
- **Page Up** — previous page
- **Page Down** — next page

Filmroll keeps the active photograph visible while navigating.

---

# 11. Thumbnail Zoom

The thumbnail grid can be resized without changing the archive.

Use:

- **Ctrl + Mouse Wheel** — zoom thumbnails
- **Ctrl + +** — increase thumbnail size
- **Ctrl + -** — decrease thumbnail size
- **Ctrl + Shift + +** — largest thumbnail size
- **Ctrl + Shift + -** — smallest thumbnail size

Mouse-wheel zoom is throttled so that rapid wheel movement does not cause unnecessary redraws.

Normal mouse-wheel scrolling continues to scroll the grid.

---

# 12. Ratings

Every Stack can have a rating from **0 to 5**.

The rating is stored with the Stack.

Use:

- **0** — remove rating
- **1** — one star
- **2** — two stars
- **3** — three stars
- **4** — four stars
- **5** — five stars

When photographs are selected in the Thumbnail Grid, pressing a number applies that rating to the selected photographs.

Ratings are also available in Loupe/Compare.

The rating is displayed as a star on the thumbnail.

---

# 13. Filtering by Rating

Rating filters provide a quick way to review selected classes of photographs.

Use:

- **Ctrl+0** — show rating 0
- **Ctrl+1** — show rating 1
- **Ctrl+2** — show rating 2
- **Ctrl+3** — show rating 3
- **Ctrl+4** — show rating 4
- **Ctrl+5** — show rating 5
- **Ctrl+9** — remove the rating filter

The status bar shows the active rating filter.

---

# 14. Metadata Filtering

Choose:

**Edit → Apply Filter...**

or press:

**Ctrl+F**

Filmroll provides filters for:

- Camera
- Lens
- Focal Length
- Aperture
- ISO
- Film Simulation

A filter can be removed by invoking **Ctrl+F** again when a filter is already active.

The filter operates on the metadata available in the archive.

---

# 15. Rejecting Photographs

Reject is a review state, not an immediate deletion.

Select one or more photographs and press:

**Delete**

or choose:

**Edit → Reject**

Filmroll toggles the rejected state.

Rejected photographs are dimmed and marked with an `✕`.

The rejection state is saved in the archive.

---

# 16. Hiding Rejected Photographs

Press:

**Ctrl+H**

or choose:

**View → Hide Rejected**

This toggles whether rejected photographs are displayed in the Thumbnail Grid.

Hiding a rejected photograph does not delete it.

---

# 17. Culling

Culling is the destructive cleanup operation.

Choose:

**Edit → Cull**

or press:

**Ctrl+Shift+Delete**

Filmroll identifies photographs that should be removed from the active archive and moves their full-size representations into the archive's `9-bin` folders.

The RAW, JPEG and TIFF files are handled according to their type.

LOW previews associated with culled photographs are removed.

### Important

**Culling is destructive from the point of view of the active archive.**

Use Reject and review carefully before performing a cull.

Keep an independent backup of important photographs.

---

# 18. Loupe / Image View

Select one photograph and press:

**Enter**

or double-click it.

Filmroll opens the image in Loupe view.

If multiple photographs are selected, Filmroll can open them together for comparison.

- 1 selected image → single-image view
- 2–4 selected images → Compare view
- More than 4 selected images → Filmroll falls back to the active image

---

# 19. Loupe Navigation

In Loupe/Compare:

- **Left / Right** — navigate photographs
- **Up / Down** — navigate between comparison panes
- **Esc** — close Loupe

When viewing a single photograph, Left/Right navigation moves through the visible archive photographs.

When comparing multiple photographs, Left/Right and Up/Down can be used to change the active comparison position.

---

# 20. Viewing Preview, JPEG and RAW

Press:

**J**

to cycle through the available display modes:

```text
Preview → JPEG → RAW → Preview
```

The current source is shown in the lower-right corner of the image.

Possible indicators include:

```text
JPG
RAW
RAW+JPG
```

If a requested representation is unavailable, Filmroll falls back to an available image.

---

# 21. RAW Viewing

Filmroll can display FUJIFILM RAW files directly using a RAW decoder.

RAW display uses:

- Camera white balance
- Half-size RAW processing

The half-size mode is intentional. Filmroll is primarily an **archive, review and selection tool**, not a RAW development application.

Half-size RAW rendering keeps Loupe, Compare, zoom and pan responsive while still providing a useful inspection view.

For detailed RAW development, pixel-level processing and final image rendering, use a dedicated RAW application.

---

# 22. Loupe Zoom

Zoom is controlled with:

**Ctrl + Mouse Wheel**

This matches the thumbnail-grid zoom convention.

Zoom starts from the fitted image size and increases progressively.

The image maintains its aspect ratio.

At higher magnifications, the image is clipped to the available canvas rather than being continually resized to fit the window.

---

# 23. Mouse-Centred Zoom

Zooming is centred around the mouse pointer.

This means that when you zoom into a particular detail, the area underneath the pointer remains the visual focus.

This is particularly useful for:

- Faces
- Fine details
- Focus inspection
- Texture
- Edge detail
- Small objects

---

# 24. Panning

With a zoomed image:

**Left mouse button + drag**

moves the image.

For Compare view:

**Ctrl + Left mouse button + drag**

performs synchronized panning across the comparison canvases.

This makes it possible to inspect the same region of several photographs at the same time.

---

# 25. Loupe Rendering Performance

Loupe rendering is designed to remain responsive during interaction.

Pan and zoom updates are throttled rather than forcing a complete redraw for every mouse event.

During active dragging, rendering can use a faster resampling path. Once interaction stops, the image can be rendered at higher quality.

This is particularly useful with large JPEGs and RAW images.

---

# 26. Metadata Overlay

Press:

**M**

to toggle the metadata overlay.

The overlay displays photographic metadata associated with the current Stack.

The overlay adapts its width to the displayed information and avoids occupying unnecessary screen space when the information cannot fit usefully.

---

# 27. Copy Metadata

Press:

**Ctrl+C**

in Loupe to copy the current photograph's metadata to the clipboard.

The copied information includes the photographic Identity and the available metadata text.

This is useful when documenting or comparing photographs outside Filmroll.

---

# 28. Histogram

Press:

**H**

to toggle the histogram.

Filmroll displays RGB and luminance/white information for the current image.

The histogram is intended as a quick exposure and tonal-distribution inspection tool rather than as a replacement for a full RAW-development histogram.

---

# 29. Notes

Press:

**N**

to edit notes for the current photograph.

Notes are stored as free-form text in the Stack metadata.

They are not drawn onto the photograph.

Notes are preserved when the archive is saved.

---

# 30. Loupe Ratings

In Loupe:

- **0** — remove rating
- **1** — rating 1
- **2** — rating 2
- **3** — rating 3
- **4** — rating 4
- **5** — rating 5

The rating is immediately reflected in the photograph and saved to the archive.

---

# 31. Rejecting from Loupe

Press:

**Delete**

to toggle Reject/Accept for the current photograph.

The Thumbnail Grid is updated to reflect the new state.

---

# 32. Loupe Context Menu

Right-click in Loupe to access common actions:

- Edit notes
- Rating 1–5
- Unmark rating
- Cycle image source
- Histogram
- Metadata
- Copy Metadata
- Reject/Accept

Keyboard shortcuts are shown alongside the actions where applicable.

---

# 33. Building Previews

If imported photographs do not have Filmroll previews, select the desired photographs and choose:

**Preview → Build**

or press:

**B**

This generates previews for the selected Stacks that need them.

---

# 34. Rebuilding All Previews

Choose:

**Preview → Rebuild All**

The menu currently exposes this action as **Ctrl+B**.

Rebuilding previews is useful when you want to regenerate the archive's LOW representations.

Because preview generation can be time-consuming, Filmroll performs it as a background operation.

---

# 35. Exporting RAW Files

Select the photographs you want to edit and choose:

**Edit → Export Raw...**

Filmroll asks for a destination folder and copies the selected RAW files there.

Filmroll prevents exporting into protected folders belonging to the current archive.

## Fujifilm X RAW STUDIO integration

On Windows, if a valid Fujifilm X RAW STUDIO executable has been configured, Filmroll can offer to open X RAW STUDIO after copying the RAW files.

This creates a convenient workflow:

```text
Filmroll
   ↓
Select photographs
   ↓
Export RAW
   ↓
Open Fujifilm X RAW STUDIO
   ↓
Develop / edit
   ↓
Export JPEG
   ↓
Import JPEG back into Filmroll
```

If X RAW STUDIO is not configured, or Filmroll is running on another operating system, RAW export still works normally.

---

# 36. Configuring X RAW STUDIO

The X RAW STUDIO executable path is configurable in Filmroll's configuration.

Filmroll validates the configured path.

The integration is only offered when:

- The operating system is Windows
- A valid X RAW STUDIO executable has been configured

Filmroll does not require X RAW STUDIO for normal archive, import, browsing, rating, rejection or JPEG workflows.

---

# 37. Exporting JPEG Files

Select photographs and choose:

**Edit → Export Jpeg**

Filmroll copies the JPEG representations of the selected Stacks to the chosen destination.

This is useful when you want to share or process existing camera JPEGs without exporting RAW files.

---

# 38. A Practical FUJIFILM Workflow

A typical workflow can be:

### 1. Import

Import the camera card or a folder containing the day's photographs.

### 2. Browse

Use the Thumbnail Grid to review the photographs.

### 3. Filter

Use metadata filters when you want to isolate a camera, lens, focal length, aperture, ISO or film simulation.

### 4. Rate

Use 1–5 ratings to mark photographs worth keeping or revisiting.

### 5. Reject

Mark unwanted photographs with **Delete**.

### 6. Compare

Select up to four photographs and press **Enter** to compare them.

### 7. Inspect

Use:

- Loupe zoom
- Pan
- Histogram
- Metadata
- RAW/JPEG switching

### 8. Cull

After reviewing the rejected photographs, use **Ctrl+Shift+Delete** to cull.

### 9. Develop

Export selected RAW files to X RAW STUDIO when further RAW development is required.

### 10. Re-import

Import the resulting JPEGs into Filmroll.

This keeps Filmroll focused on archive management and photographic review while allowing a dedicated Fujifilm RAW application to handle development.

---

# 39. Archive Repair

Choose:

**File → Repair...**

Repair is intended for situations where the physical archive has been moved or its files are no longer where Filmroll expects them to be.

You can specify a new archive location.

The repair operation can also unlink missing files from the catalogue.

Use the missing-file option carefully: once catalogue entries are removed, Filmroll will no longer consider those files part of the archive.

After repairing, Filmroll allows you to save the repaired archive.

---

# 40. Archive Integrity

Filmroll can check whether:

- The archive root exists
- Expected files exist
- Files are located in appropriate archive folders
- File names match Filmroll's expected naming convention

If an archive has been moved, use **Repair** rather than manually editing the `.far` file.

---

# 41. Long-Running Operations

Operations such as:

- Import
- Preview generation
- Rebuilding previews
- Culling
- File export

can run in the background.

Filmroll displays progress in the status area.

The application protects the active archive while a long-running operation is in progress.

---

# 42. Cancelling an Operation

When an operation supports cancellation, the status area provides a cancel control.

Cancellation is cooperative: worker processes are asked to stop and exit cleanly.

If files have already been transferred before cancellation, those completed operations are not necessarily undone automatically. Archive consistency can be restored through Filmroll's repair mechanisms.

---

# 43. Closing Filmroll

When closing Filmroll:

- Unsaved archive changes are detected.
- You may save them before exiting.
- Running background operations may require confirmation before Filmroll exits.

For important archives, allow file operations to finish before closing the application.

---

# 44. Full Screen

Press:

**F11**

to toggle full-screen mode.

This is particularly useful when using Loupe or reviewing a large thumbnail grid.

---

# 45. Keyboard Shortcuts — Main Window

| Shortcut | Action |
|---|---|
| Ctrl+N | New Archive |
| Ctrl+O | Open Archive |
| Ctrl+S | Save |
| Ctrl+A | Select All visible |
| Delete | Reject / Accept selected |
| Ctrl+Shift+Delete | Cull |
| Ctrl+F | Apply / remove metadata filter |
| B | Build previews for selected |
| Ctrl+B | Rebuild all previews |
| Ctrl+H | Hide / show rejected |
| Ctrl+Mouse Wheel | Thumbnail zoom |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+Shift++ | Largest thumbnail size |
| Ctrl+Shift+- | Smallest thumbnail size |
| Enter | Open Image / Compare |
| F5 | Refresh |
| F11 | Full Screen |
| Ctrl+0 | Filter rating 0 |
| Ctrl+1 | Filter rating 1 |
| Ctrl+2 | Filter rating 2 |
| Ctrl+3 | Filter rating 3 |
| Ctrl+4 | Filter rating 4 |
| Ctrl+5 | Filter rating 5 |
| Ctrl+9 | Remove rating filter |
| 0 | Apply rating 0 |
| 1–5 | Apply rating 1–5 |
| Arrow keys | Navigate |
| Home | First photograph |
| End | Last photograph |
| Page Up | Previous page |
| Page Down | Next page |

---

# 46. Keyboard Shortcuts — Loupe / Compare

| Shortcut | Action |
|---|---|
| J | Cycle Preview → JPEG → RAW |
| Ctrl+Mouse Wheel | Zoom |
| Left mouse drag | Pan |
| Ctrl+Left mouse drag | Synchronized pan |
| N | Edit notes |
| M | Toggle metadata |
| H | Toggle histogram |
| Ctrl+C | Copy metadata |
| Delete | Reject / Accept |
| 0 | Remove rating |
| 1–5 | Apply rating |
| Left / Right | Navigate |
| Up / Down | Change comparison position |
| Esc | Close Loupe |

---

# 47. Source and File Handling

Filmroll keeps different representations of a capture together.

The normal archive locations are:

| Type | Folder |
|---|---|
| RAW | `1-raw` |
| TIFF | `2-tif` |
| JPEG | `3-jpg` |
| LOW preview | `4-low` |
| Culled RAW | `9-bin/raw` |
| Culled TIFF | `9-bin/tif` |
| Culled JPEG | `9-bin/jpg` |

Filmroll uses its own identity-based file naming convention inside these folders.

LOW preview files use the Identity followed by `-LOW`.

---

# 48. Data Safety

Filmroll is an archive and file-management application. Some operations modify or move physical files.

Recommended practice:

1. Keep the original camera-card data until import has been verified.
2. Keep independent backups of important photographs.
3. Review rejected photographs before culling.
4. Do not manually rename or move files inside a Filmroll archive unless you subsequently use Repair.
5. Keep the original legacy `.far` archive when performing format conversion until the converted archive has been verified.
6. Do not treat the `9-bin` folders as a substitute for a real backup.

---

# 49. What Filmroll Is — and Is Not

Filmroll is intended for:

- Image transfer
- Photographic archiving
- FUJIFILM metadata analysis
- Fast browsing
- Selection
- Rating
- Rejection
- Comparison
- Basic image inspection
- RAW/JPEG review
- Export to a dedicated RAW workflow

Filmroll is **not** intended to replace a full RAW developer.

Its RAW viewing mode is deliberately optimized for inspection and responsiveness rather than maximum-quality demosaicing and editing.

---

# 50. FUJIFILM Metadata

Filmroll makes particular use of FUJIFILM metadata.

Depending on what the camera records, metadata can include information related to:

- Film Simulation
- White Balance
- White Balance fine tuning
- Dynamic Range
- Highlight tone
- Shadow tone
- Colour
- Color Chrome
- Color Chrome FX Blue
- Sharpness
- Clarity
- Grain
- Noise Reduction

Filmroll also exposes selected photographic metadata through its filtering system.

Metadata availability depends on the source file and the information recorded by the camera.

---

# 51. Recommended Working Philosophy

A useful way to think about Filmroll is:

**Archive first. Review second. Develop only what deserves it.**

Instead of sending every RAW file through a RAW developer:

- Import everything
- Review quickly
- Reject obvious failures
- Rate the photographs worth keeping
- Compare similar frames
- Export only the RAW files that need development
- Develop them in X RAW STUDIO or another dedicated RAW application
- Bring the resulting JPEGs back into Filmroll

This keeps the archive organized while avoiding unnecessary RAW-processing work.

---

# 52. Version 0.5.0

Filmroll 0.5.0 includes the current archive format and review workflow described in this document, including:

- JSON-based `.far` persistence through `jsonpickle`
- Legacy archive conversion support
- FUJIFILM photographic Identity construction
- Fast virtualized thumbnail browsing
- Thumbnail zoom
- Ratings and rating filters
- Reject / hide rejected / cull workflow
- Metadata filtering
- Loupe and Compare
- Preview / JPEG / RAW source cycling
- RAW inspection using camera white balance and half-size processing
- Mouse-centred Loupe zoom
- Pan and synchronized Compare panning
- Metadata overlay and clipboard copy
- RGB/luminance histogram
- Notes
- Background preview generation
- RAW and JPEG export
- Optional Fujifilm X RAW STUDIO integration on Windows
- Archive repair
- Full-screen review

---

# 53. Final Note

Filmroll is built around the workflow of photographers who want their camera originals, JPEGs, previews and review decisions to remain together.

For the best experience, treat the Filmroll archive as a managed collection: **import through Filmroll, perform review inside Filmroll, use Repair when an archive is moved, and maintain independent backups of important photographs.**
