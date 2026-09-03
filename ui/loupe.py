# region(python_imports)

import logging
import ttkbootstrap as tb
import tkinter as tk
import pyperclip

# endregion

# region(project_imports)

from core.config import Config
from ui.dialog import UserCommentDialog
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

        self._reset()
        self._stacks = stacks

        self._root = tk.Toplevel(self._parent)
        self._root.configure(bg="#1e1e1e")
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
        self._root.title(self._current_stack().identity)
        for canvas in self._canvases:
            canvas._redraw()

    def _on_window_closing(self):
        self._reset()

    def _on_key(self, event):
        if self._root is None: return
        ctrl = (event.state & 0x0004) != 0
        shift = (event.state & 0x0001) != 0

        # -------------------------
        # Copy metadata to clipboard
        # -------------------------
        if ctrl and event.keysym == "c":
            self._onkey_ctrl_c(event)
            return

        # -------------------------
        # Delete → toggle reject
        # -------------------------
        if event.keysym == "Delete":
            self._onkey_delete(event)
            return

        # -------------------------
        # Navigation
        # -------------------------
        if event.keysym in ("Left", "Right", "Up", "Down"):
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
        if event.keysym == "n":
            self._onkey_n(event)
            return

        # -------------------------
        # m → Toggle metadata
        # -------------------------
        if event.keysym == "m":
            self._onkey_m(event)
            return

        # -------------------------
        # h → Toggle histogram
        # -------------------------
        if event.keysym == "h":
            self._onkey_h(event)
            return

        # -------------------------
        # j → Toggle original jpeg
        # -------------------------
        if event.keysym == "j":
            self._onkey_j(event)
            return

        # -------------------------
        # 0, 1, 2, 3 → Rating
        # -------------------------
        if event.keysym in ("0", "1", "2", "3", "4", "5"):
            self._onkey_rating(event.keysym)
            return

    def _onkey_esc(self, event):
        self._reset()

    def _onkey_delete(self, event=None):
        self._current_stack().rejected = not self._current_stack().rejected
        self._redraw()
        self._parent._doc.save()
        self._parent._redraw()

    def _onkey_arrow(self, event):
        def _navigate_global():
            if ( event.keysym not in ["Left", "Right"] or 
                len(self._parent._get_visible_indices()) <= 0
            ):
                return
    
            self._parent._navigate(False, False, event)
            self._stacks[0] = self._parent._get_active_stack()
            self._active_local = 0
            self._canvases[0].set_pos(0)
    
        def _navigate_local():
            count = len(self._stacks)
    
            if event.keysym == "Left":
                self._active_local = max(0, self._active_local - 1)
            elif event.keysym == "Right":
                self._active_local = min(count - 1, self._active_local + 1)
            elif event.keysym == "Up":
                self._active_local = max(0, self._active_local - self._cols)
            elif event.keysym == "Down":
                self._active_local = min(count - 1, self._active_local + self._cols)
            else: return

        if len(self._stacks) == 1: _navigate_global()
        else: _navigate_local()
        self._redraw()

    def _onkey_n(self, event=None):
        dlg = UserCommentDialog(self._root, self._current_stack().metadata.comment)
        if not dlg.show(): return
        self._current_stack().metadata.comment = dlg._usernote.get()
        self._parent._doc.save()
        self._redraw()

    def _onkey_m(self, event=None):
        self._show_metadata = not self._show_metadata
        self._redraw()

    def _onkey_ctrl_c(self, event=None):
        stack = self._stacks[0] if len(self._stacks) == 1 else self._stacks[self._active_local]
        pyperclip.copy("\n".join([ f"Identity: {stack.identity}", stack.metadata.get_text_full(),]))

    def _onkey_h(self, event=None):
        self._show_histogram = not self._show_histogram
        self._redraw()

    def _onkey_rating(self, number):
        nval = int(number)
        self._current_stack().metadata.rating = nval
        self._parent._doc.save()
        self._parent._redraw()
        self._redraw()

    def _onkey_j(self, event=None):
        if self._display_mode == DisplayMode.preview:
            self._display_mode = DisplayMode.jpeg
        elif self._display_mode == DisplayMode.jpeg:
            self._display_mode = DisplayMode.raw
        else: self._display_mode = DisplayMode.preview

        for canvas in self._canvases:
            canvas.set_display_mode(self._display_mode)

        self._redraw()

# endregion

# region(private_methhods)

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
        menubutton = tb.Menubutton(self._root, text="Actions", bootstyle="info")
        popup_menu = tk.Menu(menubutton, tearoff=0)
        popup_menu.add_command(label="Edit notes...", accelerator="N", command= self._onkey_n)
        popup_menu.add_separator()
        popup_menu.add_command(label="Red", accelerator="1", command= lambda: self._onkey_rating("1"))
        popup_menu.add_command(label="Blue", accelerator="2", command= lambda: self._onkey_rating("2"))
        popup_menu.add_command(label="Green", accelerator="3", command= lambda: self._onkey_rating("3"))
        popup_menu.add_command(label="Maroon", accelerator="3", command= lambda: self._onkey_rating("4"))
        popup_menu.add_command(label="Orange", accelerator="3", command= lambda: self._onkey_rating("5"))
        popup_menu.add_command(label="Unmark", accelerator="0", command= lambda: self._onkey_rating("0"))
        popup_menu.add_separator()
        popup_menu.add_command(label="Original", accelerator="J", command= self._onkey_j)
        popup_menu.add_command(label="Histogram", accelerator="H", command= self._onkey_h)
        popup_menu.add_command(label="Metadata", accelerator="M", command= self._onkey_m)
        popup_menu.add_command(label="Copy Metadata", accelerator="Ctrl+C", command= self._onkey_ctrl_c)
        popup_menu.add_separator()
        popup_menu.add_command(label="Reject/Accept", accelerator="Del", command= self._onkey_delete)
        menubutton['menu'] = popup_menu
        popup_menu.tk_popup(x, y)

# endregion
