"""Appendix C: the paper's K = 219 scores against the live trial universe after #4258 (N = 278, ETFHoldStrategy
excluded; results/dsr_live_4258.json), for the 173 eligible variants, on the zero-reference moments (main study) and on
the above-cash moments (Section 5.6). Also the pre-#4258 universe (286) for the record. Output: results/live_k_quadrants.json."""
import csv, json, os
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(f"{V}/results/dsr_live_4258.json"))
out = {}
for col, tag in (("main", "v1"), ("excess", "v2")):
    rows = [r for r in csv.DictReader(open(f"{V}/results/{col}/published_variants.csv")) if r["excluded_from_primary"] != "True" and r["ssr_full"] not in ("", "None")]
    assert len(rows) == 173
    for uni in ("post4258", "pre4258"):
        live = D[f"{uni}_{tag}"]["by_variant_id"]
        diffs = [abs(float(r["dsr"]) - live[r["variant_id"]]) for r in rows]
        res = {"n_trials": D[f"{uni}_{tag}"]["meta"]["n_trials"], "benchmark_ann": D[f"{uni}_{tag}"]["meta"]["benchmark_annualized_sharpe"],
               "max_abs_diff_vs_K219": max(diffs), "median_abs_diff": sorted(diffs)[86],
               "n_ge_090_live": sum(live[r["variant_id"]] >= 0.9 for r in rows), "n_ge_090_K219": sum(float(r["dsr"]) >= 0.9 for r in rows),
               "crossings": [(r["name"], round(float(r["dsr"]), 4), round(live[r["variant_id"]], 4)) for r in rows if (float(r["dsr"]) >= 0.9) != (live[r["variant_id"]] >= 0.9)]}
        for thr in (0.5, 0.37):
            q = [0, 0, 0, 0]
            for r in rows:
                hi_d = live[r["variant_id"]] >= 0.9; hi_s = float(r["ssr_full"]) >= thr
                q[(0 if hi_d else 2) + (0 if hi_s else 1)] += 1
            res[f"quadrants_at_{thr}"] = q
        out[f"{col}_{uni}"] = res
json.dump(out, open(f"{V}/results/live_k_quadrants.json", "w"), indent=1)
for k, v in out.items(): print(k, {a: b for a, b in v.items() if a != "crossings"}, "crossings:", len(v["crossings"]))
print(out["main_post4258"]["crossings"])
