# Geometry Gives You Parity For Free, And Then You Hit A Wall

### What dendrite length actually buys a resonator neuron — and exactly where it stops buying anything

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. The question, stated precisely

Watching Nils Berglund's angled-cavity wave simulations — a central cavity fed
by satellite cavities sitting at different radii and angles — the question
was: *the length the landing zone is from the soma, does that matter? How
far? How does the axon connect? Nature found something here.*

`resonator_neuron.py`, the unit built in the previous repo (*The Resonator
Computer*), had no notion of length at all. Every dendrite delivered its
phasor to the soma in the same timestep, at the same phase — a wire, not a
cable. This paper adds the one physical thing that was missing, asks what it
buys, and follows the answer all the way to a structural wall and then past
it.

**The two-sentence result, in advance:** dendrite length is a real, free,
no-learning knob — it retunes a unit between XOR and XNOR continuously, and
it does so exactly the way a real damped oscillator would, with a measurable
instability at every quarter-wavelength mismatch. But length alone cannot
produce AND, OR, NAND, or NOR. That requires a second, structurally distinct
ingredient — and the ingredient turns out to be geometrically cheap to grow,
but it is not free in the same sense length is, and a paper has to say so
plainly rather than round it off.

| claim | status |
|---|---|
| dendrite length is a physical phase delay, `φ = (Ω·L/v) mod 2π` | **exact** (definition of a travelling wave on a cable) |
| length alone retunes a fixed unit between XOR and XNOR | **verified in code**, algebra and real damped-oscillator dynamics agree to `1e-2` |
| there is a literal zero-margin instability at every quarter-wavelength mismatch | **verified in code** (continuous sweep, see §2) |
| length (rotation, attenuation, either, both) cannot produce AND/OR/NAND/NOR | **verified in code** as a structural fact, not a sampling gap (see §3–4) |
| an always-on third dendrite supplies the missing gates | **verified in code** (see §6) |
| "geometry replaces weights entirely," "no tuned parameters" | **false, and corrected below** (see §7) — the always-on dendrite's *strength* is a tuned parameter, not a free one |
| this models a real biological dendritic tree | **analogy** — a lumped-ODE unit, not Berglund's actual 2-D wave field; named as the next build |

---

## 1. The mechanism: length is a built-in phase-shift register

A travelling wave at carrier frequency `Ω`, launched at `t = 0`, covers a
cable of length `L` at speed `v`. By the time it reaches the soma it has
accumulated a phase

```
φ = (Ω · L / v)  mod 2π
```

on top of whatever bit-phase (`0` or `π`) it was carrying when it left. The
consequence is immediate and testable: **two dendrites carrying the
identical bit but different lengths arrive at the soma as different
phasors.** The previous unit's XOR mechanism — destructive interference,
`|p_a + p_b| = 0` when the two bits disagree, `= 2` when they agree — is
exact only when the two arrival phases are matched. Detune one length and
you detune the gate.

`delay_dendrite.py` makes this mechanism explicit (`DelayDendrite.carry`)
and checks the resulting unit two ways, holding the same standard as every
prior file in this line: the algebraic fixed point of the soma, and the real
damped, driven oscillator network integrated to steady state. They agree at
every tested length to `1e-2` — the physics computes the algebra, not just
on paper.

---

## 2. Result 1 — length alone retunes XOR ↔ XNOR, with a real wall

Holding one dendrite at zero length and sweeping the other across a full
wavelength, with the *same fixed amplitude band* that was originally tuned
for XOR at length zero:

```
length = 0.000  (φ = 0.000·π)  ->  XOR  region
length = 1.683  (φ = 0.673·π)  ->  XNOR region   <- crossing
length = 3.342  (φ = 1.337·π)  ->  XOR  region   <- crossing back
```

This is not three functions appearing — it is two, with the crossing points
being the interesting part. Exactly at each crossing, the margin between
"fire" and "don't fire" goes to **zero**: the unit becomes the most
noise-fragile configuration physically possible, not a third logical
regime, just deaf. The complementary, stable points — zero mismatch, or
exactly half a wavelength of mismatch — are the only places where the
margin is maximal (amplitude swings the full `0 → 2` range cleanly).

That has a direct, falsifiable biological reading: **if a real dendrite's
logical role depends on length this way, evolution tuning a dendrite to a
multiple of half a carrier wavelength is not decoration — it is the only
stable place to sit.** Sitting near a quarter-wavelength mismatch would be
selected against for the same reason an engineer would never deliberately
build that circuit: it is the point of maximum sensitivity to noise, with
the least signal to show for it.

