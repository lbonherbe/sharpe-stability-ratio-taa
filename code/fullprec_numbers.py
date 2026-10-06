"""Full-precision values for every per-series table cell of the paper (version 0.5).

Runs the study script in-process (same inputs, same seed, output to a scratch folder) and reads the in-memory
series, so table cells are rounded ONCE from full precision with decimal ROUND_HALF_UP, never from the
4-decimal CSV, which would round twice. Writes ../results/fullprec_tables.json and prints the tables.
"""
import json, math, os, sys, tempfile, csv
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(HERE)
os.environ.setdefault("SSR_DATA_DIR", f"{V}/data")  # the month-end extracts (not redistributed, see data/README.md)
os.environ["SSR_OUT_DIR"] = tempfile.mkdtemp(prefix="ssr_fullprec_")
src = open(f"{HERE}/ssr_paper_study_v2.py").read().replace("print(json.dumps(clean(R), indent=1))", "")
ns = {"__file__": f"{HERE}/ssr_paper_study_v2.py", "__name__": "study"}
exec(compile(src, "ssr_paper_study_v2.py", "exec"), ns)
series, benchmarks, el = ns["series"], ns["benchmarks"], ns["el"]
# the study must equal the published run
for a, b in ((f"{os.environ['SSR_OUT_DIR']}/results.json", f"{V}/results/results.json"), (f"{os.environ['SSR_OUT_DIR']}/published_variants.csv", f"{V}/results/published_variants.csv")):
    assert open(a).read() == open(b).read(), f"in-process run differs from {b}"

def r(v, k=2):
    if v is None: return None
    q = Decimal(1).scaleb(-k)
    return str(Decimal(repr(float(v))).quantize(q, rounding=ROUND_HALF_UP))

by_name = {s["name"]: s for s in series.values()}
out = {"top_bottom": [], "selected": [], "benchmarks": [], "named_parts": {}}
ranked = sorted(el, key=lambda s: -s["ssr_full"])
for s in ranked[:12] + ranked[-13:]:
    b = s["boot"]["b36"]
    out["top_bottom"].append(dict(name=s["name"], start=s["start"][:4], sharpe=r(s["sharpe_full"]), dsr=r(s["dsr"], 3), ssr=r(s["ssr_full"]),
                                  ssr4=r(s["ssr_full"], 4), pct=[r(b["pct_lo95"]), r(b["pct_hi95"])], turnover=r(s["turnover"], 1), stype=s["stype"], freq=s["freq"]))
SELECTED = ["haa/haa-standard", "baa/baa-g12", "daa/daa-g12", "paa/paa-high", "laa/laa-standard", "vitral-multi-asset-momentum/vitral-mam-standard",
            "momentum-correlation-triplet/mom-corr-triplet-standard", "gtaa/gtaa-5", "adm/adm-standard", "gem/gem-standard", "sma-trend/sma-trend-spy",
            "century-momentum/century-momentum-standard", "golden-butterfly/golden-butterfly-base", "all-weather-dalio/all-weather-dalio-base",
            "classic-60-40/classic-60-40-base", "buy-the-dip/buy-the-dip-standard"]
for n in SELECTED:
    s = by_name.get(n)
    if s is None:
        out["selected"].append(dict(name=n, missing=True)); continue
    out["selected"].append(dict(name=n, start=s["start"][:4], sharpe=r(s["sharpe_full"]), dsr=r(s["dsr"], 3), ssr=r(s["ssr_full"]), ssr_2000=r(s["ssr_2000"]),
                                ssr_2008=r(s["ssr_2008"]), q_le05=r(s["boot"]["b36"]["q_le05"]) if s.get("boot") else None,
                                q_le05_raw=s["boot"]["b36"]["q_le05"] if s.get("boot") else None))
for b in benchmarks.values():
    out["benchmarks"].append(dict(name=b["name"], start=b["start"][:4], months=b["months"], sharpe=r(b["sharpe_full"]), ssr=r(b["ssr_full"]), ssr_2000=r(b["ssr_2000"]),
                                  ssr_2008=r(b["ssr_2008"]), **{f"sub_{k}": r(b[f"sub_{k}"]) for k in ("pre2000", "2000s", "2010s", "2020s")}, sub_2000s_n=b["sub_2000s_n"]))
for n in ("haa/haa-standard", "momentum-correlation-triplet/mom-corr-triplet-standard", "gem/gem-standard"):
    s = by_name[n]; p = s["parts"]; b = s["boot"]["b36"]
    out["named_parts"][n] = dict(n_windows=p["n_windows"], min_z_ann=r(p["min_z_ann"]), mean_z_ann=r(p["mean_z"] * math.sqrt(12)), naive_sd=r(p["naive_sd"]), hac_sd=r(p["hac_sd"]),
                                 hac_over_naive=r(p["hac_sd"] / p["naive_sd"]), neg_share=p["neg_share"], bootmean=r(b["mean"]), pct=[r(b["pct_lo95"]), r(b["pct_hi95"])],
                                 basic=[r(b["basic_lo95"]), r(b["basic_hi95"])], ssr=r(s["ssr_full"]), ssr_2000=r(s["ssr_2000"]))
# family ranges named in Section 5.4
fam = {}
for s in el: fam.setdefault(s["strategy"], []).append(s["ssr_full"])
out["family_ranges"] = {k: [r(min(v)), r(max(v)), len(v)] for k, v in fam.items()}
out["rank_of"] = {n: 1 + [x["name"] for x in ranked].index(n) for n in ("classic-60-40/classic-60-40-base", "paired-switching/paired-switching-spy-tlt", "uis/uis-standard", "haa/haa-standard")}
out["classic_6040_ssr"] = r(by_name["classic-60-40/classic-60-40-base"]["ssr_full"])
json.dump(out, open(f"{V}/results/fullprec_tables.json", "w"), indent=1)
print(json.dumps(out, indent=1))
