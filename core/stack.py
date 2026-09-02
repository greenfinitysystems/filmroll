# region(python_imports)

import logging
import logging
from typing import Any

# endregion

# region(project_imports)

from core.file import File, FileType
from core.config import Config

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class Stack:

# region(class_methods)

    def __init__(self):
        self._raw_file = None
        self._jpg_file = None
        self._low_file = None
        self._tif_file = None
        self._metadata = None
        self._rejected = False

# endregion

# region(properties)

    @property
    def raw(self) -> File | None:
        return self._raw_file

    @property
    def jpg(self) -> File | None:
        return self._jpg_file

    @property
    def low(self) -> File | None:
        return self._low_file

    @property
    def tif(self) -> File | None:
        return self._tif_file

    @property
    def any(self) -> File | None:
        if self.low is not None: return self.low
        if self.jpg is not None: return self.jpg
        if self.raw is not None: return self.raw
        return None

    @property
    def identity(self) -> str | None:
        if self.any: return self.any.identity
        return None

    @property
    def metadata(self) -> Any | None:
        if self._metadata is None:
            self._metadata = self.exifread()
        return self._metadata

    @property
    def files(self) -> list:
        files = []
        if self.raw: files.append(self.raw)
        if self.jpg: files.append(self.jpg)
        if self.low: files.append(self.low)
        if self.tif: files.append(self.tif)
        return files

    @property
    def orphan(self) -> bool:
        return self.low is not None and (self.raw is None and self.jpg is None)

    @property
    def nopreview(self) -> bool:
        return (self.low is None)

    @property
    def empty(self) -> bool:
        return len(self.files) <= 0

    @property
    def rejected(self) -> bool:
        return self._rejected

    @rejected.setter
    def rejected(self, value: bool =True):
        self._rejected = value

# endregion

# region(methods)

    def find(self, type) -> File | None:
        if type == FileType.LOW: return self._low_file
        elif type == FileType.JPG: return self._jpg_file
        elif type == FileType.RAW: return self._raw_file
        elif type == FileType.TIF: return self._tif_file
        else: return None

    def add(self, value: File) -> None:
        if value.type not in (FileType.RAW, FileType.JPG, FileType.LOW, FileType.TIF):
            logwriter.warning(f"Unsupported FileType {value.name}. Throwing TypeError")
            raise TypeError("Unsupported file type")

        min_image_size = (640 * 480 * 1.21)
        if value.type == FileType.JPG and value.image_size <= min_image_size:
            logwriter.info(f"File {value.name} is too small. ignoring.")
            return

        if self.identity is not None and self.identity != value.identity:
            logwriter.warning(f"Identity mismatch. expected={self.identity}, got=>{value.identity}. Throwing Exception")
            raise Exception("Identity mismatch")

        if value.type == FileType.RAW:
            if self.raw is None: self._raw_file = value
            elif self.raw.mtime < value.mtime: self._raw_file = value

        elif value.type == FileType.TIF:
            if self.tif is None: self._tif_file = value
            elif self.tif.mtime < value.mtime: self._tif_file = value

        elif value.type == FileType.LOW:
            if self.low is None: self._low_file = value
            elif self.low.mtime < value.mtime: self._low_file = value

        elif value.type == FileType.JPG:
            if self.jpg is None: self._jpg_file = value
            elif self.jpg.mtime < value.mtime: self._jpg_file = value

        if self._raw_file == value or self._jpg_file == value or self._low_file == value:
            logwriter.info(f"File {value.name} has been added to this stack")

    def remove(self, type: FileType) -> None:
        if type == FileType.LOW: self._low_file = None
        elif type == FileType.JPG: self._jpg_file = None
        elif type == FileType.RAW: self._raw_file = None
        elif type == FileType.TIF: self._tif_file = None
        else:
            logwriter.warning(f"Unsupported FileType. Throwing TypeError") 
            raise TypeError("Unsupported FileType")  

    def print(self, prefix: str) -> None:
        print("{")
        print(prefix + f"id:{self.identity},")
        if self.raw: self.raw.print(prefix)
        if self.jpg: self.jpg.print(prefix)
        if self.low: self.low.print(prefix)
        print("}")

    def exifread(self) -> Any:
        if self.any is None:
            logwriter.warning(f"Empty stack.")
            return None

        metadata = self.any.exifread()

        if self._metadata is not None:
            metadata.rating = self._metadata.rating
            metadata.comment = self._metadata.comment
            metadata.tags = self._metadata.tags

        self._metadata = metadata

        return self._metadata

# endregion

