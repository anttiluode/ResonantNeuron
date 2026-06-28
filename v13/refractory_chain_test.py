"""
true_directional_gate.py -- diagnosis from nonlinear_gate_test_2.py: a relay
that reads SCALAR AMPLITUDE at a point cannot distinguish which direction a
wave arrived from -- amplitude has no direction information once the wave
has passed through. A real action potential's directionality comes from
something more specific: the REFRACTORY period. After firing, the membrane
just behind the spike is briefly unable to fire again, which is what
prevents the spike from propagating backward into already-fired territory
-- forward propagation continues into fresh (unfired) membrane, backward
propagation dies because that membrane just fired and is refractory.

This is the actual mechanism, modeled honestly: a one-way relay needs not
just a threshold, but a REFRACTORY STATE that blocks re-triggering for a
short window after firing. Test whether THIS additional ingredient (not
present in the naive relay) is what creates genuine directionality.
"""
import numpy as np
from cavity_field import CavityField, build_geometry

class RefractoryGatedField(CavityField):
    """A chain of refractory relay points along a line. Each point: if its
    local field amplitude exceeds threshold AND it is not refractory, it
    fires -- writing a fixed pulse to the NEXT point in the chain (and not
    the previous one) -- then enters a refractory window during which it
    cannot fire again. This is the minimal model of regenerative,
    direction-selective propagation (the actual AP mechanism), as opposed
    to the bidirectional point-amplitude relay tested previously.
    """
    def __init__(self, mask, relay_chain, threshold=0.05, gain=3.0,
                 refractory_steps=15, **kwargs):
        super().__init__(mask, **kwargs)
        self.relay_chain = relay_chain  # ordered list of (y,x), defines FORWARD direction
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
                # fire forward only: push a fresh pulse to the NEXT point
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


def measure(mask, soma_yx, sat_yx, chain_sat_to_soma, drive_point, measure_point,
            Omega, use_relay, drive_amp=15.0, damping=0.001,
            n_settle=900, n_measure=300):
    if use_relay:
        field = RefractoryGatedField(mask, chain_sat_to_soma, threshold=0.05,
                                      gain=3.0, refractory_steps=15,
                                      dx=1.0, c=1.0, damping=damping)
    else:
        field = CavityField(mask, dx=1.0, c=1.0, damping=damping)
    def drive(t):
        f = np.zeros_like(mask); f[drive_point] += drive_amp*np.sin(Omega*t); return f
    field.run(n_settle, drive)
    vals = []
    for _ in range(n_measure):
        field.run(1, drive); vals.append(field.u[measure_point])
    return np.sqrt(np.mean(np.array(vals)**2))


if __name__ == "__main__":
    print("="*78)
    print("TRUE ONE-WAY GATE: a chain of refractory relays (the actual AP")
    print("mechanism) -- does THIS break reciprocity, where the naive")
    print("amplitude-threshold relay (nonlinear_gate_test.py) did not?")
    print("="*78)

    L = 15
    Omega = 2*np.pi*0.10
    mask, soma_c, sat_cs, _ = build_geometry(
        grid_size=140, soma_radius=14, n_satellites=1, satellite_radius=7,
        satellite_lengths=[L], satellite_angles_deg=[0], skew_deg=0.0)
    sat_yx = (int(sat_cs[0][0]), int(sat_cs[0][1]))
    soma_yx = (int(soma_c[0]), int(soma_c[1]))

    # chain defined sat -> soma direction (this IS "forward" by construction)
    chain = build_chain(soma_c, sat_yx, n_relay_points=6)
    print(f"\nRelay chain (satellite -> soma order): {chain}")

    passive_fwd = measure(mask, soma_yx, sat_yx, chain, sat_yx, soma_yx, Omega, use_relay=False)
    relay_fwd   = measure(mask, soma_yx, sat_yx, chain, sat_yx, soma_yx, Omega, use_relay=True)
    passive_bwd = measure(mask, soma_yx, sat_yx, chain, soma_yx, sat_yx, Omega, use_relay=False)
    relay_bwd   = measure(mask, soma_yx, sat_yx, chain, soma_yx, sat_yx, Omega, use_relay=True)

    print(f"\n  passive, forward  (sat->soma): {passive_fwd:.5f}")
    print(f"  relay,   forward  (sat->soma): {relay_fwd:.5f}")
    print(f"  passive, backward (soma->sat): {passive_bwd:.5f}")
    print(f"  relay,   backward (soma->sat): {relay_bwd:.5f}")

    fwd_boost = relay_fwd / passive_fwd
    bwd_boost = relay_bwd / passive_bwd
    directionality = fwd_boost / bwd_boost
    print(f"\n  Forward boost:  {fwd_boost:.3f}x")
    print(f"  Backward boost: {bwd_boost:.3f}x")
    print(f"  Directionality ratio: {directionality:.3f}")
    print(f"\n  VERDICT: refractory chain {'DOES' if directionality > 2.0 else 'DOES NOT'} "
          f"produce meaningfully directional transmission.")
