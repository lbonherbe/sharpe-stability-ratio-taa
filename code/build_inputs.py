"""Inputs for the v0.7 impact study (2026-10-17), read-only, offline after the pulls in ../raw/.

Two input folders, both on the same sample definition as v05_restated (219 active ids of 5 September
2026, the 177 published ids of the old leaderboard, ggcem excluded later by the study, cutoff applied
by the study):

- inputs_B: today's restated data (latest backtest_runs row per id, all created 2026-10-17), SSR(0).
  * variants_monthend.jsonl: last daily_nav observation of every calendar month (raw/monthend_raw.txt);
  * variants_monthly.jsonl: the 14 fields of the v05 extract, from the same latest run (raw/meta_raw.txt);
  * leaderboard.json: the live public leaderboard (full, USD, cache built 2026-10-17 13:35 UTC)
    restricted to the 177 paper ids; deflated_sharpe recomputed with the platform's compute_catalog_dsr
    at K = 219 from the stored (v1, raw-return) moments of the latest runs;
  * bench_monthend.jsonl: copied from v05_restated (observed fund prices, not backtests; see IMPACT.md).
- inputs_C: as inputs_B, but deflated_sharpe recomputed at K = 219 from the stored excess-cash-v2
  shadow moments (metrics.ratios_excess_v2: moments of r - c over the same month-end dates), plus
  cash_usd.csv (prod cash_benchmark_levels, USD, daily) that the study subtracts.
"""
import json, os, sys, shutil
from collections import Counter

sys.path.insert(0, os.path.expanduser("~/Code/bestfolio/backend"))
from app.services.dsr_service import compute_catalog_dsr  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(HERE); A = os.path.dirname(V)
OLD = f"{A}/v05_restated/inputs"
log_lines = []
def log(s=""):
    print(s); log_lines.append(s)

ids219 = [int(x) for x in open(f"{A}/v05_restated/raw/ids219.txt").read().strip().split(",")]
paper_published = [e["variant_id"] for e in json.load(open(f"{OLD}/leaderboard.json"))["entries"]]
assert len(ids219) == 219 and len(paper_published) == 177

monthend = [json.loads(l) for l in open(f"{V}/raw/monthend_raw.txt") if l.startswith("{")]
meta = [json.loads(l) for l in open(f"{V}/raw/meta_raw.txt") if l.startswith("{")]
universe = [json.loads(l) for l in open(f"{V}/raw/dsr_universe_raw.txt") if l.startswith("{")]
live = json.load(open(f"{V}/raw/leaderboard_live_full_usd.json"))
assert sorted(r["variant_id"] for r in monthend) == sorted(ids219)
assert sorted(r["variant_id"] for r in meta) == sorted(ids219)
log(f"latest runs: created {dict(Counter(r['_created_at'][:10] for r in meta))}, methodology {dict(Counter(r['_methodology_version'] for r in meta))}, "
    f"code {dict(Counter(r['_code_sha'][:8] for r in meta))}, rr_def {dict(Counter(r['rr_def'] for r in meta))}")
log(f"live leaderboard: {live['total']} entries, cache {live['cache_meta']}, dsr_meta n_trials {live['dsr_meta']['n_trials']}")

# check: month-end NAV at 2026-08-31 equals the run's daily_nav on that day
bad = [r["variant_id"] for r, m in zip(sorted(monthend, key=lambda r: r["variant_id"]), sorted(meta, key=lambda r: r["variant_id"]))
       if m["_nav_20260831"] is not None and abs(float(r["nav"].get("2026-08-31", "nan")) - float(m["_nav_20260831"])) > 1e-9]
log(f"NAV 2026-08-31 equals daily_nav for all ids holding that date: {not bad} {bad[:5]}")

# ---- step 1: reproduce the live published DSR (the cache predates variants 300-313, first run 13:09-13:12)
def records(rows, v2=False):
    out = []
    for r in rows:
        src = (r["v2"] or {}) if v2 else r
        out.append({"variant_id": r["variant_id"], "sharpe_ann": (src.get("sharpe_ratio") if v2 else r["sharpe_ann"]),
                    "n_obs": int(src["total_months"] if v2 else r["n_obs"]) if (src.get("total_months") if v2 else r["n_obs"]) is not None else None,
                    "monthly_sharpe": src.get("monthly_sharpe"), "monthly_skew": src.get("monthly_skew"), "monthly_kurtosis": src.get("monthly_kurtosis")})
    return out
