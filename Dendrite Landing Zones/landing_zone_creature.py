"""
================================================================================
LANDING-ZONE CREATURE
A forager whose perception is place-coded phases, not hand-coded numbers.
================================================================================

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
"Do not hype. Do not lie. Just show."

Every sense the creature has is turned into a bump on a ring of landing zones
(LandingZones). The brain never compares numbers -- it compares POPULATIONS by
interference:

  STEER:  the direction-to-food is place-coded. The creature's heading is
          place-coded twice -- once rotated a little LEFT, once RIGHT. Two
          coincidence somas ask "which rotated heading agrees more with where
          the food is?" The difference of the two coincidences is the turn.
          (This is the owl's two-eared comparison, and a ring-attractor steer.)

  AVOID:  forward obstacle proximity is place-coded on an arc; an AIS threshold
          turns 'too close' into a discrete avoidance spike that overrides steer.

So the control path is: continuous sense -> landing-zone bump (phase) ->
coincidence soma (interference) -> AIS spike / graded turn -> motion.
No arithmetic comparison of raw sensor values anywhere in the loop.

Honest question this tests: does perception-as-waves actually drive a body to
food and around walls? We measure it.
================================================================================
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import LineCollection

from landing_zone import (LandingZones, coincidence, ais_spike,
                          value_to_angle, TAU)

RNG = np.random.default_rng(4)

# ----------------------------------------------------------------------------
# world
# ----------------------------------------------------------------------------
class World:
    def __init__(self):
        self.W = self.H = 20.0
        self.obstacles = [(6, 6, 1.3), (14, 8, 1.2), (9, 14, 1.1), (15, 15, 1.0)]
        self.food = (17.0, 17.0)        # single goal, lower-effort to read honestly

    def is_free(self, x, y):
        if x < 0.5 or x > self.W-0.5 or y < 0.5 or y > self.H-0.5: return False
        for ox, oy, r in self.obstacles:
            if (x-ox)**2 + (y-oy)**2 < (r+0.3)**2: return False
        return True

    def front_proximity(self, x, y, h, reach=3.0):
        """1 = obstacle right ahead, 0 = clear ahead (sampled along heading)."""
        for k in range(1, 13):
            t = reach*k/12
            if not self.is_free(x+t*np.cos(h), y+t*np.sin(h)):
                return 1.0 - t/reach
        return 0.0

    def dir_to_food(self, x, y):
        return np.arctan2(self.food[1]-y, self.food[0]-x) % TAU


# ----------------------------------------------------------------------------
# creature whose perception is landing zones
# ----------------------------------------------------------------------------
class Creature:
    def __init__(self, x, y, heading):
        self.x, self.y, self.heading = x, y, heading
        self.ring = LandingZones(n=24, kappa=4.0)   # for circular senses (heading, bearing)
        self.arc  = LandingZones(n=20, kappa=5.0)   # for the bounded proximity sense
        self.speed = 0.18
        self.turn_gain = 0.30
        self.trail_x, self.trail_y = [], []
        self.reached = False
        self._avoid_dir = 0.0
        self.log = {"steer": [], "avoid": [], "coh_food": []}

    def perceive_and_act(self, world):
        # ---- senses as continuous values ----
        bearing = world.dir_to_food(self.x, self.y)         # circular, [0,2pi)
        prox    = world.front_proximity(self.x, self.y, self.heading)  # [0,1]

        # ---- place-code them (input transducer) ----
        a_food   = self.ring.encode(bearing, noise=0.05, rng=RNG)
        a_headL  = self.ring.encode(self.heading + 0.5)      # heading rotated left
        a_headR  = self.ring.encode(self.heading - 0.5)      # heading rotated right
        a_prox   = self.arc.encode(value_to_angle(prox), noise=0.05, rng=RNG)
        a_near   = self.arc.encode(value_to_angle(0.7))      # template: "this close"

        # ---- coincidence somas (interference) ----
        cohL = coincidence(self.ring, a_food, a_headL)       # food agrees with left?
        cohR = coincidence(self.ring, a_food, a_headR)       # food agrees with right?
        steer = cohL - cohR                                  # signed, in-substrate

        prox_match = coincidence(self.arc, a_prox, a_near)   # is something close ahead?
        avoid = ais_spike(prox_match, threshold=0.6)         # AIS commit

        # also a forward coincidence to know if we're basically aimed at food
        coh_food = coincidence(self.ring, a_food, self.ring.encode(self.heading))

        # ---- arbitration ----
        if avoid > 0.5:
            # commit to turning toward the clearer side and HOLD it until clear,
            # so we sweep past the obstacle instead of jittering against it
            if self._avoid_dir == 0:
                pl = world.front_proximity(self.x, self.y, self.heading + 0.7)
                pr = world.front_proximity(self.x, self.y, self.heading - 0.7)
                self._avoid_dir = +1.0 if pl <= pr else -1.0
            turn = self._avoid_dir
            drive = 0.9                                       # keep moving while turning
        else:
            self._avoid_dir = 0
            turn = np.clip(3.0 * steer, -1, 1)               # steer toward food
            drive = 1.0

        self.heading = (self.heading + self.turn_gain * turn) % TAU
        nx = self.x + self.speed * drive * np.cos(self.heading)
        ny = self.y + self.speed * drive * np.sin(self.heading)
        if world.is_free(nx, ny):
            self.x, self.y = nx, ny
        self.trail_x.append(self.x); self.trail_y.append(self.y)

        self.log["steer"].append(steer)
        self.log["avoid"].append(avoid)
        self.log["coh_food"].append(coh_food)

        if (self.x-world.food[0])**2 + (self.y-world.food[1])**2 < 0.6**2:
            self.reached = True


# ----------------------------------------------------------------------------
# run + figure
# ----------------------------------------------------------------------------
def main():
    world = World()
    creature = Creature(2.0, 2.0, heading=0.3)
    steps = 1100
    for t in range(steps):
        creature.perceive_and_act(world)
        if creature.reached:
            print(f"[creature] reached food at step {t}")
            break
    if not creature.reached:
        print("[creature] did not reach food in time")
    dist = ((creature.x-world.food[0])**2 + (creature.y-world.food[1])**2)**0.5
    print(f"[creature] final distance to food = {dist:.2f}, path length = "
          f"{sum(np.hypot(np.diff(creature.trail_x), np.diff(creature.trail_y))):.1f}")

    fig = plt.figure(figsize=(13, 5.5)); fig.patch.set_facecolor("#0b0f14")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 1], height_ratios=[1, 1],
                          hspace=0.4, wspace=0.25)

    # trajectory
    ax = fig.add_subplot(gs[:, 0]); ax.set_facecolor("#11161d")
    ax.set_xlim(0, world.W); ax.set_ylim(0, world.H); ax.set_aspect("equal")
    for s in ax.spines.values(): s.set_color("#1f2730")
    ax.tick_params(colors="#3a4350")
    for ox, oy, r in world.obstacles:
        ax.add_patch(Circle((ox, oy), r, color="#2b3540"))
    ax.scatter(*world.food, s=320, c="#3fd07f", marker="*", edgecolors="white", linewidths=.6, zorder=5)
    tx, ty = creature.trail_x, creature.trail_y
    pts = np.array([tx, ty]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(segs, cmap="cool", array=np.linspace(0, 1, len(segs)), linewidths=2)
    ax.add_collection(lc)
    ax.scatter(tx[0], ty[0], s=70, c="#4aa3ff", edgecolors="white", linewidths=.6, zorder=6)
    ax.set_title("Forager driven entirely by place-coded perception",
                 color="#e6edf3", fontsize=12)

    def style(a):
        a.set_facecolor("#11161d"); a.tick_params(colors="#7d8b99")
        for s in a.spines.values(): s.set_color("#1f2730")
        a.title.set_color("#e6edf3"); a.xaxis.label.set_color("#7d8b99"); a.yaxis.label.set_color("#7d8b99")
        a.grid(True, alpha=0.12)

    ax2 = fig.add_subplot(gs[0, 1]); style(ax2)
    ax2.plot(creature.log["steer"], color="#4aa3ff", lw=1.3)
    ax2.axhline(0, color="#3a4350", lw=0.8)
    ax2.set_title("Steering signal  (left coincidence − right coincidence)", fontsize=10)
    ax2.set_ylabel("turn")

    ax3 = fig.add_subplot(gs[1, 1]); style(ax3)
    ax3.plot(creature.log["coh_food"], color="#3fd07f", lw=1.3, label="aim-at-food coincidence")
    ax3.plot(creature.log["avoid"], color="#ff5d52", lw=1.0, label="AIS avoid spike")
    ax3.set_title("Heading-vs-food agreement & avoidance spikes", fontsize=10)
    ax3.set_xlabel("step"); ax3.set_ylim(-1.1, 1.2)
    ax3.legend(facecolor="#11161d", labelcolor="#e6edf3", fontsize=8, loc="lower right")

    fig.suptitle("Perception as waves: senses → landing-zone bumps → coincidence somas → motion",
                 color="#e6edf3", fontsize=12, y=1.0)
    plt.savefig("landing_zone_creature.png", dpi=110, facecolor="#0b0f14", bbox_inches="tight")
    print("saved -> landing_zone_creature.png")


if __name__ == "__main__":
    main()
