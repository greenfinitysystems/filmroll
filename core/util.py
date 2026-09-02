# region(python_imports)

import logging
import math
import re
from typing import Any, NamedTuple

# endregion

# region(project_imports)

# There are no project module import

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class Util:

# region(methods)

    @staticmethod
    def convert_size_to_str(size_bytes: int) -> str:
        if size_bytes == 0: return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    @staticmethod
    def chunk_generator(lst: list, chunk_size: int):
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    @staticmethod
    def is_valid_hex_code(s: str):
        hex_pattern = r'^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$'
        return bool(re.match(hex_pattern, s))

# endregion

# region(worker_func_tuples)

class PreviewJob(NamedTuple):
    identity: str

class FileOpsJob(NamedTuple):
    source: str
    destination: str
    command: Any
    size: int =0

class CollateJob(NamedTuple):
    source: str

class MetadataJob(NamedTuple):
    identity: str

# endregion

# region(other_tuples)

class MetadataFilter(NamedTuple):
    property: str
    label: str
    values: list
    selected_values: list

class Rectangle(NamedTuple):
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

# endregion

