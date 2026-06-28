# Does Anything In This Model Actually Flow One Way?

### Testing Grok's AIS/directionality proposal directly on the real PDE — and finding the easy version of "directed flow" doesn't exist

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. The claim being tested

A collaborating model (Grok) suggested that the repo's `skew_deg` parameter
("angled cavities") already produces directed circulation/chirality in
dendrite channels, and proposed adding a periodic, AIS-inspired structure
(in the spirit of the real ~190nm ankyrin-G/spectrin lattice that gives
axons their forward-only signal flow) to strengthen this further — framed
as a small refinement to something the model was said to already have.

This paper tests that claim directly on the v12 PDE, rather than discussing
it. The result is not a refinement. **Neither mechanism Grok proposed — a
skewed channel angle, or a passive periodic lattice along the channel —
produces any directional bias at all**, and a third, more serious attempt
(a true active relay with biological refractory dynamics) also failed, for
a specific and informative reason. Nothing built across this whole line so
far transmits a signal differently in one direction than the other.

| claim | status |
|---|---|
| `skew_deg` (channel angle) already produces directed circulation | **false, measured directly** — reciprocity ratio 1.0000 at every angle tested |
| a passive periodic lattice (the literal AIS-inspired proposal) breaks reciprocity | **false, measured directly** — ratio 1.0000 even with a 6-period constriction lattice |
| an active, threshold-triggered relay (no refractory state) breaks reciprocity | **false, measured directly** — ratio 1.07, indistinguishable from noise |
| a chain of relays with genuine refractory dynamics (the real AP mechanism) breaks reciprocity | **false as built** — ratio 0.58, and the apparent "backward boost" that showed up first was a feedback-loop measurement artifact at the relay nearest the read point, traced and confirmed, not a real directional effect |
| a real AIS depends on voltage-gated, regenerative, refractory dynamics, not passive geometry | **the established neuroscience fact this paper confirms by elimination** — every passive mechanism failed exactly as the mechanism predicts it should |

---

## 1. Why this needed a direct test, not a discussion

Grok's writeup mixed two different things under one name. It correctly and
accurately described the real biology — the AIS's ~190nm ankyrin-G/
βIV-spectrin periodic lattice, voltage-gated Na⁺/K⁺ channel clustering, the
domain boundary between axon and soma. It then said the *model's* skew
coupling "already gives directed circulation," which conflates two
different parts of this whole project's history: the **lumped lag-operator
work** (`skew_core.py`, from the v9/v10 line, which genuinely does compute
a directional quantity, `L = Im(z · z̄_lag)`, from a covariance matrix) and
the **v12 PDE cavity work** (`cavity_field.py`), where `skew_deg` is only a
drawing angle for where a satellite cavity sits — it has never been tested
for directionality, and nothing in how it's built gives a mechanical reason
to expect any.

That distinction is exactly the kind of thing worth checking rather than
asserting, because the two pieces of code share a word ("skew") but do
different jobs.

---

## 2. Test 1 — does `skew_deg` make a channel directional?

`test_skew_reciprocity.py` builds a single straight channel between a
satellite cavity and the soma at various `skew_deg` values, then measures
transmission **both ways**: drive the satellite, read the soma (forward);
drive the soma, read the satellite (backward), on the identical mask.

```
skew_deg | fwd (sat->soma) | bwd (soma->sat) | ratio
       0 |        0.20983  |        0.20983  | 1.0000
      15 |        0.34337  |        0.34337  | 1.0000
      30 |        0.24100  |        0.24100  | 1.0000
      45 |        0.20985  |        0.20985  | 1.0000
      60 |        0.15474  |        0.15474  | 1.0000
```

Ratio is exactly `1.0000` at every angle, to five decimal places. This is
not a near-miss — it's exact reciprocity, which is the physically correct
behavior for a passive linear wave equation (`u_tt = c²∇²u − γu_t`):
nothing in that equation has any notion of "direction" independent of
which end you happen to drive. Angle changes *how much* energy couples
into the channel (note the amplitude does vary with angle — geometry
matters for coupling efficiency) but never *which way* it prefers to flow.

