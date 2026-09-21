# region(python_imports)

import logging
import ttkbootstrap as tb

# endregion

# region(project_imports)

from core.config import Config
from ui.canvas import Canvas, DisplayMode

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class Loupe:

# region(class_methods)

    def __init__(self, parent):
        self._parent = parent
        self._reset()

# endregion

# region(methods)

    def show(self, stacks):
        assert len(stacks) > 0, "No valid stack. Loupe cannot open"

        cfg = Config()

        self._reset()
        self._stacks = stacks

        self._root = tb.Toplevel(self._parent._parent._root)
        self._root.iconphoto(False, self._parent._parent._icon)
        self._root.configure(bg=cfg.gallery_color)

        self._root.update_idletasks()
        self._root.geometry("1000x700")
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_closing)
        self._root.bind("<Key>", self._on_key)

        count = len(self._stacks)
        if    count == 1: self._rows, self._cols = 1, 1
        elif  count == 2: self._rows, self._cols = 1, 2
        elif  count == 3: self._rows, self._cols = 2, 2
        else: self._rows, self._cols = 2, 2

        for r in range(self._rows):
            self._root.rowconfigure(r, weight=1)

        for c in range(self._cols):
            self._root.columnconfigure(c, weight=1)

        if self._canvases is not None:
            for c in self._canvases:
                c._reset()

        self._canvases = []
        for i in range(count):
            self._canvases.append(Canvas(self, i))

        self._redraw()

        self._root.lift()
        self._root.focus_set()
        self._root.deiconify()
        self._root.update_idletasks()

# endregion

# region(event_handlers)

    def _redraw(self, event=None):
        try:
            if self._root is None: 
                return

            self._root.title(self._current_stack().identity)
            for canvas in self._canvases:
                canvas._redraw()

        except Exception as e:
            logwriter.error(f"Exception occured in Loupe._redraw: {str(e)}")

    def _on_window_closing(self):
        if self._canvases is not None:
            for c in self._canvases:
                c._reset()
        self._reset()

    def _on_key(self, event):
        if self._root is None: return
        ctrl = (event.state & 0x0004) != 0
        #shift = (event.state & 0x0001) != 0

        # -------------------------
        # Copy metadata to clipboard
        # -------------------------
        if ctrl and event.keysym == "c":
            self._onkey_ctrl_c()
            return

        # -------------------------
        # Delete → toggle reject
        # -------------------------
        if event.keysym in ("Delete", "KP_Delete"):
            self._onkey_delete()
            return

        # -------------------------
        # Navigation
        # -------------------------
        if event.keysym in ("Left", "Right", "Up", "Down", "KP_Left", "KP_Right", "KP_Up", "KP_Down"):
            self._onkey_arrow(event)
            return

        # -------------------------
        # Escape
        # -------------------------
        if event.keysym == "Escape":
            self._onkey_esc(event)
            return

        # -------------------------
        # n → Toggle notes
        # -------------------------
        if event.keysym == "p":
            self._onkey_p()
            return

        # -------------------------
        # m → Toggle metadata
        # -------------------------
        if event.keysym == "m":
            self._onkey_m()
            return

        # -------------------------
        # h → Toggle histogram
        # -------------------------
        if event.keysym == "h":
            self._onkey_h()
            return

        # -------------------------
        # j → Toggle original jpeg
        # -------------------------
        if event.keysym == "j":
            self._onkey_j()
            return

        # -------------------------
        # 0, 1, 2, 3 → Rating
        # -------------------------
        if event.keysym in ("0", "1", "2", "3", "4", "5", "KP_0", "KP_1", "KP_2", "KP_3", "KP_4", "KP_5", "KP_9"):
            nval = (
                int (event.char)
                if event.char in ('0', '1', '2', '3', '4', '5', '9')
                else int(event.keysym)
            )
        
            self._onkey_apply_rating(nval)
            return "break"

# endregion

