# region(python_imports)

import logging
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import ScrolledText

# endregion

# region(project_imports)

from core.config import Config
from core.util import IptcInfo
from ui.tageditor import TagEditor
from ui.dialog import Dialog

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class IptcDialog(Dialog):
    def __init__(self, parent: tk.Tk, iptc: IptcInfo):
        self._caption = tk.StringVar(value=iptc.caption)
        self._usernote = tk.StringVar(value=iptc.comment)
        self._author =  tk.StringVar(value=iptc.author)
        self._copyright =  tk.StringVar(value=iptc.copyright)
        self._rating = tk.IntVar(value=iptc.rating)
        self._tags = list(iptc.tags)

        self._iptcinfo = None

        super().__init__(parent=parent, ok="Save", width=650, height=600, title="Image Properties")

    def body(self) -> None:
        cfg = Config()

        # our main grid
        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        
        part1 = tb.Frame(main, padding=(5, 5))
        part1.grid(row=0, column=0, sticky="ew")
        part1.columnconfigure(0, weight=0)
        part1.columnconfigure(1, weight=1)

        row = 0

        label = tb.Label(part1, text="Caption" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(part1, textvariable=self._caption,
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))

        row += 1

        label = tb.Label(part1, text="Author" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(part1, textvariable=self._author,
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))

        row += 1
        
        label = tb.Label(part1, text="Copyright" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(part1, textvariable=self._copyright,
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))

        part2 = tb.Frame(main, padding=(5, 5))
        part2.grid(row=1, column=0, sticky="ew")
        part2.columnconfigure(0, weight=1)

        row = 0

        label = tb.Label(part2, text="Comments" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)

        row += 1

        self._st = ScrolledText(part2, width=50, height=10)
        self._st.grid(row=row, column=0, sticky="ew", padx=5, pady=5)

        row += 1
        
        label = tb.Label(part2, text="Tags" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=(10,0))

        row += 1

        self._tageditor = TagEditor(part2, values=cfg.tagstore.get(), tags=self._tags, max_height=40, allowcreate=True)
        self._tageditor.grid(row=row, column=0, sticky="ew", pady=0)
        self._st.insert('1.0', self._usernote.get())

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()
        self._st.focus_set()

    def validate(self) -> bool:
        self._usernote.set(self._st.get('1.0', 'end-1c'))
        self._iptcinfo = IptcInfo(
            author = self._author.get(),
            copyright= self._copyright.get(),
            caption= self._caption.get(),
            comment= self._usernote.get(),
            rating = int(self._rating.get()),
            tags = tuple(self._tageditor.get()),
        )

        return True

class BatchIptcDialog(Dialog):
    def __init__(self, parent: tk.Tk, tags: list, title_suffix: str=None):
        self._cur_tags = tags
        self._author = tk.StringVar(value="")
        self._copyright = tk.StringVar(value="")
        self._overwrite = tk.IntVar(value=0)
        super().__init__(parent=parent, ok="Apply", width=600, height=550, title=f"Image Properties {title_suffix or ''}")

    def body(self) -> None:
        cfg = Config()

        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        part1 = tb.Frame(main, padding=(5, 5))
        part1.grid(row=0, column=0, sticky="ew")
        part1.columnconfigure(0, weight=0)
        part1.columnconfigure(1, weight=1)

        row = 0

        label = tb.Label(part1, text="Author" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(part1, textvariable=self._author,
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))

        row += 1
        
        label = tb.Label(part1, text="Copyright" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(part1, textvariable=self._copyright,
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))

        row += 1

        tb.Checkbutton(part1, text="Overwrite Existing Values", variable=self._overwrite,
        ).grid(row=row, column=1, sticky="ew", padx=(6,0), pady=(16,6), ipady=2, columnspan=2)

        # ---

        part2 = tb.Frame(main, padding=(5, 5))
        part2.grid(row=1, column=0, sticky="ew")
        part2.columnconfigure(0, weight=1)

        row = 0

        label = tb.Label(part2, text="Remove Tags" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)

        row += 1

        self._del_te = TagEditor(part2, values=self._cur_tags, tags=[], max_height=60, allowcreate=False)
        self._del_te.grid(row=row, column=0, sticky="ew", padx=5, pady=5)

        row += 1

        label = tb.Label(part2, text="Add Tags" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=(10,0))

        row += 1
        
        self._add_te = TagEditor(part2, values=cfg.tagstore.get(), tags=[], max_height=60)
        self._add_te.grid(row=row, column=0, sticky="ew", padx=5, pady=5)

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()

