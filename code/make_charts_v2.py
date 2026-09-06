"""Charts for the working paper (six figures). Reads results/, writes charts/."""
import csv, json, math, sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _chartkit as ck
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
S = os.environ.get("SSR_OUT_DIR", os.path.join(_HERE, "..", "results")); OUT = os.environ.get("SSR_CHART_DIR", os.path.join(_HERE, "..", "charts"))
import os; os.makedirs(OUT, exist_ok=True)
P1, P2, P3 = ck.apply(plt, "emerald_rose")
DPI = 125

rows = [r for r in csv.DictReader(open(f"{S}/published_variants.csv")) if r["excluded_from_primary"] != "True"]
f = lambda v: float(v) if v not in ("", None, "None") else None
bench = {r["benchmark"]: r for r in csv.DictReader(open(f"{S}/benchmarks.csv"))}
for b in bench.values(): b["sharpe"] = b["sharpe_ann"]
res = json.load(open(f"{S}/results.json"))

def save(fig, name):
    path = f"{OUT}/{name}.png"; fig.savefig(path, dpi=DPI, bbox_inches="tight"); plt.close(fig); print("wrote", path)

# Figure 1: distribution of SSR (full history) with benchmark markers
ssr = np.array([f(r["ssr_full"]) for r in rows if f(r["ssr_full"]) is not None])
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.hist(ssr, bins=np.arange(0.1, 1.25, 0.05), color=P1, alpha=.9, edgecolor=ck.BG)
for (label, key, col), yfrac in zip((("S&P 500", "S&P 500 (VFINX)", P2), ("60/40", "60/40 (VFINX/VBMFX)", P3)), (0.92, 0.62)):
    v = f(bench[key]["ssr_full"]); ax.axvline(v, color=col, lw=2, ls="--"); ax.text(v + 0.012, ax.get_ylim()[1] * yfrac, f"{label} {v:.2f}", color=col, fontsize=9)
med = float(np.median(ssr)); ax.axvline(med, color=ck.INK, lw=1, alpha=.6); ax.text(med + 0.01, ax.get_ylim()[1] * 0.78, f"median {med:.2f}", color=ck.INK, fontsize=9)
ax.set_xlabel("Sharpe Stability Ratio, full history (36-month window, bandwidth 35)"); ax.set_ylabel("published variants")
ax.set_title(f"Sharpe Stability Ratio, {len(ssr)} published variants, completed months through August 2026"); ck.style(ax, "y")
save(fig, "fig1_ssr_distribution")

# Figure 2: SSR vs Sharpe scatter, benchmarks marked, a few names
fig, ax = plt.subplots(figsize=(8, 5.2))
x = np.array([f(r["sharpe_ann"]) for r in rows]); y = np.array([f(r["ssr_full"]) if f(r["ssr_full"]) is not None else np.nan for r in rows])
lev = np.array([r["leveraged"] == "True" for r in rows])
ax.scatter(x[~lev], y[~lev], s=22, color=P1, alpha=.75, label="unleveraged variants")
ax.scatter(x[lev], y[lev], s=22, color=P2, alpha=.75, label="leveraged variants")
for key, marker, label in (("S&P 500 (VFINX)", "*", "S&P 500"), ("60/40 (VFINX/VBMFX)", "D", "60/40"), ("Gold (GLD)", "s", "Gold"), ("Long Treasuries (TLT)", "^", "TLT")):
    b = bench[key]
    if f(b["ssr_full"]) is None: continue
    ax.scatter([f(b["sharpe"])], [f(b["ssr_full"])], s=140, marker=marker, color=ck.INK, zorder=5); ax.annotate(label, (f(b["sharpe"]), f(b["ssr_full"])), xytext=(6, 4), textcoords="offset points", color=ck.INK, fontsize=9)
for name in ("momentum-correlation-triplet/mom-corr-triplet-standard", "haa/haa-standard", "classic-60-40/classic-60-40-base", "sma-trend/sma-trend-gld", "gem/gem-standard"):
    r = next((r for r in rows if r["name"] == name), None)
    if r and f(r["ssr_full"]) is not None:
        ax.annotate(name.split("/")[1], (f(r["sharpe_ann"]), f(r["ssr_full"])), xytext=(6, -10), textcoords="offset points", color=ck.MUTED, fontsize=8)
rho = res["spearman_full"]["sharpe_full"]["rho"]
ax.set_xlabel("annualised monthly Sharpe ratio, full history, cash reference zero"); ax.set_ylabel("Sharpe Stability Ratio, full history")
ax.set_title(f"SSR against the Sharpe ratio, full history: rank correlation {rho:.2f}"); ax.legend(frameon=False, loc="upper left"); ck.style(ax)
save(fig, "fig2_ssr_vs_sharpe")

# Figure 3: rolling 36-month Sharpe, HAA vs S&P 500
haa = json.load(open(f"{S}/rolling_haa-standard.json")); sp = json.load(open(f"{S}/rolling_sp500.json"))
def to_x(d): y, m = int(d[:4]), int(d[5:7]); return y + (m - 1) / 12
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.plot([to_x(d) for d in haa["dates"]], haa["rolling_sharpe_ann"], color=P1, lw=1.4, label="HAA standard")
ax.plot([to_x(d) for d in sp["dates"]], sp["rolling_sharpe_ann"], color=P2, lw=1.2, label="S&P 500 (VFINX)")
ax.axhline(0, color=ck.INK, lw=.8, alpha=.6)
ytop = ax.get_ylim()[1]
for yr, lab, yf in ((2000, "dot-com", 0.92), (2008, "GFC", 0.92), (2020, "COVID", 0.92), (2022, "2022", 0.80)):
    ax.axvline(yr, color=ck.MUTED, lw=.6, ls=":"); ax.text(yr + 0.15, ytop * yf, lab, color=ck.MUTED, fontsize=8)
