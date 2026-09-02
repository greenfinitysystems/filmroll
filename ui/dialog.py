# region(python_imports)

import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from PIL import Image, ImageTk
import ttkbootstrap as tb

# endregion

# region(project_imports)

from core.config import Config

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class Dialog(tk.Toplevel):

    def __init__(self, parent: tk.Tk, width: int =440, height: int =320, ok: str ="OK", cancel: str ="Cancel", title: str | None =None):
        super().__init__(parent)

        cfg = Config()
        self.title(title if title else cfg.appname)
        self.ok = ok
        self.cancel = cancel
        self.parent = parent
        self.resizable(False, False)
        self.result = None
        
        x = self.parent.winfo_rootx() + self.parent.winfo_width()//2 - width//2
        y = self.parent.winfo_rooty() + self.parent.winfo_height()//2 - height//2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.columnconfigure(0, weight=1)

        self.body()
        self.withdraw()       

    def body(self) -> None:
        box = tk.Frame(self)
        box.grid(row=1, column=0, sticky="nsew", padx=22, pady=10)

        button_pad = (6,3)

        tb.Button(box, text=self.cancel, width=10, padding=button_pad, command=self.on_cancel, bootstyle="secondary"
        ).pack(side=tk.RIGHT, padx=8, pady=8)

        tb.Button(box, text=self.ok, width=10, padding=button_pad, command=self.on_ok, bootstyle="primary"
        ).pack(side=tk.RIGHT, padx=16, pady=5)

        self.bind("<Key>", self.on_key)

    def on_key(self, event: any) -> None:
        if event.keysym == "Escape":
            self.on_cancel()
            return

        ctrl = (event.state & 0x0004) != 0
        shift = (event.state & 0x0001) != 0

        if ctrl and event.keysym in ["Return", "KP_Enter"]:
            self.on_ok()
            return

    def on_ok(self, event: any =None) -> None:
        if not self.validate():
            return

        self.result = True
        self.destroy_dialog()

    def on_cancel(self, event: any =None) -> None:
        self.result = False
        self.destroy_dialog()

    def destroy_dialog(self) -> None:
        if self.parent:
            self.parent.focus_set()
        self.grab_release()
        self.destroy()

    def show(self) -> None:
        self.deiconify()
        self.grab_set()
        self.wait_window(self)
        return self.result

    def validate(self) -> bool:
        return True

class AboutDialog(Dialog):

    def __init__(self, parent: tk.Tk):
        cfg = Config()
        super().__init__(parent=parent, width=460, height=380, title=f"About {cfg.appname}")

    def body(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.columnconfigure(0, weight=1)
        frame.grid()

        cfg = Config()

        logo_path = cfg.asset("logo.png")
        img = Image.open(logo_path)
        w, h = img.size
        nw = int(w * (48/h))
        img = img.resize((nw, 48))

        self.logo = ImageTk.PhotoImage(img)

        logo_label = ttk.Label(
            frame,
            image=self.logo,
            justify="center",
        ).grid(row=0, column=0, pady=(5,0))

        text_frame = ttk.LabelFrame(frame, text=cfg.version, padding=2)
        text_frame.grid(row=1, column=0, sticky="ew", pady=(10.5), padx=5)

        ttk.Label(
            text_frame,
            text=cfg.about,
            wraplength=401,
            justify="center"
        ).grid(row=0, column=0, pady=(0,0))

        ttk.Button(
            frame,
            text="OK",
            width=12,
            command=self.destroy
        ).grid(row=3, column=0, pady=(15,15))

class RepairArchiveDialog(Dialog):
    def __init__(self, parent: tk.Tk, current_path: str):
        self._apath = tk.StringVar()
        self._apath.set(current_path)

        self._delete_missing = tk.IntVar()
        self._delete_missing.set(0)

        super().__init__(parent=parent, height=240, title="Move Archive")

    def body(self) -> None:
        main = tk.Frame(self, padx=25, pady=40)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)

        browse_pad = (6,3)

        tb.Label(main, text="New Location"
        ).grid(row=0, column=0, sticky="w", pady=4)

        tb.Entry(main, textvariable=self._apath,
        ).grid(row=0, column=1, sticky="ew", padx=(6,6), pady=(0,6))

        tb.Button(
            main,
            text="Browse…",
            width=8,
            padding=browse_pad,
            command=self.browse_path
        ).grid(row=0, column=2, padx=(6,4), pady=(0,6))

        var = tk.IntVar()

        tb.Checkbutton(main, text="Unlink missing files from Archve", variable=self._delete_missing
        ).grid(row=1, column=1, sticky="w", padx=(6,0), pady=(6,6), ipady=2)

        super().body()

    def browse_path(self) -> None:
        dir = filedialog.askdirectory(title="Select Folder", initialdir=self._apath.get())
        if dir: self._apath.set(dir)

    def validate(self) -> bool:
        if (self._apath.get() == "" or 
            not Path(self._apath.get()).exists() or 
            not Path(self._apath.get()).is_dir()):
            messagebox.showerror("Error", "Please provide a valid folder.")
            return False

        return True

