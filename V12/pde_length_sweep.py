"""
pde_length_sweep.py -- THE central test. delay_dendrite.py (the lumped model)
claimed: sweeping one dendrite's length over one wavelength retunes a fixed
unit continuously between XOR and XNOR, with a literal zero-margin wall at
each quarter-wavelength mismatch. Does the REAL 2-D wave field do the same
thing when the "length" is an actual channel length on the grid -- the wave
physically travelling further, accumulating real propagation delay, not an
injected algebraic phase?

This is the test that decides whether v11's parity-wall result is a fact
about wave physics, or an artifact of the lumped ODE's simplifications.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from cavity_field import CavityField, build_geometry


def measure_unit(length_a, length_b, Omega, c=1.0, drive_amp=3.0,
                  damping=0.002, grid_size=140, soma_radius=14,
                  satellite_radius=7, n_settle=700, n_measure=200):
    """Return soma RMS amplitude for all 4 bit combinations at given lengths."""
    amps = {}
    for bit_a in (0, 1):
        for bit_b in (0, 1):
            mask, soma_c, sat_cs, _ = build_geometry(
                grid_size=grid_size, soma_radius=soma_radius, n_satellites=2,
                satellite_radius=satellite_radius,
                satellite_lengths=[length_a, length_b],
                satellite_angles_deg=[0, 180], skew_deg=0.0)
            field = CavityField(mask, dx=1.0, c=c, damping=damping)
            sat0 = (int(sat_cs[0][0]), int(sat_cs[0][1]))
            sat1 = (int(sat_cs[1][0]), int(sat_cs[1][1]))
            soma_yx = (int(soma_c[0]), int(soma_c[1]))
            phase_a, phase_b = np.pi * bit_a, np.pi * bit_b

            def forcing_fn(t, pa=phase_a, pb=phase_b, s0=sat0, s1=sat1):
                f = np.zeros_like(mask)
                f[s0] += drive_amp * np.sin(Omega * t + pa)
                f[s1] += drive_amp * np.sin(Omega * t + pb)
                return f

            field.run(n_settle, forcing_fn)
            vals = []
            for _ in range(n_measure):
                field.run(1, forcing_fn)
                vals.append(field.u[soma_yx])
            amps[(bit_a, bit_b)] = np.sqrt(np.mean(np.array(vals) ** 2))
    return amps


def classify(amps, tol_ratio=0.15):
    """Classify the 4-amplitude pattern as XOR-like, XNOR-like, or
    degenerate (no clean separation), same logic as identify_function
    in delay_dendrite.py but operating on noisy PDE measurements."""
    agree = (amps[(0, 0)] + amps[(1, 1)]) / 2
    disagree = (amps[(0, 1)] + amps[(1, 0)]) / 2
    scale = max(agree, disagree, 1e-9)
    if abs(agree - disagree) / scale < tol_ratio:
        return "DEGENERATE/WALL", agree, disagree
    elif agree > disagree:
        return "XNOR-like (agree louder)", agree, disagree
    else:
        return "XOR-like (disagree louder)", agree, disagree


if __name__ == "__main__":
    print("=" * 78)
    print("PDE LENGTH SWEEP: does real channel length retune XOR<->XNOR,")
    print("the way the lumped ODE model (delay_dendrite.py) predicted?")
    print("=" * 78)

    Omega = 2 * np.pi * 0.10
    c = 1.0
    # wavelength of the carrier at speed c: lambda = 2*pi*c/Omega
    wavelength = 2 * np.pi * c / Omega
    print(f"\nCarrier wavelength = {wavelength:.2f} grid units (Omega={Omega:.4f}, c={c})")
    print(f"Holding dendrite A fixed at length=10, sweeping dendrite B's")
    print(f"actual channel length across one wavelength.\n")

    La = 10.0
    # sweep B across one wavelength relative to A; coarse because each point
    # is a full PDE run (4 bit combos x settle+measure)
    Lb_values = La + np.linspace(0, wavelength, 9)

    print(f"{'L_b':>7} {'mismatch':>9} | {'00':>7} {'01':>7} {'10':>7} {'11':>7} | regime")
    print("-" * 80)
    results = []
    for Lb in Lb_values:
        amps = measure_unit(La, Lb, Omega, c=c)
        regime, agree, disagree = classify(amps)
        results.append((Lb, amps, regime))
        mismatch = Lb - La
        print(f"{Lb:7.2f} {mismatch:9.2f} | {amps[(0,0)]:7.4f} {amps[(0,1)]:7.4f} "
              f"{amps[(1,0)]:7.4f} {amps[(1,1)]:7.4f} | {regime}")

    regimes = [r[2] for r in results]
    distinct = set(r.split(" ")[0] for r in regimes)
    print(f"\nDistinct regimes encountered: {sorted(distinct)}")

    has_xor = any("XOR-like" in r for r in regimes)
    has_xnor = any("XNOR-like" in r for r in regimes)
    print(f"\nXOR-like regime appeared:  {has_xor}")
    print(f"XNOR-like regime appeared: {has_xnor}")
    print(f"\nVERDICT: real 2-D wave field on the angled-cavity geometry "
          f"{'CONFIRMS' if (has_xor and has_xnor) else 'DOES NOT CONFIRM'} "
          f"the lumped model's length->XOR/XNOR retuning claim.")