---

## 3. Test 2 — does a passive periodic lattice (the literal AIS-inspired proposal) do it?

`ais_filter.py` builds a channel with a genuine periodic constriction —
narrow, wide, narrow, wide, six periods, mimicking the *spacing* of a real
cytoskeletal lattice, even varying local wave speed in the constricted
zones. This is the most literal version of Grok's suggestion: a passive
structure shaped like the real biology.

```
Periodic-constriction channel, forward (sat->soma): 1.35722
Same channel, backward (soma->sat):                 1.35722
Ratio: 1.0000
```

Again exactly reciprocal. This confirms a specific piece of wave physics
worth stating plainly: **periodicity can shape *which frequencies* pass
through a channel (a bandgap, a filter), but it cannot by itself make
those frequencies prefer a direction.** A photonic crystal, a Bragg
grating, a 1-D phononic lattice — all famous for frequency-selective
behavior, none of them directional, for the same underlying reason: they
are time-reversal-symmetric, passive, linear structures. The AIS's real
190nm lattice is real and does real things (channel clustering, a
diffusion barrier), but periodicity *alone*, modeled as a passive
geometric feature, is not the part of the AIS that makes it one-way.

---

## 4. Test 3 — does an active, threshold-triggered relay do it?

This is where the test gets more interesting, because the first attempt
at an active (nonlinear) element also failed, and figuring out *why* is
the most useful part of this paper.

`active_relay_test.py` places a relay that reads the field amplitude at
one point and, whenever it crosses a threshold, overwrites a different
point further along with a fixed-gain copy — a toy "read here, write
there" element, explicitly asymmetric in code. A proper four-way
comparison (passive vs. relay-present, forward vs. backward) isolates the
relay's actual contribution:

```
  passive, forward  (sat->soma): 0.20983
  relay,   forward  (sat->soma): 0.41286   (relay reads the driven side)
  passive, backward (soma->sat): 0.20983
  relay,   backward (soma->sat): 0.38643   (relay's read side is now undriven)

  Forward boost from relay:  1.968x
  Backward boost from relay: 1.842x
  Directionality ratio:      1.068
```

The relay boosts transmission substantially in *both* directions, almost
equally. The mechanical reason is simple once it's traced: the relay reads
**scalar amplitude at a point**. A wave passing through that point from
either direction produces the same amplitude there — amplitude carries no
information about which way the wave was travelling when it arrived. A
relay built on amplitude-thresholding alone cannot be directional, no
matter how asymmetric its read/write wiring looks in the code, because the
read step itself already lost the one piece of information directionality
would require.

---

## 5. Test 4 — does a refractory relay chain (the real AP mechanism) do it?

A real action potential's one-way property doesn't come from a single
threshold — it comes from **refractoriness**: membrane that just fired is
briefly unable to fire again, so a spike can propagate into fresh territory
ahead of it but cannot turn around and re-trigger the territory it just
came from. `refractory_chain_test.py` builds the honest version of this: a
chain of six relay points, each one firing forward to its specific next
neighbor and then entering a refractory window before it can fire again.

```
  passive, forward  (sat->soma): 0.20983
  relay,   forward  (sat->soma): 2.99386
  passive, backward (soma->sat): 0.20983
  relay,   backward (soma->sat): 5.15633

  Forward boost:  14.268x
  Backward boost: 24.574x
  Directionality ratio: 0.581
```

