"""Write the Theme Pack file (packs/theme_pack.py -> .parkpack) and check it
reads back through the app's own loader. release.ps1 runs this; the pack's
installer (pack-installer.iss) wraps the file.

    python tools/build_pack.py [out_file]
    (default: dist/release/DesktopPark-ThemePack-v<app version>.parkpack)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packs"))

import store  # noqa: E402
import theme_pack  # noqa: E402


def app_version():
    source = (ROOT / "desktop_park.py").read_text(encoding="utf-8")
    return re.search(r'(?m)^__version__\s*=\s*"([^"]+)"', source).group(1)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT / "dist" / "release" / ("DesktopPark-ThemePack-v%s.parkpack" % app_version()))
    pack = theme_pack.build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, separators=(",", ":")), encoding="utf-8")

    back = store.read_pack(str(out))                 # exactly what the app will see
    if len(back["drawings"]) != len(pack["drawings"]) or len(back["parks"]) != len(pack["parks"]):
        raise SystemExit("The pack did not survive the app's checks - see store.read_pack().")
    known = {a["id"] for a in store._builtin_art()} | {a["id"] for a in back["drawings"]}
    for park in back["parks"]:
        missing = {o["art"] for o in park["objects"]} - known
        if missing:
            raise SystemExit("%s uses unknown pictures: %s" % (park["name"], ", ".join(sorted(missing))))
    print("%s: %d parks, %d pictures, %d KB" % (out, len(back["parks"]), len(back["drawings"]),
                                               out.stat().st_size // 1024))


if __name__ == "__main__":
    main()
