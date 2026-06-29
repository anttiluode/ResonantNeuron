"""
Verify the load-bearing physics BEFORE building on it:
does adding a local restoring term  u_tt + b u_t + w0^2 u = c^2 lap(u)
actually make a patch resonate at frequency f0 = w0/2pi, i.e. respond
maximally to a chirp input at f0 and weakly off it?

If this fails, "each compartment to its own frequency" is just words.
"""
import numpy as np

def driven_point(w0, b, c, dt, drive_freqs, T=4000):
    """Single-cell-ish: drive one point sinusoidally, measure steady-state amplitude.
       Discretize u_tt + b u_t + w0^2 u = F(t)   (lap=0 for an isolated cell)."""
    resp = []
    for f in drive_freqs:
        w = 2*np.pi*f
        u=0.0; up=0.0; amps=[]
        for n in range(T):
            F = np.sin(w*n*dt)
            # (u_next -2u+up)/dt^2 + b(u_next-up)/(2dt) + w0^2 u = F
            A = 1/dt**2 + b/(2*dt)
            rhs = F - w0**2*u + (2*u-up)/dt**2 + b*up/(2*dt) - up/dt**2*0
            # solve cleanly:
            u_next = (2*u - up + dt**2*(F - w0**2*u) - 0 ) # undamped base
            u_next = (2*u - (1-b*dt/2)*up + dt**2*(F - w0**2*u))/(1+b*dt/2)
            up=u; u=u_next
            if n>T//2: amps.append(abs(u))
        resp.append(np.max(amps))
    return np.array(resp)

dt=0.05; b=0.3; c=0.5
freqs=np.linspace(0.2,3.0,30)
for f0 in [0.5, 1.0, 2.0]:
    w0=2*np.pi*f0
    r=driven_point(w0,b,c,dt,freqs)
    peak=freqs[np.argmax(r)]
    print(f"target f0={f0:.2f} Hz  ->  measured peak response at {peak:.2f} Hz   (ratio {peak/f0:.2f})")
