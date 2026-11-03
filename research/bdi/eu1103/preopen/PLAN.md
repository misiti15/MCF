Educational only — not financial advice

# eu1103 / preopen — pre-declaration (owner Q3, 2026-11-03: what can we know by 09:25-09:38, and an "on deck" list)

Written 2026-11-03 before any feature in this folder was joined to a trade outcome. Research only: nothing in config/,
setups, exits, ledger, backlog or the live path changes.

## Data (only what the live runner has or can get from Alpaca)
- Pre-market: Alpaca SIP 30-minute bars 04:00-09:30 ET (`fetch_pm.py`, read-only GET, the same data plan the runner
  uses). Per symbol-day: pm volume, pm $ volume, pm high / low, first open, last close (= last pre-market trade before 09:30).
- Overnight news: Alpaca news API (`/v1beta1/news`, Benzinga feed — checked 2026-11-03, HTTP 200 on our keys).
  Count of articles tagged with the symbol, prior session 16:00 ET -> 09:30 ET (`fetch_news.py`).
- Daily bars (prior close / high / low, adv20, ATR) and the 09:30-09:38 1-minute RTH bars: two-year SIP cache
  (lab) and Alpaca for the live sessions.
- Short interest / days-to-cover: NOT on Alpaca. Asset `shortable` / `easy_to_borrow` flags are current-state only (no
  history), so they cannot be back-tested; not used.

## Features (all known by 09:30, or 09:35 for the opening bar; no look-ahead)
Symbol level:
1. `pm_rvol`   = pm $ volume / median pm $ volume of the symbol's prior 20 sessions (needs >= 10 prior sessions).
2. `pm_share`  = pm $ volume / adv20 (prior).
3. `pm_gap_atr` = |pm_last / prev_close - 1| / (atr_d / prev_close)   (size of the gap known at 09:30, ATR units).
4. `pm_gap_side` = signed pm gap in the trade direction (gap x +1 long / -1 short), ATR units.
5. `pm_range_atr` = (pm_high - pm_low) / atr_d.
6. `pcl`       = prior-day close location (close - low) / (high - low).
7. `news_n`    = overnight article count (log1p).
8. `o5_rvol`   = 09:30-09:35 $ volume / adv20.
9. `o5_ret_side` = (09:35 close / 09:30 open - 1) in ATR units, signed in the trade direction.
Market level (same for every name that day):
10. `spy_pm_side` = SPY pm gap % signed in the trade direction.
11. `qqq_spy_pm` = QQQ pm gap % - SPY pm gap % (tech leadership pre-open), signed in the trade direction.
12. `pm_breadth_side` = share of the lab universe with pm_last > prev_close, minus 0.5, signed in the trade direction.
13. `pm_disp`   = cross-sectional std of pm gaps (% , universe) — a "big news morning" proxy.
14. `sec_pm_side` = the stock's sector SPDR pm gap % signed in the trade direction (sector = the SPDR with the highest
    daily-return correlation on TRAIN; names with corr < 0.3 get no sector and the feature is missing -> kept).

## Trades scored
The 8 busiest live setups as eu1103/universe ran them on the two-year open frames (its `score2y.py`, the live modules'
own mask() / score(), first signal per symbol-day, live min_adv per setup, production costs + time-of-day multiplier).
TRAIN = 2024-10 + 2025-03..12, VALID = 2026-01..03 + 2026-07-01..09-15. Locked block 2024-11-01..2025-02-28 never loaded
or requested (asserted in both fetchers). Old holdouts (Apr-Jun 2026, Sep 16-Oct 5 2026) not scored; Sep 2026 pre-market
bars before 10-06 are used only as the trailing 20-session median for live `pm_rvol`.
Live = run_id 1 trades of all 5 accounts, 2026-10-06..11-02 (paper fills, rule 7), R = pnl_adj / $ risk.

## Gates (the configurations)
For each setup s and feature f: drop trades with f below its TRAIN q10 / q20 / q30 (of that setup's trades), or above
q70 / q80 / q90 -> 6 cuts. 14 features x 6 cuts x 8 setups = **672 setup gates**, plus the same 84 on the pooled book
(both sides, side-signed features) = **756 configurations**. Missing feature -> trade kept.
Admissible on TRAIN (owner / task rule): keeps >= 70% of the setup's trades AND >= 90% of its top-decile winners
(R >= the setup's TRAIN q90). Charter line (80% trades) reported beside it.
Pick: per setup the admissible gate with the highest TRAIN kept-avg-R lift (kept minus all), only if lift > 0 with
day-clustered t >= 1.0 on the lift (kept vs dropped). The pooled-book pick likewise.
"On deck" score for a day = the list of setups whose chosen gate is a market-level feature (10-13) and is passed that day
(setup ON) or not (OFF); symbol-level gates act per trade.

## Judged (once, no re-tuning)
- VALID: kept avg R, lift vs all, day-clustered t of kept-minus-dropped, retention of trades and top-decile winners
  (VALID q90), lift vs the same gate on the day-matched random control (does the feature pick the setup's trades or just
  good days for everyone).
- Live (paper, 20 sessions): the same chosen gates applied to that setup's live trades (and the pooled gate to all live
  trades), same metrics; avg R w/o best day.
- Pass = lift > 0 on VALID AND live, retention >= 70% / >= 90% on both, VALID t >= 1.0. With 756 configurations the
  try-count bar sqrt(2 ln 756) = 3.64 applies to any claim of an edge; a pass here is a lead, not a proposal.
- Daily-green goal: share of sessions green in total R and avg R, before and after the gate, reported for VALID and live.
