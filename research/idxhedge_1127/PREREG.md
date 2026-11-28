Educational only — not financial advice.

# IDXHEDGE-1127 pre-registration (written 2026-11-27 evening ET, before any configuration below was simulated or scored)

Question (remedy): Primary is ~80% short and its worst days are squeezes (e.g. 11-25). Does a ONE-SHOT index-long hedge
sleeve (SPY or QQQ), opened at a squeeze moment known in real time and sized to Primary's net short exposure at that
moment, cut Primary's tail (worst-5 days, days <= -10R, red days) on CHECK and T2 at a cost of no more than ~0.2 R/day,
better than a size-matched constant hedge and random-time hedges? Sources: UPDAY-1127 (SQZ long hedged Primary, corr
-0.32, too costly in single stocks; index suggested), HEDGE-B 1126 (continuous SPY beta hedge cut depth but cost 60-120
R/yr through rebalance churn; "one-shot hedge" salvage lead). Research only: no config / setup / exit / assignment /
decision / ledger change.

## Configurations (N = 12) = trigger {A, B6, B10} x instrument {SPY, QQQ} x k {0.25, 0.5}
- **Trigger A (gap-down morning, SPY reclaims VWAP):** day is a heavy gap-down morning: gd_share >= q67, where gd_share =
  share of the fixed 469-name universe (data/cache_fresh/1Min names, as DAYTYPE-1127) whose first regular 09:30 open is
  <= 0.99 x the prior session's last regular close (prior close not bridged over the locked block or gaps > 5 calendar days),
  and q67 = 67th percentile of gd_share over FIT days only (computed mechanically by the script, printed in the report).
  Trigger minute m = first 1-min bar with bar start in [10:30, close-60 min] where SPY close_m > SPY VWAP_m and
  close_{m-1} <= VWAP_{m-1} (a cross back above VWAP), and Primary's net beta exposure E_m < 0 (net short).
- **Trigger B X (book squeeze while SPY above VWAP), X in {6, 10}:** m = first bar with start in [09:45, close-60 min]
  where Primary's closed + open book R (all setups, E4 mark at bar m close, costs in) <= -X R, SPY close_m > VWAP_m,
  and E_m < 0.
- VWAP = cumulative typical-price ((h+l+c)/3) x volume VWAP of SPY from the 09:30 bar, regular session only, bars at or
  after the calendar close dropped (mcf.data.bars.cap_at_close semantics; pre-2024 half days from the idxdip_1127 list).
- **One shot:** at most one hedge per day, never re-entered. **Fill:** close of bar m+1 (one-minute delay). **Exit:** the
  first bar m' > fill bar with SPY close_{m'} < VWAP_{m'} -> exit at close of bar m'+1; else flat at the close of the bar
  starting at calendar close - 6 min (i.e. flat at 15:55, 12:55 on half days).
- **Size:** hedge long notional (in R-dollars, 1R = 1 unit) = k x (-E_m) / 0.01 / beta_I, where E_m = sum over Primary's
  open lots of side x beta_SPY x 0.01 x entry / risk (R per +1% SPY; hedgeb_1126 shrunk 60-day betas, point in time) and
  beta_I = 1 for SPY, QQQ's point-in-time 60-session daily beta to SPY (shifted one day; default 1.2 if < 20 obs) for QQQ.
  Sized once at the trigger; lots opened later are not hedged. Hedge R = notional x (P_exit / P_fill - 1) - costs.
- The sleeve is an overlay: it is not part of Primary's latch / LATCH-OPEN / -20R halt (those use Primary's lots only).
Counted: N ≈ 9,350 (wave-5 synthesis) + 12 = **≈ 9,362**. Family bar sqrt(2 ln 9,362) ≈ 4.28 shown descriptively;
per-study multiplicity bar for the sleeve's own t: sqrt(2 ln 12) = **2.23**.

## Engine, lots, contexts, splits
- Engine E4 = research/cfprimary_1127/e4nb.py extended to record, per minute, the book's closed + open R and E (and E by
  setup); daily R by setup must equal the unextended engine exactly (asserted on all days) before any score.
