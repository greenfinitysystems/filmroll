# region(python_imports)

import logging
from typing import Any

# endregion

# region(project_imports)

from core.metadata import Metadata
from core.config import Config

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

class FujifilmMetadata(Metadata):

# region(class_methods)

    def __init__(self, exif_data: Any):
        super().__init__(exif_data)

        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.Sharpness")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.WhiteBalance")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.Color")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.WhiteBalanceFineTune")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.HighIsoNoiseReduction")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.Clarity")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.ShadowTone")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.HighlightTone")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.DevelopmentDynamicRange")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.GrainEffectRoughness")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.ColorChromeEffect")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.MonochromaticColorWC")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.MonochromaticColorMG")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.GrainEffectSize")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.ColorChromeFXBlue")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.FilmMode")
        Metadata._read_entry(exif_data, self._data, "Exif.Fujifilm.ColorTemperature")

# endregion

# region(properties)

    @property
    def sharpness(self) -> str:
        attrib = 'Sharpness'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_sharpness)
        except:
            return "n/a"

    @property
    def white_balance(self) -> str:     
        attrib = 'WhiteBalance'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            wb = self._lookup(int(raw_value), FujifilmLut.lut_white_balance)
            return wb if wb != "Kelvin" else f"{self.color_temperature}K"
        except:
            return "n/a"

    @property
    def white_balance_r_shift(self) -> str:
        attrib = 'WhiteBalanceFineTune'
        raw_value = self._data[attrib] if attrib in self._data else None

        try:
            parts = str(raw_value).split(' ')
            r = int(parts[0]) / 20
            r_value = f"{r:+.0f}"

        except:
            r_value = "0"

        return r_value

    @property
    def white_balance_b_shift(self) -> str:
        attrib = 'WhiteBalanceFineTune'
        raw_value = self._data[attrib] if attrib in self._data else None

        try:
            parts = str(raw_value).split(' ')
            b = int(parts[1]) / 20
            b_value = f"{b:+.0f}"

        except:
            b_value = "0"

        return b_value

    @property
    def white_balance_shift(self) -> str: 
        return f"R {self.white_balance_r_shift} B {self.white_balance_b_shift}"

    @property
    def color(self) -> str: 
        attrib = 'Color'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_color)
        except:
            return "n/a"

    @property
    def noise_reduction(self) -> str: 
        attrib = 'HighIsoNoiseReduction'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_noise_reduction)
        except:
            return "n/a"

    @property
    def clarity(self) -> str: 
        attrib = 'Clarity'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_clarity)
        except:
            return "n/a"

    @property
    def shadow(self) -> str: 
        attrib = 'ShadowTone'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_shadow)
        except:
            return "n/a"

    @property
    def highlight(self) -> str: 
        attrib = 'HighlightTone'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_highlight)
        except:
            return "n/a"

    @property
    def dynamic_range(self) -> str: 
        attrib = 'DevelopmentDynamicRange'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_dynamic_range)
        except:
            return "n/a"

    @property
    def grain_roughness(self) -> str: 
        attrib = 'GrainEffectRoughness'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_grain_roughness)
        except:
            return "n/a"

    @property
    def grain_size(self) -> str: 
        attrib = 'GrainEffectSize'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_grain_size)
        except:
            return "n/a"

    @property
    def color_chrome_effect(self) -> str: 
        attrib = 'ColorChromeEffect'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_color_chrome_effect)
        except:
            return "n/a"

    @property
    def color_chrome_fx_blue(self) -> str: 
        attrib = 'ColorChromeFXBlue'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            return self._lookup(int(raw_value), FujifilmLut.lut_color_chrome_fx_blue)
        except:
            return "n/a"

    @property
    def film(self) -> str: 
        attrib = 'FilmMode'
        try:
            raw_value = self._data[attrib] if attrib in self._data else None
            if raw_value is not None:
                return self._lookup(int(raw_value), FujifilmLut.lut_film)
            return self.color
        except:
            return "N/a"

    @property
    def monochromatic_color(self) -> str: 
        attrib = 'MonochromaticColorWC'
        wc = self._data[attrib] if attrib in self._data else None

        try: wc_str = f"WC {int(wc):+.0f} " if wc is not None else ""
        except: wc_str = ""

        attrib = 'MonochromaticColorMG'
        mg = self._data[attrib] if attrib in self._data else None
        try: mg_str = f"MG {int(mg):+.0f}" if mg is not None else ""
        except: mg_str = ""

        return f"{wc_str}{mg_str}"

    @property
    def color_temperature(self) -> str:
        return self._data.get("ColorTemperature", "")

    @ property
    def white_balance_display(self) -> str:
        return f"{self.white_balance} {self.white_balance_shift}"

