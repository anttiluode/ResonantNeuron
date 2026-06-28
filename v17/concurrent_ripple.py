"""
concurrent_ripple.py -- the clean next build: a full N-bit ripple-carry
adder run with FULL CONCURRENCY -- every stage of every bit live on one
shared clock at once -- with each carry physically propagating as a spike
before the next stage can consume it.

v16 left two things separate:
  - married_ripple.py: multi-bit, but SEQUENTIAL (each full adder blocks to
    completion before the next bit starts). Correct, but hides cross-stage
    timing.
  - married_adder_timed.py: CONCURRENT, but only ONE full adder (one bit).
    Revealed the per-stage latency (~460 ticks/spike-hop) but not how it
    accumulates across bits.

This file combines them: N full adders, all instantiated up front, ALL
stepping together every tick. Stage i's carry-out is the output spike of its
OR unit; it is wired into stage i+1's carry-dependent units only once that
spike has physically arrived. So stage i+1's carry path genuinely waits for
stage i's carry to ripple in -- the defining behavior of a ripple-carry
adder, now as real propagating spikes across the whole word at once.

The questions this answers that neither v16 file could:
  (1) Does a fully concurrent multi-bit adder still compute correctly when
      every stage is live simultaneously (no stage-by-stage blocking)?
  (2) Does total latency scale LINEARLY with bit width N -- the signature of
      true ripple-carry (the carry must walk the whole word) -- or does
      concurrency hide it?
  (3) What is the worst case: the input that forces a carry to ripple all
      the way from bit 0 to bit N (e.g. 0b111... + 0b000...1)?

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from married_adder_timed import TimedUnit


class FullAdderStage:
    """One bit's worth of full adder as five concurrent TimedUnits.
    Exposes: provide bit inputs (a,b available immediately; cin wired from
    the previous stage's carry spike when it arrives); read sum_bit and
    carry_out as they become available."""

    def __init__(self, axon_len=30):
        self.u = {
            "XOR_ab":  TimedUnit("XOR", axon_len=axon_len),
            "XOR_sum": TimedUnit("XOR", axon_len=axon_len),
            "AND_ab":  TimedUnit("AND", axon_len=axon_len),
            "AND_cin": TimedUnit("AND", axon_len=axon_len),
            "OR_cout": TimedUnit("OR",  axon_len=axon_len),
        }
        self.a = self.b = None
        self.cin = None
        self._cin_wired = False
        self.sum_bit = None
        self.carry_out = None

    def settle(self):
        for unit in self.u.values():
            unit.settle()

    def set_ab(self, a, b):
        self.a, self.b = a, b
        self.u["XOR_ab"].provide_inputs([a, b])
        self.u["AND_ab"].provide_inputs([a, b])

    def set_cin(self, cin):
        """Called when the carry-in bit becomes available (from prev stage's
        carry spike, or 0 for stage 0)."""
        self.cin = cin

    def step(self):
        for unit in self.u.values():
            unit.step()
        # internal wiring: XOR_ab's spike feeds XOR_sum and AND_cin, paired
        # with cin -- but only once BOTH axb is ready AND cin is available
        axb = self.u["XOR_ab"].output_bit
        if axb is not None and self.cin is not None:
            if self.u["XOR_sum"].inputs is None:
                self.u["XOR_sum"].provide_inputs([axb, self.cin])
            if self.u["AND_cin"].inputs is None:
                self.u["AND_cin"].provide_inputs([self.cin, axb])
        # OR_cout needs both AND outputs
        ab = self.u["AND_ab"].output_bit
        cab = self.u["AND_cin"].output_bit
        if ab is not None and cab is not None and self.u["OR_cout"].inputs is None:
            self.u["OR_cout"].provide_inputs([ab, cab])
        # collect outputs
        if self.u["XOR_sum"].output_bit is not None and self.sum_bit is None:
            self.sum_bit = self.u["XOR_sum"].output_bit
        if self.u["OR_cout"].output_bit is not None and self.carry_out is None:
            self.carry_out = self.u["OR_cout"].output_bit


def concurrent_ripple_add(x, y, nbits, axon_len=30, max_ticks=40000,
                          trace=False):
    """Add two nbits integers with all stages live concurrently on one clock.
    Returns (result, ticks_to_complete) or (result, ticks, trace_list)."""
    stages = [FullAdderStage(axon_len=axon_len) for _ in range(nbits)]
    for st in stages:
        st.settle()

    # all a,b bits available at t=0; stage 0's cin is 0 immediately
    for i in range(nbits):
        stages[i].set_ab((x >> i) & 1, (y >> i) & 1)
    stages[0].set_cin(0)

    carry_arrival_ticks = [None] * nbits   # when each stage's carry_out lands
    tr = []
    for tick in range(max_ticks):
        for st in stages:
            st.step()
        # ripple: when stage i's carry_out is ready, wire it into stage i+1
        for i in range(nbits - 1):
            if stages[i].carry_out is not None and stages[i + 1].cin is None:
                stages[i + 1].set_cin(stages[i].carry_out)
                if carry_arrival_ticks[i] is None:
                    carry_arrival_ticks[i] = tick
        # done when every stage has a sum bit and the final carry is known
        all_sums = all(st.sum_bit is not None for st in stages)
        final_carry = stages[-1].carry_out
        if all_sums and final_carry is not None:
            result = 0
            for i in range(nbits):
                result |= (stages[i].sum_bit << i)
            result |= (final_carry << nbits)
            if trace:
                return result, tick, carry_arrival_ticks
            return result, tick
    # timed out
    if trace:
        return None, max_ticks, carry_arrival_ticks
    return None, max_ticks


if __name__ == "__main__":
    print("=" * 72)
    print("FULLY CONCURRENT MULTI-BIT RIPPLE ADDER")
    print("All stages live on one shared clock; carries ripple as real spikes")
    print("=" * 72)

    rng = np.random.default_rng(1)

    # correctness across random additions, smaller counts (full concurrent
    # excitable sims are slow), honestly scoped
    print("\n[1] Correctness (random additions, fully concurrent):")
    for nbits, ntrials in [(3, 12), (4, 8)]:
        correct = 0
        for _ in range(ntrials):
            x = int(rng.integers(0, 2 ** nbits))
            y = int(rng.integers(0, 2 ** nbits))
            got, ticks = concurrent_ripple_add(x, y, nbits)
            exp = x + y
            if got == exp:
                correct += 1
            else:
                print(f"    MISMATCH {x}+{y}={exp}, got {got}")
        print(f"    {nbits}-bit: {correct}/{ntrials} correct "
              f"({'PASS' if correct == ntrials else 'FAIL'})")

    # latency scaling: the worst case forces a full carry ripple
    print("\n[2] Latency scaling -- worst case (carry ripples the whole word):")
    print("    x = 2^n - 1 (all ones), y = 1  -> carry propagates bit 0 -> n")
    print(f"    {'nbits':>6} | {'result':>8} | {'ticks':>7} | {'ticks/bit':>10}")
    for nbits in [1, 2, 3, 4, 5]:
        x = (2 ** nbits) - 1
        y = 1
        got, ticks = concurrent_ripple_add(x, y, nbits)
        exp = x + y
        ok = "OK" if got == exp else f"XX (got {got})"
        print(f"    {nbits:6d} | {got:8d} | {ticks:7d} | "
              f"{ticks/nbits:10.1f}   {ok}")

    print("\n[3] Carry-arrival trace (8 = 0b1000 case, watch the ripple walk):")
    nbits = 4
    x, y = 0b0111, 0b0001   # 7 + 1 = 8: carry ripples through all 4 bits
    got, ticks, arrivals = concurrent_ripple_add(x, y, nbits, trace=True)
    print(f"    {x} + {y} = {got} (expected {x+y}), total {ticks} ticks")
    for i, t in enumerate(arrivals):
        if t is not None:
            print(f"    carry out of bit {i} arrived at tick {t}")

    print("\n" + "=" * 72)
    print("If ticks grow ~linearly with nbits in [2], that is true ripple-")
    print("carry behavior: the carry physically walks the word one stage at a")
    print("time, as real spikes, and the delay is the sum of per-stage spike")
    print("latencies. Concurrency does not hide it -- it makes it physical.")
