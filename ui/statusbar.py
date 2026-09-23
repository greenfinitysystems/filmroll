# region(python_imports)

import logging
import tkinter as tk
from typing import Any
import ttkbootstrap as tb
from PIL import Image, ImageDraw, ImageFont, ImageTk

# endregion

# region(project_imports)

from core.config import Config

# endregion

# region(enumerations)

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

import traceback
def _debug_assert_(condition, message):
    if condition: return True
    # Join the list into a single clean string
    # We slice [:-1] to exclude this line/function itself from the trace
    stack = '\n'.join(traceback.format_stack()[:-1])
    logwriter.debug(f"assert failed: {message}-{stack}")
    return False

# endregion

class StatusBar(tb.Frame):

# region(class_methods)

    def __init__(self, parent: Any, cancel_func: Any):
        super().__init__(parent)
        self._parent = parent
        self._cancel_func = cancel_func

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=0)
        self.columnconfigure(5, weight=4)
        self.columnconfigure(6, weight=0)

        cfg = Config()

        self._status = tk.StringVar(value="Ready")
        self._selstat = tk.StringVar(value="SEL 0")
        self._docstat = tk.StringVar(value="IMG 0")
        self._metaind = tk.StringVar(value="⌕")
        self._rateind = tk.StringVar(value="★")

        tb.Label(self, textvariable=self._status,  width=30,).grid(row=0, column=0, sticky="ew", padx=(5,5))
        tb.Label(self, textvariable=self._selstat, width=10, anchor="e",).grid(row=0, column=1, sticky="ew", padx=(0,0))
        tb.Label(self, textvariable=self._docstat, width=10,).grid(row=0, column=2, sticky="ew", padx=(0,0))

        self._metaind_ctrl = tb.Label(self, textvariable=self._metaind, width=2,)
        self._metaind_ctrl.grid(row=0, column=3, sticky="ew", padx=(0,5))

        self._rateind_ctrl = tb.Label(self, textvariable=self._rateind, width=2,)
        self._rateind_ctrl.grid(row=0, column=4, sticky="ew", padx=(0,5))

        self.progress = tb.Progressbar(self, orient="horizontal", mode="determinate", bootstyle="primary")
        self.progress.grid(row=0, column=5, sticky="ew")

        progress_cancel_img_a = Image.open(cfg.asset("cancel-a.png")).resize((16, 16))
        self.progress_cancel_img_a = ImageTk.PhotoImage(progress_cancel_img_a)
        progress_cancel_img_i = Image.open(cfg.asset("cancel-i.png")).resize((16, 16))
        self.progress_cancel_img_i = ImageTk.PhotoImage(progress_cancel_img_i)

        self.cancel_button = tb.Label(self, image=self.progress_cancel_img_i)
        self.cancel_button.grid(row=0, column=6, padx=(5,5))
        self.cancel_button_state = tk.DISABLED

        self.set_rating_indicator(0)
        self.set_filter_indicator(0)

# endregion

# region(methods)

    def update_statusbar(self, status: str, progress, step: bool=False) -> None:
        if status: self._status.set(status)
        progress = self.progress["value"] + progress if step else progress
        if progress >= 0: self.progress["value"] = min(100,progress)
        self.update_idletasks()

    def reset_statusbar(self) -> None:
        self.update_statusbar("Ready", 0)

    def enable_cancel(self, enable: bool=True) -> None:
        if enable:
            self.cancel_button.config(image=self.progress_cancel_img_a)
            self.cancel_button.bind("<Button-1>", self._cancel_func)
            self.cancel_button_state = tk.NORMAL
        else:
            self.cancel_button.config(image=self.progress_cancel_img_i)
            self.cancel_button.unbind("<Button-1>")
            self.cancel_button_state = tk.DISABLED

    def set_document_stats(self, count: int) -> None:
        self._docstat.set(f"IMG {count}")

    def set_selected_stats(self, count: int):
        self._selstat.set(f"SEL {count}")

    def set_rating_indicator(self, indicator: int=9):
        indicator = max(0, min(9, indicator))
        self._rateind_ctrl.configure(foreground=Config().rating_colors[indicator])

    def set_filter_indicator(self, indicator: int=0):
        color = "#000000" if indicator!=0 else "#ffffff"
        self._metaind_ctrl.configure(foreground=color)

# endregion

