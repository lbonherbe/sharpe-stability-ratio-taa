"""SSR study v2 (2026-09-06): the referee-driven regeneration.

Changes versus ssr_paper_study.py, all in response to the adversarial review (paper/codex-review-v0.2.md):
- completed months only: returns dated after CUTOFF (2026-08-31) are dropped (the extract ended 3/4 Sep 2026);
- three variants of one strategy whose macroeconomic input uses revised rather than point-in-time data are
  excluded from the PRIMARY sample (EXCLUDED_STRATEGIES); their effect is reported as a sensitivity;
- distinct-value counts use the same eligible cohort for SSR and DSR;
- turnover tercile bounds come from the tercile slices themselves (the old range bug);
- bootstrap B = 2000 with bootstrap mean, percentile AND basic intervals, and the uncentered proportion q(<=0.5);
- extra diagnostics: within-tactical turnover correlation, tercile composition, subperiod rank correlations under
  four bandwidths with pairwise sample sizes, sample-size-rule lag distribution, mean/naive-sd/HAC-sd for named
  comparisons, duplicate return paths, HAA rolling counts, partial-month sensitivity, DSR precision facts;
- results.json is standards-compliant (no NaN).
Definitions are unchanged (rolling 36-month per-period Sharpe, ddof=1, Bartlett L=35 with divisor-n autocovariances,
SR* = 0, 120-month gate) and mirror backend/app/services/sharpe_stability.py.
"""
from __future__ import annotations
import json, math, csv, os
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

_HERE = os.path.dirname(os.path.abspath(__file__))
# Month-end extracts (variants_monthend.jsonl, variants_monthly.jsonl, bench_monthend.jsonl, leaderboard.json)
# are not redistributed in this archive; see data/README.md. Point SSR_DATA_DIR at a folder holding them.
A = os.environ.get("SSR_DATA_DIR", os.path.join(_HERE, "..", "data"))
OUT = os.environ.get("SSR_OUT_DIR", os.path.join(_HERE, "..", "results")); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20260906)
CUTOFF = "2026-08-31"
EXCLUDED_STRATEGIES = {"ggcem"}  # revised-data macro input, restatement pending (identified in the supplement)
W = 36; L = 35; GATE = 120; B = 2000

def rolling_sharpe(r, w=W):
    v = np.asarray(r, float)
    if v.size < w: return np.empty(0)
    win = sliding_window_view(v, w); sd = win.std(axis=1, ddof=1)
    return np.divide(win.mean(axis=1), sd, out=np.full(win.shape[0], np.nan), where=sd > 1e-12)

def nw_var(z, bw):
    z = np.asarray(z, float); n = z.size
    if n == 0 or np.ptp(z) == 0: return 0.0
    bw = min(bw, n - 1); c = z - z.mean()
    ac = np.correlate(c, c, mode="full")[n - 1:n + bw] / n
    wts = 1.0 - np.arange(1, bw + 1) / (bw + 1)
    return float(ac[0] + 2.0 * np.dot(wts, ac[1:]))

def ssr_parts(r, w=W, bw=None, gate=GATE):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if r.size < gate or r.size < w: return None
    z = rolling_sharpe(r, w)
    if not np.all(np.isfinite(z)): return None
    v = nw_var(z, (w - 1) if bw is None else bw)
    if v <= 0: return None
    return {"ssr": float(z.mean() / math.sqrt(v)), "mean_z": float(z.mean()), "naive_sd": float(z.std(ddof=1)), "hac_sd": float(math.sqrt(v)), "n_windows": int(z.size), "min_z_ann": float(z.min() * math.sqrt(12)), "neg_share": float((z < 0).mean())}

def ssr(r, **k):
    p = ssr_parts(r, **k); return None if p is None else p["ssr"]

def nw_rule_L(n): return int(math.floor(4 * (n / 100.0) ** (2.0 / 9.0)))
def sharpe_ann(r): r = np.asarray(r, float); return float(r.mean() / r.std(ddof=1) * math.sqrt(12))
def psr0(r):
    from statistics import NormalDist
    r = np.asarray(r, float); n = r.size; sr = r.mean() / r.std(ddof=1)
    zz = (r - r.mean()) / r.std(ddof=1); g3 = float((zz ** 3).mean()); g4 = float((zz ** 4).mean())
    var = 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2
    return float(NormalDist().cdf(sr * math.sqrt(n - 1) / math.sqrt(var))) if var > 0 else None

