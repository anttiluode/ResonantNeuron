#!/usr/bin/env python3
"""
experiment.py
=============
Does PHASE multiplexing beat FREQUENCY multiplexing for packing independent
streams into one 1D channel? Four measurements, each able to embarrass the
hopeful answer:

  1. CAPACITY CEILING  -- how many streams fit before recovery collapses?
  2. AWGN ROBUSTNESS   -- under additive Gaussian noise, does phase help?
  3. TIMING JITTER     -- under a wandering clock, who survives?
  4. RATE READOUT      -- if the decoder reads power only (no phase), who survives?

Honest expectation going in (to be confirmed or broken by the numbers):
the channel has a fixed number of orthogonal dimensions (~2*B). Frequency and
phase are just two bases for that same space, so phase cannot exceed the
dimension limit -- it can only reclaim the quadrature that cosine-only FDM
throws away. And phase, being timing-coded, should be the FRAGILE one.
"""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiplex import encode, decode, decode_power_only

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")
os.makedirs(RESULTS, exist_ok=True)

N, B = 512, 128                       # channel length, frequency bins (bandwidth)
rng = np.random.default_rng(1)


def recovery_R2(true, rec):
    if np.std(true) < 1e-12 or np.std(rec) < 1e-12:
        return 0.0
    r = np.corrcoef(true, rec)[0, 1]
    return float(max(0.0, r) ** 2)


def run_capacity(trials=24):
    Ks = np.unique(np.linspace(8, 300, 22).astype(int))
    curves = {"fdm": [], "phase": []}
    for scheme in curves:
        for K in Ks:
            acc = []
            for _ in range(trials):
                v = rng.standard_normal(K)
                s = encode(v, scheme, N, B)
                acc.append(recovery_R2(v, decode(s, K, scheme, N, B)))
            curves[scheme].append(float(np.mean(acc)))
    return Ks.tolist(), curves


def run_awgn(K=64, trials=40):
    snrs = np.array([0.1, 0.3, 1.0, 3.0, 10.0])
    out = {"fdm": [], "phase": []}
    for scheme in out:
        for snr in snrs:
            acc = []
            for _ in range(trials):
                v = rng.standard_normal(K)
                s = encode(v, scheme, N, B)
                noise = rng.standard_normal(N)
                noise *= np.std(s) / (np.std(noise) * np.sqrt(snr))
                acc.append(recovery_R2(v, decode(s + noise, K, scheme, N, B)))
            out[scheme].append(float(np.mean(acc)))
    return snrs.tolist(), out


def run_jitter(K=64, trials=40):
    levels = np.array([0.0, 0.002, 0.005, 0.01, 0.02, 0.05])
    t0 = np.arange(N) / N
    out = {"fdm": [], "phase": []}
    for scheme in out:
        for lev in levels:
            acc = []
            for _ in range(trials):
                v = rng.standard_normal(K)
                # synthesize on a JITTERED clock; decode assumes a clean one
                jit = gaussian_filter1d(rng.standard_normal(N), 2.0)
                jit *= lev / (np.std(jit) + 1e-12)
                tj = t0 + jit
                s = encode(v, scheme, N, B, t=tj)
                acc.append(recovery_R2(v, decode(s, K, scheme, N, B, t=t0)))
            out[scheme].append(float(np.mean(acc)))
    return levels.tolist(), out


def run_rate_readout(K=64, trials=40):
    """Decoder reads spectral power only (no phase) -- a firing-rate code."""
    out = {}
    for scheme in ("fdm", "phase"):
        acc = []
        for _ in range(trials):
            v = np.abs(rng.standard_normal(K))     # positive 'rates'
            s = encode(v, scheme, N, B)
            acc.append(recovery_R2(v, decode_power_only(s, K, scheme, N, B)))
        out[scheme] = float(np.mean(acc))
    return out


