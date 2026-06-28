# The Complete Unit: Marrying the Interference Soma to the Directional Axon

### Computation and direction in one element — and the seam where they almost didn't join

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. The question this build answers

The v14 paper ended on an explicit open question: it had built a directional
excitable axon (a spike that propagates one way, grounded in Leterrier's
AIS account) but had *not* connected it to the resonator ALU — the
interference-soma logic gates from the original *Resonator Computer*. The
flagged next question was: **can a directional excitable axon be married to
the interference-based soma to make a complete directional computing unit?**

This build does the marriage and tests it. The answer is yes, with one real
seam that had to be designed across carefully, and one honest nuance in the
directionality result.

| claim | status |
|---|---|
| the resonator soma's gate logic survives being read out as a spike | **verified** — all 6 two-input gates (XOR, XNOR, AND, OR, NAND, NOR) reproduce their exact truth tables through the married unit |
| a logical 1 originates a propagating spike; a logical 0 stays silent | **verified** — the spike reaches the axon end exactly when the gate fires |
| the output spike is directional (axon, not dendrite) | **verified with a control** — forward 31 cells, backward 0, vs. uniform-control backward 8 |
| backward = 0 is real attenuation, not a dead region | **verified** — the dendrite region *can* fire from a direct kick, it just doesn't from a back-propagating spike |
| married units compose (A's spike drives B's input) | **verified** — a two-unit chain computes correctly on 24/24 cases |
| the amplitude→kick coupling can corrupt the logic | **true, and designed around** — a clean band-membership comparator (not amplitude-scaled kick) was required; §2 explains why |

---

## 1. The seam: two different kinds of signal

The two halves of the unit speak different languages, and naming this
precisely is the whole engineering problem:

- The **resonator soma** outputs a *steady-state amplitude* `|s|` — a
  static, settled number. The gate's logic is *which band* `|s|` lands in
  (constructive `|s|≈2`, destructive `|s|≈0`, biased variants for AND/OR).
  This is the v11/Resonator-Computer result.
- The **excitable axon** needs a *transient super-threshold kick* to
  originate a spike. Its input is "did something cross threshold *now*," not
  "how loud is the standing wave." This is the v14 result.

A static amplitude and a transient threshold-crossing are not the same kind
of object. The marriage is a comparator that converts one into the other:
soma amplitude band membership → a kick (or no kick) at the axon's
origination site.

---

## 2. The design decision that made it work (and the failure mode it avoids)

The naive coupling — "kick the axon with strength proportional to `|s|`" —
breaks the logic, and it breaks it in a specific way worth recording. Some
gates fire on *high* `|s|` (XNOR fires when inputs agree, `|s|≈2`) and some
on *low* `|s|` (XOR fires when inputs disagree, `|s|≈0`). An amplitude-scaled
kick can only ever handle the high-firing gates; for XOR, the case that
should fire produces `|s|≈0`, which would give *no* kick — exactly backwards.

The fix is a **clean comparator**: the soma decides band membership (the
gate's actual logical output, low-firing or high-firing alike), and band
membership triggers a *fixed-strength* kick, decoupled from the marginal
value of `|s|`. This is why all six gates pass, including the low-firing
ones. The comparator is doing the same job a real neuron's threshold does:
converting a graded somatic signal into an all-or-nothing decision to
initiate a spike, independent of exactly how far over threshold the input
was.

There was also a plain bug found and fixed along the way, recorded honestly
because it shows the test was real: the first run had every gate's *soma
logic* perfect but *every spike* failing to reach the axon end. The cause
was not conceptual — the axon was 80 cells long and the spike (traveling ~1
cell per 18 steps) simply hadn't arrived within the run window. Shortening
the axon to 40 cells and lengthening the window fixed it, and confirmed the
spike genuinely propagates rather than teleporting.

---

## 3. Result 1 — the logic survives the marriage

`married_unit.py` runs all six gates. For each, the unit's output is defined
as *did a spike reach the axon end*, and this is compared to the gate's
truth table:

```
XOR  [PASS]   XNOR [PASS]   AND [PASS]
OR   [PASS]   NAND [PASS]   NOR [PASS]
```

In every row of every gate, the spike reaches the axon end exactly when the
soma's logic says 1. The interference computation is intact when read out as
a directional spike — the axon's strong nonlinearity (an all-or-nothing
regenerative pulse) does not corrupt the soma's graded interference result,
because the comparator cleanly separates the two stages.

