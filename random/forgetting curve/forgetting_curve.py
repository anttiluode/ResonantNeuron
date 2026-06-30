"""
Absorbing boundaries + a Berglund magnetron cavity, to measure the REAL
forgetting curve of the wave reservoir.

Last time the order-memory accuracy stayed flat at 100% out to long delays.
That was NOT durable memory - it was an artifact: reflecting walls trapped the
energy so the standing wave never decayed. To get the true memory horizon we
need energy to LEAVE the domain (absorbing boundary), exactly the open boundary
condition in Langtangen & Linge.

Plan, in order, each step gated on the previous:
  1. Build the damped-wave leapfrog scheme from the book (eq. 63).
  2. VERIFY an absorbing sponge layer actually absorbs: a single pulse's energy
     must decay to ~0, while a reflecting box conserves it. (Verify the tool
     before trusting any result.)
  3. Measure the forgetting curve in an OPEN box with absorbing edges:
     fire 3 magnitude-ordered pulses at one point, snapshot the field at growing
     delays, ask a linear readout to recover the order. Accuracy should now FALL
     toward chance - the decay time is the real memory horizon.
  4. Berglund magnetron cavity (reflecting walls + one absorbing outlet): does a
     resonator HOLD the order-memory longer than open space? This is the honest
     test of whether structured cavities extend the horizon - the thing that
     would connect a millisecond ring to a seconds-long thought. Could go either
     way: resonance preserves, or chaotic mixing scrambles. The data decides.
"""

import numpy as np
import math
from itertools import permutations
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt

rng = np.random.default_rng(3)

# ---------------- solver ----------------

def laplacian(u):
    up = np.pad(u, 1, mode='constant')   # zero pad -> Dirichlet walls at array edge
    return (up[:-2,1:-1] + up[2:,1:-1] + up[1:-1,:-2] + up[1:-1,2:] - 4*u)

class WaveField:
    """
    Damped 2D wave equation (book eq. 63):
      u^{n+1} = [2u^n - (1 - b dt/2) u^{n-1} + (c dt)^2 lap(u^n)] / (1 + b dt/2)
    b(x,y) is a spatially varying damping (the absorbing sponge).
    `inside` is a boolean mask; outside it u is forced to 0 (reflecting cavity wall).
    """
    def __init__(self, N, c=0.5, dt=0.6, b=None, inside=None):
        self.N = N; self.c = c; self.dt = dt
        self.b = np.zeros((N,N)) if b is None else b
        self.inside = np.ones((N,N), bool) if inside is None else inside
        self.reset()

    def reset(self):
        self.u = np.zeros((self.N, self.N))
        self.u_prev = np.zeros((self.N, self.N))

    def step(self):
        bdt = self.b * self.dt / 2.0
        lap = laplacian(self.u)
        u_next = (2*self.u - (1 - bdt)*self.u_prev + (self.c*self.dt)**2 * lap) / (1 + bdt)
        u_next[~self.inside] = 0.0
        self.u_prev = self.u
        self.u = u_next

    def inject(self, pos, amp=1.0, sigma=2.0):
        r0, c0 = pos
        rr, cc = np.meshgrid(np.arange(self.N), np.arange(self.N), indexing='ij')
        bump = amp * np.exp(-((rr-r0)**2 + (cc-c0)**2)/(2*sigma**2))
        self.u = self.u + bump * self.inside

    def energy(self):
        return float(np.sum(self.u**2))


# ---------------- geometries ----------------

def sponge(N, width, bmax):
    """Damping that ramps from 0 in the interior to bmax over `width` cells at all 4 edges."""
    b = np.zeros((N, N))
    ramp = np.linspace(0, 1, width)**2
    for k in range(width):
        val = bmax*ramp[k]
        b[k,:]      = np.maximum(b[k,:], val)
        b[N-1-k,:]  = np.maximum(b[N-1-k,:], val)
        b[:,k]      = np.maximum(b[:,k], val)
        b[:,N-1-k]  = np.maximum(b[:,N-1-k], val)
    return b

def make_open_box(N, width=8, bmax=0.6):
    inside = np.ones((N,N), bool)
    return inside, sponge(N, width, bmax)

