# region(python_imports)

import logging
import pyperclip
from enum import Enum
from typing import Any
import ttkbootstrap as tb
from PIL import Image, ImageTk
import copy

# endregion

# region(project_imports)

from core.config import Config
from ui.iptcdialog import BatchIptcDialog, IptcDialog
from ui.searchdialog import SearchDialog
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
    copy = 2
    cull = 3
    seperator_1 = 4
    filter = 5
    seperator_2 = 6
    editRaw = 7
    editJpeg = 8

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

class ImageMenu(Enum):
    build = 0
    rebuildAll = 1
    seperator_1 = 2
    rate0 = 3
    rate1 = 4
    rate2 = 5
    rate3 = 6
    rate4 = 7
    rate5 = 8
    seperator_2 = 9
    editIptc = 10

# endregion

class ThumbnailGrid(tb.Frame):

    FILTER_REJECTED = 1  # 0001
    FILTER_RATING = 2  # 0010
    FILTER_METADATA = 4  # 0100

# region(class_methods)

    def __init__(self, parent: Any, win: Any):
        super().__init__(parent)

        cfg = Config()

        self._parent = win
        self._menubar = self._parent.menubar

        self._edit_menu = tb.Menu(self._menubar, tearoff=0, postcommand=self._on_edit_menu_unfold)
        self._edit_menu.add_command(label="Select All", command=self._onkey_ctrl_a, accelerator="Ctrl+A")
        self._edit_menu.add_command(label="Reject", command=lambda: self._onkey_delete(list(self._selected_indices)), accelerator="Del")
        self._edit_menu.add_command(label="Copy Metadata", command=lambda: self._onkey_ctrl_c(list(self._selected_indices)), accelerator="Ctrl+C")
        self._edit_menu.add_command(label="Cull", command=self._onkey_shift_delete, accelerator="Ctrl+Shift+Del")
        self._edit_menu.add_separator()
        self._edit_menu.add_command(label="Search...", command=self._onkey_ctrl_f, accelerator="Ctrl+F")
        self._edit_menu.add_separator()
        self._edit_menu.add_command(label="Export Raw...", command=lambda: self._on_edit_export_raws(list(self._selected_indices)))
        self._edit_menu.add_command(label="Export Jpeg...", command=lambda: self._on_edit_export_jpegs(list(self._selected_indices)))

        self._image_menu = tb.Menu(self._menubar, tearoff=0, postcommand=self._on_preview_menu_unfold)
        self._image_menu.add_command(label="Build Previews", command=lambda: self._onkey_b(list(self._selected_indices)), accelerator="B")
        self._image_menu.add_command(label="Rebuild All Previews", command=self._onkey_ctrl_b, accelerator="Ctrl+B")
        self._image_menu.add_separator()
        self._image_menu.add_command(label="Unmark",      command=lambda: self._onmenu_apply_rating(list(self._selected_indices), 0), accelerator="0")
        self._image_menu.add_command(label="Red",    command=lambda: self._onmenu_apply_rating(list(self._selected_indices), 1), accelerator="1")
        self._image_menu.add_command(label="Blue",   command=lambda: self._onmenu_apply_rating(list(self._selected_indices), 2), accelerator="2")
        self._image_menu.add_command(label="Green",  command=lambda: self._onmenu_apply_rating(list(self._selected_indices), 3), accelerator="3")
        self._image_menu.add_command(label="Maroon", command=lambda: self._onmenu_apply_rating(list(self._selected_indices), 4), accelerator="4")
        self._image_menu.add_command(label="Orange", command=lambda: self._onmenu_apply_rating(list(self._selected_indices), 5), accelerator="5")
        self._image_menu.add_separator()
        self._image_menu.add_command(label="Properties...", command=lambda: self._onkey_p(list(self._selected_indices)))

        self._view_menu = tb.Menu(self._menubar, tearoff=0, postcommand=self._on_view_menu_unfold)
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
        self._canvas.configure(bg=cfg.gallery_color)

        self._reset()

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

        self._canvas.bind("<Button-3>", self._on_handle_rclick)

        self._canvas.bind("<Key>", self._on_key)
        self._canvas.focus_set()

        # these members should not change on reset
        self._fullscreen = False
        self._loupe = Loupe(self)

# endregion

