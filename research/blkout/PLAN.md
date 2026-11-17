# BLKOUT — what the earnings blackout costs or saves existing setups (Observer; frozen 2026-11-17 ~06:00 ET, BEFORE any outcome)

Educational only — not financial advice. Approved by Lead (lead-20261117-0500-1) as a DESCRIPTIVE look, 0 configs. It informs the
owner's blackout POLICY only; it proposes no setup and no rule change. Skeptic's pre-score conditions (skeptic-20261117-0950-1/0951-2)
are all built in below. One run; no tuning after this commit; only dated amendments written before the run may change it.

## Question
Scout's Move Hunt look: ~62% of big moves (~31/day) are in earnings-blackout names that Live skips by rule. Do EXISTING setups' 2-year
backtest trades inside the blackout window (+-4 sessions of a report) do better or worse than the same setups' trades outside it?

## Data (fixed)
- Trades: research/momside/data/trades_full.parquet (Builder's MOMSIDE Amendment 2 input: FULL-DAY 2-year backtest lists bt_lab1104,
  all entry times; columns setup, side, symbol, date, r (net), gross, spy_move). Locked block absent (asserted). Half days
  2025-07-03 / 11-28 / 12-24 dropped (checklist 42; count printed).
- Earnings: research/bdi/earnings/data/earnings_yf.parquet (the file the blackout policy uses, GD.EARN). ASSERT it exists (GD._blackout
  silently returns 'no blackout' if missing). Print coverage: share of traded names with >= 6 reports inside the trade window.
  Names with < 6 reports are EXCLUDED from both groups (missing dates would leak event trades into 'outside').
- Sessions: offsets counted on the actual NYSE sessions present in the trade file (not busday_offset).

## Definitions
- Reaction session R0: report session 'bmo' -> report date; 'amc' -> next session; other / 'dmh' / missing time -> report date
  (time untrusted; such events count in the POOLED inside group but are EXCLUDED from the BMO/AMC split).
- Offset k = sessions from R0 to the trade date (nearest report). INSIDE = |k| <= 4 (the policy window); OUTSIDE = |k| >= 10 (a clean
  gap); 5 <= |k| <= 9 is a buffer, excluded.
- x = gross R (primary first, checklist 17); ex-market x = gross - beta_setup x spy_move (beta per setup by OLS on TRAIN trades, as
  MOMSIDE); net r reported last, with the cost caveat below.

## Primary (pooled, before any split) — same-week non-event control
Within setup x ISO-week cells holding BOTH inside and outside trades: diff = mean(inside) - mean(outside) of that cell's trades, weighted
by the cell's inside count. Pooled over cells; day-clustered SE by clustering cell contributions on the inside trades' session dates
(pooled ratio estimator, checklist 39). Reported for gross, ex-market and net; TRAIN (<= 2025-09-30) / VALID (2025-10-01..2026-10-07) /
FWD (2026-10-08..), as MOMSIDE. MDE80 = 2.8 x SE printed beside each (checklist 41). Best-week share of the total.

## Secondary (only after the primary; cells counted, checklist 26)
- Per setup (>= 30 inside trades): inside-minus-outside ex-market per trade; better / worse counts; top-5 share.
- Offset profile k = -4..+4 (9 cells) and BMO vs AMC (2) on trusted-time events only: 18 cells, printed with n and t; read as
  descriptive only.
- Side: long vs short setups.

## Cost caveat (Skeptic) — no 'blackout COSTS R' claim from this run
The 2-year backtest charges x3 costs only when |gap| >= 20%; event-day spreads are wider than normal, so inside-blackout net R reads
OPTIMISTIC. If the primary shows inside gross > outside, the claim waits for Phase 2: measured NBBO spreads on a sample of event days vs
the same names' normal days (Alpaca historical quotes, fetched outside 07:30-16:00 ET, block refused by obs_blockguard), and inside
trades re-charged by that ratio. If inside gross <= outside, the blackout is not costing R and the policy reads as protective.

## Reading (pre-registered)
| primary ex-market (VALID) | reading |
|---|---|
| inside < outside, t <= -2 | blackout PROTECTS: existing setups do worse in event windows; policy stands. |
| |t| < 2 | nothing above MDE80 either way; the blackout neither costs nor saves measurably; policy is the owner's call on risk. |
| inside > outside, t >= 2 | possible cost of the blackout -> Phase 2 spread re-charge BEFORE any owner line. |
TRAIN must agree in sign for either directional reading; FWD reported only.
Run: after FWDCAL is read; light local job, outside market hours (Builder's container holds trades_full.parquet).
