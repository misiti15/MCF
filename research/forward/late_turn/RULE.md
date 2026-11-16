# Late-turn rule — FROZEN 2026-11-16 (forward shadow only)

*Educational only — not financial advice. Research only: no order, no config, no account runs this.*

Owner 2026-11-16: "late turn forward yes". Source: `research/morning_low_1116` (NOTES.md, cell
11:20 / D1 / X = 10 bps / SPY +90, traded as SPXL). The rule below is that cell exactly as found; it is not
re-tuned. `shadow.py --verify` re-scores every cached session and reproduces the study's 35 signal days and their R
(same set, max |R diff| 5e-5). Any change to anything below = a new rule with a new freeze date and a fresh count.

## Rule (all prices from 1-minute RTH bars, bar close = bar start + 1 min)

1. **09:50 price** = SPY close of the 09:49 bar.
2. **Window** 10:55-11:20 (bars 10:55 .. 11:19). Window low = lowest SPY bar low in it.
3. **Setup** (all three, known at 11:20):
   - new low: the window low is below every SPY bar low from 09:50 to 10:54;
   - dip: the window low is at least **10 bps** below the 09:50 price;
   - reclaim: SPY's 11:19-bar close (the 11:20 price) is **above** SPY's 10:54-bar close (the 10:55 price).
   Otherwise the day is NO-SETUP (logged, not scored).
4. **Trade**: long **SPXL** at its 11:19-bar close (11:20).
   Stop = entry x (1 - 3 x u), u = max(SPY 11:20 price / window low - 1, 0.15%) + 0.05%.
   Stop checked on SPXL bar lows from the 11:20 bar on; fill at the stop, or at the bar open if it gapped through.
   Exit: SPXL close of the 12:49 bar (**12:50**, 90 minutes), if not stopped.
5. **Costs** (always in): 1 cent + 1 bp per side, +2 cents on a stop fill. R = (exit - entry - costs) / (entry - stop).

History (2024-09 .. 2026-11, locked block excluded, chosen after seeing VALID — the reason it is forward-only):
35 signal days (~7.6% of sessions, ~1.6 a month), avg +0.33 R, t 2.25, worst -1.07 R, avg R w/o best day +0.26 R;
TRAIN +0.20 R (n 18), VALID +0.46 R (n 17). Below the study's try-count bar (3.76 at N = 1,155).

## Pass bar for promotion to a Testing candidate (stated up front, scored once)

Scored on forward sessions only (2026-11-13 onward; 11-13 and 11-16 backfilled the same day the rule was frozen,
both NO-SETUP). When the forward log reaches **20 signal days**:

- avg R after costs **> 0**, and
- t-stat of R **>= 1.5**, and
- avg R **without the best day > 0**, and the best day **< 50%** of total R (no one-big-day record).

All four → write it up as a Testing candidate (a DECISION for the owner; still not enabled automatically).
Any one missing → retire the rule (logged; no re-tune on the same forward data).
At ~1.6 signals a month, 20 signals take roughly a year. An early look at 10 signals is reported for information
only and cannot promote or retire the rule.

## Running it

    python research/forward/late_turn/shadow.py --date YYYY-MM-DD     # after 12:50 ET (or re-run: idempotent)
    python research/forward/late_turn/shadow.py --verify              # rule == study, on the cache

`forward.csv`: one row per session (upsert by date): setup yes/no, signal time, SPY 09:50 price / window low / dip,
SPXL entry / stop / exit / exit time / stopped, R after costs, status (done / no setup: why / pending).
Bars come from `mcf.replay.store._fetch_bars` (read-only market data, no trading endpoint).
