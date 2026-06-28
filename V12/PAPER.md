# From Lumped ODE to Real Wave: What Survives Contact With the PDE

### Re-deriving the parity wall on an actual 2-D wave field, on the real angled-cavity geometry — and finding it isn't quite what the lumped model said

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. What this build was for

The previous paper (*Geometry Gives You Parity For Free, And Then You Hit A
Wall*) built everything on a **lumped soma/dendrite ODE** — a model where
"dendrite length" was implemented as an algebraically injected phase shift,
`φ = Ω·L/v`, applied instantly to a phasor. That model is honest about being
a shortcut; it was flagged in that paper's own limits section as the thing
to redo properly: *"re-derive these same three results directly from a PDE
on the real geometry, with no lumped shortcut."*

This build does that. It solves the actual scalar wave equation,
`u_tt = c²∇²u − γu_t`, on a 2-D domain shaped like Berglund's angled-cavity
rings — a circular soma cavity connected to satellite cavities by real
channels of real physical length, with Neumann (reflecting) boundaries —
and asks the same question the lumped model answered: does matched/
mismatched dendrite length retune a unit between XOR and XNOR?

**The headline result is not a clean confirmation.** The core mechanism
survives. The precise *shape* of the transition does not, and the reason
why is itself the most useful thing this build found.

| claim from the lumped paper | what the PDE shows |
|---|---|
| matched dendrite lengths give destructive interference (XOR) or constructive (XNOR), cleanly | **confirmed** — exact zero on disagreement at matched length, in the real field |
| sweeping length retunes the unit between XOR-like and XNOR-like behavior | **confirmed**, qualitatively — both regimes appear as channel length is swept |
| the transition follows a clean `cos(φ)`-shaped curve, symmetric about a sharp quarter-wavelength wall | **not confirmed** — the real transition is lopsided, has an extended low-margin plateau, and the zero-crossing does not sit at the predicted point |
| "length = pure phase delay" is a complete description of what a channel does | **false above a certain length** — a channel becomes a two-port resonant element (it reflects), not a one-way delay line, once its own length is not negligible compared to the carrier wavelength |

---

## 1. The solver

`cavity_field.py` implements `u_tt = c²∇²u − γu_t + forcing` with a 5-point
Laplacian, Neumann boundaries via edge-replicated padding, and leapfrog time
integration at a CFL-stable timestep. The domain is built by
`build_geometry()`: a circular soma cavity, `N` satellite cavities placed at
controllable radial distance (`= dendrite length`, now a literal
**channel length on the grid**, not an injected number) and angle (the
Berglund "skew"), connected to the soma by real channels of finite width.

Stability was checked first, not assumed: a driven pulse run for 1000 steps
stays finite and bounded (`cavity_field.py --selftest`).

---

## 2. Result 1 — matched lengths: the core interference mechanism is real

At matched dendrite lengths (`L_a = L_b = 10`, carrier `Ω = 2π·0.10`),
driving both satellites with bit-encoded phase (`0 → phase 0`, `1 → phase
π`) and measuring the soma's RMS amplitude over a full carrier period
**after the transient has settled**, gives:

```
 a  b | soma RMS amplitude
 0  0 |   0.1145
 0  1 |   0.0000
 1  0 |   0.0000
 1  1 |   0.1145
```

Exact zero on disagreement, clean nonzero on agreement — real destructive
interference in a real wave field, not a coincidence of the algebra. This
was checked for signal-to-noise before being trusted: an earlier pass at
longer channel length and higher damping gave a soma amplitude near the
numerical floor (ratio of soma to satellite amplitude `~0.004`), which was
caught and corrected by tuning damping and length to a regime with soma
amplitude two orders of magnitude clearer (§ Honest limits below states
exactly what was tuned and why, so the choice is auditable, not hidden).

---

## 3. Result 2 — length sweep retunes the regime, qualitatively as predicted

Holding one dendrite at length 10 and sweeping the other's actual channel
length across roughly one carrier wavelength, in the regime where the
carrier wavelength is comparable to the channel lengths (`Ω = 2π·0.10`,
`λ = 10` grid units):

```
  L_b  mismatch |    00      01      10      11   | regime
10.00     0.00  | 0.1145  0.0000  0.0000  0.1145  | XNOR-like
17.50     7.50  | 0.0519  0.0618  0.0618  0.0519  | XOR-like
```

Both regimes appear. The qualitative claim — length retunes the unit, full
stop — survives the move from algebra to a real field.

---

## 4. Result 3 — the shape of the transition does NOT survive, and the reason is the actual finding

The lumped model predicted a specific *shape*: a smooth, symmetric
`cos(φ)`-like curve crossing zero at exactly the quarter-wavelength point,
with the same sharp pointlike instability on either side. To test the shape
properly (not just "does XOR appear somewhere, does XNOR appear somewhere")
required moving to a regime where the channel length is genuinely small
compared to the carrier wavelength (`L ≪ λ`) — the regime the lumped model's
"length = pure phase delay" assumption actually requires. That meant a much
lower carrier frequency (`Ω = 2π·0.02`, `λ = 50`), with drive amplitude and
damping re-tuned for signal-to-noise (`drive_amp = 15`, `damping = 0.001`,
confirmed by a direct sweep before trusting any number from this regime).

The raw, unthresholded `agree − disagree` gap as a function of injected
phase mismatch, every value printed by `wall_shape_analysis.py`:

