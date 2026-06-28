"""Corrected version: properly isolate the relay's directional effect by
comparing FOUR conditions, not two -- the earlier ratio conflated 'relay
present but reading wrong side' with 'no relay at all'.
"""
import numpy as np
from cavity_field import CavityField, build_geometry
from cavity_field import CavityField, build_geometry

class GatedCavityField(CavityField):
    """Adds a one-way relay: forces the field at write_point to track the
    field at read_point with a fixed gain, every step, ONLY in that
    direction (the read point's own dynamics are untouched)."""
    def __init__(self, mask, read_point, write_point, threshold=0.05,
                 gain=1.0, **kwargs):
        super().__init__(mask, **kwargs)
        self.read_point = read_point
        self.write_point = write_point
        self.threshold = threshold
        self.gain = gain

    def step(self, forcing=None):
        u_next = super().step(forcing)
        val = self.u[self.read_point]
        if abs(val) > self.threshold:
            self.u[self.write_point] = self.gain * val
        return self.u

L = 15
Omega = 2*np.pi*0.10
mask, soma_c, sat_cs, _ = build_geometry(
    grid_size=140, soma_radius=14, n_satellites=1, satellite_radius=7,
    satellite_lengths=[L], satellite_angles_deg=[0], skew_deg=0.0)
sat_yx = (int(sat_cs[0][0]), int(sat_cs[0][1]))
soma_yx = (int(soma_c[0]), int(soma_c[1]))
cy, cx = soma_c
relay_read = (int(cy), int(cx + 14 + L*0.3))   # closer to satellite
relay_write = (int(cy), int(cx + 14 + L*0.7))  # closer to soma

def run_trans(drive_point, measure_point, use_relay):
    if use_relay:
        field = GatedCavityField(mask, relay_read, relay_write, threshold=0.02,
                                  gain=1.0, dx=1.0, c=1.0, damping=0.001)
    else:
        field = CavityField(mask, dx=1.0, c=1.0, damping=0.001)
    def drive(t):
        f = np.zeros_like(mask); f[drive_point] += 15.0*np.sin(Omega*t); return f
    field.run(900, drive)
    vals = []
    for _ in range(300):
        field.run(1, drive); vals.append(field.u[measure_point])
    return np.sqrt(np.mean(np.array(vals)**2))

print("="*78)
print("FOUR-WAY COMPARISON: passive vs relay, forward vs backward")
print("="*78)
print("\n(relay reads near satellite-side, writes near soma-side, by construction)\n")

passive_fwd = run_trans(sat_yx, soma_yx, use_relay=False)
relay_fwd   = run_trans(sat_yx, soma_yx, use_relay=True)
passive_bwd = run_trans(soma_yx, sat_yx, use_relay=False)
relay_bwd   = run_trans(soma_yx, sat_yx, use_relay=True)

print(f"  passive, forward  (sat->soma): {passive_fwd:.5f}")
print(f"  relay,   forward  (sat->soma): {relay_fwd:.5f}   (relay reads the driven side)")
print(f"  passive, backward (soma->sat): {passive_bwd:.5f}")
print(f"  relay,   backward (soma->sat): {relay_bwd:.5f}   (relay's READ side is now the UNDRIVEN side)")

print(f"\n  Forward boost from relay:  {relay_fwd/passive_fwd:.3f}x")
print(f"  Backward boost from relay: {relay_bwd/passive_bwd:.3f}x")
print(f"\n  TRUE DIRECTIONALITY RATIO (relay_fwd/passive_fwd) / (relay_bwd/passive_bwd):")
print(f"  = {(relay_fwd/passive_fwd) / (relay_bwd/passive_bwd):.3f}")
print("\n  If the relay is genuinely one-way, this ratio should be >> 1: the relay")
print("  should meaningfully boost transmission when driven from the side it")
print("  reads, and do little/nothing when driven from the side it only writes to.")
