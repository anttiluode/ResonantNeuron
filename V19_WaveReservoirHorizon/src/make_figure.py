"""Generate the summary figure from results/two_factor.json."""
import sys, os, json, numpy as np
import matplotlib.pyplot as plt
sys.path.insert(0,os.path.dirname(__file__))
from reservoir import WaveField, make_magnetron, make_open_box

here=os.path.dirname(__file__)
res=json.load(open(os.path.join(here,"..","results","two_factor.json")))
R=res["results"]; delays=res["delays"]; chance=res["chance"]

fig=plt.figure(figsize=(14,8))

# forgetting curves
ax1=plt.subplot(2,2,1)
styles={"A":("open box, uniform","o-","#4477aa"),
        "B":("open box, tuned","s--","#66ccee"),
        "C":("cavity, uniform","o-","#ee6677"),
        "D":("cavity, tuned","s--","#cc3311")}
for k,(lab,st,col) in styles.items():
    ax1.semilogx(delays,[R[k]["acc"][str(d)] if str(d) in R[k]["acc"] else R[k]["acc"][d] for d in delays],
                 st,color=col,label=lab,lw=2)
ax1.axhline(chance,color="k",ls=":",label="chance")
ax1.set_xlabel("delay after last pulse (steps)"); ax1.set_ylabel("order-recall accuracy")
ax1.set_title("Forgetting curves\n(all matched to 32-step energy half-life)")
ax1.set_ylim(0,1.05); ax1.legend(fontsize=8); ax1.grid(alpha=0.3)

# 2x2 table as heatmap
ax2=plt.subplot(2,2,2)
H=np.array([[R["A"]["horizon"],R["B"]["horizon"]],
            [R["C"]["horizon"],R["D"]["horizon"]]])
im=ax2.imshow(H,cmap="viridis",aspect="auto")
ax2.set_xticks([0,1]); ax2.set_xticklabels(["uniform","tuned"])
ax2.set_yticks([0,1]); ax2.set_yticklabels(["open box","magnetron"])
for i in range(2):
    for j in range(2):
        ax2.text(j,i,f"{int(H[i,j])}",ha="center",va="center",
                 color="w",fontsize=14,fontweight="bold")
ax2.set_title("Memory horizon (steps)\ncavity rows are lower bounds")
plt.colorbar(im,ax=ax2,fraction=0.046)

# energy vs order: the key conceptual panel
ax3=plt.subplot(2,2,3)
N=64; dt=0.6
insM,_,cM=make_magnetron(N)
f=WaveField(N,dt=dt,inside=insM,b=np.zeros((N,N))); f.reset(); f.inject(cM,1.0)
E=[]; 
for _ in range(1900):
    f.step(); E.append(f.energy())
E=np.array(E)/max(E)
ax3.semilogx(range(1,1901),E,color="#ee6677",label="cavity bulk energy")
ax3.axhline(0.5,color="gray",ls=":",label="half-energy (~32 steps)")
ax3.axvline(32,color="gray",ls=":")
ax3.axvspan(1900,1901,color="none")
ax3.text(200,0.6,"order still\nreadable here\n(>1900 steps)",fontsize=9,color="#cc3311")
ax3.set_xlabel("steps"); ax3.set_ylabel("energy / peak")
ax3.set_title("The point: energy fades in ~32 steps,\norder survives ~16x longer")
ax3.legend(fontsize=8); ax3.grid(alpha=0.3)

# the cavity geometry
ax4=plt.subplot(2,2,4)
ax4.imshow(insM,cmap="Greys",origin="upper")
ax4.set_title("Magnetron cavity\n(reflecting walls, one outlet right)")
ax4.axis("off")

plt.tight_layout()
plt.savefig(os.path.join(here,"..","results","two_factor_figure.png"),dpi=140,bbox_inches="tight")
print("saved results/two_factor_figure.png")
