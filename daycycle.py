"""Day and night, from your computer's clock. Pure logic so it can be tested.

night_level() is 0.0 in full day and 1.0 in full night, easing through dusk
(18:00-19:30) and dawn (05:30-07:00). It never darkens your screen - the app
uses it for glowing lamps, fireflies and sleepy pets.
"""

import datetime

MODES = ("clock", "day", "night")
LABELS = {"clock": "Follow my clock", "day": "Always day", "night": "Always night"}

DUSK = (18.0, 19.5)       # hours: night fades in between these
DAWN = (5.5, 7.0)         # hours: night fades out between these


def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def night_level(when=None, mode="clock"):
    if mode == "day":
        return 0.0
    if mode == "night":
        return 1.0
    when = when or datetime.datetime.now()
    h = when.hour + when.minute / 60 + when.second / 3600
    if DAWN[1] <= h < DUSK[0]:
        return 0.0
    if DUSK[0] <= h < DUSK[1]:
        return _smooth((h - DUSK[0]) / (DUSK[1] - DUSK[0]))
    if DAWN[0] <= h < DAWN[1]:
        return 1.0 - _smooth((h - DAWN[0]) / (DAWN[1] - DAWN[0]))
    return 1.0


def is_halloween_season(today=None):
    """October: the Halloween pictures move to the top of the board."""
    today = today or datetime.date.today()
    return today.month == 10
