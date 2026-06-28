"""
test_skew_reciprocity.py -- Grok's writeup claims "the skew coupling already
gives directed circulation in the dendrite ring." Test this directly on the
actual v12 PDE: does a channel built at nonzero skew_deg transmit a wave
differently forward (satellite -> soma) than backward (soma -> satellite)?

The wave equation being solved, u_tt = c^2*lap(u) - gamma*u_t, is LINEAR and
TIME-REVERSAL SYMMETRIC in its spatial operator. A straight channel, however
it's angled when drawn, has no built-in mechanism to prefer one direction --
reciprocity (same transmission either way) is the expected default unless
something explicitly breaks it (e.g. a one-way valve, a nonlinearity, or an
asymmetric damping profile). This script measures it rather than assumes it.
"""
import numpy as np
from cavity_field import CavityField, build_geometry

def measure_transmission(L, skew_deg, Omega, drive_amp=15.0, damping=0.001,
                          n_settle=900, n_measure=300):
    """Drive ONE end of a single dendrite channel, measure RMS amplitude
    at the OTHER end, for both directions of driving."""
    mask, soma_c, sat_cs, _ = build_geometry(
        grid_size=140, soma_radius=14, n_satellites=1, satellite_radius=7,
        satellite_lengths=[L], satellite_angles_deg=[0], skew_deg=skew_deg)
    sat_yx = (int(sat_cs[0][0]), int(sat_cs[0][1]))
    soma_yx = (int(soma_c[0]), int(soma_c[1]))

    # forward: drive at satellite, read at soma
    field_fwd = CavityField(mask, dx=1.0, c=1.0, damping=damping)
    def drive_sat(t):
        f = np.zeros_like(mask); f[sat_yx] += drive_amp*np.sin(Omega*t); return f
    field_fwd.run(n_settle, drive_sat)
    vals = []
    for _ in range(n_measure):
        field_fwd.run(1, drive_sat); vals.append(field_fwd.u[soma_yx])
    fwd_amp = np.sqrt(np.mean(np.array(vals)**2))

    # backward: drive at soma, read at satellite (SAME mask, same channel)
    field_bwd = CavityField(mask, dx=1.0, c=1.0, damping=damping)
    def drive_soma(t):
        f = np.zeros_like(mask); f[soma_yx] += drive_amp*np.sin(Omega*t); return f
    field_bwd.run(n_settle, drive_soma)
    vals = []
    for _ in range(n_measure):
        field_bwd.run(1, drive_soma); vals.append(field_bwd.u[sat_yx])
    bwd_amp = np.sqrt(np.mean(np.array(vals)**2))

    return fwd_amp, bwd_amp


if __name__ == "__main__":
    print("="*78)
    print("DOES skew_deg (the angled-cavity geometry) PRODUCE DIRECTIONAL")
    print("(non-reciprocal) TRANSMISSION, as Grok's writeup assumed?")
    print("="*78)
    Omega = 2*np.pi*0.10
    L = 15.0
    print(f"\nOmega={Omega:.4f}, channel length={L}, testing several skew angles:\n")
    print(f"{'skew_deg':>9} | {'fwd (sat->soma)':>16} | {'bwd (soma->sat)':>16} | {'ratio fwd/bwd':>14}")
    print("-"*70)
    for skew in [0, 15, 30, 45, 60]:
        fwd, bwd = measure_transmission(L, skew, Omega)
        ratio = fwd / (bwd + 1e-12)
        print(f"{skew:9.0f} | {fwd:16.5f} | {bwd:16.5f} | {ratio:14.4f}")

    print("\nIf this is a passive linear wave equation (no valve, no nonlinearity,")
    print("no asymmetric damping), reciprocity (ratio ~= 1.0 at every skew angle)")
    print("is the physically correct expectation -- a straight channel transmits")
    print("identically in both directions no matter what angle it's drawn at,")
    print("the same way two-terminal passive linear circuits are reciprocal.")
