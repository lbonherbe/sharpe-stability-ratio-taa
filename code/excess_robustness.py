"""Section 5.6 (SSR above cash): cross-column comparisons of the main study (SSR(0), results/main) and the above-cash
study (excess-cash-v2, results/excess), 173 variants. Writes results/excess_robustness.json and prints it."""
import csv, json, os
import numpy as np
from scipy.stats import spearmanr
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(col):
    return {r["variant_id"]: r for r in csv.DictReader(open(f"{V}/results/{col}/published_variants.csv")) if r["excluded_from_primary"] != "True" and r["ssr_full"] not in ("", "None")}
A, C = load("main"), load("excess"); ids = sorted(set(A) & set(C), key=int); assert len(ids) == 173
f = lambda r, k: float(r[k]) if r[k] not in ("", "None") else np.nan
a = np.array([f(A[i], "ssr_full") for i in ids]); c = np.array([f(C[i], "ssr_full") for i in ids])
sa = np.array([f(A[i], "sharpe_ann") for i in ids]); sc = np.array([f(C[i], "sharpe_ann") for i in ids])
start = np.array([A[i]["start"][:4] for i in ids]); stype = np.array([A[i]["strategy_type"] for i in ids])
out = {"n": len(ids)}
out["spearman_ssr_main_vs_excess"] = spearmanr(a, c).correlation
out["spearman_sharpe_main_vs_excess"] = spearmanr(sa, sc).correlation
out["pearson_ssr"] = float(np.corrcoef(a, c)[0, 1])
out["median_ratio_excess_over_main"] = float(np.median(c / a))
# flags: SSR(0) below 0.5 (the paper's cutoff) vs above-cash below 0.37 (the platform's split) and below 0.5
fa = a < 0.5
for thr in (0.37, 0.5):
    fc = c < thr
    out[f"flags_main05_vs_excess{thr}"] = {"both_low": int((fa & fc).sum()), "main_low_only": int((fa & ~fc).sum()), "excess_low_only": int((~fa & fc).sum()), "both_high": int((~fa & ~fc).sum()),
                                          "agree_share": float(((fa & fc) | (~fa & ~fc)).mean())}
# ranks
ra = (-a).argsort().argsort() + 1; rc = (-c).argsort().argsort() + 1
for k in (12, 43):
    out[f"top{k}_overlap"] = int(len(set(np.where(ra <= k)[0]) & set(np.where(rc <= k)[0])))
    out[f"bottom{k}_overlap"] = int(len(set(np.where(ra > 173 - k)[0]) & set(np.where(rc > 173 - k)[0])))
mv = np.abs(ra - rc); out["rank_move_median"] = float(np.median(mv)); out["rank_move_max"] = int(mv.max())
out["rank_move_ge_40"] = int((mv >= 40).sum())
# by start: the level drop is larger for histories that hold the high-rate decades
for lab, m in (("start_before_1990", start < "1990"), ("start_1990_on", start >= "1990"), ("start_2000_on", start >= "2000")):
    out[f"median_ratio_{lab}"] = [float(np.median(c[m] / a[m])), int(m.sum())]
    out[f"median_rank_change_{lab}"] = float(np.median((ra - rc)[m]))
for lab in ("taa", "static"):
    m = stype == lab; out[f"median_ratio_{lab}"] = float(np.median(c[m] / a[m]))
# biggest movers (rank)
order = np.argsort(rc - ra)
out["largest_rise"] = [[A[ids[j]]["name"], A[ids[j]]["start"], int(ra[j]), int(rc[j]), round(a[j], 4), round(c[j], 4)] for j in order[:8]]
out["largest_fall"] = [[A[ids[j]]["name"], A[ids[j]]["start"], int(ra[j]), int(rc[j]), round(a[j], 4), round(c[j], 4)] for j in order[::-1][:8]]
# permutation multiples, if available
try:
    pa = {r["id"]: r for r in csv.DictReader(open(f"{V}/results/main_perm/permutation_results.csv")) if r["kind"] == "variant" and r["window"] == "full"}
    pc = {r["id"]: r for r in csv.DictReader(open(f"{V}/results/excess_perm/permutation_results.csv")) if r["kind"] == "variant" and r["window"] == "full"}
    keys = [k for k in pa if k in pc and k in A]
    mk = "multiple"
    ma = np.array([float(pa[k][mk]) for k in keys]); mc = np.array([float(pc[k][mk]) for k in keys])
    out["perm_multiple_col"] = mk; out["perm_n"] = len(keys)
    out["spearman_multiple_main_vs_excess"] = spearmanr(ma, mc).correlation
    out["multiple_above1_both"] = int(((ma > 1) & (mc > 1)).sum())
except FileNotFoundError as e:
    out["perm"] = f"not yet: {e}"
json.dump(out, open(f"{V}/results/excess_robustness.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
