# region(python_imports)

import logging
import tkinter as tk
from tkinter import colorchooser
import ttkbootstrap as tb

# endregion

# region(project_imports)

from ui.dialog import Dialog
from core.config import Config
from ui.messagebox import MessageBox

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class ConfigDialog(Dialog):
    def __init__(self, parent: tk.Tk):
        cfg = Config()

        self._gallery_color = tk.StringVar(value=cfg.gallery_color)
        self._border_color = tk.StringVar(value=cfg.border_color)
        self._caption_color = tk.StringVar(value=cfg.caption_color)
        self._preview_size = tk.StringVar(value=cfg.preview_size)
        self._border_size = tk.IntVar(value=int(cfg.border_ratio * 100))
        self._use_focal_groups = tk.IntVar(value=cfg.use_focal_groups)
        self._log_level = tk.StringVar(value=cfg.log_level)

        super().__init__(parent=parent, ok="Apply", width=450, height=400, title="Options")

    def body(self) -> None:
        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)

        browse_pad = (6,3)
        loglevel = ["error", "warning", "info", "debug"]

        row = 0

        tb.Label(main, text="Log Level"
        ).grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Combobox(main, textvariable=self._log_level, values=loglevel, state='readonly'
        ).grid(row=row, column=1, sticky="ew", padx=(6,4), pady=(0,6), ipady=0)

        row += 1

        label = tb.Label(main, text="Background Color" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(main, textvariable=self._gallery_color, state='readonly',
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))
        tb.Button(main, text="Pick…", width=8, padding=browse_pad,command=self._pick_gallery_color,
        ).grid(row=row, column=2, padx=(6,4), pady=(0,6))

        row += 1

        label = tb.Label(main, text="Preview Border Color" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(main, textvariable=self._border_color, state='readonly',
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))
        tb.Button(main, text="Pick…", width=8, padding=browse_pad, command=self._pick_border_color,
        ).grid(row=row, column=2, padx=(6,4), pady=(0,6))

        row += 1
        
        label = tb.Label(main, text="Preview Caption Color" )
        label.grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Entry(main, textvariable=self._caption_color, state='readonly',
        ).grid(row=row, column=1, sticky="ew", padx=(6,6), pady=(0,6))
        tb.Button(main, text="Pick…", width=8, padding=browse_pad, command=self._pick_caption_color,
        ).grid(row=row, column=2, padx=(6,4), pady=(0,6))

        row += 1

        tb.Label(main, text="Preview Size (px)"
        ).grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Combobox(main, textvariable=self._preview_size, values=Config().supported_preview_size, state='readonly'
        ).grid(row=row, column=1, sticky="ew", padx=(6,4), pady=(0,6), ipady=0)

        row += 1

        tb.Label(main, text="Border Size (%)"
        ).grid(row=row, column=0, sticky="w", padx=5, pady=0)
        tb.Spinbox(main, from_=2, to=20, increment=1, 
            textvariable=self._border_size, width=10, state="readonly"
        ).grid(row=row, column=1, sticky="w", padx=(6,4), pady=(0,6))

        row += 1

        tb.Checkbutton(main, text="Use Focal Groups in Filter", variable=self._use_focal_groups,
        ).grid(row=row, column=1, sticky="w", padx=(6,4), pady=(10,10))       

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()

    def validate(self) -> bool:
        cfg = Config()

        cfg.log_level = self._log_level.get()
        cfg.gallery_color = self._gallery_color.get()
        cfg.border_color = self._border_color.get()
        cfg.caption_color = self._caption_color.get()
        cfg.preview_size = self._preview_size.get()
        cfg.border_ratio = self._border_size.get() / 100.0
        cfg.use_focal_groups = self._use_focal_groups.get()

        cfg._save()
        MessageBox.showinfo(parent=self, title="Options", message="Changes will take effect after restart.")

        return True

    def _pick_gallery_color(self):
        color_code = colorchooser.askcolor(parent=self, title="Pick Color")
        if color_code[1]: self._gallery_color.set(color_code[1])

    def _pick_border_color(self):
        color_code = colorchooser.askcolor(parent=self, title="Pick Color")
        if color_code[1]: self._border_color.set(color_code[1])

    def _pick_caption_color(self):
        color_code = colorchooser.askcolor(parent=self, title="Pick Color")       
        if color_code[1]: self._caption_color.set(color_code[1])
