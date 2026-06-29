# WaveReservoirHorizon

A wave-based reservoir that stores the **temporal order** of its inputs, and a
measurement of how long that memory survives — in an open medium versus a
**Berglund magnetron cavity**, with the dissipation matched so the comparison is
fair.

Governing standard for this repo: **do not hype, do not lie, just show.** Every
claim below is produced by code in `src/` and can be reproduced by running it.
Where a result is a lower bound, it says so. Where a hypothesis failed, it stays
in the ledger as a failure.

---

## What this is

The medium is the damped 2D wave equation (Langtangen & Linge, *Finite difference
methods for wave equations*, eq. 63), with two additions:

- a spatially varying damping field `b(x,y)` — the absorbing boundary / "sponge",
- an optional local restoring field `w0(x,y)` giving each region a preferred
  resonant frequency `f0 = w0/2π` — the physical stand-in for the ion-channel
  resonance gradient measured by Narayanan & Johnston (2007).

The task is deliberately built so only *temporal order* can solve it: three
pulses of distinct magnitudes {1, 2, 3} are fired **at a single point** in one of
the 6 possible orders (6 classes). Same point every time, so "which location was
hit" carries no information. A **linear** readout (logistic regression) on the
coarse-grained frozen field at a chosen delay must recover the order. Accuracy
vs. delay is the **forgetting curve**; the delay at which it crosses halfway to
chance is the **memory horizon**.

---

## The headline result (and how it corrected the author's own guess)

Earlier in this line of work we found a magnetron cavity holding order ~40×
longer than open space, and **suspected it was an artifact**: the cavity is
nearly lossless (tiny outlet, reflecting walls), and a low-loss box holding a
pattern a long time is not surprising. The honest test was to **match the
dissipation** — force every condition to lose energy at the same rate — and see
if the cavity advantage survived.

It survived. With all conditions matched to the **same 32-step energy half-life**:

| 2×2 horizon (steps) | uniform channels | tuned channels |
|---|---|---|
| **open box** | ~120 (collapsed) | ~100 (collapsed) |
| **magnetron cavity** | >1900 (lower bound) | >1900 (lower bound) |

- **Geometry main effect: ~+1800 steps.** With energy draining equally fast in
  all four conditions, the cavity *still* holds the readable order ~16× longer
  than its own energy half-life, while the open box forgets right as its energy
  fades. So the cavity is **not** merely leaking less — its shape locks the input
  order into long-lived standing modes. The author's "it's just low loss"
  hypothesis was **wrong**, and the matched-dissipation test is what showed it.
- **Channel-tuning main effect: ≈0 (−10 steps, within noise).** Giving each
  satellite its own resonant frequency ("each to its own frequency") did **not**
  extend the order-memory horizon in this task. Clean negative for the
  Snyder/Narayanan-Johnston-inspired upgrade *as a carrier of temporal order*.
  The per-region resonance may matter for *frequency* selectivity (a different
  task) but it is not what carries *sequence* here; the geometric mode structure
  is.

### Why we trust the cavity number (anti-leak checks)
At delay 1900, dissipation matched:
- order signal is **~98× above the readout noise floor** (not a sub-noise leak),
- the surviving field is **structured**, spatial std/mean ≈ 3.3 (not a flat near-DC
  pedestal masquerading as memory — the failure mode we hit in an earlier version).

### What we do NOT claim
- The cavity horizon is a **lower bound** (>1900 steps); we did not run it to
  collapse here, so "+1800" is itself a floor, not a measured value.
- "Steps" are not milliseconds. A physical-time conversion exists in
  `measure_horizon.py` but it rests on an openly-stated calibration choice
  (a chosen dendritic wave speed and cable length), not a measurement. Treat the
  step-count and the cavity/box **ratio** as the defensible quantities; treat any
  millisecond figure as illustrative and tunable.

---

## Files

```
src/
  reservoir.py        core solver (damped wave + sponge + w0 restoring field),
                      geometries (open box, magnetron), helpers. Verified:
                      a patch with w0=2πf0 peaks within ~3% of f0 (tests/).
  measure_horizon.py  single-factor forgetting curve: open box vs cavity, with
                      a steps->ms calibration (calibration flagged as a choice).
  two_factor.py       the 2×2 dissipation-matched experiment above. This is the
                      one that can embarrass the cavity result, and didn't.
results/
  horizon.json        forgetting curves + horizons (single factor)
  two_factor.json     the 2×2 table, matched half-lives, shuffle controls
docs/
  THEORY.md           how this maps onto the geometric-neuron stack and the
                      cited literature, with the honest ledger
```

## Run

```bash
mkdir -p results
python3 src/two_factor.py      # the main result (a few minutes)
python3 src/measure_horizon.py # single-factor curves + ms calibration
```

## Honest ledger

- **Verified in code:** the restoring term produces frequency-selective resonance;
  the sponge absorbs (single-pulse energy → ~1% of peak); the open box forgets
  order on the timescale of its energy; the cavity holds structured order ~16× its
  energy half-life under matched dissipation; the long-horizon cavity signal is
  ~98× above noise and spatially structured.
- **Failed / null (kept in the ledger):** per-compartment frequency tuning did
  not extend the order horizon. An earlier weak-sponge run plateaued falsely
  (slow near-DC residue) and was caught by a diagnostic, not shipped. A first
  dissipation-matching attempt targeted the wrong (unreachable) half-life and
  silently produced a null; caught and fixed by verifying the match held.
- **Lower bounds, not measurements:** cavity horizons (>1900 steps); the geometry
  main effect (≥~1800 steps); any millisecond figure.
- **Open questions:** where does the cavity curve actually collapse; whether
  channel tuning helps a *frequency*-discrimination task (vs. the order task here);
  whether a graded `w0` ramp behaves differently from discrete tuned patches.

## References (context, not endorsement of every claim)

- Langtangen & Linge, *Finite difference methods for wave equations* — the solver.
- Snyder (2026), *Resonant hierarchies*, Front. Psychol. 17, doi:10.3389/fpsyg.2026.1704370
  — framework for dendritic resonance gradients and multiscale nesting; motivates
  the `w0` field. It is a hypothesis/synthesis paper, not new measurement.
- Narayanan & Johnston (2007) — the measured ~2→12 Hz somatodendritic resonance
  gradient that `w0(x,y)` stands in for.
- El-Quessny & Feller (2021), *Dendrite morphology minimally influences...* — the
  empirical counterweight: bare dendritic shape can be computationally inert. Our
  null tuning effect and our finding that *mode structure* (not silhouette detail)
  carries the memory should be read next to this.
```
