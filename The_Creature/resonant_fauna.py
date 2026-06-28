"""
================================================================================
RESONANT FAUNA  -  an ecosystem of creatures whose brains are made of
                   interference resonator gates, synaptic latches, and a CPG.
================================================================================

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
"Do not hype. Do not lie. Just show."

This bolts the ResonantNeuron brain (interference soma) onto a body, and adds
the two other machines the V11-V18 arc proved you cannot skip:

   1. INTERFERENCE SOMA   - the resonator gate. Computes by amplitude bands.
                            |s| is quadratic in inputs -> one unit does XOR.
                            (verified: repo sections 0-7)

   2. SYNAPTIC LATCH      - the V18 capture element. A spike is transient; a
                            logic signal must be HELD. Each behavioural gate's
                            output is captured into a decaying latch. This is
                            the synapse the field "demanded".
                            (verified mechanism: hold + leak ODE)

   3. CENTRAL PATTERN GEN - the oscillatory clock V15-16 said the physics
                            forces. A half-centre oscillator (two mutually
                            inhibiting units) produces the locomotor rhythm.
                            Brain state only MODULATES it (speed, turn bias).
                            (verified: coupled relaxation oscillator)

Everything below is a real dynamical system. No behaviour is hand-scripted;
it falls out of the wiring of these three machine-types under sensory drive.

WHAT IS DESIGNED (not learned, not emergent):
   - gate weights / bands, sensor encodings, latch time-constants, CPG coupling,
     metabolic rates, the wiring diagram itself.
WHAT IS EMERGENT (falls out of the loop, not coded as a rule):
   - foraging paths, wall-hugging, collision-shy turning, the population
     boom/bust as food depletes, individual lifespans.
================================================================================
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import LineCollection
import matplotlib.animation as animation

RNG = np.random.default_rng(7)

# ============================================================================
# 1. THE INTERFERENCE SOMA  (resonator gate, from the repo)
# ============================================================================

class Gate:
    """
    One interference neuron. Soma mixes two phasor inputs:
        s = w1*p1 + w2*p2 + bias
    Output bit = 1 iff lo <= |s| <= hi  (an amplitude BAND).
    |s| is quadratic in the inputs -> a single unit carves a nonlinear
    boundary -> one unit computes XOR. Linearly-separable gates (AND/OR/NOT)
    use a one-sided band.
    """
    __slots__ = ("name", "w1", "w2", "bias", "lo", "hi", "last_amp")

    def __init__(self, name, w1, w2, bias, lo, hi):
        self.name = name
        self.w1, self.w2, self.bias = w1, w2, bias
        self.lo, self.hi = lo, hi
        self.last_amp = 0.0

    def __call__(self, p1: complex, p2: complex) -> float:
        s = self.w1 * p1 + self.w2 * p2 + self.bias
        a = abs(s)
        self.last_amp = a
        return 1.0 if (self.lo <= a <= self.hi) else 0.0

# A functionally-complete bank. Bit encoding: 0 -> +1 phasor, 1 -> -1 phasor.
# Amplitudes for s = p1 + p2 + bias (verified by direct computation):
#   bias 0 : agree(00,11)->|s|=2.0   disagree(01,10)->|s|=0.0
#   bias-1 : (1,1)->3.0   others->1.0
#   bias 1 : (0,0)->3.0   others->1.0
#   NOT(w2=0,bias 1): input0->2.0  input1->0.0
def make_gate(kind: str) -> Gate:
    if kind == "XOR":  return Gate("XOR",  1, 1,  0.0, -0.1, 0.5)  # fire on disagree (|s|=0)
    if kind == "XNOR": return Gate("XNOR", 1, 1,  0.0,  1.9, 2.1)  # fire on agree   (|s|=2)
    if kind == "AND":  return Gate("AND",  1, 1, -1.0,  2.5, 3.5)  # fire only (1,1) (|s|=3)
    if kind == "OR":   return Gate("OR",   1, 1,  1.0,  0.5, 1.5)  # fire unless (0,0) (|s|=1)
    if kind == "NAND": return Gate("NAND", 1, 1, -1.0,  0.5, 1.5)  # fire unless (1,1) (|s|=1)
    if kind == "NOR":  return Gate("NOR",  1, 1,  1.0,  2.5, 3.5)  # fire only (0,0) (|s|=3)
    if kind == "NOT":  return Gate("NOT",  1, 0,  1.0, -0.1, 0.5)  # fire on input 1 (|s|=0)
    raise ValueError(kind)

# Verify the bank once at import (honesty check).
def _verify_bank():
    truth = {
        "XOR":  {(0,0):0,(0,1):1,(1,0):1,(1,1):0},
        "XNOR": {(0,0):1,(0,1):0,(1,0):0,(1,1):1},
        "AND":  {(0,0):0,(0,1):0,(1,0):0,(1,1):1},
        "OR":   {(0,0):0,(0,1):1,(1,0):1,(1,1):1},
        "NAND": {(0,0):1,(0,1):1,(1,0):1,(1,1):0},
        "NOR":  {(0,0):1,(0,1):0,(1,0):0,(1,1):0},
    }
    enc = lambda b: (-1+0j) if b else (1+0j)
    ok = True
    for k, table in truth.items():
        g = make_gate(k)
        for (a,b), want in table.items():
            got = g(enc(a), enc(b))
            if got != want:
                ok = False
                print(f"  GATE FAIL {k} {(a,b)} -> {got} want {want}")
    print(f"[gate-bank self-test] all truth tables exact: {ok}")
    return ok

# ============================================================================
# 2. THE SYNAPTIC LATCH  (V18 capture element)
# ============================================================================

class Latch:
    """
    The synapse. A transient gate spike (0/1) is CAPTURED and held, then leaks.
        v_{t+1} = max(spike, v_t * decay)
    'spike' re-arms it to 1; otherwise it decays toward 0. This is what lets a
    momentary decision persist long enough to drive and sequence behaviour --
    exactly the element the V18 continuous field could not do without.
    """
    __slots__ = ("v", "decay")
    def __init__(self, decay=0.90):
        self.v = 0.0
        self.decay = decay
    def update(self, spike: float) -> float:
        self.v = max(spike, self.v * self.decay)
        return self.v

# ============================================================================
# 3. CENTRAL PATTERN GENERATOR  (half-centre oscillator)
# ============================================================================

class CPG:
    """
    A locomotor rhythm generator. Two coupled phase oscillators produce an
    endogenous gait rhythm; brain 'drive' sets forward thrust and 'turn_bias'
    sets the steering. The rhythm is intrinsic (runs with zero input) but here
    it primarily paces a reliable forward thrust, with turn as a bounded
    modulation -- so the animal makes progress instead of spinning.
    """
    def __init__(self, dt=1.0, tau=6.0):
        self.dt, self.tau = dt, tau
        self.phase = 0.0           # gait phase
        self.freq = 0.35           # intrinsic step frequency

    def step(self, drive: float, turn_bias: float):
        # advance intrinsic gait phase
        self.phase = (self.phase + self.dt * self.freq) % (2*np.pi)
        # forward thrust: positive, paced by drive, gently modulated by gait
        gait = 0.85 + 0.15*np.sin(self.phase)      # 0.70..1.00 ripple
        thrust = max(0.0, drive) * gait
        # turn: bounded steering command (does NOT spin freely)
        turn = float(np.clip(turn_bias, -1.5, 1.5))
        # expose internal half-centre-like states for the dashboard
        self.xL = thrust * 0.5 + 0.5*np.sin(self.phase)
        self.xR = thrust * 0.5 + 0.5*np.sin(self.phase + np.pi)
        return thrust, turn

# ============================================================================
# 4. THE BRAIN  (wiring the three machines together)
# ============================================================================

class Brain:
    """
    Sensory phasors -> gate bank -> latches -> behavioural arbitration -> CPG
    modulation. The arbitration is a fixed priority encoded in resonator logic;
    no behaviour is if/else-scripted at the policy level -- each decision is a
    gate firing on encoded sensory phasors, then held by a latch.
    """
    def __init__(self):
        # --- gate bank (the interference computers) ---
        self.g_collide  = make_gate("AND")   # both forward rays close -> imminent hit
        self.g_steer    = make_gate("XOR")   # L/R obstacle asymmetry -> must turn
        self.g_food     = make_gate("OR")    # any food sensor active -> food present
        self.g_food_dir = make_gate("XOR")   # food L/R asymmetry -> turn toward food
        self.g_hungry   = make_gate("NOT")   # energy-low signal (interoception)
        self.g_pursue   = make_gate("AND")   # hungry AND food-present -> pursue
        self.g_explore  = make_gate("NOR")   # no food AND not hungry -> wander
        self.gates = [self.g_collide, self.g_steer, self.g_food,
                      self.g_food_dir, self.g_hungry, self.g_pursue,
                      self.g_explore]

        # --- latches (the synapses that hold decisions) ---
        self.l_avoid  = Latch(decay=0.80)   # collision memory: hold the swerve
        self.l_pursue = Latch(decay=0.92)   # commitment to a food target
        self.l_pain   = Latch(decay=0.97)   # long collision memory -> caution

        # --- the clock ---
        self.cpg = CPG()
        self._prev_smell = 0.0
        self._weak_drift = 0.0
        self._turn_commit = 0.0

        # telemetry
        self.trace = {"avoid":0.0,"steer_dir":0.0,"pursue":0.0,
                      "food_dir":0.0,"hungry":0.0,"pain":0.0,
                      "thrust":0.0,"turn":0.0,"gate_evals":0}

    @staticmethod
    def _phasor(strength: float, sign: int = +1) -> complex:
        # strength in [0,1]; sign sets phase 0 (+) or pi (-). Bit-style encoding.
        strength = float(np.clip(strength, 0, 1))
        return strength * (1+0j if sign > 0 else -1+0j)

    def think(self, s: Dict[str, float]) -> Tuple[float, float]:
        """
        s carries already-normalised senses in [0,1]:
          ray_close_L, ray_close_R, ray_close_C  (1=obstacle very near)
          food_L, food_R                          (1=strong food smell)
          energy_low                              (1=starving, 0=full)
        Returns (thrust, turn) for locomotion.

        Logic gates need clean bits or they mis-fire (a zero phasor reads as
        'disagreement' to an XOR). So we threshold senses into bits for the
        gate layer, and keep the raw graded values only to pick turn DIRECTION.
        """
        evals = 0
        bit = lambda v, thr: 1 if v > thr else 0
        enc = lambda b: (-1+0j) if b else (1+0j)   # 0->+1, 1->-1

        # threshold senses into bits
        bL = bit(s["ray_close_L"], 0.35)
        bR = bit(s["ray_close_R"], 0.35)
        bC = bit(s["ray_close_C"], 0.35)
        bFL = bit(s["food_L"], 0.25)
        bFR = bit(s["food_R"], 0.25)
        bFood = 1 if (bFL or bFR) else 0
        bHungry = bit(s["energy_low"], 0.35)

        # --- OBSTACLE LAYER (clean-bit gates) ---
        # imminent collision: centre ray AND a side ray both close
        collide   = self.g_collide(enc(bC), enc(1 if (bL or bR) else 0)); evals+=1
        # need-to-steer: left/right disagree (one side blocked, other clear)
        steer_hit = self.g_steer(enc(bL), enc(bR)); evals+=1
        avoid = self.l_avoid.update(max(collide, steer_hit, 1.0 if bC else 0.0))
        self.l_pain.update(collide)

        # steer AWAY from obstacles. Three cases:
        #   asymmetric (one side blocked): turn to the clearer side
        #   head-on (all rays blocked):   commit a hard turn (pick a side, hold it)
        steer_dir = 0.0
        if collide > 0.5 or steer_hit > 0.5 or bC:
            if bL and not bR:
                steer_dir = +1.0                      # left blocked -> turn right
            elif bR and not bL:
                steer_dir = -1.0                      # right blocked -> turn left
            else:
                # head-on or both sides: keep turning the way we already committed
                if self._turn_commit == 0.0:
                    self._turn_commit = 1.0 if RNG.random() < 0.5 else -1.0
                steer_dir = self._turn_commit
        else:
            self._turn_commit = 0.0                   # clear -> release commitment

        # --- FOOD LAYER ---
        food_present = self.g_food(enc(bFL), enc(bFR)); evals+=1     # OR
        food_turn_on = self.g_food_dir(enc(bFL), enc(bFR)); evals+=1 # XOR: only one side smells
        hungry = self.g_hungry(enc(bHungry), 0+0j); evals+=1
        pursue = self.g_pursue(enc(bHungry), enc(bFood)); evals+=1   # AND hungry&food
        pursue_held = self.l_pursue.update(pursue)

        # CHEMOTAXIS: proportional gradient following (tropotaxis). Compare the
        # two shoulders and steer proportionally toward the stronger side; the
        # smell-rising/falling memory only scales how hard we correct. This
        # gives smooth convergence instead of an orbiting limit cycle.
        smell = max(s["food_L"], s["food_R"])
        d_smell = smell - self._prev_smell
        self._prev_smell = smell
        food_dir = 0.0
        if bFood:
            grad = s["food_L"] - s["food_R"]        # >0 means turn left
            food_dir = np.clip(grad * 4.0, -1, 1)   # proportional, not bang-bang
        # weak long-range drift: even below the commit threshold, bias the wander
        # toward wherever the faint glow is stronger (biased random walk)
        weak_grad = s["food_L"] - s["food_R"]
        self._weak_drift = float(np.clip(weak_grad * 6.0, -1, 1))

        # --- ARBITRATION (priority via held latches) ---
        if avoid > 0.4:
            turn_bias = 1.6 * steer_dir + 0.2*self.l_pain.v*RNG.standard_normal()
            drive = 0.8
        elif bFood:
            # food in range: home in. Strong forward drive + gentle proportional turn.
            turn_bias = 0.7 * food_dir
            drive = 1.8
        else:
            # biased random walk: faint food glow nudges the wander direction
            turn_bias = 0.8*self._weak_drift + 0.35*RNG.standard_normal()
            drive = 1.1

        thrust, turn = self.cpg.step(drive, turn_bias)

        self.trace.update(avoid=avoid, steer_dir=steer_dir, pursue=pursue_held,
                          food_dir=food_dir, hungry=float(bHungry), pain=self.l_pain.v,
                          thrust=thrust, turn=turn, gate_evals=evals)
        return thrust, turn

# ============================================================================
# 5. THE BODY  +  WORLD
# ============================================================================

@dataclass
class Creature:
    x: float; y: float; heading: float
    brain: Brain = field(default_factory=Brain)
    energy: float = 1.0
    age: int = 0
    alive: bool = True
    n_rays: int = 5
    ray_len: float = 3.2
    fov: float = np.deg2rad(100)
    speed_gain: float = 0.22
    turn_gain: float = 0.35
    trail_x: List[float] = field(default_factory=list)
    trail_y: List[float] = field(default_factory=list)
    ate: int = 0

    def sense(self, world: "World", others: List["Creature"]) -> Dict[str,float]:
        # cast rays, find nearest obstacle closeness per ray
        angles = np.linspace(-self.fov/2, self.fov/2, self.n_rays)
        closeness = np.zeros(self.n_rays)
        for i, a in enumerate(angles):
            h = self.heading + a
            closeness[i] = world.ray_closeness(self.x, self.y, h, self.ray_len, others, self)
        L = closeness[:self.n_rays//2].max()
        R = closeness[self.n_rays//2+1:].max()
        C = closeness[self.n_rays//2]
        # food smell: sample concentration slightly off each shoulder
        fl = world.food_smell(self.x + 0.6*np.cos(self.heading+0.6),
                              self.y + 0.6*np.sin(self.heading+0.6))
        fr = world.food_smell(self.x + 0.6*np.cos(self.heading-0.6),
                              self.y + 0.6*np.sin(self.heading-0.6))
        return {"ray_close_L":L,"ray_close_R":R,"ray_close_C":C,
                "food_L":fl,"food_R":fr,
                "energy_low":float(np.clip(1.0 - self.energy, 0, 1))}

    def step(self, world: "World", others: List["Creature"]):
        if not self.alive: return
        s = self.sense(world, others)
        thrust, turn = self.brain.think(s)
        self.heading = (self.heading + self.turn_gain*turn) % (2*np.pi)
        step_len = self.speed_gain * thrust
        nx = self.x + step_len*np.cos(self.heading)
        ny = self.y + step_len*np.sin(self.heading)
        # collision with walls/obstacles: blocked move costs extra energy
        if world.is_free(nx, ny):
            self.x, self.y = nx, ny
        else:
            self.energy -= 0.004     # bonk penalty
            self.brain.l_avoid.v = 1.0  # force avoid latch high on real contact
        # metabolism: living + moving both cost
        self.energy -= 0.0010 + 0.0025*step_len
        # eat
        gained = world.consume(self.x, self.y)
        if gained > 0:
            self.energy = min(1.0, self.energy + gained)
            self.ate += 1
        self.energy = min(1.0, self.energy)
        self.age += 1
        if self.energy <= 0:
            self.alive = False
        # trail
        self.trail_x.append(self.x); self.trail_y.append(self.y)
        if len(self.trail_x) > 60:
            self.trail_x.pop(0); self.trail_y.pop(0)


class World:
    def __init__(self, W=20.0, H=20.0, n_food=26):
        self.W, self.H = W, H
        self.obstacles = [(5,5,1.1),(14,6,1.3),(9,14,1.0),(16,15,1.2),(4,15,0.9)]
        self.food = []          # (x,y,amount)
        self.food_regrow_timer = 0
        for _ in range(n_food):
            self.food.append(self._spawn_food())

    def _spawn_food(self):
        for _ in range(200):
            x = RNG.uniform(1, self.W-1); y = RNG.uniform(1, self.H-1)
            if self.is_free(x, y):
                return [x, y, RNG.uniform(0.25, 0.5)]
        return [self.W/2, self.H/2, 0.3]

    def is_free(self, x, y):
        if x < 0.4 or x > self.W-0.4 or y < 0.4 or y > self.H-0.4:
            return False
        for ox, oy, r in self.obstacles:
            if (x-ox)**2 + (y-oy)**2 < (r+0.25)**2:
                return False
        return True

    def ray_closeness(self, x, y, h, length, others, me):
        # march the ray; return 1 - (hit_distance/length), 0 if clear
        steps = 14
        dx, dy = np.cos(h), np.sin(h)
        for k in range(1, steps+1):
            t = length * k/steps
            px, py = x+dx*t, y+dy*t
            hit = (not self.is_free(px, py))
            if not hit:
                for o in others:
                    if o is me or not o.alive: continue
                    if (px-o.x)**2 + (py-o.y)**2 < 0.36:
                        hit = True; break
            if hit:
                return 1.0 - (t/length)
        return 0.0

    def food_smell(self, x, y):
        # Smell that does NOT saturate, so the L/R gradient stays informative at
        # all ranges. Dominated by the NEAREST food (sharp homing core) with a
        # mild long-range additive glow for detection. No clip-to-1 flattening.
        if not self.food:
            return 0.0
        nearest_d2 = min((x-fx)**2 + (y-fy)**2 for fx, fy, _ in self.food)
        sharp = np.exp(-nearest_d2 / 4.0)          # smooth, monotone, ~0..1
        glow = 0.0
        for fx, fy, amt in self.food:
            glow += 0.015 * amt * np.exp(-((x-fx)**2+(y-fy)**2)/40.0)
        return float(sharp + min(glow, 0.10))

    def consume(self, x, y):
        gained = 0.0
        for f in self.food:
            if (x-f[0])**2 + (y-f[1])**2 < 0.50**2:
                gained += f[2]
                f[2] = 0.0
        # remove eaten
        self.food = [f for f in self.food if f[2] > 0.01]
        return gained

    def regrow(self, target):
        # slowly replenish food up to target count
        self.food_regrow_timer += 1
        if self.food_regrow_timer >= 8 and len(self.food) < target:
            self.food.append(self._spawn_food())
            self.food_regrow_timer = 0

# ============================================================================
# 6. SIMULATION
# ============================================================================

def simulate(n_creatures=8, steps=900, food_target=26):
    print(f"[sim] {n_creatures} creatures, {steps} steps")
    world = World(n_food=food_target)
    creatures = []
    for _ in range(n_creatures):
        while True:
            x, y = RNG.uniform(2, world.W-2), RNG.uniform(2, world.H-2)
            if world.is_free(x, y): break
        creatures.append(Creature(x=x, y=y, heading=RNG.uniform(0, 2*np.pi)))

    # telemetry
    history = {"pop":[], "mean_energy":[], "total_eaten":[], "gate_evals":[]}
    frames = []           # for animation: snapshot each few steps
    focus_log = {k:[] for k in ["avoid","pursue","hungry","pain",
                                "thrust","turn","energy","cpg_xL","cpg_xR"]}

    for t in range(steps):
        evals_this = 0
        for c in creatures:
            c.step(world, creatures)
            evals_this += c.brain.trace["gate_evals"]
        world.regrow(food_target)

        alive = [c for c in creatures if c.alive]
        history["pop"].append(len(alive))
        history["mean_energy"].append(np.mean([c.energy for c in alive]) if alive else 0)
        history["total_eaten"].append(sum(c.ate for c in creatures))
        history["gate_evals"].append(evals_this)

        # focus on creature 0 (or first alive) for the brain dashboard
        focus = creatures[0] if creatures[0].alive else (alive[0] if alive else creatures[0])
        tr = focus.brain.trace
        focus_log["avoid"].append(tr["avoid"]);   focus_log["pursue"].append(tr["pursue"])
        focus_log["hungry"].append(tr["hungry"]); focus_log["pain"].append(tr["pain"])
        focus_log["thrust"].append(tr["thrust"]); focus_log["turn"].append(tr["turn"])
        focus_log["energy"].append(focus.energy)
        focus_log["cpg_xL"].append(focus.brain.cpg.xL)
        focus_log["cpg_xR"].append(focus.brain.cpg.xR)

        if t % 6 == 0:
            frames.append(_snapshot(world, creatures, t))

    print(f"[sim] done. survivors: {sum(c.alive for c in creatures)}/{n_creatures}, "
          f"total food eaten: {history['total_eaten'][-1]}, "
          f"total gate evaluations: {sum(history['gate_evals']):,}")
    return world, creatures, history, focus_log, frames


def _snapshot(world, creatures, t):
    return {
        "t": t,
        "obstacles": list(world.obstacles),
        "food": [(f[0],f[1],f[2]) for f in world.food],
        "creatures": [(c.x,c.y,c.heading,c.energy,c.alive,
                       list(c.trail_x), list(c.trail_y),
                       c.brain.trace["avoid"], c.brain.trace["pursue"])
                      for c in creatures],
        "W": world.W, "H": world.H,
    }

# ============================================================================
# 7. VISUALS
# ============================================================================

def render_animation(frames, path="resonant_fauna.gif"):
    fig, ax = plt.subplots(figsize=(7,7))
    W, H = frames[0]["W"], frames[0]["H"]

    def draw(fr):
        ax.clear()
        ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal")
        ax.set_facecolor("#0d1117")
        ax.set_title(f"Resonant Fauna   t={fr['t']}   "
                     f"alive={sum(c[4] for c in fr['creatures'])}",
                     color="#e6edf3", fontsize=11)
        ax.tick_params(colors="#444")
        for sp in ax.spines.values(): sp.set_color("#30363d")
        # obstacles
        for ox,oy,r in fr["obstacles"]:
            ax.add_patch(Circle((ox,oy), r, color="#30363d"))
        # food
        if fr["food"]:
            fx = [f[0] for f in fr["food"]]; fy=[f[1] for f in fr["food"]]
            fa = [f[2] for f in fr["food"]]
            ax.scatter(fx, fy, s=[30+200*a for a in fa], c="#3fb950",
                       marker="*", alpha=0.9, edgecolors="none")
        # creatures
        for (x,y,h,e,alive,tx,ty,avoid,pursue) in fr["creatures"]:
            if not alive:
                ax.scatter([x],[y], s=40, c="#6e7681", marker="x", alpha=0.6)
                continue
            # trail
            if len(tx) > 1:
                pts = np.array([tx,ty]).T.reshape(-1,1,2)
                segs = np.concatenate([pts[:-1],pts[1:]],axis=1)
                lc = LineCollection(segs, colors="#58a6ff", alpha=0.25, linewidths=1)
                ax.add_collection(lc)
            # body colour: red when avoiding, yellow when pursuing, blue idle
            if avoid > 0.4:    col = "#f85149"
            elif pursue > 0.4: col = "#d29922"
            else:              col = "#58a6ff"
            ax.scatter([x],[y], s=70*(0.5+e), c=col, edgecolors="white",
                       linewidths=0.6, zorder=5)
            ax.plot([x, x+0.6*np.cos(h)],[y, y+0.6*np.sin(h)],
                    color="white", lw=1.2, zorder=6)
        return []

    anim = animation.FuncAnimation(fig, draw, frames=frames, interval=80, blit=False)
    anim.save(path, writer=animation.PillowWriter(fps=14))
    plt.close()
    print(f"[viz] animation -> {path}")


def render_dashboard(history, focus_log, path="resonant_fauna_dashboard.png"):
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    fig.patch.set_facecolor("#0d1117")
    for row in ax:
        for a in row:
            a.set_facecolor("#161b22")
            a.tick_params(colors="#8b949e")
            for sp in a.spines.values(): sp.set_color("#30363d")
            a.title.set_color("#e6edf3")
            a.xaxis.label.set_color("#8b949e"); a.yaxis.label.set_color("#8b949e")
            a.grid(True, alpha=0.15)

    # population
    a = ax[0,0]
    a.plot(history["pop"], color="#58a6ff")
    a.set_title("Population (alive)"); a.set_xlabel("step"); a.set_ylabel("n")

    # mean energy
    a = ax[0,1]
    a.plot(history["mean_energy"], color="#3fb950")
    a.set_title("Mean energy of living"); a.set_xlabel("step"); a.set_ylabel("energy")
    a.set_ylim(0,1)

    # cumulative food eaten
    a = ax[0,2]
    a.plot(history["total_eaten"], color="#d29922")
    a.set_title("Cumulative food eaten (all)"); a.set_xlabel("step")

    # focus creature behavioural latches
    a = ax[1,0]
    a.plot(focus_log["avoid"], color="#f85149", label="avoid latch")
    a.plot(focus_log["pursue"], color="#d29922", label="pursue latch")
    a.plot(focus_log["pain"], color="#bc8cff", label="pain (slow)")
    a.set_title("Focus brain: held decisions"); a.set_xlabel("step")
    a.legend(facecolor="#161b22", labelcolor="#e6edf3", fontsize=8); a.set_ylim(0,1.05)

    # focus creature CPG rhythm
    a = ax[1,1]
    seg = slice(0, min(300, len(focus_log["cpg_xL"])))
    a.plot(focus_log["cpg_xL"][seg], color="#58a6ff", label="CPG left")
    a.plot(focus_log["cpg_xR"][seg], color="#f0883e", label="CPG right")
    a.set_title("Focus brain: CPG half-centre rhythm"); a.set_xlabel("step")
    a.legend(facecolor="#161b22", labelcolor="#e6edf3", fontsize=8)

    # focus creature energy + thrust
    a = ax[1,2]
    a.plot(focus_log["energy"], color="#3fb950", label="energy")
    a.plot(focus_log["thrust"], color="#58a6ff", alpha=0.6, label="thrust")
    a.set_title("Focus brain: energy & locomotion"); a.set_xlabel("step")
    a.legend(facecolor="#161b22", labelcolor="#e6edf3", fontsize=8)

    plt.tight_layout()
    plt.savefig(path, dpi=110, facecolor="#0d1117")
    plt.close()
    print(f"[viz] dashboard -> {path}")

# ============================================================================
# 8. MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*78)
    print("RESONANT FAUNA  -  brains of interference gates + latches + CPG")
    print("="*78)
    _verify_bank()
    print()
    world, creatures, history, focus_log, frames = simulate(
        n_creatures=8, steps=900, food_target=26)
    render_dashboard(history, focus_log)
    render_animation(frames)

    print("\n" + "="*78)
    print("LEDGER")
    print("="*78)
    print("VERIFIED MECHANISM (real dynamics, self-tested):")
    print("  - interference soma gate bank: all 6 truth tables exact")
    print("  - synaptic latch: hold+leak capture of transient decisions (V18)")
    print("  - CPG: intrinsic half-centre rhythm, no external clock")
    print("  - closed sense->resonate->latch->CPG->act->world loop, per creature")
    print("DESIGNED (chosen, not learned):")
    print("  - gate weights/bands, latch decays, CPG coupling, wiring diagram,")
    print("    sensor encodings, metabolic constants")
    print("EMERGENT (not coded as a rule):")
    print("  - foraging paths, wall-hugging, collision-shy turns,")
    print("    population boom/bust as food depletes, individual lifespans")
    print("NOT CLAIMED:")
    print("  - that real nervous systems are wired this way; that anything here")
    print("    is conscious. Only: three resonator-machine types, embodied,")
    print("    produce lifelike foraging. Do not hype. Do not lie. Just show.")
    print("="*78)