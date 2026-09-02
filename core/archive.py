# region(python_imports)

import logging
import pickle
import jsonpickle
from datetime import datetime
from pathlib import Path
from typing import Self, Any
import subprocess
import platform

# endregion

# region(project_imports)

from core.file import File, FileType, FileOps
from core.stack import Stack
from core.preview import PreviewBuilder
from core.util import FileOpsJob, MetadataJob, PreviewJob, CollateJob
from core.config import Config
from core.proxy import AsyncProxy, AsyncCtrlParams
from ui.messagebox import messagebox

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class Archive():

# region(class_methods)

    CURRENT_VERSION = 2

    def __init__(self):
        self._root = None
        self._catalog = {}
        self._last_saved_loc = None
        self._lock_count = 0
        self._dirty = False

        self._title = None
        self._description = None

        self._version = self.CURRENT_VERSION

    def __setstate__(self, state):
        # Old picklings before versioning might not have a '_version' key
        old_version = state.get("_version", 1)

        # 3. Upgrade from v1 to v2
        if old_version < 2:
            state["_lock_count"] = 0
            state["_title"] = None
            state["_description"] = None

        # 5. Bring the version up to date and load the dictionary
        state["_version"] = self.CURRENT_VERSION
        self.__dict__.update(state)

# endregion

# region(properies)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def name(self) -> str | None:
        if self._root is None: return None
        if self._title is not None: return self._title
        return self._root.stem

    @property
    def description(self) -> str:
        return self._description

    @property
    def low_dir(self) -> Path | None:
        return (self._root / "4-low") if self._root is not None else None

    @property
    def jpg_dir(self) -> Path | None:
        return (self._root / "3-jpg") if self._root is not None else None

    @property
    def raw_dir(self) -> Path | None:
        return (self._root / "1-raw") if self._root is not None else None

    @property
    def tif_dir(self) -> Path | None:
        return (self._root / "2-tif") if self._root is not None else None

    def dir_by_type(self, type: FileType) -> Path | None:
        if type == None: return self.root
        if type == FileType.RAW: return self.raw_dir
        elif type == FileType.TIF: return self.tif_dir
        elif type == FileType.JPG: return self.jpg_dir
        elif type == FileType.LOW: return self.low_dir
        else: raise TypeError("Unsupported file type")

    @property
    def bin_dir(self) -> Path | None:
        return (self._root / "9-bin") if self._root is not None else None

    @property
    def bin_dir_jpg(self) -> Path | None:
        return (self.bin_dir / "jpg") if self._root is not None else None

    @property
    def bin_dir_raw(self) -> Path | None:
        return (self.bin_dir / "raw") if self._root is not None else None

    @property
    def bin_dir_tif(self) -> Path | None:
        return (self.bin_dir / "tif") if self._root is not None else None

    def bin_dir_by_type(self, type: FileType) -> Path | None:
        if type == None: return self.bin_dir
        if type == FileType.RAW: return self.bin_dir_raw
        elif type == FileType.TIF: return self.bin_dir_tif
        elif type == FileType.JPG: return self.bin_dir_jpg
        elif type == FileType.LOW: return None
        else: raise TypeError("Unsupported file type")

    @property
    def anys(self) -> list:
        return [s.any for s in self._catalog.values() if s.any is not None]

    @property
    def lows(self) -> list:
        return [s.low for s in self._catalog.values() if s.low is not None]

    @property
    def jpgs(self) -> list:
        return [s.jpg for s in self._catalog.values() if s.jpg is not None]

    @property
    def raws(self) -> list:
        return [s.raw for s in self._catalog.values() if s.raw is not None]

    @property
    def tifs(self) -> list:
        return [s.tif for s in self._catalog.values() if s.tif is not None]

    @property
    def files(self) -> list:
        return (self.raws + self.tifs + self.jpgs + self.lows)

    @property
    def ready(self) -> bool:
        return (self._root is not None and self._lock_count == 0)

    @property
    def path(self) -> str:
        return self._last_saved_loc

    @property
    def file_count(self) -> int:
        counter = 0
        for s in self._catalog.values():
            counter += len(s.files)
        return counter

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        self._dirty = value

# endregion