- Lots: bench10 regenerated tonight (squeeze_1125/gen.py + hedgeb_1126/build.py, unchanged); expected 52,544 candidates.
  **LIVE-L costs on shorts**, LR8 research on NM-ETF (as cfprimary / rwout).
- Contexts: **LO** (LATCH-OPEN, main) and **BASE** (realised -2R latch) alongside. A config must pass in LO; BASE reported.
- Splits: FIT 2024-10 + 2025-03..09 (q67 fit + confirmation only); **CHECK** 2025-10-01..2026-11-04; **T2**
  2023-01-03..2024-09-13. EARLY (2016-22) does not exist for the Primary bench, so it is not scored (stated in report).
  Locked block 2024-11-01..2025-02-28 filtered at load and asserted absent in every script.

## Hedge costs (index ETFs; honest, not zero)
- **IDX-L (main):** 1 bp per side of notional (half-spread + slippage on SPY/QQQ, as HEDGE-B) + SEC fee on the sell
  (20.60e-6 x value) + TAF 0.000195/share on the sell + CAT 0.00005/share each side.
- **LR8-IDX (alongside, conservative):** the live runner per-share formula 2 x (0.01 + price x 1e-4) + 0.02 per round trip
  (~2.7 bp at $600).
- **Stress:** fill and exit one more minute late (+1 min) and +2 bp per side on top of IDX-L.

## Controls (per config x context, CHECK and T2)
- **C-RAND (random-time hedges), 500 draws, seed 1127:** per period, the same number of hedge days as the config, drawn
  from days where Primary is net short (E < 0) at some bar in [10:30, close-60]; entry bar uniform among those bars;
  same k, same instrument, same VWAP-loss / 15:55 exit and costs. Reported: the config's percentile on dR/day and on the
  worst-5 improvement.
- **C-CONST (size-matched constant hedge):** every day, a long in the same instrument from the 10:30 bar close to 15:55,
  with a constant notional set so that per period its total notional-minutes equal the config's. Reported alongside.
- **C-ALWAYS (descriptive):** every day with E < 0 at 10:30, the same sizing rule at 10:30, held to 15:55.

## Metrics (Primary + sleeve vs Primary alone, per config x context x period)
Avg R/day and dR/day (= sleeve net R per day over all sessions), sleeve cost per year (252 x avg sleeve cost / day) and
dR per year; sleeve gross / net per hedge day, hit rate, day-clustered t of sleeve net R over hedge days; **worst-5 days**
(mean), **days <= -10R**, **red days per month** (x 21), rolling 20-session floor; best-day share of the sleeve's total net
R (largest single day / total, when total > 0) and avg sleeve R without its best day; stress and LR8-IDX versions;
per-setup / book effect: the sleeve P&L allocated to setups by each setup's share of E at the trigger (count of setups
improved / worse and by how much per month); share of hedge days that are Primary's worst-20% days.

## Pass bars (all in LO, on BOTH CHECK and T2; a config passes as a REMEDY only if every bar holds)
1. Cost: dR/day >= -0.20 (IDX-L) and >= -0.25 under stress.
2. Tail: worst-5 mean improves by >= 10% and days <= -10R does not rise.
3. Red days per month do not rise by more than 0.5.
4. Control: worst-5 improvement above the 90th percentile of C-RAND, and dR/day >= C-RAND median.
5. Beats C-CONST on worst-5 at no worse dR/day (- 0.05 tolerance).
6. Best-day share of the sleeve's tail benefit (largest single-day improvement among the worst-5 days / total) < 50%.
A **full PASS (self-financing hedge)** additionally needs sleeve net R > 0 on CHECK and T2 with day-clustered t >= 2.23.
Verdict: PASS (full) / PASS-REMEDY (bars 1-6) / LEAD (bars 1-2 on both splits, any control bar failing) / FAIL.
Any PASS/LEAD is research only; nothing is built or switched on from this study.
