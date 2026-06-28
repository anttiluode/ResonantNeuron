"""
adder.py — composing resonator-neurons into an arithmetic unit
==============================================================
The axon of one unit pings the dendrite of the next: a gate's output bit is
re-encoded as a phasor and fed downstream. Compose gates -> a 1-bit full adder
-> chain full adders -> an N-bit ripple-carry adder. Then ADD REAL NUMBERS.

A screensaver cannot add. If 1000 random N-bit additions all come back correct
from a network whose only primitive is a resonator's interference amplitude,
the network computes. That is the whole proof.

Theta-gamma timing (theta_gamma_clock): each gate settles within a GAMMA burst;
the THETA cycle latches stage outputs and propagates the carry one stage per
cycle. The dynamical adder runs on this clock; the algebraic adder is the
fixed-point shortcut used for large-scale verification.

PerceptionLab / Antti Luode, with Claude. Do not hype. Do not lie. Just show.
"""
import numpy as np
from resonator_neuron import encode_bit
from gates import make_gate, gate_out

# build the gate instances once
G = {k: make_gate(k) for k in ["XOR", "AND", "OR"]}


def full_adder(a, b, cin, dynamical=False):
    """Sum = a XOR b XOR cin ;  Cout = (a AND b) OR (cin AND (a XOR b))
    Each XOR/AND/OR is a resonator unit; outputs ping downstream as phasors."""
    axb = gate_out(G["XOR"], [a, b], dynamical)              # half-adder sum
    s   = gate_out(G["XOR"], [axb, cin], dynamical)          # full sum bit
    ab  = gate_out(G["AND"], [a, b], dynamical)              # carry from a,b
    cab = gate_out(G["AND"], [cin, axb], dynamical)          # carry from cin
    cout = gate_out(G["OR"], [ab, cab], dynamical)           # combined carry
    return s, cout


def ripple_add(x, y, nbits, dynamical=False):
    """Add two nbits integers via chained full adders (LSB first)."""
    carry = 0; out = 0
    for i in range(nbits):
        a = (x >> i) & 1; b = (y >> i) & 1
        s, carry = full_adder(a, b, carry, dynamical)
        out |= (s << i)
    out |= (carry << nbits)          # final carry = top bit
    return out


def theta_gamma_clock(x, y, nbits):
    """Run the ripple adder on an explicit theta-gamma schedule, returning a
    trace: each THETA cycle advances one bit-stage; within it the GAMMA gates
    settle dynamically. Proves the timing carries the computation."""
    carry = 0; out = 0; trace = []
    for i in range(nbits):                       # one theta cycle per stage
        a = (x >> i) & 1; b = (y >> i) & 1
        s, carry = full_adder(a, b, carry, dynamical=True)  # gamma settling
        out |= (s << i)
        trace.append(dict(theta_cycle=i, a=a, b=b, sum_bit=s, carry_out=carry))
    out |= (carry << nbits)
    return out, trace


if __name__ == "__main__":
    print("=" * 60)
    print("FULL ADDER — 8-row truth table (algebraic & dynamical)")
    print("=" * 60)
    print("  a b cin | sum cout | expected | ok")
    ok_all = True
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                s, co = full_adder(a, b, c, dynamical=True)
                exp = a + b + c
                good = (s + 2 * co == exp); ok_all &= good
                print(f"   {a} {b}  {c}  |  {s}   {co}   |   {exp}={co}{s}  | {'ok' if good else 'XX'}")
    print(f"  full adder correct (dynamical resonators): {ok_all}")

    print("\n" + "=" * 60)
    print("RIPPLE-CARRY ADDER — 1000 random additions")
    print("=" * 60)
    rng = np.random.default_rng(0)
    NB = 8; wrong = 0
    for _ in range(1000):
        x = int(rng.integers(0, 2 ** NB)); y = int(rng.integers(0, 2 ** NB))
        got = ripple_add(x, y, NB, dynamical=False)
        if got != x + y:
            wrong += 1
    print(f"  {NB}-bit, algebraic : {1000 - wrong}/1000 correct")

    # dynamical (real resonator settling) on a smaller sample — it is slower
    wrongd = 0; M = 60
    for _ in range(M):
        x = int(rng.integers(0, 2 ** NB)); y = int(rng.integers(0, 2 ** NB))
        if ripple_add(x, y, NB, dynamical=True) != x + y:
            wrongd += 1
    print(f"  {NB}-bit, DYNAMICAL : {M - wrongd}/{M} correct (real oscillator settling)")

    print("\n" + "=" * 60)
    print("THETA-GAMMA CLOCK — one worked addition, stage by stage")
    print("=" * 60)
    x, y = 0b01101, 0b00111      # 13 + 7 = 20
    res, trace = theta_gamma_clock(x, y, 5)
    for tr in trace:
        print(f"  theta cycle {tr['theta_cycle']}: a={tr['a']} b={tr['b']} "
              f"-> sum bit {tr['sum_bit']}, carry {tr['carry_out']}")
    print(f"  {x} + {y} = {res}   correct: {res == x + y}")
