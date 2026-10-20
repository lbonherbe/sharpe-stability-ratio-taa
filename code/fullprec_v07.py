"""Full-precision values for every per-series number the v0.7 paper prints, for one column.

Usage: fullprec_v07.py main|excess. Runs the study in-process on the same inputs (output to a scratch folder),
asserts byte identity with results/<col>/results.json and published_variants.csv, and writes
results/<col>/fullprec_tables.json: table rows rounded ONCE from full precision (decimal ROUND_HALF_UP), plus a
per-series dump of the 173 eligible variants (results/<col>/fullprec_series.json) for text queries.
"""
import json, math, os, sys, tempfile
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(HERE)
col = sys.argv[1]; assert col in ("main", "excess")
os.environ["SSR_DATA_DIR"] = f"{V}/inputs" if col == "main" else f"{V}/inputs_C"
if col == "excess": os.environ["SSR_EXCESS"] = "1"
else: os.environ.pop("SSR_EXCESS", None)
os.environ["SSR_OUT_DIR"] = tempfile.mkdtemp(prefix="ssr_fullprec_")
src = open(f"{HERE}/ssr_study_v07.py").read()
ns = {"__file__": f"{HERE}/ssr_study_v07.py", "__name__": "study"}
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "ssr_study_v07.py", "exec"), ns)
series, benchmarks, el = ns["series"], ns["benchmarks"], ns["el"]
for f in ("results.json", "published_variants.csv", "benchmarks.csv"):
    assert open(f"{os.environ['SSR_OUT_DIR']}/{f}").read() == open(f"{V}/results/{col}/{f}").read(), f"in-process run differs: {f}"

def r(v, k=2):
    if v is None: return None
    return str(Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-k), rounding=ROUND_HALF_UP))

by_name = {s["name"]: s for s in series.values()}
ranked = sorted(el, key=lambda s: -s["ssr_full"])
out = {"top_bottom": [], "selected": [], "benchmarks": [], "named_parts": {}}
for i, s in enumerate(ranked):
    if i < 12 or i >= len(ranked) - 13:
        b = s["boot"]["b36"]
        out["top_bottom"].append(dict(rank=i + 1, id=s["id"], name=s["name"], start=s["start"][:4], sharpe=r(s["sharpe_full"]), dsr=r(s["dsr"], 3),
                                      ssr=r(s["ssr_full"]), ssr4=r(s["ssr_full"], 4), pct=[r(b["pct_lo95"]), r(b["pct_hi95"])], turnover=r(s["turnover"], 1),
                                      stype=s["stype"], freq=s["freq"]))
SELECTED = ["haa/haa-standard", "baa/baa-g12", "daa/daa-g12", "paa/paa-high", "laa/laa-standard", "vitral-multi-asset-momentum/vitral-mam-standard",
            "momentum-correlation-triplet/mom-corr-triplet-standard", "gtaa/gtaa-5", "adm/adm-standard", "gem/gem-standard", "sma-trend/sma-trend-spy",
            "century-momentum/century-momentum-standard", "golden-butterfly/golden-butterfly-base", "all-weather-dalio/all-weather-dalio-base",
            "classic-60-40/classic-60-40-base", "buy-the-dip/buy-the-dip-standard"]
for n in SELECTED:
    s = by_name[n]
    out["selected"].append(dict(name=n, rank=1 + [x["name"] for x in ranked].index(n), start=s["start"][:4], sharpe=r(s["sharpe_full"]), dsr=r(s["dsr"], 3),
                                ssr=r(s["ssr_full"]), ssr_2000=r(s["ssr_2000"]), ssr_2008=r(s["ssr_2008"]), q_le05=r(s["boot"]["b36"]["q_le05"])))
for b in benchmarks.values():
    out["benchmarks"].append(dict(name=b["name"], start=b["start"][:4], months=b["months"], sharpe=r(b["sharpe_full"]), ssr=r(b["ssr_full"]), ssr_2000=r(b["ssr_2000"]),
                                  ssr_2008=r(b["ssr_2008"]), **{f"sub_{k}": r(b[f"sub_{k}"]) for k in ("pre2000", "2000s", "2010s", "2020s")}, sub_2000s_n=b["sub_2000s_n"]))
for n in ("haa/haa-standard", "momentum-correlation-triplet/mom-corr-triplet-standard", "gem/gem-standard"):
    s = by_name[n]; p = s["parts"]; b = s["boot"]["b36"]
    out["named_parts"][n] = dict(n_windows=p["n_windows"], min_z_ann=r(p["min_z_ann"]), mean_z_ann=r(p["mean_z"] * math.sqrt(12)), mean_z=r(p["mean_z"], 3),
                                 naive_sd=r(p["naive_sd"], 3), hac_sd=r(p["hac_sd"], 3), hac_over_naive=r(p["hac_sd"] / p["naive_sd"], 1), neg_share=p["neg_share"],
                                 neg_count=round(p["neg_share"] * p["n_windows"]), bootmean=r(b["mean"]), pct=[r(b["pct_lo95"]), r(b["pct_hi95"])],
                                 basic=[r(b["basic_lo95"]), r(b["basic_hi95"])], ssr=r(s["ssr_full"]), ssr_2000=r(s["ssr_2000"]), sharpe=r(s["sharpe_full"]),
                                 rolling_start=s["dates"][35][:7], months=s["months"])
fam = {}
for s in el: fam.setdefault(s["strategy"], []).append(s["ssr_full"])
out["family_ranges"] = {k: [r(min(v)), r(max(v)), len(v)] for k, v in fam.items()}
out["rank_of"] = {n: 1 + [x["name"] for x in ranked].index(n) for n in ("classic-60-40/classic-60-40-base", "paired-switching/paired-switching-spy-tlt", "uis/uis-standard", "haa/haa-standard", "us-market-benchmark/us-market-100", "simple-path-100/simple-path-100") if n in by_name}
json.dump(out, open(f"{V}/results/{col}/fullprec_tables.json", "w"), indent=1)
def clean(x):
    if isinstance(x, dict): return {k: clean(v) for k, v in x.items() if k not in ("r", "dates", "z")}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x] if len(x) < 50 else None
    if hasattr(x, "tolist"): return None
    return x
json.dump([clean(s) for s in ranked], open(f"{V}/results/{col}/fullprec_series.json", "w"), indent=1, default=str)
print("ok", col, len(ranked))
