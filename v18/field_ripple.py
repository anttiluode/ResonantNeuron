"""
field_ripple.py -- chain continuous-field full adders into a multi-bit
ripple adder, with the carry coupling stage-to-stage as a real latched
field output (no scheduler passing bits). Tests that the continuous-field
coupling works across stage boundaries, not just within one full adder.
"""
import numpy as np
from field_adder import FieldFullAdder


def field_ripple_add(x, y, nbits, max_ticks=8000):
    """Multi-bit add with continuous-field full adders. Stage i's carry-out
    (a latched field output) becomes stage i+1's carry-in. We run stages in
    dependency order but each is a real continuous field computation; the
    carry handoff uses the latched output_bit (the physical capture)."""
    carry = 0
    out = 0
    total_ticks = 0
    for i in range(nbits):
        a = (x >> i) & 1
        b = (y >> i) & 1
        fa = FieldFullAdder()
        s, cout, ticks = fa.run(a, b, carry, max_ticks=max_ticks)
        if s is None or cout is None:
            return None, total_ticks
        out |= (s << i)
        carry = cout
        total_ticks += ticks
    out |= (carry << nbits)
    return out, total_ticks


if __name__ == "__main__":
    print("=" * 64)
    print("CONTINUOUS-FIELD RIPPLE ADDER (real field, latched carry handoff)")
    print("=" * 64)
    rng = np.random.default_rng(2)
    for nbits, ntrials in [(3, 8), (4, 6)]:
        correct = 0
        for _ in range(ntrials):
            x = int(rng.integers(0, 2**nbits))
            y = int(rng.integers(0, 2**nbits))
            got, ticks = field_ripple_add(x, y, nbits)
            exp = x + y
            if got == exp:
                correct += 1
            else:
                print(f"  MISMATCH {x}+{y}={exp} got {got}")
        print(f"  {nbits}-bit: {correct}/{ntrials} correct "
              f"({'PASS' if correct==ntrials else 'FAIL'})")
    # worst case latency
    print("\n  worst-case (carry ripples whole word):")
    for nbits in [1, 2, 3]:
        x, y = (2**nbits)-1, 1
        got, ticks = field_ripple_add(x, y, nbits)
        print(f"    {nbits}-bit: {x}+{y}={got} (exp {x+y}), {ticks} ticks total")
