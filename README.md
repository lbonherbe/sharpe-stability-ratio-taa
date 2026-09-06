# Replication package: The Sharpe Stability Ratio in Tactical and Static Asset Allocation Backtests

Laurent Bonherbe, BestFolio Research. Working paper, version 0.3, 6 September 2026. SSRN link: to be added once the abstract page is live.

The paper applies the Sharpe Stability Ratio (SSR) of Bajo Traver and Rodriguez Dominguez (2026, SSRN 6344658) to 173 published strategy variants of the BestFolio catalog. This repository holds the code that produced every number, table and figure in the paper, the outputs it produced, and the supplementary tables. It does not hold the raw month-end series (see "What is not here").

## Layout

| Path | Content |
|---|---|
| `paper/ssr-taa-working-paper.pdf` | The paper (same version as on SSRN). |
| `code/ssr_paper_study_v2.py` | The study. Reads the month-end extracts, writes everything in `results/`. Python 3.11, NumPy only. |
| `code/make_charts_v2.py`, `code/_chartkit.py` | The six figures. Reads `results/`, writes `charts/`. Matplotlib. |
| `code/verify_production_agreement.py` | Agreement check between the platform's production implementation and the standalone script (Section 4.4). Needs the private backend; its retained output is in `results/`. |
| `fixture/ssr_reference.json` | Hand-derived reference values (synthetic series) used to test both implementations. |
| `results/results.json` | Every aggregate number in the paper, keyed by topic. |
| `results/published_variants.csv` | 177 published variants: identifiers, type, frequency, leverage, risk category, history, Sharpe, Deflated and Probabilistic Sharpe, SSR on the full history and the 2000 and 2008 windows, four subperiods with return counts, window and bandwidth variants, ratio components, bootstrap summaries for 12- and 36-month blocks. `excluded_from_primary` marks the three revised-data variants and the one below the ten-year gate. |
| `results/benchmarks.csv` | The same statistics for the seven benchmark series. |
| `results/rolling_haa-standard.json`, `results/rolling_sp500.json` | The two rolling Sharpe paths behind Figure 3. |
| `results/run.log` | The study's console output. |
| `results/production-agreement-check.txt` | Output of the agreement check (217 of 219 active variants agree to 15 decimals; the other two are below the production gate). |
| `charts/` | The six figures as rendered in the paper. |

## Definition (identifier `ssr-36m-nw-v1`)

Monthly simple returns from completed month-end net asset values, cash reference zero. Rolling per-period Sharpe ratio over a 36-month window (sample standard deviation, ddof 1). Long-run variance of the rolling series by the Newey-West Bartlett kernel with bandwidth 35 and sample autocovariances with divisor N. SSR = mean of the rolling series divided by the square root of that variance. Reported only with at least 120 monthly returns. Bootstrap: moving blocks of 12 or 36 monthly returns, 2,000 replicates, percentile and basic intervals. The paper's Section 4 gives the formulas and the reasons for each choice.

## Reproducing

```
pip install numpy matplotlib
SSR_DATA_DIR=/path/to/extracts python code/ssr_paper_study_v2.py   # writes results/
python code/make_charts_v2.py                                        # writes charts/
```

The study takes a few minutes; the bootstrap dominates. The random seed is fixed in the script.

## What is not here

The four extract files the study reads (`variants_monthend.jsonl`, `variants_monthly.jsonl`, `bench_monthend.jsonl`, `leaderboard.json`, all pulled from the production database and public API on 5 September 2026) are not redistributed: the benchmark prices are licensed data, and the catalog extract includes research variants that were not published at the time. They are retained by the author and available to referees on request through the SSRN abstract page. The published variants' current statistics, including the SSR, are served by the platform's public leaderboard endpoint (`https://bestfolio.app/api/performance/leaderboard`, field `sharpe_stability`).

## Licence and citation

Code: MIT (see `LICENSE`). Results tables and figures: CC BY 4.0. Cite the paper (see `CITATION.cff`).