# region(methods)

    def set_doc(self, archive: Any, redraw: bool=True) -> None:
        if archive is None: return

        if self._doc: self.unset_doc()

        self._doc = archive
        self._items = self._doc.as_list(sorted_list=True)
        self._total_items = len(self._items)

        for i, item in enumerate(self._items):
            self._identity_map[item.identity] = i

        self._menubar.insert_cascade("Help", label="View", menu=self._view_menu)
        self._menubar.insert_cascade("View", label="Image", menu=self._image_menu)
        self._menubar.insert_cascade("Image", label="Edit", menu=self._edit_menu)

        ds = f"PRE {self._total_items} DOC {self._doc.file_count}"
        self._parent.docstat.set(ds)

        self._metadata_filters = self._doc.get_filters()

        if not redraw: return

        self._redraw()
        self._canvas.focus_set()

        return

    def unset_doc(self) -> None:
        try:
            self._menubar.delete('Edit')
            self._menubar.delete('Image')
            self._menubar.delete('View')
            self._parent.docstat.set("PRE 0 DOC 0")
            self._image_cache.clear()
        except:
            pass

        finally:
            self._loupe._on_window_closing()
            self._reset()

    def refresh(self) -> None:
        if not self._doc: return
        self._parent.on_file_reload()

    def backup_state(self) -> tuple:
        return (self._thumb_size, self._active_filters, self._rating_filter, copy.deepcopy(self._metadata_filters))

    def restore_state(self, fstate: tuple) -> None:
        if not self._doc: return
        self._thumb_size, self._active_filters, self._rating_filter, filters = fstate
        self._copy_metadata_filters(filters)
        self._apply_filters()
        self._redraw()
        self._canvas.focus_set()

# endregion

