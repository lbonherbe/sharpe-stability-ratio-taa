# Ancillary script output, restated series of 2026-09-28 (paper version 0.5)

Context: ancillary script run on the month-end series of the 219 variants active on 5 September 2026, as restated on 28 September 2026, including the partial September month. Used for the Section 2.1 autocorrelation-adjusted Deflated Sharpe check and the Section 4.4 reproduction of the Deflated Sharpe Ratios (Section 3.3, K = 219, computed by `dsr_recompute.py` with the platform's implementation). The primary study (`ssr_paper_study_v2.py`) uses completed months only, so the SSR figures printed below (partial month, 177 published variants, ad hoc percentiles) are not the paper's.
Data: latest backtest run per variant sampled to month-end (219 variants), benchmark month-ends with the total-return corrections (`build_bench_monthend.py`), leaderboard fields of 28 September 2026 with the K = 219 Deflated Sharpe Ratio (`dsr_recompute.py`).
Method: `ssr_catalog.py` (stdlib only; imports app.deflated_sharpe from the private backend for the expected-maximum benchmark). Rolling 36-month per-period Sharpe, rf=0, sample SD; SSR(0) = mean / sqrt(Newey-West long-run variance, Bartlett, L=w-1). AR(1) Deflated Sharpe variance of Lopez de Prado, Lipton and Zoonekynd (2026).
Full-precision values quoted in the paper: DSR reproduction max |diff| 4.98e-07 (the six-decimal rounding); AR(1)-adjusted minus current: min -0.017918, max +0.020948; one threshold crossing at 0.90 (published, downward).

Names: variants that were not published on the leaderboard are shown as "unpublished research variant N"; their names are withheld (2026-10-06). Their numbers are unchanged.

```
SANITY monthly Sharpe vs engine: n=219 median|diff|=0.0000 max=0.0000

PUBLISHED variants with SSR: 177 of 177; start-date distribution: {'1980': 34, '1990': 147, '2000': 169, '2008': 175}
SSR(0,w=36,L=35) full history, published: min 0.15 p10 0.31 p25 0.36 median 0.45 p75 0.52 p90 0.63 max 1.18; distinct at 2dp: 54
Spearman SSR_full vs Sharpe_full: 0.59
Spearman SSR_full vs DSR (Robustness): 0.53
Spearman SSR_full vs SSR_nw(auto-lag): 0.97
Common window since 2000-01: 169 published variants; Spearman SSR_2000 vs Sharpe_2000: 0.68; Spearman SSR_full vs SSR_2000: 0.78

TOP 12 published by SSR (full history)
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
carter-white-knuckle/carter-white-knuckle-base       2019-10   0.51  0.460    1.18                    0.03     0 -0.03
momentum-correlation-triplet/mom-corr-triplet-standa 1987-11   1.25  1.000    0.91    0.90    0.77    0.19     0 -0.09
momentum-correlation-triplet/mom-corr-triplet-smartl 1987-11   1.10  0.999    0.89    0.81    0.69    0.14     0 -0.11
low-initiative-letf-v2/low-initiative-letf-v2-standa 2002-02   0.82  0.904    0.85            1.11    0.14     0 -0.04
alphaone-momentum/alphaone-momentum-standard         1993-09   0.92  0.986    0.81    0.82    1.00    0.25     0 -0.02
momentum-correlation-triplet/mom-corr-triplet-plus   1986-03   1.23  1.000    0.80    0.76    0.79    0.14     0 -0.04
rvol-shifter/rvol-shifter-cash-only                  2003-02   0.86  0.926    0.75            0.90    0.05     0 -0.06
dms-triad/dms-triad                                  1985-09   1.25  1.000    0.68    0.73    1.15    0.12     0 -0.07
pragmatic-aa/pragmatic-aa-standard                   1986-03   1.13  1.000    0.68    0.65    0.65    0.09     0 -0.07
dms-triad/dms-triad-plus                             1985-09   1.18  1.000    0.66    0.89    1.09   -0.04     0 -0.07
kiss-momentum/kiss-combined-70-30                    1986-03   1.20  0.999    0.66    0.80    0.78   -0.26     1 -0.07
tqqq-quadrant-stack/tqqq-quadrant-stack-buffered     1996-12   0.91  0.971    0.66    0.80    1.18   -0.48     2 -0.08

BOTTOM 12 published by SSR (full history)
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
us-market-benchmark/us-market-100                    1988-01   0.81  0.926    0.29    0.31    0.73   -0.90    12  0.00
global-market-benchmark/global-market-60-40          1988-01   0.72  0.827    0.29    0.30    0.76   -1.05    12  0.03
letf-upro-zroz-gld/letf-upro-zroz-gld-base           1986-07   0.71  0.819    0.28    0.31    0.56   -1.04    12 -0.04
paired-switching/paired-switching-spy-tlt            1920-07   0.72  0.946    0.28    0.36    0.37   -1.10    10  0.01
uis/uis-standard                                     1920-09   0.71  0.940    0.24    0.43    0.39   -0.94    12  0.00
gold-cross-asset/gold-cross-asset-base               1986-03   0.68  0.794    0.22    0.20    0.14   -1.09    13 -0.02
regime-detector/regime-detector-standard             1990-11   0.67  0.744    0.22    0.24    0.50   -1.67    10 -0.03
vix-shield/vix-shield-leveraged                      1990-02   0.65  0.731    0.21    0.27    1.67   -1.46    13 -0.05
regime-detector/regime-detector-smartleverage        1990-11   0.61  0.637    0.20    0.22    0.50   -1.73    13 -0.04
schwoerer-rp-gold-scv/schwoerer-rp-gold-scv-no-filte 1986-03   0.72  0.855    0.19    0.39    0.38   -1.31    20  0.03
sma-trend/sma-trend-tlt                              1991-01   0.56  0.508    0.18    0.14    0.09   -1.09    13  0.03
sma-trend/sma-trend-gld                              1991-01   0.57  0.538    0.15    0.13    0.07   -1.53    22  0.02

BENCHMARKS
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
S&P 500 (VFINX)                                      1976-09   0.82           0.32    0.30    0.74   -0.90    10  0.00
SPY                                                  1993-02   0.78           0.26    0.30    0.74   -0.92    15  0.00
QQQ                                                  1999-04   0.56           0.27    0.30    0.88   -0.93    13  0.05
GLD                                                  2004-12   0.67           0.20            0.17   -0.93    18 -0.05
TLT                                                  2002-08   0.32           0.15            0.11   -1.22    19  0.05
US bonds (VBMFX)                                     1987-01   1.16           0.33    0.30    0.23   -0.92     8  0.10
60/40 (VFINX/VBMFX)                                  1987-01   0.95           0.34    0.35    0.61   -0.66     7  0.01

SELECTED well-known strategies
name                                                    from Sharpe    DSR SSRfull SSR2000 SSR2008 minRoll  %neg  rho1
haa/haa-standard                                     1974-03   1.49  1.000    0.48    0.89    0.92    0.26     0 -0.01
buy-the-dip/buy-the-dip-standard                     1985-11   1.04  0.990    0.41    0.94    1.02   -0.46     7 -0.03
momentum-correlation-triplet/mom-corr-triplet-standa 1987-11   1.25  1.000    0.91    0.90    0.77    0.19     0 -0.09
baa/baa-g12                                          1986-03   1.28  1.000    0.60    0.51    0.50   -0.68     2 -0.07
daa/daa-g12                                          1986-03   1.29  1.000    0.51    0.48    0.48   -0.54     3 -0.02
gem/gem-standard                                     1986-03   1.04  0.998    0.41    0.38    0.52   -0.11     1 -0.01
adm/adm-standard                                     1986-03   1.10  1.000    0.53    0.51    0.61   -0.02     0 -0.01
gtaa/gtaa-5                                          1986-03   1.14  1.000    0.46    0.40    0.85    0.10     0 -0.07
paa/paa-high                                         1986-03   1.27  1.000    0.52    0.43    0.43   -0.31     4 -0.06
laa/laa-standard                                     1986-03   1.18  1.000    0.63    0.69    0.76   -0.34     1 -0.12
classic-60-40/classic-60-40-base                     1923-01   0.79  0.989    0.31    0.37    0.63   -1.25     7  0.06
golden-butterfly/golden-butterfly-base               1988-01   1.14  0.999    0.49    0.53    0.62    0.11     0 -0.07
vitral-multi-asset-momentum/vitral-mam-standard      1986-03   1.25  1.000    0.61    0.57    0.53   -0.03     0 -0.04
letf-upro-zroz-gld/letf-upro-zroz-gld-base           1986-07   0.71  0.819    0.28    0.31    0.56   -1.04    12 -0.04
golden-ratio-dual-gate/golden-ratio-dual-gate-standa 2008-05   1.06  0.980    0.62                    0.41     0 -0.03
since 2000: S&P 500 (VFINX) SSR 0.30 -> 156 of 169 published variants score higher
since 2000: SPY SSR 0.30 -> 156 of 169 published variants score higher
since 2000: QQQ SSR 0.30 -> 154 of 169 published variants score higher
since 2000: US bonds (VBMFX) SSR 0.30 -> 156 of 169 published variants score higher
since 2000: 60/40 (VFINX/VBMFX) SSR 0.35 -> 134 of 169 published variants score higher

DSR reproduction: n_trials mine 219 vs prod 219; benchmark monthly mine 0.159680 vs prod 0.15968
rho1 across 219 trials: min -0.14 p10 -0.08 median -0.03 p90 0.03 max 0.09; share |rho1|>0.10: 2%
DSR reproduction vs leaderboard (published): median|diff| 0.0000 max 0.0000
AR(1)-adjusted DSR minus current: median +0.0001, most negative -0.0179, most positive +0.0209; fragile-flag flips at 0.90: 1
   flip: voltarget-qqq/voltarget-qqq-conservative           rho1 +0.02 DSR 0.902 -> 0.899 (published)
   largest drop: unpublished research variant 1                     rho1 +0.09 DSR 0.927 -> 0.909 n=303
   largest drop: dms-bamboo/dms-bamboo-plus-plus                    rho1 +0.07 DSR 0.916 -> 0.902 n=498
   largest drop: unpublished research variant 2                     rho1 +0.06 DSR 0.650 -> 0.642 n=496
   largest drop: unpublished research variant 3                     rho1 +0.07 DSR 0.643 -> 0.635 n=333
   largest drop: schwoerer-rp-gold-scv/schwoerer-rp-gold-scv-no-fil rho1 +0.03 DSR 0.855 -> 0.848 n=487
   largest drop: unpublished research variant 4                     rho1 +0.04 DSR 0.937 -> 0.930 n=259
```
