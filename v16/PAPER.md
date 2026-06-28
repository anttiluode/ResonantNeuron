# Arithmetic From Directional Units, And The Latency That Comes With It

### Scaling the married soma+axon unit to a full adder — and watching logic depth become physical propagation delay

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. What this build does

v15 married the interference soma (computation) to the directional excitable
axon (one-way spike) into one complete unit, and showed it computed all six
gates, sent directionally, and chained two-deep. It ended on a scoped
limit: *this is not a full clocked ALU rebuilt on the married substrate;
scaling to arithmetic is future work.* This build does that scaling, and
the result has two parts — one expected, one that is the actual finding.

**Expected:** a full adder and a multi-bit ripple-carry adder built entirely
from married directional units compute correctly. Arithmetic survives being
carried by physical spikes.

**The actual finding:** when the units run *concurrently on a shared clock*
(rather than each blocking to completion before the next starts), the adder
still computes correctly — but it now has a real, measurable **latency**,
and that latency is exactly the logic depth of the circuit made physical:
~460 timesteps per serial spike-hop. The algebraic adder had zero latency.
This one has a structural delay proportional to how deep the carry has to
ripple. That delay is the physical price of directionality, and it is the
concrete reason a spike-based computer needs a clock to stage multi-bit
arithmetic.

| claim | status |
|---|---|
| a full adder of married units computes all 8 rows via directional spikes | **verified** — every sum/carry bit is a spike that reached an axon end |
| it scales to a multi-bit ripple-carry adder | **verified** — 60/60 random additions correct (4-bit and 6-bit) |
| it still computes when units run concurrently on a shared clock | **verified** — all 8 full-adder rows correct under concurrency |
| concurrency reveals a real propagation latency the algebraic version lacked | **verified and quantified** — ~460 ticks per serial spike-hop, latency bands at 0/1/2/3 hops |
| that latency equals the circuit's logic depth | **verified** — latency tracks critical-path spike-hop count, row by row |
| this is a complete clocked ALU ready to replace silicon | **false, and not claimed** — it is a verified full adder + small ripple adder; §6 states what's still missing |

---

## 1. Logical composition: arithmetic survives the spike readout

`married_adder.py` builds a full adder from five married units —
`XOR(a,b)`, `XOR(that, cin)`, `AND(a,b)`, `AND(cin, a^b)`, `OR(.,.)` — where
every internal wire is the output of a married unit: a spike that reached
the end of an excitable axon, consumed as the input bit of the next unit.
All eight rows are correct:

```
a b cin | sum cout | expected
0 0  0  |  0   0   | sum=0 cout=0   OK
0 0  1  |  1   0   | sum=1 cout=0   OK
0 1  1  |  0   1   | sum=0 cout=1   OK
1 1  1  |  1   1   | sum=1 cout=1   OK
   ... (all 8 rows pass)
```

`married_ripple.py` chains these into an N-bit ripple-carry adder, where the
carry rippling between stages is itself the output spike of a stage's OR
unit. On random additions: **4-bit 40/40 correct, 6-bit 20/20 correct.**
Arithmetic is carried entirely by directional spikes, not algebra.

(The bit widths and trial counts are smaller than the original algebraic
adder's 1000-addition sweep, deliberately: each bit here runs full
excitable-axon integrations, which are slow. 60/60 is enough to prove the
composition is sound; it is not claimed to be an exhaustive sweep.)

---

## 2. The timing question, and why it is the real test

In §1, each unit's `.run()` blocks to completion before the next unit
starts. That proves *logical* composition but hides *timing* — it is still
effectively sequential. A real directional device runs its units
concurrently, and a downstream gate cannot originate its spike until its
upstream inputs' spikes have physically arrived. The honest test of whether
this is a physical directional computer (rather than a sequential simulation
wearing spikes) is to run it concurrently and see what happens.

`married_adder_timed.py` does this: all five units advance one shared
timestep together. Each unit waits in a `WAIT` state until its input bits
are available, then transitions `KICKING → PROPAGATING → DONE`, and its
output bit becomes available only once its spike physically reaches the axon
end. Downstream units' inputs are wired in as upstream outputs arrive.

---

## 3. The finding: logic depth becomes physical latency

The concurrent full adder computes all 8 rows correctly — and the per-row
latency is the interesting part:

```
a b cin | sum cout | ticks | critical-path spike-hops
0 0  0  |  0   0   |     2 | 0  (every gate outputs 0, no spike needed)
0 0  1  |  1   0   |   460 | 1  (XOR_sum must fire for sum=1)
0 1  0  |  1   0   |   919 | 2
1 1  0  |  0   1   |   919 | 2
0 1  1  |  0   1   |  1379 | 3  (carry: XOR_ab -> AND_cin -> OR_cout)
```

