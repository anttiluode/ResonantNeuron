# No Scheduler: A Continuous-Field Adder, And The Latch The Field Demanded

### Replacing the discrete scheduler with one continuous field — and discovering the capture mechanism that a true field forces you to add

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. What this build does

v17 ran a concurrent ripple adder, but its concurrency was a *discrete
scheduler*: host code checked `axon.v[-3] > 0.5`, flipped an `output_bit`
flag, and wired that bit into the next unit. The routing logic lived in the
Python program, not in the physics. The v17 paper named the honest next
step: replace the scheduler with one continuous field where every unit
evolves under the same update rule and carries couple by real physical
mechanism, not host-code bookkeeping.

This build does that, and it produced a genuine finding I did not anticipate:
**a true continuous field does not work without a capture/latch mechanism,
because a propagating spike is transient** — it passes the output point and
moves on — while a logic signal must be *held* for downstream gates to read.
The scheduler had hidden this by latching `output_bit` in host code. Remove
the scheduler and the need for a physical latch becomes unavoidable. That
latch is the continuous-field analogue of a synapse capturing a spike into a
sustained signal — which is exactly what a real synapse does.

| claim | status |
|---|---|
| a continuous-field full adder (one update rule, no scheduler) computes all 8 rows | **verified, but only after adding a latch** — see below |
| a naive field (no latch) fails specifically when a spike must propagate to a downstream gate | **verified** — the first version failed every row where `a^b=1` had to propagate |
| the failure is because a propagating spike is transient, not held | **verified by trace** — the downstream gate saw its input as 1 for a few ticks then 0 as the spike passed |
| an output latch (capture) fixes it, and is the synapse analogue | **verified** — with latching, all 8 rows correct |
| logic-depth latency survives into the continuous field | **verified** — latencies band at 240/531/901/1352, the same depth structure as v17 |
| it scales to a multi-bit ripple adder | **verified** — 3-bit 8/8, 4-bit 6/6, with stage-sequential carry handoff |
| this is a single simultaneous field over the entire multi-bit device | **false, and stated** — the *full adder* is one no-scheduler field; the multi-bit version chains those field-adders with latched carry handoff (§5) |

---

## 1. The architecture: one field, one rule

`field_adder.py` represents each of a full adder's five gates as a real
excitable line (FitzHugh–Nagumo) living in a shared field. Every line
integrates the *same* update equation every tick. There is no "activate this
unit now" step. A gate's logic is imposed by a local soma comparator at its
input (origination) end: the interference amplitude of its input bits decides
whether to drive that end above threshold. Its output end is read by
downstream gates as physical coupling — the field value there *is* the signal
the next gate senses.

The five gates are wired by fixed physical coupling (output end of A → input
source of B). Crucially, no host code decides *when* B may compute: B is
always integrating, and simply stays subthreshold until real current arrives
from A. That is the whole point of removing the scheduler — activation order
is an emergent consequence of when spikes physically arrive, not a thing the
program imposes.

---

## 2. The failure: a transient spike is not a held signal

The first version, with no latch, failed — and failed *informatively*. It
got exactly the rows where no spike has to propagate (both inputs to the
half-sum agreeing, `a^b=0`) and failed every row where the half-sum `a^b=1`
had to travel to a downstream gate.

`diag_coupling.py` traced one failing case (`0+1+0`, expecting sum 1). The
trace showed `XOR(a,b)` *did* fire and its spike *did* reach the output end —
at tick ~480 the output read `+1.577` (bit 1), and the downstream `XOR_sum`
finally saw its input as `[0,1]`. But by tick 560 the output had fallen to
`−1.770` (bit 0): **the spike had passed the output cell and moved on.** The
downstream gate saw its input flicker 1 then 0 — an unstable, transient
input it could never cleanly compute on.

This is a real property of excitable propagation, not a bug in the logic: a
travelling action potential is a moving pulse. At any fixed point it is a
brief transient. The scheduler version never hit this because host code
latched `output_bit = 1` permanently the instant the spike was detected. In
a true field, nothing does that for free.

---

## 3. The fix: capture, which is what a synapse is

The resolution is to give each gate's output end a **latch**: once a spike
has *ever* reached it, the output bit stays 1. This converts the transient
travelling spike into a stable, held logic level that downstream gates can
read for as long as they need.

This is not an arbitrary patch — it is the continuous-field analogue of the
exact mechanism biology uses at this junction. A synapse does not pass the
membrane voltage through; it *captures* the arriving spike (neurotransmitter
release, receptor binding, a postsynaptic potential that persists far longer
than the presynaptic spike) and converts it into a sustained downstream
signal. The latch is the minimal model of that capture. The finding is that
the field *demands* it: without a capture mechanism, a spike-propagation
computer cannot hold its intermediate results long enough to compute with
them. The scheduler abstraction hid a real requirement of the physics.

With the latch, all eight rows are correct:

