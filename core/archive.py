# region(python_imports)

import logging
import pickle
import jsonpickle
from jsonpickle import tags
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
from core.util import FileOpsJob, MetadataJob, PreviewJob, CollateJob, JpegExportJob, JpegExportTemplate
from core.config import Config
from core.proxy import AsyncProxy, AsyncCtrlParams
from ui.messagebox import messagebox

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

import traceback

def _debug_assert_(condition, message):
    if condition: return True
    # Join the list into a single clean string
    # We slice [:-1] to exclude this line/function itself from the trace
    stack = '\n'.join(traceback.format_stack()[:-1])
    logwriter.debug(f"assert failed: {message}-{stack}")
    return False

# endregion

class Archive():

    CURRENT_VERSION = 3

    class Unpickler(jsonpickle.Unpickler):
        def __init__(self):
            super().__init__()
            self._schema = 0

        def _restore_object_instance_variables(self, obj, instance):
            if instance.__class__.__name__ == "Archive":
                state_dict = obj.get(tags.STATE)
                if isinstance(state_dict, dict):
                    self._schema = int(state_dict.get('_version'))

            if ( hasattr(instance, '__setstate__') and 
                not (instance.__class__.__name__ == "File" and self._schema < 3)):
                obj.setdefault(tags.STATE, {})

            return super()._restore_object_instance_variables(obj, instance)

# region(class_methods)

    def __init__(self):
        self._root = None
        self._catalog = {}
        self._last_saved_loc = None
        self._title = None
        self._description = None
        self._version = self.CURRENT_VERSION

    def __getstate__(self):
        state = self.__dict__.copy()

        if '_lock_count' in state: del state['_lock_count']
        if '_dirty' in state: del state['_dirty']

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        if not hasattr(self, '_title'): self._title = ''
        if not hasattr(self, '_description'): self._description = ''
        if not hasattr(self, '_lock_count'): self._lock_count = 0
        if not hasattr(self, '_dirty'): self._dirty = False

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

    @property
    def syspaths(self) -> list:
        return [self.raw_dir, self.tif_dir, self.jpg_dir,
            self.low_dir, self.bin_dir,]

# endregion

