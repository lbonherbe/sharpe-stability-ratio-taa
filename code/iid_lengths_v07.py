"""Supplement to the permutation script's iid baseline for v0.7: the sample's median history moved from 486 to 499
months and its longest from 1,274 to 1,519. Same estimator and DGP (iid normal, annualised Sharpe 1.0 and the four
Sharpe levels at the median length), 2,000 replicates per cell, own seed (20261017) so the permutation script's
random stream, and therefore every permutation result, is untouched. Output: results/iid_lengths_v07.json."""
import json, math, os, sys
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, L, GATE, R = 36, 35, 120, 2000
rng = np.random.default_rng(20261017)
def rolling_sharpe(v):
    win = sliding_window_view(v, W); sd = win.std(axis=1, ddof=1); return win.mean(axis=1) / sd
def nw_var(z, bw):
    n = z.size; bw = min(bw, n - 1); c = z - z.mean(); ac = np.correlate(c, c, mode="full")[n - 1:n + bw] / n
    return float(ac[0] + 2.0 * np.dot(1.0 - np.arange(1, bw + 1) / (bw + 1), ac[1:]))
def ssr(r):
    z = rolling_sharpe(r); v = nw_var(z, L); return z.mean() / math.sqrt(v) if v > 0 else None
out = {"seed": 20261017, "R": R, "by_length_sharpe1": {}, "by_sharpe_499m": {}}
for n in (120, 220, 499, 1519):
    v = np.array([x for x in (ssr(rng.normal(1 / math.sqrt(12), 1.0, n)) for _ in range(R)) if x is not None])
    out["by_length_sharpe1"][n] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), se=float(v.std(ddof=1) / math.sqrt(v.size)))
for S in (0.5, 1.0, 1.5, 2.0):
    v = np.array([x for x in (ssr(rng.normal(S / math.sqrt(12), 1.0, 499)) for _ in range(R)) if x is not None])
    out["by_sharpe_499m"][S] = dict(mean=float(v.mean()), ratio=float(v.mean() / S))
json.dump(out, open(f"{V}/results/iid_lengths_v07.json", "w"), indent=1); print(json.dumps(out, indent=1))
