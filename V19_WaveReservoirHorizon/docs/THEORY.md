# THEORY.md — where this sits in the geometric-neuron stack

This repo is one layer of a larger physics-native picture of neural computation.
It does not prove that picture; it tests one falsifiable piece of it and reports
the result, including a part that failed.

## The stack (as built across the repos)

1. **Computation = interference** (ResonantNeuron). Logic gates fall out of
   amplitude bands when phasors mix in a soma.
2. **Representation = phase on a manifold** (Landing Zones). A value is *where* a
   bump sits on a ring; steering is a coincidence (cosine of a phase difference).
3. **Memory = something that survives in the medium.** This repo asks: what kind
   of *something*, and for how long?

## What this layer establishes

Two claims, one positive and one negative, both from the dissipation-matched 2×2.

**Positive — geometry stores temporal order beyond its energy.**
A wave medium genuinely encodes the *order* of same-location pulses (propagation
turns "when" into "where"), and a reflecting cavity with a single outlet holds
that order in standing modes that outlive the bulk energy by ~16×, even when the
energy is forced to drain as fast as in open space. This is the honest, surviving
form of "geometry is memory": not the silhouette being pretty, but the **mode
structure** of the enclosed domain acting as a store. It is a measured separation
of two things people conflate — *energy persistence* (which we equalized) and
*information persistence* (which the cavity still won).

**Negative — per-compartment frequency tuning did not carry the order.**
Giving each satellite its own resonant frequency (`w0(x,y)`, the
Narayanan-Johnston / Snyder mechanism) left the order-memory horizon unchanged.
So in this task, "each to its own frequency" is not what holds the sequence. That
does not refute the resonance-gradient idea — it refutes a specific guess about
*what* it would buy you (temporal-order capacity). It very plausibly matters for
a *frequency-discrimination* or *multiplexing* task instead; that is a different
experiment, named in the open questions.

## How it reconciles the two cited papers

- **Snyder (2026)** argues dendrites are spatially organized frequency filters and
  that channel gradients give them real resonant structure. Our `w0` field is a
  faithful toy of that, and the resonance is verified. But our result says that
  structure, on its own, is not the carrier of *sequence* memory.
- **El-Quessny & Feller (2021)** show empirically that bare dendritic *morphology*
  often does not dictate a neuron's computation — wiring and timing do. Our null
  tuning effect, and our finding that it is the **mode structure** (a global
  property of the enclosed geometry) rather than local detail that holds the
  order, sits comfortably with their caution: do not assume shape-per-se computes;
  show which property of the shape is doing the work, and which is decoration.

The reconciliation: geometry matters here **through its global resonant modes**
(which set how long a distributed standing pattern can persist), not through
either bare silhouette or per-patch frequency labels. That is a narrower, more
defensible claim than "geometry is memory," and it is the one the data supports.

## The honest cliff edges (still open)

- The cavity horizon is uncollapsed (lower bound). We have not measured where the
  order finally washes out, only that it is ≫ the open box under matched loss.
- We tested discrete tuned patches ("each to its own frequency"). A smooth `w0`
  ramp (closer to the literal Narayanan-Johnston gradient) is untested and could
  behave differently.
- The map to biological time rests on a calibration choice, not a measurement.
- None of this touches learning. The connection that would make it "physics-based
  AI" rather than physics-based memory — a coupling that evolves on a free-energy
  gradient, with no external optimizer — remains the unproven frontier, exactly as
  flagged earlier in the program.

## Figure caveat (results/two_factor_figure.png)

The bottom-left "energy" panel is drawn from the cavity at its *matched* damping
level, which came out ≈0 (the cavity was already the fastest-leaking condition,
so no damping could be added without overshooting the shared 32-step target).
With ≈0 added damping the cavity energy oscillates and persists rather than
showing a clean 32-step decay, so the "half-energy at 32 steps" guide line in
that panel is illustrative of the *target*, not of that particular trace. The
load-bearing, correct panels are the forgetting curves (top-left) and the 2×2
horizon table (top-right). The honest one-line statement is: **under matched bulk
dissipation, the open box forgets order on its energy timescale while the cavity
does not** — established by the table, not by the energy trace.
