# GeometricNeuron16 — Arithmetic From Directional Units

This folder scales the married soma+axon unit (v15) up to arithmetic: a full
adder and a multi-bit ripple-carry adder built entirely from directional
units, where every internal wire is a real propagating spike. Then it runs
the adder *concurrently on a shared clock* and finds the latency that
spike-propagation imposes — which turns out to equal the circuit's logic
depth.

**Start with `PAPER.md`** for the full argument and the timing finding.
This README is the map.

---

## The short version

v15 proved the married directional unit computes one gate and chains
two-deep, and flagged "scale to arithmetic" as next. It scales: a full adder
of five married units gets all 8 rows, and a ripple adder gets 60/60 random
additions — every bit carried by a spike, not algebra. The new result is
what concurrency reveals: the adder still computes, but with a real latency
(~460 timesteps per serial spike-hop) that the instant algebraic version
never had. That latency is the logic depth made physical, and it's the
structural reason a spike computer needs a clock.

---

## The files, in run order

**`resonator_neuron.py`**, **`gates.py`**, **`propagating_spike.py`**,
**`married_unit.py`** — the building blocks from v15, copied in unchanged:
the interference-soma gates, the excitable axon, and the married unit that
joins them (soma computes, axon sends a directional spike).

**`married_adder.py`** — a full adder built from five married units. Every
internal signal (the half-sum, both carries) is the spike output of one unit
consumed as the input bit of the next. Tests all 8 rows: all correct. This
proves the directional mechanism carries arithmetic, not just single-gate
logic.

**`married_ripple.py`** — chains married full adders into an N-bit
ripple-carry adder and verifies on random additions (4-bit: 40/40, 6-bit:
20/20). The carry rippling between stages is itself a chain of spikes.

**`married_adder_timed.py`** — the timing test, and the real finding. Runs
all five units of a full adder *concurrently* on a shared step-clock;
downstream units wait for upstream spikes to physically arrive before they
can fire. It still computes all 8 rows — but the per-row latency is
quantized into bands (2, 460, 919, 1379 ticks) that correspond exactly to
how many serial spike-hops the answer needs. Logic depth made physical.

---

## The finding in one line

Directional units do arithmetic correctly, and the price of directionality
is a latency equal to the circuit's logic depth (~460 ticks per spike-hop) —
which is precisely why a spike-based computer needs a clock to stage
multi-bit computation, exactly the role the original adder's theta-gamma
clock played, now measured rather than assumed.

---

## Honest scope

This is a verified full adder plus a small ripple adder, not a complete ALU
(no subtraction, multiplication, registers, or control). The concurrent
timing test is run on the single full adder; combining full concurrency with
multi-bit carry-ripple across all stages is the natural next build, not done
here. See `PAPER.md` §6 for the complete limits.

---

## Reproduce it

```
python married_adder.py
python married_ripple.py
python married_adder_timed.py
```

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
