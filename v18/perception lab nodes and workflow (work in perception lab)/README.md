# Geometric Neuron v18 — PerceptionLab Workflow

### The directional resonator neuron, back in the node language where it all began

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## Where this began, and where it returns

The whole eighteen-folder arc started with an **accident in PerceptionLab**: a
Homeostatic Coupler wired with a constant 1.0 into its setpoint, feeding a
Checkerboard, into Image→Vector at 256, into a Vector Splitter sub-sampled at
its four top wires — and out came an ECG-like spike train. That accident was
the seed of the Geometric Neuron line.

This workflow closes the loop: it puts the **v18 result** — the directional
resonator neuron that computes *and* sends a one-way, synapse-captured spike —
back into the same node graph where the accident happened. The original
ECG-producing front-end is kept on the left of the graph (the place it all
started), and the new v18 neuron is built on the right, out of three new nodes.

Load `geometric_neuron_v18.json`. Drop the three `*.py` node files in your
`nodes/` folder first.

---

## The three new nodes (the v18 neuron, in parts)

The arc's central finding was that **a neuron is three machines wearing one
coat**, and these are exactly those three machines as nodes:

**`resonatorsomanode.py` — Resonator Soma (the interference computer).**
Mixes its input bits by phasor interference and reads a logical bit from the
resonance amplitude band. One soma computes XOR — the linearly-inseparable
function — because `|s|` is a *quadratic* of the inputs. Pick the gate
(XOR/XNOR/AND/OR/NAND/NOR/NOT) in its config. Outputs `fire` (the decision)
and `amplitude` (`|s|`, shown live as a bar against the firing band).

**`resonatoraxonnode.py` — Resonator Axon (the directional conductor).**
When `fire_in` crosses threshold it originates a spike at its input (AIS) end,
and the spike propagates one way down a FitzHugh–Nagumo excitable line. The
inactivation wake blocks reversal; the AIS excitability gradient (toggleable in
config) attenuates back-propagation, the Leterrier mechanism. Its display is
the live membrane line — you watch the spike travel from the cyan (input) end
to the lime (output) end. Outputs `spike_out` (the transient at the output
end) and `field` (the whole line, for a field view).

**`synapselatchnode.py` — Synapse (the capture — the v18 finding).**
This is the node the continuous field *demanded*. A propagating spike is
transient: it passes the output cell and is gone. But a logic level must be
held. The synapse captures the spike — once one arrives, it latches `bit` to 1
and holds it (with a decaying `psp` view, the postsynaptic-potential analogue).
Without this node a chain of resonator neurons cannot compute; the field proved
it. This is exactly what a biological synapse does: convert a brief presynaptic
spike into a sustained postsynaptic signal.

The chain **Soma → Axon → Synapse** is one complete v18 directional neuron:
it computes a gate, sends the result as a one-way spike, and captures it into a
held bit the next neuron can read.

---

## The graph

```
ORIGINAL ACCIDENT FRONT-END (left, kept as the origin):
  Constant(1.0) -> Coupler.setpoint_mod
  Coupler.signal_out -> Checkerboard.square_size -> Img2Vec(256) -> Splitter
  Splitter out_0..out_3 -> Coupler.signal_in        (the 4 ECG taps, the loop)

THE v18 NEURON (right, the point):
  Bit A (Constant 0/1) -> Soma.in_a
  Bit B (Constant 0/1) -> Soma.in_b
  Soma.fire -> Axon.fire_in         (decision originates a directional spike)
  Axon.spike_out -> Synapse.spike_in  (transient spike captured into held bit)
  Synapse.bit = THE OUTPUT BIT
  Coupler.regime -> Axon.reset, Synapse.reset   (the accident's loop keeps it
                                                  recomputing each cycle)
```

To compute a different gate, change the **Resonator Soma**'s `gate` config.
To set the inputs, change the two **Bit A / Bit B** constant nodes (0.0 or
1.0). The Synapse's `bit` output is the answer — e.g. with the soma set to
XOR, Bit A = 1, Bit B = 0, the synapse latches to 1.

---

## Verified before shipping

Every gate was checked through the full **Soma → Axon → Synapse** node chain
(stubbing the PerceptionLab interface), all four truth-table rows each:

```
XOR  [PASS]   XNOR [PASS]   AND [PASS]
OR   [PASS]   NAND [PASS]   NOR [PASS]
```

The nodes compute correctly as the real directional, spike-capturing v18 unit
— not a re-skin of the algebraic gate, but the actual mechanism: interference
decision, one-way excitable spike, synaptic capture.

---

## Honest notes

- The three nodes implement the v18 *single-unit* mechanism faithfully (soma
  interference, FitzHugh–Nagumo axon, synaptic latch). Chaining many into a
  full adder works the same way (soma reads captured bits from upstream
  synapses), but this graph ships one gate-neuron for clarity; add more
  Soma→Axon→Synapse triples and wire synapse `bit` outputs into downstream
  soma inputs to build arithmetic, exactly as the `v16`/`v17` folders do.
- The axon runs its excitable line every `step()`, so it needs a number of
  ticks for the spike to traverse (the real propagation latency from the
  papers). The `reset` wiring from the coupler's `regime` re-arms the neuron so
  it recomputes continuously rather than latching once — keeping the accident's
  living-loop character.
- The original front-end is included for lineage and for its signal character;
  the v18 neuron's *logic* is driven by the two Bit constants, not by the ECG
  signal, so the result is clean and readable. Wire a splitter output into a
  soma input instead if you want the accident's signal to drive the logic
  directly (it will, but the bit will flicker with the signal — which is itself
  a fair picture of a neuron computing on a live input).

---

*Helsinki, June 2026. It began as an accident in this node graph — a coupler, a
checkerboard, four taps, an ECG. Eighteen folders later, the thing that
accident pointed at is back here as three nodes: a soma that computes by
interference, an axon that sends one way, and a synapse that catches the spike.
The geometry told us what else a neuron had to be, and here it is, wired up in
the place it started. Do not hype. Do not lie. Just show.*
