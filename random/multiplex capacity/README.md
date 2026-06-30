# MultiplexCapacity — does phase beat frequency for packing streams into one wave?

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
**Do not hype. Do not lie. Just show.**

---

## Why this exists

The "holographic Koopman compressor" multiplexed many audio modes into one 1D
wave by giving each a carrier frequency, then pulled them back out by
synchronous demodulation. Stripped of the metaphor that is **frequency-division
multiplexing** — 1920s radio. The honest question it raised is the one worth
testing: *how many independent streams can one 1D channel actually carry, and
does using **phase** buy anything over using **frequency**?* Phase is this
program's native variable, so if phase multiplexing had more capacity, that
would matter.

It does not. This repo shows why, with four measurements — two of which broke
the prediction I went in with, which is why they're worth keeping.

## The setup

A channel is one real signal of length `N` samples with `B` usable frequency
bins. Two ways to pack `K` scalar streams into it:

- **frequency (FDM, cosine only):** one stream per bin → capacity `B`. This is
  what the compressor did.
- **phase (quadrature):** each bin carries two streams, one on `cos` and one on
  `sin` (in-phase / quadrature) → capacity `2B`.

Both are matched-filter decoded. Below capacity both recover to machine
precision (`src/multiplex.py` self-test: max error ~1e-14).

## What the four experiments found (N=512, B=128, so 2B=256)

**1. Capacity ceiling — phase doubles it, then stops.**
Clean capacity (R²>0.9): frequency = **133** streams (≈ B), phase = **258**
streams (≈ 2B). A clean **1.94×**. But notice *what* the factor of two is:
phase isn't transcending anything — it's reclaiming the `sin` quadrature that
cosine-only FDM throws in the bin. The hard wall is the channel's **2B
dimension count** (the classic `2·bandwidth·time` degrees of freedom). Neither
scheme beats it. Frequency and phase are two **bases for the same space**, not
two different-sized spaces.

**2. Additive Gaussian noise — exactly identical.**
Mean R² gap between schemes across SNR = **0.007**. This is not a coincidence,
it's a theorem made visible: Gaussian noise is rotationally invariant, so it
hits every orthonormal basis equally. No basis — frequency, phase, or any
other — can be more robust to white noise than any other. Phase gives **zero**
advantage here.

**3. Timing jitter — phase wins, but NOT for the reason you'd hope (the surprise).**
Under a wandering clock, phase multiplexing degraded *more slowly* than
frequency. I had predicted the opposite (phase = timing-coded = fragile). The
data said phase, and then the diagnosis said why: phase packs 64 streams into 32
bins, so it sits at **lower frequencies** than frequency-MUX (64 bins). Jitter
phase-error grows with frequency (`Δφ ≈ 2πf·δt`), so the lower-frequency scheme
wins. **This is bandwidth efficiency, not phase magic** — a frequency code using
both quadratures would inherit the same benefit. Logged as a confound, not a
result.

**4. Rate (power-only) readout — phase needs a phase-sensitive decoder.**
A decoder that reads only spectral power per bin (a firing-**rate** code)
recovers frequency streams perfectly (R²=1.0) but **scrambles** phase streams
(R²=0.48), because it cannot separate the two quadrature partners sharing a bin.
Phase coding only pays off if the decoder can actually read phase.

## The honest bottom line

Phase and frequency are **the same currency** — orthogonal dimensions of a
band-limited channel. Phase multiplexing buys **no capacity** the dimension
count doesn't already grant; its apparent "2× over the compressor" is just the
compressor having wasted half the channel. Under white noise the two are
provably identical. The differences that *do* appear trace to bandwidth
occupancy (jitter) or decoder type (rate readout), not to phase being special.

Where phase plausibly *does* matter in a brain is the thing this experiment
**did not** test: **decoder locality and selectivity**. A phase-gated
coincidence detector (communication-through-coherence; Fries 2005/2015; Akam &
Kullmann 2010/2014 on oscillatory multiplexing) is a cheap, local mechanism a
single neuron can build to select one stream — whereas frequency demux needs a
filter bank. The neuroscience case for phase is about *how cheaply you can route
and gate*, not about *how many bits fit*. That's the next experiment, and it's
the one that could still make phase earn its keep.

## Ledger

- **Verified:** below-capacity recovery is exact (1e-14); the 2× capacity ratio;
  the AWGN null; the rate-readout scramble.
- **Surprise, honestly handled:** phase looked jitter-robust; traced to lower
  frequency occupancy, not an intrinsic phase property — flagged, not sold.
- **Not claimed:** that phase beats frequency in capacity (it doesn't); that any
  of this is how brains route information (untested); that the jitter advantage
  is a phase property (it's bandwidth efficiency).
- **Open:** the locality/selectivity test — can a phase-gated coincidence
  detector select one stream more cheaply than a frequency filter bank? That is
  where the real neuroscience claim lives.

## Files

- `src/multiplex.py` — encoders/decoders (FDM, quadrature, power-only) + self-test
- `src/experiment.py` — the four experiments, the figure, the JSON, the verdict
- `results/capacity_result.png` — the four panels
- `results/capacity_result.json` — the numbers
