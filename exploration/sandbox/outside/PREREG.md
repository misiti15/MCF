# Track 6 (outside research) pre-registration — written 2026-11-28 00:40 ET, before any scoring

Educational only — not financial advice.

Two outside ideas, both absent from research/backlog.jsonl (checked: no "profit lock / daily target / consistency",
no per-setup equity-curve governor on intraday setups; the Komar governor was only tried on swing books, cwt-c-c9).

## Idea A: DAILY PROFIT LOCK ("quit while ahead", prop-firm daily target / consistency practice; house-money
literature says traders over-risk after gains)
Rule: per account and day, once the account's CLOSED R for the day reaches +X, no new entries for the rest of the
day; open lots run to their normal exits. X = k * sd_day, k in {0.25, 0.5, 1.0} (3 configs).
- Live: 10 journals, run 1, closed trades, 10-23..11-27, LR8 R. Per account (no cross-account dedupe).
  sd_day = expanding sd of that account's previous days' R (needs >= 5 prior days; earlier days unchanged).
- Bench: P4 candidates (L3-fromopen, RW3, RW5, NM-ETF) from the 2-year minute bench (cand.parquet, LIVE-L R),
  simplified book (<= 30 lots/setup/day, <= 3 per symbol per setup, -2R closed latch, -20R closed halt).
  sd_day from FIT period. Scored on CHECK and T2 separately. Locked block never read (asserted).
Scores: dR/day (day-clustered t on daily differences), red days, worst-5, avg dR without best day + best-day share,
lots removed, and two controls: (i) random skip of the same number of lots spread over all days (1,000 draws);
(ii) same-day random skip (same count, same day) - tests whether post-lock lots are worse than that day's lots.
Pass (for a forward-test proposal): dR > 0 with t >= 2 on both bench splits AND above the 95th pct of both controls
AND live dR >= 0.

## Idea B: SETUP EQUITY-CURVE GOVERNOR ("trade the equity curve", Komar / practitioner method)
Rule: a setup trades on day d only if the sum of its R over its last K traded sessions (walk-forward, before d) >= 0.
K in {5, 10} (2 configs). Needs K prior sessions; before that, trades normally.
- Live: all journals deduped (footrace key), setups with >= 20 trades.
- Bench: the 8 setups in cand.parquet, raw candidates (no book rules), CHECK and T2.
Scores: R per kept lot vs R per skipped lot, total dR, setups improved / worse, random setup-day skip control
(same skip fraction per setup, 1,000 draws). Pass: kept-lot avg R > skipped-lot avg R with t >= 2 on both bench
splits and live, and above the 95th pct of the random control.

Configs: 5 (A: 3, B: 2). Cumulative before tonight's tracks ~9,363.
Plus one descriptive check (0 configs): correlation of morning closed R (to 12:00 ET) with afternoon R per account-day.