# region(user_events)

    def _onkey_esc(self, event):
        self._reset()

    def _onkey_arrow(self, event):
        def _navigate_global():
            if ( event.keysym not in ("Left", "Right", "KP_Left", "KP_Right") or 
                len(self._parent._get_visible_indices()) <= 0
            ):
                return

            self._parent._navigate(False, False, event)
            new_stack = self._parent._get_active_stack()
            if self._stacks[0].identity == new_stack.identity:
                return

            self._stacks[0] = new_stack
            self._active_local = 0
            self._show_histogram = False
            self._canvases[0].reload()

        def _navigate_local():
            count = len(self._stacks)
    
            if event.keysym in ("Left", "KP_Left"):
                self._active_local = max(0, self._active_local - 1)
            elif event.keysym in ("Right", "KP_Right"):
                self._active_local = min(count - 1, self._active_local + 1)
            elif event.keysym in ("Up", "KP_Up"):
                self._active_local = max(0, self._active_local - self._cols)
            elif event.keysym in ("Down", "KP_Down"):
                self._active_local = min(count - 1, self._active_local + self._cols)
            else: return

        if len(self._stacks) == 1: _navigate_global()
        else: _navigate_local()
        self._redraw()

    def _onkey_m(self):
        self._show_metadata = not self._show_metadata
        self._redraw()

    def _onkey_h(self):
        self._show_histogram = not self._show_histogram
        self._redraw()

    def _onkey_j(self):
        if self._display_mode == DisplayMode.preview:
            self._display_mode = DisplayMode.jpeg
        elif self._display_mode == DisplayMode.jpeg:
            self._display_mode = DisplayMode.raw
        else: self._display_mode = DisplayMode.preview

        for canvas in self._canvases:
            canvas._display_mode = self._display_mode
            canvas.reload()

        self._redraw()

    # --

    def _onkey_p(self):
        self._parent._onkey_p(self._parent._indices([self._current_stack(),]))

    def _onkey_delete(self):
        self._parent._onkey_delete(self._parent._indices([self._current_stack(),]))

    def _onkey_ctrl_c(self):
        self._parent._onkey_ctrl_c(self._parent._indices([self._current_stack(),]))

    def _onmenu_apply_rating(self, number):
        self._parent._onmenu_apply_rating(self._parent._indices([self._current_stack(),]), number)

    def _onmenu_export_raw(self):
        self._parent._on_edit_export_raws(self._parent._indices([self._current_stack(),]))

    def _onmenu_export_jpeg(self):
        self._parent._on_edit_export_jpegs(self._parent._indices([self._current_stack(),]))

# endregion

# region(private_methods)

    def _reset(self):
        if hasattr(self, "_canvases") and self._canvases is not None:
            for canvas in self._canvases:
                canvas._reset()

        self._canvases = None

        if hasattr(self, "_root") and self._root is not None:
            self._root.destroy()

        self._root = None

        if hasattr(self, "_stacks") and self._stacks is not None:
            self._stacks.clear()

        self._stacks = None

        self._active_local = 0

        self._show_metadata = False
        self._show_histogram = False
        self._display_mode = DisplayMode.preview

    def _current_stack(self):
        return self._stacks[self._active_local]

    def _show_popup_menu(self, x, y):
        menubutton = tb.Menubutton(self._root, text="Actions", bootstyle="primary")
        popup_menu = tb.Menu(menubutton, tearoff=0)

        popup_menu.add_command(label="Reject", accelerator="Del", command=lambda: self._onkey_delete())
        popup_menu.add_command(label="Copy Metadata", accelerator="Ctrl+C", command=lambda: self._onkey_ctrl_c())
        popup_menu.add_separator()
        popup_menu.add_command(label="Unmark", accelerator="0", command= lambda: self._onmenu_apply_rating(0))
        popup_menu.add_command(label="Red", accelerator="1", command= lambda: self._onmenu_apply_rating(1))
        popup_menu.add_command(label="Blue", accelerator="2", command= lambda: self._onmenu_apply_rating(2))
        popup_menu.add_command(label="Green", accelerator="3", command= lambda: self._onmenu_apply_rating(3))
        popup_menu.add_command(label="Maroon", accelerator="4", command= lambda: self._onmenu_apply_rating(4))
        popup_menu.add_command(label="Orange", accelerator="5", command= lambda: self._onmenu_apply_rating(5))
        popup_menu.add_separator()
        popup_menu.add_command(label="Source", accelerator="J", command=lambda: self._onkey_j())
        popup_menu.add_command(label="Histogram", accelerator="H", command=lambda: self._onkey_h())
        popup_menu.add_command(label="Metadata", accelerator="M", command=lambda: self._onkey_m())
        popup_menu.add_separator()
        popup_menu.add_command(label="Export Raw...", command=lambda: self._onmenu_export_raw())
        popup_menu.add_command(label="Export Jpeg...", command=lambda: self._onmenu_export_jpeg())
        popup_menu.add_separator()
        popup_menu.add_command(label="Properties...", accelerator="P", command=lambda: self._onkey_p())
        

        menubutton['menu'] = popup_menu
        popup_menu.tk_popup(x, y)

# endregion

