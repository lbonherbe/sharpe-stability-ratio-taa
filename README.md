# Replication package: The Sharpe Stability Ratio in Tactical and Static Asset Allocation Backtests

Laurent Bonherbe, BestFolio Research. Working paper, version 0.7, 20 October 2026. Posted on SSRN 16 September 2026 (version 0.4): https://ssrn.com/abstract=7441662 (DOI https://doi.org/10.2139/ssrn.7441662).

Data vintage (version 0.7): the sample is the catalog of 5 September 2026 (219 active variants, 177 published, 173 eligible); every series is the platform's backtest as re-run on 17 October 2026 (code `896bf8a`, methodology `drift-until-flip-v1`), with completed months through August 2026, the benchmark corrections applied and the Deflated Sharpe Ratio at K = 219. Version 0.7 reports every result twice: with a cash reference of zero, as the SSR's authors recommend (`results/zero_reference/`), and with returns measured above US dollar cash, a Treasury bill fund chain (`results/above_cash/`, paper Section 5.6 and Appendix E.3). The paper's Appendix G lists what moved between versions (see also "Versions" below). Earlier outputs are in this repository's history (version 0.6 at commit 05ecf7c, version 0.4 at commit 8b86d9b).

The paper applies the Sharpe Stability Ratio (SSR) of Bajo Traver and Rodriguez Dominguez (2026, SSRN 6344658) to 173 published strategy variants of the BestFolio catalog. This repository holds the code that produced every number, table and figure in the paper, the outputs it produced, and the supplementary tables. It does not hold the raw month-end series (see "What is not here").

## Layout

| Path | Content |
|---|---|
| `paper/ssr-taa-working-paper.pdf` | The paper (version 0.7). |
| `code/ssr_study_v07.py` | The study: `ssr_paper_study_v2.py` of version 0.6 with an option (`SSR_EXCESS=1`) to measure returns above cash. Reads the month-end extracts, writes one results folder. Python 3.11, NumPy only. |
| `code/ssr_paper_study_v2.py` | The version 0.5 and 0.6 study, kept for reference. |
| `code/ssr_permutation_v07.py` | The permutation benchmark of Section 5.2 and Appendix D.7: the SSR of each series' own monthly returns in random orders, the permutation multiple and p-value. Stops unless every real SSR equals the matching study table. Suggested by Randy Harris of Dual Momentum Systems. |
| `code/fullprec_v07.py` | Reruns the study in-process, checks the outputs are identical, and rounds every per-series table cell once from full precision. |
| `code/excess_robustness.py`, `code/iid_lengths_v07.py`, `code/live_k_quadrants.py` | Section 5.6 comparisons between the two definitions, the independent-returns baseline by history length, and the Deflated Sharpe cells at the platform's live count of trials (Appendix C). |
| `code/make_charts_v07.py`, `code/make_fig_v07.py`, `code/make_fig_excess.py`, `code/_chartkit.py` | The figures. Read `results/`, write `charts/`. Matplotlib. |
| `code/verify_production_agreement.py` | Agreement check between the platform's production implementation and the standalone script (Appendix A.4). Needs the private backend; its retained output is in `results/`. |
| `code/build_bench_monthend.py`, `code/dsr_recompute.py` | Build the benchmark month-ends and the Deflated Sharpe input at K = 219. Need the private backend. |
| `code/ssr_catalog.py` | The ancillary script: the autocorrelation-adjusted Deflated Sharpe check (Appendix F.1) and the reproduction of the Deflated Sharpe Ratios (Appendix A.4). Needs the private backend. |
| `fixture/ssr_reference.json` | Reference values on synthetic series, computed by a separate, independent implementation and used to test both implementations. |
| `results/zero_reference/`, `results/above_cash/` | For each definition: `results.json` (every aggregate number, keyed by topic), `published_variants.csv` (177 published variants, every per-series statistic), `benchmarks.csv` (the seven benchmark series), `fullprec_tables.json`, the two rolling Sharpe paths behind Figure 3, and the permutation run (`permutation_results.csv`, `.json`, `permutation_run.log`). |
| `results/supplementary_*.csv` | The supplementary tables as distributed with the paper (published variants and benchmarks, both definitions). |
| `results/excess_robustness.json`, `results/iid_lengths_v07.json`, `results/live_k_quadrants.json` | Outputs of the three comparison scripts above. |
| `results/production-agreement-check.txt` | Output of the agreement check. |
| `charts/` | The figures as rendered in the paper. |

