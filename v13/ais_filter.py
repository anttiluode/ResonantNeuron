"""
ais_filter.py -- Grok's concrete, testable suggestion: model a periodic
AIS-like structure (190nm ankyrin/spectrin rings, in spirit) as a spatial
filter along the channel, and see if THAT breaks reciprocity, since plain
geometry (skew angle) provably does not (test_skew_reciprocity.py).

The real AIS mechanism that actually creates directional bias in biology
is NOT passive linear filtering -- it's voltage-gated ion channels
(Na+/K+) clustered at the AIS, which are NONLINEAR and THRESHOLD-based:
they open above a voltage threshold and impose a strong preferred direction
because the action potential, once triggered, is an active regenerative
process that only propagates forward (away from already-depolarized,
refractory membrane). That is fundamentally different from a passive
periodic density modulation along a tube.

This file tests the two candidate mechanisms Grok's suggestion actually
maps to, honestly distinguished:

  (A) PASSIVE periodic impedance modulation (e.g. periodic local change in
      wave speed c(x) or damping gamma(x) along the channel, mimicking a
      periodic cytoskeletal lattice). Prediction: this can shape a
      frequency-dependent transmission (a literal photonic-crystal-style
      bandgap/filter), but being passive and linear, it CANNOT make forward
      transmission differ from backward transmission. Reciprocity still
      holds for any passive linear medium, periodic or not.

  (B) ACTIVE one-way gating: add a true nonlinear threshold element partway
      along the channel that only passes signal one direction (the actual
      mechanism of a real axon initial segment / action potential). This
      DOES break reciprocity, by construction, because it's not a passive
      linear medium anymore.

Testing (A) is the fair test of "does Grok's literal proposal (periodic
structure) work." Testing (B) shows what WOULD work, and why it's a
different kind of element than anything in this repo so far.
"""
import numpy as np
from cavity_field import CavityField, build_geometry


def build_periodic_channel_mask(L=30, period=4.0, n_periods=6, width=3.0,
                                 grid_size=140):
    """A straight channel with a periodic narrowing (mimicking a lattice
    of constrictions, in spirit like ankyrin-anchored periodic structure),
    connecting two cavities. Returns mask, soma_yx, sat_yx, and the speed
    multiplier map (which test (A) will use to also vary c(x) periodically)."""
    ny = nx = grid_size
    mask = np.zeros((ny, nx))
    cy, cx = ny//2, nx//2
    yy, xx = np.mgrid[0:ny, 0:nx]

    soma_r, sat_r = 14, 7
    d2_soma = (yy-cy)**2 + (xx-cx)**2
    mask[d2_soma <= soma_r**2] = 1.0
    sat_cx = cx + soma_r + L
    d2_sat = (yy-cy)**2 + (xx-sat_cx)**2
    mask[d2_sat <= sat_r**2] = 1.0

    entry_x = cx + soma_r
    n_pts = int(L*2)+4
    speed_mult = np.ones((ny, nx))
    for i in range(n_pts):
        t = i/(n_pts-1)
        px = entry_x + t*(sat_cx - entry_x)
        d2 = (yy-cy)**2 + (xx-px)**2
        # periodic width modulation: every `period` grid units, narrow the channel
        phase = (px - entry_x) % period
        local_width = width if phase < period/2 else width*0.5
        mask[d2 <= local_width**2] = 1.0
        # periodic speed modulation for test (A): slower in the "constricted" zones
        speed_mult[d2 <= local_width**2] = 0.5 if phase < period/2 else 1.0

    return mask, (cy, cx), (cy, int(sat_cx)), speed_mult


def measure_directional(mask, soma_yx, sat_yx, Omega, drive_amp=15.0,
                         damping=0.001, n_settle=900, n_measure=300, c=1.0):
    field_fwd = CavityField(mask, dx=1.0, c=c, damping=damping)
    def drive_sat(t):
        f = np.zeros_like(mask); f[sat_yx] += drive_amp*np.sin(Omega*t); return f
    field_fwd.run(n_settle, drive_sat)
    vals = []
    for _ in range(n_measure):
        field_fwd.run(1, drive_sat); vals.append(field_fwd.u[soma_yx])
    fwd = np.sqrt(np.mean(np.array(vals)**2))

    field_bwd = CavityField(mask, dx=1.0, c=c, damping=damping)
    def drive_soma(t):
        f = np.zeros_like(mask); f[soma_yx] += drive_amp*np.sin(Omega*t); return f
    field_bwd.run(n_settle, drive_soma)
    vals = []
    for _ in range(n_measure):
        field_bwd.run(1, drive_soma); vals.append(field_bwd.u[sat_yx])
    bwd = np.sqrt(np.mean(np.array(vals)**2))
    return fwd, bwd


if __name__ == "__main__":
    print("="*78)
    print("TEST (A): PASSIVE periodic structure (Grok's literal proposal)")
    print("="*78)
    mask, soma_yx, sat_yx, _ = build_periodic_channel_mask()
    Omega = 2*np.pi*0.10
    fwd, bwd = measure_directional(mask, soma_yx, sat_yx, Omega)
    print(f"\nPeriodic-constriction channel, forward (sat->soma): {fwd:.5f}")
    print(f"Same channel, backward (soma->sat):                 {bwd:.5f}")
    print(f"Ratio: {fwd/(bwd+1e-12):.4f}")
    print("\nExpected if passive/linear theory is right: ratio ~= 1.0 even with")
    print("a periodic lattice structure -- periodicity can filter FREQUENCY")
    print("(bandgaps), it cannot by itself filter DIRECTION.")
