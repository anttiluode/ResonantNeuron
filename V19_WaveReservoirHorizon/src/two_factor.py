"""
two_factor.py - the experiment that can embarrass the cavity result.

The 40x cavity advantage from the horizon experiment is suspect: the cavity holds
memory partly just because it is nearly lossless (tiny outlet, reflecting walls).
A low-loss box holding a pattern a long time is not surprising and is not
"geometry computes". To separate the real effects we run a 2x2 design with
DISSIPATION MATCHED across all four conditions (same energy half-life), so no
condition can win just by leaking less:

                | uniform channels      | tuned channels (each satellite its own f0)
  ----------------------------------------------------------------------------------
  open box      | A: plain medium       | B: tuned medium, no cavity
  magnetron     | C: cavity, no tuning  | D: cavity + tuned compartments

Questions:
  - Does GEOMETRY (C,D vs A,B) extend the readable horizon once loss is matched?
    If not, the 40x was just low loss (El-Quessny lesson: bare shape can be inert).
  - Does CHANNEL TUNING (B,D vs A,C) extend it? This is the Snyder/Narayanan-Johnston
    mechanism: per-region resonance, not silhouette.
  - Do they interact (D special)?

Honest guardrails kept from earlier work:
  - same-point magnitude-order task (no "which site" cheat)
  - shuffle control pins chance
  - DISSIPATION MATCHED: each condition's global damping is scaled so a single
    pulse decays to the same energy half-life (measured, not assumed)
"""

import sys, os, json, math
import numpy as np
from itertools import permutations
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

sys.path.insert(0, os.path.dirname(__file__))
from reservoir import (WaveField, make_open_box, make_magnetron,
                       tuned_w0_field, sponge_edges, coarse, disk)

RNG = np.random.default_rng(11)


# --------------------------------------------------- dissipation matching

def energy_halflife(field, inject_pos, sigma=2.0, max_steps=20000):
    """Steps for a single pulse's energy to fall to half its peak. inf if it never does."""
    field.reset()
    field.inject(inject_pos, amp=1.0, sigma=sigma)
    peak = 0.0
    half = None
    for s in range(max_steps):
        field.step()
        e = field.energy()
        peak = max(peak, e)
        if half is None and e < peak / 2 and s > 20:
            half = s
            break
    return half if half is not None else float("inf")


def match_uniform_damping(make_field_with_buniform, inject_pos, target_half,
                          lo=0.0, hi=1.0, iters=22):
    """Bisection on a uniform interior damping level so the field's energy
    half-life equals target_half (in steps). Returns the damping level.
    More damping -> shorter half-life, so we search upward in damping to
    SHORTEN a half-life down to the (shared, fastest) target."""
    def half_for(level):
        fld = make_field_with_buniform(level)
        return energy_halflife(fld, inject_pos)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        h = half_for(mid)
        if h > target_half:   # too slow -> need more damping
            lo = mid
        else:                 # too fast -> need less damping
            hi = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------- task

def run_snapshots(field, inject_pos, magnitudes, order, gap, delays, sigma=2.0):
    field.reset()
    for mag_idx in order:
        field.inject(inject_pos, amp=magnitudes[mag_idx], sigma=sigma)
        for _ in range(gap):
            field.step()
    snaps = {}
    cps = set(delays)
    for s in range(1, max(delays) + 1):
        field.step()
        if s in cps:
            snaps[s] = field.u.copy()
    return snaps


def forgetting_curve(make_field, inject_pos, delays, n_per_class=24, gap=16,
                     ck=12, noise=0.02, sigma=2.0):
    orders = list(permutations(range(3)))
    mags0 = [1.0, 2.0, 3.0]
    X = {d: [] for d in delays}
    y = []
    for label, order in enumerate(orders):
        for _ in range(n_per_class):
            fld = make_field()
            j = 1.0 + 0.03 * RNG.standard_normal()
            mags = [m * j for m in mags0]
            snaps = run_snapshots(fld, inject_pos, mags, order, gap, delays, sigma)
            for d in delays:
                X[d].append(coarse(snaps[d].reshape(fld.N, fld.N), ck)
                            + noise * RNG.standard_normal(ck * ck))
            y.append(label)
    y = np.array(y)
    accs = {}
    for d in delays:
        accs[d] = float(cross_val_score(LogisticRegression(max_iter=2500),
                                        np.array(X[d]), y, cv=4).mean())
    ysh = RNG.permutation(y)
    shuf = float(cross_val_score(LogisticRegression(max_iter=2500),
                                 np.array(X[delays[0]]), ysh, cv=4).mean())
    return accs, shuf


def horizon(delays, accs, chance=1/6, hi=1.0):
    mid = (hi + chance) / 2
    ds = sorted(delays)
    a = [accs[d] for d in ds]
    for i in range(1, len(ds)):
        if a[i-1] >= mid >= a[i]:
            frac = (a[i-1]-mid)/(a[i-1]-a[i]+1e-12)
            return ds[i-1]+frac*(ds[i]-ds[i-1]), True
    return ds[-1], False   # lower bound, did not collapse


# --------------------------------------------------- main

