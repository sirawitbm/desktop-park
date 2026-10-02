"""Pixel shape shader - a drawing aid for the built-in art (not used by the app).

Give it a mask (a set of filled pixels) and a colour ramp, and it returns
rows of palette letters with a dark outline, light from the top-left and no
pillow shading - the house style from the pixel-art skill. Output is pasted
into art_pack.py and then touched up by hand.

    python tools/shade.py            # prints the sample shapes
"""

import math


def circles(w, h, blobs, flat_bottom=None):
    """Mask from overlapping circles [(cx, cy, r)], optionally cut flat at a row."""
    mask = set()
    for y in range(h):
        for x in range(w):
            if flat_bottom is not None and y > flat_bottom:
                continue
            if any(math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r for cx, cy, r in blobs):
                mask.add((x, y))
    return mask


def shade(mask, w, h, ramp, outline="k", light=(-1.0, -1.2), bands=(-0.7, -0.1, 0.55), blobs=None):
    """ramp = letters dark..light (3 or 4). Pixels facing the light get the
    lighter letters; the outline wraps everything. With blobs, each pixel is
    shaded by the puff it sits on top of, so a tree crown gets clumps."""
    if not mask:
        return ["." * w for _ in range(h)]
    xs = [x for x, _ in mask]
    ys = [y for _, y in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1, (max(xs) - min(xs) + 1) / 2), max(1, (max(ys) - min(ys) + 1) / 2)
    lx, ly = light
    norm = math.hypot(lx, ly)
    lx, ly = lx / norm, ly / norm
    grid = [["."] * w for _ in range(h)]
    for x, y in mask:
        edge = any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            grid[y][x] = outline
            continue
        if blobs:
            # the puff this pixel belongs to: the one it is deepest inside (later puffs win ties)
            bx, by, br = max(reversed(blobs), key=lambda b: b[2] - math.hypot(x + 0.5 - b[0], y + 0.5 - b[1]))
            nx, ny = (x + 0.5 - bx) / br, (y + 0.5 - by) / br
        else:
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        d = nx * lx + ny * ly                       # +1 faces the light
        level = sum(d > b for b in bands)           # 0..3
        grid[y][x] = ramp[min(level, len(ramp) - 1)]
    return ["".join(r) for r in grid]


def show(rows):
    print("\n".join('        "%s",' % r for r in rows))


if __name__ == "__main__":
    w, h = 22, 18
    b = [(11, 12.5, 6), (6.5, 10.5, 5.5), (16, 11, 5.5), (11, 7, 6.2)]
    show(shade(circles(w, h, b), w, h, "qgGl", blobs=b))