Verified two ways (`delay_dendrite.py`): the algebraic fixed point and the
real damped-oscillator integration agree at every one of 200 sampled
lengths.

---

## 3. Result 2 — sweeping both lengths never escapes parity

A fair test of "how the axon connects" has to let nature place *both*
dendrite lengths, not just one relative to an arbitrary zero. `both_lengths_swept.py`
places both lengths independently across a full wavelength — 625
combinations — and asks what logical function results at each point, using
the *best possible* band placement for that combination (not a band fixed
in advance, so the test can't be accused of just missing the right
threshold).

**Only `{XOR, XNOR, DEGENERATE}` ever appear.** This is not a resolution or
sampling problem — it is structural, and the reason is exact: the soma sum
`|w_a·p_a + w_b·p_b|` with `|w_a| = |w_b| = 1` is invariant under the
symmetry that exchanges which input is "the larger contributor." A sum of
two equal-magnitude phasors can report only one bit of information —
*agreement vs. disagreement* — no matter where in phase-space you place
them. There is no length placement, on either dendrite, that breaks a tie
into a majority vote.

---

## 4. Result 3 — attenuation doesn't break the symmetry either

A real cable does not only delay and rotate a signal — it also
**attenuates** it: a longer cable means a weaker arrival,
`exp(-α·L)`. This is a second, physically independent consequence of length,
and unlike pure rotation it genuinely *could* break the `|w_a| = |w_b|`
symmetry, since two different lengths now also carry two different
magnitudes. `attenuation_test.py` tests this directly, sweeping the
attenuation coefficient `α` across `[0, 0.5]` (i.e., from no loss to
severe loss over one wavelength of cable) and the length over a full
wavelength at each setting.

**Only XOR and XNOR ever appear, at every attenuation strength tested.**
Attenuation shrinks the radius of the parity decision boundary — the
overall amplitude scale gets smaller — but it does not change the
boundary's topology. Length, whether expressed as phase rotation,
amplitude attenuation, or both together, is **parity-complete and nothing
more.**

---

## 5. The wall, independently cross-checked against earlier, unrelated work

`gates.py`, from the prior repo, was built weeks before this question was
asked, for an unrelated reason (composing a full adder). It already encoded
the fix instinctively, stated in its own comment:

> *"AND/OR/NOT are linearly separable; a biased unit with a one-sided band
> does it."*

And indeed, every AND/OR/NAND/NOR gate built in that file uses an explicit,
nonzero **bias** term (`±2.0`) added to the soma sum — never just weights or
phase. This is an independent confirmation, arrived at from the opposite
direction (composing a working adder, not analyzing a symmetry) of the same
fact derived rigorously above: **escaping the parity family requires a
soma bias — a quantity that pure dendrite geometry (length, phase,
attenuation) cannot supply, because bias is a property of the soma, not the
cable.**

---

## 6. Closing the loop — growing a bias geometrically

The live question, raised directly: can bias itself be geometric — something
nature could "find" the same way it finds a cable length — rather than a
free-floating constant that has to be asserted from outside the system?

`geometric_bias_candidate.py` tests the most physically minimal candidate: a
**third dendrite that is always on** — carrying a constant phasor with no
upstream input of its own (biologically: a leak conductance, a tonic
synapse, or a connection to a constant-rate pacemaker cell, not a sensory
input). Sweeping only that dendrite's coupling strength `w_ref`, with the
two real inputs unchanged:

```
w_ref = -3.0  ->  NOR
w_ref = -2.0  ->  NOR   (zero margin at the threshold itself)
w_ref = -1.0  ->  NAND
w_ref =  0.0  ->  XOR   (no reference dendrite — Result 1's baseline)
w_ref = +1.0  ->  OR    (zero margin at the threshold itself)
w_ref = +2.0  ->  OR
w_ref = +3.0  ->  AND
```

All four missing gates appear, from one new structural element, varying
only its strength. This *does* geometrically realize bias, in the precise
sense that `w_ref · exp(iφ_ref)` is a constant added to the soma sum,
identical in algebraic form to the explicit bias terms in `gates.py`.

---

## 7. The correction that has to be made before this is called a paper

A synthesis written about this result (by a collaborating model, not by the
author of the code) concluded that the system needs "no matrix
multiplications, floating-point weights, or backpropagation" — that
dendrite length and a tonic synapse together fully replace weights, and
that "the physical shape of the cavity *is* the software." That framing
overshoots what was actually shown, in one specific, checkable way, and the
paper has to correct it rather than carry it forward.

