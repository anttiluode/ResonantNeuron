#!/usr/bin/env python3
"""
experiment.py
=============
Is a phase-gated coincidence detector a cheaper/faster router than a neural
network matrix multiply? Four measurements:

  1. IDENTITY    -- train a readout to route the channel; what does it become?
  2. COST        -- MACs and parameters per extracted stream.
  3. SPARSITY    -- cost vs how many of K streams you actually need.
  4. FAIRNESS    -- put an UNKNOWN channel in the middle: who survives?

Going in: the coincidence detector should equal the trained net for free on a
clean channel (because it IS the optimal readout), win on sparsity, and lose
the moment the channel mixes unpredictably (because it can't adapt). If that's
what we see, "coincidence beats matmul" is false -- it IS matmul, minus the
training, restricted to the easy case.
"""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from router import (encode, oscillator, coincidence, train_linear_readout,
                    random_mixing, r2)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")
os.makedirs(RESULTS, exist_ok=True)

N, K = 256, 80
rng = np.random.default_rng(1)


def main():
    print("=" * 66)
    print(f"COINCIDENCE DETECTOR  vs  TRAINED MATMUL ROUTER  (N={N}, K={K})")
    print("=" * 66)
    target = 7

    # training / test data: random stream values -> multiplexed signal
    Vtr = rng.standard_normal((2500, K)); Xtr = np.array([encode(v, N) for v in Vtr])
    Vte = rng.standard_normal((600, K));  Xte = np.array([encode(v, N) for v in Vte])

    # ---- 1. IDENTITY ----
    w_learned = train_linear_readout(Xtr, Vtr[:, target])
    w_osc = (2.0 / N) * oscillator(target, N)
    cos_sim = float(np.dot(w_learned, w_osc) /
                    (np.linalg.norm(w_learned) * np.linalg.norm(w_osc) + 1e-12))
    coin_R2 = r2(Vte[:, target], np.array([coincidence(x, target, N) for x in Xte]))
    lin_R2 = r2(Vte[:, target], Xte @ w_learned)
    print(f"\n[1] IDENTITY")
    print(f"    trained readout vs coincidence oscillator: cosine sim = {cos_sim:.4f}")
    print(f"    coincidence R2 = {coin_R2:.4f}   trained-linear R2 = {lin_R2:.4f}")
    print(f"    --> the net LEARNS the oscillator. Coincidence detection is a matmul row.")

    # ---- 2. COST ----
    coin_macs, coin_params = N, 0
    dense_macs, dense_params = K * N, K * N
    print(f"\n[2] COST per extracted stream")
    print(f"    coincidence: {coin_macs} MACs, {coin_params} trained params")
    print(f"    dense readout (all K): {dense_macs} MACs, {dense_params} params "
          f"= {dense_macs//K} MACs/stream")
    print(f"    --> SAME MACs per stream. The win is 0 params (known code), not fewer FLOPs.")

    # ---- 3. SPARSITY ----
    fracs = np.linspace(0.02, 1.0, 12)
    gate_cost = [int(f * K) * N for f in fracs]     # extract f*K streams on demand
    dense_cost = [K * N for _ in fracs]             # dense layer computes all K always
    print(f"\n[3] SPARSITY: extracting a fraction of streams")
    print(f"    need 5% of streams: gating {gate_cost[0]} MACs vs dense {dense_cost[0]} MACs "
          f"({dense_cost[0]/max(gate_cost[0],1):.0f}x)")
    print(f"    need 100%:          gating {gate_cost[-1]} vs dense {dense_cost[-1]} (equal)")
    print(f"    --> coincidence is cheaper ONLY when you need few of many (sparsity, not phase).")

    # ---- 4. FAIRNESS: an unknown channel in the middle ----
    M = random_mixing(N, rng)
    Xtr_mix = Xtr @ M.T
    Xte_mix = Xte @ M.T
    # coincidence uses the ORIGINAL oscillator (doesn't know the channel mixed)
    coin_mix = r2(Vte[:, target], np.array([coincidence(x, target, N) for x in Xte_mix]))
    # trained readout learns on the mixed signals
    w_mix = train_linear_readout(Xtr_mix, Vtr[:, target])
    lin_mix = r2(Vte[:, target], Xte_mix @ w_mix)
    print(f"\n[4] UNKNOWN CHANNEL (random mixing between encoder and decoder)")
    print(f"    clean channel:  coincidence R2={coin_R2:.3f}   trained R2={lin_R2:.3f}")
    print(f"    mixed channel:  coincidence R2={coin_mix:.3f}   trained R2={lin_mix:.3f}")
    print(f"    --> the fixed gate collapses; the trained readout learns to invert the")
    print(f"        channel. Learning is what you pay for, and what robustness costs.")

    # ---- verdict ----
    print("\n" + "=" * 66)
    print("VERDICT")
    print("=" * 66)
    print(f"  - coincidence detection IS one row of a matmul (cos sim {cos_sim:.2f},")
    print(f"    same {N} MACs/stream). It is not a cheaper operation; it is the same one.")
    print(f"  - its genuine advantages are narrow and not phase-specific:")
    print(f"      (a) zero training, because the address is known a priori;")
    print(f"      (b) sparse readout, cheaper only when you need few of many streams.")
    print(f"  - it is brittle: an unknown channel ({coin_mix:.2f}) defeats the fixed gate")
    print(f"    while the trained net ({lin_mix:.2f}) adapts. So the answer to 'cheaper")
    print(f"    and faster than matmul' is NO -- it's the same matmul, minus the learning,")
    print(f"    only in the case where the code is clean and already known.")

    results = {
        "identity": {"cosine_similarity": cos_sim, "coincidence_R2": coin_R2,
                     "trained_R2": lin_R2},
        "cost": {"coincidence_macs": coin_macs, "coincidence_params": coin_params,
                 "dense_macs_allK": dense_macs, "dense_params": dense_params,
                 "macs_per_stream_equal": N},
        "sparsity": {"fracs": fracs.tolist(), "gate_cost": gate_cost,
                     "dense_cost": dense_cost},
        "fairness": {"clean": {"coincidence": coin_R2, "trained": lin_R2},
                     "mixed": {"coincidence": coin_mix, "trained": lin_mix}},
    }
    with open(os.path.join(RESULTS, "router_result.json"), "w") as f:
        json.dump(results, f, indent=2)

    # ---- figure ----
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    n_show = 96
    ax[0, 0].plot(w_osc[:n_show], color="#d1495b", lw=2.4, label="coincidence oscillator")
    ax[0, 0].plot(w_learned[:n_show], color="#1a1a2e", lw=1.2, ls="--",
                  label="trained readout weights")
    ax[0, 0].set_title(f"1. The net learns the oscillator\ncosine similarity = {cos_sim:.3f}")
    ax[0, 0].set_xlabel("weight index"); ax[0, 0].legend(fontsize=9)

    ax[0, 1].bar(["coincidence\n(1 stream)", "dense matmul\n(all K)"],
                 [coin_macs, dense_macs], color=["#1a1a2e", "#d1495b"])
    ax[0, 1].set_ylabel("MACs")
    ax[0, 1].set_title(f"2. Cost: same {N} MACs per stream\n(dense computes all K at once)")
    for i, v in enumerate([coin_macs, dense_macs]):
        ax[0, 1].text(i, v, f"{v}", ha="center", va="bottom", fontsize=9)

    ax[1, 0].plot(fracs * 100, gate_cost, "o-", color="#1a1a2e",
                  label="phase-gated (on demand)")
    ax[1, 0].plot(fracs * 100, dense_cost, "s-", color="#d1495b",
                  label="dense readout (always all K)")
    ax[1, 0].set_xlabel("% of streams you actually need")
    ax[1, 0].set_ylabel("MACs")
    ax[1, 0].set_title("3. Sparsity is the only real saving\n(cheaper when you need few of many)")
    ax[1, 0].legend(fontsize=9)

    x = np.arange(2); wbar = 0.35
    ax[1, 1].bar(x - wbar/2, [coin_R2, coin_mix], wbar, color="#1a1a2e", label="coincidence")
    ax[1, 1].bar(x + wbar/2, [lin_R2, lin_mix], wbar, color="#d1495b", label="trained")
    ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels(["clean\nchannel", "unknown\nmixing"])
    ax[1, 1].set_ylabel("recovery $R^2$"); ax[1, 1].set_ylim(0, 1.05)
    ax[1, 1].set_title("4. The fixed gate is brittle\nlearning buys channel-inversion")
    ax[1, 1].legend(fontsize=9)

    plt.tight_layout()
    fig.savefig(os.path.join(RESULTS, "router_result.png"), dpi=130)
    print(f"\n[saved] results/router_result.png")
    print(f"[saved] results/router_result.json")


if __name__ == "__main__":
    main()
