# GeometricNeuron14 — Directionality, Done Right

This folder finally produces directional signal flow — the thing
GeometricNeuron13 tried four ways and failed to get — by abandoning the
geometric/passive approach entirely and building the mechanism the actual
AIS literature describes: an excitable origination site with a real
inactivation variable.

**Start with `PAPER.md`.** It has the full argument, every number, the
control test that makes the result trustworthy, and the grounding in
Christophe Leterrier's 2018 *Journal of Neuroscience* AIS review. This
README is the map of the three scripts.

---

## The short version

v13 established, by four failures, that no passive or
instantaneous-amplitude mechanism can flow one way — ruling out the
"angled geometry gives directed circulation" story. Reading Leterrier
identified the three missing ingredients: spike **origination** at a
localized site (not filtering a passing wave), **inactivation** (genuine
between-timestep state, not instantaneous threshold), and a **Nav-density
gradient** (the AIS is ~30× easier to excite than dendrites). This folder
implements those and gets clean directional propagation with a control.

---

## The files, in the order they were run

**`cavity_field.py`** — the wave PDE solver from earlier folders, copied in
so this folder runs standalone. Not central to v14 (the directionality
mechanism is the excitable line, not the wave field), but kept for
continuity and because `ais_origination.py` uses it.

**`ais_origination.py`** — the FIRST approach, kept honestly because it
**failed**. It builds an origination site with a toy Nav gate, but the gate
triggers on local field amplitude, so it fires near-equally whether driven
from the soma side or the axon side (300 vs 280 fires) — reproducing the
exact v13 failure one more time. This file is in the repo as the record of
the wrong turn, not deleted. Run it to see the failure that motivated the
fix.

**`propagating_spike.py`** — the fix, and the core mechanism. A 1-D
excitable line (FitzHugh–Nagumo), the textbook model of how a nerve impulse
travels. Two tests: (1) a kicked pulse propagates directionally in its
launch direction and spawns no reverse partner (the inactivation wake blocks
reversal); (2) two pulses from opposite ends annihilate on collision rather
than passing through — the definitive signature of nonlinear,
history-dependent propagation, which linear waves cannot do.

**`ais_directionality.py`** — the capstone. Builds a neuron axis with
Leterrier's excitability gradient (dendrite hard to excite, AIS very easy,
axon normal), originates a spike at the AIS, and measures forward vs.
backward spread. Result: 49 cells forward (into axon) vs. 5 cells backward
(into dendrite), a ratio of ~10:1 — **and a control with the gradient
removed spreads symmetrically (48/48)**, proving the asymmetry comes from
the Nav-density gradient, not the kick location.

---

## The honest boundary

This is not a perfect one-way valve, and doesn't claim to be — real
back-propagating action potentials do invade dendrites (Leterrier says so),
and the model reproduces exactly that: backward spread is attenuated to 5
cells, not zero. The verified claim is *strong directional attenuation via
the excitability gradient*, which is what the biology actually says.

The deflationary-but-useful takeaway for the whole project: directionality
is **not** a free consequence of the interference/geometry substrate. The
geometry gives you computation (parity, the v11 result); the excitable
dynamics give you direction. Different physical ingredients, different jobs —
and conflating them was the error this folder corrects.

---

## Reproduce it

```
python propagating_spike.py
python ais_directionality.py
python ais_origination.py
```

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
