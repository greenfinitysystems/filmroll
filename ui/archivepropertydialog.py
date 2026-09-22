# region(python_imports)

import logging
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import ScrolledText

# endregion

# region(project_imports)

from ui.dialog import Dialog

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class ArchivePropertyDialog(Dialog):
    def __init__(self, parent: tk.Tk, name: str, desc: str):
        self._arname = tk.StringVar(value=(name or ""))
        self._ardesc = tk.StringVar(value=(desc or ""))
        super().__init__(parent=parent, ok="Save", height=400, title="Archive Properties")

    def body(self) -> None:
        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        label = tb.Label(main, text="Title" )
        label.grid(row=0, column=0, sticky="w", padx=5, pady=0)
        name = tb.Entry(main, textvariable=self._arname)
        name.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        label = tb.Label(main, text="Description" )
        label.grid(row=2, column=0, sticky="w", padx=5, pady=0)
        self._st = ScrolledText(main, width=50, height=10)
        self._st.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        self._st.insert('end', self._ardesc.get())

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()

    def validate(self) -> bool:
        self._ardesc.set( self._st.get('1.0', 'end-1c'))
        return True