---

## 4. Result 2 — the output is genuinely directional

`directional_chain.py` replaces the plain axon with a v14-style gradient
axon (dendrite side hard to excite, axon side normal) and measures spike
spread both ways from the origination site:

```
XNOR (0,0): forward 31 cells, backward 0 cells
XNOR (1,1): forward 31 cells, backward 0 cells
OR   (0,1): forward 31 cells, backward 0 cells
AND  (1,1): forward 31 cells, backward 0 cells

CONTROL (uniform excitability): forward 31, backward 8
```

The spike runs the full length of the axon and does not back-propagate into
the dendrite. The control — identical setup with the excitability gradient
removed — lets the spike spread 8 cells backward (to the boundary),
confirming the asymmetry comes from the gradient, not from geometry or the
origination point.

**The honest nuance**, checked rather than assumed: backward = 0 is *not*
because the dendrite region is inert. A direct super-threshold kick placed
inside the dendrite region *does* fire it (verified). The dendrite is
genuinely excitable; it simply has a high enough threshold that a
back-propagating spike from the AIS doesn't carry enough to invade it. That
is exactly the biological picture — real back-propagating action potentials
exist but are attenuated — not a trivial dead-zone artifact. (A curiosity
noted in passing: an *over*-strong direct kick to the dendrite, 40+, fails
to fire it, because excessive forcing pushes the FitzHugh–Nagumo cell out of
its excitable regime — a known property of the model, not relevant to the
directionality claim but recorded for completeness.)

---

## 5. Result 3 — the units compose

A computing element is only useful if its output drives the next element's
input. `directional_chain.py` tests the minimal chain: unit A computes a
gate, its output spike (1 if it reached the axon, else 0) becomes one input
bit to unit B. Across three choices of gate A, all four input combinations,
and both values of B's other input — 24 cases — the chained computation is
correct **24/24**. One married unit's directional spike can serve as a clean
logical input to the next.

---

## 6. What this completes, and what it doesn't

This closes the loop the whole arc was reaching for: a single element that
**computes** (interference soma — the geometry/parity result from v11),
**sends directionally** (excitable gradient axon — the Leterrier-grounded
result from v14), and **composes** (A drives B). The two mechanisms that
earlier threads kept conflating — geometry-for-computation and
excitability-for-direction — are here joined in one unit while kept
mechanically distinct, with a comparator as the clean interface between
them. That separation is the actual design lesson: they are different
physical jobs, and the unit works *because* the marriage respects the
difference rather than pretending one mechanism does both.

What it does **not** establish: this is a small demonstration (six gates, a
two-unit chain), not a full clocked ALU rebuilt on the married substrate.
The original Resonator Computer composed its interference gates into a
ripple-carry adder; whether the *directional* married units compose that far
— and whether the spike timing introduces clocking constraints the
purely-algebraic gates didn't have — is the next question, not one answered
here. The marriage is proven possible and clean at the single-unit and
two-unit-chain scale; scaling it to arithmetic is future work.

---

## 7. Honest limits

- The axon is a 1-D FitzHugh–Nagumo line (40 cells), the reduced standard
  model, not a biophysical multi-compartment axon. Spike *timing* (the ~18
  steps-per-cell propagation speed) is a model parameter, not calibrated to
  anything biological.
- The comparator (soma band → fixed kick) is an explicit engineered
  interface. It is the honest analogue of a neuron's spike-initiation
  threshold, but it is a designed component, not something that fell out of
  the physics — the paper claims the marriage *works*, not that it is
  *automatic*.
- "Composes" is demonstrated at two units. No claim is made here about
  multi-stage timing, fan-out, or whether a deep chain accumulates spike
  shape/timing drift. Those are real questions the two-unit test does not
  reach.
- The directionality gradient values are chosen to encode the *direction*
  of the real Nav-density asymmetry, not fitted to measured densities — same
  scope limit as v14.

---

## Reproduce it

```
python married_unit.py        # all 6 gates survive the marriage (logic -> spike)
python directional_chain.py   # the spike is directional (with control) AND composes
```

Every number in this paper is reproduced by these two files (which import
the resonator gate definitions and the excitable-axon model from the
adjacent files). The complete directional logic element is real; the seam
between interference-computation and excitable-direction is closable with a
clean comparator; and scaling it to a full arithmetic unit is the honest
next step.
