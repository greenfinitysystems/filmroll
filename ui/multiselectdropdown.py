# region(python_imports)

import sys
import tkinter as tk
import ttkbootstrap as ttk

# endregion

# region(project_imports)

# There is nothing here

# endregion

# region(globals)

# There is nothing here

# endregion

class MultiSelectDropdown(ttk.Frame):
    """
    A reusable multi-select dropdown widget.

    The collapsed widget displays the current selection.
    Clicking it opens a popup containing a searchable list
    of checkboxes.

    Parameters
    ----------
    parent:
        Parent tkinter widget.

    values:
        Iterable of strings to display.

    searchable:
        If True, a search entry is displayed in the popup.

    command:
        Optional callback called whenever the selection changes.
        The callback receives the current selection as a list.

    width:
        Width of the collapsed display.

    """

# region(class_methods)

    def __init__(
        self,
        parent,
        values=None,
        searchable=True,
        command=None,
        width=20,
        max_height=100,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self._values = list(values or [])
        self._selected = set()
        self._searchable = searchable
        self._command = command
        self._width = width
        self._max_height = max_height

        self._popup = None
        self._search_var = None
        self._checkbox_vars = {}
        self._checkbox_widgets = {}

        self._outside_click_binding = None
        self._mousewheel_tag = f"MultiSelectDropdown_{id(self)}"

        self._build()

# endregion

# region(methods)

    def get(self):
        """Return the currently selected values as a list."""
        return [value for value in self._values if value in self._selected]

    def set(self, values):
        """Set the current selection."""
        values = set(values or [])

        self._selected = {
            value for value in self._values
            if value in values
        }

        self._update_display()
        self._notify()

    def clear(self):
        """Clear the current selection."""
        self._selected.clear()
        self._update_checkboxes()
        self._update_display()
        self._notify()

    def select_all(self):
        """Select all available values."""
        self._selected = set(self._values)

        self._update_checkboxes()
        self._update_display()
        self._notify()

    def values(self, values=None):
        """
        Get or replace the available values.

        values()        -> current values\n
        values(new)     -> replace available values
        """
        if values is None:
            return list(self._values)

        self._values = list(values)
        self._selected.intersection_update(self._values)

        if self._popup is None:
            self._update_display()
            return
        
        self._update_controls_visibility()
        self._build_checkbox_list()

        self._list_container.update_idletasks()
        self._list_canvas.update_idletasks()
        self._popup.update_idletasks()

        self._update_list_height()

        self._popup.update_idletasks()
        self._position_popup()

        self._update_display()

# endregion

# region(private_methods)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _build(self):
        self._display = tk.Frame(
            self,
            bg="white",
            highlightthickness=1,
            highlightbackground="#b8b8b8",
            highlightcolor="#808080",
        )

        self._display.pack(fill="x")

        self._display_text = tk.Label(
            self._display,
            text="",
            anchor="w",
            bg="white",
        )

        self._display_text.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 4),
        )

        self._display_arrow = tk.Label(
            self._display,
            text="▼",
            bg="white",
            fg="#666666",
            width=2,
        )

        self._display_arrow.pack(
            side="right",
            padx=(0, 4),
        )

        self._display.bind(
            "<Button-1>",
            lambda event: self._toggle_popup(),
        )

        self._display_text.bind(
            "<Button-1>",
            lambda event: self._toggle_popup(),
        )

        self._display_arrow.bind(
            "<Button-1>",
            lambda event: self._toggle_popup(),
        )

        self._update_display()

    # ------------------------------------------------------------------
    # Popup
    # ------------------------------------------------------------------

    def _toggle_popup(self):
        if self._popup is not None and self._popup.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        self._popup = tk.Toplevel(self)

        if sys.platform.startswith('linux'):
        # Tells the Linux window manager this is a borderless utility/splash component
        # This leaves event propagation and focus management fully intact
            self._popup.wm_attributes('-type', 'splash')
        else:
            # Windows handles overridedirect cleanly without destroying event loops
            self._popup.overrideredirect(True)

        self._popup.title("")
        self._popup.transient(self.winfo_toplevel())
        self._popup.resizable(False, False)

        border = tk.Frame(
            self._popup,
            bd=0,
            highlightthickness=1,
            highlightbackground="#d0d0d0",
            highlightcolor="#d0d0d0",
        )

        border.pack(fill="both", expand=True)

        container = ttk.Frame(border, padding=5,)
        container.pack(fill="both", expand=True)

        if self._searchable:
            self._search_var = tk.StringVar()

            search = ttk.Entry(
                container, 
                textvariable=self._search_var,
            )

            self._search_var.trace_add(
                "write",
                self._filter_changed,
            )

            search.pack(fill="x", pady=(0, 5))

        list_frame = ttk.Frame(container)
        list_frame.pack(fill="both", expand=True)

        self._list_canvas = tk.Canvas(
            list_frame,
            highlightthickness=0,
            borderwidth=0,
            width=1,
            height=1,
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self._list_canvas.yview,
        )

        self._list_canvas.configure(yscrollcommand=scrollbar.set,)
        self._list_canvas.pack(side="left",fill="both",expand=True,)
        scrollbar.pack(side="right",fill="y",)

        self._list_container = ttk.Frame(self._list_canvas)
        self._list_canvas_window = self._list_canvas.create_window(
            (0, 0),
            window=self._list_container,
            anchor="nw",
        )

        self._list_container.bind(
            "<Configure>",
            lambda event: self._list_canvas.configure(
                scrollregion=self._list_canvas.bbox("all")
            ),
        )

        self._list_canvas.bind(
            "<Configure>",
            lambda event: self._list_canvas.itemconfigure(
                self._list_canvas_window,
                width=event.width,
            ),
        )

        self._list_container.bindtags((self._mousewheel_tag, *self._list_container.bindtags(),))
        self._list_canvas.bindtags((self._mousewheel_tag, *self._list_canvas.bindtags(),))

        # Selection controls
        self._controls = ttk.Frame(container)

        select_all = ttk.Button(
            self._controls,
            text="Select All",
            command=self.select_all,
            bootstyle="link",
        )

        clear_all = ttk.Button(
            self._controls,
            text="Clear",
            command=self.clear,
            bootstyle="link",
        )

        select_all.pack(side="left")
        clear_all.pack(side="right")

        self._update_controls_visibility()
        self._build_checkbox_list()
        self._update_list_height()
        self._position_popup()

        self._popup.deiconify()
        self._popup.lift()
        self._popup.focus_force()

        self.winfo_toplevel().bind_class(self._mousewheel_tag, "<MouseWheel>", self._mousewheel,)
        self.winfo_toplevel().bind_class(self._mousewheel_tag, "<Button-4>", self._mousewheel,)
        self.winfo_toplevel().bind_class(self._mousewheel_tag, "<Button-5>", self._mousewheel,)
        self.winfo_toplevel().bind_all("<Escape>", self._close_popup, add="+",)
        self._outside_click_binding = self.winfo_toplevel().bind("<Button-1>", self._outside_click, add="+",)

    def _close_popup(self, event=None):
        if self._outside_click_binding is not None:
            self.winfo_toplevel().unbind("<Button-1>", self._outside_click_binding,)
            self._outside_click_binding = None

        if self._popup is not None:
            try:
                self._popup.destroy()
            except tk.TclError:
                pass

        self._popup = None
        self._search_var = None
        self._checkbox_vars.clear()
        self._checkbox_widgets.clear()

    def _position_popup(self):
        self._popup.update_idletasks()

        x = self._display.winfo_rootx()
        y = self._display.winfo_rooty() + self._display.winfo_height()

        width = self._display.winfo_width()

        # Let the popup return to its natural requested height.
        self._popup.geometry("")
        self._popup.update_idletasks()
        height = self._popup.winfo_reqheight()

        self._popup.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def _update_list_height(self):
        self._list_container.update_idletasks()
        content_height = sum(
            checkbox.winfo_reqheight()
            for checkbox in self._checkbox_widgets.values()
            if checkbox.winfo_ismapped()
        )

        self._list_canvas.configure(
            height=max(1, min(content_height, self._max_height))
        )

        self._list_canvas.yview_moveto(0)

    def _update_controls_visibility(self):
        if self._values:
            self._controls.pack(fill="x", pady=(5, 0))
        else:
            self._controls.pack_forget()

    # ------------------------------------------------------------------
    # Checkbox list
    # ------------------------------------------------------------------

    def _build_checkbox_list(self):
        for widget in self._list_container.winfo_children():
            widget.destroy()

        self._checkbox_vars.clear()
        self._checkbox_widgets.clear()

        for value in self._values:
            variable = tk.BooleanVar(value=value in self._selected)
            checkbox = ttk.Checkbutton(
                self._list_container,
                text=value,
                variable=variable,
                command=lambda v=value: self._selection_changed(v),
            )

            checkbox.bindtags((self._mousewheel_tag, *checkbox.bindtags(),))

            checkbox.pack(fill="x", anchor="w",)
            self._checkbox_vars[value] = variable
            self._checkbox_widgets[value] = checkbox

        self._apply_filter()

    def _selection_changed(self, value):
        if self._checkbox_vars[value].get():
            self._selected.add(value)
        else:
            self._selected.discard(value)

        self._update_display()
        self._notify()

    def _update_checkboxes(self):
        for value, variable in self._checkbox_vars.items():
            variable.set(value in self._selected)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _filter_changed(self, *args):
        self._apply_filter()

    def _apply_filter(self):
        search_text = (
            "" if self._search_var is None
            else self._search_var.get().lower()
        )

        for value, checkbox in self._checkbox_widgets.items():
            if search_text in value.lower():
                checkbox.pack(fill="x", anchor="w")
            else:
                checkbox.pack_forget()

        # Let the list container recalculate its requested size.
        self._list_container.update_idletasks()

        # Recalculate the canvas scroll region explicitly.
        self._list_canvas.configure(
            scrollregion=self._list_canvas.bbox("all")
        )

        # Resize the viewport to the visible items.
        self._update_list_height()

        # Always return to the top after filtering.
        self._list_canvas.yview_moveto(0)

        self._popup.update_idletasks()
        self._position_popup()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _update_display(self):
        selected = self.get()

        if not selected:
            text = "Select..."
        elif len(selected) == 1:
            text = selected[0]
        else:
            text = f"{len(selected)} selected"

        self._display_text.configure(
            text=text,
        )

    # ------------------------------------------------------------------
    # Callback
    # ------------------------------------------------------------------

    def _notify(self):
        if self._command is not None:
            self._command(self.get())

# endregion

# region(event_handlers)

    # ------------------------------------------------------------------
    # Popup focus handling
    # ------------------------------------------------------------------

    def _outside_click(self, event):
        """Close the popup when clicking outside it."""

        if self._popup is None:
            return

        x = event.x_root
        y = event.y_root
        popup_x = self._popup.winfo_rootx()
        popup_y = self._popup.winfo_rooty()
        popup_right = popup_x + self._popup.winfo_width()
        popup_bottom = popup_y + self._popup.winfo_height()

        if not (
            popup_x <= x <= popup_right
            and popup_y <= y <= popup_bottom
        ):
            self._close_popup()

    def _mousewheel(self, event):
        if event.num == 4:
            # Linux: wheel up
            self._list_canvas.yview_scroll(-1, "units")

        elif event.num == 5:
            # Linux: wheel down
            self._list_canvas.yview_scroll(1, "units")

        else:
            # Windows / macOS
            self._list_canvas.yview_scroll(
                int(-1 * event.delta / 120),
                "units",
            )

        return "break"

# endregion

