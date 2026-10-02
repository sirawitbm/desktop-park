# Park Polish And Presets: Review Handoff

Branch: `feat/park-polish-harness-review`, continuing the work from
`feat/park-polish-and-presets`, based on local `main`, which was four commits
ahead of `origin/main` when this work began. This pass is committed locally;
no version bump, release, or push was made. Review this branch against local
`main` to isolate the changes below.

## AutoHarness And Copilot

[AutoHarness](https://github.com/tigerless-labs/autoharness) is a self-learning
skills plugin for Claude Code, not a Desktop Park runtime dependency or a
test harness. The user already has it in Claude Code. Upstream ships Claude
Code plugin hooks and agents, not a Copilot integration, so it was not attached
to this GitHub Copilot session. A Copilot port would need to adapt the session
capture, reflection, skill promotion and recall lifecycle; installing only
its MCP server would not provide that full behavior.

No AutoHarness configuration or generated session files are included in this
branch. Do not commit private session evidence or transcripts.

## Implemented

- Drawing saves now write synchronously. A failed write keeps the editor open
  and rolls back the attempted library/scene change; retries do not duplicate
  objects. The board has a persistent warning and Retry control, including a
  folded-bar indicator. Repeated failures produce only one tray notification
  until a save succeeds. Tray Quit refuses to exit on write failure.
- Editor dismissal, Cancel and Escape use Save / Discard / Cancel when dirty.
  Changes to frames, canvas size, name, kind and movement count as edits.
  Undo back to the original content clears dirty state.
- Custom frames are normalized to the first frame's rectangular canvas, with
  missing pixels transparent and excess pixels cropped. Invalid palette colors,
  non-finite positions and wrong container types are rejected or defaulted.
- Ground shadows are included in explicit edit repaint bounds. Removing,
  resizing and beginning a drag erase the old shadow. Night shading invalidates
  when a light moves, including sub-16-pixel moves, or changes radius.
- Park Undo stores up to 40 scene snapshots with their source screen size.
  Add, remove, clear, drag, scale, movement, flip, order, copy and preset loading
  are undoable. Pet wandering and reactions do not create Undo entries.
  History is session-only and is not a custom-drawing history.
- Up to 32 named parks retain objects, source screen dimensions, weather,
  auto-weather, time mode and sky visibility. Loading adapts to the current
  screen and can be undone, including the restored environment settings.
  Overwrite/delete/load-replacement use confirmations. Preset saves are
  synchronous and restore the previous preset list on write failure.
- `.parkart` drawing files are versioned JSON. Imports are capped at 1 MB,
  validated and assigned fresh UUID-based IDs. Export is available on board
  picture context menus; import is on the board and tray. Presets reference
  drawings from the shared library. Deleting a drawing removes its preset uses.
- Sprite pixmaps use LRU eviction: at most 2,000 entries and an estimated 48 MiB
  of pixel storage. This is a pixel-memory estimate, not total process/GPU RAM.
  Art replacement invalidates its cache entries and updates memory accounting.
- Opt-in low-power mode uses 67 ms movement and 100 ms weather updates. The
  simulation advances by the selected interval, so time does not run at half
  speed. The setting is saved; native compositor/power consumption is unmeasured.
- Weather's 700-particle bound now includes rain splashes. A 4K profiling run
  exposed the previous post-spawn overshoot; a regression covers it.
- Shared-scale thumbnails have a larger whole-pixel hover preview and name.
  Trees use clustered rather than diagonal-band shading. Cherry, palm and
  spooky tree now occupy the 24-27 pixel tree band. Cat, dog and duck have four
  distinct walk frames; cat, dog, duck and bunny have blink/sleep poses.
- CI installs PySide6 so Qt tests execute rather than silently skip. Windows
  Python 3.10 and 3.13 remain the configured CI targets.

## Verification

Run from the project folder:

```powershell
python -m unittest discover -s tests
python tools/profile_weather.py --frames 32
python tools/contact_sheets.py docs/polish
python tools/screenshots.py docs/polish
git diff --check
```

The image tools need Pillow in addition to the runtime requirements. Render
with `QT_QPA_PLATFORM=offscreen` for completely headless runs. The screenshot
tool isolates persistence in a temporary directory and does not alter your
real park. Off-screen Windows renders explicitly load installed Segoe fonts.

Local suite: **104 tests**, including the existing 70 plus loader, editor,
save-failure, repaint, Undo, preset, import/export, cache and 4K weather cases.
Local testing used Python 3.14.6 with PySide6. GitHub CI itself has not run yet.

Weather profiler, 32 measured frames after four warm-up frames; Windows system
Python 3.14.6, off-screen Qt raster rendering. Scenes use ten seconds of seeded
weather simulation at full night. This is not a before/after speedup claim.

| Scene | 1920 x 1040 median | 3840 x 2080 median |
|---|---:|---:|
| Clear night | 0.35 ms | 2.34 ms |
| Rain night | 1.06 ms | 4.01 ms |
| Snow night | 0.52 ms | 3.18 ms |

All measured particle counts were at most 700. Low power halves weather update
requests from 20/s to 10/s, but actual CPU/GPU/power savings still need a native
Windows measurement. No native mixed-DPI or game-overlay claim is made.

## Visual Review

- [Changed sprite sheet](polish/changed-sprites.png)
- [Every pet frame and pose](polish/1_pets.png)
- [Decorations and resized trees](polish/2_decor.png)
- [Animated walk/blink/sleep preview](polish/animation.gif)
- [Modern and Pixel boards](polish/looks.png)
- [Folded bars](polish/hotbar.png)
- [Editor](polish/editor.png)
- [Hover preview](polish/hover.png)
- [Persistent save warning](polish/save-warning.png)
- [Dark background](polish/park.png), [light background](polish/park-light.png),
  [busy background](polish/park-busy.png)

## Reviewer Checklist

1. Force an unwritable save location: try drawing Save, Retry, and tray Quit.
   Confirm no false successful close, duplicated drawings, or silent exit.
2. Close/Escape a modified editor, including metadata-only changes. Check all
   three choices, and confirm Save completes the editor only once.
3. Remove/resize/drag grounded items on a light desktop. No stale shadow pixels
   should remain; moving/resizing lamps should immediately retint nearby items.
4. Use Undo across add, drag, delete, clear and preset loads, then change screens.
   Verify ground contact, object order, environment state and disabled controls.
5. Save, rename, overwrite and delete presets; restart and load them. Import the
   same drawing twice, export/reimport animations, and try malformed files.
6. Inspect animations at normal size, particularly cat/dog feet, duck waddle,
   blink duration, sleeping silhouettes and recolored tree foliage.
7. On real Windows, test click-through/lock and taskbar folding at 100%, 150% and
   200% DPI, screen unplug/replug and borderless games. Measure idle/night/4K
   CPU and GPU use before making a performance claim.

## Deliberately Deferred

- Optional light sticker rims: painted rims alter the overlay's mouse-hit
  surface and need a coordinated hit-test design and native verification.
- Per-effect weather dirty regions: low-power mode and the measured profiler
  land first; stars, glows, clouds and translucent rays need overlap-aware bounds.
- More species' walk/hop/sleep redraws, variable animation rates, pixel-grid
  rain/rays, a ground strip and first-run-tip redesign.
- Built-in blink/sleep poses are not editable/exported with user drawings yet.
  Existing custom frame animations still work unchanged.
- Native installer/build, signing, release metadata and Python CI outcomes.