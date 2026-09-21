# region(python_imports)

import tkinter as tk
import ttkbootstrap as ttk

# endregion

# region(project_imports)

# There is nothing here

# endregion

# region(globals)

# There is nothing here

# endregion

class TagEditor(ttk.Frame):
    """
    Reusable tag editor.

    Parameters
    ----------
    parent:
        Parent tkinter widget.

    values:
        Iterable of available tags used for suggestions.

    tags:
        Iterable of currently selected tags.

    command:
        Optional callback called whenever the selected tags change.
        Receives the current tags as a list.
    """

# region(class_methods)

    def __init__(
        self,
        parent,
        values=None,
        tags=None,
        command=None,
        width=40,
        max_height=100,
        allowcreate=True,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self._values = []
        self._tags = []
        self._command = command
        self._width = width
        self._max_height = max_height
        self._allowcreate = allowcreate

        self._popup = None
        self._listbox = None

        # Tag wrapping state
        self._wrapping = False
        self._wrap_after_id = None
        self._last_wrap_width = 0

        self._style = ttk.Style()

        self._build()

        self.values(values or [])
        self.set(tags or [])

# endregion

# region(methods)

    # Public API

    def get(self):
        """Return the currently selected tags."""
        return list(self._tags)

    def set(self, tags):
        """Replace the currently selected tags."""
        seen = set()
        self._tags = []

        for tag in tags or []:
            tag = self._normalize(tag)

            if tag and tag not in seen:
                seen.add(tag)
                self._tags.append(tag)

        self._update_tags()
        self._notify()

    def clear(self):
        """Remove all selected tags."""
        self._tags.clear()
        self._update_tags()
        self._notify()

    def values(self, values=None):
        """
        Get or replace the available suggestion tags.

        values()       -> current values
        values(new)    -> replace available values
        """
        if values is None:
            return list(self._values)

        seen = set()
        self._values = []

        for value in values:
            value = self._normalize(value)

            if value and value not in seen:
                seen.add(value)
                self._values.append(value)

        self._update_suggestions()

# endregion

# region(private_methods)

    # Construction

    def _build(self):
        self._tag_frame = tk.Frame(
            self,
            bg="white",
            highlightthickness=1,
            highlightbackground="#b8b8b8",
            highlightcolor="#808080",
        )
        self._tag_frame.pack(fill="x")

        # The tag area is a bounded, vertically scrollable viewport.
        # The Entry remains outside the viewport and is therefore always visible.
        self._tags_container = tk.Frame(
            self._tag_frame,
            bg="white",
        )
        self._tags_container.pack(
            fill="x",
            padx=5,
            pady=(4, 2),
        )

        self._tags_canvas = tk.Canvas(
            self._tags_container,
            bg="white",
            highlightthickness=0,
            borderwidth=0,
        )

        self._tags_canvas.pack(
            side="left",
            fill="x",
            expand=True,
        )

        self._tags_scrollbar = ttk.Scrollbar(
            self._tags_container,
            orient="vertical",
            command=self._tags_canvas.yview,
        )

        self._tags_frame = tk.Frame(
            self._tags_canvas,
            bg="white",
        )

        self._tags_window = self._tags_canvas.create_window(
            (0, 0),
            window=self._tags_frame,
            anchor="nw",
        )

        self._tags_frame.bind(
            "<Configure>",
            self._tags_frame_configure,
        )
        self._tags_canvas.bind(
            "<Configure>",
            self._tags_canvas_configure,
        )

        self._tags_canvas.configure(
            yscrollcommand=self._tags_scrollbar.set,
        )
        self._tags_canvas.bind("<MouseWheel>", self._tags_mousewheel)
        self._tags_canvas.bind("<Button-4>", self._tags_mousewheel)
        self._tags_canvas.bind("<Button-5>", self._tags_mousewheel)
        self._tags_frame.bind("<MouseWheel>", self._tags_mousewheel)
        self._tags_frame.bind("<Button-4>", self._tags_mousewheel)
        self._tags_frame.bind("<Button-5>", self._tags_mousewheel)

        # Keep the input field on its own row so it is always visible.
        self._style.configure(
            "TagEditor.TEntry",
            borderwidth=1,
            relief="solid",
        )

        self._entry = ttk.Entry(
            self._tag_frame,
            width=self._width,
            style="TagEditor.TEntry",
        )

        self._entry.pack(
            fill="x",
            padx=5,
            pady=(2, 5),
        )

        self._entry.bind(
            "<KeyRelease>",
            self._entry_changed,
        )
        self._entry.bind(
            "<Return>",
            self._return_pressed,
        )
        self._entry.bind(
            "<Escape>",
            self._escape_pressed,
        )
        self._entry.bind(
            "<Down>",
            self._down_pressed,
        )
        self._entry.bind(
            "<Up>",
            self._up_pressed,
        )
        self._entry.bind(
            "<KP_Down>",
            self._down_pressed,
        )
        self._entry.bind(
            "<KP_Up>",
            self._up_pressed,
        )
        self._entry.bind(
            "<KP_Enter>",
            self._return_pressed,
        )
        self._entry.bind(
            "<FocusOut>",
            self._focus_out,
        )

        self._update_tags()

    # Tags

    def _update_tags(self):
        """Schedule the tag pills to be wrapped into rows."""
        if self._wrap_after_id is not None:
            try:
                self.after_cancel(self._wrap_after_id)
            except tk.TclError:
                pass

        self._wrap_after_id = self.after_idle(self._wrap_tags)

    def _tags_frame_configure(self, event=None):
        if self._wrapping:
            return

        width = self._tags_frame.winfo_width()

        if width <= 1 or width == self._last_wrap_width:
            return

        if self._wrap_after_id is not None:
            try:
                self.after_cancel(self._wrap_after_id)
            except tk.TclError:
                pass

        self._wrap_after_id = self.after_idle(self._wrap_tags)

    def _tags_canvas_configure(self, event=None):
        """Keep the wrapped tag frame the same width as the viewport."""
        if self._tags_canvas.winfo_width() <= 1:
            return

        self._tags_canvas.itemconfigure(
            self._tags_window,
            width=self._tags_canvas.winfo_width(),
        )

        if self._wrap_after_id is not None:
            try:
                self.after_cancel(self._wrap_after_id)
            except tk.TclError:
                pass

        self._wrap_after_id = self.after_idle(self._wrap_tags)

    def _set_tag_scrollbar(self, visible):
        """Show or hide the tag-area scrollbar."""
        if visible:
            if not self._tags_scrollbar.winfo_ismapped():
                self._tags_scrollbar.pack(
                    side="right",
                    fill="y",
                )
        else:
            if self._tags_scrollbar.winfo_ismapped():
                self._tags_scrollbar.pack_forget()

    def _wrap_tags(self):
        """Arrange tag pills into rows and constrain the tag area height."""
        self._wrap_after_id = None

        if self._wrapping:
            return

        self._wrapping = True

        try:
            for widget in self._tags_frame.winfo_children():
                widget.destroy()

            self._set_tag_scrollbar(False)
            self.update_idletasks()

            available_width = self._tags_canvas.winfo_width()

            if available_width <= 1:
                return

            if not self._tags:
                self._tags_canvas.configure(height=1,
                    scrollregion=(0, 0, available_width, 1),)
                self._tags_canvas.yview_moveto(0)
                return

            self._last_wrap_width = available_width

            gap = 4
            row = None
            used_width = 0
            has_tags = False

            for tag in self._tags:
                if row is None:
                    row = tk.Frame(
                        self._tags_frame,
                        bg="white",
                    )
                    row.pack(fill="x")
                    row.bind("<MouseWheel>", self._tags_mousewheel)
                    row.bind("<Button-4>", self._tags_mousewheel)
                    row.bind("<Button-5>", self._tags_mousewheel)

                pill = self._create_tag(row, tag)
                self.update_idletasks()
                pill_width = pill.winfo_reqwidth()

                if has_tags and used_width + pill_width > available_width:
                    pill.destroy()

                    row = tk.Frame(
                        self._tags_frame,
                        bg="white",
                    )
                    row.pack(fill="x")
                    row.bind("<MouseWheel>", self._tags_mousewheel)
                    row.bind("<Button-4>", self._tags_mousewheel)
                    row.bind("<Button-5>", self._tags_mousewheel)

                    used_width = 0
                    has_tags = False

                    pill = self._create_tag(row, tag)
                    self.update_idletasks()
                    pill_width = pill.winfo_reqwidth()

                used_width += pill_width + gap
                has_tags = True

            self.update_idletasks()

            required_height = self._tags_frame.winfo_reqheight()
            max_height = max(1, int(self._max_height))

            if required_height > max_height:
                # The scrollbar reduces the viewport width, so re-wrap once
                # using the final available width.
                self._set_tag_scrollbar(True)
                self.update_idletasks()

                available_width = self._tags_canvas.winfo_width()

                for widget in self._tags_frame.winfo_children():
                    widget.destroy()

                row = None
                used_width = 0
                has_tags = False

                for tag in self._tags:
                    if row is None:
                        row = tk.Frame(
                            self._tags_frame,
                            bg="white",
                        )
                        row.pack(fill="x")
                    row.bind("<MouseWheel>", self._tags_mousewheel)
                    row.bind("<Button-4>", self._tags_mousewheel)
                    row.bind("<Button-5>", self._tags_mousewheel)

                    pill = self._create_tag(row, tag)
                    self.update_idletasks()
                    pill_width = pill.winfo_reqwidth()

                    if has_tags and used_width + pill_width > available_width:
                        pill.destroy()

                        row = tk.Frame(
                            self._tags_frame,
                            bg="white",
                        )
                        row.pack(fill="x")
                        row.bind("<MouseWheel>", self._tags_mousewheel)
                        row.bind("<Button-4>", self._tags_mousewheel)
                        row.bind("<Button-5>", self._tags_mousewheel)

                        used_width = 0
                        has_tags = False

                        pill = self._create_tag(row, tag)
                        self.update_idletasks()
                        pill_width = pill.winfo_reqwidth()

                    used_width += pill_width + gap
                    has_tags = True

                self.update_idletasks()
                required_height = self._tags_frame.winfo_reqheight()

            viewport_height = min(required_height, max_height)

            self._tags_canvas.configure(
                height=viewport_height,
                scrollregion=(0, 0, self._tags_frame.winfo_reqwidth(), required_height),
            )

            if required_height <= max_height:
                self._tags_canvas.yview_moveto(0)

        finally:
            self._wrapping = False

    # Tag-area scrolling

    def _tags_mousewheel(self, event):
        """Scroll the tag area with the mouse wheel."""
        if self._tags_frame.winfo_reqheight() <= self._max_height:
            return

        if event.num == 4:
            self._tags_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._tags_canvas.yview_scroll(1, "units")
        elif event.delta:
            self._tags_canvas.yview_scroll(
                int(-event.delta / 120),
                "units",
            )

        return "break"

    def _create_tag(self, parent, tag):
        """Create one rounded tag pill and return it."""

        # Measure the tag text using the same basic Tk font metrics
        # used by the final Canvas text.
        measure = tk.Label(
            parent,
            text=tag,
            padx=6,
            pady=2,
        )
        measure.update_idletasks()

        text_width = measure.winfo_reqwidth()
        height = measure.winfo_reqheight()

        measure.destroy()

        # Space reserved for the remove "×".
        remove_width = 20
        width = text_width + remove_width

        radius = min(height // 2, 10)

        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=parent.cget("bg"),
            highlightthickness=0,
            borderwidth=0,
            cursor="arrow",
        )

        canvas.pack(
            side="left",
            padx=(0, 4),
            pady=1,
        )

        # Tags from the global dictionary use the normal neutral pill.
        # Tags created locally for this archive/image get a distinct tint.
        pill_bg = "#e6e6e6" if tag in self._values else "#d9edf7"

        # Draw a rounded rectangle from four simple canvas shapes.
        canvas.create_arc(
            0,
            0,
            radius * 2,
            height,
            start=90,
            extent=180,
            fill=pill_bg,
            outline=pill_bg,
        )

        canvas.create_arc(
            width - radius * 2,
            0,
            width,
            height,
            start=270,
            extent=180,
            fill=pill_bg,
            outline=pill_bg,
        )

        canvas.create_rectangle(
            radius,
            0,
            width - radius,
            height,
            fill=pill_bg,
            outline=pill_bg,
        )

        canvas.create_rectangle(
            0,
            radius,
            width,
            height - radius,
            fill=pill_bg,
            outline=pill_bg,
        )

        canvas.create_text(
            6,
            height // 2,
            text=tag,
            anchor="w",
            fill="#333333",
        )

        canvas.create_text(
            width - remove_width // 2,
            height // 2,
            text="×",
            anchor="center",
            fill="#666666",
        )

        canvas.bind(
            "<Button-1>",
            lambda event, value=tag: (
                self._remove_tag(value)
                if event.x >= width - remove_width
                else None
            ),
        )

        # Mouse-wheel events can land on the pill Canvas rather than the
        # containing tag frame. Forward them to the tag-area scroller.
        canvas.bind("<MouseWheel>", self._tags_mousewheel)
        canvas.bind("<Button-4>", self._tags_mousewheel)
        canvas.bind("<Button-5>", self._tags_mousewheel)

        return canvas

    def _remove_tag(self, tag):
        if tag not in self._tags:
            return

        self._tags.remove(tag)

        self._update_tags()
        self._notify()

        self._entry.focus_set()

    # Input

    def _entry_changed(self, event=None):
        # Arrow keys navigate the suggestion list.  They do not change the
        # Entry text, so do not rebuild/reset the suggestions on KeyRelease.
        if event is not None and event.keysym in ("Up", "Down"):
            return

        self._update_suggestions()

    def _return_pressed(self, event=None):
        text = self._normalize(self._entry.get())

        if not text:
            return "break"

        selected = self._get_highlighted_tag()

        if selected:
            self._add_tag(selected)
        else:
            self._add_tag(text)

        return "break"

    def _add_tag(self, tag):
        tag = self._normalize(tag)

        if tag not in self._values and not self._allowcreate:
            return

        if not tag or "|" in tag:
            return

        if tag not in self._tags:
            self._tags.append(tag)
            self._update_tags()
            self._notify()

        self._entry.delete(0, "end")
        self._update_suggestions()
        self._entry.focus_set()

    def _update_suggestions(self):
        text = self._normalize(self._entry.get())

        if not text:
            self._close_popup()
            return

        matches = [
            value
            for value in self._values
            if text in value.lower()
            and value not in self._tags
        ]

        if not matches:
            self._close_popup()
            return

        self._open_popup(matches)

    def _open_popup(self, values):
        if self._popup is None:
            self._popup = tk.Toplevel(self)
            self._popup.overrideredirect(True)

            self._popup.transient(self.winfo_toplevel())

            self._listbox = tk.Listbox(
                self._popup,
                activestyle="none",
                borderwidth=0,
                highlightthickness=1,
                highlightcolor="#b8b8b8",
                selectmode="browse",
            )

            self._listbox.pack(
                fill="both",
                expand=True,
            )

            # Handle mouse selection before the Listbox class binding.
            # This keeps the Entry in control of focus and makes selection
            # behave consistently on Windows and Linux.
            self._listbox.bind(
                "<Button-1>",
                self._suggestion_clicked,
            )

            self._listbox.bind(
                "<Return>",
                self._listbox_return,
            )
            self._listbox.bind(
                "<KP_Enter>",
                self._listbox_return,
            )
            self._listbox.bind(
                "<Down>",
                self._down_pressed,
            )
            self._listbox.bind(
                "<Up>",
                self._up_pressed,
            )
            self._listbox.bind(
                "<KP_Down>",
                self._down_pressed,
            )
            self._listbox.bind(
                "<KP_Up>",
                self._up_pressed,
            )

            self._listbox.bind(
                "<Escape>",
                self._escape_pressed,
            )

        self._listbox.delete(0, "end")

        for value in values:
            self._listbox.insert("end", value)

        self._position_popup()

        if self._listbox.size():
            self._listbox.selection_clear(0, "end")
            self._listbox.selection_set(0)
            self._listbox.activate(0)

        self._popup.deiconify()
        self._popup.lift()

        # Keep keyboard focus in the Entry.  The Listbox is only the visual
        # selection surface; Up/Down are handled by the Entry bindings.
        self._entry.focus_set()

    def _position_popup(self):
        if self._popup is None:
            return

        self._popup.update_idletasks()

        x = self._entry.winfo_rootx()
        y = self._entry.winfo_rooty() + self._entry.winfo_height()

        width = self._entry.winfo_width()
        height = min(
            self._listbox.winfo_reqheight(),
            150,
        )

        self._popup.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def _close_popup(self):
        if self._popup is not None:
            try:
                self._popup.destroy()
            except tk.TclError:
                pass

        self._popup = None
        self._listbox = None

    # Keyboard navigation

    def _down_pressed(self, event=None):
        if self._listbox is None:
            return

        size = self._listbox.size()

        if not size:
            return

        current = self._listbox.curselection()

        index = current[0] if current else -1
        index = min(index + 1, size - 1)

        self._listbox.selection_clear(0, "end")
        self._listbox.selection_set(index)
        self._listbox.activate(index)
        self._listbox.see(index)

        return "break"

    def _up_pressed(self, event=None):
        if self._listbox is None:
            return

        size = self._listbox.size()

        if not size:
            return

        current = self._listbox.curselection()

        index = current[0] if current else 0
        index = max(index - 1, 0)

        self._listbox.selection_clear(0, "end")
        self._listbox.selection_set(index)
        self._listbox.activate(index)
        self._listbox.see(index)

        return "break"

    def _get_highlighted_tag(self):
        if self._listbox is None:
            return None

        selection = self._listbox.curselection()

        if not selection:
            return None

        return self._listbox.get(selection[0])

    def _listbox_return(self, event=None):
        tag = self._get_highlighted_tag()

        if tag:
            self._add_tag(tag)

        return "break"

    def _suggestion_clicked(self, event=None):
        if self._listbox is None:
            return "break"

        # Do the selection ourselves rather than relying on the Listbox
        # class binding.  The latter transfers focus to the popup on some
        # platforms, which can make the editor appear read-only on Windows
        # and can prevent the selection from completing on Linux.
        index = self._listbox.nearest(event.y)

        bbox = self._listbox.bbox(index)
        if not bbox:
            return "break"

        y = bbox[1]
        height = bbox[3]

        if event.y < y or event.y >= y + height:
            return "break"

        self._listbox.selection_clear(0, "end")
        self._listbox.selection_set(index)
        self._listbox.activate(index)

        tag = self._listbox.get(index)
        if tag:
            self._add_tag(tag)

        return "break"

    def _escape_pressed(self, event=None):
        self._close_popup()
        self._entry.focus_set()
        return "break"

    def _focus_out(self, event=None):
        # Give mouse clicks on the popup a chance to occur
        # before closing it.
        self.after(100, self._check_popup_focus)

    def _check_popup_focus(self):
        if self._popup is None:
            return

        try:
            focused = self.focus_get()
        except tk.TclError:
            return

        if focused not in (
            self._entry,
            self._listbox,
        ):
            self._close_popup()

    # Helpers

    @staticmethod
    def _normalize(value):
        if not isinstance(value, str):
            return ""

        return value.strip().lower()

    def _notify(self):
        if self._command is not None:
            self._command(self.get())

# endregion
