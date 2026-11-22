"""Instagram-style cards: a square canvas with a map or chart, headings and footnotes.

Nothing here reads a hardcoded path. You pass the images, an optional
background and the fonts as arguments. With no fonts given, matplotlib's own
DejaVu Sans is used; with no background, a plain colour.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont

CANVAS = 4000
PURPLE = (46, 26, 89)
BLACK = (0, 0, 0)


@dataclass
class CardText:
    """All the words on a card. Leave anything you do not need empty."""

    header_1: str = ""
    header_2: str = ""
    header_3: str = ""
    sub_header_1: str = ""
    sub_header_2: str = ""
    sub_header_3: str = ""
    # Number shown at the bottom and top of the colour bar.
    scale_min: str = ""
    scale_max: str = ""
    # The big number box, for example a national average.
    section_1: str = ""
    section_2: str = ""
    section_3: str = ""
    copyright: str = ""
    footer_1: str = ""
    footer_2: str = ""
    footer_3: str = ""
    footer_4: str = ""
    # 1 = a one-line title (header_1, header_2); 2 = a two-line title.
    header_lines: int = 1


@dataclass
class CardFonts:
    """Font files for the card. Any left as None falls back to DejaVu Sans."""

    heading: Optional[str] = None
    body: Optional[str] = None
    italic: Optional[str] = None
    italic_medium: Optional[str] = None
    _cache: dict = field(default_factory=dict, repr=False)

    def get(self, role, size):
        key = (role, size)
        if key not in self._cache:
            path = getattr(self, role) or self.heading or self.body or fm.findfont("DejaVu Sans")
            self._cache[key] = ImageFont.truetype(os.fspath(path), size)
        return self._cache[key]


def _fonts(fonts):
    if fonts is None:
        return CardFonts(heading=fm.findfont("DejaVu Sans"), body=fm.findfont("DejaVu Sans"), italic=fm.findfont("DejaVu Sans Oblique"), italic_medium=fm.findfont("DejaVu Sans Oblique"))
    if isinstance(fonts, str):
        return CardFonts(heading=fonts, body=fonts, italic=fonts, italic_medium=fonts)
    return fonts


def new_canvas(background=None, background_color=(255, 255, 255), size=CANVAS):
    """The empty card. ``background`` is an image file you provide; otherwise a flat colour."""
    if background is not None:
        img = Image.open(background).convert("RGB")
        return img.resize((size, size)) if img.size != (size, size) else img
    return Image.new("RGB", (size, size), background_color)


def _fit(image, width):
    height = width * image.size[1] / image.size[0]
    return image.resize((int(width), int(height)), Image.LANCZOS)


def _prepare_colorbar(colorbar_image, crop):
    bar = Image.open(colorbar_image).convert("RGBA")
    bar = bar.resize((1629, 1629), Image.LANCZOS).crop(crop).resize((1200, 127))
    return bar.rotate(90, expand=1)


def map_card(
    map_image,
    colorbar_image,
    text,
    fonts=None,
    background=None,
    background_color=(255, 255, 255),
    layout="state",
    colorbar_crop=(148, 1185, 1541, 1333),
):
    """Card with the map, a vertical colour bar and all the text.

    ``map_image`` and ``colorbar_image`` are PNG files saved from the map and
    colour bar functions (save the map with a transparent background).
    ``layout`` is ``"state"`` or ``"district"``: the district layout draws the
    map bigger and the title smaller. Returns a PIL image.
    """
    fonts = _fonts(fonts)
    img = new_canvas(background, background_color)
    size, offset = ((5000, (-490, -390)) if layout == "state" else (5800, (-990, -490)))
    big_map = Image.open(map_image).convert("RGBA").resize((size, size), Image.LANCZOS)
    img.paste(big_map, offset, mask=big_map)
    bar = _prepare_colorbar(colorbar_image, colorbar_crop)
    img.paste(bar, (50, 2400), mask=bar)
    draw = ImageDraw.Draw(img)
    _header(draw, fonts, text, layout)
    _copyright(draw, fonts, text)
    _minmax(draw, fonts, text)
    _footer(draw, fonts, text)
    _midsection(draw, fonts, text)
    return img


def chart_card(chart_image, text, fonts=None, background=None, background_color=(255, 255, 255), layout="state"):
    """Card with a ranked bar chart (or any transparent PNG) under the title."""
    fonts = _fonts(fonts)
    img = new_canvas(background, background_color)
    chart = _fit(Image.open(chart_image).convert("RGBA"), 3800)
    img.paste(chart, (100, 800), mask=chart)
    draw = ImageDraw.Draw(img)
    _header(draw, fonts, text, layout)
    _copyright(draw, fonts, text)
    return img


def save_card(img, path, dpi=(300, 300), quality=95):
    folder = os.path.dirname(os.fspath(path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    img.save(path, quality=quality, dpi=dpi)


def _header(d, fonts, t, layout):
    f_top = fonts.get("heading", 134)
    f_main = fonts.get("heading", 203 if layout == "state" else 80)
    f_sub = fonts.get("body", 68)
    x = 2740
    if t.header_lines == 1:
        d.text((x, 324), t.header_1, font=f_top, fill=BLACK, align="center", anchor="mb")
        d.text((x, 360), t.header_2, font=f_main, fill=BLACK, align="center", anchor="mt")
        subs = (590, 690, 790) if layout == "state" else (490, 590, 690)
    else:
        d.text((x, 324), t.header_1, font=f_top, fill=BLACK, align="center", anchor="mb")
        d.text((x, 464), t.header_2, font=f_top, fill=BLACK, align="center", anchor="mb")
        d.text((x, 490), t.header_3, font=f_main, fill=BLACK, align="center", anchor="mt")
        subs = (690, 790, 890) if layout == "state" else (590, 690, 790)
    for y, line in zip(subs, (t.sub_header_1, t.sub_header_2, t.sub_header_3)):
        d.text((x, y), line, font=f_sub, fill=PURPLE, align="center", anchor="mt")


def _copyright(d, fonts, t):
    d.text((3950, 3950), t.copyright, font=fonts.get("italic_medium", 52), fill=BLACK, align="center", anchor="rs")


def _minmax(d, fonts, t):
    f = fonts.get("heading", 60)
    d.text((200, 3550), t.scale_min, font=f, fill=BLACK, align="center", anchor="ls")
    d.text((200, 2500), t.scale_max, font=f, fill=BLACK, align="center", anchor="ls")


def _footer(d, fonts, t):
    f = fonts.get("italic_medium", 52)
    f_last = fonts.get("italic", 52)
    d.text((55, 3755), t.footer_1, font=f, fill=BLACK, align="center", anchor="ls")
    d.text((55, 3820), t.footer_2, font=f, fill=BLACK, align="center", anchor="ls")
    d.text((55, 3885), t.footer_3, font=f, fill=BLACK, align="center", anchor="ls")
    d.text((55, 3950), t.footer_4, font=f_last, fill=BLACK, align="center", anchor="ls")


def _midsection(d, fonts, t):
    d.text((3150, 2480), t.section_1, font=fonts.get("heading", 80), fill=BLACK, align="center", anchor="mb")
    d.text((3150, 2790), t.section_2, font=fonts.get("body", 300), fill=BLACK, align="center", anchor="mb")
    d.text((3150, 2850), t.section_3, font=fonts.get("heading", 80), fill=BLACK, align="center", anchor="mt")


def compact_map_card(map_image, colorbar_image, text, fonts=None, colorbar_crop=(148, 1185, 1541, 1333),
                     map_crop=(800, 600, 4300, 4400), ink=(33, 42, 55)):
    """Tight map image with a horizontal colour bar and a "Scale" caption inside it.

    The newest layout from the original notebooks: no heading and no
    background, so the result can be placed on any page. The image is
    transparent where the map is. ``text.scale_min`` and ``text.scale_max``
    label the two ends and ``text.section_1`` to ``section_3`` give the big
    number box.
    """
    fonts = _fonts(fonts)
    big_map = Image.open(map_image).convert("RGBA").resize((5000, 5000), Image.LANCZOS).crop(map_crop)
    bar = Image.open(colorbar_image).convert("RGBA").resize((1629, 1629), Image.LANCZOS).crop(colorbar_crop).resize((1200, 127))
    big_map.paste(bar, (1900, 500), mask=bar)
    d = ImageDraw.Draw(big_map)
    small = fonts.get("body", 50)
    d.text((1920, 520), text.scale_min, font=small, fill=ink, align="center", anchor="mm")
    d.text((3050, 520), text.scale_max, font=small, fill=ink, align="center", anchor="mm")
    d.text((2485, 670), "Scale", font=small, fill=ink, align="center", anchor="mm")
    d.text((2700, 2280), text.section_1, font=fonts.get("body", 80), fill=ink, align="center", anchor="mb")
    d.text((2700, 2590), text.section_2, font=fonts.get("body", 300), fill=ink, align="center", anchor="mb")
    d.text((2700, 2650), text.section_3, font=fonts.get("body", 80), fill=ink, align="center", anchor="mt")
    return big_map
