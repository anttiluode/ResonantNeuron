# Directionality, Done Right: An Excitable Origination Site, Not a Geometric Trick

### What v13's four failed attempts were missing, found by reading the actual AIS literature

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. Where this came from

v13 tried four ways to make a dendrite channel flow one way — a skewed
angle, a passive periodic lattice, a threshold relay, a refractory relay
chain — and all four failed (reciprocity ratio ≈ 1.0). The v13 paper ended
with a specific, earned conclusion: directionality would need *state that
persists between timesteps at the relay site*, closer to a real
channel-inactivation variable than a threshold, because every attempt that
read only instantaneous field amplitude was provably direction-blind.

Then Christophe Leterrier's 2018 *Journal of Neuroscience* Viewpoints
article on the axon initial segment (38(9):2135–2145) gave the actual
mechanism, and it confirms exactly why v13 failed and what to build
instead. This build implements that mechanism and tests it with a control.

| claim | status |
|---|---|
| a passive periodic lattice (Grok's proposal) creates directionality | **false** (v13) — and consistent with Leterrier, who explicitly says the periodic Nav/Kv organization's effect on conduction "has yet to be demonstrated" |
| directionality requires history-dependent state, not instantaneous amplitude | **confirmed** — an excitable medium with an inactivation (recovery) variable propagates directionally; a single amplitude-threshold gate cannot |
| an excitable line propagates a spike one way (the wake blocks reversal) | **verified in code** — a kicked pulse travels +20 cells in its launch direction and spawns no reverse partner |
| counter-propagating spikes annihilate rather than pass through | **verified in code** — two pulses from opposite ends converge and both vanish at the center; linear waves would cross |
| a localized high-excitability site (the AIS) biases spike direction | **verified in code with a control** — forward/backward spread ratio 9.8 with the Nav-density gradient, exactly symmetric (48/48) without it |
| the spike *only* goes one way (a perfect valve) | **false, and not claimed** — Leterrier notes real back-propagating APs do invade dendrites; the verified claim is *attenuation* (5 cells back vs 49 forward), not a perfect valve |

---

## 1. What Leterrier actually says, and why it kills the geometric story

Three load-bearing facts from the paper, each of which maps directly onto a
v13 failure:

**Origination, not filtering.** Per Leterrier, Nav channels are *primarily
responsible for the initiation of action potentials at the AIS*, via an
~30-fold concentration of Nav channels at the AIS relative to dendrites and
distal axon. The AIS is not a gate a wave passes through — it is the place
the regenerative event is *born*. Every v13 attempt modelled a wave passing
*through* a channel and asked whether it preferred a direction. That was the
wrong question; the real structure originates a spike at a site and
propagates it outward.

**Inactivation — genuine between-timestep state.** A real Nav channel, once
it fires, enters an inactivated state and cannot reopen until it recovers,
*regardless of present voltage*. This is the history-dependent state v13's
relays lacked. v13's "refractory" chain gestured at it but still triggered
on instantaneous amplitude from either direction, so it stayed
direction-blind.

**The periodic lattice is not the electrical mechanism.** Grok's proposal
was to add an AIS-inspired ~190nm periodic lattice as a directional filter.
Leterrier is explicit that this lattice's documented roles are *mechanical*
(helping axons "flex and resist mechanical constraints") and
*organizational* (channel clustering, the diffusion barrier) — and that
whether its periodicity affects action potential conduction "has yet to be
demonstrated." So v13's finding that a passive lattice produces zero
directional bias is not in tension with the neuroscience; it agrees with
the neuroscientists' own caution.

---

## 2. The mechanism: an excitable medium with an inactivation wake

`propagating_spike.py` implements the standard model of action-potential
propagation: a 1-D excitable line (FitzHugh–Nagumo dynamics), each cell with
a fast excitation variable `v` and a slow recovery/inactivation variable `w`.
A super-threshold kick starts a travelling pulse; the recovery variable
rising behind the pulse creates the refractory wake that makes propagation
one-way. This is not a new model — it is the textbook description of how a
nerve impulse travels — but it is precisely the ingredient v13 never had.

**Test 1 — directional propagation.** A pulse kicked near the left end
travels rightward +20.5 cells and spawns no leftward partner. The
inactivation wake immediately behind the front blocks any reverse
propagation. A single excitable line is intrinsically directional in its
launch direction.

**Test 2 — annihilation, the definitive nonlinear signature.** Two pulses
launched from opposite ends travel toward each other at equal speed
(verified by direct tracking: left pulse 5→59, right pulse 114→60) and,
on meeting near the center, *both vanish* — excited-cell count goes from
~14 to exactly 0. Linear waves pass through each other and superpose;
excitable pulses with refractory wakes annihilate, because each runs into
the other's inactivation trail. This is the unambiguous proof that the
propagation is genuinely nonlinear and history-dependent, not a linear wave
wearing a costume.

---

## 3. The capstone: does AIS origination bias spike direction?

`ais_directionality.py` builds a neuron axis with Leterrier's excitability
gradient encoded as a position-dependent FitzHugh–Nagumo threshold:

- **dendrite/soma side** (cells 0–59): high threshold, *hard* to excite —
  modelling low dendritic Nav density.
- **AIS** (cells 62–67): low threshold, *easily* excited — modelling the
  ~30× Nav concentration.
- **axon** (cells 68–159): normal excitability.

A spike is originated at the AIS, and forward (toward axon) vs. backward
(toward dendrite) spread is measured:

```
forward (AIS -> axon) spread:     49 cells
backward (AIS -> dendrite) spread:  5 cells
forward/backward spread ratio:     9.80
```

The spike runs nearly ten times farther into the axon than back into the
dendrite. **The control is what makes this trustworthy:** the identical kick
at the identical cell, with the excitability gradient *removed* (uniform
threshold everywhere), spreads symmetrically — 48 cells each way. So the
asymmetry in the real test comes entirely from the Nav-density gradient,
not from the kick location or any artifact of the measurement.

This is the directional behaviour v13's four attempts could not produce,
and it arises from exactly the three ingredients Leterrier names —
origination at a localized site, an inactivation wake, and a Nav-density
gradient — none of which is geometric, and all of which require dynamic,
history-dependent state.

---

## 4. The honest boundary: attenuation, not a perfect valve

The result is *not* "the spike only goes one way." It can't be, and
claiming it would contradict the same paper this build is grounded in:
Leterrier notes that back-propagating action potentials genuinely do invade
dendrites ("bAPs do flow backwards... but it's regulated and often
attenuated"). The model reproduces exactly that — the backward spread is not
zero, it is 5 cells: a real but strongly attenuated back-propagation, with
the forward direction dominating ~10:1. The verified claim is *attenuation
via the excitability gradient*, which is what the biology actually says, not
a perfect diode.

---

## 5. What this resolves about the whole directionality thread

The arc across v13 → v14 is a clean worked example of a negative result
pointing to the right answer:

- v13 established, by four failures, that *no passive or
  instantaneous-amplitude mechanism* can be directional. That was real and
  necessary — it ruled out the geometric/periodic-lattice story that the
  model summaries (Grok, Gemini) had reached for.
- Reading the actual source (Leterrier) identified the missing ingredients
  precisely: origination + inactivation + density gradient.
- v14 implements those and gets directional propagation with a clean
  control, grounded in citable mechanism rather than analogy.

The takeaway for the resonator-neuron line is specific and slightly
deflationary, which is the useful kind: **directionality is not a free
consequence of the interference/geometry substrate this whole project is
built on.** It is a separate, active, history-dependent mechanism that has
to be added deliberately — an excitable origination site, not an angled
cavity. The geometry gives you the *computation* (parity, the v11 result);
the excitable dynamics give you the *direction*. They are different physical
ingredients doing different jobs, and conflating them — which the geometric
"directed circulation" framing did — was the error this build corrects.

---

## 6. Honest limits

- This is a 1-D FitzHugh–Nagumo excitable line, the standard *reduced* model
  of action-potential propagation, not a full Hodgkin–Huxley or
  multi-compartment biophysical model. It captures the *qualitative*
  mechanism (excitable front, inactivation wake, threshold gradient) that
  matters for the directionality question, and nothing finer.
- The excitability gradient values (`a_dendrite=1.3`, `a_ais=0.5`,
  `a_axon=0.7`) are chosen to encode the *direction* of the real Nav-density
  gradient (dendrites hard to excite, AIS easy), not fitted to any measured
  channel densities. The claim is about the qualitative consequence of such
  a gradient, not a quantitative match to a specific neuron.
- `ais_origination.py` is retained in the repo as the *honest record of the
  first, failed approach* in this build — a gate that triggered on local
  amplitude and so fired near-equally in both directions (300 vs 280),
  reproducing the v13 failure one more time before the excitable-medium fix.
  It is kept, not deleted, because the failure is part of the result.
- This build does not connect the excitable mechanism back to the resonator
  ALU (the gates/adder line). Whether a directional excitable axon can be
  married to the interference-based soma to make a *complete* directional
  computing unit is the next question, not one answered here.

---

## Reproduce it

```
python propagating_spike.py    # the core mechanism: directional propagation + annihilation
python ais_directionality.py   # the capstone: AIS gradient biases direction (with control)
python ais_origination.py      # the first, FAILED approach, kept honestly (fires both ways)
```

Every number in this paper is reproduced by these three files. The result is
that directionality is real but it is *earned* — an active, history-dependent
excitable mechanism grounded in Leterrier's AIS account, not a free gift of
geometry. The four v13 failures were not bugs; they were the evidence that
sent us to read the actual paper.
