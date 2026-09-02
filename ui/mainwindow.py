# region(python_imports)

import logging
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from enum import Enum
from pathlib import Path
from PIL import Image, ImageTk, ImageFont, ImageDraw

# endregion

# region(project_imports)

from core.archive import Archive
from core.config import Config
from core.proxy import AsyncProxy
from ui.dialog import AboutDialog, RepairArchiveDialog, ArchivePropertyDialog
from ui.thumbnailgrid import ThumbnailGrid

# endregion

# region(enumerations)

class FileMenu(Enum):
    new = 0
    open = 1
    save = 2
    saveAs = 3
    close = 4
    separator_1 = 5
    repair = 6
    separator_2 = 7
    importFiles = 8
    importFolder = 9
    separator_3 = 10
    properties = 11
    convert = 12
    separator_4 = 13
    exit = 14

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class FilmrollGUI:

# region(class_methods)

    def __init__(self, root):
        super().__init__()

        self.root = root
        self.root.withdraw()

        # Variables
        self.doc = None

        cfg = Config()
        self._appname = cfg.appname

        logo_path = cfg.asset("icon.png")
        img = Image.open(logo_path)
        w, h = img.size
        nw = int(w * (48/h))
        img = img.resize((nw, 48))

        self.icon = ImageTk.PhotoImage(img)
        self.root.iconphoto(True, self.icon)

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        main = ttk.Frame(root)
        main.grid(row=0, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)

        display = tk.Frame(main, bg="#1e1e1e")
        display.grid(row=0, column=0, sticky="nsew", pady=(1,3))
        display.rowconfigure(0, weight=1)
        display.columnconfigure(0, weight=1)

        self.menubar = tk.Menu(self.root, tearoff=0)
        self.root.config(menu=self.menubar)

        self.file_menu = tk.Menu(self.menubar, tearoff=0, postcommand=self.on_file_menu_unfold)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New...", command=self.on_file_new, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open...", command=self.on_file_open, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save", command=self.on_file_save, accelerator="Ctrl+S")
        self.file_menu.add_command(label="Save As...", command=self.on_file_save_as)
        self.file_menu.add_command(label="Close", command=self.on_file_close)
        self.file_menu.add_separator() #
        self.file_menu.add_command(label="Repair...", command=self.on_file_repair)
        self.file_menu.add_separator() #
        self.file_menu.add_command(label="Add Files...", command=self.on_file_import_files)
        self.file_menu.add_command(label="Import Folder...", command=self.on_file_import_folder)
        self.file_menu.add_separator() #
        self.file_menu.add_command(label="Properties...", command=self.on_file_properties)
        self.file_menu.add_command(label="Convert...", command=self.on_file_convert)
        self.file_menu.add_separator() #
        self.file_menu.add_command(label="Exit", command=self.root.destroy)

        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About...", command=self.on_help_about)

        self.thumbnailgrid = ThumbnailGrid(display, self.menubar, self)
        self.thumbnailgrid.grid(row=0, column=0, sticky="nsew")

        # -------------------------
        # STATUS SECTION
        # -------------------------

        self.status = tk.StringVar(value="Ready")
        self.selstat = tk.StringVar(value="SEL 0")
        self.docstat = tk.StringVar(value="PRE 0 DOC 0")

        status_frame = ttk.Frame(main)
        status_frame.grid(row=1, column=0, sticky="ew", pady=(2,8))
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=0)
        status_frame.columnconfigure(2, weight=0)
        status_frame.columnconfigure(3, weight=4)
        status_frame.columnconfigure(4, weight=0)

        ttk.Label(
            status_frame,
            textvariable=self.status,
            width=30,
        ).grid(row=0, column=0, sticky="ew", padx=(5,5))

        ttk.Label(
            status_frame,
            textvariable=self.selstat,
            width=15,
            anchor="e",
        ).grid(row=0, column=1, sticky="ew", padx=(0,0))

        ttk.Label(
            status_frame,
            textvariable=self.docstat,
            width=20,
        ).grid(row=0, column=2, sticky="ew", padx=(0,0))

        self.progress = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            mode="determinate",
        )

        self.progress.grid(row=0, column=3, sticky="ew")

        progress_cancel_imgpath_a = Path(__file__).parent.parent / "assets" / "cancel-a.png"
        progress_cancel_img_a = Image.open(progress_cancel_imgpath_a).resize((16, 16))
        self.progress_cancel_img_a = ImageTk.PhotoImage(progress_cancel_img_a)

        progress_cancel_imgpath_i = Path(__file__).parent.parent / "assets" / "cancel-i.png"
        progress_cancel_img_i = Image.open(progress_cancel_imgpath_i).resize((16, 16))
        self.progress_cancel_img_i = ImageTk.PhotoImage(progress_cancel_img_i)

        self.cancel_button = ttk.Label(
            status_frame,
            image=self.progress_cancel_img_i
        )

        self.cancel_button.grid(row=0, column=4, padx=(5,5))
        self.cancel_button_state = tk.DISABLED

        # -------------------------
        # CUSTOM EVENTS SECTION
        # -------------------------

        self.root.bind("<Key>", self.on_key)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        cfg._host = self

        self._proxy = AsyncProxy()
        self._proxy._host = self
        self._proxy.register_event("UPDATE_STATUSBAR", lambda data: self.update_statusbar(*data))
        self._proxy.register_event("RELOAD_DOCUMENT", lambda data: self.on_file_open(data))
        self._proxy.start()

        self.root.title(self._appname)
        self.root.deiconify()

        self.maximize()

