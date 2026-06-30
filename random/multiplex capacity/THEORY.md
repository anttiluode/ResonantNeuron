# THEORY — why phase and frequency are the same currency

## The dimension count is the whole story

A real signal sampled at `N` points is a vector in an `N`-dimensional space.
Any orthonormal basis of that space gives `N` independent coordinates — no more,
no fewer. The Fourier basis splits those `N` dimensions into a DC term, `N/2−1`
cosine coordinates, `N/2−1` sine coordinates, and a Nyquist term. In
continuous-time language this is the classic result that a signal of bandwidth
`B` and duration `T` has about `2BT` independent degrees of freedom.

Multiplexing is just *a choice of how to spend those dimensions*:

- **Cosine-only FDM** spends one dimension per stream and uses only the cosine
  half of the basis → ceiling `≈ N/2` (here `B` bins).
- **Quadrature/phase** uses both the cosine and sine of each frequency → ceiling
  `≈ N` (here `2B`).

So phase "doubles capacity" over cosine-only FDM in the same sense that using
both hands doubles how much you can carry over using one hand. The ceiling at
the full dimension count is hard: pack `K > 2B` streams and, by pigeonhole, two
must share a coordinate and their values add — irrecoverably. No encoding trick,
phase or otherwise, escapes the dimension count. (If one did, you could send
unlimited information through a fixed channel, which is exactly what Shannon
forbids.)

## Why Gaussian noise can't tell the bases apart

White Gaussian noise has a rotationally invariant distribution: its covariance
is a scalar multiple of the identity, so it looks statistically identical in
every orthonormal basis. Project it onto cosine coordinates or onto
phase/quadrature coordinates — same noise power per coordinate either way.
Matched-filter recovery of any orthonormal code therefore has identical
error under AWGN. Experiment 2 is this theorem rendered as two curves that lie
on top of each other (gap 0.007).

## Why the jitter result is a confound, not a property

Timing jitter `t → t + δt` turns into a phase error `Δφ ≈ 2πf·δt` that **grows
with frequency**. Whichever scheme places its streams at lower frequencies for a
given stream count will look more jitter-robust. Quadrature packs two streams per
bin, so for the same `K` it occupies half the frequency extent of cosine-only
FDM — hence lower top frequency, hence less jitter error. The advantage is
inherited from bandwidth efficiency (a dimension-counting fact again), not from
phase being intrinsically timing-robust. A frequency code that also used both
quadratures would show the same robustness. To isolate any *intrinsic* phase
effect you would have to match the frequency content exactly, which is impossible
at equal `K` and equal bandwidth — precisely because the two schemes are the same
dimensions wearing different labels.

## Where phase is actually different: the decoder, not the channel

Everything above is about the *channel* — and there phase and frequency are
interchangeable. The asymmetry lives in the **decoder**:

- A **power/rate** readout (Experiment 4) collapses each bin's two quadrature
  coordinates into one magnitude, so it cannot separate phase-multiplexed
  streams (R² 0.48 vs 1.0). A rate code is blind to phase.
- A **phase-gated coincidence detector** — multiply by a local oscillator at a
  target phase and integrate over a short window — selects exactly the stream
  aligned with that phase and rejects the rest, using a mechanism a single
  neuron physically has. A frequency demultiplexer needs a bank of tuned filters.

This is the real content of the neuroscience "oscillatory multiplexing" /
"communication-through-coherence" literature: the win from phase is **selective
routing with a cheap local gate**, not extra bits in the channel. The capacity
is fixed by physics; the *access pattern* is where biology might be clever. That
is the experiment this repo sets up but does not yet run.
