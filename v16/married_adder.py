"""
married_adder.py -- scale the married directional unit (v15) to arithmetic.

The original Resonator Computer (adder.py) composed gates ALGEBRAICALLY: a
gate's output bit was instantly re-encoded as a phasor and fed to the next
gate. No time, no propagation. The married unit (v15) is different: its
output is a SPIKE that physically propagates down an excitable axon (~18
steps/cell). Composing married units into a full adder means each internal
wire is a real travelling spike, and a downstream gate cannot compute until
its upstream inputs' spikes have ARRIVED.

This file tests whether arithmetic survives that. Two layers:

  LAYER 1 (logical composition, this file): does a full adder built from
  married units produce the correct 8-row truth table, when every internal
  signal (a^b, the carries) is the OUTPUT of a married unit -- i.e. a
  spike-reached-the-axon-end bit -- fed as the INPUT bit of the next?
  This proves the composition is LOGICALLY sound: the directional spike
  readout is a faithful bit that downstream units can consume.

  LAYER 2 (timing, married_adder_timed.py): does it still work when the
  units run concurrently on a shared clock, with carries that must
  physically propagate stage-to-stage before the next stage can fire?

The full adder, same logic as the original:
    Sum  = a XOR b XOR cin
    Cout = (a AND b) OR (cin AND (a XOR b))
Five married units: XOR(a,b), XOR(that,cin), AND(a,b), AND(cin, a^b), OR(.,.).
Each unit's output is "did its spike reach its axon end" -- a real bit
produced by the directional mechanism, not an algebraic shortcut.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from married_unit import MarriedUnit

# Build the five married units of a full adder ONCE (reused across inputs).
# Each is a real soma+excitable-axon unit; .run([bits]) originates a spike
# and returns whether it reached the axon end (the output bit).
_UNITS = {
    "XOR_ab":   MarriedUnit("XOR", axon_len=40),
    "XOR_sum":  MarriedUnit("XOR", axon_len=40),
    "AND_ab":   MarriedUnit("AND", axon_len=40),
    "AND_cin":  MarriedUnit("AND", axon_len=40),
    "OR_cout":  MarriedUnit("OR",  axon_len=40),
}


def _bit(unit_key, bits):
    """Run a married unit, return its output bit (spike reached axon end)."""
    _, reached, _ = _UNITS[unit_key].run(list(bits))
    return 1 if reached else 0


def married_full_adder(a, b, cin):
    """A full adder where every internal wire is a directional spike output
    of a married unit. Returns (sum_bit, carry_out)."""
    axb = _bit("XOR_ab", [a, b])            # half-adder sum, as a spike-bit
    s   = _bit("XOR_sum", [axb, cin])        # full sum bit
    ab  = _bit("AND_ab", [a, b])             # carry from a,b
    cab = _bit("AND_cin", [cin, axb])        # carry from cin and (a^b)
    cout = _bit("OR_cout", [ab, cab])        # combined carry
    return s, cout


if __name__ == "__main__":
    print("=" * 70)
    print("MARRIED FULL ADDER -- 8-row truth table, every internal wire a")
    print("directional spike output of a married unit (not algebra)")
    print("=" * 70)
    print("  a b cin | sum cout | expected      | ok")
    print("-" * 70)
    all_ok = True
    for a in (0, 1):
        for b in (0, 1):
            for cin in (0, 1):
                s, cout = married_full_adder(a, b, cin)
                total = a + b + cin
                exp_s = total & 1
                exp_c = total >> 1
                ok = (s == exp_s and cout == exp_c)
                all_ok &= ok
                print(f"  {a} {b}  {cin}  |  {s}   {cout}   | "
                      f"sum={exp_s} cout={exp_c} | {'OK' if ok else 'XX'}")
    print("-" * 70)
    print(f"\nFULL ADDER CORRECT (all 8 rows, via directional spikes): {all_ok}")
    print("\nEvery sum and carry bit above was produced by a spike physically")
    print("reaching the end of a married unit's excitable axon, then being")
    print("consumed as the input bit of the next unit. The directional")
    print("mechanism carries arithmetic, not just single-gate logic.")
