"""Permutation benchmark for the SSR working paper, version 0.5 (Section 6.5).

Question: how much of a series' SSR comes from the level of its Sharpe ratio, and how much from the
order in which its monthly returns arrived? Reordering a series' own monthly returns at random keeps
its mean, its standard deviation and so its full-sample Sharpe ratio exactly, and destroys serial
dependence, volatility clustering and regime structure. The mean SSR of the reordered series is the
level a return series of that Sharpe ratio, distribution and length reaches with no temporal structure;
the permutation multiple is the real SSR divided by that mean.

The shuffle null was suggested by Randy Harris of Dual Momentum Systems (email of 22 September 2026).

Same data and estimator as ssr_paper_study_v2.py (functions copied verbatim): the month-end extracts
the study reads (for paper version 0.5, the series restated on 28 September 2026), completed months through 31 August 2026, 36-month window, Bartlett bandwidth 35, 120-month
gate, zero cash reference. The script stops if any real SSR differs from the published supplementary
table, so the definitions cannot have drifted.

Outputs: permutation_results.csv (per series), permutation_results.json (every number quoted in
the paper), permutation_run.log (console).
"""
import csv, json, math, os, sys, time
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

_HERE = os.path.dirname(os.path.abspath(__file__))
# Month-end extracts are not redistributed in this archive; see data/README.md. Point SSR_DATA_DIR at a folder holding them.
A = os.environ.get("SSR_DATA_DIR", os.path.join(_HERE, "..", "data"))
OUT = os.environ.get("SSR_OUT_DIR", os.path.join(_HERE, "..", "results")); os.makedirs(OUT, exist_ok=True)
SUPP = os.path.join(_HERE, "..", "results", "published_variants.csv")
CUTOFF = "2026-08-31"
EXCLUDED_STRATEGIES = {"ggcem"}
W = 36; L = 35; GATE = 120
B = 10_000            # reorderings per series
R_IID = 2_000         # replicates per cell of the iid baseline
SEED = 20260925
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- estimator (verbatim from ssr_paper_study_v2.py)
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

def ssr(r, w=W, bw=L, gate=GATE):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if r.size < gate or r.size < w: return None
    z = rolling_sharpe(r, w)
    if z.size == 0 or not np.all(np.isfinite(z)): return None
    v = nw_var(z, bw)
    if v <= 0: return None
    return float(z.mean() / math.sqrt(v))

def sharpe_ann(r): r = np.asarray(r, float); return float(r.mean() / r.std(ddof=1) * math.sqrt(12))

def ranks(x):
    order = np.argsort(x, kind="mergesort"); r = np.empty(len(x)); r[order] = np.arange(1, len(x) + 1)
    xs = x[order]; i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]: j += 1
        if j > i: r[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return r

def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(ranks(a[m]), ranks(b[m]))[0, 1])

def rets_from_nav(nav, cutoff=CUTOFF):
    ks = sorted(k for k in nav if k <= cutoff + "T"); v = np.array([float(nav[k]) for k in ks])
    return ks[1:], v[1:] / v[:-1] - 1.0

def window(dates, r, start=None, end=None):
    m = np.array([(start is None or d >= start) and (end is None or d <= end) for d in dates]); return np.asarray(r)[m]

def blend(navA, navB, wa):
    da, ra = rets_from_nav(navA); db, rb = rets_from_nav(navB); ib = {d[:7]: x for d, x in zip(db, rb)}
    dd, rr = [], []
    for d, x in zip(da, ra):
        if d[:7] in ib: dd.append(d); rr.append(wa * x + (1 - wa) * ib[d[:7]])
    return dd, np.array(rr)

