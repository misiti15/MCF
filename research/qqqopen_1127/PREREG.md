# QQQOPEN-1127 — pre-registration (written before any scoring)

*Educational only — not financial advice.* Research only: no change to config/, setups, exits, assignments, decisions or the ledger.

## Question
The live index open-dip setups (IDX1-qqq100-0955-TQQQ-hold / -trail, IDX3-spy075-0955-3x-trail; class `index_dip_bounce`,
research/bdi/idxdip1015) have 3 live trades each, all winners (IDX1 hold +3.5R avg, one +8.4R day 2026-11-25). Their
original evidence was 359 DEV sessions (8 trades, t 0.23). Is the idea real on long index history, or luck? Should it get
more exposure (more accounts / size)?

## Data
* SIP 1-minute RTH bars, QQQ, SPY, TQQQ, SPXL. 2016-01-04..2022-09-30 fetched GET-only from Alpaca market data (raw
  prices — each day is self-contained, so splits do not matter intraday and cost buckets use the real traded price);
  2022-10-03..2024-09-13 `data/cache_fresh/1Min`; 2024-09-16..2026-11-04 `data/cache_hist/1Min`.
* The 3x ETF's real bars are traded (TQQQ for QQQ signals, SPXL for SPY signals; live IDX3 picks SPXL or UPRO by dollar
  volume, SPXL was the pick on 85% of the original DEV trades — SPXL only here). Intraday leveraged-ETF decay is negligible
  (daily reset), and the real bars already contain it.
* **Locked block 2024-11-01..2025-02-28 is never read** (asserted in code on every day loaded).

## Splits
EARLY 2016-01..2022-12 (new, never used by this lineage) · T2 2023-01..2024-09 · FIT 2024-10 + 2025-03..09 ·
CHECK 2025-10-01..2026-11-04. DEV = EARLY + FIT. Live window 2026-10-16..2026-11-26 reported separately (live trades, LR8).

## Rules simulated (replicating mcf/strategies/index_dip.py + mcf/backtest/engine.simulate)
* FADE-LONG (= live rule): index running low since 09:30 >= X% below the open on a bar closed by 09:55; trigger = first
  index bar closing in [09:50, 10:05] with close >= run_low + 0.20 x (open - run_low). Trade: 3x ETF, market entry at the
  next bar's open; stop = ETF running low - 0.10 x (ETF open - ETF low); stop-first inside a bar, gap through -> bar open.
* FADE-SHORT (symmetric): index running high >= X% above the open by 09:55; trigger close <= run_high - 0.20 x
  (run_high - open) in [09:50, 10:05]; short the 3x bull ETF; stop = ETF running high + 0.10 x (ETF high - ETF open).
* FOLLOW-SHORT / FOLLOW-LONG (continuation): index move since the open at the 09:54 bar close (known at 09:55) <= -X% /
  >= +X%; enter at the 09:55 bar open in the direction of the move; stop = the ETF's session open -/+ 0.10 x |ETF open -
  ETF 09:54 close| (the move since the open is the risk).
* Exits: HOLD = flatten at 15:55 (half days: last bar - 4 min, the LR1 rule), TRAIL = trail 1R behind the best once
  MFE >= +1R (engine semantics: updated at bar end, active from the next bar).

## Configurations (counted)
signal (QQQ->TQQQ, SPY->SPXL) x X (0.5, 0.75, 1.0, 1.5 %) x rule (FADE-LONG, FADE-SHORT, FOLLOW-SHORT, FOLLOW-LONG) x
exit (HOLD, TRAIL) = **64**, plus the 3 live replicas traded on the 1x ETF (QQQ/SPY) as an instrument check = **67**.
Lineage (idxdip1015) 1,134 -> 1,201. Cumulative program N ~8,952 + 67 = ~9,019 (lineage-claim bar t >= ~4.3).

## Costs (always in)
LIVE-L (primary; research/primshorts_1126/cells_live.json: cost_R = a / stop_width_bps + b per price bucket x exit kind)
and LR8 (1c + 1 bp per side x time-of-day entry mult, +2c on stops, short borrow 1.2 bp). Also reported, never used for a
pass: ETF-TIGHT (1 bp per side + 1c extra on stops), since 3x index ETFs are penny-spread names and LIVE-L's fixed b term
was fit on stocks.

## Pass bars
**H1 (pre-specified, no selection): the 3 live configs** (QQQ 1.0 FADE-LONG HOLD, QQQ 1.0 FADE-LONG TRAIL, SPY 0.75
FADE-LONG TRAIL). Each passes only if ALL of:
1. LIVE-L mean R > 0 on EARLY, T2 and CHECK separately (FIT reported);
2. LIVE-L day-clustered t over all non-locked history (EARLY+T2+FIT+CHECK) >= 2.13 (one-sided Bonferroni for 3);
3. avg R without the best day > 0 over all history; best-day share of total R < 50% (and < 25% flagged as healthy);
4. control: mean R above the 95th percentile of a size-matched random-day control (500 draws: same count, random other
   days of the same split, entry at the same clock time, same stop distance in % of price, same exit), all history;
5. positive LIVE-L mean in >= 60% of calendar years with >= 3 trades;
6. positive in both regimes: QQQ above vs below its 50-day SMA at the prior close (and high vs low 20-day realized vol
   reported).
LR8 is reported alongside; a pass under LIVE-L that fails LR8 is called out.

**H2 (grid search, 64 configs): finalists** = configs with DEV LIVE-L day t >= 2.0 and >= 30 DEV trades, top 4 by DEV t
(if none, the top 4 by DEV t are still listed as non-finalists). A finalist passes only if: DEV t >= 2.90 (sqrt(2 ln 67)),
T2 > 0 and CHECK > 0 under LIVE-L, pooled T2+CHECK day t >= 1.5, plus bars 3-4 above. Every finalist is reported.

**Remedy effect report:** if a finalist modifies a live setup (e.g. a different exit for IDX1), the per-setup effect on each
of the 5 live IDX setups (IDX1 hold/trail, IDX2, IDX3, IDX5 replicas) is reported: how many improve / worsen and by how much.

## Verdict rule
PASS = H1 passes for a config (deserves more exposure, still via backlog + owner). LEAD = positive on EARLY, T2 and CHECK
but a t / concentration / control bar missed. FAIL = negative on EARLY, T2 or CHECK (live record = luck / small sample).
INCONCLUSIVE = too few trades (< 30 over all history) to judge.
