"""
reservoir.py - 2D damped wave reservoir with verified absorbing boundaries.

The medium is the damped 2D wave equation (Langtangen & Linge, eq. 63):

    u^{n+1} = [ 2 u^n - (1 - b dt/2) u^{n-1} + (c dt)^2 lap(u^n) ] / (1 + b dt/2)

where b(x,y) is a spatially varying damping field (the absorbing "sponge"),
and `inside` is a boolean mask: outside it, u is forced to 0, giving a
reflecting (Dirichlet) cavity wall.

Stability (2D leapfrog): (c*dt/dx)^2 must be <= 1/2. With dx = 1 this is
(c*dt)^2 <= 1/2.

Nothing here is hyped. Every claim the surrounding experiments make is meant to
be reproducible by running them. See README.md for the honest ledger.
"""

import numpy as np


def laplacian(u):
    """5-point stencil, zero-padded -> Dirichlet (u=0) at the array border."""
    up = np.pad(u, 1, mode="constant")
    return up[:-2, 1:-1] + up[2:, 1:-1] + up[1:-1, :-2] + up[1:-1, 2:] - 4 * u


class WaveField:
    """Damped 2D wave field on a masked domain with a damping array b(x,y) and an
    optional local restoring field w0(x,y) (the "channel resonance" term).

    With w0 != 0 the equation is
        u_tt + b u_t + w0^2 u = c^2 lap(u)
    so each location has a preferred (resonant) frequency f0 = w0 / 2pi. This is
    the physical stand-in for the Ih / ion-channel resonance gradient measured by
    Narayanan & Johnston (2007): geometry sets where waves go, the w0 field sets
    what frequency each region prefers. Verified in tests/ to peak within ~3% of
    the intended f0.
    """

    def __init__(self, N, c=0.5, dt=0.6, dx=1.0, b=None, inside=None, w0=None):
        self.N = N
        self.c = c
        self.dt = dt
        self.dx = dx
        cfl = (c * dt / dx) ** 2
        if cfl > 0.5 + 1e-9:
            raise ValueError(f"unstable: (c*dt/dx)^2 = {cfl:.3f} > 0.5")
        self.b = np.zeros((N, N)) if b is None else b
        self.w0 = np.zeros((N, N)) if w0 is None else w0
        self.inside = np.ones((N, N), bool) if inside is None else inside
        self.reset()

    def reset(self):
        self.u = np.zeros((self.N, self.N))
        self.u_prev = np.zeros((self.N, self.N))

    def step(self):
        bdt = self.b * self.dt / 2.0
        lap = laplacian(self.u) / (self.dx ** 2)
        restoring = self.w0 ** 2 * self.u
        u_next = (2 * self.u - (1 - bdt) * self.u_prev
                  + (self.c * self.dt) ** 2 * lap
                  - self.dt ** 2 * restoring) / (1 + bdt)
        u_next[~self.inside] = 0.0
        self.u_prev = self.u
        self.u = u_next

    def inject(self, pos, amp=1.0, sigma=2.0):
        """Add a localized Gaussian displacement kick at pos=(row, col)."""
        r0, c0 = pos
        rr, cc = np.meshgrid(np.arange(self.N), np.arange(self.N), indexing="ij")
        bump = amp * np.exp(-((rr - r0) ** 2 + (cc - c0) ** 2) / (2 * sigma ** 2))
        self.u = self.u + bump * self.inside

    def energy(self):
        return float(np.sum(self.u ** 2))


# ---------------------------------------------------------------- geometries

def sponge_edges(N, width, bmax):
    """Damping ramping 0 -> bmax over `width` cells at all four edges."""
    b = np.zeros((N, N))
    ramp = np.linspace(0, 1, width) ** 2
    for k in range(width):
        v = bmax * ramp[k]
        b[k, :] = np.maximum(b[k, :], v)
        b[N - 1 - k, :] = np.maximum(b[N - 1 - k, :], v)
        b[:, k] = np.maximum(b[:, k], v)
        b[:, N - 1 - k] = np.maximum(b[:, N - 1 - k], v)
    return b


def disk(N, center, radius):
    rr, cc = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    return (rr - center[0]) ** 2 + (cc - center[1]) ** 2 <= radius ** 2


def capsule(N, p0, p1, halfwidth):
    """Thick line segment (a channel) between p0 and p1."""
    rr, cc = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    p0 = np.array(p0, float)
    p1 = np.array(p1, float)
    d = p1 - p0
    L2 = d @ d + 1e-9
    pts = np.stack([rr.ravel(), cc.ravel()], 1).astype(float)
    t = np.clip(((pts - p0) @ d) / L2, 0, 1)
    proj = p0 + t[:, None] * d
    dist = np.linalg.norm(pts - proj, axis=1).reshape(N, N)
    return dist <= halfwidth


def make_open_box(N, width=16, bmax=1.5):
    """Open medium: full grid interior, strong absorbing sponge at all edges.

    The sponge must be strong/wide enough to drain even slow near-DC components,
    otherwise the forgetting curve plateaus *inside* the true horizon and looks
    like durable memory when it is not (this was a real bug we hit; see README).
    """
    inside = np.ones((N, N), bool)
    return inside, sponge_edges(N, width, bmax)


def make_magnetron(N=64, rc=9, rs=6, orbit=21, n_sat=8, chan=2, outlet=2,
                   sp_w=12, sp_max=1.5, return_sats=False):
    """Berglund magnetron cavity: central disk + n_sat satellites + channels +
    one outlet to the right edge. Reflecting walls everywhere; absorbing sponge
    only in the outlet near the right edge."""
    c0 = (N // 2, N // 2)
    inside = disk(N, c0, rc)
    sat_centers = []
    for k in range(n_sat):
        ang = 2 * np.pi * k / n_sat
        sc = (int(round(c0[0] + orbit * np.sin(ang))),
              int(round(c0[1] + orbit * np.cos(ang))))
        sat_centers.append(sc)
        inside |= disk(N, sc, rs)
        inside |= capsule(N, c0, sc, chan)
    right_sat = (c0[0], c0[1] + orbit)
    inside |= capsule(N, right_sat, (c0[0], N - 1), outlet)
    b = np.zeros((N, N))
    ramp = np.linspace(0, 1, sp_w) ** 2
    for k in range(sp_w):
        b[:, N - 1 - k] = np.maximum(b[:, N - 1 - k], sp_max * ramp[k])
    b *= inside
    if return_sats:
        return inside, b, c0, sat_centers, rs
    return inside, b, c0


def tuned_w0_field(N, sat_centers, rs, f0_list, dt):
    """Build a w0(x,y) field: each satellite disk gets its own resonant frequency.
    'each to its own frequency' - the theta-gamma-nesting reading of the magnetron.
    f0_list are frequencies in cycles-per-step units (kept small for stability:
    w0*dt must stay well below 1)."""
    w0 = np.zeros((N, N))
    for sc, f0 in zip(sat_centers, f0_list):
        d = disk(N, sc, rs)
        w0[d] = 2 * np.pi * f0
    # safety: cap so the restoring term stays stable (w0*dt < ~1)
    w0 = np.minimum(w0, 0.9 / dt)
    return w0


def coarse(field2d, k):
    """Block-mean coarse-grain to a k x k feature vector (prevents pixel-cheating)."""
    N = field2d.shape[0]
    bb = N // k
    return field2d[:bb * k, :bb * k].reshape(k, bb, k, bb).mean(axis=(1, 3)).ravel()
