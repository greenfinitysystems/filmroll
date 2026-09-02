# region(python_imports)

import logging
import shutil
import exiv2
from pathlib import Path
from enum import Enum
from PIL import Image
from typing import Any

# endregion

# region(project_imports)

from core.metadata import Metadata
from core.fujifilm import FujifilmMetadata
from core.config import Config

# endregion

# region(enumerations)

class FileType(Enum):
    RAW = 1
    TIF = 2
    JPG = 3
    LOW = 4
    SIDECAR = 5

class FileOps(Enum):
    Copy = 1
    Move = 2
    Delete = 3

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

MAX_PREVIEW_SIZE = (2048 * 2048 * 1.21)

# endregion

class File:

# region(class_methods)

    def __init__(self, path: str):
        pathobj = Path(path).resolve()

        self._path = str(pathobj)
        self._identity = None
        self._image_size = 0
        self._filetype = None
        self._image_size = 0
        self._mtime = None
        self._file_size = -1

        if not pathobj.exists() or not pathobj.is_file():
            logwriter.warning(f"File not found or not a file. Throwing FileNotFoundError")
            raise FileNotFoundError("File not found or not a file")

        cfg = Config()

        if pathobj.suffix.lower() in cfg.raw_ext: self._filetype = FileType.RAW
        elif pathobj.suffix.lower() in cfg.jpg_ext: self._filetype = FileType.JPG
        elif pathobj.suffix.lower() in cfg.tif_ext: self._filetype = FileType.TIF
        else:
            logwriter.warning(f"Unsupported file extension {pathobj.suffix}. Throwing TypeError") 
            raise TypeError(f"Unsupported file type: {path}")

        try:
            image = exiv2.ImageFactory.open(str(pathobj))
            image.readMetadata()
            exif_data = image.exifData()
            camerabody_serial = (exif_data['Exif.Photo.BodySerialNumber']).value()
            datetime_original = str(exif_data['Exif.Photo.DateTimeOriginal'].value()).replace(':','').replace(' ','-')
            seqno = int(str(exif_data['Exif.Fujifilm.0x1101'].value()))
            sequence_number = f"-{seqno}" if seqno > 0 else ""
            self._identity = f"{camerabody_serial}-{datetime_original}{sequence_number}"

        except Exception as e:
            logwriter.warning(f"Unable to construct identity => {pathobj.name}") 
            logwriter.warning(str(e))
            raise Exception(f"File identity failed => {pathobj.name}")

        if self._filetype == FileType.JPG:
            with Image.open(str(pathobj)) as jpg_image:
                self._image_size = jpg_image.size[0] * jpg_image.size[1]

        global MAX_PREVIEW_SIZE
        if self._filetype == FileType.JPG and self._image_size <= MAX_PREVIEW_SIZE:
            self._filetype = FileType.LOW

    def __getattr__(self, name):
        if name == "_path":
            raise AttributeError(name)

        internal_path = self.__dict__.get("_path")       
        if internal_path is not None:
            return getattr(Path(internal_path), name)

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __fspath__(self):
        return str(Path(self._path))

    def __str__(self):
        return str(Path(self._path))

    def __truediv__(self, other):
        return Path(self._path) / other

# endregion

# region(properties)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def dir(self) -> str:
        return Path(self._path).parent.resolve()

    @property
    def legit_name(self) -> str:
        if self.type == FileType.LOW: l_name = (self.identity + '-LOW') + self.suffix
        else: l_name = (self.identity + self.suffix)
        return l_name

    @property
    def identity(self) -> str:
        return self._identity

    @property
    def type(self) -> FileType:
        return self._filetype

    @property
    def image_size(self) -> int:
        return self._image_size

    @property
    def file_size(self) -> int:
        if self._file_size < 0:
            self._file_size = Path(self._path).stat().st_size
        return self._file_size

    @property
    def mtime(self) -> float:
        if self._mtime is None:
            self._mtime = Path(self._path).stat().st_mtime
        return self._mtime

# endregion

# region(methods)

    def exists(self) -> bool:
        pathobj = Path(self._path)
        return (pathobj.exists() and pathobj.is_file())

    def migrate(self, value: Path) -> bool:
        new_dir = value.resolve()
        new_path = new_dir / self.legit_name

        if self._path == new_path:
            return True

        if not new_path.exists() or not new_path.is_file():
            logwriter.warning(f"Path {str(value)} not found or not a file.")
            return False

        self._path = str(new_path)
        return True

    def exifread(self) -> Any:
        try:
            image = exiv2.ImageFactory.open(self._path)
            image.readMetadata()
            exif_data = image.exifData()
            make = str(exif_data['Exif.Image.Make'].value())
            return FujifilmMetadata(exif_data) if make.lower()== "fujifilm" else Metadata(exif_data)

        except Exception as e:
            logwriter.warning(f"Exception occured while extracting metadata.")
            logwriter.warning(str(e))
            return None

    def print(self, prefix: str) -> None:
        def type_to_str(t):
            if t== FileType.RAW: return "RAW"
            if t== FileType.JPG: return "JPG"
            if t== FileType.LOW: return "LOW"
        print(prefix + f"[{type_to_str(self.type)}: {self.name}]")

    @staticmethod
    def copy_to(src: str, target: str) -> bool:
        src_path = Path(src)
        if not src_path.exists() or not src_path.is_file(): 
            logwriter.warning(f"Source not found => {str}.")
            return False

        dst_path = Path(target)
        if dst_path.exists() and dst_path.is_file() and (
            src_path.stat().st_mtime < dst_path.stat().st_mtime):
            logwriter.info(f"Destination is more recent. Refusing to overwrite.")
            return True

        try: 
            shutil.copy2(src, target)
            logwriter.info(f"Copy successful => {src} to {target}")

        except Exception as e:
            logwriter.warning(f"Exception occured iin shutil.copy2().") 
            logwriter.warning(str(e))
            return False

        return True

    @staticmethod
    def move_to(src: str, target: str) -> bool:
        src_path = Path(src)
        if not src_path.exists() or not src_path.is_file(): 
            logwriter.warning(f"Source not found or not a file.")
            return False

        dst_path = Path(target)
        if dst_path.is_dir() and not dst_path.exists():
            logwriter.warning(f"Destination folder does not exist {target}")
            return False

        # if the target file already exists in the destinaton folder 
        # shutil.move will throw a exception; giving the full path it doesn't
        tgt_path = dst_path
        if tgt_path.is_dir():
            tgt_path = dst_path / src_path.name

        try: 
            shutil.move(src, str(tgt_path))
            logwriter.info(f"Move successful => {src} to {target}")

        except Exception as e:
            logwriter.warning(f"Exception occured in shutil.move().") 
            logwriter.warning(str(e))
            return False

        return True

    @staticmethod
    def delete(src: str) -> bool:
        src_path = Path(src)
        if not src_path.exists() or not src_path.is_file(): 
            logwriter.warning(f"Source nonexistant or not a file.")
            return False

        try:
            src_path.unlink()
            logwriter.info(f"Delete successful => {src}")

        except Exception as e:
            logwriter.warning(f"Exception occured in Path.unlink().") 
            logwriter.warning(str(e))
            return False

        return True

# endregion

