"""How things in the park move. Pure logic - no windows - so it can be tested.

Coordinates are screen pixels inside the park; (0, 0) is the top-left and
the ground is the bottom edge (just above the taskbar).
"""

import math
import random

GRAVITY = 900.0          # px/s^2
ANIM_FPS_MOVING = 10     # pets moving: the "10fps" pixel look
ANIM_FPS_STILL = 3       # decorations with frames (seaweed) sway slowly
MIN_SCALE, MAX_SCALE = 1, 12

# What a pet can do when you click it. One is picked at random each time.
REACTIONS = ("love", "jump", "spin", "shake", "dance", "sleep", "dash")
# How long each one lasts, in seconds.
REACTION_TIME = {"love": 0.6, "jump": 0.8, "spin": 0.8, "shake": 0.7,
                 "dance": 1.6, "sleep": 4.0, "dash": 1.2}
# How much the wind pushes things that move this way (flyers feel it most).
WIND_PUSH = {"fly": 0.15, "swim": 0.07}   # gentle, or they all end up on one side
# While doing these, the pet stops its normal wandering.
# At night, a resting pet dozes off now and then (chance per second at full night).
NAP_CHANCE = 1 / 25
NAP_TIME = (8.0, 20.0)
HOLDS_STILL = ("spin", "shake", "dance", "sleep")


class Thing:
    """One object placed in the park."""

    def __init__(self, uid, art_id, w, h, x=0.0, y=0.0, scale=4,
                 behavior="stay", flip=False, speed_mult=1.0, is_pet=False):
        self.uid = uid
        self.art_id = art_id
        self.art_w, self.art_h = w, h        # size in art pixels
        self.x, self.y = float(x), float(y)
        self.scale = scale
        self.behavior = behavior
        self.flip = flip                     # True = facing left
        self.speed_mult = speed_mult         # snails are slow, bees are not
        self.is_pet = is_pet                 # decorations never react or nap
        self.vx = self.vy = 0.0
        self.timer = 0.0                     # seconds left in this state
        self.state = "idle"
        self.target = None                   # (x, y) for swimmers/flyers
        self.speed = 0.0
        self.anim_t = random.random()
        self.age = random.random() * 10      # drives the swim bob
        self.dragging = False
        self.reaction = None                 # what it's doing after a click
        self.reaction_t = 0.0
        self._fx_t = 0.0                     # time until the next particle

    # -- size ---------------------------------------------------------------
    @property
    def w(self):
        return self.art_w * self.scale

    @property
    def h(self):
        return self.art_h * self.scale

    def rect(self):
        return (self.x + self.shake(), self.y + self.bob(), self.w, self.h)

    def bob(self):
        if self.behavior == "swim" and not self.dragging and self.reaction != "sleep":
            return math.sin(self.age * 2.2) * max(2, self.scale * 0.8)
        return 0.0

    def shake(self):
        if self.reaction == "shake":
            return math.sin(self.reaction_t * 60) * max(2, self.scale * 0.7)
        return 0.0

    def moving(self):
        return abs(self.vx) > 1 or abs(self.vy) > 1

    def frame_index(self, n_frames, is_pet):
        if n_frames <= 1 or self.reaction == "sleep":
            return 0
        if (self.moving() or self.dragging or self.reaction == "dance"
                or (is_pet and self.behavior in ("swim", "fly"))):
            return int(self.anim_t * ANIM_FPS_MOVING) % n_frames
        if not is_pet:
            return int(self.anim_t * ANIM_FPS_STILL) % n_frames
        return 0

    def to_dict(self):
        return {"uid": self.uid, "art": self.art_id, "x": round(self.x),
                "y": round(self.y), "scale": self.scale,
                "behavior": self.behavior, "flip": self.flip}