# region(methods)

    # returns the content of the archive as a list
    def as_list(self) -> list:
        return list(self._catalog.values()) if self._root is not None else []

    # returns the content of the archive as a sorted list by identity
    def as_list2(self) -> list:
        return sorted( (list(self._catalog.values()) if self._root is not None else [] ), key= lambda stack: stack.identity)

    # search for a file based oon identity and type
    def find(self, identity: str, type: FileType) -> File | None:
        stack = self._catalog.get(identity, None)
        if stack is not None:
            return stack.find(type)
        return None

    # locks the current archive for any content changing processes
    def lock(self) -> None:
        # logwriter.info(f"Locking archive. current lock ={self._lock_count}")
        self._lock_count += 1

    # unlocks the current archive locked by a previous operation
    def unlock(self, force: bool = False) -> None:
        # logwriter.info(f"Unlocking archive. current lock ={self._lock_count}")
        
        if force:
            self._lock_count = 0
            return

        if self._lock_count > 0:
            self._lock_count -= 1
            return

        self._lock_count = 0

    # clones the current archive definition to a new file.
    # it does not do anything with the actual mage files
    def clone(self) -> Self:
        assert self.root is not None, "Archive::clone() - archive has no root"

        bytestr = pickle.dumps(self)
        return pickle.loads(bytestr)

    @staticmethod
    # creates a new archive at the give folder
    def new(base: str) -> Self:
        path = Path(base).resolve()
        assert path.exists() and path.is_dir(), "Archive::new() - path not found"

        # create the new archive object
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        ar = Archive()
        ar._root = path / f"FILMROLL-{ts}"

        # create the archive subfolders
        for d in [
            ar.raw_dir, ar.tif_dir, ar.jpg_dir, ar.low_dir, ar.bin_dir, 
            ar.bin_dir_raw, ar.bin_dir_tif, ar.bin_dir_jpg
        ]:
            d.mkdir(parents=True)

        # save the new archive
        ar.save()

        logwriter.info(f"New archive {str(ar._root)} created")
        return ar

    @staticmethod
    # opens a saved archive from disk and returns the archive
    def open(file_name: str) -> Self:
        with open(file_name, "r") as f:
            ar = jsonpickle.decode(f.read())
        ar.unlock()
        return ar

    @staticmethod
    # opens a saved legacy archive from disk and returns the archive
    def open_legacy(file_name: str) -> Self:
        with open(file_name, 'rb') as f:
            ar = pickle.load(f)

        ar.unlock()
        return ar

    # closes the current archive
    def close(self) -> None:
        self._root = None
        self._catalog.clear()
        self.lock()

    # saves the current archive. also works as "save as"
    def save(self, save_as: str =None) -> None:
        assert self.root is not None, "Archive::save() - archive has no root"

        # we are given a file name, we will use that
        if save_as is not None:
            self._last_saved_loc = save_as

        # otherwise we will see if we already had an last_saved_location
        # but if we find that our last saved location is None, which can be 
        # a case because during the creation of a new archive we force it to save
        # for the first time, we will use a default archive name
        if self._last_saved_loc is None:
            self._last_saved_loc = self._root / f"{Config().appname}.far"

        self.unlock(force=True)
        self.dirty = False

        # after saving the document, we will reopen it
        # with open(self._last_saved_loc, 'wb') as f:
        #     pickle.dump(self, f)

        frozen_json = jsonpickle.encode(self)
        with open(self._last_saved_loc, "w") as f:
            f.write(frozen_json)

    # backs up current archive to a different file
    def backup(self) -> None:
        assert self.root is not None, "Archive::backup() - archive has no root"

        # construct a backup file name and path
        p = Path(self._last_saved_loc)
        backup_file_name = f"{p.stem}-backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}{p.suffix}"
        backup_file = p.parent / backup_file_name

        # clone the current archive and remove any lock
        ar = self.clone()
        ar.unlock(force=True)

        # save the cloned archive
        # with open(backup_file, 'wb') as f:
        #     pickle.dump(ar, f)

        frozen_json = jsonpickle.encode(self)
        with open(backup_file, "w") as f:
            f.write(frozen_json)

    # move and repair the current archive to a new folder
    # and also checks and fixes integrity.
    def move(self, new_path: str, remove_missing: bool) -> None:
        assert self.root is not None, "Archive::move() - archive has no root"

        # check that the new path that we are given is a valid path
        # and also a "folder"
        path = Path(new_path).resolve()
        assert path.exists() and path.is_dir(), "Archive::new() - path not found"

        # set this as new root path and try to repair
        self._root = path
        self.repair(remove_missing=True if remove_missing > 0 else False)

    # checks if the current archive has errors or integrity issue
    def check(self) -> None:
        assert self.root is not None, "Archive::check() - archive has no root"

        # first chcek that the root itself exists
        if not self.root.exists():
            return False

        # Now for all the files in this archive we need to perform certain check
        for f in self.files:
        # firstly all files are located in the correct folder
            if self.dir_by_type(f.type) != f.dir:
                return False

        # secondly, the file should physically exists
            if not f.exists() and not f.is_file():
                return False

        # thirdly, the files actual name and legitimate name are the same
            if f.name != f.legit_name:
                return False

        logwriter.info(f"Archive is in good state")
        return True

    # repair current archive by checking and removing missing files
    def repair(self, remove_missing: bool =True) -> None:
        assert self.root is not None, "Archive::repair() - archive has no root"

        for f in self.files:
        # for all the files in the archive
        # we will try to fix their path first
            if f.migrate(self.dir_by_type(f.type)):
                continue

        # if does not work and we have remove_missing on
        # we will kick that file out of our archive
            stack = self._catalog.get(f.identity, None)
            if remove_missing and stack is not None:
                stack.remove(f.type)

        # Next, check if we have left with some stacks 
        # where we only have the preview files left (or no file at all). This is meaningless
        # and hence we shall remove these stacks too.
        self._catalog = {k : v for k, v in self._catalog.items() 
            if not v.empty and not v.orphan }

    # imports a single folder containing RAW, JPG, TIFF or PNG files
    # multiprocess - multistep
    def import_folder(self, folder: list | str) -> None:
        # final step
        def _step_5(src_ar, ar, win):
            # we are done; finally we will copy our temporary archive, where we did
            # all the important work to the original archive; and save it too
            src_ar = ar.clone()
            src_ar.repair()
            src_ar.save()

            # we are done. we shall unlock the origical document
            src_ar.unlock()

            logwriter.info(f"Archive.import all processes completed")

            # asking the thumbnail view, or whomsoever it may concern to 
            # reload the document
            win.event_queue.put(("RELOAD_DOCUMENT", True))

        # consolidate and repair
        # if user cancels, it has no effect as such
        def _step_4(event):
            async_res = event.payload
            win = AsyncProxy()

            logwriter.info(f"Archive.import._step_4")

            # as usual - stop the custom event first; we don't need it any more
            win.exit_async_session(event)

            # clean the status bar
            win.reset_statusbar()

            # just for shoing the message
            win.evaluate_async_outcome(event)

            # get back the temporary archive.
            ar = async_res.event_args[1]

            # copy the list of stacks that we shared with the child processes
            # to our new temporary archive. It has all the new low files added
            mp_catalog = async_res.event_args[2]
            for k, v in mp_catalog.items():
                ar._catalog[k] = v

            ar.repair()

            # we are done; finally we will copy our temporary archive, where we did
            # all the important work to the original archive; and save it too
            src_ar = async_res.event_args[0]
            _step_5(src_ar, ar, win)

        # generate previews
        # if user cancels midway, confirm if he/she wants to proceed with preview generation
        # if yes, resume; if not, leave it as-is, jump to step 5 and return
        def _step_3(event):
            async_res = event.payload
            win = AsyncProxy()

            logwriter.info(f"Archive.import._step_3)")

            # as usual - stop the custom event first; we don't need it any more
            win.exit_async_session(event)

            # clean the status bar
            win.reset_statusbar()

            # get back the temporary archive.
            ar = async_res.event_args[1]

            # try to repair the archive. It has all the files after collating
            # so if it cannot find any file, it means, the file was not physically copied
            # for some reason, whether user canceled it midway or a netwrok / hardware
            # issue occured during transfer; we will keep only those files that we 
            # could actually transfer
            ar.repair(remove_missing=True)

            logwriter.info(f"Archive successfully repaired")

            # we will evaluate (and through messages), if user stopped it or there was an exception
            # we will ask user if he/she wants to continue further and will act accordngly
            if not win.evaluate_async_outcome(event):
                if not messagebox.askyesno("Confirm", "Generating previews for already transfered files?"):
                    _step_5(src_ar, ar, win)
                    return

            preview_schedule = [
                PreviewJob(identity=stack.identity,) 
                for stack in ar._catalog.values() if stack.nopreview
            ]

            # get back the original archive.
            src_ar = async_res.event_args[0]

            # check if we have any previews to be generated. If not, we are done
            if len(preview_schedule) <= 0:
                _step_5(src_ar, ar, win)
                return

            logwriter.info(f"Going for preview generation")

            # let us create the preview files in batch
            # we wll once again create a multi-process shared list of stacks
            # and allow the child processes to make real changes here
            # this will not modify our src_ar in anyways
            mp_catalog = win.manager.dict()
            for k, v in ar._catalog.items():
                mp_catalog[k] = v

            # let us fire a multi-process pool to generate preview images
            # in batch. all new low_files created will be added to the temporary catalog
            # keeping source archive unaffected; meet you agaiin at _step_3
            static_args = (mp_catalog, str(ar.dir_by_type(FileType.LOW)))
            event_args = (src_ar, ar, mp_catalog,)
            win.exec_async(Archive._previews, static_args, preview_schedule, 
                "<<on_import_folder_step_4>>", _step_4, event_args)

            logwriter.info(f"Worker processes for preview generation launched")

        # physical file transfer
        # if user cancels, do nothng and return
        def _step_2(event):
            async_res = event.payload
            win = AsyncProxy()

            logwriter.info(f"Archive.import() _step_2")

            # first deactivate the custom event was added in step_1 to bring us here 
            win.exit_async_session( event)
            win.reset_statusbar()

            # get back the source archive we transmtted via event payload
            # from step_1; also create a temp archive with the same root
            # as our original archive. Hence forth we will do all modifications
            # on ths temporary archive and finally clone it back to the source
            src_ar = async_res.event_args[0]

            # we will evaluate (and through messages) but will not do anything much
            # as we were working on a copy. we will unlock the original archive and return
            if not win.evaluate_async_outcome(event):
                src_ar.unlock()
                return

            ar = Archive()
            ar._root = src_ar._root

            # copy the list of stacks that we shared with the child processes
            # to our new temporary archive. It has all the collating movements
            mp_catalog = async_res.event_args[1]
            for k, v in mp_catalog.items():
                ar._catalog[k] = v

            # we don't need this shared list any more as we have copied its
            # content to our temporary archive (ar)
            mp_catalog.clear()

            # clean it up. delete any file from the stack where the original files
            # like the Big RAWs or JPEGs were not found and we only have the preview
            for st in ar.as_list():
                if st.orphan or st.empty:
                    del ar._catalog[st.identity]

            # now let us try to identify all the files that were added as part 
            # of collation. We will try to look up every file from the temp archive,
            # which hold the stacks from the shared list that the child processes modified
            # in step_1 and see if we have a similar fle in our original archive. If 
            # the file is not found in the original archive OR the original archive has
            # an older version of the file (timestamp?) then we will believe that these files 
            # were added by the collation process
            f_list = []
            for new_f in ar.files:
                old_f = src_ar.find(new_f.identity, new_f.type)
                if old_f is None or new_f.mtime > old_f.mtime:
                    f_list.append(new_f)

            # don't proceed unless we really have something to do; and always ask the user
            # because this can initiate many GBs of file transfer taking long hours
            accepted = len(f_list)

            # no point moving any further
            if accepted <= 0: 
                messagebox.showinfo("Information", f"No new or updated files found to import.")
                src_ar.unlock()
                return

            logwriter.info(f"New or updated files found")

            # warn the user; file transfers can be lengthy depending on size and number of files
            if not messagebox.askyesno("Confirmation", 
                f"Total {accepted} files will be copied to this archive folder. Proceed?"):
                src_ar.unlock()
                return

            logwriter.info(f"User confirmation obtained")

            # let us create a copy schedue. We will copy the files and not move, just to be safe
            copy_schedule = []
            for f in f_list:
                dst = ar.dir_by_type(f.type) / f.legit_name
                if str(f) != str(dst):
                    copy_schedule.append(FileOpsJob(source= str(f), destination= str(dst), 
                        size= 0, command= FileOps.Copy))

            # FIre the multi-process mechanism. start physically copying the files
            # meet again on step_3 and we will carry forward our src_ar and ar along with us
            # to the next step
            event_args = (src_ar, ar,)
            win.exec_async(Archive._fileops, None, copy_schedule, 
                "<<on_import_folder_step_3>>", _step_3, event_args)

            logwriter.info(f"Worker processes for fileops launched")

        # collation
        def _step_1(src_ar, files):
            win = AsyncProxy()

            # clean the status bar
            win.reset_statusbar()

            logwriter.info(f"Archive.import._step_1")

            # if the length of the list is zero, it means we have no image file n the folder
            # inform user and return
            if len(files) <= 0: 
                messagebox.showinfo("Empty Folder", f"No images found. Nothing to import.")
                src_ar.unlock()
                return

            # create a list of collate jobs
            collate_schedule = [CollateJob(source= f,) for f in files]

            # we wll also create a multi-process shared list of stacks
            # and allow the child processes to make real changes here
            # this will not modify our src_ar in anyways
            mp_catalog = win.manager.dict()
            for k, v in src_ar._catalog.items():
                mp_catalog[k] = v

            # let us fire a multi-process pool to process the collate 
            # schedule as quickly as possible. After this process the shared 
            # list of stack will be modified, still keeping the original
            # source archive unaffected; meet you agaiin at _step_2
            static_args = (mp_catalog,)
            event_args = (src_ar, mp_catalog,)
            win.exec_async(Archive._collate, static_args, collate_schedule, 
                "<<on_import_folder_step_2>>", _step_2, event_args)

            logwriter.info(f"Worker processes for collation launched.")

        # convert folder to files
        def _step_0(src_ar, folder):
            win = AsyncProxy()

            # clean the status bar
            win.reset_statusbar()

            # Singleton configuration object
            cfg = Config()

            logwriter.info(f"Archive.import._step_0")

            # validate it is a legitimate folder
            p = Path(folder)
            if not p.exists() or not p.is_dir():
                messagebox.showinfo("Requested path not found or not a folder.")
                src_ar.unlock()
                return

            logwriter.info(f"Folder path valid")

            # get only image files from the folder
            files = [str(f) for f in p.iterdir() if (f.is_file() and (f.suffix.lower() in cfg.img_ext))]

            # if the length of the list is zero, it means we have no image file n the folder
            # inform user and return
            if len(files) <= 0: 
                messagebox.showinfo("Empty Folder", f"No images found. Nothing to import.")
                src_ar.unlock()
                return

            logwriter.info(f"Found files to import")

            # now we know maxmum number of files which may become part of the 
            # archive. Note that, not all files are going to be added, because 
            # some fles may already be part of the archive or we already have a 
            # more recent version of the same file. But we will let the user know
            # this number anyways
            response = messagebox.askyesno("Confirm", f"{len(files)} images found. This may take a while. Proceed?")
            if not response:
                src_ar.unlock()
                return

            logwriter.info(f"User confirmation obtained")

            # time to move on the next step for the real action
            _step_1(src_ar, files)

        assert self.root is not None, "Archive::import_folder() - archive src_ar has no root"

        # lock the source archive so that it does not get modified
        # in the thumbnal view while we contnue processing it.
        # The values are still not alteredin the origincal archive
        # it is just a precautonary step
        self.lock()

        # if we are given a lis of files, skip _step_0 and 
        # directly go to _step_1
        if isinstance(folder, list):
            _step_1(self, folder)

        # if we are given a folder path, go to _step_0 to 
        # get the list of files first
        elif isinstance(folder, str):
            _step_0(self, folder)

        # wrong argument type
        else:
            assert False, "Archive::import_folder() - argument can only be a string (path) or a list (of file paths))"

    # deletes RAW and JPG file if the corresponding preview is rejected
    # multiprocess - multistep
    def cull(self) -> None:
        def _step_2(event):
            logwriter.info(f"Started _step_2")
            async_res = event.payload

            # deactivate the event that brought us here
            win = AsyncProxy()
            win.exit_async_session(event)

            # clean the status bar
            win.reset_statusbar()

            # get back the source archive
            src_ar = async_res.event_args[0]

            # repair the temporary archive. If we cannot find a file there
            # it means we deleted it through cullng. f some files were not removed
            # during culling because of anyreason (like netwrk or hardware failure)
            # or may be user canceled midway, it will stay
            ar = async_res.event_args[1]
            ar.repair(remove_missing=True)

            logwriter.info(f"Archive successfully repaired")

            # clone the temporary archive back to the original archive
            # and we are almost done
            src_ar = ar.clone()
            src_ar.save()

            # we will evaluate (and through messages) but will not do anything much
            # as our repair function would have taken care of any missing file(s)
            win.evaluate_async_outcome(event)

            # fnally unlock the source archive
            src_ar.unlock()

            # if not win.evaluate_multiprocess_event_outcome(event):
            #     return

            logwriter.info(f"Cullng complete")

            # let the world know so that they can reload the document
            win.event_queue.put(("RELOAD_DOCUMENT", True))

        def _step_1(src_ar):
            win = AsyncProxy()

            # clean the status bar
            win.reset_statusbar()

            # first of all let us save the source document
            src_ar.save()

            # and we will work on a cloned copy without touching the original
            ar = src_ar.clone()

            # let us prepare a list of file we think we have to delete
            to_delete_files = []
            to_delete = [stack for stack in ar.as_list() if stack.low is None or stack.rejected]
            for stack in to_delete:
                to_delete_files.extend(stack.files)

            # we will not proceed if we don't have anything to do
            if len(to_delete_files) <= 0:
                messagebox.showinfo("Cull", f"No images found to be culled.")
                self.unlock()
                return

            logwriter.info(f"Number of files to remove => {len(to_delete_files)}")

            # warn the user that these fles will be removed from archive and also be 
            # removed from their current folder to bin folder
            if not messagebox.askyesno("Confirmation", 
                f"Total {len(to_delete)} sets containing {len(to_delete_files)} files to be deleted. Proceed?"):
                self.unlock()
                return

            logwriter.info(f"User confirmation received")

            # from the list of files we think we have to delete, let us prepare a cull schedule
            # previes will not be moved to bin, it will be physically deleted instead
            cull_schedule = [FileOpsJob(source = str(file), destination = ar.bin_dir_by_type(file.type),
                command = FileOps.Delete if file.type == FileType.LOW else FileOps.Move, size = 0)
                for file in to_delete_files]

            # launch a multi-process pool to delete / remove files as quickly as possible
            event_args = (src_ar, ar,)
            win.exec_async(Archive._fileops, None, cull_schedule, 
                "<<on_cull_step_2>>", _step_2, event_args)

            logwriter.info(f"Worker processes launched. onward to _step_2")

        assert self.root is not None, "Archive::cull() - archive src_ar has no root"

        # lock the source archive so that it does not get modified
        # in the thumbnal view while we contnue processing it.
        # The values are still not alteredin the origincal archive
        # it is just a precautonary step
        self.lock()

        # let us get into action
        logwriter.info(f"Started culling")
        _step_1(self)

    # refreshes metadata (exif data) from RAW and JPG files
    # multiprocess - multistep
    def refresh_metadata(self) -> None:
        def _step_2(event):
            async_res = event.payload

            # deactivate the event that brought us here
            win = AsyncProxy()
            win.exit_async_session(event)

            # copy the values from teh sared list to our source archive
            src_ar = async_res.event_args[0]
            mp_catalog = async_res.event_args[1]
            for k, v in mp_catalog.items():
                src_ar._catalog[k] = v

            # we will evaluate (and through messages) but will not do anything much
            # as our repair function would have taken care of any missing file(s)
            win.evaluate_async_outcome(event)

            # save the archive and unlock
            src_ar.save()
            src_ar.unlock()

            # some small cleanup
            mp_catalog.clear()

            logwriter.info(f"Refresh metadata completed")

            # let the world know to reload the document
            win.event_queue.put(("RELOAD_DOCUMENT", True))

        def _step_1(src_ar):
            win = AsyncProxy()

            # get a list of stacks where there is no metadata
            extract_schedule = [
                MetadataJob(identity= stack.identity,) 
                for stack in src_ar._catalog.values() 
            ]

            if len(extract_schedule) <= 0:
                src_ar.unlock()
                win.reset_statusbar()
                return

            logwriter.info(f"refresh_metadata._step_1 has no extract schedule")

            # like import_folder, we will create a shared catalog
            # copy existing values from the source to this catalog
            # and let the child processes play with it
            mp_catalog = win.manager.dict()
            for k, v in src_ar._catalog.items():
                mp_catalog[k] = v

            # launch a multi-process pool to get the metadata
            static_args = (mp_catalog,)
            event_args = (src_ar, mp_catalog,)
            win.exec_async(Archive._metadata, static_args, extract_schedule, 
                "<<on_refresh_metadata_step_2>>", _step_2, event_args)

            logwriter.info(f"Worker processes to extract metadata laucnhed")

        assert self.root is not None, "Archive::buld_previews() - archive src_ar has no root"

        # lock the source archive so that it does not get modified
        # in the thumbnal view while we contnue processing it.
        # The values are still not alteredin the origincal archive
        # it is just a precautonary step
        self.lock()

        logwriter.info(f"Refreshing metadata")

        # time for action
        _step_1(self)

   # build / rebuild preview images frrom JPG or RAW files
    # multiprocess - multistep
    def rebuild_previews(self, stacks: list) -> None:
        def _step_2(event):
            async_res = event.payload

            # deactivate the event that brought us here
            win = AsyncProxy()
            win.exit_async_session(event)

            # copy the values from teh sared list to our source archive
            src_ar = async_res.event_args[0]

            # copy the list of stacks that we shared with the child processes
            # to our source archive. It has all the new low files added
            mp_catalog = async_res.event_args[1]
            for k, v in mp_catalog.items():
                src_ar._catalog[k] = v
        
            src_ar.repair()

            # we will evaluate (and through messages) but will not do anything much
            # as our repair function would have taken care of any missing file(s)
            win.evaluate_async_outcome(event)

            # save the archive and unlock
            src_ar.save()
            src_ar.unlock()

            # some small cleanup
            mp_catalog.clear()

            logwriter.info(f"Preview generation completed")

            # let the world know to reload the document
            win.post_event("RELOAD_DOCUMENT", True)
            
        def _step_1(src_ar, stacks):
            win = AsyncProxy()

            # get a list of stacks where there is no metadata
            preview_schedule = [
                PreviewJob(identity= stack.identity,) 
                for stack in stacks 
            ]

            # like import_folder, we will create a shared catalog
            # copy existing values from the source to this catalog
            # and let the child processes play with it
            mp_catalog = win.manager.dict()
            for stack in stacks:
                mp_catalog[stack.identity] = stack

            # launch a multi-process pool to get the metadata
            static_args = (mp_catalog, src_ar.dir_by_type(FileType.LOW))
            event_args = (src_ar, mp_catalog,)
            win.exec_async(Archive._previews, static_args, preview_schedule, 
                "<<on_rebuild_previews_step_2>>", _step_2, event_args)

            logwriter.info(f"Worker processes for preview generation launched")

        assert self.root is not None, "Archive::build_previews() - archive src_ar has no root"
        assert stacks is not None, "Archive::build_previews() - provided stack list is None"

        if len(stacks) <= 0:
            return       

        logwriter.info(f"Refreshing metadata and rebuilding previews")

        self.lock()

        _step_1(self, stacks)

    # used for debugging. prints the inner contents on stdout
    def print(self) -> None:
        print("\n")
        print(self.name)
        for entry in self._catalog.values():
            entry.print(prefix="  ")

    # returns set of filters to be used by Filter Dialog
    # and thumbnailgrid view
    def get_filters(self) -> list:
        # get list of metadata
        filters = Config().metadata_filters

        # for every filter in filterset, find the unique values
        # and add it to the values list
        for filter in filters:
            filter.values.extend(self._find_unique_filter_values(filter))

        return filters

    # copy raf files to Archive\2-tif folder
    def copy_files(self, stacks: list, ftype: FileType, dest: str) -> None:
        def _step_1(event):
            async_res = event.payload
            win = AsyncProxy()

            logwriter.info(f"Archive.copy_rafs_for_edit() _step_2")

            # first deactivate the custom event was added in step_1 to bring us here 
            win.exit_async_session( event)
            win.reset_statusbar()

            # get back the source archive we transmtted via event payload
            # from step_1; also create a temp archive with the same root
            # as our original archive. Hence forth we will do all modifications
            # on ths temporary archive and finally clone it back to the source
            ar = async_res.event_args[0]
            ar.unlock()

            n = async_res.event_args[1]
            ftype = async_res.event_args[2]

            if ftype != FileType.RAW:
                messagebox.showinfo("Copy Complete", f"{n} images copied.")
                return

            cfg = Config()
            xrawstudio = cfg.xrawstudio_path
            current_os = platform.system()

            # if we are on windows, xrawstudio path is given and it is a valid path
            # we shall open the xrawstudio; otherwise inform the user that we succeded
            # copying the required files

            if current_os != "Windows" or xrawstudio is None or not xrawstudio.exists():
                messagebox.showinfo("Copy Complete", f"{n} raw images copied.")
                return

            if not messagebox.askyesno("Copy Complete", f"{n} raw images copied. Would you like to open Fujifilm X Raw Studio and start editing?"):
                return

            script_path = cfg.asset_path / "xrawstudio.ps1"
            subprocess.Popen(
                [
                    "powershell.exe", 
                    "-NoProfile", 
                    "-ExecutionPolicy", "Bypass", 
                    "-File", 
                    script_path,
                    dest,
                    str(xrawstudio)
                ],
                stdout=None,  # Handled by OS, does not block Python
                stderr=None
            )

        def _step_0(self, stacks, ftype, dest):
            win = AsyncProxy()

            # get files from the stack
            files = []
            if ftype == FileType.RAW:
                files = [str(s.raw) for s in stacks if s.raw]
            elif ftype == FileType.JPG:
                files = [str(s.jpg) for s in stacks if s.jpg]
            elif ftype == FileType.LOW:
                files = [str(s.low) for s in stacks if s.low]
            else:
                return
        
            # if the length of the list is zero, it means we have no image file n the folder
            # inform user and return
            if len(files) <= 0: 
                messagebox.showinfo("No Files", f"No images found to be copied.")
                return

            # let us create a copy schedue. We will copy the files and not move, just to be safe
            copy_schedule = []
            for f in files:
                dst = Path(dest) / Path(f).name
                if str(f) != str(dst):
                    copy_schedule.append(FileOpsJob(source= str(f), destination= str(dst), 
                        size= 0, command= FileOps.Copy))

            if len(copy_schedule) <= 0:
                messagebox.showinfo("No Files", f"No images found to be copied.")
                return

            # lock the source archive so that it does not get modified
            # in the thumbnal view while we contnue processing it.
            # The values are still not alteredin the origincal archive
            # it is just a precautonary step
            self.lock()

            # FIre the multi-process mechanism. start physically copying the files
            # meet again on step_3 and we will carry forward our src_ar and ar along with us
            # to the next step
            event_args = (self, len(copy_schedule), ftype)
            win.exec_async(Archive._fileops, None, copy_schedule, 
                "<<on_copy_rafs_for_edit_step_1>>", _step_1, event_args)

            logwriter.info(f"Worker processes for fileops launched")

        assert self.root is not None, "Archive::import_folder() - archive src_ar has no root"

        # first find out that we have a valid list
        # else return
        if stacks is not None and len(stacks) > 0:
            _step_0(self, stacks, ftype, dest)

