# region(python_imports)

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
import ttkbootstrap as tb
from tkinter import colorchooser

# endregion

# region(project_imports)

from core.config import Config
from ui.dialog import Dialog
from core.util import JpegExportTemplate, Util
from ui.messagebox import MessageBox

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class JpegExportDialog(Dialog):
    def __init__(self, parent: tk.Tk, exclude_paths: list, title_suffix: str = None):
        self._excluded_paths = exclude_paths
        self.jpeg_export_template = None

        # Jpeg Control
        self._tk_jpeg_path = tk.StringVar(value="")
        self._tk_jpeg_size = tk.StringVar(value="1024")
        self._tk_jpeg_qual = tk.IntVar(value=85)

        # Border Control
        self._tk_border =  tk.IntVar(value=0)
        self._tk_border_ctrl = None
        self._tk_border_size =  tk.IntVar(value=4)
        self._tk_border_size_ctrl = None
        self._tk_border_color =  tk.StringVar(value="#ffffff")
        self._tk_border_color_ctrl = None
        self._tk_border_exif =  tk.IntVar(value=0)
        self._tk_border_exif_ctrl = None
        self._tk_caption_color =  tk.StringVar(value="#000000")
        self._tk_caption_color_ctrl = None
        self._tk_inject_iptc = tk.IntVar(value=0)

        super().__init__(parent=parent, ok="Export", width=550, height=370, title=f"Export Jpeg {title_suffix or ''}")

    def body(self)->None:
        browse_pad = (6,3)
        imsize = ["400", "640", "800", "1024", "1280", "1920", "2048", "2560", "Original"]

        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)
        main.columnconfigure(3, weight=0)
        main.columnconfigure(4, weight=0)

        # ----------------------------------------------------------
        # Jpeg Control
        # ----------------------------------------------------------

        tb.Label(main, text="Location").grid(row=0, column=0, sticky="w", pady=4)
        tb.Entry(main, textvariable=self._tk_jpeg_path, state='readonly',
        ).grid(row=0, column=1, sticky="ew", padx=(6,6), pady=(0,6), columnspan=3)
        tb.Button(main, text="Browse…", width=8, padding=browse_pad, command=self._browse_jpeg_path
        ).grid(row=0, column=4, padx=(6,4), pady=(0,6))

        tb.Label(main, text="Quality(%)").grid(row=1, column=0, sticky="e", pady=4)
        sb = tb.Spinbox(main, from_=20, to=100, increment=1, 
            textvariable=self._tk_jpeg_qual, width=4, state="readonly"
        )
        sb.grid(row=1, column=1, sticky="w", padx=(6,6), pady=(0,6))

        tb.Label(main, text="Image Size").grid(row=1, column=2, sticky="w", pady=4)
        dd = tb.Combobox(main, textvariable=self._tk_jpeg_size, values=imsize, state='readonly')
        dd.grid(row=1, column=3, sticky="w", padx=(6,6), pady=(0,6), ipady=0)
        dd.set("1024")

        # ----------------------------------------------------------
        # Border Control
        # ----------------------------------------------------------

        self._tk_border_ctrl= tb.Checkbutton(main, text="Draw Border", variable=self._tk_border, command=self._border_click)
        self._tk_border_ctrl.grid(row=2, column=1, sticky="ew", padx=(6,0), pady=(16,16), ipady=2, columnspan=2)

        tb.Label(main, text="Size (%)").grid(row=3, column=0, sticky="w", pady=4)
        self._tk_border_size_ctrl = tb.Spinbox(main, from_=2, to=20, increment=1, 
            textvariable=self._tk_border_size, width=4, state="readonly")
        self._tk_border_size_ctrl.grid(row=3, column=1, sticky="w", padx=(6,6), pady=(0,6))
        
        tb.Label(main, text="Border Color").grid(row=3, column=2, sticky="w", pady=4)
        self._tk_border_color_ctrl = tb.Entry(main, textvariable=self._tk_border_color,)
        self._tk_border_color_ctrl.grid(row=3, column=3, sticky="ew", padx=(6,6), pady=(0,6))
        self._tk_border_color_pick_ctrl = tb.Button(main, text="Pick...", width=8, padding=browse_pad, command=self._pick_border_color)
        self._tk_border_color_pick_ctrl.grid(row=3, column=4, sticky="ew", padx=(6,4), pady=(0,6))

        # ----------------------------------------------------------
        # Caption Control
        # ----------------------------------------------------------

        self._tk_border_exif_ctrl= tb.Checkbutton(main, text="Print Exif Data", variable=self._tk_border_exif, command=self._exif_click)
        self._tk_border_exif_ctrl.grid(row=4, column=1, sticky="ew", padx=(6,0), pady=(8,6), ipady=2)

        tb.Label(main, text="Text Color").grid(row=4, column=2, sticky="w", pady=4)
        self._tk_caption_color_ctrl = tb.Entry(main, textvariable=self._tk_caption_color,)
        self._tk_caption_color_ctrl.grid(row=4, column=3, sticky="ew", padx=(6,6), pady=(0,6))
        self._tk_caption_color_pick_ctrl = tb.Button(main, text="Pick...", width=8, padding=browse_pad, command=self._pick_caption_color)
        self._tk_caption_color_pick_ctrl.grid(row=4, column=4, sticky="ew", padx=(6,4), pady=(0,6))

        # self._tk_inject_iptc_ctrl= tb.Checkbutton(main, text="Write IPTC", variable=self._tk_inject_iptc, state="disabled",)
        # self._tk_inject_iptc_ctrl.grid(row=5, column=1, sticky="ew", padx=(6,0), pady=(16,6), ipady=2,)

        self._border_click()

        super().body()

    def _browse_jpeg_path(self) -> None:
        dir = filedialog.askdirectory(
            parent= self,
            title="Export To",
            initialdir = Path().home(),
        )

        if not dir:
            return

        parents = Path(dir).resolve().parents

        for p in self._excluded_paths:
            if Path(dir).resolve() == p.resolve() or p.resolve() in parents:
                MessageBox.showerror("Error", "Cannot copy to protected folders.", parent=self)
                return

        self._tk_jpeg_path.set(str(dir))

    def _border_click(self) -> None:
        state = "disabled" if self._tk_border.get() == 0 else "normal"
        self._tk_border_size_ctrl.config(state=state)
        self._tk_border_color_ctrl.config(state=state)
        self._tk_border_exif_ctrl.config(state=state)
        self._tk_border_color_pick_ctrl.config(state=state)

        self._exif_click()

    def _exif_click(self) -> None:
        state = "disabled" if self._tk_border_exif.get() == 0 else "normal"
        self._tk_caption_color_ctrl.config(state=state)
        self._tk_caption_color_pick_ctrl.config(state=state)

    def _pick_border_color(self) -> None:
        color_code = colorchooser.askcolor(parent=self, title="Pick Color")
        if color_code[1]: self._tk_border_color.set(color_code[1])

    def _pick_caption_color(self) -> None:
        color_code = colorchooser.askcolor(parent=self, title="Pick Color")
        if color_code[1]: self._tk_caption_color.set(color_code[1])

    def validate(self) -> bool:
        inject_iptc = self._tk_inject_iptc.get()
        jpeg_path = self._tk_jpeg_path.get().strip()
        if jpeg_path == "":
            MessageBox.showerror("Error", "Location cannot be empty", parent=self)
            return False

        jpeg_size = (
            0 if self._tk_jpeg_size.get() == "Original" else 
            int(self._tk_jpeg_size.get())
        )
        jpeg_quality = int(self._tk_jpeg_qual.get())

        cfg = Config()

        if self._tk_border.get() == 0:
            self.jpeg_export_template = JpegExportTemplate(
                export_path = jpeg_path, 
                export_size=jpeg_size, 
                export_quality = jpeg_quality, 
                border_size=0, 
                border_color=cfg.border_color, 
                border_exif = 0,
                caption_color = cfg.caption_color,
                inject_iptc = inject_iptc,
            )

            return True

        border_color = self._tk_border_color.get().strip()
        if not Util.is_valid_hex_code(border_color):
            MessageBox.showerror("Error", "Border is enabled. Border color must be a valid color code", parent=self)
            return False

        border_size = self._tk_border_size.get() / 100.0 if self._tk_border_size.get() != "Original" else 0.0
        border_exif = int(self._tk_border_exif.get())

        caption_color = self._tk_caption_color.get()

        self.jpeg_export_template = JpegExportTemplate(
            export_path = jpeg_path, 
            export_size=jpeg_size, 
            export_quality = jpeg_quality, 
            border_size=border_size, 
            border_color=border_color, 
            border_exif = border_exif,
            caption_color = caption_color,
            inject_iptc= inject_iptc,
        )

        return True
