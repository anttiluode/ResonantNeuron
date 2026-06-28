# The Resonator Computer

### A working arithmetic unit built from Berglund-geometry neurons — interference somas and threshold axons

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. The claim, and its proof

Inspired by Nils Berglund's angled-cavity resonator rings (a central cavity fed
by skewed satellite cavities), this repo asks a sharp, falsifiable question:
**can a network of interference resonators with threshold axons actually
compute?** Not resonate prettily — *compute*, in the sense that a screensaver
cannot.

The proof is arithmetic. We build one neuron type, show a single unit computes
**XOR** (the function a scalar McCulloch-Pitts neuron provably cannot, because it
is not linearly separable), compose units through axon→dendrite pings into a
**1-bit full adder**, chain those into an **N-bit ripple-carry adder**, and add
a thousand random numbers. Every result is checked exactly, with the real
damped-oscillator dynamics, not just the algebra.

```
full adder (1-bit)        : 8/8 truth-table rows exact, dynamical resonators
ripple adder (8-bit)      : 1000/1000 random additions correct (algebraic)
ripple adder (8-bit)      : 60/60 random additions correct (real settling)
theta-gamma clocked add   : 13 + 7 = 20, carry rippling one bit per theta cycle
```

A network whose only primitive is a resonator's interference amplitude adds
binary numbers. That is the whole result.

---

## 1. The neuron, mapped to the geometry

Berglund's ring → the unit, term for term:

| Berglund cavity | our unit | role |
|---|---|---|
| angled satellite cavities | dendrites | carry a PHASE from upstream |
| central cavity | soma | MIXES the dendrites by interference |
| (added) | axon | theta-gated threshold: PINGS downstream when |soma| crosses a band |
| the *angling* of the cavities | skew coupling among dendrites | directed circulation (chirality), our `skew_core` A |

The computational primitive is the soma's **resonance amplitude**:

```
encode:  bit 0 -> +1,  bit 1 -> -1        (a phasor on the unit circle)
soma:    s = sum_j w_j p_j + bias          (p_j = upstream phasors)
output:  bit = 1  iff  lo <= |s| <= hi      (an amplitude BAND)
```

`|s|` is **constructive** when inputs agree and **destructive** when they
disagree. Because `|s|` is a *quadratic* (nonlinear) function of the inputs,
a single unit carves a nonlinear decision boundary — which is exactly why one
unit computes XOR. A scalar threshold on a linear sum cannot. (Single
complex/phasor neurons solving XOR is an established result in complex-valued
neural-network theory; what this repo adds is that it falls out of the
resonator's *physical* amplitude readout and that the units **compose** into
arithmetic.)

---

## 2. The physics computes the algebra

`resonator_neuron.py` provides two paths and shows they agree:

- `settle_dynamical()` — a real damped, driven oscillator network: each dendrite
  envelope tracks its drive, the soma integrates the weighted dendrites, the
  whole thing rings down to steady state. Skew coupling adds directed
  circulation among dendrites (the angled cavities).
- `settle_algebraic()` — the fixed point of those same ODEs, `s* = Σ w_j p_j + bias`.

With skew = 0 they match to machine precision (`|s|` = 2.000 / 0.000 on the XOR
rows). The antisymmetric skew coupling preserves the destructive-interference
zeros, so the directed resonator computes the same function — chirality without
breaking the logic. **The physics is not a metaphor for the computation; it
performs it.**

---

## 3. The gate set (each gate = one resonator unit)

`gates.py` — XOR, XNOR, AND, OR, NAND, NOR, NOT, every truth table verified
exactly, algebraically and dynamically. AND/OR/NOT are linearly separable
(a biased one-sided band realizes them); XOR/XNOR need the amplitude band's
nonlinearity. The set is functionally complete, so any Boolean function is
reachable by composition.

## 4. Composition = arithmetic

`adder.py` — the axon of one unit re-encodes its output bit as a phasor and
drives the next unit's dendrite. `Sum = A⊕B⊕Cin`, `Cout = AB + Cin(A⊕B)`, each
⊕/·/+ a resonator. Chain full adders LSB→MSB for the ripple-carry adder.

