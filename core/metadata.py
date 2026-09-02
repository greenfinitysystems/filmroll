# region(python_imports)

import logging
from fractions import Fraction
from typing import Any

# endregion

# region(project_imports)

from core.config import Config

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class Metadata:

# region(class_methods)

    def __init__(self, exif_data: Any):
        self._data = {}   
        Metadata._read_entry(exif_data, self._data, "Exif.Image.Make")
        Metadata._read_entry(exif_data, self._data, "Exif.Image.Model")
        Metadata._read_entry(exif_data, self._data, "Exif.Photo.FNumber")
        Metadata._read_entry(exif_data, self._data, "Exif.Photo.ExposureTime")
        Metadata._read_entry(exif_data, self._data, "Exif.Photo.ISOSpeedRatings")
        Metadata._read_entry(exif_data, self._data, "Exif.Photo.ExposureProgram")
        Metadata._read_entry(exif_data, self._data, "Exif.Photo.FocalLength")
        Metadata._read_entry(exif_data, self._data, "Exif.Photo.LensModel")
        Metadata._read_entry(exif_data, self._data, "Exif.Photo.ExposureBiasValue")

        # additional values which will be read from
        # iptc/xmp data in future; these are editable by user
        self.rating = 0
        self.comment = ""
        self.tags = ""

# endregion

# region(properties)

    @property
    def make(self) -> str:
        attrib = 'Make'
        return self._data[attrib] if attrib in self._data else ''

    @property
    def model(self) -> str:
        attrib = 'Model'
        return self._data[attrib] if attrib in self._data else ''

    @property
    def camera(self) -> str:
        return self.make + ' ' + self.model

    @property
    def lensmodel(self) -> str:
        attrib = 'LensModel'
        return self._data[attrib] if attrib in self._data else ''

    @property
    def iso(self) -> str:
        attrib = 'ISOSpeedRatings'
        return str(self._data[attrib]) if attrib in self._data else ''

    @property
    def aperture(self) -> str:
        attrib = 'FNumber'
        try:
            value = self._data[attrib] if attrib in self._data else ''
            return str(float(Fraction(value).limit_denominator(10)))
        except:
            return "n/a"

    @property
    def shutter_speed(self) -> str:
        attrib = 'ExposureTime'
        try:
            value = self._data[attrib] if attrib in self._data else ''
            return str(Fraction(value))
        except:
            return "n/a"

    @property
    def focal_length(self) -> str:
        attrib = 'FocalLength'
        try:
            value = self._data[attrib] if attrib in self._data else ''
            return str(float(Fraction(value).limit_denominator(10)))
        except:
            return "n/a"

    @property
    def exposure_compensation(self) -> str:
        attrib = 'ExposureBiasValue'
        raw_value = self._data[attrib] if attrib in self._data else ''

        try:
            f = Fraction(raw_value).limit_denominator(10)
            v = float(f)
            i_part = int(v)
            f_part = Fraction(v - i_part).limit_denominator(10)
            s_val = ""
            if i_part != 0: s_val = f"{i_part:+}"
            if f_part == 0: return "0"
            if i_part != 0: s_val += f" {f_part}"
            else: s_val += f"{f_part:+}"
            return s_val
        except:
            return "0"

    @property
    def rating(self) -> str:
        attrib = 'rating'
        try:
            value = self._data[attrib] if attrib in self._data else '0'
            return value
        except:
            return "n/a"

    @rating.setter
    def rating(self, value: int) -> None:
        attrib = 'rating'
        try:
            v = int(value)
            self._data[attrib] = value
        except:
            pass

    @property
    def comment(self) -> str:
        attrib = 'comment'
        try:
            value = str(self._data[attrib]) if attrib in self._data else '0'
            return value
        except:
            return "n/a"

    @comment.setter
    def comment(self, value: str) -> None:
        attrib = 'comment'
        try:
            self._data[attrib] = value
        except:
            pass

    @property
    def tags(self) -> str:
        attrib = 'tags'
        try:
            value = str(self._data[attrib]) if attrib in self._data else '0'
            return value
        except:
            return "n/a"

    @comment.setter
    def tags(self, value: str) -> None:
        attrib = 'tags'
        try:
            self._data[attrib] = value
        except:
            pass

# endregion

# region(methods)

    def get_text(self):
        lines = [
                f"Camera: {self.camera}",
                f"Lens: {self.lensmodel}",
                f"Aperture: f/{self.aperture}",
                f"Shutter: {self.shutter_speed}s",
                f"ISO: {self.iso}",
                f"EV: {self.exposure_compensation}",
            ]

        return "\n".join(lines)

    def print(self, prefix: str) -> None:
        print(f"{prefix}Aperture: {self.aperture}")
        print(f"{prefix}Shutter Speed: {self.shutter_speed}")
        print(f"{prefix}ISO: {self.iso}")
        print(f"{prefix}EC: {self.exposure_compensation}")
        print(f"{prefix}Focal Length: {self.focal_length}")
        print(f"{prefix}Camera: {self.make} {self.model}")
        print(f"{prefix}Lens: {self.lensmodel}")

# endregion

# region(private_methods)

    @staticmethod
    def _read_entry(exif_data: Any, metadata: dict, exiftag: str) -> None:
        try: 
            metadata[exiftag.split('.')[2]] = str(exif_data[exiftag].value())

        except:
            # logwriter.info(f"Skipping exiftag => {exiftag}.")
            pass

# endregion

