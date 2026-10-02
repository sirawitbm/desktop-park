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


# The park's own pixels take on the time of day (never your screen): a warm
# sunset tint at dusk and dawn, cool moonlight at night. Things near a lamp or
# fire stay lit.
SUNSET = (214, 104, 96)
MOON = (24, 34, 86)
MAX_TINT = 0.62


def tint(night, light=0.0):
    """(r, g, b, alpha) to wash over a picture. night 0..1, light 0..1 (how
    close it is to a lamp or fire). alpha 0 means leave the picture alone."""
    t = _smooth((night - 0.25) / 0.6)
    rgb = tuple(int(a + (b - a) * t) for a, b in zip(SUNSET, MOON))
    alpha = night * MAX_TINT * (1.0 - 0.85 * max(0.0, min(1.0, light)))
    return rgb + (round(alpha, 3),)


def bucket(night, light):
    """Round the levels so only a few tinted copies of each picture are made."""
    return round(night * 8) / 8, round(max(0.0, min(1.0, light)) * 4) / 4


# The sun and moon cross the top of the screen, left corner to right corner:
# the sun from 06:00 to 18:30, the moon from 18:30 to 06:00.
SUNRISE, SUNSET_H = 6.0, 18.5


def sky(when=None, mode="clock"):
    """("sun" or "moon", progress 0..1 across the sky). Always day / night
    park the sun or moon a third of the way across."""
    if mode == "day":
        return "sun", 0.35
    if mode == "night":
        return "moon", 0.35
    when = when or datetime.datetime.now()
    h = when.hour + when.minute / 60 + when.second / 3600
    if SUNRISE <= h < SUNSET_H:
        return "sun", (h - SUNRISE) / (SUNSET_H - SUNRISE)
    night_len = 24 - SUNSET_H + SUNRISE
    since = h - SUNSET_H if h >= SUNSET_H else h + 24 - SUNSET_H
    return "moon", since / night_len


def arc(progress, width, height, size):
    """Top-left corner for the sun/moon picture: low in the corners, highest
    at midday / midnight, always within the top fifth of the screen."""
    import math
    margin = size
    x = margin + progress * (width - 2 * margin) - size / 2
    top, low = height * 0.03, height * 0.18
    y = low - (low - top) * math.sin(math.pi * min(1.0, max(0.0, progress)))
    return x, y


def clock_text(when=None):
    when = when or datetime.datetime.now()
    return when.strftime("%H:%M")
