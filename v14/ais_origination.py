"""
ais_origination.py -- the v14 mechanism, built from what Leterrier (2018,
J. Neurosci. 38(9):2135-2145) actually says, not from the analogy the model
summaries reached for.

What the four v13 attempts got wrong, and what this fixes:

  v13 modelled "directionality" as a FILTER applied to a wave passing
  through a channel -- a skewed angle, a periodic lattice, a threshold
  relay, a refractory chain. All four failed (reciprocity ratio ~ 1.0),
  and the reason was traced precisely: each read INSTANTANEOUS SCALAR
  AMPLITUDE at a point, which carries no information about which direction
  a wave was travelling when it arrived.

  Leterrier locates the real directionality in two things v13 never had:

  (1) ORIGINATION, not filtering. "Nav channels are primarily responsible
      for the INITIATION of action potentials at the AIS" via an ~30-fold
      concentration of Nav channels there vs dendrites/distal axon. The
      spike is BORN at a localized high-excitability site and propagates
      OUTWARD from it. The AIS is not a gate a wave passes through; it is
      the place the regenerative event starts.

  (2) INACTIVATION -- state that persists between timesteps. A real Nav
      channel, once it opens and fires, ENTERS AN INACTIVATED STATE and
      cannot reopen until it has recovered, regardless of present voltage.
      This is genuine history-dependence at the site, not a function of the
      instantaneous field. v13's "refractory" relay gestured at this but
      still triggered on instantaneous amplitude from either direction.

This file builds the minimal honest version of (1)+(2): a localized
excitable site with a toy Nav gate that has an inactivation variable, that
ORIGINATES a pulse propagating outward, and tests whether THAT site, placed
at one end of a channel, makes the system transmit asymmetrically -- i.e.
whether a signal injected on the AIS side propagates to the far side, while
a signal injected on the far side does NOT trigger the AIS to fire back.

The honest test is NOT "does a wave pass through differently in two
directions" (a passive question that v13 already answered: no). It is "does
a spike-origination site convert an arriving subthreshold wave into an
outgoing spike only when driven hard enough, and is the resulting
input->output relationship asymmetric in a way a passive channel's is not."

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import numpy as np
from cavity_field import CavityField, build_geometry


class NavGate:
    """A toy voltage-gated sodium channel with INACTIVATION -- the minimal
    model of the history-dependent state that v13's relays lacked.

    State machine (deliberately simple, not Hodgkin-Huxley):
      - RESTING: if local drive |u| crosses v_thresh, fire -> ACTIVE,
        emit a fixed-amplitude regenerative pulse for `active_steps`.
      - ACTIVE: emitting the spike. After active_steps -> INACTIVATED.
      - INACTIVATED: cannot fire regardless of drive, for `inact_steps`.
        After inact_steps -> RESTING (recovery).

    The key property, absent in v13: once fired, the gate is BLIND to
    further input for the whole active+inactivated window. That window is
    set by the gate's own internal clock, not by the instantaneous field.
    This is what lets a spike propagate forward (into rested gates ahead)
    without re-triggering backward (into gates that just fired and are now
    inactivated)."""

    RESTING, ACTIVE, INACTIVATED = 0, 1, 2

    def __init__(self, v_thresh=0.5, spike_amp=4.0, active_steps=6,
                 inact_steps=25):
        self.v_thresh = v_thresh
        self.spike_amp = spike_amp
        self.active_steps = active_steps
        self.inact_steps = inact_steps
        self.state = self.RESTING
        self.timer = 0
        self.sign = 1.0

    def update(self, local_drive):
        """Advance one step given the local field value. Returns the pulse
        amplitude this gate emits this step (0 if not actively spiking)."""
        if self.state == self.RESTING:
            if abs(local_drive) >= self.v_thresh:
                self.state = self.ACTIVE
                self.timer = self.active_steps
                self.sign = np.sign(local_drive) if local_drive != 0 else 1.0
                return self.sign * self.spike_amp
            return 0.0
        elif self.state == self.ACTIVE:
            self.timer -= 1
            if self.timer <= 0:
                self.state = self.INACTIVATED
                self.timer = self.inact_steps
                return 0.0
            return self.sign * self.spike_amp
        else:  # INACTIVATED
            self.timer -= 1
            if self.timer <= 0:
                self.state = self.RESTING
            return 0.0


class OriginatingField(CavityField):
    """A wave field with a localized SPIKE-ORIGINATION SITE (the AIS): a
    short line of excitable points, each with its own NavGate, that
    originate a pulse propagating OUTWARD (toward the axon/far side) when
    triggered. Models Leterrier's "spike is initiated at the AIS and
    propagates outward," with real inactivation."""

    def __init__(self, mask, ais_sites, propagate_dir_point, **kwargs):
        """ais_sites: ordered list of (y,x) grid points forming the AIS,
            ordered from the soma/dendrite side toward the axon side.
        propagate_dir_point: a (y,x) point on the AXON side; when an AIS
            site fires, it writes its pulse toward this side (outward),
            establishing the polarity Leterrier describes (microtubule
            plus-ends / Nav origination both point outward)."""
        super().__init__(mask, **kwargs)
        self.ais_sites = ais_sites
        self.gates = [NavGate() for _ in ais_sites]
        self.propagate_dir_point = propagate_dir_point
        self.fire_log = []

    def step(self, forcing=None):
        u_next = super().step(forcing)
        fired_this_step = 0
        for i, (site, gate) in enumerate(zip(self.ais_sites, self.gates)):
            local = self.u[site]
            pulse = gate.update(local)
            if pulse != 0.0:
                # originate/propagate the spike OUTWARD: write the pulse to
                # this site AND nudge the next site toward the axon side, so
                # the spike marches outward, not back toward the trigger.
                self.u[site] = pulse
                if i + 1 < len(self.ais_sites):
                    # bias the next outward site -- but it must still cross
                    # its OWN threshold and not be inactivated, so this is
                    # propagation, not forced teleportation
                    nxt = self.ais_sites[i + 1]
                    self.u[nxt] += pulse * 0.6
                fired_this_step += 1
        self.fire_log.append(fired_this_step)
        return self.u