class World:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.things = []        # drawn in order: last one is in front
        # little pictures that float up and fade: [kind, x, y, life, vx, vy, max_life]
        self.particles = []
        self._last_reaction = {}
        self.wind = 0.0         # px/s from the weather; pushes flyers, swimmers, particles
        self.night = 0.0        # 0 = day, 1 = night (daycycle.py): pets get sleepy

    @property
    def ground(self):
        return self.height

    def resize(self, width, height):
        self.width, self.height = width, height
        for t in self.things:
            self.clamp(t)

    def relocate(self, width, height):
        """The park moved to a screen of another size: keep everything at the
        same place across the width, and whatever stood on the ground on it."""
        old_w, old_h = max(1, self.width), max(1, self.height)
        grounded = {id(t) for t in self.things if self.on_ground(t)}
        self.width, self.height = width, height
        for t in self.things:
            centre = (t.x + t.w / 2) / old_w
            t.x = centre * width - t.w / 2
            if id(t) in grounded:
                t.y = self.ground - t.h
            else:
                t.y = t.y / old_h * height
            t.target = None
            self.clamp(t)
        for p in self.particles:
            p[1] = p[1] / old_w * width
            p[2] = p[2] / old_h * height

    def clamp(self, t):
        t.x = min(max(t.x, 0), max(0, self.width - t.w))
        t.y = min(max(t.y, 0), max(0, self.ground - t.h))

    def on_ground(self, t):
        return t.y + t.h >= self.ground - 0.5

    def spawn(self, kind, x, y, life=1.2, vx=0.0, vy=-40.0):
        self.particles.append([kind, x, y, life, vx, vy, life])

    def _head(self, t):
        """Where particles come out: above the pet's head."""
        return t.x + t.w * (0.35 if t.flip else 0.65), t.y

    # -- placing -------------------------------------------------------------
    def drop_spot(self, t, rng=random):
        """A random place to put something new."""
        x = rng.uniform(0, max(0, self.width - t.w))
        if t.behavior in ("swim", "fly"):
            y = rng.uniform(self.height * 0.25, max(self.height * 0.25, self.height * 0.75 - t.h))
        else:
            y = self.ground - t.h
        return x, y

    # -- input ---------------------------------------------------------------
    def poke(self, t, rng=random, reaction=None):
        """The user clicked a pet: it reacts in a random way.
        Returns the reaction's name."""
        if reaction is None:
            choices = [r for r in REACTIONS if r != self._last_reaction.get(t.uid)]
            reaction = rng.choice(choices)
        self._last_reaction[t.uid] = reaction
        t.reaction, t.reaction_t, t._fx_t = reaction, REACTION_TIME[reaction], 0.0
        hx, hy = self._head(t)
        grounded = t.behavior in ("walk", "hop")
        floaty = t.behavior in ("swim", "fly")

        if reaction == "love":
            for i in range(3):
                self.spawn("heart", hx + rng.uniform(-14, 14), hy - i * 10,
                           life=1.0 + i * 0.25, vx=rng.uniform(-15, 15))
            if grounded:
                self._jump(t, 160)
        elif reaction == "jump":
            for vx in (-70, -25, 25, 70):
                self.spawn("star", hx, hy + t.h * 0.3, life=0.8, vx=vx, vy=-90)
            if grounded:
                self._jump(t, rng.uniform(320, 380))
            elif floaty:
                self._dart(t, t.x, t.y - rng.uniform(120, 220))
        elif reaction == "spin":
            self.spawn("sparkle", hx, hy, life=0.9)
        elif reaction == "shake":
            self.spawn("bang", hx, hy, life=0.9, vy=-20)
        elif reaction == "dance":
            self.spawn("note", hx, hy, life=1.2, vx=rng.uniform(-20, 20))
        elif reaction == "sleep":
            self.spawn("zzz", hx, hy, life=1.4, vx=12, vy=-25)
            t._fx_t = 0.9
        elif reaction == "dash":
            self.spawn("drop", hx, hy, life=0.8, vx=-30 if not t.flip else 30, vy=-50)
            away = 1 if t.flip else -1            # run the way it isn't facing
            if t.behavior == "walk":
                t.state, t.timer = "move", REACTION_TIME["dash"]
                t.vx = away * (25 + t.scale * 8) * 4
                t.flip = away < 0
            elif t.behavior == "hop":
                t.vx, t.vy, t.state = away * 260, -260, "air"
                t.flip = away < 0
            elif floaty:
                self._dart(t, t.x + away * rng.uniform(200, 400), t.y + rng.uniform(-100, 100))
        if reaction in HOLDS_STILL and not (grounded and not self.on_ground(t)):
            t.vx = 0.0
            if floaty:
                t.vy, t.target, t.state = 0.0, None, "idle"
        return reaction

    def _jump(self, t, power):
        if self.on_ground(t):
            t.vy, t.vx, t.state = -power, 0.0, "air"

    def _dart(self, t, tx, ty):
        t.target = (min(max(tx, 0), self.width - t.w), min(max(ty, 0), self.ground - t.h))
        t.speed, t.state = 420.0, "move"

    def released(self, t):
        """The user let go of a dragged thing."""
        t.dragging = False
        t.reaction = None
        t.vx = t.vy = 0.0
        t.target = None
        t.state = "air" if t.behavior in ("walk", "hop") else "idle"
        t.timer = 0.5
        self.clamp(t)

    # -- simulation ----------------------------------------------------------
    def step(self, dt, rng=random):
        for t in self.things:
            t.anim_t += dt
            t.age += dt
            if t.dragging:
                continue
            if self._sleepy(t) and rng.random() < dt * NAP_CHANCE * self.night:
                self.nap(t, rng)
            if t.reaction and self._react(t, dt, rng):
                self.clamp(t)
                continue
            mover = getattr(self, "_" + t.behavior, None)
            if mover is None:
                t.vx = t.vy = 0.0
            else:
                mover(t, dt, rng)
            if self.wind and t.behavior in WIND_PUSH:
                t.x += self.wind * WIND_PUSH[t.behavior] * dt
            self.clamp(t)
        for p in self.particles:
            p[1] += (p[4] + self.wind * 0.5) * dt
            p[2] += p[5] * dt
            p[4] *= 0.92                      # sideways drift slows down
            p[3] -= dt
        self.particles = [p for p in self.particles if p[3] > 0]

    def _sleepy(self, t):
        """A pet that is resting at night, so it may doze off."""
        if not t.is_pet or self.night < 0.5 or t.reaction or t.behavior == "stay":
            return False
        if t.state != "idle":
            return False
        return t.behavior in ("swim", "fly") or (self.on_ground(t) and t.vy >= 0)

    def nap(self, t, rng=random):
        t.reaction, t.reaction_t, t._fx_t = "sleep", rng.uniform(*NAP_TIME), 0.3
        t.vx = 0.0
        if t.behavior in ("swim", "fly"):
            t.vy, t.target = 0.0, None

    def _react(self, t, dt, rng):
        """Run the current click reaction. True = skip normal movement."""
        t.reaction_t -= dt
        r = t.reaction
        if t.reaction_t <= 0:
            t.reaction = None
            if r in HOLDS_STILL:
                t.state, t.timer = "idle", rng.uniform(0.3, 1.0)
            return False
        if r not in HOLDS_STILL:
            return False
        t._fx_t -= dt
        if r == "spin":
            t.flip = int(t.reaction_t / 0.1) % 2 == 0
        elif r == "dance":
            t.flip = int(t.reaction_t / 0.3) % 2 == 0
            if t._fx_t <= 0:
                hx, hy = self._head(t)
                self.spawn("note", hx, hy, life=1.2, vx=rng.uniform(-25, 25))
                t._fx_t = 0.45
            if t.behavior in ("walk", "hop") and self.on_ground(t) and t.vy >= 0:
                t.vy = -110.0
        elif r == "sleep" and t._fx_t <= 0:
            hx, hy = self._head(t)
            self.spawn("zzz", hx, hy, life=1.4, vx=12, vy=-25)
            t._fx_t = 0.9
        if t.behavior in ("walk", "hop"):
            t.vx = 0.0
            self._fall(t, dt)                 # still obey gravity
        else:
            t.vx = t.vy = 0.0
        return True

    def _fall(self, t, dt):
        """Gravity. Returns True while the thing is in the air."""
        if t.vy < 0 or not self.on_ground(t):
            t.vy += GRAVITY * dt
            t.y += t.vy * dt
            t.x += t.vx * dt
            self._bounce_walls(t)
            if t.y + t.h >= self.ground:
                t.y = self.ground - t.h
                t.vy = 0.0
                t.vx = 0.0
                if t.state == "air":
                    t.state = "idle"
                    t.timer = random.uniform(0.5, 2.5)
                return False
            return True
        t.vy = 0.0
        return False

    def _bounce_walls(self, t):
        if t.x <= 0 and t.vx < 0 or t.x + t.w >= self.width and t.vx > 0:
            t.vx = -t.vx
        if abs(t.vx) > 1:
            t.flip = t.vx < 0

    def _walk(self, t, dt, rng):
        if self._fall(t, dt):
            return
        t.timer -= dt
        if t.timer <= 0:
            if t.state == "move":
                t.state, t.vx, t.timer = "idle", 0.0, rng.uniform(1.0, 4.0)
            else:
                speed = (25 + t.scale * 8) * t.speed_mult
                t.state = "move"
                t.vx = speed if rng.random() < 0.5 else -speed
                t.timer = rng.uniform(2.0, 6.0)
        t.x += t.vx * dt
        self._bounce_walls(t)

    def _hop(self, t, dt, rng):
        if self._fall(t, dt):
            return
        t.timer -= dt
        if t.timer <= 0:
            direction = rng.choice((-1, 1)) if rng.random() < 0.3 else (-1 if t.flip else 1)
            t.vx = direction * rng.uniform(60, 130) * t.speed_mult
            t.vy = -rng.uniform(220, 330)
            t.flip = direction < 0
            t.state = "air"

    def _swim(self, t, dt, rng, speed_range=(35, 80), pause=(0.5, 3.0)):
        if t.state == "idle":
            t.vx = t.vy = 0.0
            t.timer -= dt
            if t.timer <= 0:
                t.target = (rng.uniform(0, max(0, self.width - t.w)),
                            rng.uniform(0, max(0, self.ground - t.h)))
                t.speed = rng.uniform(*speed_range) * t.speed_mult
                t.state = "move"
            return
        if t.target is None:
            t.state, t.timer = "idle", rng.uniform(*pause)
            return
        dx, dy = t.target[0] - t.x, t.target[1] - t.y
        dist = math.hypot(dx, dy)
        if dist < 3:
            t.target = None
            t.state, t.timer = "idle", rng.uniform(*pause)
            t.vx = t.vy = 0.0
            return
        step = min(t.speed * dt, dist)
        t.vx, t.vy = dx / dist * t.speed, dy / dist * t.speed
        t.x += dx / dist * step
        t.y += dy / dist * step
        if abs(dx) > 2:
            t.flip = dx < 0
        if t.speed > 200:                 # calm down after a dart
            t.speed = max(80.0, t.speed - 300 * dt)

    def _fly(self, t, dt, rng):
        self._swim(t, dt, rng, speed_range=(120, 240), pause=(0.2, 1.5))


def thing_at(things, x, y, opaque):
    """The front-most thing under (x, y). `opaque(thing, ax, ay)` says whether
    the art pixel at (ax, ay) is painted, so see-through gaps don't count."""
    for t in reversed(things):
        tx, ty, tw, th = t.rect()
        if tx <= x < tx + tw and ty <= y < ty + th:
            ax = int((x - tx) // t.scale)
            ay = int((y - ty) // t.scale)
            if t.flip:
                ax = t.art_w - 1 - ax
            if opaque(t, ax, ay):
                return t
    return None
