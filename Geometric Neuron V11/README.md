# Geometry Gives You Parity For Free, And Then You Hit A Wall

### What dendrite length actually buys a resonator neuron — and exactly where it stops buying anything

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. Where this came from

Watching Nils Berglund's angled-cavity wave simulations, the question was:
*the length the landing zone is from the soma — does that matter? How far?
How does the axon connect? Nature found something here.*

`resonator_neuron.py` (the previous repo, `ResonatorNeuron`) had no notion of
length at all. Every dendrite delivered its phasor to the soma in the same
timestep, same phase — a wire, not a cable. This repo adds the one thing
that was missing — **physical dendrite length, and the phase delay and
attenuation it causes** — and asks, precisely: *what does length give a unit
for free, with zero weight learning, and where does that stop working?*

The answer has two parts, and both are load-bearing:

1. **Length alone reconfigures a unit, but only within one family of
   functions** (parity: XOR ↔ XNOR), continuously, with a literal
   zero-margin instability at the crossover points.
2. **Length alone cannot produce AND/OR/NAND/NOR.** That requires a
   structurally different thing — and the repo identifies exactly what
   that thing is, and what it would cost a real neuron to grow it.

---

## 1. The mechanism: length is a built-in phase-shift register

A travelling wave at carrier frequency `Ω`, launched at `t=0`, covers a
cable of length `L` at speed `v`. By the time it reaches the soma it has
picked up a phase

```
φ = (Ω · L / v)  mod 2π
```

on top of whatever bit-phase (`0` or `π`) it was carrying. So **two
dendrites carrying the identical bit but different lengths arrive at the
soma as different phasors.** `resonator_neuron.py`'s XOR trick —
`|p_a + p_b| = 0` when bits disagree, `= 2` when they agree — is exact only
when the two arrival phases match. Detune the lengths and you detune the
gate. `delay_dendrite.py` makes this explicit and checks it against the real
damped-oscillator dynamics, not just the algebra (every test point in
`delay_dendrite_4.py`-equivalent code: physics matches algebra to `1e-2`).

---

## 2. Result 1 — length alone retunes XOR ↔ XNOR, with a real wall

Sweeping one dendrite's length over a full wavelength, holding the other at
zero, **with the same fixed amplitude band that was tuned for XOR at
length 0**:

```
length = 0.000  (φ = 0.000·π)  ->  XOR    region
length = 1.683  (φ = 0.673·π)  ->  XNOR   region   <- crossing
length = 3.342  (φ = 1.337·π)  ->  XOR    region   <- crossing back
```

Exactly at the crossings, the margin between "fire" and "don't fire" goes to
**zero** — the unit becomes maximally noise-fragile, not a third logical
function, just deaf. That zero-margin wall is itself a real, measurable
thing: a unit sitting near a quarter-wavelength mismatch is the worst
possible place for a real (noisy) neuron to sit, and the best possible place
is exactly at `0` or `λ/2` mismatch — which is to say, **nature tuning
dendrite length to a multiple of half a wavelength is not a coincidence
worth shrugging off; it's the only stable place to be.**

Verified two ways in `delay_dendrite.py` / `geometry_gives_what_for_free.py`:
the algebraic fixed point, and the real damped-oscillator integration —
they agree at every tested length.

---

## 3. Result 2 — sweeping BOTH lengths never escapes parity

`both_lengths_swept.py` places both dendrites' lengths independently across
a full wavelength (625 combinations). The result is not a sampling gap —
**only `{XOR, XNOR, DEGENERATE}` ever appear.** This is structural, not
numerical: `|w_a·p_a + w_b·p_b|` with `|w_a| = |w_b|` is invariant under the
symmetry that swaps which input is "the big one." A sum of two
equal-magnitude phasors can only ever report **agreement vs. disagreement.**
No placement of two equal-length-affected dendrites can turn that into a
majority vote (AND, OR).

---

## 4. Result 3 — attenuation doesn't help either

A real cable doesn't just delay a signal — it **attenuates** it (longer
cable, weaker arrival: `exp(-α·L)`). This is a second, independent physical
consequence of length, and it *does* break the `|w_a| = |w_b|` symmetry in
principle. `attenuation_test.py` tests it directly across `α ∈ [0, 0.5]`:
**only XOR/XNOR ever appear.** Attenuation shrinks the radius of the parity
boundary; it doesn't change its topology. Length — rotation or attenuation,
alone or combined — is **parity-complete, not Boolean-complete.**

