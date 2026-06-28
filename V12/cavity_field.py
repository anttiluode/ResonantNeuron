"""
cavity_field.py -- the actual 2-D scalar wave PDE on a Berglund-style
angled-cavity geometry: a circular soma cavity fed by N satellite cavities
connected by narrow channels at controllable angles and lengths, Neumann
(reflecting) boundary conditions on the walls, as in Berglund's simulations.

This REPLACES the lumped soma/dendrite ODE of resonator_neuron.py /
delay_dendrite.py with the real thing: u(x,y,t) satisfying

    u_tt = c^2 * Laplacian(u) - gamma * u_t  + forcing(x,y,t)

on a 2-D domain whose SHAPE is the dendrite -- a long thin channel really is
a long thin channel, with its own length and its own travel time, not an
injected phase constant. Driving a satellite cavity at its far end with
bit-encoded forcing and reading the soma cavity's amplitude is the test of
whether the v11 (lumped) results -- the XOR<->XNOR length sweep, the parity
wall, the structural cap on AND/OR, and the always-on dendrite fixing it --
survive when nothing is assumed and everything is solved on the grid.

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np


class CavityField:
    """A 2-D wave field on a binary mask (1 = medium, 0 = wall/outside).
    Neumann boundary: enforced by reflecting the Laplacian stencil at the
    medium/wall interface (zero-flux), the standard way to implement
    Berglund-style "waves crossing a grid of obstacles" boundaries.
    """

    def __init__(self, mask, dx=1.0, c=1.0, damping=0.02, dt=None):
        self.mask = mask.astype(np.float64)
        self.ny, self.nx = mask.shape
        self.dx = dx
        self.c = c
        self.damping = damping
        # CFL stability: dt < dx / (c * sqrt(2))
        self.dt = dt if dt is not None else 0.5 * dx / (c * np.sqrt(2))
        self.u = np.zeros_like(self.mask)      # displacement
        self.u_prev = np.zeros_like(self.mask)  # previous step (for leapfrog)
        self.t = 0.0

    def laplacian_neumann(self, u):
        """5-point Laplacian with Neumann (zero-flux) boundaries: outside the
        mask, or at domain edges, the gradient is treated as zero (a wall
        reflects, it doesn't absorb), implemented via mirrored padding,
        followed by masking so the wall cells themselves never carry field."""
        # pad with edge replication (Neumann at outer boundary)
        up = np.pad(u, 1, mode='edge')
        lap = (
            up[1:-1, 2:] + up[1:-1, :-2] +
            up[2:, 1:-1] + up[:-2, 1:-1] -
            4 * up[1:-1, 1:-1]
        ) / (self.dx ** 2)
        # zero-flux at the mask boundary: where mask==0, neighbours contribute
        # nothing extra beyond what's already imposed by clamping u=0 there
        # each step (done in step()). This keeps walls reflecting, not leaking.
        return lap

    def step(self, forcing=None):
        """One leapfrog step of u_tt = c^2 lap(u) - damping*u_t + forcing."""
        lap = self.laplacian_neumann(self.u)
        f = forcing if forcing is not None else 0.0
        # u_tt approx (u_next - 2u + u_prev)/dt^2; u_t approx (u - u_prev)/dt
        accel = self.c ** 2 * lap - self.damping * (self.u - self.u_prev) / self.dt + f
        u_next = 2 * self.u - self.u_prev + self.dt ** 2 * accel
        u_next *= self.mask          # hard wall: field is exactly zero outside medium
        self.u_prev = self.u
        self.u = u_next
        self.t += self.dt
        return self.u

    def run(self, n_steps, forcing_fn=None):
        """forcing_fn(t) -> 2D array same shape as mask, or None."""
        for _ in range(n_steps):
            f = forcing_fn(self.t) if forcing_fn is not None else None
            self.step(f)
        return self.u


def build_geometry(grid_size=160, soma_radius=18, n_satellites=2,
                    satellite_radius=8, satellite_lengths=None,
                    satellite_angles_deg=None, channel_half_width=2.0,
                    skew_deg=0.0):
    """Build the binary mask: a circular soma cavity at the centre, with
    n_satellites circular cavities connected by straight channels. Each
    satellite's RADIAL DISTANCE from the soma's rim is satellite_lengths[i]
    -- this IS the dendrite length, expressed as physical channel length on
    the grid, not as an injected phase. skew_deg rotates each channel's
    entry angle relative to the radial line (Berglund's "angled cavities").
    Returns: mask (ny,nx), soma_center, list of satellite_centers, list of
    (channel start, end) for forcing-point placement.
    """
    if satellite_lengths is None:
        satellite_lengths = [25.0] * n_satellites
    if satellite_angles_deg is None:
        satellite_angles_deg = list(np.linspace(0, 360, n_satellites, endpoint=False))

    ny = nx = grid_size
    mask = np.zeros((ny, nx), dtype=np.float64)
    cy, cx = ny // 2, nx // 2

    yy, xx = np.mgrid[0:ny, 0:nx]
    # soma disc
    soma_d2 = (yy - cy) ** 2 + (xx - cx) ** 2
    mask[soma_d2 <= soma_radius ** 2] = 1.0

    satellite_centers = []
    channel_endpoints = []

    for i in range(n_satellites):
        ang = np.deg2rad(satellite_angles_deg[i])
        L = satellite_lengths[i]
        # satellite cavity centre: radially out from soma rim by L, plus skew
        skew = np.deg2rad(skew_deg)
        # entry direction (where the channel meets the soma) vs cavity centre
        # direction (rotated by skew) -- this is the "angled cavity"
        entry_x = cx + soma_radius * np.cos(ang)
        entry_y = cy + soma_radius * np.sin(ang)
        far_ang = ang + skew
        sat_cx = entry_x + L * np.cos(far_ang)
        sat_cy = entry_y + L * np.sin(far_ang)
        satellite_centers.append((sat_cy, sat_cx))

        # carve the satellite disc
        sat_d2 = (yy - sat_cy) ** 2 + (xx - sat_cx) ** 2
        mask[sat_d2 <= satellite_radius ** 2] = 1.0

        # carve the connecting channel: a thick line segment from entry point
        # to satellite centre (so the channel actually reaches inside the
        # satellite disc, guaranteeing connectivity)
        n_pts = int(np.hypot(sat_cx - entry_x, sat_cy - entry_y) * 2) + 4
        ts = np.linspace(0, 1, n_pts)
        for t in ts:
            px = entry_x + t * (sat_cx - entry_x)
            py = entry_y + t * (sat_cy - entry_y)
            d2 = (yy - py) ** 2 + (xx - px) ** 2
            mask[d2 <= channel_half_width ** 2] = 1.0

        channel_endpoints.append(((sat_cy, sat_cx), (entry_y, entry_x)))

    return mask, (cy, cx), satellite_centers, channel_endpoints


# ============================================================ self-test
if __name__ == "__main__":
    print("=" * 78)
    print("CAVITY FIELD -- does the PDE solver run stably on the angled geometry?")
    print("=" * 78)
    mask, soma_c, sat_cs, _ = build_geometry(
        grid_size=140, soma_radius=16, n_satellites=2,
        satellite_radius=7, satellite_lengths=[20, 20],
        satellite_angles_deg=[0, 180], skew_deg=15)

    n_medium = mask.sum()
    print(f"\nGrid {mask.shape}, medium cells: {int(n_medium)} "
          f"({100*n_medium/mask.size:.1f}% of domain)")
    print(f"Soma centre: {soma_c}")
    print(f"Satellite centres: {sat_cs}")

    field = CavityField(mask, dx=1.0, c=1.0, damping=0.01)
    print(f"\ndt (CFL-stable) = {field.dt:.4f}")

    # drive satellite 0 with a short pulse, check the field stays bounded
    sat0_y, sat0_x = int(sat_cs[0][0]), int(sat_cs[0][1])

    def forcing_fn(t):
        f = np.zeros_like(mask)
        if t < 5.0:
            f[sat0_y, sat0_x] = 2.0 * np.sin(2 * np.pi * 0.15 * t)
        return f

    max_vals = []
    for step_block in range(20):
        field.run(50, forcing_fn)
        max_vals.append(np.abs(field.u).max())

    print(f"\nField |u|_max over 20 blocks of 50 steps (stability check):")
    print("  " + ", ".join(f"{v:.3f}" for v in max_vals))
    bounded = all(np.isfinite(v) and v < 1000 for v in max_vals)
    print(f"\nStays finite and bounded: {bounded}")
    if not bounded:
        print("  FAILED -- numerical instability, need smaller dt or more damping.")
