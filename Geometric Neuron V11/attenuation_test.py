"""
delay_dendrite_5.py -- real cables don't just delay/rotate a phasor, they
ATTENUATE it (longer cable -> weaker arrival, e.g. exp(-alpha*L)). This is a
SECOND physical consequence of length, distinct from phase rotation, and it
breaks the |w_a|=|w_b| symmetry that delay_dendrite_3.py showed caps a unit
at parity-only (XOR/XNOR). Does attenuation-from-length unlock AND/OR for
free, the same way rotation-from-length gave XOR/XNOR for free?
"""
import numpy as np
from delay_dendrite import encode_bit, identify_function

TWO_PI = 2*np.pi
Omega = TWO_PI*0.20
v = 1.0
period = TWO_PI/Omega*v

def carry(L, alpha, bit):
    """A cable of length L: rotates phase by Omega*L/v AND attenuates by exp(-alpha*L)."""
    phi = (Omega*L/v) % TWO_PI
    atten = np.exp(-alpha*L)
    return atten * encode_bit(bit) * np.exp(1j*phi)

def best_function(La, Lb, alpha):
    amps = []
    for a in (0,1):
        for b in (0,1):
            s = carry(La, alpha, a) + carry(Lb, alpha, b)
            amps.append(abs(s))
    amps = np.array(amps)
    order = np.argsort(amps)
    sorted_amps = amps[order]
    gaps = np.diff(sorted_amps)
    if gaps.max() < 1e-6:
        return "DEGENERATE", 0.0
    cut = np.argmax(gaps)
    thresh = (sorted_amps[cut]+sorted_amps[cut+1])/2
    margin = gaps[cut]
    fire = (amps <= thresh).astype(int)
    rows = [(0,0,fire[0],amps[0]),(0,1,fire[1],amps[1]),(1,0,fire[2],amps[2]),(1,1,fire[3],amps[3])]
    return identify_function(rows), margin

print("="*78)
print("DOES LENGTH-INDUCED ATTENUATION (not just rotation) unlock AND/OR?")
print("="*78)
print(f"\nAttenuation coefficient alpha sweep, La=0 fixed, Lb swept full period,")
print(f"watching for AND/OR/NAND/NOR appearing (not just XOR/XNOR/degenerate):\n")

for alpha in [0.0, 0.05, 0.15, 0.30, 0.50]:
    found = {}
    for Lb in np.linspace(0, period, 60):
        fname, margin = best_function(0.0, Lb, alpha)
        if fname not in found or margin > found[fname][0]:
            found[fname] = (margin, Lb)
    names = sorted(found.keys())
    print(f"  alpha={alpha:.2f}: functions found = {names}")

print("\nHONEST READ:")
print("If AND/OR/NAND/NOR never appear even with strong attenuation, the cap is")
print("structural: a TWO-INPUT SUM of two unit-circle phasors is ALWAYS symmetric")
print("under swapping which input is 'small', so attenuation changes the radius")
print("of the parity boundary but still can't break it into a true majority/AND")
print("split -- you'd need a THIRD, asymmetric structural element (e.g. a biased")
print("self-term, or 3+ dendrites) to get AND/OR. This would match gates.py in")
print("v_prior, which DID need explicit nonzero bias/3rd terms for AND/OR/NAND/NOR,")
print("not just two equal-magnitude phasors. Let's check what gates.py actually used.")
