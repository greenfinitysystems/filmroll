# region(python_imports)

import logging
import ttkbootstrap as tb
import tkinter as tk
from PIL import Image, ImageTk
from enum import Enum
from typing import Any

# endregion

# region(project_imports)

from core.config import Config
from core.file import FileType
from core.archive import Archive
from ui.dialog import FilterDialog
from ui.loupe import Loupe

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
PADDING = 10

# endregion

# region(enumeratons)

class EditMenu(Enum):
    selectAll = 0
    rejectSelected = 1
    cull = 2
    seperator_1 = 3
    filter = 4
    seperator_2 = 5
    edit_raw = 6
    edit_jpg = 7

class ViewMenu(Enum):
    toggleHideRejected = 0
    zoomIn = 1
    zoomOut = 2
    zoomMax = 3
    zoomMin = 4
    image = 5
    seperator_1 = 6
    refresh = 7
    fullScreen = 8

class PreviewMenu(Enum):
    build = 0
    rebuildAll = 1

# endregion

class ThumbnailGrid(tk.Frame):

# region(class_methods)

    def __init__(self, parent, menu, win):
        super().__init__(parent)

        # rating filter apply
        self._rating_filter = 9
        self._has_filters = False

        self._mainfrm = win
        self._menubar = self._mainfrm.menubar

        self._edit_menu = tk.Menu(self._menubar, tearoff=0, postcommand=self._on_edit_menu_unfold)
        self._edit_menu.add_command(label="Select All", command=self._onkey_ctrl_a, accelerator="Ctrl+A")
        self._edit_menu.add_command(label="Reject", command=self._onkey_delete, accelerator="Del")
        self._edit_menu.add_command(label="Cull", command=self._onkey_shift_delete, accelerator="Ctrl+Shift+Del")
        self._edit_menu.add_separator()
        self._edit_menu.add_command(label="Apply Filter...", command=self._onkey_ctrl_f, accelerator="Ctrl+F")
        self._edit_menu.add_separator()
        self._edit_menu.add_command(label="Export Raw...", command=self._on_edit_copy_raw)
        self._edit_menu.add_command(label="Export Jpeg", command=self._on_edit_copy_jpg)

        self._preview_menu = tk.Menu(self._menubar, tearoff=0, postcommand=self._on_preview_menu_unfold)
        self._preview_menu.add_command(label="Build", command=self._onkey_b, accelerator="B")
        self._preview_menu.add_command(label="Rebuild All", command=self._onkey_ctrl_b, accelerator="Ctrl+B")

        self._view_menu = tk.Menu(self._menubar, tearoff=0, postcommand=self._on_view_menu_unfold)
        self._view_menu.add_command(label="Hide Rejected", command=self._onkey_ctrl_h, accelerator="Ctrl+H")
        self._view_menu.add_command(label="Zoom In", command=self._onkey_ctrl_plus, accelerator="Ctrl+")
        self._view_menu.add_command(label="Zoom Out", command=self._onkey_ctrl_minus, accelerator="Ctrl-")
        self._view_menu.add_command(label="Largest", command=self._onkey_shift_ctrl_plus, accelerator="Ctrl+Shift+")
        self._view_menu.add_command(label="Smallest", command=self._onkey_shift_ctrl_minus, accelerator="Ctrl+Shift+-")
        self._view_menu.add_command(label="Image", command=self._on_open_preview, accelerator="Enter")
        self._view_menu.add_separator()
        self._view_menu.add_command(label="Refresh", command=self._onkey_f5, accelerator="F5")
        self._view_menu.add_command(label="Full Screen", command=self._onkey_f11, accelerator="F11")

        self._canvas = tb.Canvas(self)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.configure(bg="#1e1e1e")

        self._reset()

        cfg = Config()
        self._nopreview = cfg.asset("thumb.jpg")

        # Bindings
        self._canvas.bind("<Configure>", self._on_resize)
        self._canvas.bind("<MouseWheel>", self._on_scroll)
        self._canvas.bind("<Button-4>", self._on_scroll)
        self._canvas.bind("<Button-5>", self._on_scroll)

        self._canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self._canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        self._canvas.bind("<Double-Button-1>", self._on_open_preview)
        self._canvas.bind("<Return>", self._on_open_preview)

        self._canvas.bind("<Key>", self._on_key)
        self._canvas.focus_set()

        # these members should not change on reset
        self._fullscreen = False
        self._loupe = Loupe(self)

