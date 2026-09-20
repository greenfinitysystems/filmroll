# region(python_imports)

import json
import logging
import sys
from functools import cache
from pathlib import Path
from typing import Any

# endregion

# region(project_imports)

from core.util import MetadataFilter, Util
from core.tagstore import TagStore

# endregion

class Config:

    __VERSION__ = "0.7.0-dev"

# region(class_methods)

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, save=False):
        if getattr(self, "_initialized", False):
            return

        self._initialized = True

        base_path = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
        self._asset_path =  base_path / "assets"

        # User-writable configuration and log directory.
        if sys.platform == "win32":
            self._conf_path = Path.home() / "AppData" / "Roaming" / "Filmroll"
        else:
            self._conf_path = Path.home() / ".config" / "filmroll"

        self._conf_file = self._conf_path / "config.json"
        self._log_file = self._conf_path / "filmroll.log"
        self._tag_file = self._conf_path / "filmroll-tags.json"

        self._tagstore = TagStore(str(self._tag_file))
        if save: self._tagstore.save()

        self._curr_conf = {}

        self.log_level = "Error"
        self.gallery_color = "#1e1e1e"
        self.preview_size = 1024
        self.border_ratio = 0.04
        self.border_color = "#ffffff"
        self.caption_color = "#000000"
        self.caption_font = "DejaVuSans.ttf"
        self.xrawstudio_path = r"C:\Program Files\FUJIFILM X RAW STUDIO\FUJIFILM_X_RAW_STUDIO.exe"
        self.use_focal_groups = 1
        self.focal_groups = [
            ["Ultra Wide",         0.1,   7.0],
            ["8mm",                7.1,   9.0],
            ["10mm",               9.1,  12.0],
            ["13mm",              12.1,  15.0],
            ["16mm",              15.1,  17.0],
            ["18mm",              17.1,  19.0],
            ["20mm",              19.1,  22.0],
            ["23mm",              22.1,  24.0],
            ["25mm",              24.1,  26.0],
            ["27mm",              26.1,  29.0],
            ["30mm",              29.1,  32.0],
            ["35mm Class",        32.1,  39.0],
            ["40mm Class",        39.1,  45.0],
            ["50mm Class",        45.1,  59.0],
            ["Short Telephoto",   59.1,  80.0],
            ["Portrait Telephoto",80.1, 100.0],
            ["Long Portrait",    100.1, 150.0],
            ["Long Telephoto",   150.1, 300.0],
            ["Super Telephoto",  300.1, 500.0],
            ["Extreme Telephoto",500.1, 600.0],
            ["Ultra Telephoto",  600.1, 1000.0]
        ]

        self._load()

        # always save it back
        if save:
            self._save()

        if not (self._asset_path / self._curr_conf["caption_font"]).exists():
            raise RuntimeError(f"Missing Font file {self._curr_conf['caption_font']} while searching in in {str(self._asset_path)}")

        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d]- %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=self._log_file,
            filemode='a' # 'a' for append, 'w' for overwrite
        )

# endregion