# endregion

# region(methods)

    def get_text(self):
        lines = [
                # f"Camera: {self.camera}",
                # f"Lens: {self.lensmodel}",
                # f"Aperture: f/{self.aperture}",
                # f"Shutter: {self.shutter_speed}s",
                # f"ISO: {self.iso}",
                # f"EV: {self.exposure_compensation}",
                f"Film: {self.film}",
                f"White Balance: {self.white_balance_display}",
                f"Dynamic Range: {self.dynamic_range}",
                f"Tone: H:{self.highlight} S:{self.shadow}",
                f"Color: {self.color}",
                f"Chrome: {self.color_chrome_effect}",
                f"Chrome (Blue): {self.color_chrome_fx_blue}",
                f"Sharpness: {self.sharpness}",
                f"Clarity: {self.clarity}",
                f"Grain: {self.grain_size} {self.grain_roughness}",
                f"Noise Reduction: {self.noise_reduction}",
                
            ]

        return "\n".join(lines)

    def get_text_full(self):
        lines = [
                f"Camera: {self.camera}",
                f"Lens: {self.lensmodel}",
                f"Aperture: f/{self.aperture}",
                f"Shutter: {self.shutter_speed}s",
                f"ISO: {self.iso}",
                f"EV: {self.exposure_compensation}",
                f"Film: {self.film}",
                f"White Balance: {self.white_balance_display}",
                f"Dynamic Range: {self.dynamic_range}",
                f"Tone: H:{self.highlight} S:{self.shadow}",
                f"Color: {self.color}",
                f"Chrome: {self.color_chrome_effect}",
                f"Chrome (Blue): {self.color_chrome_fx_blue}",
                f"Sharpness: {self.sharpness}",
                f"Clarity: {self.clarity}",
                f"Grain: {self.grain_size} {self.grain_roughness}",
                f"Noise Reduction: {self.noise_reduction}",
                
            ]

        return "\n".join(lines)

    def print(self, prefix: str) -> None:
        super().print(prefix)
        print(f"{prefix}Film: {self.film}")
        print(f"{prefix}Color: {self.color}")
        print(f"{prefix}Shadow: {self.shadow}")
        print(f"{prefix}Highlight: {self.highlight}")
        print(f"{prefix}White Balance: {self.white_balance} {self.white_balance_shift}")
        print(f"{prefix}Dynamic Range: {self.dynamic_range}")
        print(f"{prefix}Sharpness: {self.sharpness}")
        print(f"{prefix}Clarity: {self.clarity}")
        print(f"{prefix}Grain: {self.grain_size} {self.grain_roughness}")
        print(f"{prefix}Noise Reduction: {self.noise_reduction}")
        print(f"{prefix}Monochromatic: {self.monochromatic_color}")

# endregion

# region(private_methods)

    def _lookup(self, raw_value: int, lut: dict) -> str:
        if raw_value is not None:
            return lut.get(raw_value, str(raw_value))
        return ""

# endregion

class FujifilmLut:

