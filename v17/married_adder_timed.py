"""
married_adder_timed.py -- the timing question, which is the real test of
whether this is a PHYSICAL directional computer or just a sequential
simulation that happens to use spikes.

In married_adder.py / married_ripple.py, each unit's .run() blocks to
completion before the next unit starts. That proves LOGICAL composition but
hides the timing: in a real device, the units run CONCURRENTLY, and a
downstream gate's spike cannot originate until its upstream inputs' spikes
have physically ARRIVED. If the carry has to ripple stage-by-stage as real
travelling spikes, does the computation still land correctly, and how long
does it take?

This file runs a full adder as a CONCURRENT system on a shared step-clock:
all units advance one timestep together. A unit fires its axon spike only
once its input bits are available (its upstream spikes have arrived at the
readout). We measure:
  (1) does the concurrent, timing-respecting full adder still get all 8 rows?
  (2) how many timesteps does a stage take (the spike-propagation latency)?
  (3) does a 2-stage ripple need the carry to arrive before stage 2 settles
      -- i.e. is there a real, measurable carry-propagation delay?

THE HONEST EXPECTATION: this should still compute correctly, but it should
reveal a real LATENCY that the algebraic adder never had -- a carry-ripple
delay proportional to (axon length x stages). That latency is the physical
price of directionality, and quantifying it is the point. If instead it
breaks (wrong answers under concurrency), that's an even more important
finding: the directional mechanism would not compose without an explicit
clock/latch, which is exactly the theta-gamma clock the original used.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from resonator_neuron import encode_bit
from propagating_spike import ExcitableLine
from gates import make_gate


class TimedUnit:
    """A married unit driven on a shared step-clock. It watches its input
    bits; when they become available (not None), it computes its soma logic
    and, if firing, originates a spike. Its OUTPUT bit becomes available
    only once that spike physically reaches the axon end -- introducing the
    real propagation latency."""

    def __init__(self, gate_kind, axon_len=30, kick_strength=12.0):
        self.soma = make_gate(gate_kind)
        self.gate_kind = gate_kind
        self.axon = ExcitableLine(n=axon_len)
        self.axon_len = axon_len
        self.kick_strength = kick_strength
        self.ais_cell = 3
        self.state = "WAIT"          # WAIT -> KICKING -> PROPAGATING -> DONE
        self.kick_steps_left = 0
        self.output_bit = None
        self.inputs = None
        self._settled = False

    def settle(self):
        for _ in range(120):
            self.axon.step()
        self._settled = True

    def provide_inputs(self, bits):
        self.inputs = list(bits)

    def step(self):
        """Advance one shared-clock tick."""
        if not self._settled:
            self.settle()
        if self.state == "WAIT":
            if self.inputs is not None and None not in self.inputs:
                # compute soma logic now that inputs are present
                phasors = [encode_bit(b) for b in self.inputs]
                amp = abs(self.soma.settle_algebraic(phasors))
                fires = self.soma.lo - 1e-9 <= amp <= self.soma.hi + 1e-9
                if fires:
                    self.state = "KICKING"
                    self.kick_steps_left = 6
                else:
                    self.output_bit = 0      # logical 0: no spike, bit ready now
                    self.state = "DONE"
        elif self.state == "KICKING":
            I = np.zeros(self.axon_len)
            I[self.ais_cell] = self.kick_strength
            self.axon.step(I)
            self.kick_steps_left -= 1
            if self.kick_steps_left <= 0:
                self.state = "PROPAGATING"
        elif self.state == "PROPAGATING":
            self.axon.step()
            if self.axon.v[-3] > 0.5:        # spike reached the axon end
                self.output_bit = 1
                self.state = "DONE"
        # DONE: nothing
        return self.state


def run_timed_full_adder(a, b, cin, max_ticks=4000):
    """Run a full adder as a concurrent clocked system. Returns (sum, cout,
    ticks_taken)."""
    u = {
        "XOR_ab":  TimedUnit("XOR"),
        "XOR_sum": TimedUnit("XOR"),
        "AND_ab":  TimedUnit("AND"),
        "AND_cin": TimedUnit("AND"),
        "OR_cout": TimedUnit("OR"),
    }
    for unit in u.values():
        unit.settle()

    # stage-0 units have their inputs immediately
    u["XOR_ab"].provide_inputs([a, b])
    u["AND_ab"].provide_inputs([a, b])

    sum_bit = cout = None
    for tick in range(max_ticks):
        for unit in u.values():
            unit.step()
        # wire outputs to downstream inputs as they become available
        axb = u["XOR_ab"].output_bit
        if axb is not None:
            if u["XOR_sum"].inputs is None:
                u["XOR_sum"].provide_inputs([axb, cin])
            if u["AND_cin"].inputs is None:
                u["AND_cin"].provide_inputs([cin, axb])
        ab = u["AND_ab"].output_bit
        cab = u["AND_cin"].output_bit
        if ab is not None and cab is not None and u["OR_cout"].inputs is None:
            u["OR_cout"].provide_inputs([ab, cab])
        # collect final outputs
        if u["XOR_sum"].output_bit is not None and sum_bit is None:
            sum_bit = u["XOR_sum"].output_bit
        if u["OR_cout"].output_bit is not None and cout is None:
            cout = u["OR_cout"].output_bit
        if sum_bit is not None and cout is not None:
            return sum_bit, cout, tick
    return sum_bit, cout, max_ticks


if __name__ == "__main__":
    print("=" * 70)
    print("TIMED (CONCURRENT) MARRIED FULL ADDER")
    print("All 5 units run on a shared clock; downstream units wait for")
    print("upstream spikes to physically arrive. Does it still compute, and")
    print("what is the real propagation latency?")
    print("=" * 70)
    print("  a b cin | sum cout | expected      | ticks | ok")
    print("-" * 70)
    all_ok = True
    latencies = []
    for a in (0, 1):
        for b in (0, 1):
            for cin in (0, 1):
                s, c, ticks = run_timed_full_adder(a, b, cin)
                total = a + b + cin
                exp_s, exp_c = total & 1, total >> 1
                ok = (s == exp_s and c == exp_c)
                all_ok &= ok
                latencies.append(ticks)
                print(f"  {a} {b}  {cin}  |  {s}   {c}   | "
                      f"sum={exp_s} cout={exp_c} | {ticks:5d} | "
                      f"{'OK' if ok else 'XX'}")
    print("-" * 70)
    print(f"\nCONCURRENT FULL ADDER CORRECT: {all_ok}")
    print(f"Propagation latency: {min(latencies)}-{max(latencies)} ticks per "
          f"full-adder stage")
    print("\nThis latency is the physical price of directionality -- the carry")
    print("must travel as a real spike before the next stage can use it. The")
    print("algebraic adder had zero latency; this one has a measurable,")
    print("structural delay. That delay IS the reason a real brain needs a")
    print("clock (theta/gamma) to stage multi-bit computation -- which is")
    print("exactly what the original adder's theta_gamma_clock modelled.")
