# The Whole Word At Once: A Fully Concurrent Ripple Adder, And The Carry That Walks It

### Combining multi-bit arithmetic with full concurrency — and measuring the carry physically rippling, one stage at a time

**PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.**

> Do not hype. Do not lie. Just show.

---

## 0. What this build does

v16 ended with a clean split it could not close in one file:

- `married_ripple.py` was *multi-bit* but *sequential* — each full adder ran
  to completion before the next bit began. Correct, but it hid all
  cross-stage timing.
- `married_adder_timed.py` was *concurrent* but *one bit only* — it revealed
  the per-stage spike latency (~460 ticks per spike-hop) but couldn't show
  how that latency accumulates across a multi-bit word.

This build combines them: an N-bit ripple-carry adder with **every stage of
every bit live on one shared clock at once**, where each carry physically
propagates as a spike before the next stage can consume it. The result is
that the adder computes correctly *and* exhibits the defining signature of
true ripple-carry — a total latency that grows linearly with word width,
because the carry has to physically walk the word one stage at a time.

| claim | status |
|---|---|
| a fully concurrent multi-bit adder (all stages live) computes correctly | **verified** — 3-bit 12/12, 4-bit 8/8 random additions correct |
| worst-case latency scales linearly with bit width | **verified** — 921 ticks per bit, dead linear from 1 to 5 bits |
| the linear growth is specifically the *carry* rippling, not per-bit overhead | **verified by control** — a sum-only case (no carry) stays flat at ~920 ticks regardless of width |
| the carry can be watched walking the word stage by stage | **verified** — carry-arrival trace: bit 0 at tick 919, bit 1 at 1840, bit 2 at 2761 |
| sums compute in parallel, only the carry is serial | **verified** — the textbook O(1)-sum / O(N)-carry structure, as literal spike propagation |
| this is a general-purpose concurrent processor | **false, and not claimed** — it is a verified concurrent ripple *adder*; §5 states the limits |

---

## 1. The architecture

`concurrent_ripple.py` instantiates N `FullAdderStage` objects up front, each
one five `TimedUnit`s (the married soma+axon units from v15/v16). Every tick,
*all* stages of *all* bits step together. The `a` and `b` input bits are
available to every stage at t=0; stage 0's carry-in is 0 immediately. But
each later stage's carry-dependent units stay in `WAIT` until that stage's
carry-in bit arrives — and the carry-in is wired from the previous stage's
carry-out *only once that carry-out spike has physically reached the end of
its OR unit's axon*.

So the ripple is real: stage i+1's carry path genuinely cannot begin until
stage i's carry has propagated in as a spike. Nothing is pre-computed or
short-circuited. The whole word is live simultaneously, but the carry chain
is forced to be serial by physics, exactly as in a hardware ripple-carry
adder.

---

## 2. Correctness under full concurrency

```
3-bit: 12/12 random additions correct (PASS)
4-bit:  8/8 random additions correct (PASS)
```

The adder computes correctly with every stage live at once — concurrency
does not corrupt the result. (Trial counts are modest because a fully
concurrent multi-bit excitable simulation is slow — every stage runs full
FitzHugh–Nagumo axon integrations every tick. Enough to prove correctness,
honestly scoped, not an exhaustive sweep.)

---

## 3. The finding: latency is linear in word width

The worst case for a ripple adder is an input that forces the carry to
propagate the entire word: `x = 2ⁿ − 1` (all ones), `y = 1`, so a carry born
at bit 0 must ripple all the way to bit n.

```
nbits | result | ticks | ticks/bit
    1 |      2 |   919 |   919.0
    2 |      4 |  1840 |   920.0
    3 |      8 |  2761 |   920.3
    4 |     16 |  3682 |   920.5
    5 |     32 |  4603 |   920.6
```

The total latency is almost perfectly linear: **+921 ticks for every
additional bit.** Each bit the carry must cross adds one stage's worth of
spike propagation. This is the defining behavior of ripple-carry — O(N)
delay in the word width — and here it is not a property assumed in a timing
model, it is the measured consequence of carries being physical spikes that
travel at finite speed.

---

## 4. The control: it really is the carry, not per-bit overhead

A linear-looking number is not enough on its own — the growth could in
principle be a fixed per-bit cost paid regardless of whether a carry
actually ripples. Three cases separate these:

