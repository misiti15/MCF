# TICKSEL pre-registration (2026-11-25, written before any trait/ticker result was computed)
Educational only - not financial advice. Research only: no config, setup, account, ledger change; nothing committed.

## Question
Do ticker traits (A) or individual tickers (B) predict R for MCF's strong setups, so that setups can be made more selective
(exclusions of clearly negative buckets; size/priority tilts) WITHOUT cutting trade counts much?

## Data / engine (E1-style 2-year lab, bench10 "normal way" engine; no new simulator logic)
- Signals + 1-min exits: research/ultimate_1119/top10/bench10.py logic (copy tk.py; pyramid S/L2 trade lists reused for
  L3-fromopen and GEN-261029-06). Costs: LR8 research basis (add_r). Book: each setup's HOME account rules (bench10 BOOK +
  ETB>=0.9 for shorts, price>=5, testing cost filter 0.15R). Home: L3-fromopen/RW3/RW5/NM-ETF primary; L3-lowdist/L3-rsi5hi
  testing; RW7 testingf; RW6 livelab; GEN-261029-06 testingd.
- Halves: FIT = 2024-10 + 2025-03..09 (discovery ONLY); CHECK = 2025-10-01..2026-11-04 (scored once); T2 = 2023-01-03..2024-09-13
  (scored once). Locked block 2024-11-01..2025-02-28 never read (filters + asserts). Live: pyramid/X/live_dedup.parquet
  (10-06..11-24, LR8, one account per symbol-day) - direction check only.
- Two cost bases, both reported: R (research LR8) and R_adj = R + 0.5 x modelled cost when entry < $20 (Pyramid G: research
  model ~0.04-0.09R too harsh on sub-$20 names). A price-related rule must hold on BOTH bases.

## Traits (knowable at entry; prior days only + today's open)
price (entry) buckets <10 / 10-20 / 20-50 / 50-100 / >=100; ADV20 quintile; ATR14% quintile; beta60 vs SPY quintile;
sector ETF (secmap; ETFs = "ETF"); ETF vs stock; leveraged/inverse ETP; gap% bucket; prior-day return bucket; prior 5-day
return bucket; prior-day relative dollar volume (news/earnings proxy; no earnings calendar is available) bucket;
median quoted spread tercile (today's value - static, flagged); ETB rate (today's flag - static, flagged). Quintile cut
points are fixed on FIT. Market cap and short interest: no data (not tested).

## Families (Remedies rule: rules are family-level, not per-setup)
- L3 long (gap-down recovery): L3-gap-slope-fromopen-FD, L3-gap-slope-lowdist-FD, L3-gap-slope-rsi5hi-FD
- GD short (gap-down short fades): RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD,
  RW7-gapdn-bounce-early-short-FD
- singles: RW6-ns2-up3-short-FD, NM-ETF-late-dip-di-long, GEN-261029-06 (single-setup rules are flagged as "tailored")

## Selection rule (FIT only) and configs (max 15)
EXCLUSION candidates: a trait bucket in a family with FIT booked trades n >= 150 (singles n >= 60), share of family trades
<= 25%, bucket avg R - rest avg R <= -0.10 on BOTH cost bases, day-clustered t of the bucket-minus-rest difference <= -2.5.
Top 8 by t across families -> configs X1..X8 (fewer if fewer qualify).
TILT candidates (size 1.5x in the best bucket(s), 0.5x in the worst; no trade dropped): the 3 strongest family-level
monotone trait splits on FIT (t >= 2.5, top-vs-bottom quintile/bucket) -> configs W1..W3.
INDIVIDUAL TICKERS (B): per setup, empirical-Bayes shrunk FIT avg R per symbol (shrink k = 20 trades toward the setup mean).
  B0 (descriptive, not a config): CHECK avg R by FIT-shrunk decile; Spearman of symbol FIT vs CHECK avg R (n>=3 both).
  B1: exclude symbols in the bottom decile of shrunk FIT R (with >= 3 FIT trades). B2: 1.5x size on the top decile.
Total configs <= 13 (X1-8, W1-3, B1-2).

## Pass bar (scored once on CHECK and once on T2)
Exclusion PASS: on CHECK the excluded trades' avg R < 0 AND <= kept avg R - 0.05, total book R rises (book re-run after the
exclusion), trades kept >= 85% (family), day-clustered t of the difference <= -2.0, same sign on T2, and on per-setup
effects more family setups improve than worsen; plus beats random removal of the same share (>= 95th pct of 200 draws).
Tilt PASS: CHECK and T2 sized total R per unit of risk deployed above unsized by >= +0.01R/trade-equivalent and day-
clustered t >= 2.0. Tickers B: CHECK top-minus-bottom decile difference > 0 with t >= 2.0 and T2 same sign.
Live direction: reported only (no live per-setup filters from short samples - STOP2 rule 26(2)).
Every finalist reported (failures first), configs counted, per-setup better/worse, avg R w/o best day + best-day share,
trades kept %.
