# GeometricNeuron15 — The Complete Unit

This folder marries the two halves the whole project had kept separate: the
**interference soma** (the resonator logic gates, which compute) and the
**directional excitable axon** (the v14 spike, which sends one way). The
result is a single element that computes a gate, originates a directional
spike carrying the result, and chains into the next unit.

**Start with `PAPER.md`** for the full argument, the seam that had to be
designed across, and every number with its control. This README is the map.

---

## The short version

v14 built a directional axon but left it disconnected from the resonator
ALU, flagging "can they be married?" as the next question. They can. The
catch is that the soma outputs a *static amplitude* and the axon needs a
*transient threshold kick* — two different kinds of signal — so the marriage
needs a clean comparator (band membership → fixed-strength kick) between
them. With that, all six logic gates survive, the output spike is
directional, and units compose.

---

## The files, in run order

**`resonator_neuron.py`**, **`gates.py`** — the interference-soma logic
gates from the original Resonator Computer, copied in unchanged. `gates.py`
defines XOR/XNOR/AND/OR/NAND/NOR as resonator units (weights, bias, and the
amplitude band each one fires in).

**`propagating_spike.py`** — the excitable-axon model from v14 (FitzHugh–
Nagumo line), copied in. The directional spike substrate.

**`married_unit.py`** — the marriage. A `MarriedUnit` runs the soma gate,
and if the soma's amplitude lands in the firing band, a clean fixed-strength
kick originates a spike on the excitable axon. The unit's output is "did the
spike reach the axon end." Tests all six gates: every truth table is
reproduced exactly. This file also documents (in comments) the failure mode
that an amplitude-scaled kick would cause, and why the band-membership
comparator avoids it.

**`directional_chain.py`** — the two properties `married_unit.py` doesn't
check: (1) is the output spike *directional* — does it go to the axon and
not back into the dendrite? Tested with a v14-style excitability gradient
and a uniform-axon control. (2) does it *compose* — can unit A's spike drive
unit B's input? Tested on a two-unit chain, 24/24 correct.

---

## The honest boundary

This is a single-unit and two-unit-chain demonstration, not a full clocked
ALU rebuilt on the married substrate. The original Resonator Computer
composed its gates into a ripple-carry adder; whether the *directional*
married units scale that far — and whether spike timing adds clocking
constraints the algebraic gates didn't have — is the next question, not one
this folder answers. The marriage is proven clean at small scale; scaling to
arithmetic is future work.

The directionality result also carries a checked nuance: backward spread is
0 not because the dendrite is inert (a direct kick *can* fire it) but because
its higher threshold attenuates the back-propagating spike — the real
biological picture (attenuated back-propagation), not a dead-zone artifact.

---

## Reproduce it

```
python married_unit.py
python directional_chain.py
```

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
