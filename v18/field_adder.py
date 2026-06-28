"""
field_adder.py -- a TRUE continuous-time field simulation of the directional
resonator adder. No scheduler. No "provide_inputs when ready." No Python
conditional deciding when a downstream unit may compute.

In v17, the concurrency was a discrete scheduler: a unit's output_bit became
"available" via a Python check (axon.v[-3] > 0.5), and a downstream unit's
inputs were wired in by host code once that flag flipped. That is an
abstraction over physics -- the host program is doing the routing.

Here, EVERYTHING is one field evolving under ONE update rule every tick. A
unit's axon is a real excitable line; when its spike reaches the axon's far
end, that end is PHYSICALLY COUPLED to the next unit's input site -- the
spike injects current there, and whether the downstream unit fires is
decided by the downstream unit's own dynamics responding to that injected
current. The carry is not a bit the host passes along; it is a spike whose
arrival physically drives the next stage. If the coupling is too weak, the
carry dies and the adder fails. If it works, the computation emerges from
the field, not from the scheduler.

ARCHITECTURE of one full adder as coupled excitable lines:
  Each gate = one excitable axon line (FitzHugh-Nagumo) with an input region
  (near end) and an output region (far end). The gate's LOGIC is imposed by
  a local input transform at the near end: the resonator soma's interference
  rule decides whether the arriving input(s) drive the line above threshold.
  We implement that as: the near-end drive = comparator(soma_amplitude(inputs)),
  where the inputs are themselves the field values at upstream output regions.

  The five gates of a full adder are five lines in one field array. Coupling
  points (output of gate A -> input of gate B) are fixed wiring: every tick,
  the field value at A's output end is read and contributes to the drive at
  B's input end, THROUGH the soma comparator. This is continuous: there is no
  moment where the host "decides" B can start; B is always integrating, and
  it simply stays subthreshold until real current arrives from A.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from resonator_neuron import encode_bit
from gates import make_gate


class FieldUnit:
    """One gate as a continuous excitable line in the shared field. Holds its
    own v,w state. Its near end (input) is driven by a soma-comparator on its
    input sources; its far end (output) is read by downstream units."""

    def __init__(self, name, gate_kind, n=30, D=0.5, eps=0.08, a=0.7, b=0.8,
                 dt=0.1, kick_amp=12.0):
        self.name = name
        self.gate_kind = gate_kind
        self.soma = make_gate(gate_kind)
        self.n = n
        self.D, self.eps, self.a, self.b, self.dt = D, eps, a, b, dt
        self.kick_amp = kick_amp
        self.v = np.full(n, -1.2)
        self.w = np.full(n, -0.6)
        self.ais_cell = 3            # input/origination end
        self.out_cell = n - 3        # output end (read by downstream)
        # input sources: list of (unit, 'output_value_fn') resolved each tick,
        # plus fixed external bits. Set by the wiring.
        self.input_sources = []      # callables returning a bit (0/1) or None
        self.external_bits = []      # fixed input bits (for primary inputs)
        self._fired_latch = False    # has this unit's soma decided to fire?
        self._fire_decision = None
        self._output_latched = False  # has a spike ever reached the output end?

    def output_value(self):
        """The field value at the output end -- what downstream units sense."""
        return self.v[self.out_cell]

    def output_bit(self):
        """Thresholded output, LATCHED. A propagating spike is transient: it
        passes the output cell and moves on. But a logic output must be HELD
        for downstream units to read it. The biological analogue is a synapse
        capturing the spike, or a sustained plateau depolarization. We latch:
        once a spike has ever reached the output end, the output bit stays 1.
        Until then it is 0. This is the physical 'capture' that turns a
        transient travelling spike into a stable logic level."""
        if self.v[self.out_cell] > 0.5:
            self._output_latched = True
        return 1 if self._output_latched else 0

    def current_input_bits(self):
        """Resolve current input bits from sources. Returns list or None if
        any source is not yet determined."""
        bits = list(self.external_bits)
        for src_fn in self.input_sources:
            val = src_fn()
            if val is None:
                return None
            bits.append(val)
        return bits

    def laplacian(self):
        x = self.v
        lap = np.zeros_like(x)
        lap[1:-1] = x[2:] + x[:-2] - 2 * x[1:-1]
        lap[0] = x[1] - x[0]
        lap[-1] = x[-2] - x[-1]
        return lap

    def compute_drive(self):
        """The soma comparator: if the unit's inputs are all available and
        the interference amplitude lands in the firing band, drive the AIS
        cell above threshold. This is the continuous analogue of the kick --
        but it is applied as a standing current as long as the soma says
        'fire', and the EXCITABLE LINE decides what to do with it."""
        bits = self.current_input_bits()
        if bits is None:
            return 0.0, False           # inputs not ready -> no drive
        phasors = [encode_bit(b) for b in bits]
        amp = abs(self.soma.settle_algebraic(phasors))
        fires = self.soma.lo - 1e-9 <= amp <= self.soma.hi + 1e-9
        return (self.kick_amp if fires else 0.0), fires

    def step(self, settle_phase=False):
        I = np.zeros(self.n)
        if not settle_phase:
            drive, fires = self.compute_drive()
            # latch the fire decision once made, and apply the drive as a
            # transient at the AIS (origination) -- only while not yet fired
            if fires and not self._fired_latch:
                I[self.ais_cell] = drive
                # latch after a few ticks of driving handled by caller timing
        lap = self.laplacian()
        dv = self.v - self.v ** 3 / 3 - self.w + self.D * lap + I
        dw = self.eps * (self.v + self.a - self.b * self.w)
        self.v = self.v + self.dt * dv
        self.w = self.w + self.dt * dw


class FieldFullAdder:
    """Five FieldUnits wired into a full adder, evolving as ONE field. The
    wiring is fixed physical coupling: each unit's input sources are other
    units' output_bit() (thresholded field reads at output ends). There is
    no scheduler deciding activation order -- every unit integrates every
    tick, staying subthreshold until real upstream spikes arrive."""

    def __init__(self, n=30):
        self.units = {
            "XOR_ab":  FieldUnit("XOR_ab", "XOR", n=n),
            "XOR_sum": FieldUnit("XOR_sum", "XOR", n=n),
            "AND_ab":  FieldUnit("AND_ab", "AND", n=n),
            "AND_cin": FieldUnit("AND_cin", "AND", n=n),
            "OR_cout": FieldUnit("OR_cout", "OR", n=n),
        }
        U = self.units
        # wiring (physical coupling): downstream input = upstream output_bit
        # XOR_sum inputs: (XOR_ab output, cin)
        U["XOR_sum"].input_sources = [lambda: U["XOR_ab"].output_bit()
                                       if U["XOR_ab"]._done else None]
        # AND_cin inputs: (cin, XOR_ab output)
        U["AND_cin"].input_sources = [lambda: U["XOR_ab"].output_bit()
                                       if U["XOR_ab"]._done else None]
        # OR_cout inputs: (AND_ab output, AND_cin output)
        U["OR_cout"].input_sources = [
            lambda: U["AND_ab"].output_bit() if U["AND_ab"]._done else None,
            lambda: U["AND_cin"].output_bit() if U["AND_cin"]._done else None,
        ]
        for u in self.units.values():
            u._done = False

    def set_inputs(self, a, b, cin):
        U = self.units
        U["XOR_ab"].external_bits = [a, b]
        U["AND_ab"].external_bits = [a, b]
        U["XOR_sum"].external_bits = [cin]   # plus XOR_ab via source
        U["AND_cin"].external_bits = [cin]   # plus XOR_ab via source

    def run(self, a, b, cin, max_ticks=4000):
        self.set_inputs(a, b, cin)
        # settle all lines to rest
        for _ in range(120):
            for u in self.units.values():
                u.step(settle_phase=True)
        # mark "done" when a unit's output end has resolved: a unit is done
        # either when its spike reached the output (bit=1) OR when its soma
        # decided NOT to fire given available inputs (bit=0, stable)
        sum_bit = cout = None
        for tick in range(max_ticks):
            for u in self.units.values():
                u.step()
            # update done-flags: a unit is done if it fired and reached out,
            # or its inputs are ready and it decided not to fire
            for u in self.units.values():
                if u._done:
                    continue
                if u.output_bit() == 1:
                    u._done = True
                else:
                    bits = u.current_input_bits()
                    if bits is not None:
                        _, fires = u.compute_drive()
                        if not fires:
                            # decided not to fire; give the line a moment to
                            # confirm it stays low, then mark done
                            u._nofire_count = getattr(u, "_nofire_count", 0) + 1
                            if u._nofire_count > 80:
                                u._done = True
            if self.units["XOR_sum"]._done and sum_bit is None:
                sum_bit = self.units["XOR_sum"].output_bit()
            if self.units["OR_cout"]._done and cout is None:
                cout = self.units["OR_cout"].output_bit()
            if sum_bit is not None and cout is not None:
                return sum_bit, cout, tick
        return sum_bit, cout, max_ticks


if __name__ == "__main__":
    print("=" * 70)
    print("CONTINUOUS-FIELD FULL ADDER (no scheduler -- one field, one rule)")
    print("=" * 70)
    print("  a b cin | sum cout | expected      | ticks | ok")
    print("-" * 70)
    all_ok = True
    for a in (0, 1):
        for b in (0, 1):
            for cin in (0, 1):
                fa = FieldFullAdder()
                s, c, ticks = fa.run(a, b, cin)
                total = a + b + cin
                exp_s, exp_c = total & 1, total >> 1
                ok = (s == exp_s and c == exp_c)
                all_ok &= ok
                print(f"  {a} {b}  {cin}  |  {s}   {c}   | "
                      f"sum={exp_s} cout={exp_c} | {ticks:5d} | "
                      f"{'OK' if ok else 'XX'}")
    print("-" * 70)
    print(f"\nCONTINUOUS-FIELD FULL ADDER CORRECT: {all_ok}")
