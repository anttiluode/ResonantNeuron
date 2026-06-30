#!/usr/bin/env python3
"""
multiplex.py
============
Two ways to pack K independent scalar streams into ONE 1D channel of length N:

  'fdm'   -- frequency-division, cosine only. One stream per frequency bin.
             This is (essentially) what the "holographic compressor" did.
  'phase' -- quadrature / phase multiplexing. Each frequency bin carries TWO
             streams, one on cos and one on sin (in-phase and quadrature).

The point of the comparison: does using PHASE buy capacity over using
FREQUENCY? Both are matched-filter decoded. Validated to machine precision
below capacity in the self-test.
"""
import numpy as np


def _basis(N, k, t=None):
    if t is None:
        t = np.arange(N) / N
    return np.cos(2 * np.pi * k * t), np.sin(2 * np.pi * k * t)


def encode(values, scheme, N, B, t=None):
    """values: length-K array of stream values.  B = number of frequency bins.
       fdm capacity = B ; phase capacity = 2B.  Beyond capacity, streams
       collide on shared slots (their values add) -- recovery then degrades."""
    if t is None:
        t = np.arange(N) / N
    s = np.zeros(len(t))
    for k, v in enumerate(values):
        if scheme == "fdm":
            binf = (k % B) + 1
            s += v * np.cos(2 * np.pi * binf * t)
        else:
            slot = k % (2 * B)
            binf = (slot // 2) + 1
            c, sn = _basis(N, binf, t)
            s += v * (c if slot % 2 == 0 else sn)
    return s


def decode(signal, K, scheme, N, B, t=None):
    """Matched-filter (correlation) decode of K streams."""
    if t is None:
        t = np.arange(N) / N
    out = np.zeros(K)
    for k in range(K):
        if scheme == "fdm":
            binf = (k % B) + 1
            out[k] = (2.0 / N) * np.sum(signal * np.cos(2 * np.pi * binf * t))
        else:
            slot = k % (2 * B)
            binf = (slot // 2) + 1
            c, sn = _basis(N, binf, t)
            basisvec = c if slot % 2 == 0 else sn
            out[k] = (2.0 / N) * np.sum(signal * basisvec)
    return out


def decode_power_only(signal, K, scheme, N, B):
    """A decoder that can read only spectral POWER per bin, not phase
       (a 'rate' readout). It recovers magnitude per frequency bin and splits
       it -- it cannot tell the cos stream from the sin stream."""
    t = np.arange(N) / N
    out = np.zeros(K)
    for k in range(K):
        if scheme == "fdm":
            binf = (k % B) + 1
            a = (2.0 / N) * np.sum(signal * np.cos(2 * np.pi * binf * t))
            out[k] = abs(a)                       # cos-only: power == |a|
        else:
            slot = k % (2 * B)
            binf = (slot // 2) + 1
            c, sn = _basis(N, binf, t)
            a = (2.0 / N) * np.sum(signal * c)
            b = (2.0 / N) * np.sum(signal * sn)
            out[k] = np.hypot(a, b)               # only the magnitude survives
    return out


def _selftest():
    N, B = 512, 128
    rng = np.random.default_rng(0)
    print("self-test (zero noise, below capacity -> perfect recovery):")
    for scheme, cap in [("fdm", B), ("phase", 2 * B)]:
        K = cap // 2
        v = rng.standard_normal(K)
        s = encode(v, scheme, N, B)
        err = np.max(np.abs(v - decode(s, K, scheme, N, B)))
        print(f"  {scheme:6s} K={K:3d} (cap {cap}): max error = {err:.1e}")


if __name__ == "__main__":
    _selftest()