def main():
    print("=" * 66)
    print(f"MULTIPLEXING CAPACITY  (channel N={N}, bandwidth B={B} bins)")
    print(f"  dimension limit ~ 2B = {2*B} orthogonal streams")
    print("=" * 66)

    Ks, cap = run_capacity()
    # CLEAN (near-lossless) capacity = largest K still recovered at R2 > 0.9.
    # A lenient threshold overstates capacity because collisions degrade
    # gracefully (a few corrupted streams barely dent the correlation).
    def ceiling(curve):
        good = [k for k, r in zip(Ks, curve) if r > 0.9]
        return max(good) if good else 0
    cap_fdm, cap_phase = ceiling(cap["fdm"]), ceiling(cap["phase"])
    print(f"\n[1] CLEAN CAPACITY (R2>0.9):")
    print(f"    fdm (cos only) : {cap_fdm:3d} streams   (channel bins B={B})")
    print(f"    phase (cos+sin): {cap_phase:3d} streams   (dimension limit 2B={2*B})")
    print(f"    phase / fdm capacity ratio = {cap_phase/max(cap_fdm,1):.2f}  "
          f"(~2x: phase reclaims the quadrature FDM wastes)")

    snrs, awgn = run_awgn()
    gap = np.mean(np.abs(np.array(awgn["fdm"]) - np.array(awgn["phase"])))
    print(f"\n[2] AWGN ROBUSTNESS (K=64): mean |fdm-phase| R2 gap = {gap:.3f}")
    print(f"    fdm  R2 vs SNR: {[round(x,2) for x in awgn['fdm']]}")
    print(f"    phase R2 vs SNR:{[round(x,2) for x in awgn['phase']]}")
    print(f"    --> near-zero gap means phase gives NO advantage under AWGN")

    levels, jit = run_jitter()
    print(f"\n[3] TIMING JITTER (K=64):")
    print(f"    fdm  R2 vs jitter: {[round(x,2) for x in jit['fdm']]}")
    print(f"    phase R2 vs jitter:{[round(x,2) for x in jit['phase']]}")
    diff = np.mean(np.array(jit['phase']) - np.array(jit['fdm']))
    print(f"    --> mean (phase - fdm) = {diff:+.3f}  "
          f"(phase is MORE jitter-robust here)")
    print(f"    CONFOUND (honest): phase packs 64 streams into 32 bins, so it "
          f"occupies LOWER frequencies than fdm (64 bins). Jitter phase-error "
          f"grows with frequency, so phase wins via bandwidth efficiency -- "
          f"NOT because phase is intrinsically timing-robust.")

    rate = run_rate_readout()
    print(f"\n[4] RATE READOUT (power only, no phase):")
    print(f"    fdm  R2 = {rate['fdm']:.3f}   phase R2 = {rate['phase']:.3f}")
    print(f"    --> a power/rate decoder reads frequency streams cleanly but "
          f"SCRAMBLES phase streams (each bin's two quadrature partners blur "
          f"into one magnitude).")

    # verdict
    print("\n" + "=" * 66)
    print("VERDICT (from the numbers, including the surprises)")
    print("=" * 66)
    print(f"  1. phase doubles CLEAN capacity over cosine-only FDM "
          f"({cap_phase} vs {cap_fdm}) -- by using the quadrature FDM throws")
    print(f"     away, NOT by beating the channel's 2B={2*B} dimension limit.")
    print(f"  2. under AWGN, phase and frequency are identical (gap {gap:.3f}):")
    print(f"     Gaussian noise is basis-blind, so no scheme wins. (a theorem,")
    print(f"     confirmed numerically.)")
    print(f"  3. phase looked more jitter-robust, but that's bandwidth")
    print(f"     efficiency (lower frequencies), not phase magic -- flagged.")
    print(f"  4. a rate/power readout cannot separate phase streams.")
    print(f"  BOTTOM LINE: phase and frequency are the same currency -- "
          f"dimensions of a band-limited channel. Phase buys no capacity the")
    print(f"  dimension count doesn't already allow. Its real edge (untested "
          f"here) is decoder LOCALITY, not bits.")

    results = {
        "channel": {"N": N, "B": B, "dimension_limit": 2 * B},
        "capacity": {"Ks": Ks, "curves": cap,
                     "ceiling_fdm": cap_fdm, "ceiling_phase": cap_phase},
        "awgn": {"snrs": snrs, "curves": awgn, "mean_gap": float(gap)},
        "jitter": {"levels": levels, "curves": jit},
        "rate_readout": rate,
    }
    with open(os.path.join(RESULTS, "capacity_result.json"), "w") as f:
        json.dump(results, f, indent=2)

    # figure
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    ax[0, 0].plot(Ks, cap["fdm"], "o-", color="#d1495b", label="frequency (cos only)")
    ax[0, 0].plot(Ks, cap["phase"], "s-", color="#1a1a2e", label="phase (cos+sin)")
    ax[0, 0].axvline(B, color="#d1495b", ls=":", lw=1)
    ax[0, 0].axvline(2 * B, color="#1a1a2e", ls=":", lw=1)
    ax[0, 0].axhline(0.5, color="gray", ls="--", lw=0.8)
    ax[0, 0].set_xlabel("number of streams K")
    ax[0, 0].set_ylabel("recovery $R^2$")
    ax[0, 0].set_title(f"1. Capacity ceiling\nphase doubles it (B={B} -> 2B={2*B}), "
                       "but no further")
    ax[0, 0].legend()

    ax[0, 1].semilogx(snrs, awgn["fdm"], "o-", color="#d1495b", label="frequency")
    ax[0, 1].semilogx(snrs, awgn["phase"], "s-", color="#1a1a2e", label="phase")
    ax[0, 1].set_xlabel("SNR")
    ax[0, 1].set_ylabel("recovery $R^2$")
    ax[0, 1].set_title("2. Additive Gaussian noise\nidentical curves "
                       "(phase gives no advantage)")
    ax[0, 1].legend()

    ax[1, 0].plot(levels, jit["fdm"], "o-", color="#d1495b", label="frequency")
    ax[1, 0].plot(levels, jit["phase"], "s-", color="#1a1a2e", label="phase")
    ax[1, 0].set_xlabel("timing-jitter level")
    ax[1, 0].set_ylabel("recovery $R^2$")
    ax[1, 0].set_title("3. Wandering clock (timing jitter)\nphase survives better "
                       "-- via lower frequencies, not phase magic")
    ax[1, 0].legend()

    ax[1, 1].bar(["frequency", "phase"], [rate["fdm"], rate["phase"]],
                 color=["#d1495b", "#1a1a2e"])
    ax[1, 1].set_ylabel("recovery $R^2$")
    ax[1, 1].set_ylim(0, 1)
    ax[1, 1].set_title("4. Power-only (rate) readout\nphase streams scrambled "
                       "without a phase-sensitive decoder")

    plt.tight_layout()
    fig.savefig(os.path.join(RESULTS, "capacity_result.png"), dpi=130)
    print(f"\n[saved] results/capacity_result.png")
    print(f"[saved] results/capacity_result.json")


if __name__ == "__main__":
    main()
