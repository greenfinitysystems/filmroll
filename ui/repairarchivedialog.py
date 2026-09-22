# region(python_imports)

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
import ttkbootstrap as tb

# endregion

# region(project_imports)

from ui.dialog import Dialog
from ui.messagebox import MessageBox

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class RepairArchiveDialog(Dialog):
    def __init__(self, parent: tk.Tk, current_path: str):
        self._path = tk.StringVar()
        self._path.set(current_path)

        self._delete_missing = tk.IntVar()
        self._delete_missing.set(0)

        super().__init__(parent=parent, height=240, title="Repair Archive")

    def body(self) -> None:
        main = tb.Frame(self, padding=(25, 40))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)

        browse_pad = (6,3)

        tb.Label(main, text="New Location"
        ).grid(row=0, column=0, sticky="w", pady=4)

        tb.Entry(main, textvariable=self._path,
        ).grid(row=0, column=1, sticky="ew", padx=(6,6), pady=(0,6))

        tb.Button(
            main,
            text="Browse…",
            width=8,
            padding=browse_pad,
            command=self.browse_path
        ).grid(row=0, column=2, padx=(6,4), pady=(0,6))

        tb.Checkbutton(main, text="Unlink missing files from Archve", variable=self._delete_missing
        ).grid(row=1, column=1, sticky="w", padx=(6,0), pady=(6,6), ipady=2)

        super().body()

    def browse_path(self) -> None:
        dir = filedialog.askdirectory(title="Select Folder", initialdir=self._path.get())
        if dir: self._path.set(dir)

    def validate(self) -> bool:
        if (self._path.get() == "" or 
            not Path(self._path.get()).exists() or 
            not Path(self._path.get()).is_dir()):
            MessageBox.showerror("Error", "Please provide a valid folder.", parent=self)
            return False

        return True
