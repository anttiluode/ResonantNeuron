"""Look at the RAW agree-disagree gap as a continuous function of phase,
not through my classify() threshold, to see the true shape of the
transition -- is it actually flat/wide, or does my arbitrary 12% threshold
just make a smoothly-narrow transition LOOK like a wide flat band?
"""
import numpy as np
from pde_length_sweep import measure_unit

Omega = 2*np.pi*0.02
c = 1.0
La = 10.0

print(f"{'phase':>6} | {'agree':>8} {'disagree':>8} | {'signed gap':>10}")
print("-"*50)
for pd in range(0, 191, 15):
    mismatch = (pd*np.pi/180)*c/Omega
    Lb = La + mismatch
    amps = measure_unit(La, Lb, Omega, c=c, drive_amp=15.0, damping=0.001,
                         n_settle=1000, n_measure=300)
    agree = (amps[(0,0)]+amps[(1,1)])/2
    disagree = (amps[(0,1)]+amps[(1,0)])/2
    gap = agree - disagree
    print(f"{pd:6d} | {agree:8.5f} {disagree:8.5f} | {gap:+10.5f}")
