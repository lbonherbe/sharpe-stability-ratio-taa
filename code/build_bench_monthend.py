"""Benchmark month-ends for version 0.5: the 5 September 2026 benchmark extract with the platform's
28 September 2026 total-return corrections applied to VFINX, VBMFX and VUSTX (paper Sections 3.2 and Appendix A).

- VBMFX and VUSTX: the daily adjusted-close series with the platform's price-correction registry applied
  (apply_return_corrections, which restores the distributions missing from the provider's records before 1990),
  sampled at the extract's month-end dates;
- VFINX: the S&P 500 daily total-return series for 1976-08-31 to 1987-01-05, spliced onto VFINX at 1987-01-06 as
  the platform's price builder does, sampled at the extract's month-end dates;
- every other symbol (GLD, TLT, QQQ, ...): the 5 September extract unchanged (no correction applies to them).
The corrected series' monthly returns must equal the extract's from February 1987 (VFINX) and January 1990
(VBMFX, VUSTX) on; the script stops otherwise.

Needs the private backend (BF_BACKEND_DIR, for app/backtest/price_corrections.py and the S&P 500 daily file) and
private data: SSR_BENCH_SOURCE (the 5 September benchmark extract), SSR_PRICE_CACHE (a pickled DataFrame of daily
adjusted closes by symbol). Writes $SSR_DATA_DIR/bench_monthend.jsonl.
"""
import importlib.util, json, os, sys
import numpy as np
import pandas as pd

BACKEND = os.environ["BF_BACKEND_DIR"]; SOURCE = os.environ["SSR_BENCH_SOURCE"]
CACHE = os.environ["SSR_PRICE_CACHE"]; OUT = os.environ["SSR_DATA_DIR"]

spec = importlib.util.spec_from_file_location("price_corrections", f"{BACKEND}/app/backtest/price_corrections.py")
pc = importlib.util.module_from_spec(spec); sys.modules["price_corrections"] = pc; spec.loader.exec_module(pc)
old = {json.loads(l)["symbol"]: json.loads(l) for l in open(SOURCE)}
raw = pd.read_pickle(CACHE)

def month_end_nav(s, keys):
    out = {}
    for k in keys:
        v = s.loc[:pd.Timestamp(k[:10])]
        if len(v): out[k] = float(v.iloc[-1])
    return out

def corrected(sym):
    keys = sorted(old[sym]["nav"])
    s = pc.apply_return_corrections(sym, raw[sym].dropna())
    if sym == "VFINX":
        tier = pd.read_csv(f"{BACKEND}/app/backtest/data/sp500_tr_daily.csv", parse_dates=["date"]).set_index("date")["nav"]
        v = raw["VFINX"].dropna(); cut = pd.Timestamp("1987-01-06")
        tier = tier[tier.index < cut] * (v.loc[cut] / tier.iloc[-1])
        s = pd.concat([tier, v[v.index >= cut]])
    return month_end_nav(s, keys)

def rets(nav):
    ks = sorted(nav); v = np.array([nav[k] for k in ks]); return dict(zip(ks[1:], v[1:] / v[:-1] - 1))

fixed = {s: corrected(s) for s in ("VFINX", "VBMFX", "VUSTX")}
for sym, frm in (("VFINX", "1987-02"), ("VBMFX", "1990-01"), ("VUSTX", "1990-01")):
    assert sorted(fixed[sym]) == sorted(old[sym]["nav"]), f"{sym}: month-end dates differ"
    ro, rn = rets(old[sym]["nav"]), rets(fixed[sym])
    changed = [k for k in ro if abs(ro[k] - rn[k]) > 1e-9]
    assert all(k < frm for k in changed), f"{sym}: returns from {frm} on moved"
    print(f"{sym}: {len(changed)} monthly returns changed, {changed[0]} to {changed[-1]}; returns from {frm} on unchanged")
with open(f"{OUT}/bench_monthend.jsonl", "w") as f:
    for sym, rec in old.items():
        f.write(json.dumps({"symbol": sym, "nav": fixed.get(sym, rec["nav"])}) + "\n")
print(f"wrote {OUT}/bench_monthend.jsonl")
