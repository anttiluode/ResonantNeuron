"""
geometric_bias_candidate.py -- can a STRUCTURAL asymmetry (not a learned
weight, not an arbitrary bias constant) supply the thing AND/OR needs?

Candidate: an extra dendrite carrying a FIXED, always-on reference signal
(e.g. a constant phasor representing a constitutively-active synapse or a
leak channel) -- geometrically just "one more cable, always at phase 0,
always 1". This is the most physically minimal candidate for "bias" because
it doesn't require an arbitrary tunable constant injected into the soma --
it's just counting one more dendrite, the same primitive as all the others.
"""
import numpy as np
from delay_dendrite import encode_bit, identify_function

TWO_PI = 2*np.pi
Omega = TWO_PI*0.20

def soma_amp(a, b, w_ref, phi_ref=0.0):
    """2 real inputs + 1 fixed 'always on' reference dendrite, weight w_ref."""
    pa = encode_bit(a)
    pb = encode_bit(b)
    p_ref = w_ref * np.exp(1j*phi_ref)  # constant, input-independent contribution
    return abs(pa + pb + p_ref)

print("="*78)
print("DOES A THIRD, CONSTANT-PHASE 'REFERENCE DENDRITE' (no input, just always-on)")
print("FUNCTION AS A GEOMETRIC BIAS AND UNLOCK AND/OR?")
print("="*78)
print(f"\n{'w_ref':>7} | 00 amp | 01 amp | 10 amp | 11 amp | function")
print("-"*70)
for w_ref in [-3, -2, -1, 0, 1, 2, 3]:
    amps = [soma_amp(a,b,w_ref) for a in (0,1) for b in (0,1)]
    amps = np.array(amps)
    gaps = np.diff(np.sort(amps))
    if gaps.max() < 1e-6:
        fname = "DEGENERATE"
    else:
        thresh = np.sort(amps)[np.argmax(gaps)] + gaps.max()/2
        fire = (amps <= thresh).astype(int)
        rows = list(zip([0,0,1,1],[0,1,0,1],fire,amps))
        fname = identify_function(rows)
    print(f"{w_ref:7.1f} | " + " | ".join(f"{x:6.3f}" for x in amps) + f" | {fname}")

print("\nHONEST READ:")
print("A third dendrite that ALWAYS fires (input-independent) IS structurally just")
print("a bias term wearing a dendrite costume: w_ref*exp(i*phi_ref) is a constant")
print("added to the soma sum, identical in form to gates.py's explicit bias. So")
print("this DOES geometrically realize bias -- but the geometric cost is an extra")
print("CONSTITUTIVELY ACTIVE synapse (something that fires with NO upstream input),")
print("which is a real, separate biological mechanism (tonic/leak conductance, or a")
print("synapse onto a constant-rate pacemaker), not free from 'just routing wires'.")
print("It confirms the wall rather than evading it: AND/OR cost you a dedicated,")
print("always-on input -- nature would need to GROW that, not just route cable length.")