class FilterDialog(Dialog):
    def __init__(self, parent: tk.Tk, filters: list):
        self._filters = filters
        self._variables = []
        super().__init__(parent=parent, ok="Apply", height=440, title="Apply Filter")

    def body(self) -> None:
        # our main grid
        main = tk.Frame(self, padx=25, pady=20)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)

        # for all the filter sets, create set of individual dropdown and label
        # add a generic Any + Label name (like Any Camera) which represnts no selection
        # also create an array of tk.StringVar for the dropdowns
        for i, f in enumerate(self._filters):
            # f.values.insert(0, "Any " + f.label)
            var = tk.StringVar()
            self._variables.insert(i, var)

            # create the GUI widgets
            label = tb.Label(main, text=f.label )
            label.grid(row=i, column=0, sticky="w", pady=10)
            dropdown = tb.Combobox(main, textvariable=var, values=f.values, state='readonly')
            dropdown.grid(row=i, column=1, sticky="ew", padx=(5,5), pady=(10,0), ipady=2)

            # if previous values exists set it or select the top tem (Any ...)
            if len(f.selected_values) > 0:
                dropdown.set(f.selected_values[0])
            else:
                dropdown.current(0)

        # the base class body creates the rest of the form with Ok, cancel Buttons
        super().body()

    def validate(self) -> bool:
        for i, f in enumerate(self._filters):
            f.selected_values.clear()
            text = self._variables[i].get()
            if not text.startswith("Any"):
                f.selected_values.insert(0, text)

        return True

class ArchivePropertyDialog(Dialog):
    def __init__(self, parent: tk.Tk, name: str, desc: str):
        name = "" if name is None else name
        desc = "" if desc is None else desc
        self._arname = tk.StringVar(value=name)
        self._ardesc = tk.StringVar(value=desc)
        super().__init__(parent=parent, ok="Save", height=400, title="Archive Properties")

    def body(self) -> None:
        # our main grid
        main = tk.Frame(self, padx=25, pady=20)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        label = ttk.Label(main, text="Title" )
        label.grid(row=0, column=0, sticky="w", padx=5, pady=0)
        name = ttk.Entry(main, textvariable=self._arname)
        name.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        label = ttk.Label(main, text="Description" )
        label.grid(row=2, column=0, sticky="w", padx=5, pady=0)
        self._st = scrolledtext.ScrolledText(main, width=50, height=10)
        self._st.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        self._st.insert('end', self._ardesc.get())

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()

    def validate(self) -> bool:
        self._ardesc.set( self._st.get('1.0', 'end-1c'))
        return True

class UserCommentDialog(Dialog):
    def __init__(self, parent: tk.Tk, comment):
        self._usernote = tk.StringVar(value=comment)
        super().__init__(parent=parent, ok="Save", height=350, title="Image Notes")

    def body(self) -> None:
        # our main grid
        main = tk.Frame(self, padx=25, pady=20)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        label = ttk.Label(main, text="Notes" )
        label.grid(row=2, column=0, sticky="w", padx=5, pady=0)
        self._st = scrolledtext.ScrolledText(main, width=50, height=10)
        self._st.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        self._st.insert('1.0', self._usernote.get())

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()
        self._st.focus_set()

    def validate(self) -> bool:
        self._usernote.set( self._st.get('1.0', 'end-1c'))
        return True