# endregion

# region (private methods)

    def _find_unique_filter_values(self, filter: Any) -> list:
        unique_values = set()
        
        # fnd the attribyte value (property) for all stacks
        # and build an unique set for them
        for stack in self.as_list():
            if hasattr(stack.metadata, filter.property):
                unique_values.add(getattr(stack.metadata, filter.property))

        # convert the set into a list and sort the list
        # based on whether it represents a numeric list or text / mixed list
        # the is_digit() won't work with floating numbers containing the '.'
        # character. so we will replace that with '' rght before is_digit() test
        # note, we shall replace exactly one '.' character as floating points
        # cannot have multiple '.' in t
        ls = list(unique_values)
        is_numeric_list = all(str(li).replace('.', '', 1).isdigit() for li in ls)

        # sort based on content type: numeric or mixed / string
        # we will also do a lower() comparison so that it does not changes based upon
        # uppercase and lowercase strings
        ls = sorted(ls, key=float) if is_numeric_list else sorted(ls, key=str.lower)

        # insert a dummy 'Any Camera' type value. This value to be ignores whoever
        # is using ths list. it represents that the particular filter is not set / used
        ls.insert(0, "Any " + filter.label)

        return ls

# endregion

# region(worker_functions)

    # worker function for copying, moving or deleting files
    # used in multiprocess
    @staticmethod
    def _fileops(async_ctrl: AsyncCtrlParams, batch: list) -> None:
        for job in batch:
            # check for user cancelation
            if async_ctrl.stopped():
                return

            desc = ""

            try:
                # switch on type of job command
                if job.command == FileOps.Copy: 
                    File.copy_to(job.source, job.destination)
                    desc = "Copying..."
                elif job.command == FileOps.Move: 
                    File.move_to(job.source, job.destination)
                    desc = "Moving..."
                elif job.command == FileOps.Delete: 
                    File.delete(job.source)
                    desc = "Deleting..."
            except:
                pass

            # ask the async ctrl to update the main window status bar
            async_ctrl.notify(desc, Path(job.source).name)

    # worker function for collating new files to their respective stacks
    # used in multiprocess
    @staticmethod
    def _collate(async_ctrl: AsyncCtrlParams, catalog: Any, batch: list) -> None:
        for job in batch:
            # check for user cancelation
            if async_ctrl.stopped():
                return

            try:
                # this is the most expensive operation as it will
                # extract metadatas from the file; check the File.__init__()
                fo = File(job.source)

                # see if we already have a stack matching this identity
                # this means, we already have raw / jpg or tiff file for this image
                stack = catalog.get(fo.identity, None)

                # if not, create a new stack
                if stack is None:
                    stack = Stack()

                # ask the stack to add this file to itself if it is found suitable.
                stack.add(fo)

                # add the stack basck to the catalog. This s important as this 
                # is a shared dict, unless we add it back, it won't update the catalog
                catalog[stack.identity] = stack
            except:
                # we must do an error logging here.
                pass

            # ask the async ctrl to update the main window status bar
            async_ctrl.notify("Collating...", Path(job.source).name)

    # worker function for extracting metadata from images; will update stack metadata
    # used in multiprocess
    @staticmethod
    def _metadata(async_ctrl: AsyncCtrlParams, mp_catalog: Any, batch: list) -> None:
        for job in batch:
            # check for user cancelation
            if async_ctrl.stopped():
                return

            # get the stack, ask for the exifdata. if it is not there 
            # it will laod and cache it
            stack = mp_catalog[job.identity]
            stack.exifread()
            mp_catalog[job.identity] = stack

            # ask the async ctrl to update the main window status bar
            async_ctrl.notify("Extracting...", 
                mp_catalog[job.identity].any.name)

    # worker function for generating previews from metadata and images
    # used in multiprocess
    @staticmethod
    def _previews(async_ctrl: AsyncCtrlParams, catalog: Any, dir: str, batch: list) -> None:
        for job in batch:
            try:
                # check for user cancelation
                if async_ctrl.stopped():
                    return

                # get the stack that we will work upon
                stack = catalog[job.identity]

                # if the stack has no jpg or raw file, skip
                if stack.jpg is None and stack.raw is None:
                    continue

                # prefer jpg over raw for preview generation
                f = stack.jpg if stack.jpg is not None else stack.raw

                # create an appropriate low_file name in low folder
                path = Path(dir) / f"{stack.identity}-LOW.JPG"

                # generate the preview file in low folder
                size = PreviewBuilder().generate_preview_file(source=str(f), 
                    destination=str(path), metadata=stack.exifread())

                # add the newly generated low_file to the stack and add the stack
                # back to the catalog
                bytestr = pickle.dumps(f)
                new_file = pickle.loads(bytestr)
                new_file._path = str(path)
                new_file._identity = stack.identity
                new_file._filetype = FileType.LOW
                new_file._file_size = size

                stack._low_file = new_file
                catalog[job.identity] = stack

                # ask the async ctrl to update the main window status bar
                async_ctrl.notify("Generating Preview...", f.name)
            except Exception as e:
                print(str(e))

# endregion
