# CoincidenceVsMatmul — is phase-gated routing cheaper than a matrix multiply?

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
**Do not hype. Do not lie. Just show.**

---

## The question

The multiplexing repo ended on a claim worth testing: phase coding's real value
isn't capacity, it's the **decoder** — a single neuron with a theta clock can
pluck one stream out of a multiplexed wave with a *phase-gated coincidence
detector* (multiply by a local oscillator, integrate), where a standard network
would need a learned matrix multiply. So: **can a coincidence detector route
information cheaper and faster than a neural-network matmul?**

The answer is **no**, and the experiment shows the precise reason rather than
asserting it.

## What the four panels show

**1. The net learns the oscillator.**
Train a linear readout from `(multiplexed signal → target value)` examples on a
clean channel. Its learned weights match the coincidence oscillator with
**cosine similarity 1.000**, and both recover the stream at R²=1.0. The trained
network *rediscovers* `cos(2πft)` as its weights. A phase-gated coincidence
detector is therefore **one row of a matrix multiply** — not a different, cheaper
operation. The same operation.

**2. Same FLOPs per stream.**
Coincidence detection of one stream = `N` multiply-accumulates (one dot product),
**0 trained parameters**. A dense readout that computes all `K` streams = `K·N`
MACs and `K·N` parameters — which is the *same* `N` MACs *per stream*. The
coincidence detector is not doing fewer operations; it's doing the same dot
product, with its weights handed to it for free instead of learned.

**3. The only real saving is sparsity.**
If you need only a few of `K` streams, on-demand gating costs `n·N` while a dense
layer always computes all `K` (`K·N`). Need 5% of streams → 80× cheaper; need
100% → identical. This is a genuine advantage, but it's **sparse readout beats
dense readout** — a general fact (the reason attention, gating, and
mixture-of-experts exist), not anything phase-specific.

**4. The fixed gate is brittle; learning is what you pay for.**
Put an unknown linear mixing between encoder and decoder. The coincidence
detector, using its fixed oscillator, **collapses (R²=0.003)** — it doesn't know
the channel scrambled the code. The trained readout **learns to invert the
mixing (R²=1.0)**. That is exactly what the extra parameters and training buy:
adaptation to an unknown channel. The cheap local gate only works when the code
is clean and already known.

## The honest verdict

"Coincidence detection beats matmul" is false. Coincidence detection **is** a
matmul row — identical FLOPs, and on a clean channel the network literally learns
to become it. Its real advantages are narrow and not about phase:

- **zero training**, because in a multiplexer the address is known a priori
  (a structured code needs no learning — same reason a Fourier transform needs no
  training);
- **sparse, on-demand readout**, cheaper only when you want a slice of many
  streams.

And it pays for those with **brittleness**: the moment the channel mixes
unpredictably, the fixed gate is worthless and you must spend parameters and
training to recover. So Antti's prior is right — the answer is no — and now the
reason is on the table: it's the same computation, minus the learning, in the
one regime where learning wasn't needed.

## Where this leaves the phase idea (honestly)

Phase-gated coincidence detection is real and a neuron really can do it. But it
is not a free lunch over matrix multiplication — it is matrix multiplication that
nature gets to skip training for, because evolution/oscillatory structure
supplies the "weights" (the clock). The legitimate engineering interest is in the
two narrow wins above (training-free structured readout; sparse access), and in
the hardware claim this code can't measure: a local timing gate may cost less
*energy* and *wiring* than fetching a dense weight matrix, even at equal FLOPs.
That energy/locality claim — not a FLOP or accuracy claim — is the only place
left for phase to genuinely win, and it needs hardware, not numpy.

## Ledger

- **Verified:** trained readout ≡ oscillator (cos sim 1.000); equal MACs/stream;
  80× sparsity saving at 5% need; fixed-gate collapse under unknown mixing
  (0.003) vs trained recovery (1.000).
- **Not claimed:** that coincidence detection is a cheaper operation (it isn't);
  that phase routing beats matmul in FLOPs or accuracy (it doesn't); any
  energy/hardware advantage (untested — would need real hardware).
- **Open / real:** the energy-and-locality comparison on neuromorphic hardware,
  where a fixed local oscillator might beat dense weight access at equal FLOPs.

## Files

- `src/router.py` — encoder, coincidence detector, trained readout, mixing channel, self-test
- `src/experiment.py` — the four experiments, figure, JSON, verdict
- `results/router_result.png` — the four panels
- `results/router_result.json` — the numbers
