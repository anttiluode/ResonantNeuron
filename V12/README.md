# GeometricNeuron12 — Real PDE

This folder re-derives the v11 "parity wall" result — the claim that
dendrite length alone retunes a resonator unit between XOR-like and
XNOR-like behavior — on an actual 2-D wave field, instead of the lumped
soma/dendrite ODE the earlier result was built on.

**Start with `PAPER.md`.** It has the full argument, every number, and the
honest verdict: the core mechanism survives, the predicted shape of the
transition doesn't, and the reason it doesn't (a dendrite channel acting as
a two-port resonator, not a one-way delay line) is the actual finding of
this build.

This README is just the map of the six scripts and what each one is for.

---

## What changed from v11

v11's unit injected a dendrite's "length" as an instant algebraic phase
shift, `φ = Ω·L/v`, applied to a phasor. There was no real space, no real
propagation, nothing that could reflect or resonate on its own.

This folder replaces that with the real thing: a domain shaped like
Berglund's angled-cavity rings — a circular soma cavity, satellite cavities
sitting at a genuine radial distance and angle, connected by channels of
real physical length — solving `u_tt = c²∇²u − γu_t + forcing` on that
domain with Neumann (reflecting) walls. "Length" here is a number of grid
cells a wave actually has to cross, at a finite speed, with nothing assumed
about what that crossing does to its phase.

---

## The files, in the order they were actually run

**`cavity_field.py`** — the solver and the geometry builder. `CavityField`
does the leapfrog wave integration; `build_geometry()` carves the soma
disc, the satellite discs, and the connecting channels into a binary mask
at whatever lengths and angles you ask for. Running this file directly is
just a stability check: drive a pulse, confirm the field stays bounded for
1000 steps. Nothing about XOR or logic is tested here — this is the
foundation the rest of the folder stands on.

**`pde_xor.py`** — the first real test: at *matched* dendrite lengths, does
the soma show clean constructive/destructive interference, the way the
lumped model's XOR mechanism predicted? It does — exact zero on
disagreement, clean nonzero on agreement. This file also contains the
signal-to-noise tuning that had to happen before the result could be
trusted (an earlier, longer-channel setup put the soma signal within 0.4%
of the satellite drive amplitude, too close to the noise floor to mean
anything; this file uses the corrected, checked parameters).

**`pde_length_sweep.py`** — sweeps one dendrite's *actual channel length* on
the grid and asks whether both XOR-like and XNOR-like regimes appear, in
the regime where the channel length is comparable to the carrier
wavelength. They do, qualitatively. This is also the file that first
surfaced the discrepancy with v11's clean prediction — at full-wavelength
mismatch the unit should have returned exactly to its starting regime, and
it didn't, which is what sent the investigation into the next two files.

**`pde_length_sweep_delayline_regime.py`** — redoes the length sweep in the
regime the lumped model's assumptions actually require: channel length much
smaller than the carrier wavelength, so the channel should behave as a true
one-way delay line. Covers a full half-wavelength of phase mismatch with
parameters re-tuned for signal-to-noise at this much lower carrier
frequency. Confirms both regimes still appear, but the transition between
them is not the clean curve v11 predicted.

**`wall_shape_analysis.py`** — looks at the *raw, unthresholded* gap between
"agree" and "disagree" amplitudes as phase mismatch is swept, rather than
forcing each point through a binary XOR/XNOR/degenerate classifier. This is
the file that shows the transition is lopsided, crosses zero near 60°
rather than the predicted 90°, and sits in an extended low-margin plateau
rather than a sharp instability point.

**`standing_wave_diagnostic.py`** — the explanation. Checks whether the
amplitude at the channel's midpoint decays monotonically with channel
length (what a one-way delay line with damping would do) or not (the
signature of reflection and standing-wave structure). It's non-monotonic —
confirming the channel is acting as its own short resonant element, which
is the mechanical reason the clean wall didn't survive the move to a real
field.

---

## Reproduce it

```
python cavity_field.py
python pde_xor.py
python pde_length_sweep.py
python pde_length_sweep_delayline_regime.py
python wall_shape_analysis.py
python standing_wave_diagnostic.py
```

Each script is self-contained and prints its own numbers; none of them
depend on a saved output from a previous run. `cavity_field.py` is imported
by the others for the solver and geometry builder, so keep it in the same
folder.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