---

## 5. The wall, named exactly, and independently cross-checked

`gates.py`, in the previous repo, built weeks before this question was
asked, already encoded the fix instinctively, in its own comment:

> *"AND/OR/NOT are linearly separable; a biased unit with a one-sided band
> does it."*

Every AND/OR/NAND/NOR gate in that file uses an explicit, nonzero **bias**
(`±2.0`) — never just weights or phase. This independently confirms today's
derivation from the opposite direction: **escaping the parity family
requires a soma bias, a quantity that pure dendrite geometry (length, phase,
attenuation) cannot supply**, because bias is a property of the *soma*, not
the *cable*.

---

## 6. Closing the loop — can geometry grow its own bias?

The honest next question: is "bias" forever a free-floating constant you
have to assert, or could *it* also come from a structural, geometric fact —
something nature could "find" the same way it finds cable length?

`geometric_bias_candidate.py` tests the most physically minimal candidate:
**a third dendrite that is always on** — a constitutively active synapse
carrying a constant phasor, with no upstream input of its own (biologically:
a leak/tonic conductance, or a synapse onto a pacemaker). Sweeping only its
coupling strength `w_ref`, with the two real inputs unchanged:

```
w_ref = -3.0  ->  NOR
w_ref = -2.0  ->  NOR  (zero margin at the threshold itself)
w_ref = -1.0  ->  NAND
w_ref =  0.0  ->  XOR     (no reference dendrite — back to result 1)
w_ref = +1.0  ->  OR
w_ref = +2.0  ->  OR  (zero margin at the threshold itself)
w_ref = +3.0  ->  AND
```

**All four missing gates appear**, from one new structural element, varying
only its strength. This *does* geometrically realize bias — but the
honest cost has to be stated plainly: it requires a dendrite that fires
**without any upstream signal at all.** That is not "more careful routing of
existing wires," the way length is. It is a categorically different
biological object — a tonic, input-independent drive — and growing one is a
separate achievement from growing a longer cable.

---

## 7. The actual finding, stated once, plainly

Dendrite length is a real, free, zero-learning knob. It tunes which parity
function a unit detects and how sharply, continuously, with a measurable
instability wall at every quarter-wavelength mismatch — and it does this
exactly the way a real damped oscillator would, not just on paper. That much
of Antti's intuition — *length matters, nature found it* — is now a checked
fact, not a feeling.

But length is parity-complete, not Boolean-complete. The rest of Boolean
logic needs a second, structurally distinct ingredient: a bias, which itself
can be grown geometrically too — but only by adding a fundamentally
different kind of dendrite (one with no input, always on), not by routing
more cable on the ones you already have.

If biology is doing anything like this, the prediction is precise enough to
go looking for: **expect two distinct geometric knobs in real dendritic
trees** — path length (tuning parity sensitivity, continuously, for free) and
a separate population of tonically-active or leak-dominated synapses
(supplying the bias that breaks parity into full Boolean logic). Those
should look different under a microscope, because they are doing
mathematically different jobs.

---

## 8. Honest limits

- This is still the lumped-ODE soma/dendrite model, not Berglund's actual
  2-D wave field on an angled-cavity geometry. The next, harder build
  (named in the prior repo's §7.4) is to re-derive these same three results
  directly from a PDE on the real geometry, with no lumped shortcut.
- `v` (propagation speed) and `Ω` (carrier frequency) are free parameters
  here; this file doesn't constrain them to biologically real dendrite
  conduction velocities. That's a deliberate scope limit, not a hidden one.
- The "always-on third dendrite" is the *simplest* geometric bias candidate,
  not necessarily the *only* one or the one biology uses. It is offered as a
  proof that *a* geometric bias mechanism exists, not as a claim about which
  real cellular structure plays that role.

---

## Reproduce it

```
python delay_dendrite.py              # Result 1: length sweep, XOR<->XNOR, the wall
python both_lengths_swept.py           # Result 2: 2D length sweep, structural cap
python attenuation_test.py             # Result 3: attenuation tested as escape route, fails
python geometric_bias_candidate.py     # Section 6: the always-on dendrite unlocks AND/OR/NAND/NOR
python geometry_gives_what_for_free.py # all of the above, run together, with the full ledger printed
```

Every number above is reproduced by these five files. Nothing in this
README is asserted without a script that prints it.
