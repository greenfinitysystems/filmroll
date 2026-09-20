# region(python_imports)

import sys
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext, colorchooser
from tkinter.colorchooser import Chooser
import ttkbootstrap as tb
from PIL import Image, ImageTk

# endregion

# region(project_imports)

from core.config import Config
from core.util import JpegExportTemplate, Util
from ui.messagebox import MessageBox
from ui.multiselectdropdown import MultiSelectDropdown
from ui.tageditor import TagEditor

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
        # super().__init__(parent=parent, width=460, height=380, title=f"About {cfg.appname}")
        super().__init__(parent=parent, width=460, height=680, title=f"About {cfg.appname}")

    def body(self) -> None:
        frame = tb.Frame(self, padding=(20, 20))
        frame.columnconfigure(0, weight=1)
        frame.grid()

        cfg = Config()

        logo_path = cfg.asset("logo.png")
        img = Image.open(logo_path)
        w, h = img.size
        nw = int(w * (48/h))
        img = img.resize((nw, 48))

        self.logo = ImageTk.PhotoImage(img)

        tb.Label(
            frame,
            image=self.logo,
            justify="center",
        ).grid(row=0, column=0, pady=(5,0))

        version_text = [f"Version {cfg.version}\n", cfg.about]

        tb.Label(
            frame,
            text='\n'.join(version_text),
            wraplength=401,
            justify="center"
        ).grid(row=1, column=0, pady=(0,0))

        tb.Button(
            frame,
            text="Close",
            width=12,
            command=self.on_cancel,
            bootstyle="primary"
        ).grid(row=2, column=0, pady=(15,15))

        self.bind("<Key>", self.on_key)