# region(event_handlers)

    def _on_mouse_down(self, event: Any) -> None:
        self._canvas.focus_set()

        self._dragging = False
        self._start_x = self._canvas.canvasx(event.x)
        self._start_y = self._canvas.canvasy(event.y)

    def _on_mouse_drag(self, event: Any) -> None:
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

    def _on_mouse_up(self, event: Any) -> None:
        if not self._dragging:
            self._on_handle_click(event)

        if self._marquee_rect:
            self._canvas.delete(self._marquee_rect)
            self._marquee_rect = None

    def _on_key(self, event: Any) -> str | None:
        if self._total_items == 0:
            return

        ctrl = (event.state & 0x0004) != 0
        shift = (event.state & 0x0001) != 0

        # -------------------------------------------------------------------
        # Ctrl + Shift + Key
        # -------------------------------------------------------------------

        # -------------------------
        # Ctrl + Shift + Del Cull
        # -------------------------
        if shift and event.keysym in ("Delete", "KP_Delete"):
            self._onkey_shift_delete()
            return "break"

        # -------------------------
        # Ctrl + Shift + Zoom (anchor to active selection)
        # -------------------------

        if shift and ctrl and event.keysym in ("KP_Add", "equal", "plus", "=", "+"):
            self._onkey_shift_ctrl_plus()
            return "break"

        if shift and ctrl and event.keysym in ("KP_Subtract", "minus", "underscore", "-", "_"):
            self._onkey_shift_ctrl_minus()
            return "break"

        # -------------------------------------------------------------------
        # Ctrl + Key
        # -------------------------------------------------------------------

        # -------------------------
        # Ctrl + A Select All
        # -------------------------
        if ctrl and event.keysym.lower() == "a":
            self._onkey_ctrl_a()
            return "break"

        # -------------------------
        # Ctrl + B Rebuild All Previews
        # -------------------------
        if ctrl and event.keysym.lower() == "b":
            self._onkey_ctrl_b()
            return "break"

        # -------------------------
        # Ctrl + C Copy Metadata
        # -------------------------
        if ctrl and event.keysym.lower() == "c":
            self._onkey_ctrl_c(list(self._selected_indices))
            return "break"

        # -------------------------
        # Ctrl + F Apply Filter
        # -------------------------

        if ctrl and event.keysym.lower() == "f":
            self._onkey_ctrl_f()
            return "break"

        # -------------------------
        # Ctrl + H Toggle Hide Rejected
        # -------------------------

        if ctrl and event.keysym.lower() == "h":
            self._onkey_ctrl_h()
            return "break"

        # -------------------------
        # I IPTC Propertiews
        # -------------------------

        if event.keysym.lower() == "p":
            self._onkey_p(list(self._selected_indices))
            return "break"

        # -------------------------
        # Ctrl + 1, 2, 3, 4, 5, 9 Toggle Rating Filter
        # -------------------------

        if ctrl and event.keysym in ("0", "1", "2", "3", "4", "5", "9", "KP_0", "KP_1", "KP_2", "KP_3", "KP_4", "KP_5", "KP_9"):
            self._onkey_toggle_rating_filter(event)
            return "break"

        # -------------------------
        # Ctrl + / Ctrl - Zoom (anchor to active selection)
        # -------------------------

        if ctrl and event.keysym in ("KP_Add", "equal", "plus", "=", "+"):
            self._onkey_ctrl_plus()
            return "break"

        if ctrl and event.keysym in ("KP_Subtract", "minus", "underscore", "-", "_"):
            self._onkey_ctrl_minus()
            return "break"

        # -------------------------------------------------------------------
        # Key
        # -------------------------------------------------------------------

        # -------------------------
        # NumPad Enter
        # -------------------------
        if event.keysym in ("KP_Enter",):
            self._on_open_preview(event)
            return "break"
        
        # -------------------------
        # Delete → Toggle Reject
        # -------------------------
        if event.keysym in ("Delete", "KP_Delete"):
            self._onkey_delete(list(self._selected_indices))
            return "break"

        # -------------------------
        # F5 Refresh
        # -------------------------
        if event.keysym == "F5":
            self._onkey_f5()
            return "break"

        # -------------------------
        # F11 Full Screen
        # -------------------------
        if event.keysym == "F11":
            self._onkey_f11()
            return "break"

        # -------------------------
        # 0, 1, 2, 3 → Rating
        # -------------------------
        if event.keysym in ("0", "1", "2", "3", "4", "5", "KP_0", "KP_1", "KP_2", "KP_3", "KP_4", "KP_5", "KP_9"):
            nval = (
                int (event.char)
                if event.char in ('0', '1', '2', '3', '4', '5', '9')
                else int(event.keysym)
            )
        
            self._onmenu_apply_rating(list(self._selected_indices), nval)
            return "break"

        # -------------------------
        # Navigate using Arrow keys, Home, End, Page Up/Down etc
        # -------------------------
        if event.keysym in ("Home", "End", "Next", "Prior", "Left", "Right", "Up", "Down", "KP_Up", "KP_Down", "KP_Left", "KP_Right"):
            self._navigate(ctrl, shift, event)
            return "break"

        # -------------------------
        # Build Previews
        # -------------------------
        if event.keysym.lower() == "b":
            self._onkey_b(list(self._selected_indices))
            return "break"

    def _on_resize(self, _: Any) -> None:
        self._redraw()

    def _on_scroll(self, event: Any) -> str | None:
        is_ctrl = (event.state & 0x0004) != 0

        # ---------------------------------------------------------
        # Ctrl + Wheel = Thumbnail zoom
        # ---------------------------------------------------------
        if is_ctrl:
            self._on_handle_zoom(event)
            return "break"

        # ---------------------------------------------------------
        # If the entire grid fits inside the viewport, there is
        # nowhere to scroll.
        # ---------------------------------------------------------
        viewport_h = self._canvas.winfo_height()
        max_y = max(0, self._total_height - viewport_h)

        if max_y <= 0:
            return "break"

        # ---------------------------------------------------------
        # Determine scroll direction.
        # ---------------------------------------------------------
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = int(-1 * (event.delta / 120))

        if delta == 0:
            return "break"

        # ---------------------------------------------------------
        # Scroll normally.
        # ---------------------------------------------------------
        self._canvas.yview_scroll(delta, "units")

        # ---------------------------------------------------------
        # Clamp the resulting viewport position.
        # ---------------------------------------------------------
        new_y = self._canvas.canvasy(0)
        new_y = max(0, min(new_y, max_y))

        self._canvas.yview_moveto(
            new_y / max(1, self._total_height)
        )

        self._render_visible()

        return "break"

    def _on_open_preview(self, _: Any | None = None) -> None:
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

    def _on_edit_menu_unfold(self) -> None:

        active = self._doc is not None and self._doc.ready
        state = "normal" if active else "disabled"
        self._edit_menu.entryconfig(EditMenu.filter.value, state=state)
        self._edit_menu.entryconfigure(EditMenu.filter.value, 
            label="Remove Search" if (self._active_filters & ThumbnailGrid.FILTER_METADATA) else "Search...")
        self._edit_menu.entryconfig(EditMenu.cull.value, state=state)

        active = self._doc is not None and len(self._get_visible_indices()) > 0
        state = "normal" if active else "disabled"
        self._edit_menu.entryconfig(EditMenu.selectAll.value, state=state)

        active = self._doc is not None and self._doc.ready and len(self._get_visible_indices()) > 0 and len(self._get_selected_stacks()) > 0
        state = "normal" if active else "disabled"
        self._edit_menu.entryconfig(EditMenu.rejectSelected.value, state=state)
        self._edit_menu.entryconfig(EditMenu.copy.value, state=state)
        self._edit_menu.entryconfig(EditMenu.editRaw.value, state=state)
        self._edit_menu.entryconfig(EditMenu.editJpeg.value, state=state)

    def _on_view_menu_unfold(self) -> None:
        active = self._doc is not None and len(self._get_visible_indices()) > 0

        self._view_menu.entryconfigure(ViewMenu.toggleHideRejected.value, 
            label="Show Rejected" if (self._active_filters & ThumbnailGrid.FILTER_REJECTED) else "Hide Rejected")

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

    def _on_preview_menu_unfold(self) -> None:
        active = self._doc is not None and self._doc.ready and len(self._items) > 0
        state = "normal" if active else "disabled"
        self._image_menu.entryconfig(ImageMenu.rebuildAll.value, state=state)

        state = "normal" if active and len(self._get_selected_stacks()) > 0 else "disabled"
        self._image_menu.entryconfig(ImageMenu.build.value, state=state)

        self._image_menu.entryconfig(ImageMenu.rate0.value, state=state)
        self._image_menu.entryconfig(ImageMenu.rate1.value, state=state)
        self._image_menu.entryconfig(ImageMenu.rate2.value, state=state)
        self._image_menu.entryconfig(ImageMenu.rate3.value, state=state)
        self._image_menu.entryconfig(ImageMenu.rate4.value, state=state)
        self._image_menu.entryconfig(ImageMenu.rate5.value, state=state)

        self._image_menu.entryconfig(ImageMenu.editIptc.value, state=state)