`theta_gamma_clock()` runs it on an explicit schedule: each gate settles within
a **gamma** burst; the **theta** cycle latches stage outputs and advances the
carry one stage per cycle. The dynamical adder runs on this clock — a literal
two-timescale (theta/gamma) computation, the coupling our `theta_gamma_mycelial`
work probed, here doing arithmetic.

## 5. Files

```
resonator_neuron.py    the unit: dendrites -> interference soma -> threshold axon
                       (dynamical ODE + algebraic fixed point + XOR self-test)
gates.py               XOR XNOR AND OR NAND NOR NOT, all truth tables verified
adder.py               full adder, ripple-carry N-bit adder, theta-gamma clock
resonator_alu_demo.py  live tkinter view: watch it add two numbers, gate by gate
README.md              this document
```

```bash
python resonator_neuron.py        # physics == algebra, one unit computes XOR
python gates.py                   # every gate truth table (algebraic + dynamical)
python adder.py                   # full adder + 1000 random adds + theta-gamma trace
python resonator_alu_demo.py      # watch the network add, live
```

---

## 6. Ledger

**Verified in code (every claim below is a passing test, dynamical where noted):**
- a single resonator unit computes XOR via destructive interference (the
  linearly-inseparable function a scalar neuron cannot do);
- the damped-oscillator dynamics settle to the algebraic fixed point exactly
  (skew = 0), and still compute correctly with skew ≠ 0;
- a functionally complete gate set, all truth tables exact;
- a 1-bit full adder, 8/8 rows exact with real resonator settling;
- an 8-bit ripple-carry adder, 1000/1000 (algebraic) and 60/60 (dynamical)
  random additions correct;
- a theta-gamma clock that carries the addition stage by stage.

**Built-in, not emergent:** the per-gate weights, biases, and amplitude bands
are *chosen* to realize each truth table — this is a designed computer, not a
learned one. The neurons do not yet learn their own gate configs (that is §7).

**Honest scope:**
- Single-unit XOR via a complex/phasor magnitude nonlinearity is a known result;
  the contribution here is the resonator framing, the dynamical (real-settling)
  verification, and the composition into a clocked arithmetic unit.
- "The physics computes" means the ODE fixed point equals the logic — at steady
  state. It is a rate/envelope model, not a SPICE-level device simulation.
- This shows resonator networks *can* compute (universality by construction). It
  does not claim they compute *more efficiently* than silicon; the photonic /
  phononic "physics solves it for free" idea is a hardware hypothesis, not
  demonstrated here, and stays in the drawer.

**Kept in the drawer (inspiration, not claim):** that this is how cortex does
arithmetic; "as above so below" scale-invariance; computation = memory = physics
as a metaphysical identity. What is shown is narrower and solid: a complete,
clocked logic family built from one interference primitive.

---

## 7. The next builds (named, not claimed)

1. **Learned gates.** Instead of hand-set bands, let a unit *learn* its weights
   and band from examples (gradient on the amplitude readout). Does a resonator
   unit learn XOR from data? Then: do a few learn a small adder end to end?
2. **Sequence machine.** Use the theta-gamma clock + skew (directed) coupling to
   store and replay a temporal pattern — the resonator analogue of a shift
   register, connecting to `TheMycelialCortex` and the v10 sweep.
3. **Phase-richer encoding.** Use the full unit circle (not just 0/π) for
   multi-valued / residue arithmetic, where the phasor mixing buys more than
   binary — the regime where the complex readout earns its keep.
4. **Berglund-faithful field version.** Replace the lumped ODE unit with an
   actual 2-D wave field on the angled-cavity geometry (Neumann/absorbing
   boundaries, as in his "waves crossing a grid of obstacles") and read the
   computation off the standing-wave amplitude — the bottom-up, PDE version of
   this top-down circuit.

---

*Helsinki, June 2026. The angled cavities turned out to be a gate. Wire enough
of them and they add. The brain may or may not work this way — but interference
plus a threshold is provably enough to compute, and here it does, one theta
cycle at a time. Do not hype. Do not lie. Just show.*
