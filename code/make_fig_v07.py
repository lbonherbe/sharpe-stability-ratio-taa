"""Paper v0.7 Figure 1 (the v0.6 script on the v0.7 inputs; only the paths change): rolling 36-month Sharpe of HAA and the Momentum-Correlation Triplet,
with the autocorrelation of each rolling series. Same data, estimator and cutoff as the v0.5 study
(v07/inputs, completed months through 2026-08-31). Prints the values it uses and asserts that
they equal the v0.5 supplementary table, so the figure adds no new number to the paper."""
import csv, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import _chartkit as ck
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from numpy.lib.stride_tricks import sliding_window_view
W, L, CUTOFF = 36, 35, "2026-08-31"

def rolling_sharpe(r, w=W):
    win = sliding_window_view(np.asarray(r, float), w); sd = win.std(axis=1, ddof=1); return win.mean(axis=1) / sd
def nw_var(z, bw):
    n = z.size; c = z - z.mean(); ac = np.correlate(c, c, mode="full")[n - 1:n + bw] / n
    return float(ac[0] + 2 * np.dot(1 - np.arange(1, bw + 1) / (bw + 1), ac[1:]))
def acf(z, kmax):
    n = z.size; c = z - z.mean(); ac = np.correlate(c, c, mode="full")[n - 1:n + kmax] / n; return ac / ac[0]
def rets(nav):
    ks = sorted(k for k in nav if k <= CUTOFF + "T"); v = np.array([float(nav[k]) for k in ks]); return ks[1:], v[1:] / v[:-1] - 1

navs = {}
for line in open(os.path.join(ROOT, "v07", "inputs", "variants_monthend.jsonl")):
    d = json.loads(line)
    if d["variant_id"] in (1, 10): navs[d["variant_id"]] = d["nav"]
supp = {r["variant_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "v07", "results", "main", "published_variants.csv")))}
S = {}
for vid, label in ((1, "HAA"), (10, "Triplet")):
    dates, r = rets(navs[vid]); z = rolling_sharpe(r); v = nw_var(z, L)
    s = dict(label=label, dates=dates[W - 1:], z=z, mean_ann=z.mean() * math.sqrt(12), mean=z.mean(), naive=z.std(ddof=1), hac=math.sqrt(v), ssr=z.mean() / math.sqrt(v), n=z.size)
    ref = supp[str(vid)]
    assert abs(s["ssr"] - float(ref["ssr_full"])) < 5e-5, (label, s["ssr"], ref["ssr_full"])
    assert abs(s["hac"] - float(ref["hac_sd"])) < 5e-5 and abs(s["naive"] - float(ref["naive_sd"])) < 5e-5
    assert abs(s["mean_ann"] - float(ref["mean_rolling_sharpe_ann"])) < 5e-5 and s["n"] == int(ref["n_windows"])
    S[label] = s
    print(f"{label}: N={s['n']} first={s['dates'][0]} mean_ann={s['mean_ann']:.4f} mean_pp={s['mean']:.4f} naive={s['naive']:.4f} hac={s['hac']:.4f} hac/naive={s['hac']/s['naive']:.2f} ssr={s['ssr']:.4f} min_ann={s['z'].min()*math.sqrt(12):.2f}")

P1, P2, P3 = ck.apply(plt, "emerald_rose")
to_x = lambda d: int(d[:4]) + (int(d[5:7]) - 1) / 12
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [2.1, 1]})
for s, col in ((S["HAA"], P2), (S["Triplet"], P1)):
    xs = [to_x(d) for d in s["dates"]]
    a1.plot(xs, s["z"] * math.sqrt(12), color=col, lw=1.3, label=f"{s['label']}: mean {s['mean_ann']:.2f}, SSR {s['ssr']:.2f}")
    a1.hlines(s["mean_ann"], xs[0], xs[-1], color=col, lw=1, ls="--", alpha=.9)
a1.axhline(0, color=ck.INK, lw=.8, alpha=.6); a1.set_xlim(1976, 2027)
a1.set_ylabel("rolling 36-month Sharpe, annualised"); a1.set_title("A. The rolling Sharpe ratio (dashed: its mean)", fontsize=11, loc="left")
a1.legend(frameon=False, loc="lower left", fontsize=9); ck.style(a1, "y")
k = np.arange(0, 61)
for s, col in ((S["HAA"], P2), (S["Triplet"], P1)):
    a2.plot(k, acf(s["z"], 60), color=col, lw=1.4, label=s["label"])
a2.plot(k[:37], 1 - k[:37] / 36, color=ck.MUTED, lw=1, ls=":", label="overlap alone, 1 - k/36")
a2.axhline(0, color=ck.INK, lw=.8, alpha=.6); a2.set_xlabel("lag k, months"); a2.set_ylabel("autocorrelation")
a2.set_title("B. Memory of the rolling series", fontsize=11, loc="left"); a2.legend(frameon=False, fontsize=8, loc="upper right"); ck.style(a2)
fig.tight_layout()
out = os.path.join(ROOT, "v07", "charts", "fig_v07_worked_example.png"); fig.savefig(out, dpi=125, bbox_inches="tight"); print("wrote", out)
