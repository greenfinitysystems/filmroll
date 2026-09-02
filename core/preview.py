# region(python_imports)

import logging
import io
import math
import rawpy
import exiv2
from pathlib import Path
from functools import cache
from typing import Any
from PIL import Image, ImageOps, ImageDraw, ImageFont

from scipy.ndimage import gaussian_filter1d

# endregion

# region(project_imports)

from core.config import Config

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class PreviewBuilder:

# region(class_methods)

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self._font_cache = {}
        self._initialize = True

# endregion

# region(properties)

# There are no properties for this class

# endregion

# region(methods)

    def generate_preview_file(self, source: str, destination: str, metadata: Any) -> int:
        th = self._load(source)
        th, size = self._transform(th, metadata)
        th.save(destination, quality=90)
        th.close()

        self._copy_metadata(source, destination)

        logwriter.info(f"Preview generated => {destination}")

        return size

    def compute_histogram(self, source: str) -> tuple:
        img = self._load(source)

        img.thumbnail((256, 256))
        
        r, g, b = img.split()

        hist_r = r.histogram()
        hist_r_s = gaussian_filter1d(hist_r, sigma=2)

        hist_g = g.histogram()
        hist_g_s = gaussian_filter1d(hist_g, sigma=2)

        hist_b = b.histogram()
        hist_b_s = gaussian_filter1d(hist_b, sigma=2)

        img.convert('L')
        hist_w = img.histogram()
        hist_w_s = gaussian_filter1d(hist_w, sigma=2)

        img.close()

        return (hist_r_s, hist_g_s, hist_b_s, hist_w_s)

# endregion

# region(private_methods)

    def _extract_thumbnail_from_raw(self, src: str) -> Image:
        with rawpy.imread(src) as raw:
            thumb = raw.extract_thumb()

        if thumb is not None:
            return Image.open(io.BytesIO(thumb.data))

        logwriter.info(f"Failed to extract thumbnail from {src}")
        return None

    def _load(self, src: str) -> Image:
        cfg = Config()
        valid_extns = set(cfg.raw_ext) | set(cfg.jpg_ext)
        if Path(src).suffix.lower() not in valid_extns:
            logwriter.warning(f"Image is not jpg or raw => {src}. Load failed.")
            return None

        if Path(src).suffix.lower() in cfg.raw_ext:
            return self._extract_thumbnail_from_raw(src)

        return Image.open(src)

    def _transform(self, img: Image, meta: Any):
        cfg = Config()

        img = ImageOps.exif_transpose(img)

        img.thumbnail((cfg.preview_size, cfg.preview_size), Image.Resampling.LANCZOS)
        # img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))
        
        border = int(min(img.size) * cfg.border_ratio)
        border_bottom = int(cfg.border_ratio * 2.5 * min(img.size))

        img = ImageOps.expand(img, border=(border, border, border, border_bottom), 
            fill=cfg.border_color)

        film = meta.film if hasattr(meta, "film") else ""

        text_line_1 = (
            f"{film}, "
            f"f/{meta.aperture}, "
            f"{meta.shutter_speed}s, "
            f"{meta.exposure_compensation} EV, "
            f"ISO {meta.iso}, "
            f"{meta.focal_length} mm, "
        )

        text_line_2 = (
            f"{meta.make} "
            f"{meta.model}, "
            f"{meta.lensmodel}"
        )

        font_size = int(math.ceil(border_bottom * 14.0/68.3))
        line1_offset = int(math.ceil(border_bottom * 42.0/68.3))
        line2_offset = int(math.ceil(border_bottom * 20.0/68.3))

        if font_size in self._font_cache:
            caption_font = self._font_cache[font_size]
        else:
            caption_font = ImageFont.truetype(str(cfg.caption_font), font_size)
            self._font_cache[font_size] = caption_font

        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text_line_1, font=caption_font)

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        w, h = img.size
        draw.text(((w - tw) / 2, h - th - line1_offset), text_line_1, fill=cfg.caption_color, font=caption_font)

        bbox = draw.textbbox((0, 0), text_line_2, font=caption_font)

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        w, h = img.size
        draw.text(((w - tw) / 2, h - th - line2_offset), text_line_2, fill=cfg.caption_color, font=caption_font)

        return img, w*h

    def _copy_metadata(self, source: str, destination: str) -> None:
        # Following section of code will copy the metadata from source image to
        # our preview image; we may change some values here
        # but most importatly - will fix the orientation so that someone
        # openning the image in any viewer does not see double rotation

        # Open source image
        src_image = exiv2.ImageFactory.open(source)
        src_image.readMetadata()
        exif_data = src_image.exifData()

        # EXIF 274 is orientation. Now that we have rotated the image
        # we will set it to 1 (Normal) so that further image viewers don't
        # rotate it once again
        exif_data['Exif.Image.Orientation'] = 1

        # IPTC Data
        iptc_data = src_image.iptcData()

        # XMP Data
        xmp_data = src_image.xmpData()

        # Open target JPG image
        target_image = exiv2.ImageFactory.open(destination)

        # Copy Exif, IPTC, and XMP data blocks to the target
        target_image.setExifData(exif_data)
        target_image.setIptcData(iptc_data)
        target_image.setXmpData(xmp_data)

        # Copy the user comment if it exists
        target_image.setComment(src_image.comment())

        # Write the changes back to the target file
        target_image.writeMetadata()

# endregion

