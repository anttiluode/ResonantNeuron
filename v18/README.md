# GeometricNeuron18 — No Scheduler: The Continuous Field

This folder replaces v17's discrete scheduler with a **true continuous
field**: every gate of the adder is a real excitable line evolving under one
update rule, and carries couple by physical mechanism, not host-code
bookkeeping. The build produced an unanticipated finding — a true field
**demands a capture/latch** (the synapse analogue) that the scheduler had
hidden — and it includes **live visualizations** of the field computing.

**Start with `PAPER.md`** for the full argument and the latch finding. This
README is the map. **Look at `field_timeline.png` first** — it's the clearest
single picture of the field computing.

---

## The short version

v17's "concurrency" was really host code checking a flag and routing bits. To
make it a real field, everything had to evolve under one rule with carries
coupling physically. Doing that broke the adder — because a propagating spike
is *transient* (it passes the output point and moves on), but a logic signal
must be *held*. The fix is a capture/latch at each gate's output, which is
exactly what a biological synapse does. With it, the field computes correctly,
and you can watch the carry get built spike by spike.

---

## The files

**`resonator_neuron.py`**, **`gates.py`**, **`propagating_spike.py`** — the
building blocks from earlier folders (interference soma gates, excitable
axon), copied in.

**`field_adder.py`** — the core build. Each gate is a `FieldUnit` (a real
excitable line); five of them wired into a `FieldFullAdder` that evolves as
one field with no scheduler. Computes all 8 rows correctly. The code comments
document the latch (capture) mechanism the field demanded and why it's the
synapse analogue.

**`field_adder_viz.py`** — the live heatmap animation. Renders all five
gate-lines as the field evolves; bright pulses are propagating spikes. Saves
`field_adder.gif` (the animation) and `field_adder_final.png` (final frame).
Run with `python field_adder_viz.py a b cin` to pick inputs.

**`field_timeline_viz.py`** — the temporal cascade view (the clearest one).
Each gate's output-end potential over time, stacked, so you watch the
computation flow through the dependency graph: input gates fire, their spikes
trigger middle gates, which trigger the carry. Saves `field_timeline.png`.

**`field_ripple.py`** — scales to a multi-bit ripple adder by chaining
continuous-field full adders with latched carry handoff. 3-bit 8/8, 4-bit
6/6 correct.

---

## Included artifacts

- **`field_timeline.png`** — temporal cascade for `0+1+1`: XOR(a,b) fires at
  t=450, AND(cin,a^b) at t=901 (waited for it), CARRY at t=1352 (waited for
  that). The carry built in time, spike by spike.
- **`field_adder.gif`** — the field heatmap animation.
- **`field_adder_final.png`** — final frame of the animation.

---

## The finding in one line

Removing the scheduler exposed a real physical requirement every earlier
version had hidden: you must **capture** a transient propagating spike into a
held signal to compute with it — which is precisely what a synapse does. The
field doesn't work without it, and with it, the computation emerges from
physical coupling alone, visible as a spike cascade through the circuit.

---

## Honest scope

The single full adder is a true no-scheduler field. The multi-bit ripple
adder chains those field-adders with latched carry handoff — it is not yet
one simultaneous field over the whole word (that monolithic version is the
next step). The latch is a hard capture, not a decaying postsynaptic
potential. See `PAPER.md` §5-7 for full limits.

---

## Reproduce it

```
python field_adder.py
python field_adder_viz.py 0 1 1
python field_timeline_viz.py 0 1 1
python field_ripple.py
```

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
