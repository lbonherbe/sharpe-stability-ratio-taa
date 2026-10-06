"""Deflated Sharpe Ratio at K = 219 for version 0.5 (paper Section 3.3).

The platform's published scores count every variant with a stored backtest as a trial (238 on 28 September 2026).
The paper keeps its own trial set, the 219 variants active on 5 September 2026. This script
1. reproduces every live published score with the platform's own compute_catalog_dsr on the full universe (it stops
   unless all agree at six decimals), which shows the stored moments and history lengths are the ones used; and
2. applies the same function to the paper's 219 variants and writes the study's leaderboard input: the live payload
   restricted to the 177 variant ids published on 5 September 2026, with deflated_sharpe set to the K = 219 value
   (the live value kept as deflated_sharpe_live) and dsr_meta describing both.

Needs the private backend (BF_BACKEND_DIR, app/services/dsr_service.py) and private inputs in SSR_RAW_DIR:
dsr_universe_raw.txt (latest backtest run per variant: variant_id, sharpe_ann, n_obs = total_months, monthly
moments), leaderboard_live_full_usd.json (public endpoint, full period, USD), leaderboard_20260905.json (the
5 September payload, for the published id set) and variants_monthly_20260905.jsonl (the 219 trial ids).
Writes $SSR_DATA_DIR/leaderboard.json.
"""
import json, os, sys

sys.path.insert(0, os.environ["BF_BACKEND_DIR"])
from app.services.dsr_service import compute_catalog_dsr  # noqa: E402

RAW = os.environ["SSR_RAW_DIR"]; OUT = os.environ["SSR_DATA_DIR"]
universe = [json.loads(l) for l in open(f"{RAW}/dsr_universe_raw.txt") if l.startswith("{")]
live = json.load(open(f"{RAW}/leaderboard_live_full_usd.json"))
paper_published = [e["variant_id"] for e in json.load(open(f"{RAW}/leaderboard_20260905.json"))["entries"]]
ids219 = [json.loads(l)["variant_id"] for l in open(f"{RAW}/variants_monthly_20260905.jsonl")]

def records(rows):
    return [{"variant_id": r["variant_id"], "sharpe_ann": r["sharpe_ann"], "n_obs": int(r["n_obs"]) if r["n_obs"] is not None else None,
             "monthly_sharpe": r["monthly_sharpe"], "monthly_skew": r["monthly_skew"], "monthly_kurtosis": r["monthly_kurtosis"]} for r in rows]

full = compute_catalog_dsr(records(universe))
live_by = {e["variant_id"]: e for e in live["entries"]}
d = max(abs(full["by_variant_id"][v]["deflated_sharpe"] - e["deflated_sharpe"]) for v, e in live_by.items())
assert d < 5e-7, f"live scores not reproduced (max diff {d})"
print(f"reproduced {len(live_by)} live published scores exactly; live K = {live['dsr_meta']['n_trials']}")
by_id = {r["variant_id"]: r for r in universe}
k219 = compute_catalog_dsr(records([by_id[v] for v in ids219]))
assert k219["meta"]["n_trials"] == 219
print(f"K = 219: benchmark {k219['meta']['benchmark_annualized_sharpe']} annualised")
entries = []
for v in paper_published:
    e = dict(live_by[v])
    e["deflated_sharpe_live"], e["dsr_fragile_live"] = e["deflated_sharpe"], e.get("dsr_fragile")
    e["deflated_sharpe"], e["dsr_fragile"] = k219["by_variant_id"][v]["deflated_sharpe"], k219["by_variant_id"][v]["is_fragile"]
    entries.append(e)
payload = {k: v for k, v in live.items() if k != "entries"}
payload.update(total=len(entries), dsr_meta_live=live["dsr_meta"],
               dsr_meta=dict(k219["meta"], universe="the 219 variants active on 2026-09-05 (the paper's trial set), restated moments of 2026-09-28"),
               entries=entries)
json.dump(payload, open(f"{OUT}/leaderboard.json", "w"), indent=1)
print(f"wrote {OUT}/leaderboard.json ({len(entries)} entries)")