Look again at the table in §6. The always-on dendrite does not unlock
AND/OR/NAND/NOR at *any* nonzero strength — it requires specific strengths
(`|w_ref| = 1` lands on the zero-margin wall between XOR-family and
OR/NAND-family; `|w_ref| = 2` lands cleanly on OR/NOR with zero margin at
one corner; `|w_ref| = 3` is needed for clean AND/NAND separation). That is
not "no weights" — that is **a weight**, on the third dendrite, that has to
be tuned to roughly the right magnitude to get a clean gate rather than a
fragile or degenerate one. The mechanism for *supplying* the bias is
geometric (grow a tonically active synapse rather than inject an abstract
constant), but the *value* the bias needs to take is exactly as constrained
as a weight in a standard network — it is not free in the way length's
phase contribution is free.

The accurate claim, which is smaller than "no weights" but is the one that
survived every test run in this repo: **dendrite length supplies one free
parameter (a continuous phase) that costs nothing to tune and selects
within the parity family. A tonic synapse supplies a second, structurally
different parameter (a magnitude) that is not free in the same sense — it
still has to land in roughly the right range, the same way any weight
does — but it is cheap to grow and qualitatively different from a learned
synaptic weight, because it carries no input-dependent information at all.**
That is the honest version of "geometry is computation": geometry hands you
one axis for free and a second axis that is biologically cheap but not
mathematically free. Calling the whole thing weight-free erases the exact
distinction the experiments were run to find.

---

## 8. The actual finding, stated once, plainly

Dendrite length is a real, free, zero-learning knob. It tunes which parity
function a unit detects, and how sharply, continuously, with a measurable
instability wall at every quarter-wavelength mismatch — and it does this
exactly the way a real damped oscillator would, not just on paper. That much
of the original intuition — *length matters, nature found it* — is now a
checked fact.

But length is parity-complete, not Boolean-complete. The rest of Boolean
logic needs a second, structurally distinct ingredient: a soma bias. That
bias can itself be grown geometrically — by adding a dendrite with no input
of its own, always on — but its *strength* still has to be tuned to roughly
the right value, the same constraint any weight carries, just realized in a
cheaper physical substrate.

**The falsifiable biological prediction this produces:** if real dendritic
trees use anything like this mechanism, expect to find **two anatomically
distinct geometric features**, not one — variation in path length (tuning
parity sensitivity continuously, free of any learning signal) and a
separate, identifiable population of tonically active or leak-dominated
synapses (supplying the bias that breaks parity into full Boolean logic).
The two should look different under a microscope, and should respond to
different perturbations, because the math shows they are doing
mathematically different jobs — one is a free phase, the other is a tuned
magnitude.

---

## 9. Honest limits

- This is still the lumped-ODE soma/dendrite model from the prior repo, not
  Berglund's actual 2-D wave field on the angled-cavity geometry. The
  next, harder build — already named in the prior repo's roadmap — is to
  re-derive all three results directly from a PDE on the real geometry,
  with no lumped shortcut, and check whether the parity wall and the
  tonic-bias mechanism survive that translation unchanged.
- `v` (propagation speed) and `Ω` (carrier frequency) are free parameters
  in every test here; nothing in this repo constrains them to biologically
  measured dendritic conduction velocities or any specific oscillation
  band. That is a deliberate scope limit, stated rather than hidden.
- The always-on third dendrite is the *simplest* candidate that realizes a
  geometric bias, not a claim about which specific cellular structure
  biology actually uses for this role. It is offered as a proof that *a*
  geometric bias mechanism exists and is cheap, not as an anatomical
  identification.
- Single-complex-phasor units solving XOR via destructive interference is
  an established result in complex-valued neural network theory; what is
  new in this thread is the resonator framing, the dendrite-length
  mechanism, the measured parity wall, and the geometric-bias closing
  move — not the base fact that a phasor sum can do XOR.

---

## Reproduce it

```
python delay_dendrite.py              # Result 1: length sweep, XOR<->XNOR, the wall
python both_lengths_swept.py           # Result 2: 2D length sweep, structural cap
python attenuation_test.py             # Result 3: attenuation tested as escape route, fails
python geometric_bias_candidate.py     # Section 6: the always-on dendrite unlocks AND/OR/NAND/NOR
python geometry_gives_what_for_free.py # all of the above, run together, with the full ledger printed
```

Every number in this paper is reproduced by one of these five files. Nothing
above is asserted without a script that prints it.