uni272 = [r for r in universe if not (300 <= r["variant_id"] <= 313)]
full = compute_catalog_dsr(records(uni272))
live_by = {e["variant_id"]: e for e in live["entries"]}
d = [abs(full["by_variant_id"][v]["deflated_sharpe"] - e["deflated_sharpe"]) for v, e in live_by.items() if v in full["by_variant_id"]]
log(f"live DSR reproduction (universe {len(uni272)} = all stored runs less 300-313): meta {full['meta']['n_trials']} trials, "
    f"benchmark {full['meta']['benchmark_annualized_sharpe']} vs live {live['dsr_meta']['benchmark_annualized_sharpe']}; "
    f"{len(d)} published scores, max |diff| {max(d):.2e}")

# ---- step 2: K = 219 under v1 (B) and v2 (C)
by_id = {r["variant_id"]: r for r in universe}
k219_v1 = compute_catalog_dsr(records([by_id[v] for v in ids219]))
k219_v2 = compute_catalog_dsr(records([by_id[v] for v in ids219], v2=True))
assert k219_v1["meta"]["n_trials"] == 219 and k219_v2["meta"]["n_trials"] == 219
log(f"K=219 v1 meta: {k219_v1['meta']}")
log(f"K=219 v2 meta: {k219_v2['meta']}")

missing = [v for v in paper_published if v not in live_by]
log(f"paper ids missing from the live board: {missing}")
old_lb = {e["variant_id"]: e for e in json.load(open(f"{OLD}/leaderboard.json"))["entries"]}

def write(folder, dsr, label):
    os.makedirs(folder, exist_ok=True)
    with open(f"{folder}/variants_monthend.jsonl", "w") as f:
        for r in sorted(monthend, key=lambda r: r["variant_id"]): f.write(json.dumps(r) + "\n")
    keys = ["variant_id", "variant_slug", "strategy_slug", "v_active", "s_active", "start_date", "end_date", "sharpe_ratio",
            "monthly_sharpe", "monthly_skew", "monthly_kurtosis", "rr_def"]
    with open(f"{folder}/variants_monthly.jsonl", "w") as f:
        for r in sorted(meta, key=lambda r: r["variant_id"]):
            f.write(json.dumps({**{k: r[k] for k in keys}, "n_obs": None, "monthly_nav": None}) + "\n")
    entries = []
    for v in paper_published:
        e = dict(live_by[v]) if v in live_by else dict(old_lb[v], _note="missing from live board; old entry kept")
        e["deflated_sharpe_live"] = e.get("deflated_sharpe")
        e["deflated_sharpe"] = dsr["by_variant_id"][v]["deflated_sharpe"]
        e["dsr_fragile"] = dsr["by_variant_id"][v]["is_fragile"]
        entries.append(e)
    payload = {k: v for k, v in live.items() if k != "entries"}
    payload.update(total=len(entries), dsr_meta_live=live["dsr_meta"], dsr_meta=dict(dsr["meta"], universe=f"the 219 paper trial ids, {label}"), entries=entries)
    json.dump(payload, open(f"{folder}/leaderboard.json", "w"), indent=1)
    shutil.copy(f"{OLD}/bench_monthend.jsonl", f"{folder}/bench_monthend.jsonl")

write(f"{V}/inputs_B", k219_v1, "stored v1 moments of the 2026-10-17 runs")
write(f"{V}/inputs_C", k219_v2, "stored excess-cash-v2 moments of the 2026-10-17 runs")
shutil.copy(f"{V}/raw/cash_usd_raw.txt", f"{V}/inputs_C/cash_usd.csv")

# structural changes vs v05
oldm = {json.loads(l)["variant_id"]: json.loads(l) for l in open(f"{OLD}/variants_monthly.jsonl")}
moved = [(r["variant_id"], r["strategy_slug"] + "/" + r["variant_slug"], oldm[r["variant_id"]]["start_date"], r["start_date"])
         for r in meta if r["start_date"][:7] != oldm[r["variant_id"]]["start_date"][:7]]
log(f"start month changed for {len(moved)} of 219 ids (published: {sum(1 for x in moved if x[0] in paper_published)}):")
for x in sorted(moved): log(f"  {x[0]:>4} {x[1]:<60} {x[2]} -> {x[3]}{'  (published)' if x[0] in paper_published else ''}")
open(f"{V}/raw/build_inputs.log", "w").write("\n".join(log_lines) + "\n")
