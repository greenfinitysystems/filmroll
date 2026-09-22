# region(python_imports)

import logging
from fractions import Fraction
from typing import Any

# endregion

# region(project_imports)

from core.config import Config
from core.util import IptcInfo

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class Metadata:

    _jsonpickle_exclude = {'_focal_group'}

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

# endregion

# region(properties)

    @property
    def make(self) -> str:
        return self._data.get('Make', '')

    @property
    def model(self) -> str:
        return self._data.get('Model', '')

    @property
    def camera(self) -> str:
        return f"{self.make} {self.model}"

    @property
    def lensmodel(self) -> str:
        return self._data.get('LensModel', '')

    @property
    def iso(self) -> str:
        return self._data.get('ISOSpeedRatings', '')

    @property
    def aperture(self) -> str:
        try: return str(float(Fraction(self._data.get('FNumber', '')).limit_denominator(10)))
        except: return ''

    @property
    def shutter_speed(self) -> str:
        try: return str(Fraction(self._data.get('ExposureTime', '')))
        except: return ''

    @property
    def focal_length(self) -> str:
        try: return str(float(Fraction(self._data.get('FocalLength', ''))))
        except: return ''

    @property
    def focal_group(self) -> str:
        try:
            if not hasattr(self, '_focal_group'):
                self._focal_group = None

            if self._focal_group is not None:
                return self._focal_group

            focal_length = float(Fraction(self._data.get('FocalLength', '')).limit_denominator(10))

            cfg = Config()
    
            for i, (name, min_val, max_val) in enumerate(cfg.focal_groups):
                if min_val <= focal_length <= max_val:
                    self._focal_group = name
                    return self._focal_group
        except:
            pass

        return 'n/a'

    @property
    def exposure_compensation(self) -> str:
        try:
            raw_value = self._data.get('ExposureBiasValue', '0')
            if raw_value == '0':
                return '0'

            v = float(Fraction(raw_value).limit_denominator(10))
            i_part = int(v)
            f_part = Fraction(v - i_part).limit_denominator(10)

            s_val = '0'

            if i_part != 0: 
                s_val = f"{i_part:+}"
                if f_part != 0:
                    s_val += f" {f_part}"
            else:
                if f_part != 0:
                    s_val = f"{f_part:+}"

            return s_val

        except:
            return '0'

    @property
    def rating(self) -> int:
        try: return int(self._data.get('rating', 0))
        except: return 0

    @rating.setter
    def rating(self, value: int) -> None:
        self._data['rating'] = int(value)

    @property
    def comment(self) -> str:
        return self._data.get('comment', '')

    @comment.setter
    def comment(self, value: str) -> None:
        self._data['comment'] = value

    @property
    def tags(self) -> list:
        piped_string = self._data.get('tags', '')
        return [tag for tag in piped_string.split('|') if tag]

    @tags.setter
    def tags(self, value: list) -> None:
        cfg = Config()
        seen = set()
        unique_tags = []
        for tag in value or []:
            tag = tag.strip().lower()
            if tag and tag not in seen and "|" not in tag:
                seen.add(tag)
                unique_tags.append(tag)
                cfg.tagstore.add(tag)
        self._data['tags'] = '|'.join(unique_tags)

    @property
    def author(self) -> str:
        return self._data.get('author', '')

    @author.setter
    def author(self, value: str) -> None:
        self._data['author'] = value

    @property
    def copyright(self) -> str:
        return self._data.get('copyright', '')

    @copyright.setter
    def copyright(self, value: str) -> None:
        self._data['copyright'] = value

    @property
    def caption(self) -> str:
        return self._data.get('caption', '')

    @caption.setter
    def caption(self, value: str) -> None:
        self._data['caption'] = value

# endregion

# region(methods)

    def get_iptcinfo(self) -> IptcInfo:
        return IptcInfo(
            author=self.author,
            copyright=self.copyright,
            caption = self.caption,
            comment=self.comment,
            rating=self.rating,
            tags=tuple(self.tags),
        )

    def set_iptcinfo(self, value: IptcInfo) -> None:
        if not isinstance(value, IptcInfo) or value is None:
            return

        self.author = value.author
        self.copyright = value.copyright
        self.caption = value.caption
        self.comment = value.comment
        self.rating = value.rating
        self.tags = list(value.tags)

    def get_text(self, full: bool = False):
        lines = [
                f"Camera: {self.camera}",
                f"Lens: {self.lensmodel}",
                f"Aperture: f/{self.aperture}",
                f"Shutter: {self.shutter_speed}s",
                f"ISO: {self.iso}",
                f"EV: {self.exposure_compensation}",
            ]

        return "\n".join(lines)

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
