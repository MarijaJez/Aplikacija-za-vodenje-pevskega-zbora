"""Generate install icons from the shapes and colors in icon.svg."""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).parent
SCALE = 4
SIDE = 512 * SCALE


def box(*coordinates):
    return tuple(round(value * SCALE) for value in coordinates)


canvas = Image.new("RGB", (SIDE, SIDE), "#163a45")
draw = ImageDraw.Draw(canvas)
draw.ellipse(box(82, 82, 430, 430), fill="#287080")

# The note follows the matching SVG icon; the filled square keeps it maskable.
draw.polygon([box(x, y) for x, y in [(140, 133), (310, 104), (310, 152), (140, 181)]], fill="white")
draw.polygon([box(x, y) for x, y in [(268, 137), (310, 130), (310, 341), (268, 341)]], fill="white")
draw.ellipse(box(144, 294, 263, 424), fill="white")
draw.ellipse(box(328, 126, 372, 170), fill="#e0ae60")

for size, name in ((192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")):
    canvas.resize((size, size), Image.Resampling.LANCZOS).save(HERE / name, optimize=True)