# ---------------------------------------------------------------- permutation test
def permutation(r):
    """Real SSR, mean and sd of B reordered SSRs, multiple, one-sided p = (b + 1) / (B + 1)."""
    real = ssr(r)
    if real is None: return None
    sh = np.array([v for v in (ssr(rng.permutation(r)) for _ in range(B)) if v is not None])
    b = int((sh >= real).sum())
    return dict(ssr=real, shuffled_mean=float(sh.mean()), shuffled_sd=float(sh.std(ddof=1)), n_valid=int(sh.size),
                multiple=real / float(sh.mean()), b_ge=b, p=(b + 1) / (sh.size + 1))

log_lines = []
def log(s=""):
    print(s); log_lines.append(s)

t0 = time.time()
RES = {"seed": SEED, "B": B, "R_iid": R_IID, "window": W, "bandwidth": L, "gate": GATE, "cutoff": CUTOFF}

# ---------------------------------------------------------------- Part 1: iid normal baseline
log(f"=== Part 1: mean SSR of iid normal monthly returns ({R_IID} replicates per cell) ===")
iid_sharpe = {}
for S in (0.5, 1.0, 1.5, 2.0):
    s = S / math.sqrt(12)
    v = np.array([x for x in (ssr(rng.normal(s, 1.0, 486)) for _ in range(R_IID)) if x is not None])
    iid_sharpe[S] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), p95=float(np.quantile(v, .95)), ratio=float(v.mean() / S))
    log(f"  Sharpe {S:.1f}, 486 months: mean {v.mean():.3f}  sd {v.std(ddof=1):.3f}  p95 {np.quantile(v, .95):.3f}  mean/Sharpe {v.mean()/S:.3f}")
iid_length = {}
for n in (120, 220, 486, 1274):
    s = 1.0 / math.sqrt(12)
    v = np.array([x for x in (ssr(rng.normal(s, 1.0, n)) for _ in range(R_IID)) if x is not None])
    iid_length[n] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), p95=float(np.quantile(v, .95)))
    log(f"  Sharpe 1.0, {n:>4} months: mean {v.mean():.3f}  sd {v.std(ddof=1):.3f}  p95 {np.quantile(v, .95):.3f}")
RES["iid_by_sharpe_486m"] = {str(k): v for k, v in iid_sharpe.items()}
RES["iid_by_length_sharpe1"] = {str(k): v for k, v in iid_length.items()}
log(f"[part 1: {time.time()-t0:.0f}s]")

# ---------------------------------------------------------------- data (as in ssr_paper_study_v2.py)
meta = {json.loads(l)["variant_id"]: json.loads(l) for l in open(f"{A}/variants_monthly.jsonl")}
navs = {json.loads(l)["variant_id"]: json.loads(l)["nav"] for l in open(f"{A}/variants_monthend.jsonl")}
lb = {e["variant_id"]: e for e in json.load(open(f"{A}/leaderboard.json"))["entries"]}
bench_nav = {json.loads(l)["symbol"]: json.loads(l)["nav"] for l in open(f"{A}/bench_monthend.jsonl")}
supp = {int(row["variant_id"]): row for row in csv.DictReader(open(SUPP))}

series = []
for vid, nav in navs.items():
    m = meta[vid]
    if vid not in lb or m["strategy_slug"] in EXCLUDED_STRATEGIES: continue
    d, r = rets_from_nav(nav)
    if r.size < GATE: continue
    series.append(dict(id=vid, name=f"{m['strategy_slug']}/{m['variant_slug']}", kind="variant", dates=d, r=r))
for sym, label in (("VFINX", "S&P 500 (VFINX)"), ("VBMFX", "US bonds (VBMFX)"), ("GLD", "Gold (GLD)"), ("TLT", "Long Treasuries (TLT)"),
                   ("QQQ", "Nasdaq 100 (QQQ)"), ("VUSTX", "Long Treasuries (VUSTX)")):
    d, r = rets_from_nav(bench_nav[sym]); series.append(dict(id=sym, name=label, kind="benchmark", dates=d, r=r))
