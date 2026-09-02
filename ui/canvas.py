# region(python_imports)

import math
import logging
import ttkbootstrap as tb
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageDraw, ImageOps
import threading
from enum import Enum
import rawpy

# endregion

# region(project_imports)

from core.preview import PreviewBuilder
from core.config import Config
from core.util import Rectangle

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)
logwriter.setLevel(Config().logger_log_level)

# endregion

# region(enumeratons)

class DisplayMode(Enum):
    preview = 0
    jpeg = 1
    raw = 2

# endregion

class Canvas(tb.Canvas):

# region(class_methods)

    def __init__(self, parent, i):
        super().__init__(parent._root)
        self._parent = parent
        self._nopreview = Config().asset("thumb.jpg")
        
        self._reset()

        self.configure(bg="#1e1e1e")
        self.grid(row=i // self._parent._cols, column=i % self._parent._cols, sticky="nsew", pady=(10,10), padx=(10,10))
        self.configure(bg="#1e1e1e")
        self.bind("<Configure>", self._redraw)
        self.bind("<Button-1>", self._on_mouse_lbutton_press)
        self.bind("<B1-Motion>", self._on_mouse_move)
        self.bind("<ButtonRelease-1>", self._on_mouse_lbutton_release)
        self.bind("<MouseWheel>", self._on_mouse_scroll)
        self.bind("<Button-4>", self._on_mouse_scroll)
        self.bind("<Button-5>", self._on_mouse_scroll)

        self.set_pos(i)

# endregion

# region(methods)

    def set_pos(self, pos):
        try:
            self._pos = pos
            self._reload()
            threading.Thread(target=self._compute_histogram, args=()).start()
            self._reset_pan_zoom()
            self._redraw()
        except Exception as e:
            self._parent._mainfrm.report_error(f"Failed to load image", e)

    def set_display_mode(self, mode: DisplayMode):
        try:
            self._display_mode = mode
            self._reload()
            self._reset_pan_zoom()
            self._redraw()
        except Exception as e:
            self._parent._mainfrm.report_error(f"Failed to change display mode", e)

# endregion

# region(event_handlers)

    def _redraw(self, event=None): 

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

            # def onclick_menu(event):
            #     self._active_local = i
            #     self._redraw()
            #     self._show_popup_menu(event.x_root, event.y_root)

            # canvas.tag_bind("notes_icon", "<Button-1>", onclick_menu)

        # histogram overlay
        def _step_5():
            if self._histogram is None:
                return

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
            text = self._stack.metadata.get_text()
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

            self.create_rectangle(
                box_rect.left, box_rect.top,
                box_rect.right, box_rect.bottom,
                fill="#1e1e1e",
                outline=""
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

                _step_10()

        try:
            if self._root is not None and self._image is not None:
                self.delete("all")
                _step_0()

        except Exception as e:
            self._parent._mainfrm.report_error(f"Failed to redraw canvas", e)

    def _on_mouse_lbutton_press(self, event):
        self._parent._active_local = self._pos
        self._parent._redraw()

    def _on_mouse_move(self, event):
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

    def _on_mouse_lbutton_release(self, event):
        if self._drag_start is None:
            return "break"

        if self._sync_drag:
            for canvas in self._parent._canvases:
                canvas._pan_end()
        else:
            self._pan_end()

        self._parent._root.configure(cursor='')

        return "break"

    def _on_mouse_rbutton_click(self, event):
        self._parent._active_local = self._pos
        self._parent._redraw()
        self._parent._show_popup_menu(event.x_root, event.y_root)

        return "break"

    def _on_mouse_scroll(self, event):
        ctrl = (event.state & 0x0004) != 0
        if self._display_mode == DisplayMode.preview or not ctrl:
            return "break"
        
        direction = 1 if (event.num == 4 or event.delta > 0) else -1
        self._zoom_latest_direction = direction
        self._zoom_latest_pos = (event.x, event.y)

        if self._zoom_redraw_pending:
            return "break"

        self._zoom_redraw_pending = True
        self.after(16, self._process_zoom, direction, event.x, event.y)

        return "break"

# endregion

# region(private_methods)

    def _reset(self):
        self._pos = -1
        self._display_mode = DisplayMode.preview
        self._stack = None
        self._rect = None
        self._histogram = None

        if hasattr(self, "_image") and self._image is not None:
            self._image.close()

        self._image = None

        self._reset_pan_zoom()

    def _reset_pan_zoom(self):
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

    def _compute_histogram(self):
        stack = self._stack

        f = stack.jpg if stack.jpg is not None else stack.raw

        pb = PreviewBuilder()
        histogram = pb.compute_histogram(str(f))

        hist_size = (255, 100)

        for hist in histogram:
            max_v = max(hist)
            vscale = hist_size[1] / max_v if max_v != 0 else 0
            for i, v in enumerate(hist):
                hist[i] = v * vscale

        hscale = hist_size[0] / 255
        color = ("red", "green", "blue", "white")

        img = Image.new('RGB', hist_size, color='#1e1e1e')
        draw = ImageDraw.Draw(img)

        for x in range(255):
            x1 = (x * hscale)
            x2 = ((x + 1) * hscale)
            for c, hist in enumerate(histogram):
                draw.line( [(x1, hist_size[1] - hist[x]), 
                    (x2, hist_size[1] - hist[x+1])], fill=color[c], width=1)

        self._histogram = ImageTk.PhotoImage(img)

    def _reload(self):
        if self._image is not None:
            self._image.close()

        self._stack = self._parent._stacks[self._pos]

        if self._display_mode == DisplayMode.raw and self._stack.raw is not None:
            with rawpy.imread(str(self._stack.raw)) as raw:
                rgb_array = raw.postprocess(use_camera_wb=True, half_size=True)
            self._image = ImageOps.exif_transpose(Image.fromarray(rgb_array))
        elif self._display_mode == DisplayMode.jpeg and self._stack.jpg is not None:
            self._image = ImageOps.exif_transpose(Image.open(self._stack.jpg))
        elif self._display_mode == DisplayMode.preview and self._stack.low is not None:
            self._image = Image.open(self._stack.low)
        else:
            self._image = Image.open(self._nopreview)

    def _pan_start(self, event):
        self._drag_start = (event.x, event.y)

    def _pan_move(self, event):
        self._pan_latest_pos = (event.x, event.y)
        if self._pan_redraw_pending:
            return

        self._pan_redraw_pending = True
        self.after(16, self._process_pan)

    def _pan_end(self):
        self._sync_drag = False
        self._drag_start = None
        self._redraw()

    def _clip(self):
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

    def _calc_fit_zoom(self):
        img_w, img_h = self._image.size
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()

        if img_w <= 0 or img_h <= 0:
            return 0.0

        return min( canvas_w / img_w, canvas_h / img_h)

    def _process_pan(self):
        self._pan_redraw_pending = False

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
            self.after(16, self._process_pan)

    def _process_zoom(self, direction, mouse_x, mouse_y):
        self._zoom_redraw_pending = False

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
            self.after(16, self._process_zoom)

# endregion

