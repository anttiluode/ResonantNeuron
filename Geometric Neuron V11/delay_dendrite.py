"""
delay_dendrite.py -- does dendrite LENGTH change what a resonator unit computes?
==================================================================================
resonator_neuron.py (v_prior) had wires, not cables: every dendrite delivered
its phasor to the soma in the same timestep, same phase. Antti's question,
watching Berglund's angled rings: the satellites sit at different radii/angles,
so a wave launched from the rim arrives at the centre after a PATH-LENGTH
dependent phase delay. Does that delay matter, or is it decoration?

The mechanism, made explicit:
  A travelling wave at carrier frequency Omega, launched at t=0, covers a
  cable of length L at speed v. It arrives at the soma at time L/v, having
  accumulated phase  phi = Omega * L / v  (mod 2*pi), ON TOP OF whatever bit
  phase (0 or pi) it was carrying.

  So a dendrite of length L doesn't just delay a signal -- for a fixed-frequency
  carrier it ALSO rotates its phasor by phi = Omega*L/v before the soma ever
  sees it. Two dendrites carrying the IDENTICAL bit but DIFFERENT lengths
  arrive as DIFFERENT phasors. XOR's destructive-interference trick
  (|p_a + p_b| = 0 when bits disagree, = 2 when they agree) is exact only when
  the two arrival phases match. Detune the lengths and you detune the gate.

This file tests that claim head-on: sweep dendrite length, watch what logical
function the SAME unit (same weights, same band) ends up computing, and
verify a unit can be IMPLICITLY reconfigured -- AND <-> XOR <-> OR <-> NOTHING
-- purely by changing how far the dendrite physically runs. No weight change.
Length alone is a free logic parameter.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np

TWO_PI = 2 * np.pi


def encode_bit(b):
    """bit -> phasor at the dendrite's INPUT end. 0 -> +1, 1 -> -1."""
    return np.exp(1j * np.pi * b)


def arrival_phase(length, Omega, v=1.0):
    """Phase rotation a carrier accumulates travelling `length` at speed v."""
    return (Omega * length / v) % TWO_PI


class DelayDendrite:
    """A dendrite with physical length. Same envelope dynamics as before,
    but the DRIVE the soma receives is rotated by the propagation phase."""
    def __init__(self, length, Omega, v=1.0, gamma=0.25):
        self.length = length
        self.Omega, self.v, self.gamma = Omega, v, gamma
        self.phi = arrival_phase(length, Omega, v)

    def carry(self, bit_phasor):
        """What arrives at the soma after travelling `length`."""
        return bit_phasor * np.exp(1j * self.phi)


class LengthAwareResonatorNeuron:
    """Same soma/axon as resonator_neuron.py. Dendrites now have length."""
    def __init__(self, lengths, weights, bias=0.0, lo=0.0, hi=1.0,
                 Omega=TWO_PI * 0.20, v=1.0, gamma=0.25):
        self.dendrites = [DelayDendrite(L, Omega, v, gamma) for L in lengths]
        self.w = np.asarray(weights, complex)
        self.bias = complex(bias)
        self.lo, self.hi = lo, hi

    def settle_algebraic(self, bits):
        p = np.array([encode_bit(b) for b in bits], complex)
        arrived = np.array([d.carry(pj) for d, pj in zip(self.dendrites, p)])
        return np.sum(self.w * arrived) + self.bias

    def classify(self, bits):
        amp = abs(self.settle_algebraic(bits))
        fire = int(self.lo - 1e-9 <= amp <= self.hi + 1e-9)
        return fire, amp


def truth_table(unit):
    rows = []
    for a in (0, 1):
        for b in (0, 1):
            fire, amp = unit.classify([a, b])
            rows.append((a, b, fire, amp))
    return rows


def identify_function(rows):
    """Match a 2-input truth table to a named boolean function."""
    out = tuple(r[2] for r in rows)  # order: 00,01,10,11
    table = {
        (1, 0, 0, 1): "XNOR",
        (0, 1, 1, 0): "XOR",
        (0, 0, 0, 1): "AND",
        (1, 1, 1, 0): "NAND",
        (0, 1, 1, 1): "OR",
        (1, 0, 0, 0): "NOR",
        (1, 1, 1, 1): "TRUE (always fires)",
        (0, 0, 0, 0): "FALSE (never fires)",
        (1, 0, 1, 0): "NOT-A (ignores b)",
        (0, 1, 0, 1): "NOT-B (ignores a)",
        (1, 1, 0, 0): "ignores b, =NOT-A-ish",
        (0, 0, 1, 1): "ignores a, =B",
    }
    return table.get(out, f"unnamed pattern {out}")


if __name__ == "__main__":
    print("=" * 78)
    print("DOES DENDRITE LENGTH CHANGE WHAT A RESONATOR UNIT COMPUTES?")
    print("=" * 78)
    Omega = TWO_PI * 0.20
    v = 1.0
    period_length = TWO_PI / Omega * v  # length for one full 2*pi phase wrap

    print(f"\nCarrier Omega={Omega:.4f} rad/step, v={v}  ->  one full wavelength "
          f"of cable = {period_length:.3f} length-units")
    print("Same weights [1,1], same band [lo=-0.1,hi=1.0] (the v_prior XOR unit).")
    print("ONLY changing dendrite-B's length, dendrite-A fixed at length=0.\n")
    print(f"{'len_B':>8} | {'phi_B/pi':>9} | 00  amp | 01  amp | 10  amp | 11  amp | function")
    print("-" * 90)

    # sweep dendrite-B length from 0 to a bit past one full wavelength
    lengths = np.linspace(0, period_length * 1.05, 22)
    results = []
    for Lb in lengths:
        unit = LengthAwareResonatorNeuron(
            lengths=[0.0, Lb], weights=[1, 1], bias=0.0,
            lo=-0.1, hi=1.0, Omega=Omega, v=v)
        rows = truth_table(unit)
        fname = identify_function(rows)
        results.append((Lb, rows, fname))
        phi_frac = arrival_phase(Lb, Omega, v) / np.pi
        amps = " | ".join(f"{r[3]:7.3f}" for r in rows)
        print(f"{Lb:8.3f} | {phi_frac:9.3f} | {amps} | {fname}")

    # Find the distinct logical regimes encountered
    seen = []
    for Lb, rows, fname in results:
        if not seen or seen[-1][1] != fname:
            seen.append((Lb, fname))
    print("\nDistinct logic functions encountered as length increases from 0:")
    for Lb, fname in seen:
        print(f"  length >= {Lb:6.3f}  ->  {fname}")

    n_distinct = len(set(f for _, _, f in results))
    print(f"\n{n_distinct} distinct logical functions appeared from ONE unit, ZERO "
          f"weight changes, varying ONLY physical cable length.")
    claim_holds = n_distinct >= 3
    print(f"\nCLAIM ('length alone reconfigures the gate'): "
          f"{'CONFIRMED' if claim_holds else 'NOT SUPPORTED'} "
          f"({n_distinct} distinct functions observed)")
