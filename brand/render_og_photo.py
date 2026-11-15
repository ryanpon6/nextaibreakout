"""Render the default 1200x630 Open Graph / X share image.

Background: brand/og-source.jpg (1280x720; a white robot figurine on the
right, empty pale blue-grey space on the left). The repo ships Syne only as
fonts/Syne-var.woff2, so this script instantiates Syne ExtraBold (800) and
Syne SemiBold (600) to temporary TTF files with fontTools, then draws the
text with Pillow. The headline is exactly "GROK BOT TIPS & TRICKS" in ink
#0F1B3D, wrapped to two lines; "nextaibreakout.com" sits small below it in
muted #46506B. No fake UI.

Usage:
  python3 brand/render_og_photo.py
"""
from __future__ import annotations

import os
import tempfile

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "brand", "og-source.jpg")
SYNE = os.path.join(ROOT, "fonts", "Syne-var.woff2")
STATIC = os.path.join(ROOT, "static")
SHARED = "/workspace/shared/nab-relaunch/og"

W, H = 1200, 630
# Source is 1280x720 (16:9). Scale to width 1200 (1200x675) and crop 20 px
# from the top so the robot and notebook stay fully in frame and the left
# wall still has room for type. X may crop ~15 px from each edge, so type
# stays inside a 72 px left / 60 px top-bottom safe area and ends well left
# of the robot (robot body starts around x=742 in this crop).
CROP_TOP = 20
INK = (0x0F, 0x1B, 0x3D)
MUT = (0x46, 0x50, 0x6B)
HEAD_LINES = ("GROK BOT", "TIPS & TRICKS")
URL = "nextaibreakout.com"
# Mid-left placement: headline on the wall, URL just above the table edge.
LEFT = 72
TOP = 160
HEAD_SIZE = 56
URL_SIZE = 26
LINE_GAP = 10
URL_GAP = 18
SCALE = 2  # draw at 2x, then downsample for crisp edges


def _instance(wght: int, dest: str) -> None:
    font = TTFont(SYNE, recalcBBoxes=False, recalcTimestamp=False)
    instancer.instantiateVariableFont(font, {"wght": wght}).save(dest)


def _cover_crop(im: Image.Image) -> Image.Image:
    scale = W / im.width
    resized = im.resize((W, int(round(im.height * scale))), Image.Resampling.LANCZOS)
    top = min(CROP_TOP, resized.height - H)
    return resized.crop((0, top, W, top + H))


def render_og_default(dest_jpg: str | None = None, dest_png: str | None = None) -> Image.Image:
    """Composite the default share image and write JPEG (canonical) plus PNG."""
    if dest_jpg is None:
        dest_jpg = os.path.join(STATIC, "og-default.jpg")
    if dest_png is None:
        dest_png = os.path.join(STATIC, "og-default.png")

    bg = _cover_crop(Image.open(SRC).convert("RGB"))
    canvas = bg.resize((W * SCALE, H * SCALE), Image.Resampling.LANCZOS)

    with tempfile.TemporaryDirectory() as td:
        extra = os.path.join(td, "Syne-ExtraBold.ttf")
        semi = os.path.join(td, "Syne-SemiBold.ttf")
        _instance(800, extra)
        _instance(600, semi)
        head = ImageFont.truetype(extra, HEAD_SIZE * SCALE)
        url_font = ImageFont.truetype(semi, URL_SIZE * SCALE)
        draw = ImageDraw.Draw(canvas)
        x = LEFT * SCALE
        y = TOP * SCALE
        for line in HEAD_LINES:
            draw.text((x, y), line, font=head, fill=INK, anchor="lt")
            y += head.getmetrics()[0] + LINE_GAP * SCALE
        y += (URL_GAP - LINE_GAP) * SCALE
        draw.text((x, y), URL, font=url_font, fill=MUT, anchor="lt")

    canvas = canvas.resize((W, H), Image.Resampling.LANCZOS)

    os.makedirs(os.path.dirname(dest_jpg) or ".", exist_ok=True)
    # 4:4:4, quality 95: PNG was ~460 KB; this stays under 300 KB with sharp type.
    canvas.save(dest_jpg, "JPEG", quality=95, optimize=True, subsampling=0)
    canvas.save(dest_png, "PNG", optimize=True)
    # Keep the long-standing /og.png and /og-default.png URLs in sync.
    og_png = os.path.join(os.path.dirname(dest_png), "og.png")
    if os.path.isdir(os.path.dirname(og_png)):
        canvas.save(og_png, "PNG", optimize=True)
    og_jpg = os.path.join(os.path.dirname(dest_jpg), "og.jpg")
    if os.path.abspath(og_jpg) != os.path.abspath(dest_jpg) and os.path.isdir(os.path.dirname(og_jpg)):
        canvas.save(og_jpg, "JPEG", quality=95, optimize=True, subsampling=0)
    return canvas


def main() -> None:
    jpg = os.path.join(STATIC, "og-default.jpg")
    png = os.path.join(STATIC, "og-default.png")
    im = render_og_default(jpg, png)
    os.makedirs(SHARED, exist_ok=True)
    shared_png = os.path.join(SHARED, "og-default.png")
    shared_jpg = os.path.join(SHARED, "og-default.jpg")
    im.save(shared_png, "PNG", optimize=True)
    im.save(shared_jpg, "JPEG", quality=95, optimize=True, subsampling=0)
    print(
        f"wrote {jpg} ({os.path.getsize(jpg)} bytes), "
        f"{png} ({os.path.getsize(png)} bytes), "
        f"{shared_png}"
    )


if __name__ == "__main__":
    main()
