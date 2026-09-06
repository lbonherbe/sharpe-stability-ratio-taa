# Sharpe Stability Ratio prototype, 2026-09-05

Context: ancillary prototype run on the 5 September 2026 extract including the partial September month (219 active variants). Used for the Section 2.1 autocorrelation-adjusted Deflated Sharpe check, the Section 3.3 benchmark and the Section 4.4 reproduction of the published Deflated Sharpe Ratios. The primary study (ssr_paper_study_v2.py) uses completed months only.
Data: prod backtest_runs latest daily_nav sampled to month-end (219 active variants, released or not), price_cache month-end adj_close for benchmarks, public /api/performance/leaderboard (177 published, dsr_meta n_trials 219).
Method: ssr_catalog.py (stdlib only; imports app.deflated_sharpe from the repo for the expected-max benchmark). Rolling 36-month per-period Sharpe, rf=0, sample SD; SSR(0) = mean / sqrt(Newey-West long-run variance, Bartlett, L=w-1); nSSR = sqrt(n_windows) * SSR. AR(1) DSR variance per tschm/jsharpe (Lopez de Prado, Lipton, Zoonekynd 2025).

```
SANITY monthly Sharpe vs engine: n=219 median|diff|=0.0003 max=0.0050

PUBLISHED variants with SSR: 177 of 177; start-date distribution: {'1980': 34, '1990': 147, '2000': 169, '2008': 175}
SSR(0,w=36,L=35) full history, published: min 0.15 p10 0.31 p25 0.36 median 0.45 p75 0.53 p90 0.66 max 1.14; distinct at 2dp: 56
Spearman SSR_full vs Sharpe_full: 0.65
Spearman SSR_full vs DSR (Robustness): 0.58
Spearman SSR_full vs SSR_nw(auto-lag): 0.97
Common window since 2000-01: 169 published variants; Spearman SSR_2000 vs Sharpe_2000: 0.68; Spearman SSR_full vs SSR_2000: 0.81

TOP 12 published by SSR (full history)
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
carter-white-knuckle/carter-white-knuckle-base       2019-10   0.59  0.529    1.14                    0.05     0 -0.04
momentum-correlation-triplet/mom-corr-triplet-standa 1987-11   1.24  1.000    0.98    0.91    0.78    0.21     0 -0.08
momentum-correlation-triplet/mom-corr-triplet-smartl 1987-11   1.12  0.999    0.89    0.81    0.70    0.16     0 -0.09
momentum-correlation-triplet/mom-corr-triplet-plus   1986-03   1.14  1.000    0.83    0.78    0.80    0.15     0 -0.03
low-initiative-letf-v2/low-initiative-letf-v2-standa 2002-02   0.85  0.921    0.82            1.03    0.21     0 -0.01
alphaone-momentum/alphaone-momentum-standard         1993-09   0.92  0.984    0.81    0.82    1.00    0.25     0 -0.02
dms-triad/dms-triad                                  1985-09   1.26  1.000    0.77    0.72    0.93    0.35     0 -0.08
dms-triad/dms-triad-plus                             1985-09   1.20  1.000    0.75    0.84    0.93   -0.00     0 -0.07
tqqq-quadrant-stack/tqqq-quadrant-stack-buffered     1996-12   0.98  0.986    0.75    0.89    1.21   -0.36     2 -0.07
rvol-shifter/rvol-shifter-cash-only                  2003-02   0.85  0.911    0.75            0.90    0.05     0 -0.06
pragmatic-aa/pragmatic-aa-standard                   1986-03   1.17  1.000    0.73    0.66    0.65    0.10     0 -0.07
kiss-momentum/kiss-combined-70-30                    1986-03   1.24  0.999    0.73    0.80    0.79   -0.21     1 -0.07

BOTTOM 12 published by SSR (full history)
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
classic-60-40/classic-60-40-base                     1923-01   0.73  0.945    0.29    0.37    0.63   -1.30     8  0.06
letf-upro-zroz-gld/letf-upro-zroz-gld-base           1986-07   0.69  0.777    0.29    0.32    0.60   -0.98    12 -0.05
global-market-benchmark/global-market-60-40          1988-01   0.74  0.845    0.28    0.30    0.77   -1.03    12  0.03
paired-switching/paired-switching-spy-tlt            1920-07   0.70  0.897    0.27    0.36    0.37   -1.10    11  0.01
uis/uis-standard                                     1920-09   0.69  0.883    0.23    0.44    0.39   -0.95    13  0.01
gold-cross-asset/gold-cross-asset-base               1986-03   0.69  0.790    0.22    0.20    0.14   -1.09    13 -0.01
regime-detector/regime-detector-standard             1990-11   0.67  0.736    0.22    0.25    0.50   -1.66    10 -0.03
vix-shield/vix-shield-leveraged                      1990-02   0.67  0.731    0.22    0.29    1.84   -1.40    13 -0.05
regime-detector/regime-detector-smartleverage        1990-11   0.61  0.613    0.20    0.22    0.50   -1.73    13 -0.04
schwoerer-rp-gold-scv/schwoerer-rp-gold-scv-no-filte 1986-03   0.72  0.842    0.18    0.39    0.38   -1.31    20  0.03
sma-trend/sma-trend-tlt                              1991-01   0.56  0.482    0.18    0.14    0.09   -1.09    13  0.03
sma-trend/sma-trend-gld                              1991-01   0.57  0.511    0.15    0.13    0.07   -1.53    22  0.02

BENCHMARKS
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
S&P 500 (VFINX)                                      1976-09   0.75           0.30    0.30    0.74   -0.90    10 -0.02
SPY                                                  1993-02   0.78           0.26    0.30    0.74   -0.92    15  0.00
QQQ                                                  1999-04   0.56           0.27    0.30    0.88   -0.93    13  0.05
GLD                                                  2004-12   0.67           0.20            0.17   -0.93    18 -0.05
TLT                                                  2002-08   0.32           0.15            0.11   -1.22    19  0.05
US bonds (VBMFX)                                     1987-01   0.99           0.32    0.30    0.23   -0.92     9  0.11
60/40 (VFINX/VBMFX)                                  1987-01   0.93           0.34    0.35    0.61   -0.66     7  0.01

SELECTED well-known strategies
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
haa/haa-standard                                     1974-03   1.49  1.000    0.52    0.88    0.89    0.25     0  0.00
buy-the-dip/buy-the-dip-standard                     1985-11   1.00  0.976    0.38    0.98    1.00   -0.55     9 -0.03
momentum-correlation-triplet/mom-corr-triplet-standa 1987-11   1.24  1.000    0.98    0.91    0.78    0.21     0 -0.08
baa/baa-g12                                          1986-03   1.26  1.000    0.57    0.51    0.50   -0.66     2 -0.07
daa/daa-g12                                          1986-03   1.32  1.000    0.49    0.48    0.48   -0.55     3 -0.04
gem/gem-standard                                     1986-03   0.99  0.994    0.40    0.38    0.52   -0.11     1  0.00
adm/adm-standard                                     1986-03   1.08  0.999    0.53    0.51    0.61   -0.02     0 -0.01
gtaa/gtaa-5                                          1986-03   1.20  1.000    0.45    0.41    0.88    0.12     0 -0.06
paa/paa-high                                         1986-03   1.27  1.000    0.50    0.43    0.43   -0.30     4 -0.06
laa/laa-standard                                     1986-03   1.20  1.000    0.63    0.70    0.77   -0.30     1 -0.12
classic-60-40/classic-60-40-base                     1923-01   0.73  0.945    0.29    0.37    0.63   -1.30     8  0.06
golden-butterfly/golden-butterfly-base               1988-01   1.13  0.999    0.50    0.53    0.64    0.13     0 -0.07
vitral-multi-asset-momentum/vitral-mam-standard      1986-03   1.31  1.000    0.59    0.57    0.53   -0.03     0 -0.03
letf-upro-zroz-gld/letf-upro-zroz-gld-base           1986-07   0.69  0.777    0.29    0.32    0.60   -0.98    12 -0.05
golden-ratio-dual-gate/golden-ratio-dual-gate-standa 2008-05   1.13  0.989    0.67                    0.48     0 -0.03
since 2000: S&P 500 (VFINX) SSR 0.30 -> 156 of 169 published variants score higher
since 2000: SPY SSR 0.30 -> 156 of 169 published variants score higher
since 2000: QQQ SSR 0.30 -> 154 of 169 published variants score higher
since 2000: US bonds (VBMFX) SSR 0.30 -> 156 of 169 published variants score higher
since 2000: 60/40 (VFINX/VBMFX) SSR 0.35 -> 139 of 169 published variants score higher

DSR reproduction: n_trials mine 219 vs prod 219; benchmark monthly mine 0.162712 vs prod 0.162712
rho1 across 219 trials: min -0.14 p10 -0.09 median -0.03 p90 0.03 max 0.09; share |rho1|>0.10: 3%
DSR reproduction vs leaderboard (published): median|diff| 0.0000 max 0.0004
AR(1)-adjusted DSR minus current: median +0.0001, most negative -0.0185, most positive +0.0210; fragile-flag flips at 0.90: 4
   flip: sector-rotation/sector-rotation-top3               rho1 -0.04 DSR 0.894 -> 0.901 (published)
   flip: aca-dynamic-bond/aca-dynamic-bond-stocks-sleeve    rho1 -0.03 DSR 0.896 -> 0.902 (published)
   flip: aca-dynamic-bond/aca-dynamic-bond-reit-sleeve      rho1 -0.10 DSR 0.898 -> 0.919 (published)
   flip: second-grader/second-grader-base                   rho1 +0.02 DSR 0.901 -> 0.896 (unreleased)
   largest drop: schwoerer-semis-signal/schwoerer-semis-smh         rho1 +0.09 DSR 0.919 -> 0.900 n=303
   largest drop: classic-60-40/classic-60-40-base                   rho1 +0.06 DSR 0.945 -> 0.935 n=1245
   largest drop: dms-bamboo/dms-bamboo-plus-plus                    rho1 +0.05 DSR 0.935 -> 0.926 n=498
   largest drop: kelly-3sig/kelly-3sig-ijr                          rho1 +0.04 DSR 0.874 -> 0.865 n=496
   largest drop: merriman-ubh/merriman-ubh-100eq                    rho1 +0.06 DSR 0.642 -> 0.634 n=333
   largest drop: schwoerer-rp-gold-scv/schwoerer-rp-gold-scv-no-fil rho1 +0.03 DSR 0.842 -> 0.835 n=487
```