# region(properties)

    @property
    def logger_log_level(self) -> str:
        val = self._curr_conf["log_level"]
        if val == "debug": return logging.DEBUG
        if val == "info": return logging.INFO
        if val == "warning": return logging.WARNING
        return logging.ERROR

    @property
    def log_level(self) -> str:
        return self._curr_conf["log_level"]

    @log_level.setter
    def log_level(self, value: str) -> None:
        attrib = "log_level"
        valid = ["error", "warning", "info", "debug"]
        try:
            if str(value).lower() in valid:
                self._curr_conf[attrib] = str(value).lower()
        except:
            pass

    @property
    def gallery_color(self) -> str:
        return self._curr_conf["gallery_color"]

    @gallery_color.setter
    def gallery_color(self, value: Any) -> None:
        attrib = "gallery_color"
        try:
            if Util.is_valid_hex_code(value):
                self._curr_conf[attrib] = value
        except:
            pass

    @property
    def preview_size(self) -> int:
        return self._curr_conf["preview_size"]

    @preview_size.setter
    def preview_size(self, value: Any) -> None:
        attrib = "preview_size"
        try:
            if str(value) in self.supported_preview_size:
                self._curr_conf[attrib] = int(value)
        except:
            pass

    @property
    def border_ratio(self) -> float:
        return self._curr_conf["border_ratio"]

    @border_ratio.setter
    def border_ratio(self, value: Any) -> None:
        attrib = "border_ratio"
        try:
            if 0.01 < float(value) < 0.10:
                self._curr_conf[attrib] = float(value)
        except:
             pass

    @property
    def border_color(self) -> str:
        return self._curr_conf["border_color"]

    @border_color.setter
    def border_color(self, value: Any) -> None:
        attrib = "border_color"
        try:
            if Util.is_valid_hex_code(value):
                self._curr_conf[attrib] = value
        except:
            pass

    @property
    def caption_color(self) -> str:
        return self._curr_conf["caption_color"]

    @caption_color.setter
    def caption_color(self, value: Any) -> None:
        attrib = "caption_color"
        try:
            if Util.is_valid_hex_code(value):
                self._curr_conf[attrib] = value 
        except:
            pass

    @property
    def caption_font(self) -> Path:
        return (self._asset_path / self._curr_conf["caption_font"])

    @caption_font.setter
    def caption_font(self, value: Any) -> None:
        attrib = "caption_font"
        try:
            if (self._asset_path / value).exists():
                self._curr_conf[attrib] = value
        except:
            pass

    @property
    def use_focal_groups(self) -> int:
        return self._curr_conf["use_focal_groups"]

    @use_focal_groups.setter
    def use_focal_groups(self, value) -> int:
        attrib = "use_focal_groups"
        try:
            if isinstance(value, int) and int(value) >= 0:
                self._curr_conf[attrib] = int(value)
        except:
            pass

    @property
    def focal_groups(self) -> list:
        return self._curr_conf["focal_groups"]

    @focal_groups.setter
    def focal_groups(self, value: Any) -> None:
        attrib = "focal_groups"
        try:
            if self._valid_focal_groups(value):
                self._curr_conf[attrib] = value
        except:
            pass

    @property
    def xrawstudio_path(self) -> str:
        return self._curr_conf["xrawstudio_path"]

    @xrawstudio_path.setter
    def xrawstudio_path(self, value: Any) -> None:
        attrib = "xrawstudio_path"
        try:
            if value is None or str(value) == "":
                self._curr_conf[attrib] = "" 
            else:
                self._curr_conf[attrib] = value if Path(value).exists() else ""
        except:
            pass

    @property
    def raw_ext(self) -> dict:
        return {".raf",}

    @property
    def jpg_ext(self) -> dict:
        return {".jpg",".jpeg"}

    @property
    def tif_ext(self) -> dict:
        return {".tif", ".tiff",}

    @property
    def sidecar_ext(self) -> dict:
        return {".xmp", ".pp3", ".pp2"}

    @property
    def img_ext(self) -> dict:
        return (self.raw_ext | self.jpg_ext | self.tif_ext)

    @property
    def supported_preview_size(self) -> list:
        return ["640", "800", "1024", "1152", "1280", "1600", "2048"]

    @property
    def appname(self) -> str:
        return "Filmroll"

    @property
    def version(self) -> str:
        return self.__VERSION__

    @property
    def about(self) -> str:
        return f"""
Filmroll is an image transfer, archival and metadata analysis tool dedicated to FUJIFILM Users. \
Please Note that this software is continuously evolving and is being distributed "as-is". \
The author may not be held responsible, to the extent permitted by the law, for any data loss or hardware damage during \
its usage or due to program crash. Users are cautioned to take backups of important \
photographs and use it at their own discretion.

Created by Bibhas Das.
"""

    @property
    def asset_path(self) -> Path:
        return self._asset_path

    @property
    def metadata_filters(self) -> list:
        focal_filter = "focal_length" if self.use_focal_groups == 0 else "focal_group"
        focal_label = "Focal Length" if self.use_focal_groups == 0 else "Focal Group"
        return [
            MetadataFilter(property = "camera",         label = "Camera",           values=[], selected_values=[]),
            MetadataFilter(property = "lensmodel",      label = "Lens",             values=[], selected_values=[]),
            MetadataFilter(property = focal_filter,     label = focal_label,        values=[], selected_values=[]),
            MetadataFilter(property = "aperture",       label = "Aperture",         values=[], selected_values=[]),
            MetadataFilter(property = "iso",            label = "ISO",              values=[], selected_values=[]),
            MetadataFilter(property = "film",           label = "Film Simulation",  values=[], selected_values=[]),
            MetadataFilter(property = "tags",           label = "Tags",             values=[], selected_values=[]),
        ]

    @property
    def tagfile(self) -> Path:
        return self._tag_file

    @property
    def tagstore(self) -> Any:
        return self._tagstore

# endregion

# region(methods)

    def asset(self, value: str) -> Path:
        return Path(self._asset_path / value)

# endregion

# region (private_methods)

    def _save(self):
        try:
            self._conf_path.mkdir(exist_ok=True)
            with open(self._conf_file, "w") as f:
                json.dump(self._curr_conf, f, indent=2)
        except:
            raise RuntimeError("Unable to save config.json")

    def _load(self):
        try:
            with open(self._conf_file, "r") as f:
                curr_conf = json.load(f)
        except:
            return

        for key in curr_conf.keys():
            if hasattr(Config, key):
                p = getattr(Config, key)
                if isinstance(p, property) and p.fset is not None:
                    setattr(self, key, curr_conf[key])
            else:
                self._curr_conf[key] = curr_conf[key]

    def _valid_focal_groups(self, intervals):
        if intervals is None or len(intervals) <= 0:
            return False

        for v in intervals:
            if (
                not (len(v) == 3) or 
                not isinstance(v[0], str) or
                not isinstance(v[1], float) or 
                not isinstance(v[2], float)
            ):
                return False

            if round(v[1], 1) > round(v[2], 1):
                return False

        sorted_intervals = sorted(intervals, key=lambda x: x[1])

        # ranges should start from at least 1mm and ends in at least 1000mm
        if (
            round(sorted_intervals[0][1], 1) > 1.0 or 
            round(sorted_intervals[len(sorted_intervals) - 1][2], 1) < 1000.0
        ):
            return False

        for i in range(len(sorted_intervals) - 1):
            curr_max = round(sorted_intervals[i][2], 1)
            next_min = round(sorted_intervals[i+1][1], 1)
            if (next_min <= curr_max) or round((next_min - curr_max), 1) > 0.1:
                return False

        return True

# endregion

