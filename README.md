# Replication package: The Sharpe Stability Ratio in Tactical and Static Asset Allocation Backtests

Laurent Bonherbe, BestFolio Research. Working paper, version 0.5, 28 September 2026. Posted on SSRN 16 September 2026 (version 0.4): https://ssrn.com/abstract=7441662 (DOI https://doi.org/10.2139/ssrn.7441662).

Data vintage (version 0.5): the sample is the catalog of 5 September 2026 (219 active variants, 177 published, 173 eligible); every series is the platform's backtest as restated on 28 September 2026 (release `release/2026-09-28-e9a2a80`, methodology `drift-until-flip-v1`, pre-1990 total-return corrections), with the benchmark corrections applied and the Deflated Sharpe Ratio at K = 219. The paper's "Changes from version 0.4" section lists what moved. The version 0.4 outputs (5 September 2026 extract) are in this repository's history at commit 8b86d9b.

The paper applies the Sharpe Stability Ratio (SSR) of Bajo Traver and Rodriguez Dominguez (2026, SSRN 6344658) to 173 published strategy variants of the BestFolio catalog. This repository holds the code that produced every number, table and figure in the paper, the outputs it produced, and the supplementary tables. It does not hold the raw month-end series (see "What is not here").

## Layout

| Path | Content |
|---|---|
| `paper/ssr-taa-working-paper.pdf` | The paper (same version as on SSRN). |
| `code/ssr_paper_study_v2.py` | The study. Reads the month-end extracts, writes everything in `results/`. Python 3.11, NumPy only. |
| `code/make_charts_v2.py`, `code/_chartkit.py` | The six figures. Reads `results/`, writes `charts/`. Matplotlib. |
| `code/verify_production_agreement.py` | Agreement check between the platform's production implementation and the standalone script (Section 4.4). Needs the private backend; its retained output is in `results/`. |
| `code/build_bench_monthend.py` | Builds the benchmark month-ends of version 0.5: the 5 September 2026 benchmark extract with the platform's total-return corrections applied to VFINX, VBMFX and VUSTX. Needs the private backend and daily price data. |
| `code/dsr_recompute.py` | The Deflated Sharpe Ratio at K = 219 (Section 3.3): reproduces every live published score with the platform's implementation, then applies it to the paper's 219 trials and writes the study's leaderboard input. Needs the private backend. |
| `code/fullprec_numbers.py` | Reruns the study in-process and rounds every per-series table cell once from full precision; writes `results/fullprec_tables.json`. |
| `fixture/ssr_reference.json` | Reference values on synthetic series, computed by a separate, independent implementation and used to test both implementations. |
| `results/results.json` | Every aggregate number in the paper, keyed by topic. |
| `results/published_variants.csv` | 177 published variants: identifiers, type, frequency, leverage, risk category, history, Sharpe, Deflated and Probabilistic Sharpe, SSR on the full history and the 2000 and 2008 windows, four subperiods with return counts, window and bandwidth variants, ratio components, bootstrap summaries for 12- and 36-month blocks. `excluded_from_primary` marks the three revised-data variants and the one below the ten-year gate. |
| `results/benchmarks.csv` | The same statistics for the seven benchmark series. |
| `results/rolling_haa-standard.json`, `results/rolling_sp500.json` | The two rolling Sharpe paths behind Figure 3. |
| `results/run.log` | The study's console output. |
| `code/ssr_permutation_v05.py` | The permutation benchmark of Section 6.5 (new in version 0.5): the SSR of each series' own monthly returns in 10,000 random orders, the permutation multiple and p-value, and the independent-returns baseline. Same extract and estimator as the study; stops unless every real SSR equals `results/published_variants.csv`. Suggested by Randy Harris of Dual Momentum Systems. |
| `results/permutation_results.csv` | Per series (173 variants and seven benchmarks, full history and the 2000 window): Sharpe, SSR, mean and standard deviation of the reordered SSRs, multiple, count of reorderings at or above the real SSR, p-value. |
| `results/permutation_results.json`, `results/permutation_run.log` | Every number Section 6.5 quotes, and the script's console output. |
| `results/production-agreement-check.txt` | Output of the agreement check (217 of 219 active variants agree to 15 decimals; the other two are below the production gate). |
| `results/fullprec_tables.json` | Full-precision values behind the per-series table cells (Tables 4 to 6). |
| `code/ssr_catalog.py`, `results/RESULTS-ancillary-2026-09-28.md` | The ancillary script and its output: the autocorrelation-adjusted Deflated Sharpe check (paper Section 2.1) and the reproduction of the Deflated Sharpe Ratios (Section 4.4). Run on the restated series including the partial September month; needs the private backend for the expected-maximum benchmark. |
| `charts/` | The six figures as rendered in the paper. |

## Definition (identifier `ssr-36m-nw-v1`)

Monthly simple returns from completed month-end net asset values, cash reference zero. Rolling per-period Sharpe ratio over a 36-month window (sample standard deviation, ddof 1). Long-run variance of the rolling series by the Newey-West Bartlett kernel with bandwidth 35 and sample autocovariances with divisor N. SSR = mean of the rolling series divided by the square root of that variance. Reported only with at least 120 monthly returns. Bootstrap: moving blocks of 12 or 36 monthly returns, 2,000 replicates, percentile and basic intervals. The paper's Section 4 gives the formulas and the reasons for each choice.

## Reproducing

```
pip install numpy matplotlib
SSR_DATA_DIR=/path/to/extracts python code/ssr_paper_study_v2.py   # writes results/
python code/make_charts_v2.py                                        # writes charts/
SSR_DATA_DIR=/path/to/extracts python code/ssr_permutation_v05.py   # Section 6.5, about 5 minutes
SSR_DATA_DIR=/path/to/extracts python code/fullprec_numbers.py      # table cells from full precision
```

`bench_monthend.jsonl` and `leaderboard.json` are themselves built by `code/build_bench_monthend.py` and `code/dsr_recompute.py` (private backend and raw pulls; see each script's docstring).

The study takes a few minutes; the bootstrap dominates. The random seed is fixed in the script.

## What is not here

The four extract files the study reads (`variants_monthend.jsonl` and `variants_monthly.jsonl` pulled from the production database on 28 September 2026, `bench_monthend.jsonl` built from the 5 September 2026 benchmark extract by `build_bench_monthend.py`, and `leaderboard.json` built from the public API payload of 28 September 2026 by `dsr_recompute.py`), and the raw inputs of those two scripts, are not redistributed: the benchmark prices are licensed data, and the catalog extract includes research variants that were not published at the time. They are retained by the author and available to referees on request through the SSRN abstract page. The published variants' current statistics, including the SSR, are served by the platform's public leaderboard endpoint (`https://bestfolio.app/api/performance/leaderboard`, field `sharpe_stability`).

## Licence and citation

Code: MIT (see `LICENSE`). Results tables and figures: CC BY 4.0. Cite the paper (see `CITATION.cff`).
