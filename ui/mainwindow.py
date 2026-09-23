# region(python_imports)

import logging
import platform
import sys
import tkinter as tk
from enum import Enum
from typing import Any
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox as sysmessagebox
import ttkbootstrap as tb
from PIL import Image, ImageDraw, ImageFont, ImageTk

# endregion

# region(project_imports)

from core.archive import Archive
from core.config import Config
from core.proxy import AsyncProxy
from ui.statusbar import StatusBar
from ui.aboutdialog import AboutDialog
from ui.repairarchivedialog import RepairArchiveDialog
from ui.archivepropertydialog import ArchivePropertyDialog
from ui.jpegexportdialog import JpegExportDialog
from ui.configdialog import ConfigDialog
from ui.messagebox import MessageBox
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
    separator_4 = 12
    options = 13
    separator_5 = 14
    exit = 15

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

class FilmrollGUI:

# region(class_methods)

    def __init__(self):
        super().__init__()

        try:

            cfg = Config(True)

            self._root = tb.Window(themename="flatly", className="Filmroll")
            self._root.withdraw()

            # Variables
            self.doc = None

            self._appname = cfg.appname

            self._icon = tb.PhotoImage(file=str(cfg.asset("icon.png")))
            self._root.iconphoto(False, self._icon)

            self._root.rowconfigure(0, weight=1)
            self._root.columnconfigure(0, weight=1)

            main = tb.Frame(self._root)
            main.grid(row=0, column=0, sticky="nsew")
            main.rowconfigure(0, weight=1)
            main.columnconfigure(0, weight=1)

            # display = tk.Frame(main, bg="#1e1e1e")
            display = tb.Frame(main)
            display.grid(row=0, column=0, sticky="nsew", pady=(1,3))
            display.rowconfigure(0, weight=1)
            display.columnconfigure(0, weight=1)

            self.menubar = tb.Menu(self._root, tearoff=0)
            self._root.config(menu=self.menubar)

            self.file_menu = tb.Menu(self.menubar, tearoff=0, postcommand=self.on_file_menu_unfold)
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
            self.file_menu.add_command(label="Archive Properties...", command=self.on_file_properties)
            self.file_menu.add_separator() #
            self.file_menu.add_command(label="Options...", command=self.on_file_options)
            self.file_menu.add_separator() #
            self.file_menu.add_command(label="Exit", command=self.on_file_exit)

            help_menu = tb.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="Help", menu=help_menu)
            help_menu.add_command(label="About...", command=self.on_help_about)

            self.thumbnailgrid = ThumbnailGrid(display, self)
            self.thumbnailgrid.grid(row=0, column=0, sticky="nsew")

            # -------------------------
            # STATUS SECTION
            # -------------------------
            self._statusbar = StatusBar(parent=main, cancel_func=self.on_cancel_click)
            self._statusbar.grid(row=1, column=0, sticky="ew", pady=(2,8))

            # -------------------------
            # CUSTOM EVENTS SECTION
            # -------------------------

            self._root.bind("<Key>", self.on_key)
            self._root.protocol("WM_DELETE_WINDOW", self.on_closing)

            cfg._host = self

            self._proxy = AsyncProxy()
            self._proxy._host = self
            self._proxy.register_event("UPDATE_STATUSBAR", lambda data: self.update_statusbar(*data))
            self._proxy.register_event("RELOAD_DOCUMENT", lambda _: self.on_file_reload())
            self._proxy.start()

            self._root.title(self._appname)
            self._root.deiconify()

            self.maximize()
            self._root.mainloop()

        except Exception as e:
            try:
                if self._root is not None:
                    self._root.destroy()
            except:
                pass

            sysmessagebox.showerror("Critical Error", str(e))
            sys.exit()

# endregion

# region(splash_screen)

    @staticmethod
    def run() -> None:
        FilmrollGUI._show_splash(FilmrollGUI)

    @staticmethod
    def _show_splash(mainfunc) -> None:
        try:
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

            splash.after(2200,lambda: [splash.destroy(), mainfunc()])
            splash.mainloop()

        except Exception as e:
            splash.destroy()
            sysmessagebox.showerror("Critical Error", str(e))
            sys.exit()
     
# endregion

# region(user_interface)
    def maximize(self) -> None:
        current_os = platform.system()
        if current_os == "Windows": self._root.state('zoomed')
        elif current_os == "Linux": self._root.attributes('-zoomed', True)
        elif current_os == "Darwin":  self._root.state('zoomed')
        else: self._root.attributes('-fullscreen', True)

    def update_statusbar(self, status: str, progress, step: bool=False) -> None:
        self._statusbar.update_statusbar(status=status, progress=progress, step=step)

    def reset_statusbar(self) -> None:
        self.update_statusbar("Ready", 0)

    def enable_cancel(self, enable: bool=True) -> None:
        self._statusbar.enable_cancel(enable=enable)

    def report_error(self, message: str, error: Exception=None) -> None:
        logwriter.error(f"{message} => {str(error) if error is not None else 'Unexpected error'}")
        if error is not None:
            self.showerror("Error", str(error))

    def set_dirty(self) -> None:
        if self.doc is not None:
            self.doc.dirty = True
            self._root.title(self.doc.name + " *")

    def showinfo(self, title: str, message: str) -> None:
        MessageBox.showinfo(title=title, message=message, parent=self._root)

    def showwarning(self, title: str, message: str) -> None:
        MessageBox.showwarning(title=title, message=message, parent=self._root)

    def showerror(self, title: str, message: str) -> None:
        MessageBox.showerror(title=title, message=message, parent=self._root)

    def askyesno(self, title: str, message: str) -> bool:
        return MessageBox.askyesno(title=title, message=message, parent=self._root)

