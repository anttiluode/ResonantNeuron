"""
resonator_alu_demo.py — watch the resonator network add two numbers
===================================================================
Live tkinter view of the theta-gamma clocked ripple adder. Each full-adder stage
is a cluster of resonator units (XOR/AND/OR); the theta clock steps the carry
along one stage per cycle. You enter two numbers; the network adds them in front
of you, lighting each gate by its soma amplitude (bright = high |s|).

Headless:  python resonator_alu_demo.py --selftest
Live:      python resonator_alu_demo.py

PerceptionLab / Antti Luode, with Claude. Do not hype. Do not lie. Just show.
"""
import sys
import numpy as np
from resonator_neuron import encode_bit
from gates import make_gate
from adder import ripple_add

if "--selftest" in sys.argv:
    rng = np.random.default_rng(1)
    bad = sum(ripple_add(int(rng.integers(0, 256)), int(rng.integers(0, 256)), 8) !=
              (lambda x, y: x + y)(*divmod(0, 1)) for _ in range(0))  # noop guard
    ok = all(ripple_add(x, y, 8) == x + y
             for x, y in [(int(rng.integers(0, 256)), int(rng.integers(0, 256))) for _ in range(500)])
    print(f"resonator ALU: 500/500 random 8-bit additions correct = {ok}")
    sys.exit(0)


import tkinter as tk

GATE_COLOR = {"XOR": "#ffb020", "AND": "#39ff88", "OR": "#88aaff"}


class ALUDemo:
    def __init__(self, root):
        self.root = root
        root.title("Resonator ALU — a computer made of interference")
        root.configure(bg="#05050a")
        tk.Label(root, text="RESONATOR ALU  //  soma interference + threshold axons = arithmetic",
                 font=("Consolas", 13, "bold"), fg="#00ffcc", bg="#0a0f1c").pack(fill="x", pady=8)
        ctl = tk.Frame(root, bg="#05050a"); ctl.pack(pady=6)
        tk.Label(ctl, text="A:", fg="#aaa", bg="#05050a", font=("Consolas", 12)).pack(side="left")
        self.ea = tk.Entry(ctl, width=6, font=("Consolas", 12)); self.ea.insert(0, "13"); self.ea.pack(side="left", padx=4)
        tk.Label(ctl, text="B:", fg="#aaa", bg="#05050a", font=("Consolas", 12)).pack(side="left")
        self.eb = tk.Entry(ctl, width=6, font=("Consolas", 12)); self.eb.insert(0, "7"); self.eb.pack(side="left", padx=4)
        tk.Button(ctl, text="ADD (step theta cycles)", command=self.start, bg="#10331f", fg="#00ffcc",
                  font=("Consolas", 11, "bold"), relief="flat", padx=12).pack(side="left", padx=8)
        self.cv = tk.Canvas(root, width=1100, height=520, bg="#020208", highlightthickness=0); self.cv.pack(padx=10, pady=10)
        self.lbl = tk.Label(root, text="", fg="#00ffcc", bg="#05050a", font=("Consolas", 16, "bold")); self.lbl.pack(pady=6)
        self.G = {k: make_gate(k) for k in ["XOR", "AND", "OR"]}
        self.NB = 8

    def amp(self, kind, bits):
        return self.G[kind].output([encode_bit(b) for b in bits], dynamical=False)[1]

    def start(self):
        try:
            self.x = int(self.ea.get()); self.y = int(self.eb.get())
        except ValueError:
            return
        self.carry = 0; self.out = 0; self.stage = 0
        self.lbl.config(text=f"adding {self.x} + {self.y} ...")
        self.step()

    def step(self):
        if self.stage >= self.NB:
            self.out |= (self.carry << self.NB)
            ok = (self.out == self.x + self.y)
            self.lbl.config(text=f"{self.x} + {self.y} = {self.out}   {'CORRECT' if ok else 'WRONG'}",
                            fg="#00ffcc" if ok else "#ff4444")
            return
        i = self.stage
        a = (self.x >> i) & 1; b = (self.y >> i) & 1; cin = self.carry
        axb = self.G["XOR"].output([encode_bit(a), encode_bit(b)], dynamical=False)[0]
        s = self.G["XOR"].output([encode_bit(axb), encode_bit(cin)], dynamical=False)[0]
        ab = self.G["AND"].output([encode_bit(a), encode_bit(b)], dynamical=False)[0]
        cab = self.G["AND"].output([encode_bit(cin), encode_bit(axb)], dynamical=False)[0]
        cout = self.G["OR"].output([encode_bit(ab), encode_bit(cab)], dynamical=False)[0]
        self.out |= (s << i); self.carry = cout

        self.cv.delete("all")
        # draw the stage as a soma + dendrite cluster
        gates = [("XOR", [a, b], axb), ("XOR", [axb, cin], s),
                 ("AND", [a, b], ab), ("AND", [cin, axb], cab), ("OR", [ab, cab], cout)]
        for gi, (kind, ins, outb) in enumerate(gates):
            cx, cy = 180 + gi * 190, 230
            amp = self.amp(kind, ins); bright = int(min(255, 60 + amp * 90))
            col = GATE_COLOR[kind]
            # soma
            self.cv.create_oval(cx - 46, cy - 46, cx + 46, cy + 46, fill=f"#{bright:02x}{bright:02x}30", outline=col, width=3)
            self.cv.create_text(cx, cy - 6, text=kind, fill=col, font=("Consolas", 13, "bold"))
            self.cv.create_text(cx, cy + 14, text=f"|s|={amp:.1f}", fill="#ccd", font=("Consolas", 9))
            # dendrites (inputs)
            for di, bit in enumerate(ins):
                dy = cy - 70 - di * 26
                self.cv.create_line(cx, cy - 46, cx - 60, dy, fill="#445", width=2)
                self.cv.create_oval(cx - 72, dy - 9, cx - 48, dy + 9,
                                    fill="#cc3344" if bit else "#2233aa", outline="#666")
            # axon (output)
            self.cv.create_line(cx, cy + 46, cx, cy + 80, fill=col, width=3)
            self.cv.create_oval(cx - 11, cy + 80, cx + 11, cy + 102,
                                fill="#cc3344" if outb else "#2233aa", outline=col, width=2)
        self.cv.create_text(550, 40, text=f"THETA CYCLE {i}   (bit {i}:  a={a} b={b} cin={cin}  ->  sum={s} carry={cout})",
                            fill="#00ffcc", font=("Consolas", 12, "bold"))
        self.cv.create_text(550, 470, text=f"partial sum so far: {self.out}   carry into next stage: {cout}",
                            fill="#ffaa00", font=("Consolas", 12))
        self.stage += 1
        self.root.after(900, self.step)


if __name__ == "__main__":
    root = tk.Tk()
    ALUDemo(root)
    root.mainloop()