def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3: return None, int(m.sum())
    def ranks(x):
        order = np.argsort(x, kind="mergesort"); r = np.empty(len(x)); r[order] = np.arange(1, len(x) + 1)
        xs = x[order]; i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[j + 1] == xs[i]: j += 1
            if j > i: r[order[i:j + 1]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ra, rb = ranks(a[m]), ranks(b[m]); return float(np.corrcoef(ra, rb)[0, 1]), int(m.sum())

def rets_from_nav(nav, cutoff=CUTOFF):
    ks = sorted(k for k in nav if k <= cutoff + "T"); v = np.array([float(nav[k]) for k in ks])
    return ks[1:], v[1:] / v[:-1] - 1.0

def window(dates, r, start=None, end=None):
    m = np.array([(start is None or d >= start) and (end is None or d <= end) for d in dates]); return np.asarray(r)[m]

# ---------------------------------------------------------------- data
meta = {json.loads(l)["variant_id"]: json.loads(l) for l in open(f"{A}/variants_monthly.jsonl")}
navs = {json.loads(l)["variant_id"]: json.loads(l)["nav"] for l in open(f"{A}/variants_monthend.jsonl")}
lbj = json.load(open(f"{A}/leaderboard.json")); lb = {e["variant_id"]: e for e in lbj["entries"]}
bench_nav = {json.loads(l)["symbol"]: json.loads(l)["nav"] for l in open(f"{A}/bench_monthend.jsonl")}

series = {}
for vid, nav in navs.items():
    d, r = rets_from_nav(nav); m = meta[vid]; e = lb.get(vid)
    series[vid] = dict(id=vid, name=f"{m['strategy_slug']}/{m['variant_slug']}", strategy=m["strategy_slug"], dates=d, r=r, published=e is not None,
                       excluded=m["strategy_slug"] in EXCLUDED_STRATEGIES,
                       dsr=e.get("deflated_sharpe") if e else None, turnover=e.get("annual_turnover") if e else None, stype=e.get("strategy_type") if e else None,
                       freq=e.get("frequency") if e else None, leveraged=bool(e.get("variant_is_leveraged")) if e else None, risk=e.get("risk_category") if e else None,
                       cagr=(e.get("metrics") or {}).get("cagr") if e else None, maxdd=(e.get("metrics") or {}).get("max_drawdown") if e else None,
                       stored_monthly_sharpe=float(m["monthly_sharpe"]) if m.get("monthly_sharpe") else None)
def blend(navA, navB, wa):
    da, ra = rets_from_nav(navA); db, rb = rets_from_nav(navB); ib = {d[:7]: x for d, x in zip(db, rb)}
    dd, rr = [], []
    for d, x in zip(da, ra):
        if d[:7] in ib: dd.append(d); rr.append(wa * x + (1 - wa) * ib[d[:7]])
    return dd, np.array(rr)
benchmarks = {}
for sym, label in (("VFINX", "S&P 500 (VFINX)"), ("VBMFX", "US bonds (VBMFX)"), ("GLD", "Gold (GLD)"), ("TLT", "Long Treasuries (TLT)"), ("QQQ", "Nasdaq 100 (QQQ)"), ("VUSTX", "Long Treasuries (VUSTX)")):
    d, r = rets_from_nav(bench_nav[sym]); benchmarks[label] = dict(id=sym, name=label, dates=d, r=r)
d, r = blend(bench_nav["VFINX"], bench_nav["VBMFX"], 0.6); benchmarks["60/40 (VFINX/VBMFX)"] = dict(id="6040", name="60/40 (VFINX/VBMFX)", dates=d, r=r)

published_all = [s for s in series.values() if s["published"]]
primary = [s for s in published_all if not s["excluded"]]
R = {"definition": "ssr-36m-nw-v1", "cutoff": CUTOFF, "excluded_strategies": sorted(EXCLUDED_STRATEGIES), "n_active": len(series), "n_published": len(published_all), "n_excluded_published": sum(1 for s in published_all if s["excluded"]), "n_primary_published": len(primary)}

# ---------------------------------------------------------------- per-series statistics
for s in list(series.values()) + list(benchmarks.values()):
    p = ssr_parts(s["r"]); s["parts"] = p; s["ssr_full"] = p["ssr"] if p else None
    s["sharpe_full"] = sharpe_ann(s["r"]); s["months"] = int(len(s["r"])); s["start"] = s["dates"][0][:7]; s["end"] = s["dates"][-1][:7]
    s["ssr_2000"] = ssr(window(s["dates"], s["r"], "2000-01")) if s["dates"][0] <= "2000-01-31" else None
    s["ssr_2008"] = ssr(window(s["dates"], s["r"], "2008-01")) if s["dates"][0] <= "2008-01-31" else None
    s["sharpe_2000"] = sharpe_ann(window(s["dates"], s["r"], "2000-01")) if s["ssr_2000"] is not None else None
    s["psr0"] = psr0(s["r"]) if len(s["r"]) > 12 else None
    s["cassr"] = (s["ssr_full"] * s["psr0"]) if (s["ssr_full"] is not None and s["psr0"] is not None) else None
    s["nw_rule_L"] = nw_rule_L(max(len(s["r"]) - W + 1, 1))
    for w in (24, 36, 48, 60): s[f"ssr_w{w}"] = ssr(s["r"], w=w, bw=w - 1)
    for bw in (5, 15, 35, 71): s[f"ssr_L{bw}"] = ssr(s["r"], bw=bw)
    s["ssr_LNW"] = ssr(s["r"], bw=s["nw_rule_L"])
    s["ssr_w36_L15"] = s["ssr_L15"]; s["ssr_w60_L35"] = ssr(s["r"], w=60, bw=35); s["ssr_w24_L35"] = ssr(s["r"], w=24, bw=35)
subs = {"pre2000": (None, "1999-12-31"), "2000s": ("2000-01", "2009-12-31"), "2010s": ("2010-01", "2019-12-31"), "2020s": ("2020-01", None)}
SUBGATE = 72
for s in list(series.values()) + list(benchmarks.values()):
    for k, (a, b) in subs.items():
        rr = window(s["dates"], s["r"], a, b); s[f"sub_{k}"] = ssr(rr, gate=SUBGATE); s[f"sub_{k}_n"] = int(len(rr))
        for bw in (5, 15, 71): s[f"sub_{k}_L{bw}"] = ssr(rr, bw=bw, gate=SUBGATE)
    s[f"sub_2020s_dates"] = (window(s["dates"], np.array(s["dates"]), "2020-01").tolist()[:1] + window(s["dates"], np.array(s["dates"]), "2020-01").tolist()[-1:])

el = [s for s in primary if s["ssr_full"] is not None]  # eligible primary
R["n_eligible_primary"] = len(el)
vals = np.array([s["ssr_full"] for s in el])
R["quantiles"] = {str(q): float(np.quantile(vals, q)) for q in (0, .1, .25, .5, .75, .9, 1)}
R["above"] = {"0.5": int((vals >= 0.5).sum()), "0.7": int((vals >= 0.7).sum()), "below_0.3": int((vals < 0.3).sum())}
R["distinct_2dp"] = {"ssr": len({round(float(v), 2) for v in vals}), "dsr": len({round(s["dsr"], 2) for s in el}), "dsr_full_precision": len({s["dsr"] for s in el}), "dsr_exactly_1": sum(1 for s in el if s["dsr"] == 1.0), "dsr_1_at_2dp": sum(1 for s in el if round(s["dsr"], 2) == 1.0)}
R["history"] = {"months_min": min(s["months"] for s in el), "months_median": float(np.median([s["months"] for s in el])), "months_max": max(s["months"] for s in el), "starts_before": {y: sum(1 for s in el if s["start"] < y) for y in ("1980", "1990", "2000", "2008")}, "end": sorted({s["end"] for s in el}), "strategies": len({s["strategy"] for s in el})}
def sp(key_a, key_b, pop=el):
    c, n = spearman([s[key_a] for s in pop], [s[key_b] for s in pop]); return {"rho": c, "n": n}
R["spearman_full"] = {k: sp("ssr_full", k) for k in ("sharpe_full", "dsr", "psr0", "turnover", "cagr", "maxdd")}
R["spearman_windows"] = {"full_vs_2000": sp("ssr_full", "ssr_2000"), "full_vs_2008": sp("ssr_full", "ssr_2008"), "2000_vs_2008": sp("ssr_2000", "ssr_2008"), "sharpe2000_vs_ssr2000": sp("sharpe_2000", "ssr_2000")}
# groups
def med(v): v = sorted(v); return {"n": len(v), "median": float(np.median(v)), "p25": float(np.quantile(v, .25)), "p75": float(np.quantile(v, .75))} if v else None
groups = {}
for key in ("stype", "freq", "leveraged", "risk"):
    g = {}
    for s in el: g.setdefault(str(s[key]), []).append(s["ssr_full"])
    groups[key] = {k: med(v) for k, v in g.items()}
R["groups"] = groups
R["groups_mean_z_ann"] = {k: float(np.median([s["parts"]["mean_z"] * math.sqrt(12) for s in el if str(s["risk"]) == k])) for k in ("conservative", "moderate", "aggressive")}
# turnover terciles with deterministic tie policy (turnover, then variant id)
tv = sorted([s for s in el if s["turnover"] is not None], key=lambda s: (s["turnover"], s["id"])); n3 = len(tv) // 3
slices = [tv[:n3], tv[n3:2 * n3], tv[2 * n3:]]
R["turnover_terciles"] = [{"tercile": i + 1, "range": [sl[0]["turnover"], sl[-1]["turnover"]], "n": len(sl), "median_ssr": float(np.median([s["ssr_full"] for s in sl])), "median_sharpe": float(np.median([s["sharpe_full"] for s in sl])),
                           "tactical": sum(1 for s in sl if s["stype"] == "taa"), "static": sum(1 for s in sl if s["stype"] == "static"), "monthly": sum(1 for s in sl if s["freq"] == "monthly"), "daily": sum(1 for s in sl if s["freq"] == "daily"), "annual_or_quarterly": sum(1 for s in sl if s["freq"] in ("annual", "quarterly")), "leveraged": sum(1 for s in sl if s["leveraged"])} for i, sl in enumerate(slices)]
R["spearman_turnover_within_tactical"] = sp("ssr_full", "turnover", [s for s in el if s["stype"] == "taa"])
R["spearman_turnover_within_monthly_tactical"] = sp("ssr_full", "turnover", [s for s in el if s["stype"] == "taa" and s["freq"] == "monthly"])
R["zero_turnover_count"] = sum(1 for s in el if s["turnover"] is not None and s["turnover"] <= 0)
# benchmarks + beat counts
R["benchmarks"] = {b["name"]: {k: b.get(k) for k in ("start", "end", "months", "sharpe_full", "ssr_full", "ssr_2000", "ssr_2008", "sub_pre2000", "sub_2000s", "sub_2010s", "sub_2020s", "sub_2000s_n")} for b in benchmarks.values()}
for label in ("S&P 500 (VFINX)", "60/40 (VFINX/VBMFX)"):
    b = benchmarks[label]
    R[f"beat_{label}"] = {w: [sum(1 for s in el if s[w] is not None and s[w] > b[w]), sum(1 for s in el if s[w] is not None)] for w in ("ssr_2000", "ssr_2008")}
# windows / bandwidths
wins = (24, 36, 48, 60)
R["window_medians"] = {f"w{w}": float(np.median([s[f"ssr_w{w}"] for s in el if s[f"ssr_w{w}"] is not None])) for w in wins}
R["window_rank_corr"] = {f"w{a}_w{b}": sp(f"ssr_w{a}", f"ssr_w{b}")["rho"] for a in wins for b in wins if a < b}
R["bandwidth_medians"] = {k: float(np.median([s[f"ssr_{k}"] for s in el if s[f"ssr_{k}"] is not None])) for k in ("L5", "L15", "L35", "L71", "LNW")}
R["bandwidth_rank_corr_vs_L35"] = {k: sp(f"ssr_{k}", "ssr_L35")["rho"] for k in ("L5", "L15", "L71", "LNW")}
R["factorial"] = {"w24_L35_median": float(np.median([s["ssr_w24_L35"] for s in el if s["ssr_w24_L35"] is not None])), "w60_L35_median": float(np.median([s["ssr_w60_L35"] for s in el if s["ssr_w60_L35"] is not None])), "w24_L35_vs_w36_L35": sp("ssr_w24_L35", "ssr_L35")["rho"], "w60_L35_vs_w36_L35": sp("ssr_w60_L35", "ssr_L35")["rho"]}
ranks35 = {s["id"]: i for i, s in enumerate(sorted(el, key=lambda s: -s["ssr_L35"]))}; ranks71 = {s["id"]: i for i, s in enumerate(sorted([s for s in el if s["ssr_L71"] is not None], key=lambda s: -s["ssr_L71"]))}
R["max_rank_move_L35_vs_L71"] = max(abs(ranks35[i] - ranks71[i]) for i in ranks71)
R["nw_rule_L_distribution"] = {str(k): sum(1 for s in el if s["nw_rule_L"] == k) for k in sorted({s["nw_rule_L"] for s in el})}
# subperiods
keys = list(subs)
R["subperiod_n"] = {k: sum(1 for s in primary if s[f"sub_{k}"] is not None) for k in keys}
R["subperiod_obs_2020s"] = sorted({s["sub_2020s_n"] for s in primary if s["sub_2020s"] is not None})
R["subperiod_medians"] = {k: float(np.median([s[f"sub_{k}"] for s in primary if s[f"sub_{k}"] is not None])) for k in keys}
R["subperiod_medians_by_type"] = {k: {t: float(np.median([s[f"sub_{k}"] for s in primary if s[f"sub_{k}"] is not None and s["stype"] == t])) for t in ("taa", "static")} for k in keys}
R["subperiod_rank_corr"] = {f"{a}|{b}": sp(f"sub_{a}", f"sub_{b}", primary) for i, a in enumerate(keys) for b in keys[i + 1:]}
R["subperiod_2000s_vs_2010s_by_bandwidth"] = {f"L{bw}": sp(f"sub_2000s_L{bw}" if bw != 35 else "sub_2000s", f"sub_2010s_L{bw}" if bw != 35 else "sub_2010s", primary)["rho"] for bw in (5, 15, 35, 71)}
R["subperiod_pre2000_obs_range"] = [min(s["sub_pre2000_n"] for s in primary if s["sub_pre2000"] is not None), max(s["sub_pre2000_n"] for s in primary if s["sub_pre2000"] is not None)]
# bootstrap
def mbb(r, block, nb):
    r = np.asarray(r, float); T = r.size; nblk = int(math.ceil(T / block)); starts = rng.integers(0, T - block + 1, size=(nb, nblk))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(nb, -1)[:, :T]; return r[idx]
boot_summary = []
for s in el:
    out = {}
    for block in (12, 36):
        paths = mbb(s["r"], block, B); vb = []
        for pth in paths:
            z = rolling_sharpe(pth, W)
            if not np.all(np.isfinite(z)): continue
            v = nw_var(z, L); vb.append(z.mean() / math.sqrt(v) if v > 0 else np.nan)
        vb = np.array(vb); vb = vb[np.isfinite(vb)]; est = s["ssr_full"]
        lo, hi = float(np.quantile(vb, .025)), float(np.quantile(vb, .975))
        out[f"b{block}"] = {"valid": int(vb.size), "mean": float(vb.mean()), "pct_lo95": lo, "pct_hi95": hi, "basic_lo95": 2 * est - hi, "basic_hi95": 2 * est - lo, "pct5": float(np.quantile(vb, .05)), "q_le0": float((vb <= 0).mean()), "q_le05": float((vb <= 0.5).mean())}
    s["boot"] = out
R["bootstrap"] = {"B": B, "n": len(el),
                  "share_pct_interval_excludes_0_b12": float(np.mean([s["boot"]["b12"]["pct_lo95"] > 0 for s in el])), "share_pct_interval_excludes_0_b36": float(np.mean([s["boot"]["b36"]["pct_lo95"] > 0 for s in el])),
                  "share_pct5_above_05_b36": float(np.mean([s["boot"]["b36"]["pct5"] > 0.5 for s in el])), "share_pct_interval_entirely_below_05_b36": float(np.mean([s["boot"]["b36"]["pct_hi95"] < 0.5 for s in el])),
                  "median_pct_width_b36": float(np.median([s["boot"]["b36"]["pct_hi95"] - s["boot"]["b36"]["pct_lo95"] for s in el])),
                  "median_bootmean_minus_estimate_b36": float(np.median([s["boot"]["b36"]["mean"] - s["ssr_full"] for s in el])), "median_bootmean_over_estimate_b36": float(np.median([s["boot"]["b36"]["mean"] / s["ssr_full"] for s in el])),
                  "share_basic_lo95_above_05_b36": float(np.mean([s["boot"]["b36"]["basic_lo95"] > 0.5 for s in el])), "mc_se_at_p05": float(math.sqrt(0.05 * 0.95 / B))}
# quadrants + CASSR
q = {"dsr_ge_0.9_ssr_ge_0.5": 0, "dsr_ge_0.9_ssr_lt_0.5": 0, "dsr_lt_0.9_ssr_ge_0.5": 0, "dsr_lt_0.9_ssr_lt_0.5": 0}
for s in el: q[f"dsr_{'ge' if s['dsr'] >= 0.9 else 'lt'}_0.9_ssr_{'ge' if s['ssr_full'] >= 0.5 else 'lt'}_0.5"] += 1
R["quadrants"] = q; R["cassr_vs_ssr_rank_corr"] = sp("cassr", "ssr_full")["rho"]; R["psr0_min"] = float(min(s["psr0"] for s in el))
# duplicates, HAA, named comparisons, partial-month + exclusion sensitivities
sig = {}
for s in el: sig.setdefault(tuple(np.round(s["r"][-120:], 10)), []).append(s["name"])
R["duplicate_return_paths"] = [v for v in sig.values() if len(v) > 1]
haa = series[1]; R["haa"] = {"months": haa["months"], "n_windows": haa["parts"]["n_windows"], "min_z_ann": haa["parts"]["min_z_ann"], "neg_share": haa["parts"]["neg_share"], "rolling_start": haa["dates"][W - 1][:7], "ssr_full": haa["ssr_full"], "ssr_2000": haa["ssr_2000"]}
R["named"] = {s["name"]: {"sharpe": s["sharpe_full"], "ssr": s["ssr_full"], "mean_z_ann": s["parts"]["mean_z"] * math.sqrt(12), "naive_sd": s["parts"]["naive_sd"], "hac_sd": s["parts"]["hac_sd"], "neg_share": s["parts"]["neg_share"], "q_le05_b36": s["boot"]["b36"]["q_le05"], "pct": [s["boot"]["b36"]["pct_lo95"], s["boot"]["b36"]["pct_hi95"]], "basic": [s["boot"]["b36"]["basic_lo95"], s["boot"]["b36"]["basic_hi95"]], "bootmean": s["boot"]["b36"]["mean"]} for s in el if s["name"] in ("haa/haa-standard", "gem/gem-standard", "momentum-correlation-triplet/mom-corr-triplet-standard", "classic-60-40/classic-60-40-base", "golden-butterfly/golden-butterfly-base")}
for b in benchmarks.values():
    if b["parts"]: R["named"][b["name"]] = {"sharpe": b["sharpe_full"], "ssr": b["ssr_full"], "mean_z_ann": b["parts"]["mean_z"] * math.sqrt(12), "naive_sd": b["parts"]["naive_sd"], "hac_sd": b["parts"]["hac_sd"], "neg_share": b["parts"]["neg_share"]}
# sensitivity: including the excluded strategy's published variants; and partial-month (recompute with no cutoff)
inc = [s for s in published_all if s["ssr_full"] is not None]
R["sensitivity_inclusion"] = {"n": len(inc), "median": float(np.median([s["ssr_full"] for s in inc])), "above_0.5": int(sum(1 for s in inc if s["ssr_full"] >= 0.5)), "spearman_sharpe": sp("ssr_full", "sharpe_full", inc)["rho"], "subperiod_2000s_vs_2010s": sp("sub_2000s", "sub_2010s", published_all)["rho"], "subperiod_2010s_vs_2020s": sp("sub_2010s", "sub_2020s", published_all)["rho"]}
part = {}
for s in el:
    d, r = rets_from_nav(navs[s["id"]], cutoff="2026-12-31"); part[s["id"]] = ssr(r)
R["sensitivity_partial_month"] = {"median_with_partial": float(np.median([v for v in part.values() if v is not None])), "above_0.5_with_partial": int(sum(1 for v in part.values() if v is not None and v >= 0.5)), "rank_corr": spearman([part[s["id"]] for s in el], [s["ssr_full"] for s in el])[0], "max_abs_diff": float(max(abs(part[s["id"]] - s["ssr_full"]) for s in el if part[s["id"]] is not None))}
R["stored_vs_recomputed_monthly_sharpe_max_abs_diff"] = float(max(abs(s["stored_monthly_sharpe"] - (s["r"].mean() / s["r"].std(ddof=1))) for s in el if s["stored_monthly_sharpe"] is not None))
# tables
def rnd(v, k=4): return None if v is None else round(float(v), k)
rows = []
for s in sorted(published_all, key=lambda s: -(s["ssr_full"] if s["ssr_full"] is not None else -9)):
    rows.append({"variant_id": s["id"], "name": s["name"], "strategy": s["strategy"], "excluded_from_primary": s["excluded"], "strategy_type": s["stype"], "frequency": s["freq"], "leveraged": s["leveraged"], "risk_category": s["risk"], "start": s["start"], "end": s["end"], "months": s["months"], "n_windows": s["parts"]["n_windows"] if s["parts"] else None,
                 "sharpe_ann": rnd(s["sharpe_full"]), "dsr": s["dsr"], "psr0": rnd(s["psr0"]), "turnover": s["turnover"], "cagr": s["cagr"], "maxdd": s["maxdd"],
                 "ssr_full": rnd(s["ssr_full"]), "mean_rolling_sharpe_ann": rnd(s["parts"]["mean_z"] * math.sqrt(12)) if s["parts"] else None, "naive_sd": rnd(s["parts"]["naive_sd"]) if s["parts"] else None, "hac_sd": rnd(s["parts"]["hac_sd"]) if s["parts"] else None, "neg_share": rnd(s["parts"]["neg_share"]) if s["parts"] else None,
                 "ssr_2000": rnd(s["ssr_2000"]), "ssr_2008": rnd(s["ssr_2008"]), "cassr": rnd(s["cassr"]), **{f"ssr_w{w}": rnd(s[f"ssr_w{w}"]) for w in wins}, **{f"ssr_{k}": rnd(s[f"ssr_{k}"]) for k in ("L5", "L15", "L35", "L71", "LNW")}, "nw_rule_L": s["nw_rule_L"],
                 **{f"sub_{k}": rnd(s[f"sub_{k}"]) for k in keys}, **{f"sub_{k}_n": s[f"sub_{k}_n"] for k in keys},
                 **({f"boot36_{x}": rnd(s["boot"]["b36"][x]) for x in ("mean", "pct_lo95", "pct_hi95", "basic_lo95", "basic_hi95", "pct5", "q_le05")} if s.get("boot") else {}), **({f"boot12_{x}": rnd(s["boot"]["b12"][x]) for x in ("pct_lo95", "pct_hi95", "q_le05")} if s.get("boot") else {})})
with open(f"{OUT}/published_variants.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
brows = [{"benchmark": b["name"], "start": b["start"], "end": b["end"], "months": b["months"], "sharpe_ann": rnd(b["sharpe_full"]), "ssr_full": rnd(b["ssr_full"]), "ssr_2000": rnd(b["ssr_2000"]), "ssr_2008": rnd(b["ssr_2008"]), **{f"sub_{k}": rnd(b[f"sub_{k}"]) for k in keys}, **{f"sub_{k}_n": b[f"sub_{k}_n"] for k in keys}} for b in benchmarks.values()]
with open(f"{OUT}/benchmarks.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(brows[0])); w.writeheader(); w.writerows(brows)
def clean(o):
    if isinstance(o, float): return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    return o
json.dump(clean(R), open(f"{OUT}/results.json", "w"), indent=1)
for label, s in (("haa-standard", series[1]), ("sp500", benchmarks["S&P 500 (VFINX)"])):
    z = rolling_sharpe(s["r"], W) * math.sqrt(12); json.dump({"dates": s["dates"][W - 1:], "rolling_sharpe_ann": [None if not np.isfinite(x) else float(x) for x in z]}, open(f"{OUT}/rolling_{label}.json", "w"))
print(json.dumps(clean(R), indent=1))