```
phase(deg) |  agree    disagree  | signed gap
        0  | 0.03457   0.00000   |  +0.03457
       30  | 0.02176   0.01693   |  +0.00484
       60  | 0.01777   0.01778   |  −0.00001   <- zero-crossing here, not at 90°
       90  | 0.01873   0.01801   |  +0.00072
      120  | 0.01853   0.01778   |  +0.00075
      150  | 0.01939   0.01630   |  +0.00310
      180  | 0.01615   0.02148   |  −0.00533   <- the only other clear sign flip
```

This is not what a `cos(φ)` curve looks like. The lumped model predicts a
symmetric crossing at 90° with comparable margin on either side; the real
field crosses near 60°, sits in a long, nearly flat, low-margin plateau from
roughly 60° to 165°, and only swings clearly XOR-like right at 180°. This
band was checked for being a damping artifact — re-run at three damping
values spanning a 4× range, and the flat plateau did **not** narrow,
ruling out "it's just decay smearing the signal" as the explanation.

**The actual mechanism, confirmed directly:** a channel that is driven at
one end and terminates in a soma cavity at the other is a **two-port
system, not a one-way delay line.** Waves reaching the soma partially
reflect and travel back down the channel, where they interfere with the
forward-going wave. `standing_wave_diagnostic.py` checked for this
directly — measuring the RMS amplitude at the channel midpoint across
several lengths gives a **non-monotonic** pattern (`L=10: 0.0187`,
`L=20: 0.0124`, `L=30: 0.0141`, `L=35: 0.0141`) — a one-way delay line with
fixed damping would decay monotonically with length; this doesn't, which is
the signature of a standing wave shaped by reflection, not pure one-way
propagation. The channel is acting as its own short resonant cavity,
something the lumped ODE has no term for at all, because it assumed the
phase a signal carries is fixed the instant it's launched and never
modified by anything downstream.

---

## 5. What this means for the parity-wall claim

The central qualitative claim from the lumped paper survives: **dendrite
length is a real, physical knob that retunes a resonator unit between
XOR-like and XNOR-like interference**, confirmed now in an actual 2-D wave
field with no algebraic shortcuts. That part of the original intuition is
sound at two levels of model fidelity, not one.

The specific, sharp picture — a clean `cos(φ)` curve with a single
pointlike instability exactly at the quarter-wavelength — does not survive,
and the reason is itself informative: **once a dendrite's length is not
negligible next to the carrier wavelength, the dendrite is not just a delay
line, it is a resonant element in its own right.** Its length doesn't only
set an arrival phase; it also sets which of *its own* standing-wave modes
get excited, and those modes feed back into what reaches the soma in a way
the lumped phase-injection model cannot represent.

That reframes the earlier "zero-margin wall at exactly λ/4" claim from a
precise geometric prediction into a *real but messier* phenomenon: there is
a region of poor margin, but its location and width depend on the channel's
own resonant structure, not on a clean trigonometric formula. A real
dendrite's role as a logic gate would depend on **both** its length-as-delay
**and** its length-as-resonator behavior simultaneously — which is a richer,
harder, and more interesting biological prediction than the lumped model
offered, not a weaker one.

---

## 6. Honest limits

- This is a 2-D scalar wave model with idealized circular cavities and
  straight channels of fixed width — a substantial simplification of any
  real biophysical dendrite, which is 3-D, has frequency-dependent
  cable properties (the classic Rall cable equation involves resistance
  and capacitance, not a clean wave speed `c`), and is not Neumann-reflecting
  in the same idealized sense. This build closes the gap from "lumped ODE"
  to "real wave equation," not the gap from "wave equation" to "biological
  cable."
- Two distinct parameter regimes were needed to get trustworthy
  signal-to-noise (`Ω = 2π·0.10` for the qualitative XOR/XNOR check,
  `Ω = 2π·0.02` for the shape-of-transition check), because the same drive
  amplitude and damping do not give comparable soma signal strength across
  very different carrier frequencies and channel-length-to-wavelength
  ratios. Every parameter choice is justified by an explicit tuning sweep
  in the code (`tune_parameters.py`-equivalent steps), not picked to
  produce a desired answer — but the reader should know two regimes were
  used, and why.
- The "two-port / reflection" explanation for the shape mismatch is
  supported by a non-monotonic midpoint-amplitude measurement, which is
  consistent with standing-wave structure but is not a full modal
  decomposition of the channel. A more complete test (next build) would
  measure the channel's actual resonant frequencies directly and check
  whether the wall's location shifts predictably with channel width and
  damping, the way a two-port resonator model would specify.
- The always-on-dendrite bias mechanism from the lumped paper (§6 of the
  prior paper) has not yet been re-tested in this PDE. That is the natural
  next step, not yet done, and should not be assumed to survive just
  because the basic interference mechanism did — the reflection effect
  found here could plausibly interact with a constant reference dendrite
  in ways the lumped model also could not anticipate.

---

## Reproduce it

```
python cavity_field.py                          # solver self-test: stability check
python pde_xor.py                               # matched-length interference, real field
python pde_length_sweep.py                       # qualitative XOR<->XNOR retuning, L~lambda regime
python pde_length_sweep_delayline_regime.py       # same test, L<<lambda regime, half-wavelength sweep
python wall_shape_analysis.py                    # the raw signed agree/disagree gap vs phase
python standing_wave_diagnostic.py               # the reflection/standing-wave check that explains the mismatch
```

Every number in this paper is reproduced by one of these six files, in the
order they were actually run. The honest result is smaller and stranger
than a clean confirmation: the mechanism is real, the shape isn't what was
predicted, and the reason it isn't is a finding in its own right.
