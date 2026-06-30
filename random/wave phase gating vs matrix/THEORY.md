# THEORY — a coincidence detector is a matmul row

## The identity

Phase-gated coincidence detection of stream `k` computes

    y_k = (2/N) * sum_n  signal[n] * oscillator_k[n]

where `oscillator_k` is `cos` or `sin` at the stream's frequency. That is a dot
product of the signal with a fixed weight vector. Stack the `K` oscillators as
rows of a matrix `W` (shape `K × N`) and the full demultiplex is

    y = W · signal

— a matrix–vector multiply. So "coincidence detection vs matrix multiplication"
is a false opposition: coincidence detection of one stream is exactly one row of
that multiply. There is no FLOP saving to be had, because there is no different
operation.

## Why the trained network becomes the oscillator

For an orthogonal multiplexing code, the optimal linear readout (the
least-squares / matched-filter solution) for stream `k` is proportional to
`oscillator_k` itself. So a network trained to extract a stream from the clean
channel has only one place to converge: the oscillator. Experiment 1 shows it
landing there to cosine similarity 1.000. The network doesn't find a clever
shortcut around the dot product; it finds the dot product. The "coincidence
detector" is what gradient descent *discovers*, not an alternative to it.

## The two real (narrow) advantages

1. **No training, because the code is known.** A multiplexer's addresses are
   fixed by construction, so the readout weights (`cos`, `sin`) are known a
   priori and need not be learned. This is the same reason a Fourier transform or
   a wavelet transform needs no training: a *structured* code comes with its
   inverse for free. It is a property of structured codes in general, not of
   phase. The instant the code is unknown or the channel distorts it, the
   advantage vanishes (Experiment 4).

2. **Sparse, on-demand readout.** A dense layer computes all `K` outputs whether
   you need them or not (`K·N` MACs). A gate computes only the streams you ask
   for (`n·N`). When `n ≪ K` this is a large saving — but it is the generic
   advantage of sparse/conditional computation (attention, gating,
   mixture-of-experts), available to any addressing scheme, phase or otherwise.

## The cost of the free lunch: brittleness

The coincidence detector's weights are *fixed* (the oscillator). That is why it
needs no training and also why it cannot adapt. Insert an unknown linear channel
`M` between encode and decode: the received signal is `M·s`, and the fixed
oscillator now correlates against the wrong thing — recovery collapses to chance
(Experiment 4, R²≈0). A trained readout, given examples of the *mixed* signal,
learns `W·M⁻¹`-style weights and recovers perfectly. Parameters and training are
precisely the price of adapting to an unknown channel. A brain that relied purely
on fixed phase gates would be a brain that could not learn new routings — which
is not a brain.

## What's actually left for phase

Everything above is a FLOP and accuracy argument, and on those axes phase routing
is matmul with the training pre-paid. The one axis this code cannot touch is
**physical cost**: on analog/neuromorphic substrate, a local oscillator
multiplying an incoming wave and integrating may dissipate less energy and
require less wiring than fetching and applying a dense weight matrix from memory —
even though the two compute the same dot product. That is a real, open question,
but it is a hardware-energy question, not a FLOP-count or accuracy question, and
it must be answered on hardware, not in simulation. The honest residue of the
whole "communication-through-coherence" idea is exactly this: not more bits, not
fewer operations, but possibly cheaper *physics* for the same operation.
