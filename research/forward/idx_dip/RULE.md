# Index open-dip rules — FROZEN 2026-11-27 (forward shadow only)

*Educational only — not financial advice. Research only: no order, no config, no account runs this.*

Source: research/qqqopen_1127 (wave 3, IDX6 lead) and research/idxdip_1127 (wave 4: IDX6 = the only robust point;
IWM 0.75% at 09:45 = lead, recommended for a pre-registered forward check). Both rules below are those study cells
exactly as found (engine E4, `idx_sim.day_rows` + `simulate`, ported line for line into `shadow.py`); they are not
re-tuned. `shadow.py --verify` re-scores the cached FIT + CHECK history and reproduces the study per split
(IDX6 FIT n 1 +4.293R, CHECK n 1 +0.015R; IWM45 FIT n 10 +1.148R, CHECK n 9 +0.261R — identical).
Any change to anything below = a new rule with a new freeze date and a fresh count.

## Rules (SIP 1-minute RTH bars, raw prices; bar close = bar start + 1 min; open = the 09:30 bar open)

| rule | signal index | dip X | check time T | traded (long) | bounce B | exit |
|---|---|---|---|---|---|---|
| **IDX6** | QQQ | 1.5% | 09:55 | TQQQ | 0.20 | 1R trail |
| **IWM45** | IWM | 0.75% | 09:45 | TNA | 0.20 | 1R trail |

1. **Dip**: the index running low since 09:30 is <= open x (1 - X%) on a bar that closes by T.
2. **Trigger**: the first index bar from the first dip bar on, closing in [T-5, T+10], whose close >= running low +
   B x (open - running low). No trigger in the window = no signal.
3. **Entry**: k = the traded-ETF bar at/before the trigger bar's start minute; long at the open of bar k+1 (market).
   Requires ETF open - ETF low(09:30..k) > 0 and ETF close[k] > that low.
4. **Stop** = ETF low(09:30..k) - 0.10 x (ETF open - that low). Stop-first each bar; fill at the stop, or at the bar
   open if it gapped through (not on the entry bar).
5. **Trail**: once MFE >= 1R (bar highs), stop = max(stop, entry + (MFE - 1) x risk), updated at bar end.
6. **Time exit**: at the open of the first bar at/after 15:55; half days: last bar close - 5 min (e.g. 12:55 on a
   13:00 close). One trade per rule per day; both rules can fire on the same day.

## Costs (always in)

**LIVE-L main** (research/primshorts_1126/cells_live.json: cost_R = a / stop_bps + b by price bucket x exit kind),
**LR8 alongside** (1c + 1bp a side, entry x time-of-day multiplier, +2c on a stop fill, x3 under $5). Stress column
**S12** = entry one bar later (stop kept) + 2 bp adverse a side on top of LIVE-L. Same code as idx_score.costs.

## History (research/idxdip_1127, LIVE-L, 2016-01..2026-11-04, locked block excluded)

- IDX6: n 16, +1.15R, t 3.29, best day 23%, w/o best +0.94, S12 +0.73 (t 2.35). 13 of 16 trades in 2016-2022; T2,
  FIT, CHECK one trade each. ~1 trade a year since 2023.
- IWM45: n 144, +0.24R, t 2.00, best day 19%, w/o best +0.19, S12 +0.22 (t 1.73). EARLY +0.09, T2 +0.53, FIT +1.15,
  CHECK +0.26. ~11 trades a year since 2023.
- Both were picked from 40 + earlier grid configs (program N ~9,300); neither clears the per-config bar 2.72 on its own
  except IDX6 on 16 trades. That is why this is forward-only.

## Pass bar for a promotion write-up (stated up front, scored once)

Unit = one shadow trade; the **book** = both rules together; t is day-clustered (R summed per day).
Scored once the log holds **>= 15 signal days** (sessions 2026-11-05 onward; 2026-11-05..11-27 backfilled at freeze):

1. book avg R after **LIVE-L > 0**, with day-clustered **t >= 2.0** (one pre-specified test on one book; per-rule
   numbers are reported, not tested);
2. best-day share of total R **< 50%** and avg R **without the best day > 0**;
3. book avg R under **S12 > 0** (+1 minute entry, +2 bp a side).

All three → write it up for the owner (a DECISION, e.g. a low-rep home slot for IDX6 / IWM45; nothing enabled
automatically). Any one missing → close the question (logged; no re-tune on the same forward data).

**Harm stop**: from 8 signal days on, if book cumulative LIVE-L R <= -6R or book avg R <= -0.40R → close the question.
**Time cap**: at ~12 signal days a year, 15 days take ~15 months. If 15 are not reached by 2028-06-30, score what is
there and report it as INCONCLUSIVE (no pass possible).

## Run

    python research/forward/idx_dip/shadow.py --date YYYY-MM-DD      # after 16:15 ET; idempotent (replaces that date)
    python research/forward/idx_dip/shadow.py --score

Market data only (GET /v2/stocks/bars via mcf.replay.store._fetch_bars). A run during the session writes 'pending'
rows that a later run replaces. Rule-change context: these are shadow trades of fixed rules; no ledger change applies.