# endregion
    
# region(general_events)

    def on_file_menu_unfold(self) -> None:
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

    def on_cancel_click(self, _) -> None:
        if self._statusbar.cancel_button_state != tk.DISABLED:
            self.enable_cancel(False)
            self._proxy.cancel_operation()

    def on_closing(self) -> None:
        try:

            if self._proxy.running:
                if not self.askyesno("Confirm", "Jobs running in background. Quit?"): return
                self._proxy.cancel_operation()
            
            self._proxy.stop()

            if self.doc is not None and self.doc.dirty:
                resp = sysmessagebox.askyesnocancel("Confirm", "There are unsaved changes. Save it?")
                if resp is None: return
                if resp: self.on_file_save()

            self.thumbnailgrid.unset_doc()
            self._root.destroy()

        except Exception as e:
            sysmessagebox.showerror("Critical Error", str(e))
            sys.exit()

    def on_key(self, event: Any) -> None:
        ctrl = (event.state & 0x0004) != 0
        #shift = (event.state & 0x0001) != 0

        has_document = self.doc is not None
        not_working = not self._proxy.running

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

        if event.keysym == "F1":
            self.on_help_about()
            return

# endregion

# region(private_methods)

    def on_file_reload(self) -> None:
        if not _debug_assert_(( self.doc is not None and self.doc.ready),
            "FilmrollGUI.on_file_reload() - no active archive or archive busy"): return

        try:            
            arc_path = self.doc.path
            viewstate = self.thumbnailgrid.backup_state()
            # close the current active document, if any
            self.on_file_close()

            # open the document
            self.doc = Archive.open(arc_path)

            # important to check if this archive has errors
            if not self.doc.check():
                raise ValueError("Archive has issues")

            # document is clean
            self._root.title(self.doc.name)
            self.thumbnailgrid.set_doc(self.doc, redraw=False)
            self.thumbnailgrid.restore_state(viewstate)

        except ValueError:
            # we have error in the archive
            # alert the user that the current archive need repair and fix
            # return if the user cancels
            if self.askyesno("Error", "Archive is corrupt or moved to another location. Fix it?"):
                self.on_file_repair()
            else:
                self.doc = None

        except Exception as e: 
            self.report_error("FilrollGUI.on_file_reload() - Exception occured Archive.reload", str(e))

            # safe to close any open document
            self.on_file_close()

        finally:
            # clean up the status bar
            self.reset_statusbar()

# endregion

# region(help_menu)

    def on_help_about(self):
        AboutDialog(parent=self._root).show()

# endregion

