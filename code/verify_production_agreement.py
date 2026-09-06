"""Agreement check between the platform's production sharpe_stability service and the standalone prototype
(Section 4.4 of the paper). Needs the private BestFolio backend on the path (BF_BACKEND_DIR) and the
month-end extracts (SSR_DATA_DIR); its retained output is results/production-agreement-check.txt."""
import os
import sys, json, csv, importlib, math, statistics as st
W = os.environ["BF_BACKEND_DIR"]
SP = os.environ["SSR_DATA_DIR"]
sys.path.insert(0, W)
mod = importlib.import_module("app.services.sharpe_stability")
print("module members:", [n for n in dir(mod) if not n.startswith("_")][:30])
fn = None
for name in ("sharpe_stability_from_monthly_returns", "sharpe_stability_from_returns", "compute_sharpe_stability"):
    if hasattr(mod, name): fn = getattr(mod, name); break
assert fn, "no entry point found"
def rets(nav):
    ks = sorted(nav); v = [float(nav[k]) for k in ks]
    return [v[i]/v[i-1]-1 for i in range(1, len(v))]
proto = {}
for r in csv.DictReader(open(f"{SP}/ssr_catalog.csv")):
    if r["kind"] == "variant" and r["ssr_full"]:
        proto[int(r["id"])] = float(r["ssr_full"])
navs = {json.loads(l)["variant_id"]: json.loads(l)["nav"] for l in open(f"{SP}/variants_monthend.jsonl")}
diffs, nones = [], []
import numpy as np
for vid, nav in navs.items():
    r = rets(nav)
    res = fn(np.asarray(r, dtype=float))
    ssr = getattr(res, "ssr", res if isinstance(res, (float, type(None))) else None)
    if vid in proto:
        if ssr is None: nones.append(vid); continue
        diffs.append((abs(ssr - proto[vid]), vid, ssr, proto[vid]))
diffs.sort(reverse=True)
print(f"compared {len(diffs)} variants; max |diff| = {diffs[0][0]:.2e} (variant {diffs[0][1]}: codex {diffs[0][2]:.6f} vs proto {diffs[0][3]:.6f}); median |diff| = {st.median(d[0] for d in diffs):.2e}; None where proto had a value: {nones}")
# fixture check
fx = json.load(open(f"{SP}/ssr_reference.json"))
for c in fx["cases"]:
    n = 200 if c["n_windows"] > 100 else 60
    res = fn(np.asarray(fx["monthly_returns"][:n], dtype=float), window=c["window"]) if "window" in fn.__code__.co_varnames else None
    if res is not None:
        print(f"fixture w={c['window']} n={n}: codex {getattr(res,'ssr',None)} vs ref {c['ssr']:.8f}")