# endregion

# region(user_events)

    def _onkey_f11(self) -> None:
        self._fullscreen = not self._fullscreen
        self._parent._root.attributes("-fullscreen", self._fullscreen)

    def _onkey_ctrl_f(self) -> None:
        if not (self._active_filters & ThumbnailGrid.FILTER_METADATA):
            if not SearchDialog(self._parent._root, self._metadata_filters).show():
                return

        self._toggle_filter(ThumbnailGrid.FILTER_METADATA)

    def _onkey_ctrl_a(self) -> None:
        self._selected_indices = self._visible_indices.copy()
        self._render_visible()

    def _onkey_ctrl_h(self) -> None:
        self._toggle_filter(ThumbnailGrid.FILTER_REJECTED)

    def _onkey_ctrl_plus(self) -> None:
        self._ctrl_plus_minus(1)

    def _onkey_ctrl_minus(self) -> None:
        self._ctrl_plus_minus(-1)

    def _onkey_shift_ctrl_plus(self) -> None:
        self._zoom_latest_pos = (None, None)
        self._zoom_latest_direction = 1
        self._zoom_by(True)

    def _onkey_shift_ctrl_minus(self) -> None:
        self._zoom_latest_pos = (None, None)
        self._zoom_latest_direction = -1
        self._zoom_by(True)

    def _onkey_f5(self) -> None:
        if self._doc and self._doc.ready:
            self.refresh()

    def _onkey_toggle_rating_filter(self, event: Any) -> None:
        self._rating_filter = (
            int (event.char) 
            if event.char in ('0', '1', '2', '3', '4', '5', '9') else
            int(event.keysym)
        )

        self._active_filters |= ThumbnailGrid.FILTER_RATING
        self._apply_filters()

        self._redraw()
        self._canvas.focus_set()

    # ------

    def _onkey_ctrl_c(self, indices: list) -> None:
        text_lines = []
        stacks = self._stacks(indices)
        for stack in stacks:
            text_lines.append("\n".join([ f"Identity: {stack.identity}", stack.metadata.get_text(full=True),]))

        pyperclip.copy("\n--\n".join(text_lines))

    def _onmenu_apply_rating(self, indices: list, rating: int) -> None:
        stacks = self._stacks(indices)
        for stack in stacks:
            stack.metadata.rating = rating
    
        self._doc.save()
        self._redraw()
        self._loupe._redraw()

    def _onkey_delete(self, indices: list) -> None:
        if not self._doc or not self._doc.ready:
            return

        stacks = self._stacks(indices)
        for stack in stacks:
            stack.rejected = not stack.rejected

        self._doc.save()
        self._redraw()
        self._loupe._redraw()

    def _on_edit_export_raws(self, indices: list, parent: Any=None) -> None:
        if self._doc is not None and self._doc.ready:
            stacks = self._stacks(indices)
            if len(stacks) > 0:
                self._parent.on_edit_export_raws(stacks=stacks, parent=parent or self)

    def _on_edit_export_jpegs(self, indices: list, parent: Any=None) -> None:
        if self._doc is not None and self._doc.ready:
            stacks = self._stacks(indices)
            if len(stacks) > 0:
                self._parent.on_edit_export_jpegs(stacks=stacks, parent=parent or self)

    def _onkey_b(self, indices:list) -> None:
        if self._doc is not None and self._doc.ready:
            self._parent.on_preview_rebuild_previews(self._stacks(indices))

    def _onkey_p(self, indices: list, parent: Any=None) -> None:
        if len(indices) == 1:
            metadata = self._items[indices[0]].metadata
            dlg = IptcDialog(
                parent=parent or self._parent._root, 
                iptc=metadata.get_iptcinfo()
            )

            if not dlg.show():
                return

            metadata.set_iptcinfo(dlg._iptcinfo)

        elif len(indices) > 1:
            stacks = self._stacks(indices)

            cur_tags = []
            for s in stacks:
                cur_tags.extend(s.metadata.tags)
    
            cur_tags = sorted(list(set(cur_tags)))
            dlg = BatchIptcDialog(
                parent=parent or self._parent._root, 
                tags=cur_tags, 
                title_suffix=f"[{len(indices)} Images]"
            )

            if not dlg.show():
                return
    
            for s in stacks:
                existing_tags = s.metadata.tags
                del_tags = dlg._del_te.get()
                new_list = [v for v in existing_tags if v not in del_tags]
                new_list.extend(dlg._add_te.get())
                s.metadata.tags = new_list

                if ((s.metadata.author and dlg._overwrite.get() == 1) or 
                    not s.metadata.author
                ):
                    s.metadata.author = dlg._author.get()

                if ((s.metadata.copyright and dlg._overwrite.get() == 1) or 
                    not s.metadata.copyright
                ):
                    s.metadata.copyright = dlg._copyright.get()

        else:
            pass
    
        self._doc.save()

    def _onkey_shift_delete(self) -> None:
        if self._doc and self._doc.ready:
            self._parent.on_edit_cull()

    def _onkey_ctrl_b(self) -> None:
        if self._doc is not None and self._doc.ready:
            self._parent.on_preview_rebuild_previews(self._doc.as_list())

