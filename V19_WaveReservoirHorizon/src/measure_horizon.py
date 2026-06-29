"""
measure_horizon.py - find the REAL memory horizon of the open box and the
magnetron cavity, fit the decay, and convert steps -> milliseconds.

Task: 3 pulses of distinct magnitudes {1,2,3} fired at ONE point in a fixed
order (6 possible orders = 6 classes). Spatial identity carries no information
(same point every time); only the temporal ORDER can distinguish classes, and
only the wave dynamics can turn "when" into a readable spatial pattern. A linear
readout (logistic regression) on the coarse-grained frozen field at a given
delay must recover the order. Accuracy vs delay = the forgetting curve.

We run BOTH geometries out far enough that each collapses to chance, fit a
sigmoid to locate the horizon (50%-of-range crossing), and then map step-count
to milliseconds using a physical dendritic calibration (see physical_time()).

Honest guardrails baked in:
  - shuffle control pins the empirical chance level
  - same-point injection kills the "which site" cheat
  - strong sponge drains slow components (else the curve plateaus falsely)
  - we report a LOWER BOUND if a curve has not collapsed in range
"""

import sys, os, json, math
import numpy as np
from itertools import permutations
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

sys.path.insert(0, os.path.dirname(__file__))
from reservoir import (WaveField, make_open_box, make_magnetron, coarse)

RNG = np.random.default_rng(7)


def run_and_snapshot(field, inject_pos, magnitudes, order, gap, delays, sigma=2.0):
    field.reset()
    for mag_idx in order:
        field.inject(inject_pos, amp=magnitudes[mag_idx], sigma=sigma)
        for _ in range(gap):
            field.step()
    snaps = {}
    checkpoints = set(delays)
    for s in range(1, max(delays) + 1):
        field.step()
        if s in checkpoints:
            snaps[s] = field.u.copy()
    return snaps


def forgetting_curve(make_field, inject_pos, delays, n_per_class=30, gap=16,
                     coarse_k=12, noise=0.02, sigma=2.0):
    orders = list(permutations(range(3)))
    mags0 = [1.0, 2.0, 3.0]
    X = {d: [] for d in delays}
    y = []
    for label, order in enumerate(orders):
        for _ in range(n_per_class):
            field = make_field()
            j = 1.0 + 0.03 * RNG.standard_normal()
            mags = [m * j for m in mags0]
            snaps = run_and_snapshot(field, inject_pos, mags, order, gap, delays, sigma)
            for d in delays:
                f = coarse(snaps[d].reshape(field.N, field.N), coarse_k)
                X[d].append(f + noise * RNG.standard_normal(coarse_k * coarse_k))
            y.append(label)
    y = np.array(y)
    accs = {}
    for d in delays:
        clf = LogisticRegression(max_iter=3000, C=1.0)
        accs[d] = float(cross_val_score(clf, np.array(X[d]), y, cv=5).mean())
    ysh = RNG.permutation(y)
    shuffle = float(cross_val_score(LogisticRegression(max_iter=3000),
                                    np.array(X[delays[0]]), ysh, cv=5).mean())
    return accs, shuffle


def fit_horizon(delays, accs, chance=1/6, hi=1.0):
    """Locate the delay where accuracy crosses the midpoint between hi and chance.
    Linear interpolation between bracketing points; returns (horizon, collapsed?)."""
    mid = (hi + chance) / 2.0
    ds = sorted(delays)
    a = [accs[d] for d in ds]
    cross = None
    for i in range(1, len(ds)):
        if a[i - 1] >= mid >= a[i]:
            frac = (a[i - 1] - mid) / (a[i - 1] - a[i] + 1e-12)
            cross = ds[i - 1] + frac * (ds[i] - ds[i - 1])
            break
    # collapsed iff we actually observed the curve cross the midpoint within range
    collapsed = cross is not None
    if cross is None:
        cross = ds[-1]  # lower bound: never crossed in range
    return cross, collapsed


