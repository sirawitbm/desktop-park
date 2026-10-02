"""Draw the app icon (the park tile in art.APP_ICON) to assets/DesktopPark.ico.
Needs Pillow. Run once and commit the .ico:  python tools/make_icon.py

Every size is the 16 x 16 design scaled by whole pixels (nearest neighbour),
so the icon stays crisp at 16, 32, 48 ... 256 px instead of being blurred
by a downscale.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

import art  # noqa: E402
from art_pack import PAL  # noqa: E402


def base_image():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(art.APP_ICON):
        for x, ch in enumerate(row):
            if ch != ".":
                c = PAL[ch].lstrip("#")
                img.putpixel((x, y), tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    return img


def main():
    base = base_image()
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [base.resize((s, s), Image.NEAREST) for s in sizes]
    out = ROOT / "assets" / "DesktopPark.ico"
    images[-1].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
    print("Wrote", out)


if __name__ == "__main__":
    main()
