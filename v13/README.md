# GeometricNeuron13 — Does Anything Here Actually Flow One Way?

This folder tests a specific claim from a collaborating model (Grok): that
the repo's angled-cavity geometry already gives dendrites a preferred
direction of signal flow, and that a passive, AIS-inspired periodic
structure would strengthen this further.

**Start with `PAPER.md`.** It has the full argument, every number, and the
verdict: none of the four mechanisms tested — channel angle, a passive
periodic lattice, a naive threshold relay, or a refractory relay chain —
actually produce directional transmission. This README is the map of the
five scripts.

---

## The files, in the order they were actually run

**`cavity_field.py`** — same PDE solver from GeometricNeuron12, copied in
unchanged so this folder runs standalone. See that folder's README for
what it does.

**`test_skew_reciprocity.py`** — the first and most direct test: build a
single channel at various `skew_deg` angles, drive it from each end in
turn, and compare forward vs. backward transmission. Result: exactly
reciprocal (ratio 1.0000) at every angle. The channel angle parameter
changes how much energy couples in, never which way it prefers to flow.

**`ais_filter.py`** — the literal version of the proposal: a channel with a
genuine periodic constriction lattice, mimicking the spacing of a real
cytoskeletal structure. Also exactly reciprocal. This is the file that
establishes the general physics point: periodicity can filter frequency,
not direction.

**`active_relay_test.py`** — the first attempt at something that should
actually be directional: a relay that reads amplitude at one point and
writes to another whenever a threshold is crossed, explicitly asymmetric
in code. A proper four-way comparison (passive/relay × forward/backward)
shows it boosts transmission almost equally both ways — because amplitude
at a point carries no information about which direction a wave was moving
when it got there.

**`refractory_chain_test.py`** — the more serious attempt, modeling the
actual mechanism that makes a real action potential one-way: a chain of
relay points that fire forward and then go briefly refractory, unable to
re-trigger immediately. This one produced a surprising number (backward
transmission boosted *more* than forward), which is exactly the kind of
result that needs checking before it gets believed.

**`feedback_artifact_check.py`** — does that checking. Traces the raw field
value at the measurement point step by step and finds the "backward boost"
was a local feedback loop at the relay node nearest the read point, not a
real directional-transmission effect. Confirms the refractory chain, as
built, doesn't achieve directionality either, and explains exactly why.

---

## The one-sentence finding

Every passive geometric trick failed for the same underlying reason (a
linear, time-reversal-symmetric wave equation has no way to prefer a
direction), and every active-element attempt failed because it only used
*instantaneous* field amplitude, which also carries no directional
information — what's actually needed is state that persists at the relay
site between time steps, closer to a real channel-inactivation variable
than a simple threshold. That's a concrete specification for the next
build, not a guess.

---

## Reproduce it

```
python test_skew_reciprocity.py
python ais_filter.py
python active_relay_test.py
python refractory_chain_test.py
python feedback_artifact_check.py
```

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