def disk(N, center, radius):
    rr, cc = np.meshgrid(np.arange(N), np.arange(N), indexing='ij')
    return (rr-center[0])**2 + (cc-center[1])**2 <= radius**2

def capsule(N, p0, p1, halfwidth):
    """Thick line segment (channel) between p0 and p1."""
    rr, cc = np.meshgrid(np.arange(N), np.arange(N), indexing='ij')
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    d = p1 - p0; L2 = d@d + 1e-9
    pts = np.stack([rr.ravel(), cc.ravel()], 1).astype(float)
    t = np.clip(((pts - p0) @ d)/L2, 0, 1)
    proj = p0 + t[:,None]*d
    dist = np.linalg.norm(pts - proj, axis=1).reshape(N,N)
    return dist <= halfwidth

def make_magnetron(N=64, rc=9, rs=6, orbit=21, n_sat=8, chan=2, outlet=2, sp_w=8, sp_max=0.8):
    """Central cavity + n_sat satellites + connecting channels + one outlet to the right edge.
       Reflecting walls everywhere; absorbing sponge only in the outlet near the right edge."""
    c0 = (N//2, N//2)
    inside = disk(N, c0, rc)
    sat_centers = []
    for k in range(n_sat):
        ang = 2*np.pi*k/n_sat
        sc = (int(round(c0[0] + orbit*np.sin(ang))), int(round(c0[1] + orbit*np.cos(ang))))
        sat_centers.append(sc)
        inside |= disk(N, sc, rs)
        inside |= capsule(N, c0, sc, chan)
    # outlet from the rightmost satellite (angle 0) straight to the right edge
    right_sat = (c0[0], c0[1] + orbit)
    inside |= capsule(N, right_sat, (c0[0], N-1), outlet)
    # sponge only near the right edge (the outlet), so the cavity walls stay reflecting
    b = np.zeros((N,N))
    ramp = np.linspace(0,1,sp_w)**2
    for k in range(sp_w):
        b[:, N-1-k] = np.maximum(b[:, N-1-k], sp_max*ramp[k])
    b *= inside
    return inside, b, c0


# ---------------- experiments ----------------

def run_and_snapshot(field, inject_pos, magnitudes, order, gap, delays, sigma=2.0):
    """Fire pulses (magnitudes in given order) at inject_pos, then snapshot the field
       at each cumulative delay after the last pulse. Returns dict delay->flattened field."""
    field.reset()
    for mag_idx in order:
        field.inject(inject_pos, amp=magnitudes[mag_idx], sigma=sigma)
        for _ in range(gap):
            field.step()
    snaps = {}
    maxd = max(delays); checkpoints = set(delays)
    for s in range(1, maxd+1):
        field.step()
        if s in checkpoints:
            snaps[s] = field.u.copy()
    return snaps

def coarse(field2d, k):
    N = field2d.shape[0]; b = N//k
    return field2d[:b*k,:b*k].reshape(k,b,k,b).mean(axis=(1,3)).ravel()

def forgetting_curve(make_field, inject_pos, delays, n_per_class=30, gap=16,
                     n_mag=3, coarse_k=12, noise=0.01, sigma=2.0):
    orders = list(permutations(range(n_mag)))
    mags0 = [1.0, 2.0, 3.0][:n_mag]
    # collect snapshots: X[delay] -> list of feature vectors, y -> labels
    X = {d: [] for d in delays}; y = []
    for label, order in enumerate(orders):
        for _ in range(n_per_class):
            field = make_field()
            j = 1.0 + 0.03*rng.standard_normal()
            mags = [m*j for m in mags0]
            snaps = run_and_snapshot(field, inject_pos, mags, order, gap, delays, sigma)
            for d in delays:
                f = coarse(snaps[d], coarse_k) + noise*rng.standard_normal(coarse_k*coarse_k)
                X[d].append(f)
            y.append(label)
    y = np.array(y)
    accs = {}
    for d in delays:
        Xd = np.array(X[d])
        clf = LogisticRegression(max_iter=3000, C=1.0)
        accs[d] = cross_val_score(clf, Xd, y, cv=5).mean()
    # shuffle control at the smallest delay (defines chance empirically)
    Xs = np.array(X[delays[0]]); ysh = rng.permutation(y)
    shuf = cross_val_score(LogisticRegression(max_iter=3000), Xs, ysh, cv=5).mean()
    return accs, shuf, len(orders)


if __name__ == "__main__":
    N = 64
    chance = 1/math.factorial(3)
    print("="*70)
    print("ABSORBING BOUNDARIES + CAVITY: the real forgetting curve")
    print("="*70)

    # ---- Step 2: verify the sponge actually absorbs ----
    print("\n[verify] does the absorbing sponge actually remove energy?")
    insA, bA = make_open_box(N, width=8, bmax=0.6)
    refl = WaveField(N, inside=insA, b=np.zeros((N,N)))   # reflecting (no damping)
    absb = WaveField(N, inside=insA, b=bA)                # absorbing sponge
    for fld in (refl, absb):
        fld.reset(); fld.inject((N//2, N//2), amp=1.0, sigma=2.0)
    E_refl, E_abs = [], []
    for _ in range(500):
        refl.step(); absb.step()
        E_refl.append(refl.energy()); E_abs.append(absb.energy())
    E_refl = np.array(E_refl); E_abs = np.array(E_abs)
    r0 = E_refl[20]; a0 = E_abs[20]
    print(f"  reflecting box: energy at step 500 / peak = {E_refl[-1]/r0:.3f}  (should stay ~order 1)")
    print(f"  absorbing box:  energy at step 500 / peak = {E_abs[-1]/a0:.4f}  (should be ~0)")
    sponge_ok = E_abs[-1]/a0 < 0.02 and E_refl[-1]/r0 > 0.2
    print(f"  -> sponge verified: {sponge_ok}")

    # ---- Step 3: open-box forgetting curve ----
    # Use a STRONG wide sponge so even slow/near-DC components leak; otherwise the
    # curve plateaus inside the true horizon (diagnosed: weak sponge leaves a residue).
    insA, bA = make_open_box(N, width=16, bmax=1.5)
    print("\n[open box] forgetting curve (strong absorbing edges)")
    delays = [8, 100, 300, 700, 1100, 1500, 2000]
    accs_box, shuf_box, ncl = forgetting_curve(
        lambda: WaveField(N, inside=insA, b=bA),
        inject_pos=(N//2, N//2), delays=delays, n_per_class=30)
    for d in delays:
        print(f"  delay {d:4d} -> acc {accs_box[d]:.3f}")
    print(f"  shuffle control: {shuf_box:.3f}  (chance {chance:.3f})")

    # ---- Step 4: magnetron cavity forgetting curve ----
    print("\n[magnetron cavity] forgetting curve (reflecting walls + 1 outlet)")
    insM, bM, cM = make_magnetron(N, sp_w=12, sp_max=1.5)
    print(f"  cavity covers {insM.mean()*100:.1f}% of the grid")
    accs_cav, shuf_cav, _ = forgetting_curve(
        lambda: WaveField(N, inside=insM, b=bM),
        inject_pos=cM, delays=delays, n_per_class=30)
    for d in delays:
        print(f"  delay {d:4d} -> acc {accs_cav[d]:.3f}")
    print(f"  shuffle control: {shuf_cav:.3f}")

    # ---- helper: characteristic horizon = last delay above (chance + 0.15) ----
    def horizon(accs):
        good = [d for d in delays if accs[d] > chance + 0.15]
        return max(good) if good else 0
    h_box = horizon(accs_box); h_cav = horizon(accs_cav)

    # ---------------- figure ----------------
    fig = plt.figure(figsize=(15, 9))

    ax1 = plt.subplot(2,3,1)
    ax1.plot(E_refl/r0, label='reflecting (traps)', color='crimson')
    ax1.plot(E_abs/a0, label='absorbing sponge', color='steelblue')
    ax1.set_title('Step 2: sponge verification\n(energy after a single pulse)')
    ax1.set_xlabel('step'); ax1.set_ylabel('energy / peak'); ax1.legend(); ax1.grid(alpha=0.3)

    ax2 = plt.subplot(2,3,2)
    ax2.semilogx(delays, [accs_box[d] for d in delays], 'o-', color='steelblue', lw=2, label='open box')
    ax2.semilogx(delays, [accs_cav[d] for d in delays], 's-', color='darkorange', lw=2, label='magnetron cavity')
    ax2.axhline(chance, color='k', ls='--', alpha=0.6, label='chance')
    ax2.set_title('Steps 3-4: the REAL forgetting curve')
    ax2.set_xlabel('delay after last pulse (steps)'); ax2.set_ylabel('order-recall accuracy')
    ax2.set_ylim(0,1.05); ax2.legend(); ax2.grid(alpha=0.3)

    ax3 = plt.subplot(2,3,3)
    ax3.bar(['open box','cavity'], [h_box, h_cav], color=['steelblue','darkorange'])
    ax3.set_title('Memory horizon\n(last delay with acc > chance+0.15)')
    ax3.set_ylabel('steps')
    for i,v in enumerate([h_box,h_cav]): ax3.text(i, v, f"{v}", ha='center', va='bottom')

    # cavity mask + an example field
    ax4 = plt.subplot(2,3,4)
    ax4.imshow(insM, cmap='Greys', origin='upper')
    ax4.set_title('Magnetron cavity mask\n(reflecting walls, right outlet)'); ax4.axis('off')

    ax5 = plt.subplot(2,3,5)
    fld = WaveField(N, inside=insM, b=bM)
    snaps = run_and_snapshot(fld, cM, [1,2,3], (0,1,2), 16, [120])
    field_img = snaps[120].reshape(N,N)
    m = np.abs(field_img).max()+1e-9
    ax5.imshow(field_img, cmap='RdBu', vmin=-m, vmax=m, origin='upper')
    ax5.set_title('Cavity field, 120 steps after input\n(order ringing in the satellites)'); ax5.axis('off')

    ax6 = plt.subplot(2,3,6)
    insA2, bA2 = make_open_box(N, 16, 1.5)
    fldb = WaveField(N, inside=insA2, b=bA2)
    snapsb = run_and_snapshot(fldb, (N//2,N//2), [1,2,3], (0,1,2), 16, [120])
    fib = snapsb[120].reshape(N,N); mb = np.abs(fib).max()+1e-9
    ax6.imshow(fib, cmap='RdBu', vmin=-mb, vmax=mb, origin='upper')
    ax6.set_title('Open box, 120 steps after input\n(rings leaving through edges)'); ax6.axis('off')

    plt.tight_layout()
    plt.savefig('/home/claude/forgetting_curve_results.png', dpi=140, bbox_inches='tight')
    print("\nFigure saved: forgetting_curve_results.png")

    # ---------------- verdict ----------------
    print("\n" + "="*70); print("VERDICT"); print("="*70)
    print(f"chance = {chance:.3f}")
    print(f"open-box horizon  : {h_box} steps")
    print(f"cavity horizon    : {h_cav} steps")
    if not sponge_ok:
        print("WARNING: sponge verification failed; forgetting curves are untrustworthy.")
    elif accs_box[delays[-1]] < chance + 0.10:
        print("""
GOOD: with energy actually leaving the domain, open-box order-memory now DECAYS
toward chance - a real, finite forgetting curve, not the trapped-energy artifact
from before. The horizon is a measurable number.""")
        if h_cav > h_box * 1.5:
            print(f"""AND the magnetron cavity holds order-memory markedly LONGER
({h_cav} vs {h_box} steps): reflecting resonator walls trap and re-circulate the
ring structure, extending the horizon. This is a concrete mechanism for turning a
fast single-pass ring into a longer-lived store - the missing middle timescale.""")
        elif h_cav < h_box * 0.7:
            print(f"""But the cavity FORGETS FASTER ({h_cav} vs {h_box}): bouncing in the
satellites scrambles the order into a tangle the linear readout can't undo.
Resonance != linearly-readable memory. Honest negative for the cavity.""")
        else:
            print(f"""The cavity horizon ({h_cav}) is comparable to the open box ({h_box}):
the structured geometry did not clearly extend (or destroy) the linear order-memory
at this resolution.""")
    else:
        print(f"""open-box accuracy is still {accs_box[delays[-1]]:.2f} at the longest delay -
either the absorbing layer is too weak or a residual energy cue persists; the
horizon may exceed the tested range.""")
    print("="*70)