haa_ssr = next(f(r["ssr_full"]) for r in rows if r["name"] == "haa/haa-standard"); sp_ssr = f(bench["S&P 500 (VFINX)"]["ssr_full"])
ax.set_xlim(1976, 2027); ax.set_ylabel("rolling 36-month Sharpe, annualised"); ax.set_xlabel("")
ax.set_title("Rolling 36-month annualised Sharpe ratio: HAA standard and S&P 500 (VFINX)"); ax.legend(frameon=False, loc="upper left"); ck.style(ax, "y")
save(fig, "fig3_rolling_sharpe_haa_sp500")

# Figure 4: SSR since 2000 vs since 2008 (regime dependence)
x = np.array([f(r["ssr_2000"]) if f(r["ssr_2000"]) is not None else np.nan for r in rows]); y = np.array([f(r["ssr_2008"]) if f(r["ssr_2008"]) is not None else np.nan for r in rows])
fig, ax = plt.subplots(figsize=(7, 6))
m = np.isfinite(x) & np.isfinite(y)
ax.scatter(x[m], y[m], s=22, color=P1, alpha=.7, label="published variants")
lim = (0, max(np.nanmax(x[m]), np.nanmax(y[m])) + 0.1); ax.plot(lim, lim, color=ck.MUTED, lw=.8, ls="--"); ax.set_xlim(lim); ax.set_ylim(lim)
for key, marker, label in (("S&P 500 (VFINX)", "*", "S&P 500"), ("60/40 (VFINX/VBMFX)", "D", "60/40"), ("Nasdaq 100 (QQQ)", "P", "QQQ")):
    b = bench[key]
    if f(b["ssr_2000"]) is None or f(b["ssr_2008"]) is None: continue
    ax.scatter([f(b["ssr_2000"])], [f(b["ssr_2008"])], s=150, marker=marker, color=P2, zorder=5); ax.annotate(label, (f(b["ssr_2000"]), f(b["ssr_2008"])), xytext=(7, 3), textcoords="offset points", color=P2, fontsize=9)
rc = res["spearman_windows"]["2000_vs_2008"]["rho"]; n_pairs = res["spearman_windows"]["2000_vs_2008"]["n"]; b1 = res["beat_S&P 500 (VFINX)"]
ax.set_xlabel("SSR, January 2000 to August 2026"); ax.set_ylabel("SSR, January 2008 to August 2026")
ax.set_title(f"SSR on two windows, {n_pairs} paired variants: rank correlation {rc:.2f}\nS&P 500 exceeded by {b1['ssr_2000'][0]} of {b1['ssr_2000'][1]} (2000 window), {b1['ssr_2008'][0]} of {b1['ssr_2008'][1]} (2008 window)", fontsize=11)
ax.legend(frameon=False, loc="upper left"); ck.style(ax)
save(fig, "fig4_regime_2000_vs_2008")

# Figure 5: SSR vs annual turnover
x = np.array([f(r["turnover"]) if f(r["turnover"]) is not None else np.nan for r in rows]); y = np.array([f(r["ssr_full"]) if f(r["ssr_full"]) is not None else np.nan for r in rows])
m = np.isfinite(x) & np.isfinite(y) & (x > 0)
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.scatter(x[m], y[m], s=22, color=P1, alpha=.7)
ax.set_xscale("log"); ax.set_xlabel("annual turnover (log scale)"); ax.set_ylabel("Sharpe Stability Ratio, full history")
rt = res["spearman_full"]["turnover"]["rho"]
for t in res["turnover_terciles"]:
    lo, hi = t["range"]; ax.hlines(t["median_ssr"], max(lo, 0.01), hi, color=P2, lw=2.5); ax.text(math.sqrt(max(lo, 0.01) * hi), t["median_ssr"] + 0.02, f"median {t['median_ssr']:.2f}", color=P2, fontsize=8, ha="center")
ax.set_title(f"SSR and reported annual turnover: rank correlation {rt:.2f}; tercile medians marked; one zero-turnover variant omitted by the log axis", fontsize=10); ck.style(ax)
save(fig, "fig5_ssr_vs_turnover")

# Figure 6: bootstrap intervals for the top and bottom 12
rk = [r for r in rows if f(r["ssr_full"]) is not None and f(r["boot36_pct_lo95"]) is not None]
sel = rk[:12] + rk[-12:]
fig, ax = plt.subplots(figsize=(8, 7.2))
ys = np.arange(len(sel))[::-1]
for yy, r in zip(ys, sel):
    lo, hi, v = f(r["boot36_pct_lo95"]), f(r["boot36_pct_hi95"]), f(r["ssr_full"])
    ax.hlines(yy, lo, hi, color=P1 if v >= 0.5 else P2, lw=2); ax.plot([v], [yy], "o", color=ck.INK, ms=4)
ax.set_yticks(ys); ax.set_yticklabels([r["name"].split("/")[1][:34] for r in sel], fontsize=8)
ax.axvline(0.5, color=ck.MUTED, lw=.8, ls=":"); ax.axvline(0, color=ck.INK, lw=.8, alpha=.5)
bs = res["bootstrap"]
ax.set_xlabel("SSR point estimate with 95% percentile moving-block-bootstrap interval (36-month blocks, 2,000 replicates)")
ax.set_title("Selected SSR estimates and marginal 95% percentile bootstrap intervals, twelve highest and twelve lowest", fontsize=10); ck.style(ax, "x")
save(fig, "fig6_bootstrap_intervals")
print("done")
