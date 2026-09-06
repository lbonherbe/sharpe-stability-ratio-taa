Place the four month-end extracts here (or point SSR_DATA_DIR at their folder) to re-run the study:

- variants_monthend.jsonl: one line per variant, {variant_id, nav: {YYYY-MM-DD: nav}}
- variants_monthly.jsonl: one line per variant with its metadata (slug, strategy, type, frequency, leverage, risk category)
- bench_monthend.jsonl: one line per benchmark, {symbol, nav: {YYYY-MM-DD: adjusted close}}
- leaderboard.json: the public leaderboard payload (entries with deflated_sharpe, turnover, etc.)

They are not redistributed in this repository; see the top-level README.