def physical_time(step, c_sim=0.5, dt_sim=0.6, dx_sim=1.0,
                  cable_mm=1.0, grid_cells=64, wave_speed_m_s=0.5):
    """Map simulation steps to milliseconds via a dendritic calibration.

    We pin two physical anchors:
      - dx_phys: the grid spans `cable_mm` over `grid_cells` cells.
      - wave_speed_m_s: a representative dendritic wave / signal speed (~0.5 m/s
        is in the range reported for slow dendritic / unmyelinated propagation;
        this is a CALIBRATION CHOICE, stated openly, not a measurement).
    Then dt_phys follows from the simulation's own Courant relation:
        c_sim = wave_speed * dt_phys / dx_phys   ->   dt_phys = c_sim * dx_phys / wave_speed
    """
    dx_phys_m = (cable_mm * 1e-3) / grid_cells          # metres per cell
    dt_phys_s = c_sim * dx_phys_m / wave_speed_m_s       # seconds per step
    return step * dt_phys_s * 1e3                         # milliseconds


def main():
    N = 64
    chance = 1 / 6
    out = {"chance": chance, "N": N}

    insA, bA = make_open_box(N, width=16, bmax=1.5)
    insM, bM, cM = make_magnetron(N, sp_w=12, sp_max=1.5)

    # Open box: sweep until collapse
    box_delays = [8, 100, 300, 700, 1000, 1300, 1600, 2000]
    print("[open box] measuring forgetting curve ...")
    box_acc, box_shuf = forgetting_curve(lambda: WaveField(N, inside=insA, b=bA),
                                         (N // 2, N // 2), box_delays, n_per_class=30)
    for d in box_delays:
        print(f"  delay {d:5d} -> {box_acc[d]:.3f}")
    print(f"  shuffle {box_shuf:.3f}")

    # Cavity: sweep FAR (it holds much longer) until collapse
    cav_delays = [8, 1000, 4000, 8000, 14000, 22000, 32000, 45000]
    print("\n[magnetron cavity] measuring forgetting curve (extended range) ...")
    cav_acc, cav_shuf = forgetting_curve(lambda: WaveField(N, inside=insM, b=bM),
                                         cM, cav_delays, n_per_class=30)
    for d in cav_delays:
        print(f"  delay {d:5d} -> {cav_acc[d]:.3f}")
    print(f"  shuffle {cav_shuf:.3f}")

    box_h, box_collapsed = fit_horizon(box_delays, box_acc, chance)
    cav_h, cav_collapsed = fit_horizon(cav_delays, cav_acc, chance)

    out.update({
        "box": {"delays": box_delays, "acc": box_acc, "shuffle": box_shuf,
                "horizon_steps": box_h, "collapsed": box_collapsed},
        "cavity": {"delays": cav_delays, "acc": cav_acc, "shuffle": cav_shuf,
                   "horizon_steps": cav_h, "collapsed": cav_collapsed},
    })

    box_ms = physical_time(box_h)
    cav_ms = physical_time(cav_h)
    out["box"]["horizon_ms"] = box_ms
    out["cavity"]["horizon_ms"] = cav_ms
    out["gain"] = cav_h / box_h if box_h else None

    print("\n" + "=" * 60)
    print("HORIZON SUMMARY")
    print("=" * 60)
    print(f"open box : {box_h:7.0f} steps  ~ {box_ms:6.1f} ms   "
          f"({'collapsed' if box_collapsed else 'LOWER BOUND'})")
    print(f"cavity   : {cav_h:7.0f} steps  ~ {cav_ms:6.1f} ms   "
          f"({'collapsed' if cav_collapsed else 'LOWER BOUND'})")
    print(f"cavity / box horizon gain: {out['gain']:.1f}x")
    seconds_target = 1000.0
    loops = seconds_target / cav_ms if cav_ms else float('inf')
    out["loops_for_1s"] = loops
    print(f"\nTo reach a 1-second thought from a {cav_ms:.0f} ms cavity store,")
    print(f"you would need to re-circulate it ~{loops:.0f}x (nested-loop estimate).")

    with open(os.path.join(os.path.dirname(__file__), "..", "results", "horizon.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nsaved results/horizon.json")
    return out


if __name__ == "__main__":
    main()
