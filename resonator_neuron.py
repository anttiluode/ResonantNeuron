"""
resonator_neuron.py — a Berglund-geometry neuron that computes
==============================================================
The unit, mapped to the angled-cavity ring (and to our skew_core line):

    dendrites (the satellite cavities)  -> carry a PHASE from upstream
    soma      (the central cavity)      -> MIXES them by interference
    axon      (theta-gated threshold)   -> PINGS downstream when the soma's
                                            resonance amplitude crosses a bar

The computational primitive is the soma's resonance amplitude:
    s = sum_j w_j * p_j + bias            (p_j = upstream phasors)
    |s| = constructive (inputs agree) ... destructive (inputs disagree)

|s| is a NONLINEAR (quadratic) function of the inputs. That single fact is why
one of these units computes XOR -- the linearly-inseparable function a scalar
McCulloch-Pitts neuron provably cannot. (Single complex/phasor neurons solving
XOR is an established result in complex-valued NN theory; here it falls out of
the resonator's physical amplitude readout, and the units COMPOSE via axons.)

This file provides BOTH:
  - ResonatorNeuron.settle_dynamical(): a real damped driven oscillator network
    (dendrites + soma) integrated until it rings down to steady state;
  - ResonatorNeuron.settle_algebraic(): the fixed point of those same ODEs.
and shows they AGREE -- the physics computes the algebra.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np

TWO_PI = 2 * np.pi


def encode_bit(b):
    """bit -> phasor on the unit circle. 0 -> +1 (phase 0), 1 -> -1 (phase pi)."""
    return np.exp(1j * np.pi * b)


class ResonatorNeuron:
    def __init__(self, weights, bias=0.0, lo=0.0, hi=1.0, skew=0.0,
                 Omega=TWO_PI * 0.20, gamma=0.25, kappa=1.0):
        """weights: complex dendrite gains w_j. bias: complex soma bias.
        Readout: output bit = 1 iff  lo <= |soma| <= hi   (an amplitude BAND).
        skew: directed coupling among dendrites (the angled-cavity chirality).
        Omega/gamma/kappa: gamma-band natural freq, damping, soma coupling."""
        self.w = np.asarray(weights, complex)
        self.bias = complex(bias)
        self.lo, self.hi = lo, hi
        self.skew = skew
        self.Omega, self.gamma, self.kappa = Omega, gamma, kappa

    # ---- the algebra: steady state of the resonator ODEs ----
    def settle_algebraic(self, phasors):
        p = np.asarray(phasors, complex)
        return np.sum(self.w * p) + self.bias

    # ---- the physics: integrate the damped driven network until it rings down ----
    def settle_dynamical(self, phasors, dt=0.05, T=6000):
        p = np.asarray(phasors, complex)
        K = len(p)
        d = p.copy()                       # dendrite envelopes start at their drive
        s = 0j                             # soma starts silent
        # skew coupling among dendrites: antisymmetric -> conserves amplitude, adds
        # directed circulation (the angled-cavity chirality) without biasing the FP.
        S = np.zeros((K, K))
        for j in range(K):
            S[j, (j + 1) % K] += self.skew
            S[(j + 1) % K, j] -= self.skew
        for _ in range(T):
            # envelope dynamics in the rotating frame; soma normalized so its fixed
            # point is exactly  s* = sum_j w_j d*_j + bias  with d*_j = p_j.
            dd = -self.gamma * (d - p) + self.gamma * (S @ d)
            ds = -self.gamma * (s - (np.sum(self.w * d) + self.bias))
            d = d + dt * dd
            s = s + dt * ds
        return s

    def output(self, phasors, dynamical=False):
        s = self.settle_dynamical(phasors) if dynamical else self.settle_algebraic(phasors)
        amp = abs(s)
        return int(self.lo - 1e-9 <= amp <= self.hi + 1e-9), amp


# ============================================================ self-test
if __name__ == "__main__":
    print("=" * 66)
    print("RESONATOR NEURON — does the physics compute the algebra?")
    print("=" * 66)
    # XOR unit: two equal dendrites, fire when amplitude is LOW (destructive).
    # |p_a + p_b| = 2 when bits agree, 0 when they disagree -> band [0, 1] = XOR.
    xor = ResonatorNeuron(weights=[1, 1], bias=0.0, lo=-0.1, hi=1.0, skew=0.0)
    print("\n  XOR via destructive interference (fire when |soma| <= 1):")
    print("   a b | algebra |soma| | dynamical |soma| | out | XOR?")
    ok = True
    for a in (0, 1):
        for b in (0, 1):
            ph = [encode_bit(a), encode_bit(b)]
            sa = abs(xor.settle_algebraic(ph))
            sd = abs(xor.settle_dynamical(ph))
            out, _ = xor.output(ph)
            good = (out == (a ^ b))
            ok &= good and abs(sa - sd) < 1e-3
            print(f"   {a} {b} |   {sa:5.3f}        |   {sd:5.3f}          |  {out}  | {a^b}  {'ok' if good else 'XX'}")
    print(f"\n  physics matches algebra to 1e-3, and the unit computes XOR: {ok}")
    print("  -> the soma's resonance amplitude IS the nonlinearity. one unit, XOR.")