```
a b cin | sum cout | ticks
0 0  0  |  0   0   |  240
0 0  1  |  1   0   |  531
0 1  0  |  1   0   |  901
0 1  1  |  0   1   | 1352
1 1  1  |  1   1   |  901
   ... (all 8 rows OK)
```

And the latency bands (240 / 531 / 901 / 1352) reproduce the logic-depth
structure from v17 — the continuous field has the same O(depth) timing,
because the spikes still travel at finite speed.

---

## 4. Watching it compute

`field_adder_viz.py` renders the whole field as a live heatmap (saved as
`field_adder.gif` and `field_adder_final.png`): five excitable lines, bright
pulses propagating down each as the computation flows. `field_timeline_viz.py`
gives the complementary temporal view (`field_timeline.png`): each gate's
output-end potential over time, stacked, so the dependency cascade is
directly visible.

For `0 + 1 + 1` (a carry case), the timeline shows the computation marching
through the dependency graph in time:

```
AND(a,b)        : never fires        (a&b = 0, correct)
XOR(a,b)        : spike at t=450     (a^b = 1)
AND(cin,a^b)    : spike at t=901     (waited for XOR(a,b) to latch, then fired)
OR(c1,c2)=CARRY : spike at t=1352    (waited for AND(cin,a^b), produced carry)
```

Each gate fires ~450 ticks after the one it depends on — the spike-propagation
latency made visible as a temporal cascade. This is the clearest single
picture in the whole arc of "the field computing": you watch the carry get
built, one excitable spike triggering the next, with no scheduler anywhere.

---

## 5. Scaling, and an honest scope line

`field_ripple.py` chains continuous-field full adders into a multi-bit adder:
3-bit 8/8 and 4-bit 6/6 random additions correct, worst-case latency growing
with bit width (901 / 2253 / 3605 ticks for 1/2/3 bits).

The honest scope line, stated plainly because it matters: the *single full
adder* is a true no-scheduler continuous field — its five gates are one
field under one rule, and the result emerges from physical coupling. The
*multi-bit ripple adder* chains these field-adders, handing the latched carry
from one stage's field to the next stage's field. So the multi-bit version is
"continuous fields chained by latched carry," not "one simultaneous field
over the entire word." Making the whole N-bit device a single simultaneous
field (all stages' lines co-evolving in one array, carries coupling
continuously across stage boundaries) is the next heavier step. This build
establishes the continuous-field unit and its required latch, and chains it;
it does not yet melt all stages into one monolithic field.

---

## 6. What this resolves

The arc's timing/physics thread is now as deep as it has gone:

- v15: married unit (soma computes + axon sends directionally).
- v16: scales to a full adder; per-stage latency = logic depth.
- v17: concurrent multi-bit ripple, latency linear in word width (scheduler).
- v18 (this): the scheduler removed — a continuous field — which forces a
  capture/latch mechanism (the synapse analogue) that the scheduler had
  hidden, and which lets the computation emerge from physical coupling alone.

The deflationary-but-real lesson: removing the last bit of host-code
bookkeeping exposed a genuine physical requirement (you must capture a
transient spike to compute with it) that every earlier version had quietly
assumed. That requirement is not a flaw in the model — it is biology's actual
solution (the synapse), arrived at here by necessity rather than by analogy.

---

## 7. Honest limits

- The continuous field is still a 1-D FitzHugh–Nagumo line per gate, and the
  soma comparator (interference amplitude → drive) is an engineered local
  transform, not something derived from a deeper field equation. "No
  scheduler" means no host-code activation ordering; it does not mean every
  element is derived from first principles.
- The latch is a hard capture (output bit, once 1, stays 1 for the
  computation). A more biophysical version would be a decaying postsynaptic
  potential with its own time constant; the hard latch is the minimal model
  that makes the point.
- The multi-bit adder chains field-adders with latched carry handoff (§5);
  it is not one simultaneous field over the whole word. That monolithic
  version is named as the next step, not claimed here.
- Correctness sweeps are modest (8 rows exhaustively for the full adder; 8
  and 6 random additions for 3- and 4-bit) because continuous-field
  simulation is slow. The full-adder truth table is exhaustive and exact;
  the multi-bit sweeps are smaller and not claimed otherwise.
- Latency figures are specific to the axon length and FHN speed used; they
  are a structure result (logic-depth banding, linear-in-N worst case), not
  calibrated timings.

---

## Reproduce it

```
python field_adder.py            # the continuous-field full adder, all 8 rows
python field_adder_viz.py 0 1 1  # heatmap animation (field_adder.gif) + final PNG
python field_timeline_viz.py 0 1 1  # temporal cascade (field_timeline.png)
python field_ripple.py           # multi-bit, chained continuous-field adders
```

The headline: with the scheduler gone, the adder computes as a real
continuous field — but only once given a capture/latch, the synapse analogue
the field turned out to demand. The visualizations show the carry being built
in time, one excitable spike triggering the next, with no scheduler anywhere.