# endregion

# region(methods)

    def set_doc(self, archive: Archive, custom_filters: list = None):
        if self._doc: self.unset_doc()

        self._doc = archive
        self._items = self._doc.as_list2()
        self._total_items = len(self._items)

        for i, item in enumerate(self._items):
            self._identity_map[item.identity] = i

        self._menubar.insert_cascade("Help", label="View", menu=self._view_menu)
        self._menubar.insert_cascade("View", label="Preview", menu=self._preview_menu)
        self._menubar.insert_cascade("Preview", label="Edit", menu=self._edit_menu)

        ds = f"PRE {self._total_items} DOC {self._doc.file_count}"
        self._mainfrm.docstat.set(ds)

        self._filters = self._doc.get_filters()

        if custom_filters is not None:
            self._has_filters = self._copy_filters(custom_filters)
            if self._has_filters:
                self._apply_filters()

        self._redraw()
        return True

    def unset_doc(self):
        try:
            self._menubar.delete('Edit')
            self._menubar.delete('Preview')
            self._menubar.delete('View')
            self._mainfrm.docstat.set("PRE 0 DOC 0")
        except:
            pass

        finally:
            self._loupe._on_window_closing()
            self._reset()

    def refresh(self):
        if not self._doc: return

        temp_doc = self._doc
        temp_filters = self._filters

        self.unset_doc()
        self.set_doc(temp_doc, temp_filters)

        self._redraw()

# endregion