The latencies are quantized into clean bands — 2, 460, 919, 1379 — spaced
~460 ticks apart. Each band is one more serial spike-hop on the critical
path. The `0 0 0` case finishes in 2 ticks because every gate's logical
output is 0, so no spike ever has to propagate. The deepest case must send a
carry serially through three units, and pays three axon-lengths of
propagation delay to do it.

This was checked rather than asserted: `diag_latency.py` traces, row by row,
which units fire and in what dependency order, and confirms the latency
tracks the critical-path depth. (One row, `0 0 1`, initially looked like it
broke the pattern — predicted depth 0, measured 460. The measurement was
right and the hand-prediction was incomplete: with `cin=1`, the sum bit
requires `XOR_sum` to fire, which is one real spike-hop. The data corrected
the reasoning, not the reverse — recorded here because that is how the check
is supposed to work.)

---

## 4. What the latency means

The algebraic adder (the original Resonator Computer) had zero latency: a
gate's output was instantly available as the next gate's input. The married
directional adder cannot do that, because its output is a physical spike
that takes ~460 timesteps to traverse one unit's axon. Multi-bit addition,
where the carry must ripple stage to stage, therefore accumulates a delay
proportional to the number of bits times the per-stage depth.

This is not a defect — it is the physical reason real neural computation is
*clocked*. A brain cannot rely on a carry being instantly everywhere; it has
to wait for signals to propagate, which is precisely why staged computation
rides on rhythms (theta gating the slow stage-advance, gamma the fast local
settling). The original adder's `theta_gamma_clock` *modelled* that timing
by assumption; this build *measures* it emerging from the physics: the
clock period a real version would need is set by the spike-propagation
latency, ~460 ticks per hop here. The directional mechanism makes the need
for a clock not a modelling choice but a structural necessity.

---

## 5. The arc this completes

Across v11 → v16, the project went from "geometry computes parity" to a
complete, directional, composable arithmetic unit, with each step's claim
checked and each overclaim corrected:

- v11: dendrite length tunes parity (XOR/XNOR), but not AND/OR — needs bias.
- v12: that parity result survives the real wave PDE, though the clean
  quarter-wavelength wall does not (channels resonate).
- v13: no passive geometry makes signals flow one way (four failed attempts).
- v14: directionality requires an active excitable origination site with
  inactivation (grounded in Leterrier's AIS account).
- v15: the interference soma and excitable axon marry into one unit that
  computes, sends directionally, and chains.
- v16 (this): that unit scales to arithmetic, and concurrency reveals the
  latency that makes a clock structurally necessary.

The through-line: computation and direction are *different physical
mechanisms* (geometry/interference vs. excitable dynamics), they can be
joined in one unit, and joining them imposes a timing cost that the
pure-logic version never had to pay.

---

## 6. Honest limits

- This is a verified full adder plus a small (4- and 6-bit) ripple adder,
  not a complete ALU. No subtraction, no multiplication, no registers, no
  control logic. "Scales to arithmetic" means "addition, demonstrated and
  verified," not "general-purpose computer."
- The concurrent timing model (`TimedUnit`) is a discrete shared-clock
  scheduler, a reasonable but simplified model of true physical concurrency.
  It captures the essential fact (downstream waits for upstream spike
  arrival) but is not a continuous-time multi-unit field simulation.
- The ~460-ticks-per-hop latency is specific to the axon length (30 cells)
  and FitzHugh–Nagumo propagation speed used here; it is a structural
  *existence* result (there is a latency, and it equals logic depth), not a
  calibrated biological timing number.
- The ripple adder in §1 runs sequentially (blocking units), not on the
  concurrent clock of §2. Combining the two — a multi-bit adder run fully
  concurrently with measured carry-ripple latency across all stages — is the
  natural next build, not done here. The single full adder is what was run
  concurrently.
- Everything inherits the upstream scope limits: the soma is the lumped
  resonator model, the axon is 1-D FitzHugh–Nagumo, and the comparator
  between them is an engineered interface, not something that fell out of
  the physics.

---

## Reproduce it

```
python married_adder.py         # full adder, all 8 rows, via directional spikes
python married_ripple.py        # 4-bit and 6-bit ripple adder, random additions
python married_adder_timed.py   # concurrent clocked adder: correct + the latency finding
```

Every number in this paper is reproduced by these three files (which import
the married unit, the resonator gates, and the excitable axon from the
adjacent files). The headline: directional units do arithmetic, and the
price of directionality is a latency equal to the circuit's logic depth —
which is exactly why a spike computer needs a clock.