def build_ais_geometry(grid_size=140, soma_radius=14, channel_len=30,
                        ais_len=6, ais_n_sites=5):
    """A soma cavity, a channel, and a far (axon) cavity. The AIS sits at
    the START of the channel (soma side), as in biology. Returns mask plus
    the key coordinates."""
    ny = nx = grid_size
    mask = np.zeros((ny, nx))
    cy, cx = ny // 2, nx // 2
    yy, xx = np.mgrid[0:ny, 0:nx]

    # soma cavity (dendritic/somatic side -- where inputs arrive)
    mask[(yy - cy) ** 2 + (xx - cx) ** 2 <= soma_radius ** 2] = 1.0
    # axon-side cavity (where the spike should end up)
    axon_cx = cx + soma_radius + channel_len
    mask[(yy - cy) ** 2 + (xx - axon_cx) ** 2 <= 7 ** 2] = 1.0
    # channel between them
    entry_x = cx + soma_radius
    n_pts = int(channel_len * 2) + 4
    for t in np.linspace(0, 1, n_pts):
        px = entry_x + t * (axon_cx - entry_x)
        mask[(yy - cy) ** 2 + (xx - px) ** 2 <= 3.0 ** 2] = 1.0

    # AIS sites: a short line at the soma end of the channel, ordered
    # soma-side -> axon-side
    ais_start = cx + soma_radius
    ais_sites = []
    for k in range(ais_n_sites):
        px = ais_start + k * (ais_len / max(ais_n_sites - 1, 1))
        ais_sites.append((cy, int(px)))

    return (mask, (cy, cx), (cy, int(axon_cx)), ais_sites,
            (cy, int(axon_cx)))


if __name__ == "__main__":
    print("=" * 78)
    print("V14: SPIKE-ORIGINATION + Nav INACTIVATION (per Leterrier 2018)")
    print("Does an origination site break the reciprocity v13 could not?")
    print("=" * 78)

    Omega = 2 * np.pi * 0.10
    mask, soma_yx, axon_yx, ais_sites, prop_point = build_ais_geometry()
    print(f"\nsoma (input side): {soma_yx}")
    print(f"axon (output side): {axon_yx}")
    print(f"AIS sites (soma->axon order): {ais_sites}")

    def run_direction(drive_yx, measure_yx, drive_amp, n_settle=400,
                       n_measure=300):
        field = OriginatingField(mask, ais_sites, prop_point,
                                  dx=1.0, c=1.0, damping=0.01)
        def drive(t):
            f = np.zeros_like(mask)
            f[drive_yx] += drive_amp * np.sin(Omega * t)
            return f
        field.run(n_settle, drive)
        vals = []
        total_fires = 0
        for _ in range(n_measure):
            field.run(1, drive)
            vals.append(field.u[measure_yx])
            total_fires += field.fire_log[-1]
        return np.sqrt(np.mean(np.array(vals) ** 2)), total_fires

    print("\n--- Drive the SOMA side (inputs arriving at the AIS) ---")
    fwd_amp, fwd_fires = run_direction(soma_yx, axon_yx, drive_amp=8.0)
    print(f"  axon-side amplitude: {fwd_amp:.4f}   AIS fired {fwd_fires} times")

    print("\n--- Drive the AXON side (signal arriving from downstream) ---")
    bwd_amp, bwd_fires = run_direction(axon_yx, soma_yx, drive_amp=8.0)
    print(f"  soma-side amplitude: {bwd_amp:.4f}   AIS fired {bwd_fires} times")

    print(f"\nForward (soma->axon) transmission: {fwd_amp:.4f}")
    print(f"Backward (axon->soma) transmission: {bwd_amp:.4f}")
    ratio = fwd_amp / (bwd_amp + 1e-12)
    print(f"Directionality ratio: {ratio:.3f}")
    print(f"\nAIS fire counts -- forward: {fwd_fires}, backward: {bwd_fires}")
    print("(If origination is real, the AIS should fire when driven from the")
    print(" soma side and propagate to the axon; the question is whether the")
    print(" reverse drive produces a meaningfully different outcome.)")