Not only is there no forward preference — backward transmission was
boosted *more*. This result was checked rather than reported as a
surprising finding, because a ratio below 1 in the "wrong" direction is
exactly the kind of number that deserves suspicion before belief.
`feedback_artifact_check.py` traced the raw field trace at the measurement
point and found the cause: when the chain is driven from the soma side, the
wave must travel the full channel length before reaching the relay node
closest to the satellite (`chain[0]`), which fires and writes to its
neighbor *inside the channel*, not at the satellite cavity itself. That
creates a short, local feedback loop trapped near the read point, inflating
the measured amplitude there — a measurement artifact from where the relay
chain's last link happened to sit, not a real directional transmission
effect. The raw trace shows clear oscillatory ringing consistent with a
local resonance, not a clean traveling pulse.

The deeper, correct lesson survives the artifact: refractoriness only
prevents *re-triggering*, the same chain element, immediately after it
fires. It does not, by itself, give the chain any way to tell which
direction the wave that triggered it came from — the chain order
(`sat → soma`) only determines which neighbor each link writes to, and
nothing in this construction stops the chain from being triggered, and
firing, equally well when approached from either end.

---

## 6. What this confirms about the real biology, by elimination

Every passive, geometric mechanism tested — channel angle, periodic
lattice spacing, even an active threshold relay without proper
direction-sensing — failed to produce directional transmission. That is
not a string of bugs; it is the correct physical answer, and it sharpens
exactly what a real AIS must be doing that none of these toy mechanisms
captured: a real axon initial segment relies on **voltage-gated ion
channels that are themselves asymmetric in a way tied to membrane state
history** (refractory sodium channel inactivation that depends on which
membrane patch fired *and when*, not just on local instantaneous
amplitude), combined with the fact that an action potential is a
**self-regenerating, supra-threshold, all-or-nothing pulse**, not a
linearly superposable wave. Directionality in a real axon is a property of
the *trajectory* of a nonlinear, history-dependent system, not a property
extractable from a single point's instantaneous field value — which is
exactly the gap every relay design here fell into.

The honest, falsifiable statement this licenses: **any attempt to give
this resonator-neuron line a directional dendrite is going to need state
that persists *between* time steps at the relay site itself** (something
closer to an inactivation variable than a threshold), not merely a
nonlinearity applied to the instantaneous field. That's a concrete
specification for the next build, earned by three different failed
attempts rather than guessed at the start.

---

## 7. Honest limits

- The refractory relay built here is a deliberately minimal toy (fire,
  write a fixed pulse, refractory for `N` steps) — not a Hodgkin-Huxley
  model and not a claim about exactly what a real Na⁺ channel does. It was
  built to isolate one property (does refractoriness alone confer
  directionality) and that property was cleanly tested and found
  insufficient on its own, with the geometry used.
- The feedback artifact in §5 was caught and explained, but the specific
  relay-chain geometry used (linear, evenly spaced, fixed gain) was not
  exhaustively explored. A different relay placement or chain density
  might behave differently; the claim here is limited to what was actually
  built and measured, not to refractory mechanisms in general.
- This paper does not attempt the more complete fix (e.g., an
  inactivation variable that depends on the relay's *own* recent history,
  not just instantaneous threshold-crossing) — that is the named next step
  from §6, not yet built.
- Everything here uses the v12 PDE solver unchanged; no claim is made
  about whether the same conclusions would hold in the original lumped
  ODE model, where "directionality" was never tested in the first place
  (the lumped model's skew-coupling and the PDE's `skew_deg` are different
  objects, as established in §1, and this paper only tests the latter).

---

## Reproduce it

```
python test_skew_reciprocity.py    # Test 1: channel angle alone -- exactly reciprocal
python ais_filter.py               # Test 2: passive periodic lattice -- exactly reciprocal
python active_relay_test.py        # Test 3: naive threshold relay -- not directional, traced why
python refractory_chain_test.py    # Test 4: refractory relay chain -- not directional as built
python feedback_artifact_check.py  # traces the apparent "backward boost" to a feedback artifact
```

Every number in this paper is reproduced by one of these five files. The
result is smaller than the proposal that prompted it: nothing tested here
makes the model flow one way, and the reason each attempt failed is now
specific enough to point at exactly what the next attempt needs to add.
