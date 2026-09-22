# region(python_imports)

import logging
import tkinter as tk
import ttkbootstrap as tb

# endregion

# region(project_imports)

from ui.dialog import Dialog
from ui.multiselectdropdown import MultiSelectDropdown

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class SearchDialog(Dialog):
    def __init__(self, parent: tk.Tk, filters: list):
        self._filters = filters
        self._variables = []
        super().__init__(parent=parent, ok="Apply", height=400, title="Search")

    def body(self) -> None:
        # our main grid
        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        self._variables.clear()

        # for all the filter sets, create set of individual dropdown and label
        # also create an array of variables for the dropdowns
        for i, f in enumerate(self._filters):
            tb.Label(main, text=f.label).grid(row=i, column=0, sticky="w", pady=10)
            dropdown = MultiSelectDropdown(main, values=f.values, searchable=False,)
            dropdown.grid(row=i, column=1, sticky="ew", padx=(5,5), pady=(10,0), ipady=2)
            self._variables.insert(i, dropdown)
            if len(f.selected_values) > 0:
                dropdown.set(f.selected_values)

        # the base class body creates the rest of the form with Ok, cancel Buttons
        super().body()

    def validate(self) -> bool:
        for i, f in enumerate(self._filters):
            f.selected_values.clear()
            f.selected_values.extend(self._variables[i].get())
        return True
