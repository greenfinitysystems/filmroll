# region(python_imports)

import logging
import tkinter as tk
import ttkbootstrap as tb
from PIL import Image, ImageTk

# endregion

# region(project_imports)

from core.config import Config
from ui.dialog import Dialog

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class AboutDialog(Dialog):

# region(class_methods)

    def __init__(self, parent: tk.Tk):
        cfg = Config()
        # super().__init__(parent=parent, width=460, height=380, title=f"About {cfg.appname}")
        super().__init__(parent=parent, width=460, height=380, title=f"About {cfg.appname}")

# endregion

# region(overrides)

    def body(self) -> None:
        frame = tb.Frame(self, padding=(20, 20))
        frame.columnconfigure(0, weight=1)
        frame.grid()

        cfg = Config()

        logo_path = cfg.asset("logo.png")
        img = Image.open(logo_path)
        nw = int(img.size[0] * (48/img.size[1]))
        img = img.resize((nw, 48))

        self.logo = ImageTk.PhotoImage(img)

        tb.Label(frame, image=self.logo, justify="center", 
        ).grid(row=0, column=0, pady=(5,0))

        version_text = [f"Version {cfg.version}\n", cfg.about]
        tb.Label(frame, text='\n'.join(version_text), wraplength=401, justify="center"
        ).grid(row=1, column=0, pady=(0,0))

        tb.Button(frame, text="Close", width=12, command=self.on_cancel, bootstyle="primary"
        ).grid(row=2, column=0, pady=(15,15))

        self.bind("<Key>", self.on_key)

# endregion