# region(LUT)

    lut_sharpness = {
        0x0   : "-4",
        0x1   : "-3",
        0x2   : "-2",
        0x82  : "-1",
        0x3   : "0",
        0x84  : "+1",
        0x4   : "+2",
        0x5   : "+3",
        0x6   : "+4",
        0x8000: "Film Simulation",
        0xffff: "n/a"
    }

    lut_white_balance = {
        0x0   : "Auto",
        0x1   : "Auto white priority",
        0x2   : "Auto ambiance priority",
        0x100 : "Daylight",
        0x200 : "Cloudy",
        0x300 : "Daylight Fluorescent",
        0x301 : "Day White Fluorescent",
        0x302 : "White Fluorescent",
        0x303 : "Warm White Fluorescent",
        0x304 : "Living Room Warm White Fluorescent",
        0x400 : "Incandescent",
        0x500 : "Flash",
        0x600 : "Underwater",
        0xf00 : "Custom1",
        0xf01 : "Custom2",
        0xf02 : "Custom3",
        0xf03 : "Custom4",
        0xf04 : "Custom5",
        0xff0 : "Kelvin",
    }

    lut_color = {
        0x0    : "0",
        0x80   : "+1",
        0xc0   : "+3",
        0xe0   : "+4",
        0x100  : "+2",
        0x180  : "-1",
        0x200  : "Low",
        0x300  : "B&W",
        0x301  : "B&W + R",
        0x302  : "B&W + Y",
        0x303  : "B&W + G",
        0x310  : "Sepia",
        0x400  : "-2",
        0x4c0  : "-3",
        0x4e0  : "-4",
        0x500  : "Acros",
        0x501  : "Acros + R",
        0x502  : "Acros + Y",
        0x503  : "Acros + G",
        0x8000 : "Film Simulation",
    }

    lut_noise_reduction = {
        0x0   : "0",
        0x100 : "+2",
        0x180 : "+1",
        0x1c0 : "+3",
        0x1e0 : "+4",
        0x200 : "-2",
        0x280 : "-1",
        0x2c0 : "-3",
        0x2e0 : "-4",
    }

    lut_clarity = {
        -5000: "-5",
        -4000: "-4",
        -3000: "-3",
        -2000: "-2",
        -1000: "-1",
        0    : "0",
        1000 : "+1",
        2000 : "+2",
        3000 : "+3",
        4000 : "+4",
        5000 : "+5",
    }

    lut_shadow = {
        -64 : "+4",
        -56 : "+3.5",
        -48 : "+3",
        -40 : "+2.5",
        -32 : "+2",
        -24 : "+1.5",
        -16 : "+1",
        -8 : "+0.5",
        0   : "0",
        8   : "-0.5",
        16  : "-1",
        24  : "-1.5",
        32  : "-2",
    }

    lut_highlight = {
        -64 : "+4",
        -56 : "+3.5",
        -48 : "+3",
        -40 : "+2.5",
        -32 : "+2",
        -24 : "+1.5",
        -16 : "+1",
        -8 : "+0.5",
        0   : "0",
        8   : "-0.5",
        16  : "-1",
        24  : "-1.5",
        32  : "-2",
    }

    lut_dynamic_range = {
        0x0 : "Auto",
        0x1 : "Manual",
        0x100 : "100%",
        0x200 : "230%",
        0x201 : "400%",
        0x8000 : "Film Simulation"
    }

    lut_grain_roughness = {
        0  : "Off",
        32 : "Weak",
        64 : "Strong",
    }

    lut_grain_size = {
        0  : "Off",
        16 : "Small",
        32 : "Large",
    }

    lut_color_chrome_effect = {
        0: "Off",
        32: "Weak",
        64: "Strong"
    }

    lut_color_chrome_fx_blue = {
        0: "Off",
        32: "Weak",
        64: "Strong"
    }

    lut_film = {
        0: "Provia",
        256: "Studio Portrait",
        272: "Studio Portrait Enhanced Saturation",
        288: "Astia",
        304: "Studio Portrait Increased Sharpness",
        512: "Velvia",
        768: "Studio Portrait EX",
        1024: "Velvia",
        1280: "Pro Neg. Standard",
        1281: "Pro Neg. Hi",
        1536: "Classic Chrome",
        1792: "Eterna",
        2048: "Classic Negative",
        2304: "Bleach Bypass",
        2560: "Nostalgic Negative",
        2816: "Reala"
    }

# endregion

