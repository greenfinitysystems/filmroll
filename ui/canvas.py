# region(python_imports)

import logging
from typing import Any
import math
import tkinter.font as tkfont
from enum import Enum
import ttkbootstrap as tb
from PIL import Image, ImageDraw, ImageTk

# endregion

# region(project_imports)

from core.config import Config
from core.util import Rectangle, Util

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

# region(enumeratons)

class DisplayMode(Enum):
    preview = 0
    jpeg = 1
    raw = 2

# endregion

class Canvas(tb.Canvas):

# region(class_methods)

    def __init__(self, parent: Any, i: int):
        super().__init__(parent._root)
        self._parent = parent
        self._nopreview = Config().asset("thumb.jpg")
        
        self._reset()
        self._pos = i

        cfg = Config()

        self.configure(bg=cfg.gallery_color)
        self.grid(row=i // self._parent._cols, column=i % self._parent._cols, sticky="nsew", pady=(10,10), padx=(10,10))
        self.bind("<Configure>", self._redraw)
        self.bind("<Button-1>", self._on_mouse_lbutton_press)
        self.bind("<B1-Motion>", self._on_mouse_move)
        self.bind("<ButtonRelease-1>", self._on_mouse_lbutton_release)
        self.bind("<MouseWheel>", self._on_mouse_scroll)
        self.bind("<Button-4>", self._on_mouse_scroll)
        self.bind("<Button-5>", self._on_mouse_scroll)

        self.reload()

# endregion

# region(methods)

    def reload(self) -> None:
        self._reset_image_data()

        self._stack = self._parent._stacks[self._pos]
        if self._display_mode == DisplayMode.raw: file = self._stack.raw
        elif self._display_mode == DisplayMode.jpeg: file = self._stack.jpg
        elif self._display_mode == DisplayMode.preview: file = self._stack.low
        else: file = None
        self._image = file.open() if file is not None else Image.open(self._nopreview)

# endregion

# region(event_handlers)

    def _redraw(self, event=None) -> None: 
        # source type
        def _step_10():
            if self._display_mode == DisplayMode.jpeg: text = "JPG"
            elif self._display_mode == DisplayMode.raw: text = "RAW"
            else: return

            bm = int(min(self._rect.height, self._rect.width) * 0.05)
            lm = int(min(self._rect.height, self._rect.width) * 0.03)
            font_size = max(8, int(math.ceil(self._rect.width * 0.08 * 14.0/68.3)))
            self.create_text(
                self._rect.left + lm,
                self._rect.bottom - bm,
                text=text,
                fill="#dddddd",
                font=("Arial", font_size, "bold"),
                anchor="sw"
            )

        # zoom level
        def _step_9():
            tm = int(min(self._rect.height, self._rect.width) * 0.05)
            rm = int(min(self._rect.height, self._rect.width) * 0.03)
            font_size = max(8, int(math.ceil(self._rect.width * 0.08 * 14.0/68.3)))
            self.create_text(
                self._rect.right - rm,
                self._rect.top + tm,
                text=f"{self._cur_zoom * 100:.0f}%",
                fill="#dddddd",
                font=("Arial", font_size, "bold"),
                anchor="ne"
            )

        # bind popup menu
        def _step_8():
            self.tag_bind("preview", "<Button-3>", self._on_mouse_rbutton_click)

        # rating icon
        def _step_7():
            rating = self._stack.metadata.rating
            if not (0 <= rating <= 5): 
                return

            bm = int(min(self._rect.height, self._rect.width) * 0.026)
            lm = int(min(self._rect.height, self._rect.width) * 0.03)
            font_size = max(8, int(math.ceil(self._rect.width * 0.08 * 14.0/68.3)))

            char = "★"
            color = ("#dddddd", "#FF0000", "#0000FF", "#008000", "#800080", "#F28C28")

            self.create_text(
                self._rect.right - lm,
                self._rect.bottom - bm,
                text=char,
                fill=color[rating],
                font=("Arial", font_size, "bold"),
                anchor="se"
            )

        # notes icon
        def _step_6():
            text = ""
            if self._stack.raw is not None:
                if self._stack.jpg is not None:
                    text = "RAW+JPG"
                else:
                    text = "RAW"
            else:
                text = "JPG"

            bm = int(min(self._rect.height, self._rect.width) * 0.029)
            lm = int(min(self._rect.height, self._rect.width) * 0.035)
            font_size = max(14, int(math.ceil(self._rect.width * 0.08 * 14.0/68.3)))
            font_size = int(font_size / 2)
            # ☰ ⚙ 🛠 📷

            self.create_text(
                self._rect.left + lm,
                self._rect.bottom - bm,
                text=text,
                fill="#bbbbbb",
                font=("Arial", font_size, "normal"), 
                anchor="sw",
                tags="notes_icon"
            )

        # histogram overlay
        def _step_5():
            self._histogram = self._get_histogram()
            
            bm = int(min(self._rect.height, self._rect.width) * 0.1)
            lm = int(min(self._rect.height, self._rect.width) * 0.05)
    
            width = self._histogram.width()
            height = self._histogram.height()
    
            hist_rect = Rectangle(
                left    = self._rect.right - lm - width,
                top     = self._rect.bottom - bm - height,
                right   = self._rect.right - lm,
                bottom  = self._rect.bottom - bm,
            )
    
            if not ( 
                hist_rect.left > self._rect.left and 
                hist_rect.top > self._rect.top
            ):
                return
    
            self.create_image(
                hist_rect.left + width//2, 
                hist_rect.top + height//2,
                image=self._histogram
            )

        # metadata overlay
        def _step_4():
            full = (self._display_mode != DisplayMode.preview)
            text = self._stack.metadata.get_text(full=full)

            lines = text.split("\n")
            font = tkfont.Font(family="Consolas", size=10)
            max_width = max(font.measure(line) for line in lines)
            line_height = font.metrics("linespace")

            padding = 10
            tm = int(min(self._rect.height, self._rect.width) * 0.05)
            lm = int(min(self._rect.height, self._rect.width) * 0.05)

            box_rect = Rectangle(
                left   = self._rect.left + lm,
                top    = self._rect.top  + tm,
                right  = self._rect.left + lm + (max_width + padding * 2),
                bottom = self._rect.top  + tm + (line_height * len(lines) + padding * 2),
            )

            if not ( 
                box_rect.right <= self._rect.right and 
                box_rect.bottom <= self._rect.bottom
            ):
                return

            if self._metadata_bg is None:
                self._metadata_bg = ImageTk.PhotoImage(Image.new(
                    'RGBA', 
                    (box_rect.width, box_rect.height), 
                    (30,30,30,180)
                ))

            self.create_image(
                box_rect.left + box_rect.width//2, 
                box_rect.top + box_rect.height//2,
                image=self._metadata_bg
            )

            self.create_text(
                box_rect.left + padding,
                box_rect.top + padding,
                text=text,
                fill="white",
                font=("Consolas", 10),
                anchor="nw"
            )

        # selecton marker
        def _step_3():
            width = self._rect.width * 0.2
            self.create_rectangle(
                self._rect.left + self._rect.width//2 - width // 2 ,
                self._rect.bottom - 4,
                self._rect.right - self._rect.width//2 + width // 2,
                self._rect.bottom,
                outline="#4da3ff",
                width=4
            )

        # rejected symbol
        def _step_2():
            self.create_text(
                self._rect.right - int(self._rect.width * 0.05),
                self._rect.top + int(self._rect.height * 0.05),
                text="⮾",
                fill="#ff4444",
                font=("Arial", int(min(self._rect.width, self._rect.height) * 0.08), "bold"),
                anchor="ne"
            )

        # main image
        def _step_1():
            clip = self._clip()
            self.image = ImageTk.PhotoImage(clip)
            iid = self.create_image( (self.winfo_width() // 2), (self.winfo_height() // 2), image=self.image, tags="preview")
            bbox = self.bbox(iid)
            self._rect = Rectangle(
                left   = bbox[0],
                top    = bbox[1],
                right  = bbox[2],
                bottom = bbox[3],
            )

        def _step_0():
            if True:
                _step_1()

            if self._stack.rejected:
                _step_2()

            if self._pos == self._parent._active_local:
                _step_3()

            if self._parent._show_metadata:
                _step_4()

            if self._parent._show_histogram:
                _step_5()

            if self._display_mode == DisplayMode.preview:
                _step_6()

            if True:
                _step_7()

            if True:
                _step_8()

            if self._display_mode in (DisplayMode.jpeg, DisplayMode.raw):
                _step_9()

            if True:
                _step_10()

        try:
            if self._root is not None and self._image is not None:
                self.delete("all")
                _step_0()

        except Exception as e:
            logwriter.debug(f"Canvas._redraw() - Failed to redraw canvas {e}")

    def _on_mouse_lbutton_press(self, event) -> None:
        self._parent._active_local = self._pos
        self._parent._redraw()

    def _on_mouse_move(self, event) -> None:
        ctrl = (event.state & 0x0004) != 0
        drag = bool(event.state & 0x0100)

        if not drag or self._display_mode == DisplayMode.preview or (self._cur_zoom == self._min_zoom):
            return "break"

        self._sync_drag = self._sync_drag or ctrl

        if self._drag_start is not None:
            if self._sync_drag:
                for canvas in self._parent._canvases:
                    canvas._pan_move(event)
            else:
                self._pan_move(event)

        else:
            if self._sync_drag:
                for canvas in self._parent._canvases:
                    canvas._pan_start(event)
            else:
                self._pan_start(event)

            self._parent._root.configure(cursor="fleur")

        return "break"

    def _on_mouse_lbutton_release(self, event) -> None:
        if self._drag_start is None:
            return "break"

        if self._sync_drag:
            for canvas in self._parent._canvases:
                canvas._pan_end()
        else:
            self._pan_end()

        self._parent._root.configure(cursor='')

        return "break"

    def _on_mouse_rbutton_click(self, event) -> None:
        self._parent._active_local = self._pos
        self._parent._redraw()
        self._parent._show_popup_menu(event.x_root, event.y_root)

        return "break"

    def _on_mouse_scroll(self, event) -> None:
        ctrl = (event.state & 0x0004) != 0
        if self._display_mode == DisplayMode.preview or not ctrl:
            return "break"
        
        direction = 1 if (event.num == 4 or event.delta > 0) else -1
        self._zoom_latest_direction = direction
        self._zoom_latest_pos = (event.x, event.y)

        if self._zoom_redraw_pending:
            return "break"

        self._zoom_redraw_pending = True
        self._zoom_thread = self.after(16, self._process_zoom)

        return "break"

# endregion

# region(private_methods)

    def _reset(self) -> None:
        self._pos = -1
        self._display_mode = DisplayMode.preview
        self._stack = None
        self._rect = None
        self._reset_image_data()

    def _reset_image_data(self) -> None:
        self._histogram = None
        
        if hasattr(self, "_image") and self._image is not None:
            self._image.close()
        self._image = None

        if hasattr(self, "_pan_thread") and self._pan_thread is not None:
            self.after_cancel(self._pan_thread)
        self._pan_thread = None

        if hasattr(self, "_zoom_thread") and self._zoom_thread is not None:
            self.after_cancel(self._zoom_thread)
        self._zoom_thread = None

        self._metadata_bg = None

        self._cur_zoom = 0.0
        self._min_zoom = 0.0
        self._zoom_redraw_pending = False
        self._zoom_redraw_requested = False
        self._zoom_latest_direction = None
        self._zoom_latest_pos = None

        self._pan_x = 0
        self._pan_y = 0
        self._drag_start = None
        self._sync_drag = False
        self._pan_redraw_pending = False
        self._pan_latest_pos = None

    def _pan_start(self, event) -> None:
        self._drag_start = (event.x, event.y)

    def _pan_move(self, event) -> None:
        self._pan_latest_pos = (event.x, event.y)
        if self._pan_redraw_pending:
            return

        self._pan_redraw_pending = True
        self._pan_thread = self.after(16, self._process_pan)

    def _pan_end(self) -> None:
        self._sync_drag = False
        self._drag_start = None
        self._redraw()

    def _clip(self) -> Image:
        img_copy = self._image.copy()

        img_w, img_h = self._image.size
        canvas_w, canvas_h = (self.winfo_width(), self.winfo_height())

        # --------------------------------
        # PREVIEW mode
        # --------------------------------

        if self._display_mode == DisplayMode.preview:
            img_copy.thumbnail((canvas_w, canvas_h))
            self._min_zoom = self._calc_fit_zoom()
            self._cur_zoom = self._min_zoom
            return img_copy

        # --------------------------------
        # Jpeg & Raw FIT mode
        # --------------------------------

        fit_mode = (self._cur_zoom == self._min_zoom)
        self._min_zoom = self._calc_fit_zoom()

        if fit_mode:
            img_copy.thumbnail((canvas_w, canvas_h))
            self._cur_zoom = self._min_zoom
            return img_copy

        # --------------------------------
        # Jpeg & Raw ZOOM mode
        # --------------------------------

        zoom = self._cur_zoom

        crop_w = min(img_w, int(canvas_w / zoom))
        crop_h = min(img_h, int(canvas_h / zoom))

        # Current viewport centre
        cx = img_w // 2 + int(self._pan_x)
        cy = img_h // 2 + int(self._pan_y)

        half_w = crop_w // 2
        half_h = crop_h // 2

        # --------------------------------
        # Clamp viewport centre
        # --------------------------------

        cx = max(half_w, min(img_w - half_w, cx))
        cy = max(half_h,min(img_h - half_h, cy))

        # --------------------------------
        # Crop
        # --------------------------------

        left = cx - half_w
        top = cy - half_h

        right = left + crop_w
        bottom = top + crop_h

        img_copy = img_copy.crop(
            (left, top, right, bottom)
        )

        # --------------------------------
        # Magnify crop to canvas
        # --------------------------------

        display_w = int(crop_w * zoom)
        display_h = int(crop_h * zoom)

        resample = (
            Image.Resampling.BILINEAR
            if self._drag_start is not None
            else Image.Resampling.LANCZOS
        )

        img_copy = img_copy.resize(
            (display_w, display_h),
            resample
        )

        return img_copy

    def _calc_fit_zoom(self) -> tuple:
        img_w, img_h = self._image.size
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()

        if img_w <= 0 or img_h <= 0:
            return 0.0

        return min( canvas_w / img_w, canvas_h / img_h)

    def _process_pan(self) -> None:
        self._pan_redraw_pending = False
        self._pan_thread = None

        if self._drag_start is None:
            return

        if self._pan_latest_pos is None:
            return

        event_x, event_y = self._pan_latest_pos
        self._pan_latest_pos = None

        old_x, old_y = self._drag_start
        self._drag_start = (event_x, event_y)

        dx = event_x - old_x
        dy = event_y - old_y

        zoom = self._cur_zoom

        if zoom <= 0:
            return

        self._pan_x -= dx / zoom
        self._pan_y -= dy / zoom

        img_w, img_h = self._image.size

        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()

        crop_w = min(img_w, int(canvas_w / zoom))
        crop_h = min(img_h, int(canvas_h / zoom))

        max_x = max(0, (img_w - crop_w) / 2)
        max_y = max(0, (img_h - crop_h) / 2)

        self._pan_x = max(-max_x, min(max_x, self._pan_x))
        self._pan_y = max(-max_y, min(max_y, self._pan_y))

        self._redraw()

        if self._pan_latest_pos is not None:
            self._pan_redraw_pending = True
            self._pan_thread = self.after(16, self._process_pan)

    def _process_zoom(self) -> None:
        self._zoom_redraw_pending = False
        self._zoom_thread = None

        if self._zoom_latest_pos is None:
            return

        direction = self._zoom_latest_direction
        mouse_x, mouse_y = self._zoom_latest_pos

        self._zoom_latest_pos = None
        self._zoom_latest_direction = None

        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()

        old_zoom = self._cur_zoom

        center_x = canvas_w / 2
        center_y = canvas_h / 2

        image_x = (self._pan_x + (mouse_x - center_x) / old_zoom)
        image_y = (self._pan_y + (mouse_y - center_y) / old_zoom)

        _cur_zoom = self._cur_zoom
        if self._cur_zoom == self._min_zoom and direction > 0:
            if self._cur_zoom < 0.1: _cur_zoom = 0.1
            elif self._cur_zoom < 1.0: _cur_zoom = int(self._cur_zoom * 10.0) / 10.0
            else: _cur_zoom = int(self._cur_zoom * 100.0) / 100.0

        new_zoom = _cur_zoom + (0.1 * direction)
        new_zoom = max(self._min_zoom, min(4.0, new_zoom))
        if new_zoom == self._cur_zoom:
            return

        self._cur_zoom = new_zoom

        if self._cur_zoom == self._min_zoom:
            self._pan_x = 0
            self._pan_y = 0
        else:
            self._pan_x = (image_x - (mouse_x - center_x) / new_zoom)
            self._pan_y = (image_y - (mouse_y - center_y) / new_zoom)

        self._redraw()

        if self._zoom_latest_pos is not None:
            self._zoom_redraw_pending = True
            self._zoom_thread = self.after(16, self._process_zoom)

    def _get_histogram(self)-> ImageTk.PhotoImage:
        def _generate(histogram, size, img):
            hscale = size[0] / 255
            color = ("red", "green", "blue", "white")
            draw = ImageDraw.Draw(img)

            for x in range(255):
                for c, hist in enumerate(histogram):
                    draw.line( 
                        [((x * hscale), (size[1] - hist[x])), 
                        (((x + 1) * hscale), (size[1] - hist[x+1]))], 
                        fill=color[c], 
                        width=2
                    )

            return img

        key = (self._stack.identity, self._display_mode)
        if key in self._thumbnailgrid()._histogram_cache:
            return self._thumbnailgrid()._histogram_cache[key]

        hist = None
        size = (255, 100)

        if self._display_mode == DisplayMode.raw:
            if self._stack.raw is not None:
                with self._image.copy() as im:
                    hist = Util.histogram(im, size)

        elif self._display_mode == DisplayMode.jpeg:
            if self._stack.jpg is not None:
                with self._image.copy() as im:
                    hist = Util.histogram(im, size)

        elif self._display_mode == DisplayMode.preview:
            if self._stack.jpg is not None:
                with self._stack.jpg.open() as im:
                    hist = Util.histogram(im, size)

        with Image.new('RGBA', size, (30,30,30,180)) as img:
            self._thumbnailgrid()._histogram_cache[key] = (
                ImageTk.PhotoImage(_generate(hist, size, img))
                if hist is not None else 
                ImageTk.PhotoImage(img)
            )
    
        return self._thumbnailgrid()._histogram_cache[key]

    def _thumbnailgrid(self) -> Any:
        return self._parent._parent

# endregion