## Definition (identifier `ssr-36m-nw-v1`)

Monthly simple returns from completed month-end net asset values, cash reference zero (above cash: the return of US dollar cash between the same two month-ends is subtracted first). Rolling per-period Sharpe ratio over a 36-month window (sample standard deviation, ddof 1). Long-run variance of the rolling series by the Newey-West Bartlett kernel with bandwidth 35 and sample autocovariances with divisor N. SSR = mean of the rolling series divided by the square root of that variance. Reported only with at least 120 monthly returns. Bootstrap: moving blocks of 12 or 36 monthly returns, 2,000 replicates, percentile and basic intervals. The paper's Section 3 gives the formulas with a worked example, and Appendix A the reasons for each choice.

## Reproducing

```
pip install numpy matplotlib
SSR_DATA_DIR=/path/to/extracts SSR_OUT_DIR=results/zero_reference python code/ssr_study_v07.py
SSR_EXCESS=1 SSR_DATA_DIR=/path/to/extracts_above_cash SSR_OUT_DIR=results/above_cash python code/ssr_study_v07.py
SSR_DATA_DIR=/path/to/extracts SSR_OUT_DIR=results/zero_reference SSR_SUPP=results/zero_reference/published_variants.csv python code/ssr_permutation_v07.py
SSR_EXCESS=1 SSR_DATA_DIR=/path/to/extracts_above_cash SSR_OUT_DIR=results/above_cash SSR_SUPP=results/above_cash/published_variants.csv python code/ssr_permutation_v07.py
SSR_OUT_DIR=results/zero_reference python code/make_charts_v07.py
```

The above-cash extract adds the platform's daily US dollar cash index to the same month-end series. The study takes a few minutes per definition; the bootstrap dominates. The random seeds are fixed in the scripts.

## What is not here

The extract files the study reads (the month-end series and stored monthly moments of the 219 variants, pulled read-only from the production database on 17 October 2026, the cash index, the benchmark month-ends built from the 5 September 2026 benchmark extract by `build_bench_monthend.py`, and the leaderboard input built by `dsr_recompute.py`), and the raw inputs of those scripts, are not redistributed: the benchmark prices are licensed data, and the catalog extract includes research variants that were not published at the time. They are retained by the author and available to referees on request through the SSRN abstract page. The published variants' current statistics, including the SSR, are served by the platform's public leaderboard endpoint (`https://bestfolio.app/api/performance/leaderboard`, field `sharpe_stability`), measured above cash since 18 October 2026.

## Versions

- **0.7 (20 October 2026).** Every number recomputed on the series as re-run on 17 October 2026 (proxy-chain audit: indicators warm up before a strategy's earliest permitted start, so most backtests begin earlier; corrected proxy histories; the all-equity US allocation back to 1900). New Section 5.6 and Appendix E.3 repeat the headline results above US dollar cash. Sample, estimator, settings, seeds and K = 219 unchanged. Paper Appendix G.1 gives the details.
- **0.6 (6 October 2026).** Restructured for reading, not recomputed; outputs at commit 05ecf7c.
- **0.5 (28 September 2026).** Every number recomputed on the platform's restated series; permutation benchmark; AI-use statement.
- **0.4 (10 September 2026).** First SSRN posting; outputs at commit 8b86d9b.

## Licence and citation

Code: MIT (see `LICENSE`). Results tables and figures: CC BY 4.0. Cite the paper (see `CITATION.cff`).