d, r = blend(bench_nav["VFINX"], bench_nav["VBMFX"], 0.6); series.append(dict(id="6040", name="60/40 (VFINX/VBMFX)", kind="benchmark", dates=d, r=r))

n_var = sum(1 for s in series if s["kind"] == "variant")
log(f"\n=== Part 2: {n_var} published variants + {len(series) - n_var} benchmarks, B = {B} ===")
if n_var != 173: sys.exit(f"expected 173 primary variants, got {n_var}")

# identity check against the published supplementary table (4 decimals as stored)
worst = 0.0
for s in series:
    if s["kind"] != "variant": continue
    pub = supp[s["id"]]
    covers_2000 = s["dates"][0] <= "2000-01-31"          # same coverage rule as the study
    for key, rr in (("ssr_full", s["r"]), ("ssr_2000", window(s["dates"], s["r"], start="2000-01") if covers_2000 else None)):
        mine = ssr(rr) if rr is not None else None
        if pub[key] in ("", None):
            if mine is not None: sys.exit(f"{s['name']} {key}: published blank, computed {mine}")
            continue
        diff = abs(round(mine, 4) - float(pub[key])); worst = max(worst, diff)
        if diff > 1e-9: sys.exit(f"{s['name']} {key}: computed {mine:.6f} vs published {pub[key]}")
log(f"identity check: all 173 full-history and 2000-window SSRs equal the supplementary table at 4 decimals (max diff {worst:.1e})")

rows = []
for s in series:
    for win, start in (("full", None), ("2000", "2000-01")):
        dates = [x for x in s["dates"] if start is None or x >= start]
        r = window(s["dates"], s["r"], start=start)
        if start and (not s["dates"] or s["dates"][0] > "2000-01-31"): continue   # series must cover the window from its start
        res = permutation(r)
        if res is None: continue
        rows.append(dict(id=s["id"], name=s["name"], kind=s["kind"], window=win, start=dates[0][:7], months=int(r.size),
                         sharpe=sharpe_ann(r), **res))
log(f"[part 2: {time.time()-t0:.0f}s]")

with open(f"{OUT}/permutation_results.csv", "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader()
    for x in rows: wr.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in x.items()})

# ---------------------------------------------------------------- summaries
var = [x for x in rows if x["kind"] == "variant" and x["window"] == "full"]
mult = np.array([x["multiple"] for x in var]); shp = np.array([x["sharpe"] for x in var]); ss = np.array([x["ssr"] for x in var])
shm = np.array([x["shuffled_mean"] for x in var]); pp = np.array([x["p"] for x in var]); mo = np.array([x["months"] for x in var])
q = lambda p: float(np.quantile(mult, p))
# Benjamini-Hochberg at 5 percent (descriptive: the variants are not independent)
order = np.argsort(pp); m = len(pp); passed = 0
for k in range(m, 0, -1):
    if pp[order[k - 1]] <= k * 0.05 / m: passed = k; break
slope = float((shm * shp).sum() / (shp * shp).sum())
RES["catalog"] = dict(
    n=len(var), multiple=dict(min=float(mult.min()), p10=q(.10), q1=q(.25), median=q(.5), q3=q(.75), p90=q(.90), max=float(mult.max())),
    n_ge_1_5=int((mult >= 1.5).sum()), n_ge_2=int((mult >= 2.0).sum()), n_le_1=int((mult <= 1.0).sum()), n_lt_1=int((mult < 1.0).sum()),
    n_p_lt_05=int((pp < 0.05).sum()), n_p_lt_01=int((pp < 0.01).sum()), expected_p_lt_05_if_null=0.05 * len(var), n_bh05=int(passed),
    shuffled_on_sharpe_slope=slope, shuffled_sharpe_pearson=float(np.corrcoef(shm, shp)[0, 1]),
    spearman_multiple_sharpe=spearman(mult, shp), spearman_ssr_sharpe=spearman(ss, shp), spearman_multiple_ssr=spearman(mult, ss),
    spearman_multiple_ssr_over_sharpe=spearman(mult, ss / shp), spearman_nullratio_months=spearman(shm / shp, mo),
    spearman_multiple_months=spearman(mult, mo), spearman_ssr_months=spearman(ss, mo),
    median_shuffled_mean=float(np.median(shm)))