# region(file_menu)

    def on_file_new(self) -> None:
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
            self._root.title(self.doc.name)
            self.thumbnailgrid.set_doc(self.doc)

        except Exception as e: 
            self.report_error("Exception occured creating new archive", str(e))
            self.on_file_close()

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_open(self) -> None:
        # get the file name to open
        arc_path = filedialog.askopenfilename(title="Open Archive", initialdir=Path.home(),
            filetypes=((f"{self._appname} archive", "*.far"), ("All files", "*.*")))

        # if user cancels, return
        if not arc_path:
            return

        try:
            # close the current active document, if any
            self.on_file_close()

            # open the document
            self.doc = Archive.open(arc_path)

            # important to check if this archive has errors
            if not self.doc.check():
                raise ValueError("Archive has issues")

            # document is clean
            self._root.title(self.doc.name)
            self.thumbnailgrid.set_doc(self.doc)

        except ValueError:
            # we have error in the archive
            # alert the user that the current archive need repair and fix
            # return if the user cancels
            if self.askyesno("Error", "Archive is corrupt or moved to another location. Fix it?"):
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

    def on_file_save(self) -> None:
        if not _debug_assert_(( self.doc is not None and self.doc.ready),
            "FilmrollGUI.on_file_save() - no active archive or archive busy"): return

        try:
            self.doc.save()
            self._root.title(self.doc.name)

        except Exception as e:
            self.report_error("Exception occured Archive.save", str(e))

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_save_as(self) -> None:
        if not _debug_assert_(( self.doc is not None and self.doc.ready),
            "FilmrollGUI.on_file_save_as() - no active archive or archive busy"): return

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
            self._root.title(self.doc.name)

            # update the view
            self.thumbnailgrid.set_doc(self.doc)

        except Exception as e: 
            self.report_error("Exception occured saving the document", str(e))

            # Things didn't work as planned
            self.on_file_close()

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_close(self) -> None:
        # even if this is called without an active document
        # we will not fail on assertion. That is why we are not asserting
        # whether self.doc is not None or not
        if self.doc is None:
            return
                    
        try:
            if not _debug_assert_(( self.doc.ready),
                "FilmrollGUI.on_file_close() - archive busy"): return

            self.thumbnailgrid.unset_doc()
            self.doc.close()

        except Exception as e:
            self.report_error("Exception occured closing the document", str(e))

        finally:
            self.doc = None
            self._root.title(self._appname)

            # clean up the status bar
            self.reset_statusbar()

    def on_file_repair(self) -> None:
        if not _debug_assert_(( self.doc is not None and self.doc.ready),
            "FilmrollGUI.on_file_repair() - no active archive or archive busy"): return
        
        # get repair objectives from user. return if user cancels
        dlg = RepairArchiveDialog(self._root, self.doc.root)
        if not dlg.show():
            return

        try:
            # move the current archive
            self.doc.move(dlg._path.get(), dlg._delete_missing.get())
            
            # Ask user to save the newly repaired archive
            self.on_file_save_as()

        except Exception as e:
            # Handle exception
            self.report_error("Exception occured Archive.repair", str(e))

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_import_files(self) -> None:
        if not _debug_assert_(( self.doc is not None and self.doc.ready),
            "FilmrollGUI.on_file_import_files() - no active archive or archive busy"): return

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
            self.on_file_reload()

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_import_folder(self) -> None:
        if not _debug_assert_(( self.doc is not None and self.doc.ready),
            "FilmrollGUI.on_file_import_folder() - no active document or archive busy"): return

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
            self.showerror("Error", "Cannot import subfolder of current archive.")
            return

        try:
            # try to import the folder
            self.doc.import_folder(dir)

        except Exception as e:
            # report error and reload the current documet to go back where we were
            self.report_error("Exception occured Archive.import_folder", str(e))
            self.on_file_reload()

        finally:
            # clean up the status bar
            self.reset_statusbar()

    def on_file_properties(self) -> None:
        if not _debug_assert_(( self.doc is not None and self.doc.ready),
            "FilmrollGUI.on_file_properties() - no active archive or archive busy"): return

        dlg = ArchivePropertyDialog(self._root, self.doc.name, self.doc._description)
        if not dlg.show(): return

        self.doc._title = dlg._arname.get()
        self.doc._description = dlg._ardesc.get()

        self.doc.save()
        self._root.title(self.doc.name)

    def on_file_options(self) -> None:
        ConfigDialog(parent=self._root).show()

    def on_file_exit(self) -> None:
        try:
            self.on_closing()
        except:
            pass

# endregion

# region(edit_menu)

    def on_edit_cull(self) -> None:
        if not self.doc:
            return

        if not self.askyesno("Confirm", 
            f"Rejected images will be moved to bin. Proceed?"):
            return

        try: 
            self.doc.cull()

        except Exception as e: 
            self.report_error("FilmrollGUI.on_edit_cull() - Exception occured", str(e))

        finally:
            self.reset_statusbar()

    def on_edit_export_raws(self, stacks: list, parent: Any= None) -> None:
        if not self.doc: return
        
        # get the folder from user
        dir = filedialog.askdirectory(
            parent= parent or self._root,
            title="Export To",
            initialdir = Path().home(),
        )

        # if user canceled it, return
        if not dir: return

        parents = Path(dir).resolve().parents
        for p in self.doc.syspaths:
            if Path(dir).resolve() == p.resolve() or p.resolve() in parents:
                self.showerror("Error", "Cannot copy to protected folders.")
                return

        try:
            self.doc.export_raws(stacks, dir)

        except Exception as e: 
            self.report_error("FilmrollGUI.on_edit_export_raws() - Exception occured", str(e))

        finally:
            self.reset_statusbar()

    def on_edit_export_jpegs(self, stacks: list, parent: Any= None) -> None:
        if not self.doc: return

        try:
            dlg = JpegExportDialog(parent=parent or self._root, exclude_paths=self.doc.syspaths, title_suffix=f"[{len(stacks)} Images]")
            if dlg.show():
                self.doc.export_jpegs(stacks, dlg.jpeg_export_template)

        except Exception as e: 
            self.report_error("FilmrollGUI.on_edit_export_jpegs() - Exception occured", str(e))

        finally:
            self.reset_statusbar()

# endregion

# region(image_menu)

    def on_preview_rebuild_previews(self, stacks: list = None) -> None:
        if not self.doc: return
        if stacks is None: stacks = self.doc._catalog.values()

        if len(stacks) <= 0: return
        if not self.askyesno("Confirm", 
            f"Previews for {len(stacks)} images will be regenerated. Proceed?"):
            return

        try:
            self.doc.rebuild_previews(stacks)

        except Exception as e: 
            self.report_error("FilmrollGUI.on_preview_rebuild_previews() - Exception occured", str(e))

        finally:
            self.reset_statusbar()

# endregion
