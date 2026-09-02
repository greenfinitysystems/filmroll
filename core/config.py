# region(python_imports)

import sys
import json
import logging
from pathlib import Path
from typing import Any
from functools import cache

# endregion

# region(project_imports)

from core.util import Util, MetadataFilter

# endregion

class Config:

# region(class_methods)

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        base_path = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
        self._conf_path = base_path
        self._conf_file = self._conf_path / "config.json"
        self._log_file = base_path / "filmroll.log"
        self._asset_path =  base_path / "assets"
        self._curr_conf = {}

        self.log_level = "info"
        self.preview_size = 1024
        self.border_ratio = 0.04
        self.border_color = "#ffffff"
        self.caption_color = "#000000"
        self.caption_font = "DejaVuSans.ttf"
        self.focal_groups = [
            ("Ultra Wide", 0, 18),
            ("Wide", 18, 35),
            ("Normal", 35, 50),
            ("Short Tele", 50, 70),
            ("Telephoto", 70, 600)
        ]

        self.xrawstudio = r"C:\Program Files\FUJIFILM X RAW STUDIO\FUJIFILM_X_RAW_STUDIO.exe"

        self._to_save = False
        self._load()

        if self._to_save: self._save()
        if not (self._asset_path / self._curr_conf["caption_font"]).exists():
            raise RuntimeError(f"Missing Font file {self.curr_conf["caption_font"]} while searching in in {str(self._asset_path)}")

        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d]- %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=self._log_file,
            filemode='a' # 'a' for append, 'w' for overwrite
        )

        self._initialized = True  

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
    def focal_groups(self) -> list:
        return self._curr_conf["focal_groups"]

    @focal_groups.setter
    def focal_groups(self, value: Any) -> None:
        attrib = "focal_groups"
        try:
            if len(value) <= 0:
                return
            for v in value:
                if not ((len(v) == 3) and isinstance(v[0], str) and isinstance(v[1], int) and 
                    isinstance(v[2], int) and (int(v[1]) <= int(v[2]))):
                    return
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
                self._curr_conf[attrib] = None 
            else:
                self._curr_conf[attrib] = Path(value) if Path(value).exists() else None
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
        return "0.5.0"

    @property
    def about(self) -> str:
        return f"""
Filmroll is an image transfer, archival and metadata analysis tool dedicated to FUJIFILM Users. \
Please Note that this is an experimental effort and conineously evolving. \
The software is being distributed "as-is". The author is not responsible for any \
data loss, hardware damage during its usage due to program crash or unforeseen situations. \
Users are cautioned to use it at their own discretion.

Created by Bibhas Das.
"""

    @property
    def asset_path(self) -> Path:
        return self._asset_path

    @property
    def metadata_filters(self) -> list:
        return [
            MetadataFilter(property = "camera",         label = "Camera",           values=[], selected_values=[]),
            MetadataFilter(property = "lensmodel",      label = "Lens",             values=[], selected_values=[]),
            MetadataFilter(property = "focal_length",   label = "Focal Length",     values=[], selected_values=[]),
            MetadataFilter(property = "aperture",       label = "Aperture",         values=[], selected_values=[]),
            MetadataFilter(property = "iso",            label = "ISO",              values=[], selected_values=[]),
            MetadataFilter(property = "film",           label = "Film Simulation",  values=[], selected_values=[]),
        ]

# endregion

# region(methods)

    def _save(self):
        try:
            self._conf_path.mkdir(exist_ok=True)
            with open(self._conf_file, "w") as f:
                json.dump(self._curr_conf, f, indent=2)
            self._to_save = False
        except:
            raise RuntimeError("Unable to save config.json")

    def _load(self):
        try:
            with open(self._conf_file, "r") as f:
                curr_conf = json.load(f)
        except:
            self._to_save = True
            return

        for key in curr_conf.keys():
            if hasattr(Config, key):
                p = getattr(Config, key)
                if isinstance(p, property) and p.fset is not None:
                    setattr(self, key, curr_conf[key])
            else:
                self._curr_conf[key] = curr_conf[key]

    def asset(self, value: str) -> Path:
        return Path(self._asset_path / value)

    def print(self) -> None:
        dumps = json.dumps(self._curr_conf, indent=2)
        print(dumps)

# endregion
