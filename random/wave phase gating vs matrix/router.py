#!/usr/bin/env python3
"""
router.py
=========
Compare two ways to pull ONE stream out of a phase-multiplexed channel:

  coincidence  -- multiply by a local oscillator (cos/sin at the target slot),
                  integrate. Zero trained parameters. This is what a single
                  neuron with a theta clock can physically do.
  trained      -- learn a linear readout from (signal -> value) examples.
                  This is a row of a neural-network weight matrix.

The point: a coincidence detector is mathematically ONE ROW of a matrix
multiply. The trained net, given a clean multiplexed channel, *learns the
oscillator* as its weights. So "cheaper than matmul" is false in FLOP terms --
it IS a matmul row. The only honest savings are (a) zero training when the code
is known, and (b) sparse on-demand readout (extract few of many).

And it's brittle: put an unknown mixing between encoder and decoder and the
fixed oscillator fails while the trained readout learns to invert it. That is
what learning actually buys.
"""
import numpy as np


def oscillator(slot, N, t=None):
    if t is None:
        t = np.arange(N) / N
    binf = (slot // 2) + 1
    return (np.cos if slot % 2 == 0 else np.sin)(2 * np.pi * binf * t)


def encode(values, N, t=None):
    """Phase/quadrature multiplex K stream values into one length-N signal."""
    if t is None:
        t = np.arange(N) / N
    s = np.zeros(len(t))
    for k, v in enumerate(values):
        binf = (k // 2) + 1
        s += v * (np.cos if k % 2 == 0 else np.sin)(2 * np.pi * binf * t)
    return s


def coincidence(signal, slot, N):
    """Phase-gated coincidence detection of one stream: a single dot product."""
    return (2.0 / N) * np.dot(signal, oscillator(slot, N))


def train_linear_readout(X, y):
    """Least-squares linear readout y ~= X @ w. Returns the learned weight row."""
    w, *_ = np.linalg.lstsq(X, y, rcond=None)
    return w


def random_mixing(N, rng):
    """A random orthogonal NxN channel (unknown linear transfer)."""
    A = rng.standard_normal((N, N))
    Q, _ = np.linalg.qr(A)
    return Q


def r2(true, pred):
    if np.std(true) < 1e-12 or np.std(pred) < 1e-12:
        return 0.0
    return float(max(0.0, np.corrcoef(true, pred)[0, 1]) ** 2)


def _selftest():
    rng = np.random.default_rng(0)
    N, K, target = 256, 80, 7
    Vtr = rng.standard_normal((1500, K))
    Xtr = np.array([encode(v, N) for v in Vtr])
    w = train_linear_readout(Xtr, Vtr[:, target])
    w_osc = (2.0 / N) * oscillator(target, N)
    cs = np.dot(w, w_osc) / (np.linalg.norm(w) * np.linalg.norm(w_osc) + 1e-12)
    print(f"self-test: trained readout vs oscillator cosine similarity = {cs:.4f} "
          f"(should be ~1.0 -- the net learns the coincidence detector)")


if __name__ == "__main__":
    _selftest()