def main():
    N = 64
    dt = 0.6
    chance = 1/6
    inj_box = (N//2, N//2)

    # geometries
    insBox = np.ones((N, N), bool)
    insMag, _, cMag, sats, rs = make_magnetron(N, return_sats=True)

    # tuned channel field: 8 satellites, frequencies spread across a band.
    # kept small (cycles/step) so w0*dt stays stable; the SPREAD is what matters.
    f0_list = np.linspace(0.02, 0.16, len(sats))
    w0_mag = tuned_w0_field(N, sats, rs, f0_list, dt)
    # for the open box we need a comparable "tuned medium": tile the same set of
    # resonant patches across the interior so tuning is present without a cavity.
    box_patch_centers = [(16, 16), (16, 32), (16, 48), (32, 16),
                         (32, 48), (48, 16), (48, 32), (48, 48)]
    w0_box = np.zeros((N, N))
    for ctr, f0 in zip(box_patch_centers, f0_list):
        w0_box[disk(N, ctr, rs)] = 2*np.pi*min(f0, 0.9/dt/(2*np.pi))

    # ---- dissipation matching ----
    # Geometry has its OWN intrinsic loss (edge sponge, radiation), so we can only
    # match by ADDING damping, i.e. we can only make conditions leak FASTER, never
    # slower. Therefore the target half-life must be the MINIMUM (fastest) across
    # conditions at zero added damping. We measure all four bare, take the min,
    # then damp every condition down to that shared half-life and VERIFY.
    print("[match] measuring bare half-lives (zero added damping) ...")
    inj_for = {"A": inj_box, "B": inj_box, "C": cMag, "D": cMag}
    specs = {
        "A": (insBox, None),
        "B": (insBox, w0_box),
        "C": (insMag, None),
        "D": (insMag, w0_mag),
    }

    def uniform_b(level, inside):
        return np.full((N, N), level) * inside

    def bare_field(name):
        inside, w0 = specs[name]
        return WaveField(N, dt=dt, inside=inside, b=uniform_b(0.0, inside), w0=w0)

    bare = {name: energy_halflife(bare_field(name), inj_for[name]) for name in specs}
    for name in specs:
        print(f"  {name}: bare half-life {bare[name]} steps")
    target_half = min(bare.values())
    print(f"  -> matching ALL conditions DOWN to {target_half} steps (the fastest)")

    levels = {}
    for name, (inside, w0) in specs.items():
        mk = lambda lvl, inside=inside, w0=w0: WaveField(
            N, dt=dt, inside=inside, b=uniform_b(lvl, inside), w0=w0)
        lvl = match_uniform_damping(mk, inj_for[name], target_half)
        h = energy_halflife(mk(lvl), inj_for[name])
        levels[name] = lvl
        ok = abs(h - target_half) <= max(8, 0.15 * target_half)
        print(f"  {name}: damping={lvl:.4f} -> half-life {h} (target {target_half}) "
              f"{'OK' if ok else 'MISMATCH'}")

    # ---- forgetting curves with matched dissipation ----
    delays = [8, 200, 400, 700, 1000, 1400, 1900]
    results = {}
    for name, (inside, w0) in specs.items():
        lvl = levels[name]
        mk = lambda inside=inside, w0=w0, lvl=lvl: WaveField(
            N, dt=dt, inside=inside, b=uniform_b(lvl, inside), w0=w0)
        accs, shuf = forgetting_curve(mk, inj_for[name], delays)
        h, collapsed = horizon(delays, accs, chance)
        results[name] = {"acc": accs, "shuffle": shuf, "horizon": h,
                         "collapsed": collapsed, "damping": lvl}
        tag = "collapsed" if collapsed else "LOWER BOUND"
        print(f"\n[{name}] " + {"A":"open box, uniform",
                                 "B":"open box, TUNED",
                                 "C":"cavity, uniform",
                                 "D":"cavity, TUNED"}[name])
        for d in delays:
            print(f"    delay {d:4d} -> {accs[d]:.3f}")
        print(f"    shuffle {shuf:.3f} | horizon {h:.0f} ({tag})")

    out = {"chance": chance, "target_half": target_half, "delays": delays,
           "f0_list": list(f0_list), "results": results}
    with open(os.path.join(os.path.dirname(__file__), "..", "results",
                           "two_factor.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    # ---- read the 2x2 ----
    hA, hB, hC, hD = (results[k]["horizon"] for k in "ABCD")
    print("\n" + "="*64)
    print("2x2 HORIZON TABLE (dissipation matched to half-life",
          target_half, "steps)")
    print("="*64)
    print(f"                 uniform      tuned")
    print(f"  open box       {hA:7.0f}    {hB:7.0f}")
    print(f"  magnetron      {hC:7.0f}    {hD:7.0f}")
    geom_effect = ((hC + hD) - (hA + hB)) / 2
    tune_effect = ((hB + hD) - (hA + hC)) / 2
    interaction = (hD - hC) - (hB - hA)
    print(f"\n  main effect GEOMETRY (cavity - box): {geom_effect:+.0f} steps")
    print(f"  main effect TUNING (tuned - uniform): {tune_effect:+.0f} steps")
    print(f"  interaction (tuning helps more in cavity): {interaction:+.0f} steps")
    print("="*64)
    print("Reading: with loss matched, a positive effect means that factor")
    print("genuinely extends readable memory beyond just-leaking-less.")
    return out


if __name__ == "__main__":
    main()
