"""
pde_xor.py -- does the REAL 2-D wave field reproduce the lumped model's XOR?

Bit encoding on the PDE: a satellite cavity is driven with a continuous
carrier  A * sin(Omega*t + phase_bit), phase_bit in {0, pi} for bit in {0,1}.
This is the direct PDE analogue of encode_bit() in delay_dendrite.py -- same
idea (phase carries the bit), but now the carrier physically propagates
through a channel of real length, at the real wave speed c, and interferes
with whatever else reaches the soma, instead of having its phase shift
algebraically injected.

Readout: after letting the field run past its transient and into steady
state, measure the RMS amplitude of u(t) at the soma centre over one
oscillation period. That is the PDE's "|soma|" -- the direct analogue of
ResonatorNeuron's |s|.

Test: drive two satellite dendrites with two bits, sweep one dendrite's
LENGTH (not an injected phase -- the actual channel length on the grid),
and see if the same XOR<->XNOR retuning from delay_dendrite.py appears.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from cavity_field import CavityField, build_geometry


def soma_rms_amplitude(field, soma_yx, forcing_fn, n_settle, n_measure,
                        measure_period_steps):
    """Run n_settle steps to let transients die out, then measure RMS of
    u at the soma centre over n_measure steps (should span >= 1 carrier
    period for a clean amplitude readout)."""
    field.run(n_settle, forcing_fn)
    sy, sx = soma_yx
    vals = []
    for _ in range(n_measure):
        field.run(1, forcing_fn)
        vals.append(field.u[sy, sx])
    return np.sqrt(np.mean(np.array(vals) ** 2))


def run_pde_unit(bit_a, bit_b, length_a, length_b, Omega=2 * np.pi * 0.10,
                  c=1.0, grid_size=140, soma_radius=14, satellite_radius=7,
                  drive_amp=3.0, damping=0.002, skew_deg=0.0,
                  n_settle=700, n_measure=200):
    """Build geometry with two satellite dendrites at given lengths, drive
    them with bit-encoded carriers, return soma RMS amplitude."""
    mask, soma_c, sat_cs, _ = build_geometry(
        grid_size=grid_size, soma_radius=soma_radius, n_satellites=2,
        satellite_radius=satellite_radius,
        satellite_lengths=[length_a, length_b],
        satellite_angles_deg=[0, 180], skew_deg=skew_deg)

    field = CavityField(mask, dx=1.0, c=c, damping=damping)
    sat0 = (int(sat_cs[0][0]), int(sat_cs[0][1]))
    sat1 = (int(sat_cs[1][0]), int(sat_cs[1][1]))
    soma_yx = (int(soma_c[0]), int(soma_c[1]))

    phase_a = np.pi * bit_a
    phase_b = np.pi * bit_b

    def forcing_fn(t):
        f = np.zeros_like(mask)
        f[sat0] += drive_amp * np.sin(Omega * t + phase_a)
        f[sat1] += drive_amp * np.sin(Omega * t + phase_b)
        return f

    period_steps = int(round((2 * np.pi / Omega) / field.dt))
    amp = soma_rms_amplitude(field, soma_yx, forcing_fn, n_settle,
                              max(n_measure, period_steps * 2),
                              period_steps)
    return amp


if __name__ == "__main__":
    print("=" * 78)
    print("PDE TEST 1: at MATCHED dendrite lengths, does the soma show")
    print("constructive vs destructive interference like the lumped XOR unit?")
    print("=" * 78)

    Omega = 2 * np.pi * 0.10
    c = 1.0
    L = 10.0  # matched lengths, both dendrites -- regime with good soma SNR

    print(f"\nOmega={Omega:.4f}, c={c}, matched length={L} for both dendrites.")
    print(f"{'a':>2} {'b':>2} | soma RMS amplitude")
    print("-" * 36)
    amps = {}
    for a in (0, 1):
        for b in (0, 1):
            amp = run_pde_unit(a, b, L, L, Omega=Omega, c=c)
            amps[(a, b)] = amp
            print(f" {a:2d} {b:2d} | {amp:8.4f}")

    # XOR predicts: agree (00,11) -> ONE amplitude regime, disagree (01,10) -> the other
    agree_amps = [amps[(0, 0)], amps[(1, 1)]]
    disagree_amps = [amps[(0, 1)], amps[(1, 0)]]
    print(f"\nAgree (00,11) mean amp:    {np.mean(agree_amps):.4f}  (spread {np.std(agree_amps):.4f})")
    print(f"Disagree (01,10) mean amp: {np.mean(disagree_amps):.4f}  (spread {np.std(disagree_amps):.4f})")

    separable = abs(np.mean(agree_amps) - np.mean(disagree_amps)) > (np.std(agree_amps) + np.std(disagree_amps) + 1e-9)
    print(f"\nClean separation between agree/disagree groups: {separable}")
    if np.mean(agree_amps) > np.mean(disagree_amps):
        print("-> matched lengths give XNOR-like behavior (agree = louder)")
    else:
        print("-> matched lengths give XOR-like behavior (disagree = louder)")
