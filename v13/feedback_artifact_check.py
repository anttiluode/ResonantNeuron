"""Why did backward get MORE boost (24.6x) than forward (14.3x)? Check
whether this is about chain ORDER / geometry asymmetry: driving from soma
means the FIRST relay point hit is chain[-1] (closest to soma), and the
chain fires forward (toward soma) from there -- so a backward-driven wave
hits the relay nearest the soma FIRST, gets immediately amplified and
RE-INJECTED forward (right back toward the soma, which is what we're
measuring!), creating a short feedback loop that pads the 'backward'
reading. This would be a measurement artifact of relay placement, not a
real physical effect worth reporting as if it were.
"""
import numpy as np
from cavity_field import CavityField, build_geometry
from cavity_field import CavityField, build_geometry

class RefractoryGatedField(CavityField):
    """A chain of refractory relay points along a line. Each point: if its
    local field amplitude exceeds threshold AND it is not refractory, it
    fires -- writing a fixed pulse to the NEXT point in the chain (and not
    the previous one) -- then enters a refractory window during which it
    cannot fire again."""
    def __init__(self, mask, relay_chain, threshold=0.05, gain=3.0,
                 refractory_steps=15, **kwargs):
        super().__init__(mask, **kwargs)
        self.relay_chain = relay_chain
        self.threshold = threshold
        self.gain = gain
        self.refractory_steps = refractory_steps
        self.refractory_timer = [0] * len(relay_chain)

    def step(self, forcing=None):
        u_next = super().step(forcing)
        for i in range(len(self.relay_chain) - 1):
            if self.refractory_timer[i] > 0:
                self.refractory_timer[i] -= 1
                continue
            here = self.relay_chain[i]
            nxt = self.relay_chain[i + 1]
            if abs(self.u[here]) > self.threshold:
                self.u[nxt] = self.gain * np.sign(self.u[here])
                self.refractory_timer[i] = self.refractory_steps
        return self.u


def build_chain(soma_c, sat_yx, n_relay_points=6, frac_start=0.15, frac_end=0.85):
    cy, cx = soma_c
    sy, sx = sat_yx
    chain = []
    for k in range(n_relay_points):
        frac = frac_start + (frac_end - frac_start) * k / (n_relay_points - 1)
        px = cx + frac * (sx - cx)
        chain.append((int(cy), int(px)))
    return chain

L = 15
Omega = 2*np.pi*0.10
mask, soma_c, sat_cs, _ = build_geometry(
    grid_size=140, soma_radius=14, n_satellites=1, satellite_radius=7,
    satellite_lengths=[L], satellite_angles_deg=[0], skew_deg=0.0)
sat_yx = (int(sat_cs[0][0]), int(sat_cs[0][1]))
soma_yx = (int(soma_c[0]), int(soma_c[1]))
chain = build_chain(soma_c, sat_yx, n_relay_points=6)
print(f"chain: {chain}")
print(f"soma_yx: {soma_yx}, sat_yx: {sat_yx}")
print(f"chain[-1] (closest to soma, fires INTO soma): {chain[-1]}")
print(f"measure point when driving backward (=sat_yx): {sat_yx}")
print(f"\nThe relay nearest the soma (chain[-1]) has NO downstream target in")
print(f"the chain (it's the last link) -- so when the backward-driven wave")
print(f"reaches it first, what does the relay do? Let's check if chain[-1]")
print(f"even fires (it has no 'i+1' partner in the loop range(len-1)).")
print(f"\nLooking at RefractoryGatedField.step(): loop is range(len(chain)-1),")
print(f"so chain[-1] is NEVER a trigger point -- only chain[0..4] can fire.")
print(f"That means when driving from soma, the wave must travel ALL THE WAY")
print(f"to chain[0] (near satellite) before the relay does anything at all --")
print(f"so the 24.6x 'backward boost' must be coming from somewhere else.")
print(f"\nLet's just watch raw amplitude at the measure point over time for")
print(f"the backward-driven relay case, to see what's actually happening.")

field = RefractoryGatedField(mask, chain, threshold=0.05, gain=3.0,
                              refractory_steps=15, dx=1.0, c=1.0, damping=0.001)
def drive_soma(t):
    f = np.zeros_like(mask); f[soma_yx] += 15.0*np.sin(Omega*t); return f
field.run(900, drive_soma)
vals = []
for _ in range(60):
    field.run(1, drive_soma)
    vals.append(field.u[sat_yx])
print(f"\nFirst 60 samples of u[sat_yx] after settling (backward-driven):")
print(np.array(vals).round(3))