# endregion

# region(splash_screen)

    @staticmethod
    def show_splash(main_func):
        splash = tk.Tk()
        splash.overrideredirect(1)

        cfg = Config()

        img = Image.open(cfg.asset("splash.png"))
        img = img.resize((600, 400))
        width, height = img.size

        draw = ImageDraw.Draw(img)
        caption_font = ImageFont.truetype(str(cfg.caption_font), 12)
        draw.text((15, 15), f"Version {cfg.version}", font=caption_font, fill="white")

        photo = ImageTk.PhotoImage(img)
        label = tk.Label(splash,image=photo, bd=0)
        label.pack()

        screen_w = splash.winfo_screenwidth()
        screen_h = splash.winfo_screenheight()

        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)

        splash.geometry(f"{width}x{height}+{x}+{y}")
        splash.after(2000,lambda: [splash.destroy(), main_func()])

        splash.mainloop()
        
# endregion

# region(user_interface)
    def maximize(self):
        current_os = platform.system()
        if current_os == "Windows": self.root.state('zoomed')
        elif current_os == "Linux": self.root.attributes('-zoomed', True)
        elif current_os == "Darwin":  self.root.state('zoomed')
        else: self.root.attributes('-fullscreen', True)

    def update_statusbar(self, status, progress, step=False):
        if status: 
            self.status.set(status)
            self.root.update_idletasks()

        progress = self.progress["value"] + progress if step else progress
        if progress >= 0:
            self.progress["value"] = min(100,progress)

        self.root.update_idletasks()

    def reset_statusbar(self):
        self.update_statusbar("Ready", 0)

    def enable_cancel(self, enable=True):
        if enable:
            self.cancel_button.config(image=self.progress_cancel_img_a)
            self.cancel_button.bind("<Button-1>", self.on_cancel_click)
            self.cancel_button_state = tk.NORMAL
        else:
            self.cancel_button.config(image=self.progress_cancel_img_i)
            self.cancel_button.unbind("<Button-1>")
            self.cancel_button_state = tk.DISABLED

    def report_error(self, message, e=None):
        logwriter.error(message)
        if e is None: return
        logwriter.error(str(e))
        messagebox.showerror("Error", str(e))

    def set_dirty(self):
        if self.doc is not None:
            self.doc.dirty = True
            self.root.title(self.doc.name + " *")

# endregion
    
# region(general_events)

    def on_file_menu_unfold(self):
        has_document = self.doc is not None
        not_working = (self._proxy.mp_total_job <= 0)

        self.file_menu.entryconfigure(FileMenu.new.value, 
            state="normal" if not_working else "disabled")

        self.file_menu.entryconfigure(FileMenu.open.value, 
            state="normal" if not_working else "disabled")

        self.file_menu.entryconfigure(FileMenu.save.value, 
            state="normal" if has_document and not_working else "disabled")

        self.file_menu.entryconfigure(FileMenu.saveAs.value, 
            state="normal" if has_document and not_working else "disabled")

        self.file_menu.entryconfigure(FileMenu.close.value, 
            state="normal" if has_document and not_working else "disabled")

        self.file_menu.entryconfigure(FileMenu.repair.value, 
            state="normal" if has_document and not_working else "disabled")

        self.file_menu.entryconfigure(FileMenu.importFiles.value, 
            state="normal" if has_document and not_working else "disabled")
        
        self.file_menu.entryconfigure(FileMenu.importFolder.value, 
            state="normal" if has_document and not_working else "disabled")

        self.file_menu.entryconfigure(FileMenu.properties.value, 
            state="normal" if has_document and not_working else "disabled")

    def on_cancel_click(self, event):
        if self.cancel_button_state == tk.DISABLED:
            return
        self.enable_cancel(False)
        self._proxy.cancel_operation()

    def on_closing(self):
        if self._proxy.running():
            if not messagebox.askyesno("Confirm", "Jobs running in background. Quit?"): return
            self._proxy.cancel_operation()
        
        self._proxy.stop()

        if self.doc is not None and self.doc.dirty:
            resp = messagebox.askyesnocancel("Confirm", "There are unsaved changes. Save it?")
            if resp is None: return
            if resp: self.on_file_save()

        self.thumbnailgrid.unset_doc()
        self.root.destroy()

    def on_key(self, event):
        ctrl = (event.state & 0x0004) != 0
        shift = (event.state & 0x0001) != 0

        has_document = self.doc is not None
        not_working = not self._proxy.running()

        if ctrl and event.keysym.lower() == "n":
            if not_working:
                self.on_file_new()
            return

        if ctrl and event.keysym.lower() == "o":
            if not_working:
                self.on_file_open()
            return

        if ctrl and event.keysym.lower() == "s":
            if has_document and not_working:
                self.on_file_save()
            return