# region(methods)

    # returns the content of the archive as a list
    def as_list(self) -> list:
        return list(self._catalog.values()) if self._root is not None else []

    # returns the content of the archive as a sorted list by identity
    def as_list2(self) -> list:
        return sorted( (list(self._catalog.values()) if self._root is not None else [] ), key= lambda stack: stack.identity)

    # search for a file based on identity and type
    def find(self, identity: str, type: FileType) -> File | None:
        if not _debug_assert_(( self._root is not None),
            "Archive.find() - root is none"): return
        stack = self._catalog.get(identity, None)
        if stack is not None:
            return stack.find(type)
        return None

    # returns set of filters to be used by Filter Dialog
    # and thumbnailgrid view
    def get_filters(self) -> list:
        if not _debug_assert_(( self._root is not None),
            "Archive.get_filters() - root is none"): return
        
        # get list of metadata
        filters = Config().metadata_filters

        # for every filter in filterset, find the unique values
        # and add it to the values list
        for filter in filters:
            filter.values.extend(self._find_unique_filter_values(filter))

        return filters

    # locks the current archive for any content changing processes
    def lock(self) -> None:
        if self._lock_count > 0:
            return False

        self._lock_count = 1
        return True

    # unlocks the current archive locked by a previous operation
    def unlock(self) -> None:
        self._lock_count = 0

    # clones the current archive definition to a new file.
    # it does not do anything with the actual mage files
    def clone(self) -> Self:
        if not _debug_assert_(( self._root is not None),
            "Archive.clone() - root is none"): return

        bytestr = pickle.dumps(self)
        return pickle.loads(bytestr)

    @staticmethod
    # creates a new archive at the give folder
    def new(base: str) -> Self:
        path = Path(base).resolve()
        if not _debug_assert_(( path.exists() and path.is_dir()),
            "Archive.new() - path not found or not a folder"): return

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
        messages = []

        try:
            with open(file_name, "r") as f:
                ar = jsonpickle.decode(f.read(), context=Archive.Unpickler())
            ar._last_saved_loc = file_name
            return ar

        except Exception as e:
            logwriter.error(f"Error occurred opening archive: {e}")
            messages.append(str(e)) 

        logwriter.warning("Archive.open - Attempting to open in legacy mode")

        try:
            with open(file_name, 'rb') as f:
                ar = pickle.load(f)
            ar.unlock()
            ar._last_saved_loc = file_name
            # we are converting the archive here from legacy binary mode
            # to the new json mode. Hence we will save it again in the new format
            ar.save()
            return ar
        
        except Exception as e:
            logwriter.error(f"Attempted to open the archive in legacy mode. Still got error: {e}")
            messages.append(str(e))

        raise Exception("\n".join(messages))

    # closes the current archive
    def close(self) -> None:
        self._root = None
        self._catalog.clear()
        self.lock()

    # saves the current archive. also works as "save as"
    def save(self, save_as: str =None) -> None:
        if not _debug_assert_(( self._root is not None),
            "Archive.save() - root is none"): return     

        # This is important; if the users loads a version and just saves it back
        # it retained the original version, which was wrong
        self._version = Archive.CURRENT_VERSION

        # we are given a file name, we will use that
        if save_as is not None:
            self._last_saved_loc = save_as

        # if we find that our last saved location, which can be 
        # a case because during the creation of a new archive we force it to save
        # for the first time, we will use a default archive name
        if self._last_saved_loc is None:
            self._last_saved_loc = self._root / f"{Config().appname}.far"

        self.unlock()
        self.dirty = False

        # after saving the document, we will reopen it
        # with open(self._last_saved_loc, 'wb') as f:
        #     pickle.dump(self, f)

        frozen_json = jsonpickle.encode(self)
        with open(self._last_saved_loc, "w") as f:
            f.write(frozen_json)

    # backs up current archive to a different file
    def backup(self) -> None:
        if not _debug_assert_(( self._root is not None),
            "Archive.backup() - root is none"): return

        # construct a backup file name and path
        p = Path(self._last_saved_loc)
        backup_file_name = f"{p.stem}-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}{p.suffix}"
        backup_file = p.parent / backup_file_name

        # clone the current archive and remove any lock
        ar = self.clone()
        ar.unlock()

        # save the cloned archive
        # with open(backup_file, 'wb') as f:
        #     pickle.dump(ar, f)

        frozen_json = jsonpickle.encode(self)
        with open(backup_file, "w") as f:
            f.write(frozen_json)

    # move and repair the current archive to a new folder
    # and also checks and fixes integrity.
    def move(self, new_path: str, remove_missing: bool) -> None:
        if not _debug_assert_(( self._root is not None),
            "Archive.move() - root is none"): return

        # check that the new path that we are given is a valid path
        # and also a "folder"
        path = Path(new_path).resolve()
        if not _debug_assert_(( path.exists() and path.is_dir()),
            "Archive.move() - path not found or not a folder"): return

        # set this as new root path and try to repair
        self._root = path
        self.repair(remove_missing=True if remove_missing > 0 else False)

    # checks if the current archive has errors or integrity issue
    def check(self) -> None:
        if not _debug_assert_(( self._root is not None),
            "Archive.check() - root is none"): return

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
        if not _debug_assert_(( self._root is not None),
            "Archive.repair() - root is none"): return

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
        def _step_5():
            logwriter.debug(f"Entering Archive::import_folder._step_5()")
                            
            # we are done; finally we will copy our temporary archive, where we did
            # all the important work to the original archive; and save it too
            nonlocal mp_archive

            mp_archive.save()

            # we are done. we shall unlock the origical document
            self.unlock()
            logwriter.debug(f"Archive::import_folder._step_5() - archive unlocked")
            logwriter.info(f"Archive::import_folder._step_5() - Import process completed")

            # asking the thumbnail view, or whomsoever it may concern to 
            # reload the document
            win = AsyncProxy()
            win.event_queue.put(("RELOAD_DOCUMENT", True))

            logwriter.debug(f"Archive::import_folder._step_5() - document reloaded")

        # consolidate and repair
        # if user cancels, it has no effect as such
        def _step_4(event):
            logwriter.debug(f"Entering Archive::import_folder._step_4()")

            win = AsyncProxy()

            # as usual - stop the custom event first; we don't need it any more
            win.exit_async_session(event)
            win.reset_statusbar()

            # just for showing the message
            if not win.evaluate_async_outcome(event):
                logwriter.debug(f"Archive::import_folder._step_4() - there were issues during preview generation")

            # get back the temporary archive.
            nonlocal mp_archive

            # copy the list of stacks that we shared with the child processes
            # to our new temporary archive. It has all the new low files added
            nonlocal mp_catalog
            for k, v in mp_catalog.items():
                mp_archive._catalog[k] = v

            mp_catalog.clear()

            mp_archive.repair()
            logwriter.debug(f"Archive::import_folder._step_4() - shadow archive repaired")

            # we are done; finally we will copy our temporary archive, where we did
            # all the important work to the original archive; and save it too
            _step_5()

        # generate previews
        # if user cancels midway, confirm if he/she wants to proceed with preview generation
        # if yes, resume; if not, leave it as-is, jump to step 5 and return
        def _step_3(event):
            logwriter.debug(f"Entering Archive::import_folder._step_3()")

            win = AsyncProxy()
            win.exit_async_session(event)
            win.reset_statusbar()

            # get back the temporary archive.
            nonlocal mp_archive

            # try to repair the archive. It has all the files after collating
            # so if it cannot find any file, it means, the file was not physically copied
            # for some reason, whether user canceled it midway or a netwrok / hardware
            # issue occured during transfer; we will keep only those files that we 
            # could actually transfer
            mp_archive.repair(remove_missing=True)
            logwriter.debug(f"Archive::import_folder._step_3() - shadow archive repaired")

            # we will evaluate (and through messages), if user stopped it or there was an exception
            # we will ask user if he/she wants to continue further and will act accordngly
            if not win.evaluate_async_outcome(event):
                logwriter.debug(f"Archive::import_folder._step_3() - async outcome is False")
                return _step_5()

            preview_schedule = [
                PreviewJob(identity=stack.identity,) 
                for stack in mp_archive._catalog.values() if stack.nopreview
            ]

            nonlocal job_count
            job_count = len(preview_schedule)

            # check if we have any previews to be generated. If not, we are done
            if job_count <= 0:
                logwriter.debug(f"Archive::import_folder._step_3() - no preview to be generated.")
                return _step_5()

            logwriter.debug(f"Archive::import_folder._step_3() - {job_count} previews to be generated")

            # let us create the preview files in batch
            # we wll once again create a multi-process shared list of stacks
            # and allow the child processes to make real changes here
            # this will not modify our src_ar in anyways
            nonlocal mp_catalog

            mp_catalog.clear()
            for k, v in mp_archive._catalog.items():
                mp_catalog[k] = v

            cfg = Config()
            template = JpegExportTemplate(
                export_path = str(mp_archive.dir_by_type(FileType.LOW)),
                export_size = cfg.preview_size,
                export_quality = 90,
                border_size = cfg.border_ratio,
                border_color = cfg.border_color,
                border_exif = 1
            )

            # let us fire a multi-process pool to generate preview images
            # in batch. all new low_files created will be added to the temporary catalog
            # keeping source archive unaffected; meet you agaiin at _step_3
            static_args = (mp_catalog, template)
            win.exec_async(Archive._previews, static_args, preview_schedule, 
                "<<on_import_folder_step_4>>", _step_4, None)

            logwriter.debug(f"Archive::import_folder._step_3() - previews generation processes launched")

        # physical file transfer
        # if user cancels, do nothng and return
        def _step_2(event):
            logwriter.debug(f"Entering Archive::import_folder._step_2()")

            win = AsyncProxy()
            win.exit_async_session( event)
            win.reset_statusbar()

            # we will evaluate (and through messages) but will not do anything much
            # as we were working on a copy. we will unlock the original archive and return
            if not win.evaluate_async_outcome(event):
                logwriter.debug(f"Archive::import_folder._step_2() - async outcome is False")
                self.unlock()
                return

            nonlocal mp_archive

            mp_archive = self.clone()
            mp_archive.unlock()
            mp_archive._catalog.clear()

            # copy the list of stacks that we shared with the child processes
            # to our new temporary archive. It has all the collating movements
            nonlocal mp_catalog

            for k, v in mp_catalog.items():
                mp_archive._catalog[k] = v

            # we don't need this shared list any more as we have copied its
            # content to our temporary archive (ar)
            mp_catalog.clear()

            # clean it up. delete any file from the stack where the original files
            # like the Big RAWs or JPEGs were not found and we only have the preview
            for st in mp_archive.as_list():
                if st.orphan or st.empty:
                    del mp_archive._catalog[st.identity]

            # now let us try to identify all the files that were added as part 
            # of collation. We will try to look up every file from the temp archive,
            # which hold the stacks from the shared list that the child processes modified
            # in step_1 and see if we have a similar fle in our original archive. If 
            # the file is not found in the original archive OR the original archive has
            # an older version of the file (timestamp?) then we will believe that these files 
            # were added by the collation process
            f_list = []
            for new_f in mp_archive.files:
                old_f = self.find(new_f.identity, new_f.type)
                if old_f is None or new_f.mtime > old_f.mtime:
                    f_list.append(new_f)

            # don't proceed unless we really have something to do; and always ask the user
            # because this can initiate many GBs of file transfer taking long hours
            nonlocal job_count
            job_count = len(f_list)

            # no point moving any further
            if job_count <= 0: 
                logwriter.debug(f"Archive::import_folder._step_2() - no new files to import")
                messagebox.showinfo("Information", f"No new or updated files found to import.")
                self.unlock()
                return

            logwriter.debug(f"Archive::import_folder._step_1() - {job_count} files to import")

            # warn the user; file transfers can be lengthy depending on size and number of files
            if not messagebox.askyesno("Confirmation", 
                f"Total {job_count} files will be copied to this archive folder. Proceed?"):
                logwriter.debug(f"Archive::import_folder._step_2() - user declined to proceed further")
                self.unlock()
                return

            # let us create a copy schedue. We will copy the files and not move, just to be safe
            copy_schedule = []
            for f in f_list:
                dst = mp_archive.dir_by_type(f.type) / f.legit_name
                if str(f) != str(dst):
                    copy_schedule.append(FileOpsJob(source= str(f), destination= str(dst), 
                        size= 0, command= FileOps.Copy))

            # FIre the multi-process mechanism. start physically copying the files
            # meet again on step_3 and we will carry forward our src_ar and ar along with us
            # to the next step
            win.exec_async(Archive._fileops, None, copy_schedule, 
                "<<on_import_folder_step_3>>", _step_3, None)

            logwriter.debug(f"Archive::import_folder._step_2() - file copy processes launched")

        # collation
        def _step_1(files):
            logwriter.debug(f"Entering Archive.import._step_1()")

            win = AsyncProxy()
            win.reset_statusbar()

            # if the length of the list is zero, it means we have no image file n the folder
            # inform user and return
            if len(files) <= 0: 
                logwriter.debug(f"Archive::import_folder._step_1() - no files to import")
                messagebox.showinfo("Empty Folder", f"No images found. Nothing to import.")
                return

            # lock the source archive so that it does not get modified
            # in the thumbnal view while we contnue processing it.
            # The values are still not alteredin the origincal archive
            # it is just a precautonary step
            if not self.lock():
                logwriter.debug(f"Archive::import_folder._step_1() - failed to lock the archive")
                return

            # create a list of collate jobs
            collate_schedule = [CollateJob(source= f,) for f in files]

            # we wll also create a multi-process shared list of stacks
            # and allow the child processes to make real changes here
            # this will not modify our src_ar in anyways
            nonlocal mp_catalog
            mp_catalog = win.manager.dict()
            for k, v in self._catalog.items():
                mp_catalog[k] = v

            # let us fire a multi-process pool to process the collate 
            # schedule as quickly as possible. After this process the shared 
            # list of stack will be modified, still keeping the original
            # source archive unaffected; meet you agaiin at _step_2
            static_args = (mp_catalog,)
            win.exec_async(Archive._collate, static_args, collate_schedule, 
                "<<on_import_folder_step_2>>", _step_2, None)

            logwriter.debug(f"Archive::import_folder._step_1() - collate jobs launched")

        # convert folder to files
        def _step_0(folder):
            logwriter.debug(f"Entering Archive.import._step_0()")
            win = AsyncProxy()

            # clean the status bar
            win.reset_statusbar()

            # Singleton configuration object
            cfg = Config()

            # validate it is a legitimate folder
            p = Path(folder)
            if not p.exists() or not p.is_dir():
                logwriter.debug(f"Archive::import_folder._step_0() - folder path is invalid or not a folder")
                messagebox.showinfo("Requested path not found or not a folder.")
                return

            logwriter.debug(f"Archive::import_folder._step_0() - folder path is valid")

            # get only image files from the folder
            files = [str(f) for f in p.iterdir() if (f.is_file() and (f.suffix.lower() in cfg.img_ext))]

            # if the length of the list is zero, it means we have no image file n the folder
            # inform user and return
            if len(files) <= 0: 
                logwriter.debug(f"Archive::import_folder._step_0() - no files to import")
                messagebox.showinfo("Empty Folder", f"No images found. Nothing to import.")
                return

            logwriter.info(f"Archive::import_folder) - {len(files)} files to import")

            # now we know maxmum number of files which may become part of the 
            # archive. Note that, not all files are going to be added, because 
            # some fles may already be part of the archive or we already have a 
            # more recent version of the same file. But we will let the user know
            # this number anyways
            if not  messagebox.askyesno("Confirm", f"{len(files)} images found. This may take a while. Proceed?"):
                return

            # time to move on the next step for the real action
            _step_1(files)

        if not _debug_assert_(( self._root is not None and self.ready),
            "Archive.import_folder() - root is none or busy"): return

        mp_archive = None
        mp_catalog = None
        job_count = 0

        # if we are given a lis of files, skip _step_0 and 
        # directly go to _step_1
        if isinstance(folder, list):
            logwriter.info(f"Archive::import_folder() - importing file(s)")
            _step_1(folder)

        # if we are given a folder path, go to _step_0 to 
        # get the list of files first
        elif isinstance(folder, str):
            logwriter.debug(f"Archive::import_folder() - importing folder => {folder}")
            _step_0(folder)

        # wrong argument type
        else:
            _debug_assert_(False,
                "Archive.import_folder() - argument can only be a string or a list")

    # deletes RAW and JPG file if the corresponding preview is rejected
    # multiprocess - multistep
    def cull(self) -> None:
        def _step_1(event):
            logwriter.debug(f"Entering Archive.cull._step_1()")

            # deactivate the event that brought us here
            win = AsyncProxy()
            win.exit_async_session(event)

            # clean the status bar
            win.reset_statusbar()

            # repair the temporary archive. If we cannot find a file there
            # it means we deleted it through cullng. f some files were not removed
            # during culling because of anyreason (like netwrk or hardware failure)
            # or may be user canceled midway, it will stay
            self.repair(remove_missing=True)
            self.save()

            # we will evaluate (and through messages) but will not do anything much
            # as our repair function would have taken care of any missing file(s)
            if not win.evaluate_async_outcome(event):
                logwriter.info(f"Archive.cull() did not complete successfully")

            logwriter.info(f"Archive.cull() - Cullng complete")

            # let the world know so that they can reload the document
            win.event_queue.put(("RELOAD_DOCUMENT", True))

        def _step_0():
            logwriter.debug(f"Entering Archive.cull._step_0()")

            win = AsyncProxy()

            # clean the status bar
            win.reset_statusbar()
            self.save()

            # let us prepare a list of file we think we have to delete
            to_delete_files = []
            to_delete = [stack for stack in self.as_list() if stack.low is None or stack.rejected]
            for stack in to_delete:
                to_delete_files.extend(stack.files)

            # we will not proceed if we don't have anything to do
            if len(to_delete_files) <= 0:
                logwriter.debug(f"Archive.cull._step_0() - no images found for culling")
                messagebox.showinfo("Cull", f"No images found to be culled.")
                return

            logwriter.info(f"Archive.cull() - {len(to_delete_files)} files to remove")

            # warn the user that these fles will be removed from archive and also be 
            # removed from their current folder to bin folder
            if not messagebox.askyesno("Confirmation", 
                f"Total {len(to_delete)} sets containing {len(to_delete_files)} files to be deleted. Proceed?"):
                return

            logwriter.debug(f"Archive.cull._step_0() - {len(to_delete)} sets containing {len(to_delete_files)} files to be deleted")

            if not self.lock():
                logwriter.debug(f"Archive::cull._step_0() - failed to lock the archive")
                return

            # from the list of files we think we have to delete, let us prepare a cull schedule
            # previes will not be moved to bin, it will be physically deleted instead
            cull_schedule = [FileOpsJob(source = str(file), destination = self.bin_dir_by_type(file.type),
                command = FileOps.Delete if file.type == FileType.LOW else FileOps.Move, size = 0)
                for file in to_delete_files]

            # launch a multi-process pool to delete / remove files as quickly as possible
            win.exec_async(Archive._fileops, None, cull_schedule, 
                "<<on_cull_step_2>>", _step_1, None)

            logwriter.debug(f"Archive.cull._step_0() - fileops processes launched")

        if not _debug_assert_(( self._root is not None and self.ready),
            "Archive.cull() - root is none or busy"): return

        logwriter.info(f"Archive.cull() - initiated")

        _step_0()

    # build / rebuild preview images frrom JPG or RAW files
    # multiprocess - multistep
    def rebuild_previews(self, stacks: list) -> None:
        def _step_1(event):
            logwriter.debug(f"Entering Archive.rebuild_previews._step_1()")

            # deactivate the event that brought us here
            win = AsyncProxy()
            win.exit_async_session(event)

            # copy the list of stacks that we shared with the child processes
            # to our source archive. It has all the new low files added
            nonlocal mp_catalog
            for k, v in mp_catalog.items():
                self._catalog[k] = v

            self.repair(remove_missing=True)
            self.save()

            # some small cleanup
            mp_catalog.clear()

            if win.evaluate_async_outcome(event):
                nonlocal job_count
                logwriter.info(f"Archive.rebuild_previews() - {job_count} previews regenerated.")
                messagebox.showinfo("Success", f"Preview regeneration Complete. {job_count} previews regenerated.")
            else:
                logwriter.info(f"Archive.rebuild_previews() did not complete successfully")

            # let the world know to reload the document
            win.post_event("RELOAD_DOCUMENT", True)

        def _step_0():
            logwriter.debug(f"Entering Archive.rebuild_previews._step_0()")

            win = AsyncProxy()

            for stack in stacks:
                stack.exifread()

            # get a list of stacks where there is no metadata
            preview_schedule = [
                PreviewJob(identity= stack.identity,) 
                for stack in stacks 
            ]

            nonlocal job_count
            job_count = len(preview_schedule)
            
            if not self.lock():
                logwriter.debug(f"Archive::rebuild_previews._step_0() - failed to lock the archive")
                return

            # like import_folder, we will create a shared catalog
            # copy existing values from the source to this catalog
            # and let the child processes play with it
            nonlocal mp_catalog
            mp_catalog = win.manager.dict()

            for stack in stacks:
                mp_catalog[stack.identity] = stack

            cfg = Config()
            template = JpegExportTemplate(
                export_path = str(self.dir_by_type(FileType.LOW)),
                export_size = cfg.preview_size,
                export_quality = 90,
                border_size = cfg.border_ratio,
                border_color = cfg.border_color,
                border_exif = 1
            )

            # launch a multi-process pool to get the metadata
            static_args = (mp_catalog, template)
            win.exec_async(Archive._previews, static_args, preview_schedule, 
                "<<on_rebuild_previews_step_1>>", _step_1, None)

            logwriter.debug(f"Archive.rebuild_previews._step_0() - preview generation processes launched")

        if not _debug_assert_(( self._root is not None and self.ready),
            "Archive.rebuild_previews() - root is none or busy"): return

        if not _debug_assert_(( stacks is not None and len(stacks) > 0),
            "Archive.rebuild_previews() - argument stacks is either None or empty"): return

        logwriter.info(f"Archive.rebuild_previews() - initiated")

        mp_catalog = None
        job_count = 0

        _step_0()

    # copy raf files to Archive\2-tif folder
    def export_raws(self, stacks: list, dest: str) -> None:
        def _step_1(event):
            logwriter.debug(f"Entering Archive.export_raws._step_1()")

            win = AsyncProxy()

            # first deactivate the custom event was added in step_1 to bring us here 
            win.exit_async_session( event)
            win.reset_statusbar()

            self.unlock()

            nonlocal job_count
            
            logwriter.info(f"Archive.export_jpegs() - export complete. {job_count} images exported.")

            cfg = Config()
            xrawstudio = cfg.xrawstudio_path
            current_os = platform.system()

            # if we are on windows, xrawstudio path is given and it is a valid path
            # we shall open the xrawstudio; otherwise inform the user that we succeded
            # copying the required files

            if current_os != "Windows" or xrawstudio == "" or not Path(xrawstudio).exists():
                messagebox.showinfo("Success", f"Export Complete. {job_count} raw images exported.")
                return

            if not messagebox.askyesno("Success", f"Export Complete. {job_count} raw images exported. Would you like to open Fujifilm X Raw Studio and start editing?"):
                return

            logwriter.debug(f"Archive.export_raws._step_1() - attempting to launch FUJIFILM X-RAW STUDIO")

            script_path = cfg.asset_path / "xrawstudio.ps1"
            subprocess.Popen(
                [
                    "powershell.exe", 
                    "-NoProfile", 
                    "-ExecutionPolicy", "Bypass", 
                    "-File", 
                    script_path,
                    dest,
                    xrawstudio
                ],
                stdout=None,  # Handled by OS, does not block Python
                stderr=None
            )

        def _step_0():
            logwriter.debug(f"Entering Archive.export_raws._step_0()")

            win = AsyncProxy()

            # get files from the stack
            files = [str(s.raw) for s in stacks if s.raw]
        
            # if the length of the list is zero, it means we have no image file n the folder
            # inform user and return
            if len(files) <= 0: 
                logwriter.info(f"Archive.export_jpegs() No image file(s) to be exported.")
                messagebox.showinfo("No Files", f"No raw images found.")
                return

            # let us create a copy schedue. We will copy the files and not move, just to be safe
            copy_schedule = []
            for f in files:
                dst = Path(dest) / Path(f).name
                if str(f) != str(dst):
                    copy_schedule.append(FileOpsJob(source= str(f), destination= str(dst), 
                        size= 0, command= FileOps.Copy))

            nonlocal job_count
            job_count = len(copy_schedule)

            if job_count <= 0:
                logwriter.info(f"Archive.export_jpegs() - No image file(s) to be exported.")
                messagebox.showinfo("No Files", f"No raw images found to.")
                return

            logwriter.info(f"Archive.export_jpegs() - {job_count} images to be exported.")

            # lock the source archive so that it does not get modified
            # in the thumbnal view while we contnue processing it.
            # The values are still not alteredin the origincal archive
            # it is just a precautonary step
            if not self.lock():
                logwriter.debug(f"Archive::export_raws._step_0() - failed to lock the archive")
                return

            # Fire the multi-process mechanism. start physically copying the files
            # meet again on step_2 and we will carry forward our src_ar and ar along with us
            # to the next step
            win.exec_async(Archive._fileops, None, copy_schedule, 
                "<<on_export_raws_step_1>>", _step_1, None)

            logwriter.debug(f"Archive.export_jpegs._step_0() - export process launched.")

        if not _debug_assert_(( self._root is not None and self.ready),
            "Archive.export_raws() - root is none or busy"): return

        if not _debug_assert_(( stacks is not None and len(stacks) > 0),
            "Archive.export_raws() - argument stacks is either None or empty"): return

        logwriter.info(f"Archive.export_raws() initiated")

        job_count = 0

        _step_0()

    # Export Jpeg files as per user specifications
    def export_jpegs(self, stacks: list, template: JpegExportTemplate) -> None:
        def _step_1(event):
            win = AsyncProxy()

            logwriter.debug(f"Entering Archive.export_jpegs._step_2()")

            # first deactivate the custom event was added in step_1 to bring us here 
            win.exit_async_session(event)
            win.reset_statusbar()

            self.unlock()

            nonlocal job_count

            logwriter.info(f"Archive.export_jpegs() - export complete. {job_count} images exported.")
            messagebox.showinfo("Export Complete", f"{job_count} images exported.")

        def _step_0():
            win = AsyncProxy()

            # let us create a copy schedue. We will copy the files and not move, just to be safe
            export_schedule = []
            for stack in stacks:
                if stack.jpg is not None:
                    destination = Path(template.export_path) / f"{stack.identity}-{str(template.export_size)}.JPG"
                    export_schedule.append(JpegExportJob(source= str(stack.jpg), 
                        destination=str(destination), metadata=stack.metadata))

            nonlocal job_count
            job_count = len(export_schedule)

            if job_count <= 0:
                logwriter.info(f"Archive.export_jpegs() - No images to be exported")
                messagebox.showinfo("No Files", f"No images found to be exported.")
                return

            logwriter.info(f"Archive.export_jpegs() - {job_count} images to be exported")

            # lock the source archive so that it does not get modified
            # in the thumbnal view while we contnue processing it.
            # The values are still not alteredin the origincal archive
            # it is just a precautonary step
            if not self.lock():
                logwriter.debug(f"Archive::export_jpegs._step_0() - failed to lock the archive")
                return

            # FIre the multi-process mechanism. start physically copying the files
            # meet again on step_3 and we will carry forward our src_ar and ar along with us
            # to the next step
            static_args = (template,)
            win.exec_async(Archive._jpegexport, static_args, export_schedule, 
                "<<on_export_jpeg_step_1>>", _step_1, None)

            logwriter.debug(f"Archive.export_jpegs._step_0() - jpeg export processes launched")

        if not _debug_assert_(( self._root is not None and self.ready),
            "Archive.export_jpegs() - root is none or busy"): return

        if not _debug_assert_(( stacks is not None and len(stacks) > 0),
            "Archive.export_jpegs() - argument stacks is either None or empty"): return

        logwriter.info(f"Archive.export_jpegs() initiated")

        job_count = 0

        _step_0()

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

        if not self.ready:
            logwriter.debug(f"{func} - Archive is busy")
            return False
        return True