# region(private_methods)

    def _reset(self):
        # Data
        self._doc = None
        self._items = []
        self._total_items = 0
        self._identity_map = {}

        # View state management
        self._image_cache = {}
        self._visible_indices = set()

        # zooming
        self._columns = 1
        self._thumb_size = 150
        self._min_size = 60
        self._max_size = 400
        self._zoom_step = 20

        self._zoom_redraw_pending = False
        self._zoom_redraw_requested = False
        self._zoom_latest_direction = None
        self._zoom_latest_pos = None

        # layout
        self._gap = 0
        self._cell = 0
        self._total_rows = 0
        self._total_height = 0
        self._start_x = 0
        self._start_y = 0

        # Filter state
        self._filters = []
        self._filtered_indices = set()
        self._has_filters = False

        # Selection
        self._selected_indices = set()
        self._anchor_index = None
        self._active_index = None

        # Marquee
        self._marquee_start = None
        self._marquee_rect = None
        self._dragging = False
        self._drag_threshold = 5

        # Deletion / rejection
        self._hide_rejected = False

        self._redraw()

    def _redraw(self):
        self._recalculate_layout()
        self._render_visible()

    def _recalculate_layout(self):
        width = self._canvas.winfo_width()

        self._columns = max(1, width // (self._thumb_size + PADDING))

        used_width = self._columns * self._thumb_size
        extra_space = max(0, width - used_width)

        self._gap = extra_space / (self._columns + 1)
        self._cell = self._thumb_size + self._gap

        self._visible_indices = self._get_visible_indices()
        visible_count = len(self._visible_indices)
        self._total_rows = (visible_count + self._columns - 1) // self._columns

        self._total_height = self._total_rows * self._cell

        self._canvas.config(scrollregion=(0, 0, width, self._total_height))

    def _render_visible(self):
        def _draw_rejected(x, y):
            # Layer 1: heavy dark fade
            self._canvas.create_rectangle(
                x, y,
                x + self._thumb_size,
                y + self._thumb_size,
                fill="#000000",
                stipple="gray75",   # heavier than gray50
                outline="",
                tags="thumb",
                # anchor="sw"
            )

            # Layer 2: slight additional dim (solid alpha illusion)
            self._canvas.create_rectangle(
                x, y,
                x + self._thumb_size,
                y + self._thumb_size,
                fill="#000000",
                stipple="gray50",
                outline="",
                tags="thumb"
            )

            self._canvas.create_text(
                x + self._thumb_size - 10,
                y + 10,
                text="✕",
                fill="red",
                font=("Arial", 14, "bold"),
                tags="thumb"
            )

        flt = "-" if self._rating_filter == 9 else str(self._rating_filter)
        if hasattr(self._mainfrm, "selstat"):
            ds = f"SEL {len(self._selected_indices)} FLT {flt}"
            self._mainfrm.selstat.set(ds)

        self._canvas.delete("thumb")

        y_offset = self._canvas.canvasy(0)
        height = self._canvas.winfo_height()

        cell = self._cell

        start_row = int(y_offset // cell) - 1
        end_row = int((y_offset + height) // cell) + 2

        start_row = max(0, start_row)
        end_row = min(self._total_rows, end_row)


        for row in range(start_row, end_row):
            for col in range(self._columns):

                #index = row * self._columns + col

                flat_index = row * self._columns + col
                if flat_index >= len(self._visible_indices):
                    break
                index = self._visible_indices[flat_index]

                if index >= self._total_items:
                    break

                x = self._gap + col * cell
                y = row * cell

                img = self._load_image(index)

                iid = self._canvas.create_image(
                    x + self._thumb_size // 2,
                    y + self._thumb_size // 2,
                    image=img,
                    tags="thumb",
                )

                bbox = self._canvas.bbox(iid)

                # Selection
                if index in self._selected_indices:
                    self._canvas.create_rectangle(
                        x, y,
                        x + self._thumb_size,
                        y + self._thumb_size,
                        outline="#4da3ff",
                        width=2,
                        tags="thumb"
                    )

                if index == self._active_index:
                    self._canvas.create_rectangle(
                        x, y,
                        x + self._thumb_size,
                        y + self._thumb_size,
                        outline="#ffffff",
                        width=2,
                        tags="thumb"
                    )

                rating = self._items[index].metadata.rating

                if 1 <= int(rating) <= 5:    
                    char = "★"
                    color = ("#dddddd", "#FF0000", "#0000FF", "#008000", "#800080", "#F28C28")

                    self._canvas.create_text(
                        bbox[2] - 10,
                        bbox[3] - 10,
                        text=char,
                        fill=color[rating],
                        font=("Arial", 12, "bold"),
                        tags="thumb"
                    )

                # Rejection
                if self._items[index].rejected:
                    _draw_rejected(x, y)

    def _load_image(self, index: int):
        key = (index, self._thumb_size)

        if key in self._image_cache:
            return self._image_cache[key]

        path = self._nopreview if self._items[index].nopreview else self._items[index].low
        img = Image.open(path)
        img.thumbnail((self._thumb_size, self._thumb_size))

        tk_img = ImageTk.PhotoImage(img)
        self._image_cache[key] = tk_img

        return tk_img

    def _update_marquee_selection(self, left: int, top: int, right: int, bottom: int, ctrl):
        new_selection = set()

        cell = self._cell

        start_col = int((left - self._gap) / cell)
        end_col = int((right - self._gap) / cell)

        start_row = int(top / cell)
        end_row = int(bottom / cell)

        start_col = max(0, start_col)
        end_col = min(self._columns - 1, end_col)

        start_row = max(0, start_row)
        end_row = min(self._total_rows - 1, end_row)

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):

                x0 = self._gap + col * cell
                x1 = x0 + self._thumb_size

                if right < x0 or left > x1:
                    continue

                flat_index = row * self._columns + col
                if flat_index >= len(self._visible_indices):
                    break

                index = self._visible_indices[flat_index]

                if index < self._total_items:
                    new_selection.add(index)

        if ctrl:
            self._selected_indices |= new_selection
        else:
            self._selected_indices = new_selection
        self._render_visible()

    def _select_range(self, start: int, end: int):
        if start > end:
            start, end = end, start

        sel_set = set()
        for i in range(start, end + 1):
            if i in self._visible_indices:
                sel_set.add(i)
        self._selected_indices = sel_set

        # self._selected_indices = set(range(start, end + 1))

    def _ensure_visible(self, index: int):
        if self._total_items == 0:
            return False

        if index not in self._visible_indices:
            return

        flat = self._visible_indices.index(index)
        row = flat // self._columns

        view_top = self._canvas.canvasy(0)
        view_bottom = view_top + self._canvas.winfo_height()

        row_top = row * self._cell
        row_bottom = row_top + self._cell

        # Fully visible → do nothing
        if row_top >= view_top and row_bottom <= view_bottom:
            return False

        # Scroll up
        if row_top < view_top:
            new_view_y = row_top
        else:
            new_view_y = row_bottom - self._canvas.winfo_height()

        max_y = max(0, self._total_height - self._canvas.winfo_height())
        new_view_y = max(0, min(new_view_y, max_y))

        self._canvas.yview_moveto(new_view_y / max(1, self._total_height))

        return True

    def _zoom_by(self, alltheway=False):
        self._zoom_redraw_pending = False

        if self._zoom_latest_pos is None:
            return

        anchor_x, anchor_y = self._zoom_latest_pos
        direction = self._zoom_latest_direction
        self._zoom_latest_pos = None
        self._zoom_latest_direction = None
        
        if anchor_x is None or anchor_y is None:
            # fallback → center of viewport
            anchor_x = self._canvas.canvasx(self._canvas.winfo_width() // 2)
            anchor_y = self._canvas.canvasy(self._canvas.winfo_height() // 2)

        cell = self._cell

        col = int((anchor_x - self._gap) // cell)
        row = int(anchor_y // cell)

        index = row * self._columns + col
        if index < 0 or index >= self._total_items:
            return

        offset_x = anchor_x - (self._gap + col * cell)
        offset_y = anchor_y - (row * cell)

        old_x = self._gap + col * cell + offset_x
        old_y = row * cell + offset_y

        new_size = 0

        # Zoom step
        if alltheway and direction < 0:
            new_size = self._min_size

        elif alltheway and direction > 0:
            new_size = self._max_size

        else:
            new_size = self._thumb_size + (self._zoom_step if direction > 0 else -self._zoom_step)
            new_size = max(self._min_size, min(self._max_size, new_size))

        if new_size == self._thumb_size:
            return

        self._thumb_size = new_size

        self._recalculate_layout()
        self._canvas.update_idletasks()

        new_cell = self._cell

        new_row = index // self._columns
        new_col = index % self._columns

        new_x = self._gap + new_col * new_cell + offset_x
        new_y = new_row * new_cell + offset_y

        dx = new_x - old_x
        dy = new_y - old_y

        view_y = self._canvas.canvasy(0)
        new_view_y = view_y + dy

        viewport_h = self._canvas.winfo_height()
        max_y = max(1, self._total_height - viewport_h)

        new_view_y = max(0, min(new_view_y, max_y))

        self._canvas.yview_moveto(new_view_y / max(1, self._total_height))

        self._render_visible()

        if alltheway:
            return

        if self._zoom_latest_pos is not None:
            self._zoom_redraw_pending = True
            self.after(16, self._zoom_by, False)

    def _navigate(self, ctrl, shift, event):
        # -------------------------
        # Ctrl + Home / End
        # -------------------------
        if ctrl and event.keysym == "Home":
            new_index = 0

        elif ctrl and event.keysym == "End":
            new_index = self._total_items - 1

        # -------------------------
        # Page Up / Down
        # -------------------------
        elif event.keysym in ("Next", "Prior"):  # Next=PageDown, Prior=PageUp

            if self._active_index is None:
                self._active_index = 0

            current_row = self._active_index // self._columns

            rows_per_page = max(1, int(self._canvas.winfo_height() // self._cell) - 1)

            if event.keysym == "Next":  # PageDown
                new_row = current_row + rows_per_page
            else:  # PageUp
                new_row = current_row - rows_per_page

            new_row = max(0, min(self._total_rows - 1, new_row))

            col = self._active_index % self._columns
            new_index = new_row * self._columns + col

        # -------------------------
        # Arrow Keys
        # -------------------------
        elif event.keysym in ("Left", "Right", "Up", "Down"):
            if self._active_index is None:
                self._active_index = 0

            # row = self._active_index // self._columns
            # col = self._active_index % self._columns

            if self._active_index not in self._visible_indices:
                if not self._visible_indices:
                    return
                self._active_index = self._visible_indices[0]

            current_flat = self._visible_indices.index(self._active_index)

            row = current_flat // self._columns
            col = current_flat % self._columns
            #

            if event.keysym == "Left":
                col -= 1
            elif event.keysym == "Right":
                col += 1
            elif event.keysym == "Up":
                row -= 1
            elif event.keysym == "Down":
                row += 1
            else:
                return

            # new_index = row * self._columns + col

            new_flat = row * self._columns + col
            new_flat = max(0, min(len(self._visible_indices) - 1, new_flat))

            new_index = self._visible_indices[new_flat]

        # -------------------------
        # Clamp Index
        # -------------------------
        new_index = max(0, min(self._total_items - 1, new_index))

        # -------------------------
        # Selection Logic
        # -------------------------
        if shift and self._anchor_index is not None:
            self._select_range(self._anchor_index, new_index)
        else:
            self._selected_indices = {new_index}
            self._anchor_index = new_index

        self._active_index = new_index

        # -------------------------
        # Ensure Visible
        # -------------------------
        # self._ensure_visible(new_index)
        scrolled = self._ensure_visible(new_index)
        if scrolled:
            self._render_visible()
        else:
            # still need to update selection highlight
            self._render_visible()

    def _get_visible_indices(self):
        return [
            i for i in range(self._total_items) 
            if i not in self._filtered_indices and
            not (self._hide_rejected and self._items[i].rejected)
        ]

    def _get_rejected_indices(self):
        return [self._identity_map[stack.identity] for stack in self._items if stack.rejected]

    def _get_selected_stacks(self):
        return [self._items[i] for i in list(self._selected_indices)]

    def _get_active_stack(self):
        return self._items[self._active_index]

    def _apply_filters(self):
        self._filtered_indices.clear()

        for i in range(self._total_items):

            # filter out items which do not meet our rating filter criteria
            if self._rating_filter != 9:
                if str(self._items[i].metadata.rating) != str(self._rating_filter):
                    self._filtered_indices.add(i)
                    continue

            # if it has met our rating criteria, let us examine
            # if it has met our metadata filter criteria
            for f in self._filters:
                if len(f.selected_values) > 0 and str(f.selected_values[0]).lower() != str(getattr(self._items[i].metadata, f.property)).lower():
                    self._filtered_indices.add(i)
                    break

    def _remove_filters(self):
        for f in self._filters:
            f.selected_values.clear()
        self._apply_filters()

    def _copy_filters(self, filters):
        has_filter = False
        for ef in filters:
            for i, df in enumerate(self._filters):
                if df.property == ef.property:
                    for ev in ef.selected_values:
                        if any(str(item) == str(ev) for item in df.values):
                            self._filters[i].selected_values.append(ev)
                            has_filter = True
        return has_filter

    def _ctrl_plus_minus(self, direction):
        self._zoom_latest_pos = (None, None)
        self._zoom_latest_direction = direction

        if self._active_index is not None:
            row = self._active_index // self._columns
            col = self._active_index % self._columns
            x = self._gap + col * self._cell + self._thumb_size // 2
            y = row * self._cell + self._thumb_size // 2
            self._zoom_latest_pos = (x, y)

        if self._zoom_redraw_pending:
            return
        
        self._zoom_redraw_pending = True
        self.after(16, self._zoom_by, False)

# endregion

# region(event_handlers)

    def _on_handle_zoom(self, event: Any):
        canvas_x = self._canvas.canvasx(event.x)
        canvas_y = self._canvas.canvasy(event.y)

        direction = 1 if (event.num == 4 or event.delta > 0) else -1
        self._zoom_latest_direction = direction
        self._zoom_latest_pos = (canvas_x, canvas_y)

        if self._zoom_redraw_pending:
            return "break"

        self._zoom_redraw_pending = True
        self.after(16, self._zoom_by, False)

        return "break"

    def _on_mouse_down(self, event: Any):
        self._canvas.focus_set()

        self._dragging = False
        self._start_x = self._canvas.canvasx(event.x)
        self._start_y = self._canvas.canvasy(event.y)

    def _on_mouse_drag(self, event: Any):
        x2 = self._canvas.canvasx(event.x)
        y2 = self._canvas.canvasy(event.y)

        dx = abs(x2 - self._start_x)
        dy = abs(y2 - self._start_y)

        if not self._dragging and (dx > self._drag_threshold or dy > self._drag_threshold):
            self._dragging = True

            self._marquee_rect = self._canvas.create_rectangle(
                self._start_x, self._start_y, x2, y2,
                outline="#4da3ff",
                dash=(2, 2),
                width=1,
                tags="marquee"
            )

        if self._dragging:
            self._canvas.coords(
                self._marquee_rect,
                min(self._start_x, x2),
                min(self._start_y, y2),
                max(self._start_x, x2),
                max(self._start_y, y2)
            )

            ctrl = (event.state & 0x0004) != 0

            self._update_marquee_selection(
                min(self._start_x, x2),
                min(self._start_y, y2),
                max(self._start_x, x2),
                max(self._start_y, y2),
                ctrl
            )

    def _on_mouse_up(self, event: Any):
        if not self._dragging:
            self._on_handle_click(event)

        if self._marquee_rect:
            self._canvas.delete(self._marquee_rect)
            self._marquee_rect = None

    def _on_handle_click(self, event: Any):
        canvas_x = self._canvas.canvasx(event.x)
        canvas_y = self._canvas.canvasy(event.y)

        col = int((canvas_x - self._gap) // self._cell)
        row = int(canvas_y // self._cell)

        flat_index = row * self._columns + col
        if flat_index >= len(self._visible_indices):
            return
        index = self._visible_indices[flat_index]

        if index < 0 or index >= self._total_items:
            return

        ctrl = (event.state & 0x0004) != 0
        shift = (event.state & 0x0001) != 0

        if shift and self._anchor_index is not None:
            self._select_range(self._anchor_index, index)
        elif ctrl:
            if index in self._selected_indices:
                self._selected_indices.remove(index)
            else:
                self._selected_indices.add(index)
            self._anchor_index = index
        else:
            self._selected_indices = {index}
            self._anchor_index = index

        self._active_index = index
        self._render_visible()

    def _on_key(self, event: Any):
        if self._total_items == 0:
            return

        ctrl = (event.state & 0x0004) != 0
        shift = (event.state & 0x0001) != 0

        # -------------------------
        # Ctrl + H Toggle Hide Rejected
        # -------------------------

        if ctrl and event.keysym.lower() == "h":
            self._onkey_ctrl_h()
            return

        # -------------------------
        # Ctrl + F Apply Filter
        # -------------------------

        if ctrl and event.keysym.lower() == "f":
            self._onkey_ctrl_f()
            return

        # -------------------------
        # Ctrl + 1, 2, 3, 4, 5, 9 Toggle Rating Filter
        # -------------------------

        if ctrl and event.keysym in ("0", "1", "2", "3", "4", "5", "9"):
            self._onkey_toggle_rating(event)
            return

        # -------------------------
        # Ctrl + Shift + Del Cull
        # -------------------------
        if shift and event.keysym == "Delete":
            self._onkey_shift_delete()
            return

        # -------------------------
        # Delete → Toggle Reject
        # -------------------------
        if event.keysym == "Delete":
            self._onkey_delete()
            return

        # -------------------------
        # Ctrl + R Rebuild Previews
        # -------------------------
        if ctrl and event.keysym.lower() == "r":
            self._onkey_ctrl_r()
            return

        # -------------------------
        # F5 Refresh
        # -------------------------
        if event.keysym == "F5":
            self._onkey_f5()
            return

        # -------------------------
        # F11 Full Screen
        # -------------------------
        if event.keysym == "F11":
            self._onkey_f11()
            return

        # -------------------------
        # Shift + Ctrl + Zoom (anchor to active selection)
        # -------------------------

        if shift and ctrl and event.keysym in ("=", "+"):
            self._onkey_shift_ctrl_plus()
            return

        if shift and ctrl and event.keysym in ("-", "_"):
            self._onkey_shift_ctrl_minus()
            return

        # -------------------------
        # Ctrl + / Ctrl - Zoom (anchor to active selection)
        # -------------------------

        if ctrl and event.keysym in ("=", "+"):
            self._onkey_ctrl_plus()
            return

        if ctrl and event.keysym in ("-"):
            self._onkey_ctrl_minus()
            return

        # -------------------------
        # Select All
        # -------------------------
        if ctrl and event.keysym.lower() == "a":
            self._onkey_ctrl_a()
            return

        # -------------------------
        # 0, 1, 2, 3 → Rating
        # -------------------------
        if event.keysym in ("0", "1", "2", "3", "4", "5"):
            self._onkey_apply_rating(event)
            return

        # -------------------------
        # Navigate using Arrow keys, Home, End, Page Up/Down etc
        # -------------------------
        if event.keysym in ("Home", "End", "Next", "Prior", "Left", "Right", "Up", "Down"):
            self._navigate(ctrl, shift, event)
            return

        # -------------------------
        # Build Previews
        # -------------------------
        if event.keysym.lower() == "b":
            self._onkey_b()
            return

         # -------------------------
        # Rebuild All Previews
        # -------------------------
        if ctrl and event.keysym.lower() == "b":
            self._onkey_ctrl_b()
            return

    def _on_resize(self, event: Any):
        self._redraw()

    def _on_scroll(self, event: Any):
        is_ctrl = (event.state & 0x0004) != 0

        if is_ctrl:
            self._on_handle_zoom(event)
            return

        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._render_visible()

    def _on_open_preview(self, event: Any | None = None):
        count = len(self._selected_indices)

        if count == 0:
            return

        stacks = []

        if count == 1:
            stacks.append(self._items[next(iter(self._selected_indices))])

        elif 2 <= count <= 4:
            for i in list(self._selected_indices):
                stacks.append(self._items[i])

        else:
            # fallback → active image
            if self._active_index is not None:
                stacks.append(self._items[self._active_index])

        self._loupe.show(stacks)

    def _on_edit_menu_unfold(self):
        active = self._doc is not None and len(self._get_visible_indices()) > 0

        state = "normal" if active else "disabled"
        self._edit_menu.entryconfig(EditMenu.selectAll.value, state=state)
        self._edit_menu.entryconfig(EditMenu.rejectSelected.value, state=state)

        state = "normal" if active and self._doc.ready else "disabled"
        self._edit_menu.entryconfig(EditMenu.cull.value, state=state)

        self._edit_menu.entryconfig(EditMenu.filter.value, state=state)
        self._edit_menu.entryconfigure(EditMenu.filter.value, 
            label="Remove Filter" if self._has_filters else "Apply Filter...")

        state = "normal" if active and len(self._get_selected_stacks()) > 0 else "disabled"
        self._edit_menu.entryconfig(EditMenu.edit_raw.value, state=state)
        self._edit_menu.entryconfig(EditMenu.edit_jpg.value, state=state)

    def _on_view_menu_unfold(self):
        active = self._doc is not None and len(self._get_visible_indices()) > 0

        self._view_menu.entryconfigure(ViewMenu.toggleHideRejected.value, 
            label="Show Rejected" if self._hide_rejected else "Hide Rejected")

        self._view_menu.entryconfig(ViewMenu.zoomIn.value, 
            state="normal" if (active and (self._thumb_size < self._max_size)) else "disabled")

        self._view_menu.entryconfig(ViewMenu.zoomOut.value, 
            state="normal" if (active and (self._thumb_size > self._min_size)) else "disabled")

        self._view_menu.entryconfig(ViewMenu.zoomMax.value, 
            state="normal" if (active and (self._thumb_size < self._max_size)) else "disabled")

        self._view_menu.entryconfig(ViewMenu.zoomMin.value, 
            state="normal" if (active and (self._thumb_size > self._min_size)) else "disabled")

        selcount = len(self._selected_indices)

        self._view_menu.entryconfig(ViewMenu.image.value, 
            state="normal" if (active and selcount > 0) else "disabled")

        self._view_menu.entryconfig(ViewMenu.image.value, 
            label="Compare" if (active and (selcount > 1) and (selcount <= 4)) else "Image")

    def _on_preview_menu_unfold(self):
        active = self._doc is not None and len(self._items) > 0
        state = "normal" if active else "disabled"
        self._preview_menu.entryconfig(PreviewMenu.rebuildAll.value, state=state)

        state = "normal" if active and len(self._get_selected_stacks()) > 0 else "disabled"
        self._preview_menu.entryconfig(PreviewMenu.build.value, state=state)

# endregion

# region(user_event_handlers)

    def _onkey_f11(self):
        self._fullscreen = not self._fullscreen
        self._mainfrm.root.attributes("-fullscreen", self._fullscreen)

    def _onkey_ctrl_f(self):
        # remove the previously applied filters
        if self._has_filters:
            self._remove_filters()
            self._has_filters = False
            self._redraw()
            return

        # ask user for filter parameters
        # if custom_filter is not None, it will simply apply the supplied filters
        if FilterDialog(self._mainfrm.root, self._filters).show():
            self._apply_filters()
            self._has_filters = True
            self._redraw()
            return

    def _onkey_ctrl_a(self):
        self._selected_indices = self._visible_indices.copy()
        self._render_visible()

    def _onkey_delete(self):
        selected = self._get_selected_stacks()
        for stack in selected:
            stack.rejected = not stack.rejected
        self._doc.save()

        self._redraw()
        self._loupe._redraw()       

    def _onkey_shift_delete(self):
        if self._doc and self._doc.ready:
            self._mainfrm.on_edit_cull()

    def _onkey_ctrl_h(self):
        self._hide_rejected = not self._hide_rejected
        self._redraw()

    def _onkey_ctrl_plus(self):
        self._ctrl_plus_minus(1)

    def _onkey_ctrl_minus(self):
        self._ctrl_plus_minus(-1)

    def _onkey_shift_ctrl_plus(self):
        self._zoom_latest_pos = (None, None)
        self._zoom_latest_direction = 1
        self._zoom_by(True)

    def _onkey_shift_ctrl_minus(self):
        self._zoom_latest_pos = (None, None)
        self._zoom_latest_direction = -1
        self._zoom_by(True)

    def _onkey_f5(self):
        if self._doc and self._doc.ready:
            self.refresh()

    def _onkey_apply_rating(self, event):
        nval = int(event.keysym)
        stacks = self._get_selected_stacks()
        for stack in stacks:
            stack.metadata.rating = nval
        self._doc.save()

        self._redraw()
        self._loupe._redraw()

    def _onkey_toggle_rating(self, event):
        self._rating_filter = int(event.keysym)
        self._apply_filters()
        self._redraw()

    def _on_edit_copy_raw(self):
        stacks = self._get_selected_stacks()
        if len(stacks) > 0:
            self._mainfrm.on_edit_copy_files(stacks, FileType.RAW)

    def _on_edit_copy_jpg(self):
        stacks = self._get_selected_stacks()
        if len(stacks) > 0:
            self._mainfrm.on_edit_copy_files(stacks, FileType.JPG)

    def _onkey_b(self, event=None):
         if self._doc and self._doc.ready:
            self._mainfrm.on_preview_rebuild(self._get_selected_stacks())

    def _onkey_ctrl_b(self):
        if self._doc and self._doc.ready:
            self._mainfrm.on_preview_rebuild(None)

# endregion
