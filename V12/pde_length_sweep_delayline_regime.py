"""Final honest version: low Omega (long wavelength, true delay-line regime,
L << lambda for the channel lengths used), tuned drive/damping for SNR,
sweeping far enough to actually see the predicted XOR crossing at phase=180deg.
"""
import numpy as np
from pde_length_sweep import measure_unit, classify

Omega = 2*np.pi*0.02
c = 1.0
wavelength = 2*np.pi*c/Omega
print(f"Omega={Omega:.4f}, wavelength={wavelength:.1f}")
print(f"drive_amp=15, damping=0.001 (tuned for SNR)\n")

La = 10.0
# sweep mismatch up to half the wavelength (180 deg) -- should cross from
# XNOR-like (phase=0) through a wall (phase=90deg) to XOR-like (phase=180deg)
target_phase_degs = [0, 30, 60, 90, 120, 150, 180]
Lb_values = []
for pd in target_phase_degs:
    mismatch = (pd * np.pi/180) * c / Omega
    Lb_values.append(La + mismatch)

print(f"{'L_b':>8} {'mismatch':>9} {'phase(deg)':>11} | {'00':>7} {'01':>7} {'10':>7} {'11':>7} | regime")
print("-"*95)
for Lb, target_pd in zip(Lb_values, target_phase_degs):
    amps = measure_unit(La, Lb, Omega, c=c, drive_amp=15.0, damping=0.001,
                         n_settle=1000, n_measure=300)
    regime, agree, disagree = classify(amps, tol_ratio=0.12)
    mismatch = Lb - La
    print(f"{Lb:8.2f} {mismatch:9.2f} {target_pd:11.1f} | {amps[(0,0)]:7.5f} "
          f"{amps[(0,1)]:7.5f} {amps[(1,0)]:7.5f} {amps[(1,1)]:7.5f} | {regime}")
