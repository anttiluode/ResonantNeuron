"""
gates.py — a complete logic gate set, each a single ResonatorNeuron
===================================================================
Each gate is ONE resonator unit: dendrites carry the input phasors, the soma's
resonance amplitude |s| is read through an amplitude BAND [lo,hi] -> output bit.

  encode: 0 -> +1, 1 -> -1   (phasor on the unit circle)
  soma:   s = sum_j w_j p_j + bias
  output: 1 iff lo <= |s| <= hi

Why this is a real gate set and not a trick:
  - XOR/XNOR need the nonlinear amplitude readout (destructive interference) --
    the function a linear unit cannot do. The band catches the |s|~0 case.
  - AND/OR/NOT are linearly separable; a biased unit with a one-sided band does
    them. The point of including them is COMPOSITION into arithmetic.

Every gate's truth table is checked exactly at import-test time, dynamically
(real resonator settling) and algebraically.

PerceptionLab / Antti Luode, with Claude. Do not hype. Do not lie. Just show.
"""
import numpy as np
from resonator_neuron import ResonatorNeuron, encode_bit


# --- gate configurations (weights, bias, band) found to realize each table ---
# |s| values for 2 inputs with weights [1,1], bias b (real):
#   (0,0): |2+b|   (0,1)/(1,0): |b|   (1,1): |-2+b|
def make_gate(kind):
    if kind == "XOR":   # fire when inputs disagree: |s| ~ 0
        return ResonatorNeuron([1, 1], bias=0.0, lo=-0.1, hi=1.0)
    if kind == "XNOR":  # fire when inputs agree: |s| ~ 2
        return ResonatorNeuron([1, 1], bias=0.0, lo=1.0, hi=99.0)
    if kind == "AND":   # fire only at (1,1): with bias -2, |s|: (0,0)=0,(01)=2,(11)=4
        return ResonatorNeuron([1, 1], bias=-2.0, lo=3.0, hi=99.0)
    if kind == "OR":    # fire unless (0,0): bias +2 -> (00)=4,(01)=2,(11)=0; fire |s|<=3
        return ResonatorNeuron([1, 1], bias=+2.0, lo=-0.1, hi=3.0)
    if kind == "NAND":
        return ResonatorNeuron([1, 1], bias=-2.0, lo=-0.1, hi=3.0)
    if kind == "NOR":
        return ResonatorNeuron([1, 1], bias=+2.0, lo=3.0, hi=99.0)
    if kind == "NOT":   # single input: (0)->|1+b|, (1)->|-1+b|; bias +1 -> 2 vs 0
        return ResonatorNeuron([1], bias=+1.0, lo=1.0, hi=99.0)
    if kind == "MAJ3":  # majority of 3: |s| with w=[1,1,1]: (#1=0)=3,(1)=1,(2)=1,(3)=3
        # majority -> 1 when two or three 1s. |s|: 0ones=3,1one=1,2ones=1,3ones=3.
        # |s| can't separate {1one} from {2ones}. need bias to break tie:
        # bias -1: 0ones->|3-1|=2, 1->|1-1|=0, 2->|-1-1|=2, 3->|-3-1|=4
        # fire (>=2 ones): bands [2-eps? collides 0ones]. use bias -1, fire |s|>=3? only 3ones.
        # Majority is NOT realizable by one amplitude band -> compose from gates (see adder).
        raise ValueError("MAJ3 is composed from gates, not a single band unit")
    raise ValueError(kind)


GATES_2IN = ["XOR", "XNOR", "AND", "OR", "NAND", "NOR"]
TRUTH = {
    "XOR":  lambda a, b: a ^ b,
    "XNOR": lambda a, b: 1 - (a ^ b),
    "AND":  lambda a, b: a & b,
    "OR":   lambda a, b: a | b,
    "NAND": lambda a, b: 1 - (a & b),
    "NOR":  lambda a, b: 1 - (a | b),
}


def gate_out(g, bits, dynamical=False):
    return g.output([encode_bit(b) for b in bits], dynamical=dynamical)[0]


def verify_all(dynamical=False):
    allok = True
    for k in GATES_2IN:
        g = make_gate(k)
        rows = []
        for a in (0, 1):
            for b in (0, 1):
                rows.append(gate_out(g, [a, b], dynamical) == TRUTH[k](a, b))
        ok = all(rows); allok &= ok
        print(f"  {k:5s}: {'PASS' if ok else 'FAIL'}")
    # NOT (1 input)
    gn = make_gate("NOT")
    okn = all(gate_out(gn, [a], dynamical) == (1 - a) for a in (0, 1))
    allok &= okn
    print(f"  {'NOT':5s}: {'PASS' if okn else 'FAIL'}")
    return allok


if __name__ == "__main__":
    print("=" * 50)
    print("GATE SET — every truth table, ALGEBRAIC")
    print("=" * 50)
    a_ok = verify_all(dynamical=False)
    print("\n" + "=" * 50)
    print("GATE SET — every truth table, DYNAMICAL (real resonator)")
    print("=" * 50)
    d_ok = verify_all(dynamical=True)
    print(f"\n  all gates pass, algebra={a_ok}  physics={d_ok}")
