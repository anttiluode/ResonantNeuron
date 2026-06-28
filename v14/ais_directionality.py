"""
ais_directionality.py -- the v14 capstone. Now that propagating_spike.py
established that an excitable line with an inactivation wake propagates
directionally (and that counter-pulses annihilate rather than pass through),
this file answers the ORIGINAL question that v13's four attempts could not:

  Does origination at a localized AIS site send a spike preferentially
  toward the axon, and refuse to back-propagate into the dendrite?

The setup mirrors Leterrier's account directly:
  - A 1-D excitable cable (the neuron's axis), cells 0..N-1.
  - Cell 0..D = the DENDRITE/soma side (lower Nav density -> higher
    threshold, harder to excite, as in real dendrites).
  - Cell A = the AIS: a localized zone of HIGH excitability (low threshold),
    modelling the ~30x Nav concentration Leterrier describes.
  - Cell A+1..N-1 = the AXON (normal excitability).

Two tests:
  (1) Drive the AIS to threshold. Does the spike propagate INTO THE AXON
      (forward) and also back into the dendrite (backward)? Measure how far
      each way. The real AIS sends it forward; the question is whether the
      excitability gradient (high at AIS, lower in dendrite) biases this.
  (2) Drive the DENDRITE (distal) end subthreshold-for-dendrite but check
      whether it can even reach and trigger the AIS -- i.e. does the
      excitability structure make the AIS the natural ORIGINATION point
      rather than just a relay.

This is the honest test. We are NOT claiming the spike magically only goes
one way -- real back-propagating action potentials (bAPs) DO invade
dendrites, as Leterrier notes ("bAPs do flow backwards... but it's
regulated and often attenuated"). The测 measurable claim is ATTENUATION:
forward propagation into the axon is sustained, backward propagation into
the higher-threshold dendrite is attenuated. That is what the biology says,
and it is a falsifiable, quantitative prediction.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from propagating_spike import ExcitableLine


class GradientExcitableLine(ExcitableLine):
    """Excitable line with a position-dependent excitability: a parameter
    `a_profile` per cell sets local threshold. Lower a -> more excitable
    (AIS); higher a -> less excitable (dendrite). This is the minimal way
    to encode Leterrier's Nav-density gradient (high at AIS, low in
    dendrites) into the FitzHugh-Nagumo `a` parameter."""

    def __init__(self, n=160, a_profile=None, **kwargs):
        super().__init__(n=n, **kwargs)
        if a_profile is None:
            a_profile = np.full(n, 0.7)
        self.a_profile = np.asarray(a_profile, float)

    def step(self, I_ext=None):
        I = I_ext if I_ext is not None else np.zeros(self.n)
        lap = self.laplacian(self.v)
        dv = self.v - self.v ** 3 / 3 - self.w + self.D * lap + I
        dw = self.eps * (self.v + self.a_profile - self.b * self.w)
        self.v = self.v + self.dt * dv
        self.w = self.w + self.dt * dw
        self.history.append(self.v.copy())
        return self.v


def build_neuron_profile(n=160, dend_end=60, ais_center=65, ais_width=6,
                          a_dendrite=1.3, a_ais=0.5, a_axon=0.7):
    """Build the excitability profile along the neuron axis.
    a is the FHN offset: HIGHER a = harder to excite (dendrite),
    LOWER a = easier (AIS). axon is intermediate (normal)."""
    a = np.full(n, a_axon)
    a[:dend_end] = a_dendrite                  # dendrite: hard to excite
    lo = max(ais_center - ais_width // 2, 0)
    hi = min(ais_center + ais_width // 2, n)
    a[lo:hi] = a_ais                            # AIS: very easy to excite
    return a, lo, hi


def measure_spread(line, kick_cell, kick_strength=12.0, kick_dur=6,
                    n_run=900, threshold=0.5):
    """Kick one cell and measure how far excitation spreads LEFT and RIGHT
    of the kick point over the run."""
    for _ in range(150):
        line.step()  # settle
    for t in range(kick_dur + 30):
        I = None
        if t < kick_dur:
            I = np.zeros(line.n); I[kick_cell] = kick_strength
        line.step(I)
    leftmost = kick_cell
    rightmost = kick_cell
    for _ in range(n_run):
        line.step()
        excited = np.where(line.v > threshold)[0]
        if len(excited):
            leftmost = min(leftmost, excited.min())
            rightmost = max(rightmost, excited.max())
    return leftmost, rightmost


if __name__ == "__main__":
    print("=" * 78)
    print("V14 CAPSTONE: does AIS origination bias spike direction (axon vs")
    print("dendrite), per Leterrier's Nav-density gradient + inactivation?")
    print("=" * 78)

    n = 160
    a_prof, ais_lo, ais_hi = build_neuron_profile(n=n)
    ais_center = (ais_lo + ais_hi) // 2
    print(f"\nNeuron axis: {n} cells")
    print(f"  dendrite/soma side: cells 0-59   (a=1.3, hard to excite)")
    print(f"  AIS:                cells {ais_lo}-{ais_hi-1}   (a=0.5, easily excited)")
    print(f"  axon side:          cells {ais_hi}-{n-1}  (a=0.7, normal)")

    # --- Test 1: originate AT the AIS, measure forward vs backward spread ---
    print(f"\n[1] Originate a spike AT the AIS (cell {ais_center}). How far does")
    print(f"    it spread toward the axon (right) vs the dendrite (left)?")
    line = GradientExcitableLine(n=n, a_profile=a_prof)
    left, right = measure_spread(line, ais_center)
    fwd_spread = right - ais_center   # toward axon
    bwd_spread = ais_center - left    # toward dendrite
    print(f"    forward (AIS->axon) spread:    {fwd_spread} cells")
    print(f"    backward (AIS->dendrite) spread: {bwd_spread} cells")
    if bwd_spread > 0:
        ratio = fwd_spread / bwd_spread
        print(f"    forward/backward spread ratio: {ratio:.2f}")
    print(f"    => spike {'preferentially propagates toward the axon' if fwd_spread > bwd_spread else 'spreads both ways'}")

    # --- Test 2: control -- uniform excitability, no gradient ---
    print(f"\n[2] CONTROL: same kick at the same cell, but UNIFORM excitability")
    print(f"    (no AIS gradient). Spread should be symmetric -- confirming the")
    print(f"    asymmetry in [1] comes from the Nav-density gradient, not the")
    print(f"    kick location.")
    a_uniform = np.full(n, 0.7)
    line2 = GradientExcitableLine(n=n, a_profile=a_uniform)
    left2, right2 = measure_spread(line2, ais_center)
    fwd2 = right2 - ais_center
    bwd2 = ais_center - left2
    print(f"    forward spread:  {fwd2} cells")
    print(f"    backward spread: {bwd2} cells")
    print(f"    => uniform case is {'symmetric (as expected)' if abs(fwd2-bwd2) <= 5 else 'asymmetric -- unexpected, investigate'}")

    print("\n" + "=" * 78)
    print("HONEST READ:")
    print("Real back-propagating APs DO invade dendrites (Leterrier says so);")
    print("the claim is ATTENUATION via the Nav gradient, not a perfect valve.")
    print("Test [1] vs control [2] isolates whether the excitability gradient")
    print("biases propagation direction at all. The mechanism (excitable")
    print("front + inactivation wake + density gradient) is the one v13's four")
    print("passive/relay attempts lacked, and it is grounded in the Leterrier")
    print("Nav-initiation account rather than in a geometric analogy.")
