"""
field_adder_viz.py -- watch the continuous-field full adder COMPUTE.

Renders all five excitable gate-lines of a full adder as a live heatmap,
with each line's membrane potential v(x,t) shown as it evolves. You see:
  - input gates (XOR_ab, AND_ab) fire first when a,b arrive;
  - their spikes propagate down their axons (a bright pulse moving right);
  - when a spike reaches an output end, it latches and triggers the
    downstream gate (XOR_sum, AND_cin), whose spike then propagates;
  - finally OR_cout fires, producing the carry.

The wiring arrows show the physical coupling. The whole thing is ONE field
under ONE update rule -- there is no scheduler; downstream gates simply stay
quiet until real current arrives from upstream.

Saves an animated GIF and a final summary PNG so the computation is visible
without a live display.

Usage:
    python field_adder_viz.py            # default 0+1+1 (a carry case)
    python field_adder_viz.py 1 1 1      # pick a,b,cin

PerceptionLab / Antti Luode, with Claude. Helsinki, June 2026.
Do not hype. Do not lie. Just show.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from field_adder import FieldFullAdder


# gate display order (top to bottom), with their roles
GATE_ORDER = ["XOR_ab", "AND_ab", "XOR_sum", "AND_cin", "OR_cout"]
GATE_LABEL = {
    "XOR_ab":  "XOR(a,b)  = a^b",
    "AND_ab":  "AND(a,b)  = carry1",
    "XOR_sum": "XOR(a^b,cin) = SUM",
    "AND_cin": "AND(cin,a^b) = carry2",
    "OR_cout": "OR(c1,c2) = CARRY",
}


def run_and_record(a, b, cin, max_ticks=1600, record_every=4):
    """Run the field adder, recording the full field state every few ticks."""
    fa = FieldFullAdder()
    fa.set_inputs(a, b, cin)
    for _ in range(120):
        for u in fa.units.values():
            u.step(settle_phase=True)

    frames = []   # each frame: dict gate_name -> v array copy
    done_at = {}
    sum_bit = cout = None
    for tick in range(max_ticks):
        for u in fa.units.values():
            u.step()
        # done-flag logic (same as field_adder.run)
        for name, u in fa.units.items():
            if u._done:
                continue
            if u.output_bit() == 1:
                u._done = True
                done_at[name] = tick
            else:
                bits = u.current_input_bits()
                if bits is not None:
                    _, fires = u.compute_drive()
                    if not fires:
                        u._nofire_count = getattr(u, "_nofire_count", 0) + 1
                        if u._nofire_count > 80:
                            u._done = True
                            done_at[name] = tick
        if fa.units["XOR_sum"]._done and sum_bit is None:
            sum_bit = fa.units["XOR_sum"].output_bit()
        if fa.units["OR_cout"]._done and cout is None:
            cout = fa.units["OR_cout"].output_bit()
        if tick % record_every == 0:
            frames.append({n: fa.units[n].v.copy() for n in GATE_ORDER})
        if sum_bit is not None and cout is not None:
            # record a few extra frames so the end state is visible
            for _ in range(8):
                for u in fa.units.values():
                    u.step()
                frames.append({n: fa.units[n].v.copy() for n in GATE_ORDER})
            break
    return frames, sum_bit, cout, tick, done_at


def make_animation(a, b, cin, out_gif="field_adder.gif",
                   out_png="field_adder_final.png"):
    frames, sum_bit, cout, ticks, done_at = run_and_record(a, b, cin)
    n_cells = len(frames[0]["XOR_ab"])
    n_gates = len(GATE_ORDER)

    # build a (n_gates, n_cells) image per frame, stacked with gaps
    def frame_image(fr):
        img = np.full((n_gates, n_cells), np.nan)
        for i, name in enumerate(GATE_ORDER):
            img[i] = fr[name]
        return img

    fig, ax = plt.subplots(figsize=(11, 5.5))
    im = ax.imshow(frame_image(frames[0]), aspect="auto", cmap="inferno",
                   vmin=-1.3, vmax=2.0, interpolation="nearest")
    ax.set_yticks(range(n_gates))
    ax.set_yticklabels([GATE_LABEL[n] for n in GATE_ORDER], fontsize=9)
    ax.set_xlabel("position along axon  (input end -> output end)")
    title = ax.set_title("")
    cbar = fig.colorbar(im, ax=ax, fraction=0.025)
    cbar.set_label("membrane potential v")

    # mark input (AIS) and output ends
    ax.axvline(3, color="cyan", lw=0.8, ls=":", alpha=0.6)
    ax.axvline(n_cells - 3, color="lime", lw=0.8, ls=":", alpha=0.6)
    ax.text(3, -0.7, "input", color="cyan", fontsize=7, ha="center")
    ax.text(n_cells - 3, -0.7, "output", color="lime", fontsize=7, ha="center")

    total = a + b + cin
    def update(k):
        im.set_array(frame_image(frames[k]))
        title.set_text(f"Continuous-field full adder:  {a} + {b} + {cin}  "
                       f"(frame {k+1}/{len(frames)})   "
                       f"expect sum={total&1} carry={total>>1}")
        return [im, title]

    anim = FuncAnimation(fig, update, frames=len(frames), interval=60,
                         blit=False)
    anim.save(out_gif, writer=PillowWriter(fps=18))
    print(f"saved animation: {out_gif}  ({len(frames)} frames)")

    # final summary still
    update(len(frames) - 1)
    fig.savefig(out_png, dpi=110, bbox_inches="tight")
    print(f"saved final frame: {out_png}")
    plt.close(fig)

    print(f"\nResult: {a}+{b}+{cin} = sum {sum_bit}, carry {cout}  "
          f"(expected sum {total&1}, carry {total>>1})  "
          f"{'OK' if (sum_bit==total&1 and cout==total>>1) else 'MISMATCH'}")
    print(f"completed in {ticks} ticks")
    print("gate completion order (tick each gate's output resolved):")
    for name in GATE_ORDER:
        if name in done_at:
            print(f"   {GATE_LABEL[name]:28s} resolved at tick {done_at[name]}")


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        a, b, cin = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    else:
        a, b, cin = 0, 1, 1   # default: a carry-generating case
    print(f"Running continuous-field full adder for {a} + {b} + {cin} ...")
    make_animation(a, b, cin)
