"""
field_timeline_viz.py -- a complementary view: the TEMPORAL cascade. Shows,
for each gate, its output-end membrane potential over time, stacked, so you
watch the computation flow through the dependency graph: input gates fire
first, their spikes trigger middle gates, which trigger the carry gate.

This is the clearest single picture of "the field computing": you literally
see each gate's spike arrive in dependency order.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from field_adder import FieldFullAdder

GATE_ORDER = ["XOR_ab", "AND_ab", "XOR_sum", "AND_cin", "OR_cout"]
GATE_LABEL = {
    "XOR_ab":  "XOR(a,b) = a^b",
    "AND_ab":  "AND(a,b) = carry1",
    "XOR_sum": "XOR(a^b,cin) = SUM",
    "AND_cin": "AND(cin,a^b) = carry2",
    "OR_cout": "OR(c1,c2) = CARRY",
}

def run_traces(a, b, cin, max_ticks=1600):
    fa = FieldFullAdder()
    fa.set_inputs(a, b, cin)
    for _ in range(120):
        for u in fa.units.values():
            u.step(settle_phase=True)
    traces = {n: [] for n in GATE_ORDER}
    sum_bit = cout = None
    for tick in range(max_ticks):
        for u in fa.units.values():
            u.step()
        for name, u in fa.units.items():
            traces[name].append(u.v[u.out_cell])
            if u._done: continue
            if u.output_bit() == 1:
                u._done = True
            else:
                bits = u.current_input_bits()
                if bits is not None:
                    _, fires = u.compute_drive()
                    if not fires:
                        u._nofire_count = getattr(u,'_nofire_count',0)+1
                        if u._nofire_count > 80:
                            u._done = True
        if fa.units["XOR_sum"]._done and sum_bit is None:
            sum_bit = fa.units["XOR_sum"].output_bit()
        if fa.units["OR_cout"]._done and cout is None:
            cout = fa.units["OR_cout"].output_bit()
        if sum_bit is not None and cout is not None:
            for _ in range(40):
                for u in fa.units.values(): u.step()
                for name, u in fa.units.items():
                    traces[name].append(u.v[u.out_cell])
            break
    return traces, sum_bit, cout

def make_timeline(a, b, cin, out_png="field_timeline.png"):
    traces, sum_bit, cout = run_traces(a, b, cin)
    fig, axes = plt.subplots(len(GATE_ORDER), 1, figsize=(11, 7), sharex=True)
    total = a + b + cin
    for ax, name in zip(axes, GATE_ORDER):
        t = np.array(traces[name])
        ax.plot(t, color="black", lw=1.0)
        ax.axhline(0.5, color="red", ls=":", lw=0.7, alpha=0.6)
        ax.fill_between(range(len(t)), 0.5, t, where=(t > 0.5),
                        color="orange", alpha=0.6)
        ax.set_ylabel(GATE_LABEL[name], fontsize=8, rotation=0,
                      ha="right", va="center")
        ax.set_ylim(-1.5, 2.2)
        ax.set_yticks([])
        # mark the spike-arrival (first crossing of 0.5)
        crossings = np.where(t > 0.5)[0]
        if len(crossings):
            ax.axvline(crossings[0], color="green", ls="--", lw=0.8, alpha=0.7)
            ax.text(crossings[0], 1.7, f" spike @ t={crossings[0]}",
                    color="green", fontsize=7)
    axes[-1].set_xlabel("time (ticks)")
    axes[0].set_title(f"Continuous-field full adder computing {a}+{b}+{cin} "
                      f"= sum {sum_bit}, carry {cout}  (expect sum {total&1}, "
                      f"carry {total>>1})\n"
                      f"each panel: a gate's output-end potential over time; "
                      f"orange = spike present (logical 1)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_png, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"saved timeline: {out_png}")
    print(f"{a}+{b}+{cin} = sum {sum_bit}, carry {cout} "
          f"({'OK' if (sum_bit==total&1 and cout==total>>1) else 'MISMATCH'})")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        a, b, cin = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    else:
        a, b, cin = 0, 1, 1
    make_timeline(a, b, cin)
