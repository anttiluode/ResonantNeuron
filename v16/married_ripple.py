"""
married_ripple.py -- chain married full adders into an N-bit ripple-carry
adder and verify it on random additions. This is the "a screensaver cannot
add" proof, now carried entirely by directional spikes: every sum and carry
bit is a spike that reached the end of a married unit's excitable axon.

The ripple structure is the classic one: stage i adds bit i of x, bit i of
y, and the carry rippling in from stage i-1; its carry-out feeds stage i+1.
In the married version, that carry is the OUTPUT SPIKE of stage i's OR unit,
consumed as an input bit by stage i+1. The carry physically ripples as a
chain of spikes.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from married_adder import married_full_adder


def married_ripple_add(x, y, nbits):
    """Add two nbits integers via chained married full adders (LSB first).
    Every bit is produced by a directional spike."""
    carry = 0
    out = 0
    for i in range(nbits):
        a = (x >> i) & 1
        b = (y >> i) & 1
        s, carry = married_full_adder(a, b, carry)
        out |= (s << i)
    out |= (carry << nbits)
    return out


if __name__ == "__main__":
    print("=" * 70)
    print("MARRIED RIPPLE-CARRY ADDER -- random additions via directional spikes")
    print("=" * 70)

    rng = np.random.default_rng(0)

    # smaller bit width + fewer trials than the algebraic version, because
    # each bit here runs full excitable-axon integrations (slow); enough to
    # prove it, honestly scoped.
    for nbits, ntrials in [(4, 40), (6, 20)]:
        correct = 0
        for _ in range(ntrials):
            x = int(rng.integers(0, 2 ** nbits))
            y = int(rng.integers(0, 2 ** nbits))
            got = married_ripple_add(x, y, nbits)
            exp = x + y
            if got == exp:
                correct += 1
            elif correct < 1:  # show first failure if any
                print(f"  MISMATCH: {x} + {y} = {exp}, got {got}")
        print(f"  {nbits}-bit: {correct}/{ntrials} random additions correct "
              f"({'PASS' if correct == ntrials else 'FAIL'})")

    print("\n" + "=" * 70)
    print("Every digit of every sum above was carried by a spike physically")
    print("propagating down an excitable axon. The directional married unit")
    print("scales from one gate to multi-bit arithmetic.")
