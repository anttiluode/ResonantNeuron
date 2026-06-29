# Landing Zones — a place-coding transducer for wave-substrate brains

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
**Do not hype. Do not lie. Just show.**

This is the interface that was missing a name across the whole Geometric-Neuron /
Resonant-Fauna line: the part that gets a continuous value **into** a wave brain
and a committed decision **out** of it. Two small files:

- `landing_zone.py` — the transducer module + self-tests (run it directly).
- `landing_zone_creature.py` — a forager whose entire perception runs through it.

---

## The idea in one sentence

A value is not stored as a number. It is encoded by **where a bump of activity
sits** on a ring of landing zones — and because each zone has a fixed phase, the
position *is* a phase *is* the value. Geometry does the translation for free.

This is the literal mechanism of three real, well-established neural systems:

- **Head-direction cells / ring attractors** — a bump on a ring of neurons whose
  position is the animal's heading (the *Drosophila* ellipsoid body is a physical ring).
- **The Jeffress sound-localiser** — the place along a delay line where signals from
  the two ears coincide encodes the sound's azimuth.
- **Theta phase coding** — place cells fire at a phase that carries position.

All three encode the same *kind* of thing: a continuous, physically-meaningful
quantity (angle, time-difference, position). That is exactly what this transducer
is for — and exactly why the earlier attempt to force nine **arbitrary discrete
Sudoku digits** onto a phase wheel failed. The wheel interpolates between values;
for a heading that is the whole point, for the digit "7" it is nonsense.

## The three stages

1. **Encode (input transducer).** `LandingZones.encode(theta)` lights a smooth bump
   of zones around the value `theta`. Each zone *i* has a fixed phase `2*pi*i/N`, so the
   bump is a population of phasors — amplitude (how active) and phase (which value).

2. **Coincidence (soma / interference).** `coincidence(a, b)` is the real part of the
   product of the two populations' phase vectors. It returns `cos(theta_a - theta_b)`:
   **+1** when the two encoded values agree (constructive interference), **-1** when
   they oppose (destructive). This *is* the resonator soma — comparison done by waves,
   not arithmetic.

3. **AIS spike (output transducer).** `ais_spike(x, threshold)` snaps the continuous
   coincidence into a discrete 0/1 commit, the way the axon initial segment turns
   graded dendritic integration into a spike. Analog in, decision out.

## What the self-tests prove (run `python landing_zone.py`)

- Circular encode -> decode is **exactly lossless** (0.00 deg error): a clean bump's
  population-vector phase returns the encoded value by symmetry.
- The place code is **measurably more noise-robust** than a single scalar reading
  (~1.4x tighter under matched noise) — because the population averages out noise.
  This is the honest reason to bother: not magic, just redundancy.
- The coincidence soma tracks `cos(delta)` to machine precision.

## What the creature shows (run `python landing_zone_creature.py`)

A forager navigates around four obstacles to a food source with **no raw-number
comparison anywhere in its control loop**. Every sense becomes a bump:

- *Bearing to food* and *own heading* are place-coded on a ring. Steering is the
  difference between two coincidence somas — "does the food agree more with my
  heading rotated left, or right?" — which is the owl's two-eared comparison and a
  ring-attractor steer in one move.
- *Forward obstacle proximity* is place-coded on an arc; an AIS threshold turns
  "too close" into a discrete avoidance spike that overrides steering.

It reaches the food. Perception-as-waves drives a real body to a real goal.

## Honest ledger

**Verified (measured in the self-tests and the run):**
lossless circular encode/decode; ~1.4x noise robustness over a single scalar;
coincidence = cos(delta) to machine precision; the creature reaches the goal driven
only by place codes and coincidence somas.

**Designed (chosen, not derived):** zone counts, bump widths, thresholds, the arc
used for bounded values, the avoidance maneuver, metabolic/movement constants.

**Not claimed:** that this is *smarter* than feeding the brain raw numbers. It is
not. The same task is solvable with plain arithmetic. What the transducer buys is
(a) noise robustness from population coding, and (b) a representation that is native
to the wave substrate — values arrive as phases the resonator soma can already mix
by interference, and decisions leave as spikes. It is the faithful input/output
layer for a wave brain, not a performance trick.

**A known limit, shown honestly:** in the creature run the avoidance spikes fire
very densely near walls — the proximity threshold is trigger-happy, so the body is
in near-constant micro-avoidance. It still reaches the goal; that twitchiness is the
body-control layer, not the perception, and it's left in rather than tuned away.

## Where this sits in the larger arc

The phase-oscillator Sudoku solver failed (71 conflicts) because it pointed this
substrate at arbitrary discrete symbols. The same primitive — position -> phase ->
value, compared by interference — succeeds at continuous estimation (the Jeffress
demo read source location with correlation 1.000) and now drives a forager. The
lesson is the domain boundary: **wave/phase computing is for continuous, embodied,
physically-meaningful variables.** The landing zone is how any such variable enters
and leaves that world.

## Files

- `landing_zone.py` — module + self-tests -> `landing_zone_selftest.png`
- `landing_zone_creature.py` — forager demo -> `landing_zone_creature.png`