class RepairArchiveDialog(Dialog):
    def __init__(self, parent: tk.Tk, current_path: str):
        self._apath = tk.StringVar()
        self._apath.set(current_path)

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

        tb.Entry(main, textvariable=self._apath,
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
        dir = filedialog.askdirectory(title="Select Folder", initialdir=self._apath.get())
        if dir: self._apath.set(dir)

    def validate(self) -> bool:
        if (self._apath.get() == "" or 
            not Path(self._apath.get()).exists() or 
            not Path(self._apath.get()).is_dir()):
            MessageBox.showerror("Error", "Please provide a valid folder.", parent=self)
            return False

        return True

class FilterDialog(Dialog):
    def __init__(self, parent: tk.Tk, filters: list):
        self._filters = filters
        self._variables = []
        super().__init__(parent=parent, ok="Apply", height=400, title="Apply Filter")

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

class ArchivePropertyDialog(Dialog):
    def __init__(self, parent: tk.Tk, name: str, desc: str):
        name = "" if name is None else name
        desc = "" if desc is None else desc
        self._arname = tk.StringVar(value=name)
        self._ardesc = tk.StringVar(value=desc)
        super().__init__(parent=parent, ok="Save", height=400, title="Archive Properties")

    def body(self) -> None:
        # our main grid
        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        label = tb.Label(main, text="Title" )
        label.grid(row=0, column=0, sticky="w", padx=5, pady=0)
        name = tb.Entry(main, textvariable=self._arname)
        name.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        label = tb.Label(main, text="Description" )
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
    def __init__(self, parent: tk.Tk, comment: str, tags:list = []):
        self._usernote = tk.StringVar(value=comment)
        self._tags = tags
        super().__init__(parent=parent, ok="Save", width=650, height=500, title="Properties")

    def body(self) -> None:
        # our main grid
        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        label = tb.Label(main, text="Notes" )
        label.grid(row=0, column=0, sticky="w", padx=5, pady=0)
        self._st = scrolledtext.ScrolledText(main, width=50, height=10)
        self._st.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        cfg = Config()
        label = tb.Label(main, text="Tags" )
        label.grid(row=2, column=0, sticky="w", padx=5, pady=(10,0))
        self._tageditor = TagEditor(main, values=cfg.tagstore.get(), tags=self._tags, max_height=40)
        self._tageditor.grid(row=3, column=0, sticky="ew", pady=0)

        self._st.insert('1.0', self._usernote.get())

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()
        self._st.focus_set()

    def validate(self) -> bool:
        self._usernote.set( self._st.get('1.0', 'end-1c'))
        self._tags = self._tageditor.get()
        return True

class JpegExportDialog(Dialog):
    def __init__(self, parent: tk.Tk, exclude_paths: list):
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

        super().__init__(parent=parent, ok="Export", width=550, height=370, title="Export Jpeg")

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

        tb.Label(main, text="Location"
        ).grid(row=0, column=0, sticky="w", pady=4)
        
        tb.Entry(main, textvariable=self._tk_jpeg_path, state='readonly',
        ).grid(row=0, column=1, sticky="ew", padx=(6,6), pady=(0,6), columnspan=3)

        tb.Button(
            main,
            text="Browse…",
            width=8,
            padding=browse_pad,
            command=self.browse_jpeg_path
        ).grid(row=0, column=4, padx=(6,4), pady=(0,6))

        tb.Label(main, text="Size"
        ).grid(row=1, column=0, sticky="w", pady=4)

        dd = tb.Combobox(main, textvariable=self._tk_jpeg_size, values=imsize, state='readonly')
        dd.grid(row=1, column=1, sticky="w", padx=(6,6), pady=(0,6), ipady=0)
        dd.set("1024")

        tb.Label(main, text="Quality (%)"
        ).grid(row=1, column=2, sticky="e", pady=4)

        sb = tb.Spinbox(
            main, 
            from_=20, 
            to=100, 
            increment=1, 
            textvariable=self._tk_jpeg_qual,
            width=4,
            state="readonly"
        )
        sb.grid(row=1, column=3, sticky="w", padx=(6,6), pady=(0,6))

        # ----------------------------------------------------------
        # Border Control
        # ----------------------------------------------------------

        self._tk_border_ctrl= tb.Checkbutton(main, text="Border", variable=self._tk_border, command=self.border_click)
        self._tk_border_ctrl.grid(row=2, column=1, sticky="ew", padx=(6,0), pady=(16,6), ipady=2, columnspan=2)

        tb.Label(main, text="Color"
        ).grid(row=3, column=0, sticky="w", pady=4)

        self._tk_border_color_ctrl = tb.Entry(main, textvariable=self._tk_border_color,)
        self._tk_border_color_ctrl.grid(row=3, column=1, sticky="w", padx=(6,6), pady=(0,6), columnspan=3)

        tb.Label(main, text="Size (%)"
        ).grid(row=3, column=2, sticky="e", pady=4)

        self._tk_border_size_ctrl = tb.Spinbox(
            main, 
            from_=2, 
            to=20, 
            increment=1, 
            textvariable=self._tk_border_size,
            width=4,
            state="readonly"
        )
        self._tk_border_size_ctrl.grid(row=3, column=3, sticky="w", padx=(6,6), pady=(0,6))

        self._tk_border_exif_ctrl= tb.Checkbutton(main, text="Print Exif Data", variable=self._tk_border_exif,)
        self._tk_border_exif_ctrl.grid(row=4, column=1, sticky="ew", padx=(6,0), pady=(16,6), ipady=2, columnspan=2)

        self.border_click()

        super().body()

    def browse_jpeg_path(self) -> None:
        # get the folder from user
        dir = filedialog.askdirectory(
            parent= self,
            title="Export To",
            initialdir = Path().home(),
        )

        # if user canceled it, return
        if not dir:
            return

        parents = Path(dir).resolve().parents

        for p in self._excluded_paths:
            if Path(dir).resolve() == p.resolve() or p.resolve() in parents:
                MessageBox.showerror("Error", "Cannot copy to protected folders.", parent=self)
                return

        self._tk_jpeg_path.set(str(dir))

    def border_click(self) -> None:
        state = "disabled" if self._tk_border.get() == 0 else "normal"
        self._tk_border_size_ctrl.config(state=state)
        self._tk_border_color_ctrl.config(state=state)
        self._tk_border_exif_ctrl.config(state=state)

    def validate(self) -> bool:
        jpeg_path = self._tk_jpeg_path.get().strip()
        if jpeg_path == "":
            MessageBox.showerror("Error", "Location cannot be empty", parent=self)
            return False

        jpeg_size = int(self._tk_jpeg_size.get())
        jpeg_quality = int(self._tk_jpeg_qual.get())

        if self._tk_border.get() == 0:
            self.jpeg_export_template = JpegExportTemplate(
                export_path = jpeg_path, 
                export_size=jpeg_size, 
                export_quality = jpeg_quality, 
                border_size=0, 
                border_color="", 
                border_exif = 0
            )

            return True

        border_color = self._tk_border_color.get().strip()
        if not Util.is_valid_hex_code(border_color):
            MessageBox.showerror("Error", "Border is enabled. Border color must be a valid color code", parent=self)
            return False

        border_size = self._tk_border_size.get() / 100.0 if self._tk_border_size.get() != "Original" else 0.0
        border_exif = int(self._tk_border_exif.get())

        self.jpeg_export_template = JpegExportTemplate(
            export_path = jpeg_path, 
            export_size=jpeg_size, 
            export_quality = jpeg_quality, 
            border_size=border_size, 
            border_color=border_color, 
            border_exif = border_exif
        )

        return True

class BatchTagEditDialog(Dialog):
    def __init__(self, parent: tk.Tk, tags: list):
        self._cur_tags = tags
        self._del_tags = []
        self._add_tags = []
        super().__init__(parent=parent, ok="Apply", width=450, height=400, title="Apply Tags")

    def body(self) -> None:
        # our main grid
        main = tb.Frame(self, padding=(25, 20))
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        cfg = Config()

        label = tb.Label(main, text="Remove Tags" )
        label.grid(row=0, column=0, sticky="w", padx=5, pady=0)
        self._del_te = TagEditor(main, values=self._cur_tags, tags=[], max_height=40, allowcreate=False)
        self._del_te.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        
        label = tb.Label(main, text="Add Tags" )
        label.grid(row=2, column=0, sticky="w", padx=5, pady=(10,0))
        self._add_te = TagEditor(main, values=cfg.tagstore.get(), tags=[], max_height=40)
        self._add_te.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        # the base class body creates the rst of the form with Ok, cancel Buttons
        super().body()

    def validate(self) -> bool:
        self._del_tags = self._del_te.get()
        self._add_tags = self._add_te.get()
        return True

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
        # our main grid
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
        MessageBox.showinfo("Options", "Modified options will only take effect after restart.")

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
