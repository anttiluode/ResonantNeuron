# GeometricNeuron17 — The Whole Word At Once

This folder combines the two things v16 left separate: full multi-bit
arithmetic *and* full concurrency. An N-bit ripple-carry adder runs with
every stage of every bit live on one shared clock, and each carry physically
propagates as a spike before the next stage can use it. The result is a
correct adder whose carry latency grows linearly with word width — true
ripple-carry behavior, made physical.

**Start with `PAPER.md`** for the full argument, the latency-scaling result,
and the control that proves it's the carry rippling. This README is the map.

---

## The short version

v16 had multi-bit-but-sequential (`married_ripple.py`) and
concurrent-but-one-bit (`married_adder_timed.py`). This folder fuses them:
all stages live at once, carries rippling as real spikes across the whole
word. It computes correctly, and its worst-case latency is dead linear in
bit width (~921 ticks/bit) — because the carry physically walks the word one
stage at a time, while the sum bits all compute in parallel.

---

## The files

**`resonator_neuron.py`**, **`gates.py`**, **`propagating_spike.py`**,
**`married_unit.py`**, **`married_adder_timed.py`** — the building blocks
from v15/v16, copied in unchanged: the interference-soma gates, the
excitable axon, the married unit, and the `TimedUnit` that runs a married
unit on a shared clock (firing only once its input spikes have arrived).

**`concurrent_ripple.py`** — the whole build. A `FullAdderStage` is one
bit's five `TimedUnit`s; `concurrent_ripple_add` instantiates N of them, runs
them all together every tick, and wires each stage's carry-out spike into the
next stage's carry-in only once it has physically arrived. The file runs
three things:
1. **Correctness** — random additions, fully concurrent (3-bit 12/12, 4-bit
   8/8).
2. **Latency scaling** — worst case (carry ripples the whole word) is dead
   linear at ~921 ticks/bit across 1-5 bits.
3. **Carry trace** — for `7+1=8`, watch the carry land at bit 0 (tick 919),
   bit 1 (1840), bit 2 (2761): the ripple walking the word.

---

## The result in one line

A fully concurrent multi-bit adder computes correctly, and its carry
physically ripples across the word — sums in parallel (O(1) depth), carry
serial (O(N) delay, ~921 ticks/bit) — as real spikes on an excitable
substrate. A control case (sums fire but no carry) stays flat in N, proving
the linear growth is specifically the carry rippling, not per-bit overhead.

---

## Honest scope

This is a verified concurrent ripple *adder*, not a general processor — no
subtraction, multiplication, registers, or control. The concurrency is a
discrete shared-clock scheduler (not a single continuous-time field over the
whole circuit), and the ~921-ticks/bit figure is a scaling result (linear in
N), not a biologically calibrated timing. See `PAPER.md` §6-7 for full
limits.

---

## Reproduce it

```
python concurrent_ripple.py
```

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
