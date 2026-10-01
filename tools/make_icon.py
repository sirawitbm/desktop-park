"""Draw the app icon (the fish) to assets/DesktopPark.ico. Needs Pillow.
Run once and commit the .ico:  python tools/make_icon.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

import art  # noqa: E402


def main():
    fish = art.builtin_by_id()["fish"]
    rows = fish["frames"][0]
    w, h = art.size_of(fish)
    side = max(w, h) + 2
    img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    ox, oy = (side - w) // 2, (side - h) // 2
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                c = fish["palette"][ch].lstrip("#")
                img.putpixel((ox + x, oy + y), tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    big = img.resize((256, 256), Image.NEAREST)
    out = ROOT / "assets" / "DesktopPark.ico"
    big.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Wrote", out)


if __name__ == "__main__":
    main()