# endregion

# region(private_methods)

    def _reset(self) -> None:
        # Data
        self._doc = None
        self._total_items = 0

        if hasattr(self, '_items'): self._items.clear()
        else: self._items = []

        if hasattr(self, '_identity_map'): self._identity_map.clear()
        else: self._identity_map = {}

        if hasattr(self, '_histogram_cache'): self._histogram_cache.clear()
        else: self._histogram_cache = {}

        # View state management
        if hasattr(self, '_image_cache'): self._image_cache.clear()
        else: self._image_cache = {}

        if hasattr(self, '_visible_indices'): self._visible_indices.clear()
        else: self._visible_indices = set()

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
        self._rating_filter = 9
        self._active_filters = 0

        if hasattr(self, '_metadata_filters'): self._metadata_filters.clear()
        else: self._metadata_filters = []

        if hasattr(self, '_filtered_indices'): self._filtered_indices.clear()
        else: self._filtered_indices = set()

        # Selection
        self._anchor_index = None
        self._active_index = None
        if hasattr(self, '_selected_indices'): self._selected_indices.clear()
        else: self._selected_indices = set()

        # Marquee
        self._marquee_start = None
        self._marquee_rect = None
        self._dragging = False
        self._drag_threshold = 5

        self._redraw()

    def _redraw(self) -> None:
        self._recalculate_layout()
        self._render_visible()

    def _recalculate_layout(self) -> None:
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

    def _render_visible(self) -> None:
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
        if hasattr(self._parent, "selstat"):
            ds = f"SEL {len(self._selected_indices)} FLT {flt}"
            self._parent.selstat.set(ds)

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

    def _ensure_visible(self, index: int) -> bool:
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

    def _load_image(self, index: int) -> ImageTk.PhotoImage:
        key = (index, self._thumb_size)
        if key in self._image_cache:
            return self._image_cache[key]

        img = self._items[index].low.open() if self._items[index].low is not None else Image.open(self._nopreview)
        img.thumbnail((self._thumb_size, self._thumb_size))
        self._image_cache[key] = ImageTk.PhotoImage(img)
        img.close()

        return self._image_cache[key]

    def _select_range(self, start: int, end: int) -> None:
        if start > end:
            start, end = end, start

        sel_set = set()
        for i in range(start, end + 1):
            if i in self._visible_indices:
                sel_set.add(i)
        self._selected_indices = sel_set

    def _update_marquee_selection(self, left: int, top: int, right: int, bottom: int, ctrl) -> None:
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

    def _on_handle_click(self, event: Any) -> None:
        index = self._get_clicked_index(event)
        if index < 0:
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

    def _on_handle_rclick(self, event: Any) -> None:
        index = self._get_clicked_index(event)
        if index >= 0:
            self._show_popup_menu(event.x_root, event.y_root, index)

    def _navigate(self, ctrl: bool, shift: bool, event: Any) -> None:
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
        elif event.keysym in ("KP_Left", "Left", "KP_Right", "Right", "KP_Up", "Up", "KP_Down", "Down"):
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

            if event.keysym in ("KP_Left", "Left"):
                col -= 1
            elif event.keysym in ("KP_Right", "Right"):
                col += 1
            elif event.keysym in ("KP_Up", "Up"):
                row -= 1
            elif event.keysym in ("KP_Down", "Down"):
                row += 1
            else:
                return

            # new_index = row * self._columns + col

            new_flat = row * self._columns + col
            new_flat = max(0, min(len(self._visible_indices) - 1, new_flat))

            new_index = self._visible_indices[new_flat]

        else:
            return

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

    def _on_handle_zoom(self, event: Any) -> None:
        canvas_x = self._canvas.canvasx(event.x)
        canvas_y = self._canvas.canvasy(event.y)

        direction = 1 if (event.num == 4 or event.delta > 0) else -1
        self._zoom_latest_direction = direction
        self._zoom_latest_pos = (canvas_x, canvas_y)

        if self._zoom_redraw_pending:
            return "break"

        self._zoom_redraw_pending = True
        self.after(16, self._zoom_by, False)

    def _zoom_by(self, alltheway: bool=False) -> None:
        self._zoom_redraw_pending = False

        if self._zoom_latest_pos is None:
            return

        anchor_x, anchor_y = self._zoom_latest_pos
        direction = self._zoom_latest_direction

        self._zoom_latest_pos = None
        self._zoom_latest_direction = None

        if direction not in (-1, 1):
            return

        # ---------------------------------------------------------
        # Resolve the zoom anchor.
        #
        # Mouse-wheel zoom:
        #     use the actual mouse position.
        #
        # Keyboard zoom / all-the-way zoom:
        #     use the active thumbnail, or the nearest visible
        #     thumbnail to the viewport centre.
        # ---------------------------------------------------------
        anchored_index = None

        if anchor_x is None or anchor_y is None:
            anchor = self._get_zoom_anchor()

            if anchor is None:
                return

            anchored_index, anchor_x, anchor_y = anchor

        # ---------------------------------------------------------
        # If the anchor came from the mouse, determine which
        # currently visible thumbnail occupies that position.
        #
        # IMPORTANT:
        # The displayed grid is indexed through _visible_indices,
        # not directly through the archive's raw item indices.
        # ---------------------------------------------------------
        cell = self._cell

        col = int((anchor_x - self._gap) // cell)
        row = int(anchor_y // cell)

        flat_index = row * self._columns + col

        if anchored_index is None:
            if flat_index < 0 or flat_index >= len(self._visible_indices):
                # Mouse position is not over a valid thumbnail.
                # Fall back to the nearest visible thumbnail.
                anchor = self._get_zoom_anchor()

                if anchor is None:
                    return

                anchored_index, anchor_x, anchor_y = anchor

                cell = self._cell

                # Recalculate the visible position of the fallback
                # thumbnail.
                flat_index = self._visible_indices.index(anchored_index)

                row = flat_index // self._columns
                col = flat_index % self._columns

                anchor_x = (
                    self._gap
                    + col * cell
                    + self._thumb_size / 2
                )

                anchor_y = (
                    row * cell
                    + self._thumb_size / 2
                )
            else:
                anchored_index = self._visible_indices[flat_index]

        else:
            # Active/fallback anchor already identifies the actual
            # archive item. Resolve its current visible position.
            flat_index = self._visible_indices.index(anchored_index)

            row = flat_index // self._columns
            col = flat_index % self._columns

        # ---------------------------------------------------------
        # Preserve the anchor's position inside its grid cell.
        # ---------------------------------------------------------
        offset_x = anchor_x - (self._gap + col * cell)
        offset_y = anchor_y - (row * cell)

        # old_x = self._gap + col * cell + offset_x
        old_y = row * cell + offset_y

        # ---------------------------------------------------------
        # Calculate new thumbnail size.
        # ---------------------------------------------------------
        if alltheway and direction < 0:
            new_size = self._min_size

        elif alltheway and direction > 0:
            new_size = self._max_size

        else:
            new_size = (
                self._thumb_size
                + (
                    self._zoom_step
                    if direction > 0
                    else -self._zoom_step
                )
            )

            new_size = max(
                self._min_size,
                min(self._max_size, new_size)
            )

        if new_size == self._thumb_size:
            return

        self._thumb_size = new_size

        # ---------------------------------------------------------
        # Recalculate the grid.
        #
        # Zooming can change the number of columns, so the same
        # archive item may now have a completely different
        # visible row/column.
        # ---------------------------------------------------------
        self._recalculate_layout()
        self._canvas.update_idletasks()

        # ---------------------------------------------------------
        # Find the SAME archive item again in the new visible grid.
        # ---------------------------------------------------------
        if anchored_index not in self._visible_indices:
            # The item disappeared during layout/filter changes.
            # Fall back to the nearest valid visible thumbnail.
            anchor = self._get_zoom_anchor()

            if anchor is None:
                self._render_visible()
                return

            anchored_index, new_anchor_x, new_anchor_y = anchor

            new_flat_index = self._visible_indices.index(
                anchored_index
            )

            new_row = new_flat_index // self._columns
            new_col = new_flat_index % self._columns

            # Preserve the relative location within the cell.
            offset_x = new_anchor_x - (
                self._gap
                + new_col * self._cell
            )

            offset_y = new_anchor_y - (
                new_row * self._cell
            )

        else:
            new_flat_index = self._visible_indices.index(
                anchored_index
            )

            new_row = new_flat_index // self._columns
            new_col = new_flat_index % self._columns

        new_cell = self._cell

        # new_x = (
        #     self._gap
        #     + new_col * new_cell
        #     + offset_x
        # )

        new_y = (
            new_row * new_cell
            + offset_y
        )

        # ---------------------------------------------------------
        # Move the viewport so the anchor remains at the same
        # screen position.
        # ---------------------------------------------------------
        # dx = new_x - old_x
        dy = new_y - old_y

        view_y = self._canvas.canvasy(0)
        new_view_y = view_y + dy

        viewport_h = self._canvas.winfo_height()
        max_y = max(
            0,
            self._total_height - viewport_h
        )

        new_view_y = max(
            0,
            min(new_view_y, max_y)
        )

        self._canvas.yview_moveto(
            new_view_y / max(1, self._total_height)
        )

        self._render_visible()

        if alltheway:
            return

        if self._zoom_latest_pos is not None:
            self._zoom_redraw_pending = True
            self.after(16, self._zoom_by, False)

    def _get_zoom_anchor(self) -> tuple:
        """
        Return (index, canvas_x, canvas_y) for the best thumbnail to use
        as the zoom anchor.

        Priority:
            1. Active visible thumbnail
            2. Nearest visible thumbnail to viewport centre
            3. None if there are no visible thumbnails
        """

        if not self._visible_indices:
            return None

        # ---------------------------------------------------------
        # 1. Active thumbnail, if it is currently visible
        # ---------------------------------------------------------
        if self._active_index in self._visible_indices:
            flat_index = self._visible_indices.index(self._active_index)

            row = flat_index // self._columns
            col = flat_index % self._columns

            x = self._gap + col * self._cell + self._thumb_size / 2
            y = row * self._cell + self._thumb_size / 2

            return self._active_index, x, y

        # ---------------------------------------------------------
        # 2. No usable active thumbnail.
        #    Find the visible thumbnail nearest to the viewport centre.
        # ---------------------------------------------------------
        viewport_x = self._canvas.canvasx(self._canvas.winfo_width() / 2)
        viewport_y = self._canvas.canvasy(self._canvas.winfo_height() / 2)

        best_index = None
        best_x = None
        best_y = None
        best_distance = None

        for flat_index, index in enumerate(self._visible_indices):
            row = flat_index // self._columns
            col = flat_index % self._columns

            x = self._gap + col * self._cell + self._thumb_size / 2
            y = row * self._cell + self._thumb_size / 2

            distance = (x - viewport_x) ** 2 + (y - viewport_y) ** 2

            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_index = index
                best_x = x
                best_y = y

        if best_index is None:
            return None

        return best_index, best_x, best_y

    def _ctrl_plus_minus(self, direction: int) -> None:
        self._zoom_latest_pos = (None, None)
        self._zoom_latest_direction = direction

        if self._zoom_redraw_pending:
            return

        self._zoom_redraw_pending = True
        self.after(16, self._zoom_by, False)

    def _get_visible_indices(self) -> list:
        return [
            i for i in range(self._total_items) 
            if i not in self._filtered_indices
        ]

    def _get_rejected_indices(self) -> list:
        return [self._identity_map[stack.identity] for stack in self._items if stack.rejected]

    def _get_selected_stacks(self) -> list:
        return [self._items[i] for i in list(self._selected_indices)]

    def _get_active_stack(self) -> Any:
        return self._items[self._active_index]

    def _evaluate_rejected_filter(self, item: Any) -> bool:
            return not item.rejected
    
    def _evaluate_rating_filter(self, item: Any) -> bool:
        return (self._rating_filter == 9) or (item.metadata.rating == self._rating_filter)

    def _evaluate_metadata_filter(self, item) -> bool:
        for f in self._metadata_filters:
            if len(f.selected_values) > 0:
                value = getattr(item.metadata, f.property)
                if isinstance(value, list):
                    return any(item in f.selected_values for item in value)
                else:
                    if value not in f.selected_values:
                        return False
        return True

    def _apply_filters(self) -> None:
        self._filtered_indices.clear()

        for i in range(self._total_items):
            if self._active_filters & ThumbnailGrid.FILTER_REJECTED:
                if not self._evaluate_rejected_filter(self._items[i]):
                    self._filtered_indices.add(i)
                    continue

            if self._active_filters & ThumbnailGrid.FILTER_RATING:
                if not self._evaluate_rating_filter(self._items[i]):
                    self._filtered_indices.add(i)
                    continue

            if self._active_filters & ThumbnailGrid.FILTER_METADATA:
                if not self._evaluate_metadata_filter(self._items[i]):
                    self._filtered_indices.add(i)
                    continue

    def _copy_metadata_filters(self, filters: list) -> None:
        for given_filter in filters:
            for i, my_filter in enumerate(self._metadata_filters):
                if my_filter.property == given_filter.property:
                    valid_values = set(my_filter.values)
                    matching_values = [v for v in given_filter.selected_values if v in valid_values]
                    if len(matching_values) > 0:
                        self._metadata_filters[i].selected_values.clear()
                        self._metadata_filters[i].selected_values.extend(matching_values)

    def _toggle_filter(self, filter: Any) -> None:
        if self._active_filters & filter: self._active_filters &= ~filter
        else: self._active_filters |= filter
        self._apply_filters()
        self._redraw()
        self._canvas.focus_set()

    def _get_clicked_index(self, event: Any) -> int:
        canvas_x = self._canvas.canvasx(event.x)
        canvas_y = self._canvas.canvasy(event.y)

        col = int((canvas_x - self._gap) // self._cell)
        row = int(canvas_y // self._cell)

        flat_index = row * self._columns + col
        if flat_index >= len(self._visible_indices):
            return -1
        index = self._visible_indices[flat_index]

        if index < 0 or index >= self._total_items:
            return -1

        return index

    def _show_popup_menu(self, x, y, index) -> None:
        indices = (
            list(self._selected_indices)
            if len(self._selected_indices) > 1 and index in self._selected_indices
            else [index,]
        )

        menubutton = tb.Menubutton(self._parent._root, text="Actions", bootstyle="primary")
        popup_menu = tb.Menu(menubutton, tearoff=0)

        popup_menu.add_command(label="Reject", accelerator="Del", command=lambda: self._onkey_delete(indices))
        popup_menu.add_command(label="Copy Metadata", accelerator="Ctrl+C", command=lambda: self._onkey_ctrl_c(indices))
        popup_menu.add_separator()
        popup_menu.add_command(label="Unmark", accelerator="0", command= lambda: self._onmenu_apply_rating(indices, 0))
        popup_menu.add_command(label="Red", accelerator="1", command= lambda: self._onmenu_apply_rating(indices, 1))
        popup_menu.add_command(label="Blue", accelerator="2", command= lambda: self._onmenu_apply_rating(indices, 2))
        popup_menu.add_command(label="Green", accelerator="3", command= lambda: self._onmenu_apply_rating(indices, 3))
        popup_menu.add_command(label="Maroon", accelerator="4", command= lambda: self._onmenu_apply_rating(indices, 4))
        popup_menu.add_command(label="Orange", accelerator="5", command= lambda: self._onmenu_apply_rating(indices, 5))
        popup_menu.add_separator()
        popup_menu.add_command(label="Export Raw...", command=lambda: self._on_edit_export_raws(indices))
        popup_menu.add_command(label="Export Jpeg...", command=lambda: self._on_edit_export_jpegs(indices))
        popup_menu.add_separator()
        popup_menu.add_command(label="Build Previews", command=lambda: self._onkey_b(indices))
        popup_menu.add_command(label="Properties...", accelerator="P", command= lambda: self._onkey_p(indices))
        

        menubutton['menu'] = popup_menu
        popup_menu.tk_popup(x, y)

    def _stacks(self, indices: list) -> list:
        stacks = []
        for i in indices:
            stacks.append(self._items[i])
        return stacks

    def _indices(self, stacks: list) -> list:
        indices = []
        for stack in stacks:
            indices.append(self._identity_map[stack.identity])
        return indices

# endregion

