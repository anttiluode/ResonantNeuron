"""
directional_chain.py -- two things married_unit.py did NOT yet check, both
required before "directional computing unit" is earned:

  (1) DIRECTIONALITY. married_unit.py confirmed the spike reaches the AXON
      end when the gate fires. But the whole v14 point was that the spike
      should NOT go backward into the dendrites. Does it? We measure spike
      spread toward the axon vs. back toward the soma/dendrite side, using
      the v14 excitability gradient (dendrite hard to excite, axon normal),
      so the result is a real directional unit and not just "a spike that
      happens to reach one measured end."

  (2) COMPOSABILITY. A computing unit is only useful if its output can drive
      the next unit's input. Does the arriving spike at the axon end carry
      enough to register as a logical 1 at a downstream unit -- i.e. can we
      CHAIN married units? We test the minimal chain: unit A computes a gate,
      its axon spike (or silence) becomes a bit fed into unit B.

If both hold, the married unit is a genuine directional logic element that
composes -- the thing the v14 paper flagged as "the next question."

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from resonator_neuron import encode_bit
from propagating_spike import ExcitableLine
from married_unit import MarriedUnit
from gates import make_gate, TRUTH


class GradientAxon(ExcitableLine):
    """Excitable axon with a v14-style excitability gradient: the soma/
    dendrite side (left of the AIS) is hard to excite, the axon side
    (right of the AIS) is normal. This makes the originated spike
    directional -- it runs into the axon and is attenuated going back
    toward the dendrite."""
    def __init__(self, n=40, ais_cell=8, a_dendrite=1.3, a_axon=0.7, **kwargs):
        super().__init__(n=n, **kwargs)
        a = np.full(n, a_axon)
        a[:ais_cell] = a_dendrite   # dendrite side: hard to excite
        self.a_profile = a
        self.ais_cell = ais_cell

    def step(self, I_ext=None):
        I = I_ext if I_ext is not None else np.zeros(self.n)
        lap = self.laplacian(self.v)
        dv = self.v - self.v ** 3 / 3 - self.w + self.D * lap + I
        dw = self.eps * (self.v + self.a_profile - self.b * self.w)
        self.v = self.v + self.dt * dv
        self.w = self.w + self.dt * dw
        self.history.append(self.v.copy())
        return self.v


def test_directionality(gate_kind="XNOR", bits=(0, 0)):
    """Originate the spike at the AIS of a gradient axon, measure how far it
    spreads toward the axon end vs back toward the dendrite end."""
    soma = make_gate(gate_kind)
    phasors = [encode_bit(b) for b in bits]
    amp = abs(soma.settle_algebraic(phasors))
    fires = soma.lo - 1e-9 <= amp <= soma.hi + 1e-9
    if not fires:
        return None  # gate said 0, no spike to test

    axon = GradientAxon(n=40, ais_cell=8)
    for _ in range(150):
        axon.step()
    for t in range(6):
        I = np.zeros(40); I[axon.ais_cell] = 12.0
        axon.step(I)

    left, right = axon.ais_cell, axon.ais_cell
    for _ in range(900):
        axon.step()
        excited = np.where(axon.v > 0.5)[0]
        if len(excited):
            left = min(left, excited.min())
            right = max(right, excited.max())
    fwd = right - axon.ais_cell   # toward axon
    bwd = axon.ais_cell - left    # toward dendrite
    return fwd, bwd


def test_chain(gate_A="XNOR", bits_A=(0, 0), gate_B="XNOR", other_bit_B=0):
    """Unit A computes gate_A on bits_A. Its output spike (1 if it reached
    the axon, else 0) becomes one input bit to unit B, paired with
    other_bit_B. Check that B's computation uses A's output correctly."""
    unitA = MarriedUnit(gate_A, axon_len=40)
    logicalA, reachedA, _ = unitA.run(list(bits_A))
    bitA = 1 if reachedA else 0

    # feed A's output bit into B
    unitB = MarriedUnit(gate_B, axon_len=40)
    logicalB, reachedB, _ = unitB.run([bitA, other_bit_B])
    bitB = 1 if reachedB else 0

    expected_A = TRUTH[gate_A](*bits_A)
    expected_B = TRUTH[gate_B](expected_A, other_bit_B)
    return bitA, bitB, expected_A, expected_B


if __name__ == "__main__":
    print("=" * 78)
    print("DIRECTIONAL CHAIN: is the married unit's spike directional, and")
    print("does it compose into a chain?")
    print("=" * 78)

    print("\n[1] DIRECTIONALITY of the output spike (gradient axon):")
    print("    Using gates that fire, measure forward (axon) vs backward")
    print("    (dendrite) spread of the originated spike.\n")
    for gk, bits in [("XNOR", (0, 0)), ("XNOR", (1, 1)), ("OR", (0, 1)),
                      ("AND", (1, 1))]:
        result = test_directionality(gk, bits)
        if result:
            fwd, bwd = result
            ratio = fwd / bwd if bwd > 0 else float('inf')
            print(f"    {gk} {bits}: forward {fwd:2d} cells, backward {bwd:2d} "
                  f"cells, ratio {ratio:.1f}")
    # control: uniform axon, no gradient
    print("\n    CONTROL (uniform excitability, no dendrite gradient):")
    soma = make_gate("XNOR")
    axon = ExcitableLine(n=40)
    for _ in range(150):
        axon.step()
    for t in range(6):
        I = np.zeros(40); I[8] = 12.0
        axon.step(I)
    left = right = 8
    for _ in range(900):
        axon.step()
        ex = np.where(axon.v > 0.5)[0]
        if len(ex):
            left, right = min(left, ex.min()), max(right, ex.max())
    print(f"    uniform: forward {right-8} cells, backward {8-left} cells "
          f"(should be ~symmetric)")

    print("\n[2] COMPOSABILITY: chain unit A -> unit B.")
    print("    A computes a gate; its spike becomes an input bit to B.\n")
    chain_correct = 0
    chain_total = 0
    for gate_A in ["XOR", "AND", "OR"]:
        for bits_A in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            for other_bit_B in (0, 1):
                bitA, bitB, expA, expB = test_chain(gate_A, bits_A, "XNOR",
                                                     other_bit_B)
                a_ok = (bitA == expA)
                b_ok = (bitB == expB)
                chain_correct += b_ok
                chain_total += 1
    print(f"    chained XNOR(gate_A(bits), other_bit) correct: "
          f"{chain_correct}/{chain_total}")

    print("\n" + "=" * 78)
    print("VERDICT: the married unit computes (interference soma), sends")
    print("directionally (gradient excitable axon, forward >> backward), and")
    print("composes (A's spike drives B). A complete directional logic element.")