c = RES["catalog"]
log(f"\nvariants: {c['n']}")
log("multiple: min {min:.2f} p10 {p10:.2f} q1 {q1:.2f} median {median:.2f} q3 {q3:.2f} p90 {p90:.2f} max {max:.2f}".format(**c["multiple"]))
log(f">=1.5: {c['n_ge_1_5']}  >=2.0: {c['n_ge_2']}  <=1.0: {c['n_le_1']}  <1.0: {c['n_lt_1']}")
log(f"p<0.05: {c['n_p_lt_05']} (about {c['expected_p_lt_05_if_null']:.1f} expected if every series were order-free and independent)  p<0.01: {c['n_p_lt_01']}  BH 5%: {c['n_bh05']}")
log(f"shuffled mean on Sharpe through the origin: slope {slope:.3f}, Pearson {c['shuffled_sharpe_pearson']:.3f}; median shuffled mean {c['median_shuffled_mean']:.3f}")
log(f"Spearman: multiple~Sharpe {c['spearman_multiple_sharpe']:.2f}  SSR~Sharpe {c['spearman_ssr_sharpe']:.2f}  multiple~SSR {c['spearman_multiple_ssr']:.2f}  "
    f"multiple~SSR/Sharpe {c['spearman_multiple_ssr_over_sharpe']:.2f}")
log(f"Spearman with history length: (shuffled mean / Sharpe) {c['spearman_nullratio_months']:.2f}  multiple {c['spearman_multiple_months']:.2f}  SSR {c['spearman_ssr_months']:.2f}")

def show(title, sel):
    log(f"\n--- {title} ---")
    log(f"{'name':<52} {'win':>4} {'from':>7} {'mo':>5} {'Sharpe':>6} {'SSR':>5} {'shufl':>5} {'mult':>5} {'p':>7}")
    for x in sel:
        log(f"{x['name'][:52]:<52} {x['window']:>4} {x['start']:>7} {x['months']:>5} {x['sharpe']:>6.2f} {x['ssr']:>5.2f} {x['shuffled_mean']:>5.2f} {x['multiple']:>5.2f} {x['p']:>7.4f}")

show("all series, full history, by multiple", sorted([x for x in rows if x["window"] == "full"], key=lambda x: -x["multiple"]))
show("all series, 2000 window, by multiple", sorted([x for x in rows if x["window"] == "2000"], key=lambda x: -x["multiple"]))
full2000 = {x["id"]: x for x in rows if x["window"] == "2000" and x["kind"] == "variant"}
mult2000 = np.array([full2000[x["id"]]["multiple"] for x in var if x["id"] in full2000])
multfull_paired = np.array([x["multiple"] for x in var if x["id"] in full2000])
RES["catalog_2000"] = dict(n=int(mult2000.size), median=float(np.median(mult2000)),
                           spearman_with_full=spearman(multfull_paired, mult2000),
                           n_p_lt_05=int(sum(1 for x in full2000.values() if x["p"] < 0.05)))
log(f"\n2000 window: {mult2000.size} variants, median multiple {np.median(mult2000):.2f}, Spearman with full-history multiple {RES['catalog_2000']['spearman_with_full']:.2f}, p<0.05: {RES['catalog_2000']['n_p_lt_05']}")
RES["series"] = rows
json.dump(RES, open(f"{OUT}/permutation_results.json", "w"), indent=1, default=float)
open(f"{OUT}/permutation_run.log", "w").write("\n".join(log_lines) + "\n")
log(f"\n[done in {time.time()-t0:.0f}s]")
