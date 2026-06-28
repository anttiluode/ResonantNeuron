"""Candidate explanation for the lopsided, non-cosine transition: the
channel + satellite cavity is a TWO-PORT system (driven at the far end,
loaded by the soma at the near end), not a one-way delay line. Reflections
off the soma cavity travel BACK down the channel and interfere with the
forward-going wave, creating a standing-wave pattern inside the channel
itself whose node/antinode structure depends on channel length in a way
that is NOT simply "delay the phase by Omega*L/c" -- that formula assumes
a one-way, non-reflecting line, which a real bounded cavity is not.

Quick check: does the wave amplitude AT THE MIDPOINT of the channel show
length-dependent standing-wave structure, confirming reflections are
present and shaping the result (rather than pure one-way propagation)?
"""
import numpy as np
from cavity_field import CavityField, build_geometry

Omega = 2*np.pi*0.02
c = 1.0

print("Checking for standing-wave structure (reflection signature) inside")
print("the channel itself, at several channel lengths:\n")

for L in [10, 20, 30, 35]:
    mask, soma_c, sat_cs, _ = build_geometry(
        grid_size=140, soma_radius=14, n_satellites=1, satellite_radius=7,
        satellite_lengths=[L], satellite_angles_deg=[0], skew_deg=0.0)
    field = CavityField(mask, dx=1.0, c=c, damping=0.001)
    sat0 = (int(sat_cs[0][0]), int(sat_cs[0][1]))
    soma_yx = (int(soma_c[0]), int(soma_c[1]))
    cy, cx = soma_c
    mid_x = int(cx + (L/2))  # approx midpoint of the channel (angle=0, along +x)
    mid_yx = (int(cy), mid_x)

    def forcing_fn(t):
        f = np.zeros_like(mask)
        f[sat0] += 15.0*np.sin(Omega*t)
        return f

    field.run(1000, forcing_fn)
    vals_mid, vals_soma, vals_sat = [], [], []
    for _ in range(300):
        field.run(1, forcing_fn)
        vals_mid.append(field.u[mid_yx])
        vals_soma.append(field.u[soma_yx])
        vals_sat.append(field.u[sat0])
    rms_mid = np.sqrt(np.mean(np.array(vals_mid)**2))
    rms_soma = np.sqrt(np.mean(np.array(vals_soma)**2))
    rms_sat = np.sqrt(np.mean(np.array(vals_sat)**2))
    print(f"  L={L:3d}: sat_drive_rms={rms_sat:.4f}  mid_channel_rms={rms_mid:.5f}  soma_rms={rms_soma:.5f}")
