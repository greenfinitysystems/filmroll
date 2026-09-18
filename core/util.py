# region(python_imports)

import logging
import math
import re
from typing import Any, NamedTuple
from scipy.ndimage import gaussian_filter1d

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

    @staticmethod
    def histogram(image, size):
        image.thumbnail((128, 128))
        r, g, b = image.split()    
        hist_r_s = gaussian_filter1d(r.histogram(), sigma=2)    
        hist_g_s = gaussian_filter1d(g.histogram(), sigma=2)
        hist_b_s = gaussian_filter1d(b.histogram(), sigma=2)    
        # img.convert('L')
        # hist_w_s = gaussian_filter1d(img.histogram(), sigma=2)    
        # return (hist_r_s, hist_g_s, hist_b_s, hist_w_s)
        hist_data = (hist_r_s, hist_g_s, hist_b_s)

        for hist in hist_data:
            max_v = max(hist)
            vscale = size[1] / max_v if max_v != 0 else 0
            for i, v in enumerate(hist):
                hist[i] = v * vscale

        return hist_data

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

class JpegExportJob(NamedTuple):
    source: str
    destination: str
    metadata: Any

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

class JpegExportTemplate(NamedTuple):
    export_path: str
    export_size: int
    export_quality: int
    border_size: float
    border_color: str
    border_exif: int

# endregion

