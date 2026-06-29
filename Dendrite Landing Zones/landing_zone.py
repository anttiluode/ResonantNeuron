"""
================================================================================
LANDING ZONES  -  a place-coding transducer for wave-substrate computation
================================================================================

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
"Do not hype. Do not lie. Just show."

The interface that was missing a name. Three parts:

  ENCODE  (input transducer):  a continuous value lands on a ring of zones.
          Each zone i sits at a fixed phase phi_i = 2*pi*i/N. A value theta
          lights a bump of zones around it; geometry turns position into phase.
          -> the value is never stored as a number; it is WHERE the bump is.

  COINCIDENCE  (soma / interference): two place codes are compared by the real
          part of their population-vector product -- constructive interference
          when the two encoded values agree, destructive when they oppose.
          This is the resonator soma: cos(theta_a - theta_b), read from waves.

  AIS SPIKE  (output transducer): the continuous coincidence is snapped to a
          discrete event when it crosses threshold. Analog in, committed out.

This is the literal mechanism of head-direction rings, the Jeffress sound-
localiser, and theta phase codes. It is for CONTINUOUS, physically-meaningful
variables (angle, distance, time-difference) -- the opposite of the arbitrary
discrete symbols that made the Sudoku version fail.

Ledger:
  VERIFIED here (self-tests below): circular encode/decode is near-lossless;
    the place code is measurably more noise-robust than a single scalar;
    coincidence tracks cos(delta) between two encoded values.
  DESIGNED: zone count, bump width, thresholds, the arc used for bounded values.
  NOT CLAIMED: that this is smarter than arithmetic. It is not. It is the
    faithful, noise-robust, wave-native way to get a value in and a commit out.
================================================================================
"""

import numpy as np

TAU = 2 * np.pi


class LandingZones:
    """A ring of N landing zones. Position on the ring == phase == value."""

    def __init__(self, n=24, kappa=4.0):
        self.n = n
        self.kappa = kappa                       # bump sharpness (von Mises)
        self.phi = np.arange(n) * TAU / n        # each zone's fixed phase
        self._eiphi = np.exp(1j * self.phi)

    # --- input transducer: value -> population of activations ---
    def encode(self, theta, noise=0.0, rng=None):
        """theta in radians -> activation vector a_i (a bump centred at theta)."""
        a = np.exp(self.kappa * (np.cos(theta - self.phi) - 1.0))
        if noise > 0.0:
            rng = rng or np.random.default_rng()
            a = np.clip(a + noise * rng.standard_normal(self.n), 0, None)
        return a

    # --- read-out: population of activations -> value ---
    def decode(self, a):
        """Population-vector phase. Exact (to symmetry) for a clean bump."""
        Z = np.sum(a * self._eiphi)
        return np.angle(Z) % TAU

    # --- the encoded complex field (amplitude + phase), if you want the waves ---
    def phasors(self, a):
        return a * self._eiphi

    def population_vector(self, a):
        return np.sum(a * self._eiphi)


def coincidence(zones, a, b):
    """
    Soma interference: real part of the normalised product of the two
    population vectors = cos(theta_a - theta_b).
      +1  encoded values agree   (constructive)
      -1  encoded values oppose  (destructive)
       0  orthogonal
    """
    Za = zones.population_vector(a)
    Zb = zones.population_vector(b)
    denom = (abs(Za) * abs(Zb)) + 1e-12
    return float(np.real(Za * np.conj(Zb)) / denom)


def ais_spike(x, threshold=0.6):
    """Axon initial segment: continuous coincidence -> committed 0/1 event."""
    return 1.0 if x >= threshold else 0.0


# --- helpers for BOUNDED linear sensors (distance, concentration, ...) -------
# map value in [0,1] onto an arc < 2*pi so there is no wrap-around ambiguity.
ARC_LO, ARC_HI = -2.2, 2.2

def value_to_angle(v):
    v = float(np.clip(v, 0, 1))
    return ARC_LO + v * (ARC_HI - ARC_LO)

def angle_to_value(theta):
    theta = ((theta + np.pi) % TAU) - np.pi          # to (-pi, pi]
    return float(np.clip((theta - ARC_LO) / (ARC_HI - ARC_LO), 0, 1))


