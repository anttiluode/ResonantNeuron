# Pacing fix — why an isolated paced neuron now outputs a bit

If you wired `Septum.peak -> Axon.reset` (an earlier version) the neuron
computed but never delivered a bit: the axon showed `out v ≈ -1.2` (rest) and
the synapse stayed `bit=0`. That was a real bug, and it is the v16 lesson
surfacing at the node level.

**What was wrong**

- `reset` HARD-CLEARS the axon line to rest. Driving it from the theta `peak`
  wiped the line every ~139 sim-steps.
- But a spike needs to *conduct* the length of the axon before it reaches the
  output. On the old 40-cell axon that took ~650 steps — far longer than the
  theta period. So every spike was erased mid-flight, before it could ever
  arrive. The clock was strangling the computation instead of pacing it.

**The fix (two parts)**

1. The Axon node now has a separate **`trigger`** input. `trigger` ORIGINATES
   one spike on a rising edge and then lets it conduct UNDISTURBED. `reset` is
   kept only for an explicit "start a fresh computation" hard-clear. Pace with
   `peak -> trigger`, never `peak -> reset`.
2. The Axon default is now a shorter, faster line (20 cells, larger time step)
   so a full spike conducts in ~90 steps — comfortably inside one theta cycle.
   The clock period now exceeds the conduction latency, which is exactly the
   v16 condition ("the clock must be slower than the logic depth it stages").

**Correct wiring (in geometric_neuron_v19.json):**

```
Septum.peak     -> Axon.trigger      (one spike originated per theta cycle)
Axon.spike_out  -> Synapse.spike_in  (the synapse captures + HOLDS the bit)
Axon.arrived    -> Septum.reset_in   (downstream firing resets the clock — loop)
```

Do NOT wire `peak -> Synapse.reset`: that would clear the captured bit every
cycle and you'd never see the output. The synapse is meant to hold.

Verified: every gate (XOR/AND/OR, all input pairs) now latches the correct
output bit, ~one theta cycle after the inputs are presented.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
