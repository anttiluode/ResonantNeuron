"""
married_unit.py -- can the interference SOMA (the resonator gate) be married
to the directional excitable AXON (the v14 spike) to make ONE complete unit
that both COMPUTES (logic via interference amplitude) and SENDS DIRECTIONALLY
(a spike that goes to the axon, not back into the dendrites)?

THE SEAM, stated honestly before building:
  - The resonator soma outputs a STEADY-STATE AMPLITUDE |s|: a static settled
    number. Logic = which band |s| lands in (gates.py).
  - The excitable axon needs a TRANSIENT super-threshold KICK to originate a
    spike. Its input is "did something cross threshold," not "how loud is the
    standing wave."
  These are different kinds of signal. The marriage question is whether the
  soma's amplitude band can drive the axon's threshold so that:
     logical 1  -> soma amplitude in the firing band -> kick the axon ->
                   a spike ORIGINATES and propagates toward the axon end;
     logical 0  -> soma amplitude outside the band -> no kick -> no spike;
  AND whether the axon's nonlinearity PRESERVES the soma's computation
  (the gate's truth table) rather than corrupting it.

The thing that could break it (and which this file tests for):
  1. BAND DIRECTION MISMATCH. Some gates fire on LOW |s| (XOR fires when
     |s|~0) and some on HIGH |s| (XNOR fires when |s|~2). A simple
     "kick the axon when |s| > threshold" only handles the HIGH-firing
     gates. The LOW-firing gates need "kick when |s| is INSIDE [lo,hi]",
     i.e. the kick must respect the BAND, not just a one-sided threshold.
  2. AMPLITUDE-DEPENDENT SPIKE CORRUPTION. If the kick strength scales with
     |s|, a marginal |s| might give a weak, non-propagating kick -- the
     gate says 1 but the axon fails to fire, breaking the truth table.
     The fix is a CLEAN COMPARATOR: band membership -> fixed-strength kick.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from resonator_neuron import ResonatorNeuron, encode_bit
from propagating_spike import ExcitableLine
from gates import make_gate, GATES_2IN, TRUTH


class MarriedUnit:
    """A resonator soma whose logical output (band membership) originates a
    directional spike on an excitable axon. The COMPARATOR between them is
    the key design choice: the soma's amplitude band -> a clean, fixed
    super-threshold kick at the axon's origination site (or no kick)."""

    def __init__(self, gate_kind, axon_len=40, kick_strength=12.0):
        self.soma = make_gate(gate_kind)
        self.gate_kind = gate_kind
        self.axon_len = axon_len
        self.kick_strength = kick_strength
        # the AIS sits at cell 5 (near the soma end); axon extends to the right
        self.ais_cell = 5

    def soma_fires(self, bits):
        """The soma's logical output: is |s| inside the firing band?"""
        phasors = [encode_bit(b) for b in bits]
        amp = abs(self.soma.settle_algebraic(phasors))
        return self.soma.lo - 1e-9 <= amp <= self.soma.hi + 1e-9, amp

    def run(self, bits, n_run=900):
        """Compute the gate, and if it fires, originate a spike on the axon.
        Returns (logical_output, spike_reached_axon_end, axon_endpoint_amp)."""
        fires, amp = self.soma_fires(bits)
        axon = ExcitableLine(n=self.axon_len)
        for _ in range(150):
            axon.step()  # settle to rest

        if fires:
            # CLEAN COMPARATOR: band membership -> fixed-strength kick,
            # NOT amplitude-scaled. This is the design decision that keeps
            # the axon's firing decoupled from the soma's marginal amplitude.
            for t in range(6):
                I = np.zeros(self.axon_len)
                I[self.ais_cell] = self.kick_strength
                axon.step(I)

        # let any spike propagate
        reached_end = False
        endpoint_amps = []
        for _ in range(n_run):
            axon.step()
            endpoint_amps.append(axon.v[-5])  # near the axon (far) end
            if axon.v[-5] > 0.5:
                reached_end = True
        return fires, reached_end, max(endpoint_amps)


def test_gate_preserved(gate_kind):
    """Does the married unit reproduce the gate's truth table -- i.e. does
    the axon fire (spike reaches the far end) exactly when the soma's logic
    says 1, and stay silent when it says 0?"""
    unit = MarriedUnit(gate_kind)
    rows = []
    correct = 0
    for a in (0, 1):
        for b in (0, 1):
            logical, spike_reached, amp = unit.run([a, b])
            expected = TRUTH[gate_kind](a, b)
            # the WHOLE unit's output is "did a spike reach the axon end"
            unit_output = 1 if spike_reached else 0
            ok = (unit_output == expected)
            correct += ok
            rows.append((a, b, expected, logical, unit_output, ok))
    return rows, correct


if __name__ == "__main__":
    print("=" * 78)
    print("MARRIED UNIT: resonator soma (logic) + excitable axon (directional")
    print("spike). Does the spike-at-the-axon-end reproduce each gate's table?")
    print("=" * 78)

    all_perfect = True
    for gate_kind in GATES_2IN:
        rows, correct = test_gate_preserved(gate_kind)
        status = "PASS" if correct == 4 else f"FAIL ({correct}/4)"
        if correct != 4:
            all_perfect = False
        print(f"\n{gate_kind:5s} [{status}]")
        print(f"   a b | expected | soma_fires | spike@axon | ok")
        for a, b, exp, logical, out, ok in rows:
            print(f"   {a} {b} |    {exp}     |    {int(logical)}       |"
                  f"     {out}      | {'OK' if ok else 'XX'}")

    print("\n" + "=" * 78)
    print(f"ALL GATES PRESERVED THROUGH THE MARRIAGE: {all_perfect}")
    print("=" * 78)
    if all_perfect:
        print("The interference soma's logic survives being read out as a")
        print("directional spike: the axon fires (spike reaches the far end)")
        print("exactly when the gate's truth table says 1. Computation AND")
        print("direction in one unit.")