# endregion

# region (private_methods)

    def _get_export_folder(self):
        assert self.doc is not None, "No active document. Cannot export"
        if self.doc is None:
            return None

        # get the folder from user
        dir = filedialog.askdirectory(
            title="Copy To",
            initialdir = self.doc.tif_dir,
        )

        # if user canceled it, return
        if not dir:
            return None

        # sanity check. Cannot import from current archive's subfolder
        if (
            self.doc.raw_dir.resolve() in Path(dir).resolve().parents or 
            self.doc.jpg_dir.resolve() in Path(dir).resolve().parents or 
            self.doc.low_dir.resolve() in Path(dir).resolve().parents or 
            self.doc.bin_dir.resolve() in Path(dir).resolve().parents ):
            messagebox.showerror("Error", "Cannot copy to protected folders of the current archive.")
            return None

        return dir

# endregion

# region(help_menu)

    def on_help_about(self):
        AboutDialog(parent=self.root).show()

# endregion

# region(file_menu)

    def on_file_new(self):
        # get archive name from user. return if calcenled
        dir = filedialog.askdirectory(title="New Archive",
            initialdir=str(Path.home()))

        if not dir:
            return

        try: 
            # close any active document
            self.on_file_close()

            # create a new document
            self.doc = Archive.new(dir)
            self.root.title(self.doc.name)
            self.thumbnailgrid.set_doc(self.doc)

        except Exception as e: 
            self.report_error("Exception occured creating new archive", str(e))
            self.on_file_close()

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_open(self, reload=False):
        if reload and self.doc is None:
            raise Exception("Reload failed. No active document.")

        # get the file name to open
        arc_path = filedialog.askopenfilename(title="Open Archive", initialdir=Path.home(),
            filetypes=((f"{self._appname} archive", "*.far"), ("All files", "*.*"))
        ) if not reload else self.doc.path

        # if user cancels, return
        if not arc_path:
            return

        existing_filters = self.thumbnailgrid._filters if reload else None

        try: 
            # close the current active document, if any
            self.on_file_close()

            # open the document
            self.doc = Archive.open(arc_path)

            # important to check if this archive has errors
            if not self.doc.check():
                raise ValueError("Archive has issues")

            # document is clean
            self.root.title(self.doc.name)
            
            self.thumbnailgrid.set_doc(self.doc, existing_filters)

        except ValueError:
            # we have error in the archive
            # alert the user that the current archive need repair and fix
            # return if the user cancels
            if messagebox.askyesno("Error", "Archive is corrupt or moved to another location. Fix it?"):
                self.on_file_repair()
            else:
                self.doc = None

        except Exception as e: 
            self.report_error("Exception occured Archive.open", str(e))

            # safe to close any open document
            self.on_file_close()

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_save(self):
        assert self.doc is not None, "No active document. Cannot save"
        if self.doc is None:
            return

        try:
            self.doc.save()
            self.root.title(self.doc.name)

        except Exception as e:
            self.report_error("Exception occured Archive.save", str(e))

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_save_as(self):
        assert self.doc is not None, "No active document. Cannot save"
        if self.doc is None:
            return

        # get new file name & location from user
        filename = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension = "*.far",
            initialdir = self.doc.root,
            initialfile = Path(self.doc.path).name,
            filetypes=((f"{self._appname} archive", "*.far"), ("All files", "*.*"))
        )

        # if user cancels return
        if not filename:
            return

        try:
            # save in the current location
            self.doc.save(filename)

            # close currently open document and open the newly saved document
            self.on_file_close()
            self.doc = Archive.open(filename)
            self.root.title(self.doc.name)

            # update the view
            self.thumbnailgrid.set_doc(self.doc)

        except Exception as e: 
            self.report_error("Exception occured saving the document", str(e))

            # Things didn't work as planned
            self.on_file_close()

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_close(self):
        # even if this is called without an active document
        # we will not fail on assertion. That is why we are not asserting
        # whether self.doc is not None or not
        if self.doc is None:
            return

        try:
            self.thumbnailgrid.unset_doc()
            self.doc.close()

        except Exception as e:
            self.report_error("Exception occured closing the document", str(e))

        finally:
            self.doc = None
            self.root.title(self._appname)

            # clean up the status bar
            self.reset_statusbar()

    def on_file_repair(self):
        assert self.doc is not None, "No active document. Cannot import"
        if self.doc is None:
            return

        # get repair objectives from user. return if user cancels
        dlg = RepairArchiveDialog(self.root, self.doc.root)
        if not dlg.show():
            return

        try:
            # move the current archive
            self.doc.move(dlg._apath.get(), dlg._delete_missing.get())
            
            # Ask user to save the newly repaired archive
            self.on_file_save_as()

        except Exception as e:
            # Handle exception
            self.report_error("Exception occured Archive.repair", str(e))

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_import_files(self):
        assert self.doc is not None, "No active document. Cannot import"
        if self.doc is None:
            return

        # get the fiels from user
        files = filedialog.askopenfilenames(
            title="Import Files",
            initialdir = Path.home(),
        )

        # if user canceled return
        if not files or len(list(files)) <= 0:
            return

        try:
            # import the files
            self.doc.import_folder(list(files))

        except Exception as e:
            # report error and reload the current documet to go back where we were
            self.report_error("Exception occured Archive.import_folder", str(e))
            self.on_file_open(reload=True)

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_import_folder(self):
        assert self.doc is not None, "No active document. Cannot import"
        if self.doc is None:
            return

        # get the folder from user
        dir = filedialog.askdirectory(
            title="Import From",
            initialdir = Path.home(),
        )

        # if user canceled it, return
        if not dir:
            return

        # sanity check. Cannot import from current archive's subfolder
        if self.doc.root.resolve() in Path(dir).resolve().parents:
            messagebox.showerror("Error", "Cannot import subfolder of current archive.")
            return

        try:
            # try to import the folder
            self.doc.import_folder(dir)

        except Exception as e:
            # report error and reload the current documet to go back where we were
            self.report_error("Exception occured Archive.import_folder", str(e))
            self.on_file_open(reload=True)

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_properties(self):
        assert self.doc is not None, "No active document."
        if self.doc is None:
            return

        dlg = ArchivePropertyDialog(self.root, self.doc.name, self.doc._description)
        if not dlg.show(): return

        self.doc._title = dlg._arname.get()
        self.doc._description = dlg._ardesc.get()

        self.doc.save()
        self.root.title(self.doc.name)

    def on_file_convert(self):
        # get the file name to open
        arc_path = filedialog.askopenfilename(title="Open Archive", initialdir=Path.home(),
            filetypes=((f"{self._appname} archive", "*.far"), ("All files", "*.*")))

        # if user cancels, return
        if not arc_path:
            return

        src_path = Path(arc_path)
        dst_path = src_path.with_name(f"{src_path.stem}-json{src_path.suffix}")

        try:
            # open the document
            doc = Archive.open_legacy(arc_path)
            doc.save(dst_path)
            messagebox.showinfo("Conversion Complete", f"Archive comverted to latest format and saved as {dst_path.stem}{dst_path.suffix}")

        except Exception as e: 
            self.report_error("Exception occured Archive.open", str(e))


# endregion

# region(edit_menu)

    def on_edit_cull(self):
        if not self.doc:
            return

        if not messagebox.askyesno("Confirm", 
            f"Rejected images will be moved to bin. Proceed?"):
            return

        try: 
            self.doc.cull()

        except Exception as e: 
            self.report_error("Exception occured Archive.on_cull", str(e))

        finally:
            self.reset_statusbar()

    def on_edit_copy_files(self, stacks, ftype):
        dir = self._get_export_folder()
        if dir is None:
            return

        try:
            self.doc.copy_files(stacks, ftype, dir)

        except Exception as e: 
            self.report_error("Exception occured Archive.on_cull", str(e))

        finally:
            self.reset_statusbar()

# endregion

# region(preview_menu)

    def on_preview_rebuild(self, stacks: list = None):
        if not self.doc: return
        if stacks is None: stacks = self.doc._catalog.values()

        if len(stacks) <= 0: return
        if not messagebox.askyesno("Confirm", 
            f"Previews for {len(stacks)} images will be regenerated. Proceed?"):
            return

        try:
            self.doc.rebuild_previews(stacks)

        except Exception as e: 
            self.report_error("Exception occured Archive.rebuild_previews", str(e))

        finally:
            self.reset_statusbar()

# endregion

