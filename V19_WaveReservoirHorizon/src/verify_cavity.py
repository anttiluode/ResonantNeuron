"""Is the cavity's long-horizon order-memory real, or a residual-energy cue?
Check: at delay 1900, with dissipation matched to 32-step half-life, is the
field magnitude far below the readout noise (=> would be a leak/bug) or above it
(=> a real surviving trace)? Also confirm the order signal exceeds the noise."""
import sys, os, numpy as np
sys.path.insert(0,os.path.dirname(__file__))
from reservoir import WaveField, make_magnetron, coarse, disk
N=64; dt=0.6
insM,_,cM,sats,rs=make_magnetron(N,return_sats=True)
def mk(): return WaveField(N,dt=dt,inside=insM,b=np.zeros((N,N)))  # matched damping was ~0 for cavity
def run(order):
    f=mk(); f.reset(); mags=[1.,2.,3.]
    for mi in order:
        f.inject(cM,amp=mags[mi],sigma=2.0)
        for _ in range(16): f.step()
    for _ in range(1900): f.step()
    return f.u.copy()
u012=run((0,1,2)); u210=run((2,1,0))
c012=coarse(u012.reshape(N,N),12); c210=coarse(u210.reshape(N,N),12)
print(f"delay 1900 field RMS: {np.sqrt((u012**2).mean()):.4e}")
print(f"coarse feature RMS:   {np.sqrt((c012**2).mean()):.4e}")
print(f"order-diff ||012-210||: {np.linalg.norm(c012-c210):.4e}")
print(f"readout noise per feat: 2e-2")
print(f"signal/noise ratio:   {np.linalg.norm(c012-c210)/(0.02*12):.1f}")
# also: is the surviving field a near-DC pedestal or structured? check spatial variance
print(f"field spatial std/mean-abs: {u012.std()/ (np.abs(u012).mean()+1e-12):.2f}  (>1 => structured, not flat DC)")
