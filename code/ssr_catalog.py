import json, math, statistics as st, csv, sys
from statistics import NormalDist
import os
sys.path.insert(0, os.environ.get("BF_BACKEND_DIR", ""))  # private backend: app.deflated_sharpe for the expected-maximum benchmark
from app.deflated_sharpe import expected_max_sharpe  # same benchmark math as prod
SP = os.environ.get("SSR_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
N = NormalDist()
W = 36

def rets(nav):
    ks = sorted(nav); v = [float(nav[k]) for k in ks]
    return ks[1:], [v[i]/v[i-1]-1 for i in range(1, len(v))]
def sharpe(r):
    if len(r) < 2: return None
    sd = st.stdev(r); return None if sd == 0 else st.mean(r)/sd
def acf1(r):
    m = st.mean(r); d = [x-m for x in r]; den = sum(x*x for x in d)
    return sum(d[i]*d[i-1] for i in range(1, len(d)))/den if den else float('nan')
def nw_var(z, L):
    n = len(z); m = st.mean(z); d = [x-m for x in z]
    g = lambda k: sum(d[i]*d[i-k] for i in range(k, n))/n
    return g(0) + sum(2*(1-k/(L+1))*g(k) for k in range(1, L+1))
def ssr(r, w=W, sr0=0.0):
    z = [sharpe(r[i:i+w]) for i in range(len(r)-w+1)]
    z = [x for x in z if x is not None]; n = len(z)
    if n < 24: return None
    mu = st.mean(z)
    v_over = nw_var(z, w-1); Lnw = int(4*(n/100)**(2/9)); v_nw = nw_var(z, Lnw)
    return {"n_win": n, "mu_roll_ann": mu*math.sqrt(12), "min_roll_ann": min(z)*math.sqrt(12),
            "pct_neg": 100*sum(1 for x in z if x < 0)/n,
            "ssr": (mu-sr0)/math.sqrt(v_over) if v_over > 0 else None,
            "ssr_nw": (mu-sr0)/math.sqrt(v_nw) if v_nw > 0 else None}
def window(dates, r, start):
    return [x for d, x in zip(dates, r) if d >= start]
def spearman(a, b):
    def ranks(x):
        s = sorted(range(len(x)), key=lambda i: x[i]); rk = [0]*len(x)
        i = 0
        while i < len(s):
            j = i
            while j+1 < len(s) and x[s[j+1]] == x[s[i]]: j += 1
            for k in range(i, j+1): rk[s[k]] = (i+j)/2+1
            i = j+1
        return rk
    ra, rb = ranks(a), ranks(b); ma, mb = st.mean(ra), st.mean(rb)
    num = sum((x-ma)*(y-mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb))
    return num/den if den else float('nan')
def psr_z(sr, n, skew, kurt, bench, rho=0.0):
    B = rho/(1-rho); C = rho**2/(1-rho**2); a = 1+2*B; b = 1+B+C; c = 1+2*C
    V = a - b*skew*sr + c*(kurt-1)/4*sr**2
    if V <= 0: return None
    return (sr-bench)*math.sqrt(n-1)/math.sqrt(V)

meta = {json.loads(l)["variant_id"]: json.loads(l) for l in open(f"{SP}/variants_monthly.jsonl")}
navs = {json.loads(l)["variant_id"]: json.loads(l)["nav"] for l in open(f"{SP}/variants_monthend.jsonl")}
lb = {e["variant_id"]: e for e in json.load(open(f"{SP}/leaderboard.json"))["entries"]}
dsr_meta = json.load(open(f"{SP}/leaderboard.json"))["dsr_meta"]
bench = {json.loads(l)["symbol"]: json.loads(l)["nav"] for l in open(f"{SP}/bench_monthend.jsonl")}

# --- benchmarks: S&P 500 (VFINX), 60/40 monthly-rebalanced VFINX/VBMFX, SPY, QQQ, GLD, TLT
def blend(navA, navB, wa):
    da, ra = rets(navA); db, rb = rets(navB); ib = dict(zip([d[:7] for d in db], rb))
    dates, r = [], []
    for d, x in zip(da, ra):
        if d[:7] in ib: dates.append(d); r.append(wa*x + (1-wa)*ib[d[:7]])
    return dates, r
series = {}
for vid, nav in navs.items():
    m = meta[vid]; d, r = rets(nav)
    series[("variant", vid)] = dict(name=f"{m['strategy_slug']}/{m['variant_slug']}", dates=d, r=r, published=vid in lb, m=m)
for sym, label in (("VFINX", "S&P 500 (VFINX)"), ("SPY", "SPY"), ("QQQ", "QQQ"), ("GLD", "GLD"), ("TLT", "TLT"), ("VBMFX", "US bonds (VBMFX)")):
    d, r = rets(bench[sym]); series[("bench", sym)] = dict(name=label, dates=d, r=r, published=False, m={})
d, r = blend(bench["VFINX"], bench["VBMFX"], 0.6); series[("bench", "6040")] = dict(name="60/40 (VFINX/VBMFX)", dates=d, r=r, published=False, m={})

# --- sanity: my monthly Sharpe vs engine's stored monthly_sharpe
diffs = []
for (kind, vid), s in series.items():
    if kind != "variant" or not s["m"].get("monthly_sharpe"): continue
    mine = sharpe(s["r"]); diffs.append(abs(mine - float(s["m"]["monthly_sharpe"])))
print(f"SANITY monthly Sharpe vs engine: n={len(diffs)} median|diff|={st.median(diffs):.4f} max={max(diffs):.4f}")

# --- SSR full history + common windows
rows = []
for key, s in series.items():
    r, d = s["r"], s["dates"]
    full = ssr(r); s2000 = ssr(window(d, r, "2000-01")) if d[0] <= "2000-01-31" else None
    s2008 = ssr(window(d, r, "2008-01")) if d[0] <= "2008-01-31" else None
    row = dict(kind=key[0], id=key[1], name=s["name"], published=s["published"], start=d[0][:7], months=len(r),
               sharpe_ann=sharpe(r)*math.sqrt(12), rho1=acf1(r),
               dsr=lb.get(key[1], {}).get("deflated_sharpe") if key[0] == "variant" else None,
               ssr_full=full["ssr"] if full else None, ssr_nw_full=full["ssr_nw"] if full else None,
               min_roll_full=full["min_roll_ann"] if full else None, pct_neg_full=full["pct_neg"] if full else None,
               ssr_2000=s2000["ssr"] if s2000 else None, ssr_2008=s2008["ssr"] if s2008 else None,
               sharpe_2000=(sharpe(window(d, r, "2000-01")) or 0)*math.sqrt(12) if s2000 else None)
    rows.append(row)
with open(f"{SP}/ssr_catalog.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

pub = [x for x in rows if x["kind"] == "variant" and x["published"] and x["ssr_full"] is not None]
print(f"\nPUBLISHED variants with SSR: {len(pub)} of {len(lb)}; start-date distribution:",
      {k: sum(1 for x in pub if x['start'] < k) for k in ('1980','1990','2000','2008')})
vals = sorted(x["ssr_full"] for x in pub)
q = lambda p: vals[int(p*(len(vals)-1))]
print(f"SSR(0,w=36,L=35) full history, published: min {vals[0]:.2f} p10 {q(.1):.2f} p25 {q(.25):.2f} median {q(.5):.2f} p75 {q(.75):.2f} p90 {q(.9):.2f} max {vals[-1]:.2f}; distinct at 2dp: {len(set(round(v,2) for v in vals))}")
print(f"Spearman SSR_full vs Sharpe_full: {spearman([x['ssr_full'] for x in pub],[x['sharpe_ann'] for x in pub]):.2f}")
print(f"Spearman SSR_full vs DSR (Robustness): {spearman([x['ssr_full'] for x in pub],[x['dsr'] for x in pub]):.2f}")
print(f"Spearman SSR_full vs SSR_nw(auto-lag): {spearman([x['ssr_full'] for x in pub],[x['ssr_nw_full'] for x in pub]):.2f}")
p2000 = [x for x in pub if x["ssr_2000"] is not None]
print(f"Common window since 2000-01: {len(p2000)} published variants; Spearman SSR_2000 vs Sharpe_2000: {spearman([x['ssr_2000'] for x in p2000],[x['sharpe_2000'] for x in p2000]):.2f}; Spearman SSR_full vs SSR_2000: {spearman([x['ssr_full'] for x in p2000],[x['ssr_2000'] for x in p2000]):.2f}")

def show(title, xs, key="ssr_full"):
    print(f"\n{title}")
    print(f"{'name':<52} {'from':>7} {'Sharpe':>6} {'DSR':>6} {'SSRfull':>7} {'SSR2000':>7} {'SSR2008':>7} {'minRoll':>7} {'%neg':>5} {'rho1':>5}")
    for x in xs:
        f = lambda v, p=2: "" if v is None else f"{v:.{p}f}"
        print(f"{x['name'][:52]:<52} {x['start']:>7} {f(x['sharpe_ann']):>6} {f(x['dsr'],3):>6} {f(x['ssr_full']):>7} {f(x['ssr_2000']):>7} {f(x['ssr_2008']):>7} {f(x['min_roll_full']):>7} {f(x['pct_neg_full'],0):>5} {f(x['rho1']):>5}")
pub_sorted = sorted(pub, key=lambda x: -x["ssr_full"])
show("TOP 12 published by SSR (full history)", pub_sorted[:12])
show("BOTTOM 12 published by SSR (full history)", pub_sorted[-12:])
show("BENCHMARKS", [x for x in rows if x["kind"] == "bench"])
picks = ["haa/haa-standard","gem/gem-standard","baa/baa-g12","daa/daa-g12","gtaa/gtaa-5","classic-60-40/classic-60-40-base","golden-butterfly/golden-butterfly-base","buy-the-dip/buy-the-dip-standard","letf-upro-zroz-gld/letf-upro-zroz-gld-base","momentum-correlation-triplet/mom-corr-triplet-standard","golden-ratio-dual-gate/golden-ratio-dual-gate-standard","adm/adm-standard","paa/paa-high","laa/laa-standard","vitral-multi-asset-momentum/vitral-mam-standard"]
show("SELECTED well-known strategies", [x for x in rows if x["name"] in picks])
# where do benchmarks rank among published on the 2000+ window?
b2000 = {x["name"]: x["ssr_2000"] for x in rows if x["kind"] == "bench" and x["ssr_2000"] is not None}
for bname, bv in b2000.items():
    above = sum(1 for x in p2000 if x["ssr_2000"] > bv)
    print(f"since 2000: {bname} SSR {bv:.2f} -> {above} of {len(p2000)} published variants score higher")

# --- AR(1)-adjusted DSR (Lopez de Prado, Lipton, Zoonekynd variance as implemented in jsharpe)
trials = []
for (kind, vid), s in series.items():
    if kind != "variant": continue
    m = s["m"]
    if not m.get("monthly_sharpe"): continue
    trials.append(dict(vid=vid, name=s["name"], sr=float(m["monthly_sharpe"]), skew=float(m["monthly_skew"]), kurt=float(m["monthly_kurtosis"]), n=len(s["r"]), rho=acf1(s["r"]), published=s["published"]))
var_x = st.pvariance([t["sr"] for t in trials]); benchmark = expected_max_sharpe(var_x, len(trials))
print(f"\nDSR reproduction: n_trials mine {len(trials)} vs prod {dsr_meta['n_trials']}; benchmark monthly mine {benchmark:.6f} vs prod {dsr_meta['benchmark_monthly_sharpe']}")
rep, chg, flips = [], [], []
for t in trials:
    z0 = psr_z(t["sr"], t["n"], t["skew"], t["kurt"], benchmark); z1 = psr_z(t["sr"], t["n"], t["skew"], t["kurt"], benchmark, t["rho"])
    if z0 is None or z1 is None: continue
    d0, d1 = N.cdf(z0), N.cdf(z1); t["dsr0"], t["dsr1"] = d0, d1
    if t["published"] and lb.get(t["vid"]): rep.append(abs(d0 - lb[t["vid"]]["deflated_sharpe"]))
    chg.append(d1 - d0)
    if (d0 >= 0.9) != (d1 >= 0.9): flips.append(t)
rhos = sorted(t["rho"] for t in trials)
print(f"rho1 across {len(trials)} trials: min {rhos[0]:.2f} p10 {rhos[len(rhos)//10]:.2f} median {rhos[len(rhos)//2]:.2f} p90 {rhos[9*len(rhos)//10]:.2f} max {rhos[-1]:.2f}; share |rho1|>0.10: {100*sum(1 for x in rhos if abs(x)>0.10)/len(rhos):.0f}%")
print(f"DSR reproduction vs leaderboard (published): median|diff| {st.median(rep):.4f} max {max(rep):.4f}")
print(f"AR(1)-adjusted DSR minus current: median {st.median(chg):+.4f}, most negative {min(chg):+.4f}, most positive {max(chg):+.4f}; fragile-flag flips at 0.90: {len(flips)}")
for t in sorted(flips, key=lambda t: t["dsr0"]): print(f"   flip: {t['name'][:50]:<50} rho1 {t['rho']:+.2f} DSR {t['dsr0']:.3f} -> {t['dsr1']:.3f} {'(published)' if t['published'] else '(unreleased)'}")
big = sorted(trials, key=lambda t: t.get("dsr1", 0) - t.get("dsr0", 0))[:6]
for t in big: print(f"   largest drop: {t['name'][:50]:<50} rho1 {t['rho']:+.2f} DSR {t['dsr0']:.3f} -> {t['dsr1']:.3f} n={t['n']}")
