"""Paper v0.7 Figure 4 (Section 5.6): full-history SSR above cash against SSR(0), 173 published variants, with the two
benchmarks, the 0.5 cutoff of SSR(0) and the 0.37 split above cash. Reads results/main and results/excess."""
import csv, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _chartkit as ck
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr

def load(col):
    rows = {r["variant_id"]: r for r in csv.DictReader(open(f"{V}/results/{col}/published_variants.csv")) if r["excluded_from_primary"] != "True" and r["ssr_full"] not in ("", "None")}
    bench = {r["benchmark"]: r for r in csv.DictReader(open(f"{V}/results/{col}/benchmarks.csv"))}
    return rows, bench
A, BA = load("main"); C, BC = load("excess")
ids = sorted(set(A) & set(C)); assert len(ids) == 173, len(ids)
x = np.array([float(A[i]["ssr_full"]) for i in ids]); y = np.array([float(C[i]["ssr_full"]) for i in ids])
lev = np.array([A[i]["leveraged"] == "True" for i in ids]); stat = np.array([A[i]["strategy_type"] == "static" for i in ids])
rho = spearmanr(x, y).correlation
P1, P2, P3 = ck.apply(plt, "emerald_rose")
fig, ax = plt.subplots(figsize=(7.4, 6))
ax.scatter(x[~stat], y[~stat], s=22, color=P1, alpha=.75, label="tactical variants")
ax.scatter(x[stat], y[stat], s=26, color=P2, alpha=.8, marker="s", label="static variants")
lim = (0, max(x.max(), y.max()) + 0.05)
ax.plot(lim, lim, color=ck.MUTED, lw=.8, ls="--"); ax.set_xlim(lim); ax.set_ylim(lim)
ax.axvline(0.5, color=ck.MUTED, lw=.8, ls=":"); ax.axhline(0.37, color=ck.MUTED, lw=.8, ls=":")
ax.text(0.505, 0.02, "SSR(0) = 0.5", color=ck.MUTED, fontsize=8); ax.text(0.02, 0.38, "above cash = 0.37", color=ck.MUTED, fontsize=8)
for key, marker, label in (("S&P 500 (VFINX)", "*", "S&P 500"), ("60/40 (VFINX/VBMFX)", "D", "60/40")):
    ax.scatter([float(BA[key]["ssr_full"])], [float(BC[key]["ssr_full"])], s=140, marker=marker, color=ck.INK, zorder=5)
    ax.annotate(label, (float(BA[key]["ssr_full"]), float(BC[key]["ssr_full"])), xytext=(6, -10), textcoords="offset points", color=ck.INK, fontsize=9)
names = {"momentum-correlation-triplet/mom-corr-triplet-standard": "Triplet", "haa/haa-standard": "HAA", "low-initiative-letf-v2/low-initiative-letf-v2-standard": "Low-Initiative LETF v2",
         "dms-triad/dms-triad": "DMS Triad", "all-weather-dalio/all-weather-dalio-base": "All Weather", "sma-trend/sma-trend-gld": "SMA trend gold"}
for i in ids:
    n = A[i]["name"]
    if n in names:
        ax.annotate(names[n], (float(A[i]["ssr_full"]), float(C[i]["ssr_full"])), xytext=(6, 3), textcoords="offset points", color=ck.MUTED, fontsize=8)
missing = [n for n in names if n not in {A[i]["name"] for i in ids}]
print("names not found:", missing)
ax.set_xlabel("SSR, cash reference zero (the paper's measure)"); ax.set_ylabel("SSR of returns above USD cash")
ax.set_title(f"Full-history SSR above cash against SSR(0), 173 variants: rank correlation {rho:.2f}", fontsize=10)
ax.legend(frameon=False, loc="upper left"); ck.style(ax)
out = f"{V}/charts/fig_v07_above_cash.png"; fig.savefig(out, dpi=125, bbox_inches="tight"); print("wrote", out, f"rho {rho:.4f}")
