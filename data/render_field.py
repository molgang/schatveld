#!/usr/bin/env python3
"""Rendert het Schatveld dat de game genereert (faithful port van de Luau-logica):
land-gebruik (Weddewarden/Land Wursten) + de metaalwaarde-heatmap 0-100 + detector-view."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import numpy as np

COLS, ROWS, SEED = 32, 24, 20260818

# --- MetalField (identiek aan roblox/src/shared/MetalField.lua) ---
def mix(a,b,seed):
    a%=8192; b%=8192; seed%=8192
    h=(a*92821+b*68389+seed*40503)%1000003
    return (h*31+a+b)%101
def value(c,r,seed=SEED):
    base=mix(c,r,seed); cluster=mix(c//4,r//4,seed+7)
    return max(0,min(100,int(base*0.7+cluster*0.3)))

# --- Cadastre.build (identiek aan Cadastre.lua) ---
use=[["Acker"]*COLS for _ in range(ROWS)]
coastal=[[False]*COLS for _ in range(ROWS)]
for c0 in range(0,COLS,4):
    for seg in (0,1):
        r0=seg*(ROWS//2); r1=(ROWS//2-1) if seg==0 else ROWS-1
        wurt=(c0<=8 and seg==0)
        u="Wurt" if wurt else ("Deich" if c0<=1 else "Acker")
        cst=(c0<=3)
        for c in range(c0,min(c0+4,COLS)):
            for r in range(r0,r1+1):
                use[r][c]=u; coastal[r][c]=cst

USE_COL={"Acker":(0.47,0.38,0.26),"Wurt":(0.43,0.47,0.35),"Deich":(0.35,0.47,0.31),"Wasser":(0.24,0.38,0.51)}
metal=np.array([[value(c,r) for c in range(COLS)] for r in range(ROWS)])

fig=plt.figure(figsize=(15,8.6),dpi=130); fig.patch.set_facecolor("#0e1116")
fig.suptitle("Schatveld Weddewarden — Land Wursten (32×24 = 768 Flurstück-blokken)  ·  seed "+str(SEED),
             color="#e6c229",fontsize=15,y=0.98)

# Panel A: land-gebruik
axA=fig.add_subplot(1,3,1); axA.set_title("Landgebruik (kadaster)",color="#cdd7e2",fontsize=11)
img=np.zeros((ROWS,COLS,3))
for r in range(ROWS):
    for c in range(COLS): img[r][c]=USE_COL[use[r][c]]
axA.imshow(img,origin="lower"); axA.set_xticks([]); axA.set_yticks([])
axA.text(2,ROWS/2-2,"Deich\n+ kust",color="#dfe8ef",fontsize=8)
axA.text(3,3,"WURT\nWeddewarden",color="#f4d58a",fontsize=8,weight="bold")
_h=[mp.Patch(color=USE_COL["Acker"],label="Acker"),mp.Patch(color=USE_COL["Wurt"],label="Wurt"),mp.Patch(color=USE_COL["Deich"],label="Deich/kust")]
axA.legend(handles=_h,loc="lower right",fontsize=7,facecolor="#161b22",labelcolor="#cdd7e2")

# Panel B: metaal-heatmap 0-100
axB=fig.add_subplot(1,3,2); axB.set_title("Metaalwaarde 0–100 (detector)",color="#cdd7e2",fontsize=11)
im=axB.imshow(metal,origin="lower",cmap="inferno",vmin=0,vmax=100)
# markeer <10 (altijd roestig ijzer)
ys,xs=np.where(metal<10)
axB.scatter(xs,ys,s=18,facecolors="none",edgecolors="#5fd0ff",linewidths=1.1,label="<10 → roestig ijzer")
axB.set_xticks([]); axB.set_yticks([]); axB.legend(loc="lower right",fontsize=7,facecolor="#161b22",labelcolor="#cdd7e2")
cb=fig.colorbar(im,ax=axB,fraction=0.046,pad=0.04); cb.ax.tick_params(colors="#cdd7e2")

# Panel C: detector-view (getallen zoals de speler ze op de blokken ziet)
axC=fig.add_subplot(1,3,3); axC.set_title("Detector-view (getal per blok)",color="#cdd7e2",fontsize=11)
axC.set_xlim(-0.5,15.5); axC.set_ylim(-0.5,11.5); axC.set_facecolor("#0e1116")
for r in range(12):
    for c in range(16):
        v=metal[r][c]
        col="#b08c78" if v<10 else ("#f4d75a" if v>=70 else "#d6dbe5")
        axC.add_patch(mp.Rectangle((c-0.48,r-0.48),0.96,0.96,facecolor=USE_COL[use[r][c]],edgecolor="#20262e"))
        axC.text(c,r,str(v),ha="center",va="center",fontsize=7,color=col,weight="bold")
axC.set_xticks([]); axC.set_yticks([]); axC.set_aspect("equal")
axC.text(0,-1.6,"linker-onder 16×12 hoek · geel≥70, blauw-ijzer <10",color="#8b97a4",fontsize=7)

fig.tight_layout(rect=[0,0,1,0.96]); fig.savefig("data/schatveld_field.png",facecolor=fig.get_facecolor())
# stats
lo=int((metal<10).sum()); hi=int((metal>=80).sum())
print(f"veld: min {metal.min()} max {metal.max()} gem {metal.mean():.0f} · <10={lo} blokken (roestig ijzer) · >=80={hi} rijke blokken")
print("beeld -> data/schatveld_field.png")