# endregion

# region(worker_functions)

    # worker function for copying, moving or deleting files
    # used in multiprocess
    @staticmethod
    def _fileops(async_ctrl: AsyncCtrlParams, batch: list) -> None:
        for job in batch:
            try:
                # check for user cancelation
                if async_ctrl.stopped():
                    return

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

                else:
                    desc = "Ignoring..."

                # ask the async ctrl to update the main window status bar
                async_ctrl.notify(desc, Path(job.source).name)
                    
            except Exception as e:
                logwriter.error(f"Exception in Archive._fileops: {str(e)}")

    # worker function for collating new files to their respective stacks
    # used in multiprocess
    @staticmethod
    def _collate(async_ctrl: AsyncCtrlParams, catalog: Any, batch: list) -> None:
        for job in batch:
            try:
                # check for user cancelation
                if async_ctrl.stopped():
                    return

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

                # ask the async ctrl to update the main window status bar
                async_ctrl.notify("Collating...", Path(job.source).name)

            except Exception as e:
                logwriter.error(f"Exception in Archive._collate: {str(e)}")

    # worker function for generating previews from metadata and images
    # used in multiprocess
    @staticmethod
    def _previews(async_ctrl: AsyncCtrlParams, catalog: Any, template: JpegExportTemplate, batch: list) -> None:
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
                destination = Path(template.export_path) / f"{stack.identity}-LOW.JPG"

                size = PreviewBuilder().export_jpeg(
                    source=str(f), 
                    destination=str(destination),
                    template=template, 
                    metadata=stack.metadata
                )

                # add the newly generated low_file to the stack and add the stack
                # back to the catalog
                bytestr = pickle.dumps(f)
                new_file = pickle.loads(bytestr)
                new_file._path = str(destination)
                new_file._identity = stack.identity
                new_file._filetype = FileType.LOW
                new_file._file_size = size

                stack._low_file = new_file
                catalog[job.identity] = stack

                # ask the async ctrl to update the main window status bar
                async_ctrl.notify("Generating Preview...", f.name)

            except Exception as e:
                logwriter.error(f"Exception in Archive._previews: {str(e)}")

    @staticmethod
    def _jpegexport(async_ctrl: AsyncCtrlParams, template: JpegExportTemplate, batch: list) -> None:
        for job in batch:
            try:
                # check for user cancelation
                if async_ctrl.stopped():
                    return

                PreviewBuilder().export_jpeg(
                    source=job.source, 
                    destination=job.destination, 
                    template=template, 
                    metadata=job.metadata
                )

                # ask the async ctrl to update the main window status bar
                async_ctrl.notify("Exporting...", Path(job.source).name)

            except Exception as e:
                logwriter.error(f"Exception in Archive._jpegexport: {str(e)}")

# endregion