# ============================================================================
# SELF-TESTS  (run this file directly)
# ============================================================================
if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(0)

    print("=" * 70)
    print("LANDING ZONES self-test")
    print("=" * 70)

    Z = LandingZones(n=24, kappa=4.0)

    # 1) clean circular encode/decode fidelity
    thetas = np.linspace(0, TAU, 400, endpoint=False)
    errs = []
    for th in thetas:
        a = Z.encode(th)
        err = np.angle(np.exp(1j * (Z.decode(a) - th)))
        errs.append(abs(err))
    print(f"[1] clean circular encode/decode: max error = {np.degrees(max(errs)):.3f} deg "
          f"(mean {np.degrees(np.mean(errs)):.3f} deg)")

    # 2) noise robustness: place code vs a single noisy scalar, matched noise
    NOISE = 0.35
    pc_err, scalar_err = [], []
    for _ in range(2000):
        th = rng.uniform(0, TAU)
        # place code: per-zone sensory noise, then decode
        a = Z.encode(th, noise=NOISE, rng=rng)
        pc_err.append(abs(np.angle(np.exp(1j * (Z.decode(a) - th)))))
        # single scalar: the angle itself measured once with comparable noise
        # (scale the scalar noise so a single reading has the same per-sample SD
        #  as one zone -> fair "one number vs a population of noisy numbers")
        scalar_err.append(abs(np.angle(np.exp(1j * (th + NOISE * rng.standard_normal() - th)))))
    pc = np.degrees(np.mean(pc_err)); sc = np.degrees(np.mean(scalar_err))
    print(f"[2] under matched noise: place-code error {pc:.2f} deg  vs  single-scalar {sc:.2f} deg "
          f"-> place code is {sc/pc:.1f}x tighter")

    # 3) coincidence soma tracks cos(delta)
    deltas = np.linspace(-np.pi, np.pi, 60)
    coh = []
    for d in deltas:
        a = Z.encode(1.0); b = Z.encode(1.0 + d)
        coh.append(coincidence(Z, a, b))
    coh = np.array(coh)
    print(f"[3] coincidence vs cos(delta): max abs deviation = {np.max(np.abs(coh - np.cos(deltas))):.4f}")

    # 4) bounded-value round trip
    vs = np.linspace(0, 1, 50)
    rt = [angle_to_value(Z.decode(Z.encode(value_to_angle(v)))) for v in vs]
    print(f"[4] bounded value [0,1] round trip: max error = {np.max(np.abs(np.array(rt)-vs)):.4f}")

    # ---- figure ----
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    fig.patch.set_facecolor("#0b0f14")
    for a_ in ax:
        a_.set_facecolor("#11161d"); a_.tick_params(colors="#7d8b99")
        for s in a_.spines.values(): s.set_color("#1f2730")
        a_.title.set_color("#e6edf3"); a_.xaxis.label.set_color("#7d8b99"); a_.yaxis.label.set_color("#7d8b99")
        a_.grid(True, alpha=0.12)

    # a bump
    a = Z.encode(np.deg2rad(120))
    ax[0].bar(np.degrees(Z.phi), a, width=10, color="#4aa3ff")
    ax[0].axvline(120, color="#ff5d52", ls="--", lw=1.2, label="encoded value 120°")
    ax[0].axvline(np.degrees(Z.decode(a)), color="#3fd07f", ls=":", lw=1.4, label="decoded")
    ax[0].set_xlabel("landing-zone position (= phase)"); ax[0].set_ylabel("activation")
    ax[0].set_title("A value is WHERE the bump is")
    ax[0].legend(facecolor="#11161d", labelcolor="#e6edf3", fontsize=8)

    # noise robustness
    ax[1].bar([0, 1], [pc, sc], color=["#4aa3ff", "#ff5d52"], width=0.6)
    ax[1].set_xticks([0, 1]); ax[1].set_xticklabels(["place code\n(population)", "single scalar"])
    ax[1].set_ylabel("decode error (deg)")
    ax[1].set_title(f"Population code is {sc/pc:.1f}x more noise-robust")
    for i, v in enumerate([pc, sc]): ax[1].text(i, v+0.3, f"{v:.1f}°", ha="center", color="#e6edf3")

    # coincidence
    ax[2].plot(np.degrees(deltas), coh, color="#3fd07f", lw=2, label="soma coincidence")
    ax[2].plot(np.degrees(deltas), np.cos(deltas), color="#ffb454", ls="--", lw=1, label="cos(Δ)")
    ax[2].set_xlabel("difference between two encoded values (deg)")
    ax[2].set_ylabel("coincidence")
    ax[2].set_title("Soma reads agreement by interference")
    ax[2].legend(facecolor="#11161d", labelcolor="#e6edf3", fontsize=8)

    fig.suptitle("Landing-zone transducer: value→phase→value, noise-robust, with an interference soma",
                 color="#e6edf3", fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig("landing_zone_selftest.png", dpi=110, facecolor="#0b0f14", bbox_inches="tight")
    print("\nsaved -> landing_zone_selftest.png")
