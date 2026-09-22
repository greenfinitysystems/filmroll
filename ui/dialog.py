# region(python_imports)

import logging
import tkinter as tk
import ttkbootstrap as tb

# endregion

# region(project_imports)

from core.config import Config

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class Dialog(tb.Toplevel):

    def __init__(self, parent: tk.Tk, width: int =440, height: int =320, ok: str ="OK", cancel: str ="Cancel", title: str | None =None):
        super().__init__(parent)

        cfg = Config()
        self.title(title if title else cfg.appname)
        self.ok = ok
        self.cancel = cancel
        self.parent = parent
        self.resizable(False, False)
        self.result = None

        self._icon = tb.PhotoImage(file=str(cfg.asset("icon.png")))
        self.iconphoto(False, self._icon)
        
        x = self.parent.winfo_rootx() + self.parent.winfo_width()//2 - width//2
        y = self.parent.winfo_rooty() + self.parent.winfo_height()//2 - height//2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.columnconfigure(0, weight=1)

        self.body()
        self.withdraw()       

    def body(self) -> None:
        box = tb.Frame(self)
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
        #shift = (event.state & 0x0001) != 0

        if ctrl and event.keysym in ["Return", "KP_Enter"]:
            self.on_ok()
            return

    def on_ok(self, _: any =None) -> None:
        if not self.validate():
            return

        self.result = True
        self.destroy_dialog()

    def on_cancel(self, _: any =None) -> None:
        self.result = False
        self.destroy_dialog()

    def destroy_dialog(self) -> None:
        self.grab_release()
        if self.parent:
            self.parent.focus_set()
        self.destroy()

    def show(self) -> None:
        self.deiconify()
        self.grab_set()
        self.wait_window(self)
        return self.result

    def validate(self) -> bool:
        return True