```
WORST  (x=2ⁿ-1, y=1, full carry ripple):   +921 ticks per bit  (linear growth)
BEST   (x=0, y=0, no spikes at all):        ~3 ticks per bit    (flat, trivial)
MIXED  (x=2ⁿ-1, y=0, sums fire, no carry):  ~922 ticks TOTAL    (flat in N)
```

The MIXED case is the decisive one. All the sum bits fire (so spikes *do*
propagate), but no carry is ever generated, so nothing has to ripple. Its
latency is ~922 ticks **regardless of word width** — 2-bit, 3-bit, 4-bit all
land within a few ticks of each other. The sum bits all compute in parallel,
each one stage deep, finishing together. Only when a carry must ripple does
the latency grow with N.

That is the textbook structure of a ripple-carry adder made physical: the
sum bits are O(1) (parallel, constant depth), the carry chain is O(N)
(serial, walks the word). The control proves the linear scaling in §3 is
specifically the carry rippling, not an artifact of having more stages.

---

## 5. The carry, caught in the act

The carry-arrival trace for `7 + 1 = 8` (`0b0111 + 0b0001`, which forces a
carry through all four bits) shows the ripple walking the word:

```
carry out of bit 0 arrived at tick 919
carry out of bit 1 arrived at tick 1840
carry out of bit 2 arrived at tick 2761
total: 3222 ticks, result 8 (correct)
```

Each carry lands ~921 ticks after the previous one. This is the single most
direct picture of the whole result: a carry is not a number that appears
everywhere at once, it is a spike that propagates down one unit's axon,
triggers the next stage, which sends its own spike down its axon, and so on
across the word. The "ripple" in ripple-carry is, here, a literal travelling
wave.

---

## 6. What this completes, and what it doesn't

This closes the timing question the arc had been circling since v15:

- v15: one married unit computes + sends directionally + chains two-deep.
- v16: that unit scales to a full adder and a (sequential) multi-bit adder;
  concurrency on a single full adder reveals per-stage latency = logic depth.
- v17 (this): full concurrency across a multi-bit word, with the carry
  rippling as real spikes — latency linear in N, sums parallel, carry
  serial, all measured.

The directional resonator unit now demonstrably supports multi-bit
arithmetic as a concurrent physical process with the correct asymptotic
timing structure. The geometry computes (v11), the excitable axon gives
direction (v14), the marriage joins them (v15), and the join scales to a
word-wide concurrent adder whose carry physically ripples (v16-v17).

What this is **not**: a general-purpose processor. It is a verified
concurrent ripple *adder* — no subtraction, multiplication, registers,
memory, or control flow. It also does not claim the ~921-ticks-per-bit
figure is biologically calibrated; it is a structural existence result (the
latency is linear in N and equals summed per-stage spike delays), specific
to the axon length and FitzHugh–Nagumo speed used.

---

## 7. Honest limits

- The concurrency is a discrete shared-clock scheduler — all units advance
  one tick together. This captures the essential physics (downstream waits
  for upstream spike arrival) but is not a single continuous-time PDE field
  over the whole circuit. A true field simulation of the entire multi-stage
  device is the heavier next step.
- Correctness is shown on modest trial counts (12 and 8 random additions)
  because full concurrent excitable simulation is slow. The worst-case
  latency-scaling and the control cases are deterministic, so those are
  exact, but the random-addition correctness sweep is smaller than the
  algebraic adder's 1000-case sweep and is not claimed otherwise.
- Latency figures (~921 ticks/bit) are specific to axon_len=30 and the FHN
  propagation speed; they are a scaling result (linear in N), not an
  absolute timing claim.
- All upstream scope limits still apply: lumped resonator soma, 1-D FHN
  axon, engineered comparator between them.

---

## Reproduce it

```
python concurrent_ripple.py   # correctness, linear latency scaling, and the carry trace
```

The single file runs all three results: the random-addition correctness
check, the worst-case latency scaling (linear in bit width), and the
carry-arrival trace showing the ripple walk the word. It imports the timed
married unit and the gate/axon definitions from the adjacent files. The
headline: a fully concurrent multi-bit adder computes correctly, and its
carry physically ripples across the word — O(1) sums, O(N) carry — as real
spikes on an excitable substrate.
