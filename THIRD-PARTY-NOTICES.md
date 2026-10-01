# Third-party notices

Desktop Park's own code and pixel art are released under the MIT License
(see `LICENSE`). The Windows download also bundles the software below, which
keeps its own license.

## Qt for Python (PySide6) and Qt

- Used for: every window, drawing, menus and the tray icon.
- License: GNU Lesser General Public License v3 (LGPL-3.0).
- Copyright: The Qt Company Ltd. and other contributors.
- Source code and license text: <https://www.qt.io/qt-for-python>,
  <https://code.qt.io/>, <https://www.gnu.org/licenses/lgpl-3.0.html>.

Desktop Park uses PySide6 unmodified. Under the LGPL you may replace the Qt
libraries with your own build: the easiest way is to run Desktop Park from
source (`pip install PySide6` then `python desktop_park.py`), which uses
whichever PySide6 you install.

## PyInstaller

- Used for: packing the app into a single `.exe`.
- License: GPL-2.0 with the PyInstaller bootloader exception, which allows
  the packed app to use any license. <https://pyinstaller.org/en/stable/license.html>

## Python

- The `.exe` contains a copy of the Python runtime.
- License: Python Software Foundation License. <https://docs.python.org/3/license.html>

## Fonts

The font is bundled in `assets/fonts/` with its license file and is used
unmodified. It is licensed under the SIL Open Font License 1.1
(<https://openfontlicense.org>), which allows bundling it with software. It is
used by the Pixel look.

- **Pixelify Sans** - Copyright 2021 The Pixelify Sans Project Authors
  (<https://github.com/eifetx/Pixelify-Sans>). License: `assets/fonts/OFL-PixelifySans.txt`.

## Colour palettes

No art was copied. Two published colour palettes were used as starting
points for the colours:

- **Sweetie 16** by GrafxKid - 11 of its 16 colours are in the shared
  palette of the newer built-in art (`art_pack.py`).
  <https://lospec.com/palette-list/sweetie-16>
- **PICO-8 palette** by Lexaloffle Games - the first 16 colours of the
  drawing editor's colour picker. <https://www.lexaloffle.com/pico-8.php>
