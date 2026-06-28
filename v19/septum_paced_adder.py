"""
septum_paced_adder.py -- close the loop the whole arc was building toward.

v16/v17 ran the resonator adder on a HAND-CODED scheduler (a Python loop that
advanced the carry "one stage per tick"). The papers (Vardalakis 2024, Nunez &
Buno 2021) say the brain does this with a GENERATED theta rhythm from the
septum, gating computation by phase. This file replaces the hand-coded clock
with the real Kuramoto septum from septum.py:

  - the septum generates theta (no external clock -- it self-organizes);
  - each THETA CYCLE is one computational stage: when theta crosses its peak,
    the next adder stage is allowed to settle and advance the carry;
  - the GAMMA-fast settling happens within the theta cycle (the resonator soma
    + axon doing its work between theta peaks);
  - downstream firing (a stage completing) is fed BACK to the septum as the
    reset input X(t) -- closing the loop, exactly the accident's feedback
    shape (downstream taps -> coupler).

So the multi-bit addition runs on a theta clock that the system GENERATES and
that the computation itself resets -- not a scheduler we impose. This is the
network-level analogue of what v18 did for the field: the timing that earlier
folders assumed is now produced by the same edge-of-chaos pacemaker mechanism
that produced the original accident.

We keep the arithmetic itself at the verified algebraic level (the resonator
gate truth tables, proven exact in the repo core) and let the SEPTUM decide
WHEN each stage computes. The result: a theta-paced ripple adder whose stage
advance is driven by generated theta peaks, with the carry rippling one theta
cycle at a time -- the literal "theta-gamma clock" the original adder only
modelled by assumption.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from septum import KuramotoSeptum
from gates import make_gate, gate_out


def _full_adder_bits(a, b, cin):
    """One full-adder stage at the verified algebraic resonator level.
    Returns (sum_bit, carry_out). Each gate is a resonator unit (repo core)."""
    G = {k: make_gate(k) for k in ("XOR", "AND", "OR")}
    axb = gate_out(G["XOR"], [a, b])
    s = gate_out(G["XOR"], [axb, cin])
    ab = gate_out(G["AND"], [a, b])
    cab = gate_out(G["AND"], [cin, axb])
    cout = gate_out(G["OR"], [ab, cab])
    return s, cout


def theta_paced_add(x, y, nbits, verbose=False, max_seconds=3.0):
    """Add two nbits integers, advancing one bit-stage per GENERATED theta
    cycle from the Kuramoto septum. The septum is NOT given an external clock;
    it self-organizes theta, and we detect its peaks to gate stage advance.
    Downstream stage completion is fed back as the septum's reset input."""
    sep = KuramotoSeptum(n=50, f0=7.0, k=6.0, dt=1e-3, seed=0)
    fs = 1000.0                      # 1 ms steps
    carry = 0
    out = 0
    stage = 0                        # which bit we are computing
    last_phase = None
    reset_input = 0.0
    theta_trace = []
    stage_times = []
    t = 0
    max_steps = int(max_seconds * fs)

    # let the septum lock into theta first
    for _ in range(300):
        sep.step(0.0)

    while stage < nbits and t < max_steps:
        I_theta = sep.step(reset_input)
        phase = sep.theta_phase()
        theta_trace.append(I_theta)
        reset_input = 0.0            # reset is a brief feedback pulse, cleared

        # detect a theta peak: phase wraps through 0 (cos maximal)
        peaked = (last_phase is not None and last_phase > 2.5 and phase < 0.5)
        last_phase = phase

        if peaked:
            # ONE theta cycle = compute this bit-stage
            a = (x >> stage) & 1
            b = (y >> stage) & 1
            s, carry = _full_adder_bits(a, b, carry)
            out |= (s << stage)
            stage_times.append(t / fs)
            if verbose:
                print(f"    theta peak @ {t/fs:.3f}s : bit {stage}  "
                      f"a={a} b={b} -> sum={s} carry={carry}  "
                      f"(coherence {sep.coherence():.2f})")
            stage += 1
            # the stage completing fires back to the septum (closes the loop):
            # a brief reset pulse, the downstream->septum projection
            reset_input = 1.0
        t += 1

    out |= (carry << nbits)
    return out, np.array(theta_trace), stage_times


if __name__ == "__main__":
    print("=" * 72)
    print("THETA-PACED RIPPLE ADDER -- stage advance driven by GENERATED theta")
    print("(the septum self-organizes the clock; the carry ripples one theta")
    print(" cycle at a time; stage completion resets the septum -- loop closed)")
    print("=" * 72)

    print("\n[1] Worked example (verbose), 5 + 3 on 4 bits:")
    got, theta, times = theta_paced_add(5, 3, 4, verbose=True)
    print(f"    result: 5 + 3 = {got}  (expected {5+3})  "
          f"{'OK' if got == 8 else 'MISMATCH'}")
    if len(times) > 1:
        dt_theta = np.diff(times)
        print(f"    mean theta period between stages: {dt_theta.mean()*1000:.0f} ms "
              f"({1/dt_theta.mean():.1f} Hz) -- one carry hop per theta cycle")

    print("\n[2] Correctness on random additions (theta-paced):")
    rng = np.random.default_rng(3)
    for nbits, ntrials in [(3, 12), (4, 8)]:
        correct = 0
        for _ in range(ntrials):
            a = int(rng.integers(0, 2**nbits))
            b = int(rng.integers(0, 2**nbits))
            g, _, _ = theta_paced_add(a, b, nbits)
            if g == a + b:
                correct += 1
            else:
                print(f"    MISMATCH {a}+{b}={a+b} got {g}")
        print(f"    {nbits}-bit: {correct}/{ntrials} correct "
              f"({'PASS' if correct == ntrials else 'FAIL'})")

    print("\n" + "=" * 72)
    print("The addition runs on a theta clock the SYSTEM GENERATES (a Kuramoto")
    print("septum), not a scheduler we impose -- and the computation feeds back")
    print("to reset that clock. The 'theta-gamma clock' the original adder")
    print("assumed is now produced by the same edge-of-chaos pacemaker that")
    print("produced the original accident.")
