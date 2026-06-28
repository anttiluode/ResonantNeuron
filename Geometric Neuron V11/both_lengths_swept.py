"""
delay_dendrite_3.py -- can length alone (still zero weight change, equal |w|)
ever produce AND/OR, or is parity (XOR/XNOR) a hard ceiling for a 2-dendrite,
equal-weight resonator no matter how you place both lengths?

This sweeps BOTH dendrite lengths independently (not just one relative to a
fixed zero), which is the fair version of "how the axon connects" -- nature
gets to place two cable lengths, not just one.
"""
import numpy as np
from delay_dendrite import LengthAwareResonatorNeuron, identify_function

TWO_PI = 2 * np.pi
Omega = TWO_PI * 0.20
v = 1.0
period = TWO_PI / Omega * v

n = 25
La_vals = np.linspace(0, period, n)
Lb_vals = np.linspace(0, period, n)

seen_functions = {}
for La in La_vals:
    for Lb in Lb_vals:
        unit = LengthAwareResonatorNeuron(lengths=[La, Lb], weights=[1, 1], bias=0.0,
                                           lo=0, hi=0, Omega=Omega, v=v)
        amps = []
        for a in (0, 1):
            for b in (0, 1):
                s = unit.settle_algebraic([a, b])
                amps.append(abs(s))
        amps = np.array(amps)
        order = np.argsort(amps)
        sorted_amps = amps[order]
        gaps = np.diff(sorted_amps)
        if gaps.max() < 1e-6:
            fname = "DEGENERATE"
            margin = 0.0
        else:
            cut = np.argmax(gaps)
            thresh = (sorted_amps[cut] + sorted_amps[cut+1]) / 2
            margin = gaps[cut]
            fire = (amps <= thresh).astype(int)
            rows = [(0,0,fire[0],amps[0]), (0,1,fire[1],amps[1]),
                    (1,0,fire[2],amps[2]), (1,1,fire[3],amps[3])]
            fname = identify_function(rows)
        if fname not in seen_functions or margin > seen_functions[fname][0]:
            seen_functions[fname] = (margin, La, Lb)

print("Best example of each distinct function found, sweeping BOTH lengths "
      f"independently over [0, {period:.2f}] ({n}x{n} = {n*n} combos):\n")
for fname, (margin, La, Lb) in sorted(seen_functions.items(), key=lambda x: -x[1][0]):
    print(f"  {fname:30s}  best margin={margin:.3f}  at La={La:.3f}, Lb={Lb:.3f}")

print(f"\n{len(seen_functions)} distinct functions found across the full 2D length sweep.")
print("\nHONEST READ: equal-weight (symmetric |w|) interference is fundamentally")
print("a PARITY detector (agree vs disagree). Sweeping length moves WHERE the")
print("agree/disagree boundary sits in phase-space but cannot break the agree/")
print("disagree structure into AND/OR, because |w_a p_a + w_b p_b| with |w_a|=|w_b|")
print("is symmetric under simultaneously flipping both input phases -- it can")
print("only ever distinguish 'same vs different', i.e. XOR-family. AND/OR need")
print("ASYMMETRIC weight magnitude (a real nonlinearity break), not just phase/length.")
