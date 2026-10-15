# OPP 2026-10-14/15: recurring loser patterns tested as OPPORTUNITIES (pre-declaration)

*Educational only - not financial advice.*

Written 2026-10-15 **before any configuration below was scored.** Owner idea (2026-10-14): a loser pattern that
recurs is a signal; test the trade it points to, not only the filter that skips it. Parents:
`bdi1014-rw2-extension-floor` (RW2-FD short losers that "never worked", 4 sessions) and `bdi1014-st2-wrong-side`
(ST2-FD longs on stocks already down >= 3% from the open, 3 sessions). The two filters themselves stay queued in the
backlog; this study tests the opportunity side only.

## Data and costs (rules 1, 2, 19)
- `research/history2y` frames (5-minute bars 09:50-15:00, values at bar close), open months only via `lib.months()` /
  `lib.load_month` (the rule-19 locked block 2024-11-01..2025-02-28 is refused; MCF_HIST_ALLOW_LOCKED is never set).
  Head (09:35-09:45) and tail (15:05-15:55) bars come from `research/bdi/cwt/test_b/data/headtail.parquet`, read
  **with a date filter per open month only**, so no locked-block row is loaded. Daily open/close: `lib.daily()` (open
  dates only).
- Split: **train** = 2024-10 + 2025-03..2025-12, **valid** = 2026-01..2026-10-07; **open** = both. (The older
  holdouts Apr-Jun 2026 and Sep 16-Oct 5 2026 sit inside valid, as in every history study since rule 19; nothing is
  scored "once" on them here.)
- Costs: production (1c + 1 bps per side; target exit free; +2c on stop fills), entry side x `gates.tod_cost_mult`
  (09:30 open entry = x3.8), x3 extended tier (|gap| >= 20% or price < $5). R = 0.25 x daily ATR unless stated.
  Fills: entry at the signal bar's close (next poll), stop-first inside a bar, flat at the 15:55 close.
  Frame outcome columns (`r_*_t05s1/t1s1/t1s05`) are used where the geometry exists (`gates.prod_r`), otherwise the
  5-minute path (head + frame + tail) is simulated with the same cost model.

## Part A: RW2 "never worked" -> opportunity (parent RW2-exhaustion-noon-adv150-short-FD)
Signals: the RW2-FD mask (RSI5 > 90, close > 1% above 5-min SMA20, bearish divergence), adv20 >= $150M, bar close
09:50-15:00, first signal per symbol-day. Base = short t1s1 at the signal close (re-simulated; parity vs frame).
- **A1 opposite at the signal:** long at the RW2 signal close, geometries t05s1 / t1s1 / t1s05. (3)
- **A2 reverse at the RW2 stop:** when the base t1s1 short is stopped (stop before target), long at the stop bar's
  close (market, next poll; skipped after 15:50 or if the close is already through the leg's stop), geometries
  t05s1 / t1s1 / t2s1 / eod-s1 (1R stop, no target, flat 15:55). (4)
- **A3 = A2 on "never worked" stops only:** the short's best favourable excursion from entry through the stop bar was
  < 0.25R (known at the stop bar's close). (4)
- **A4 continuation short after the failed extension:** after the base stop, the first later bar (close <= 15:00)
  with trigger VL = close below VWAP, or LL = close below the previous bar's low; short at that close, R = 0.25 ATR,
  geometries t1s1 / t2s1 / eod-s1, on {all stops, never-worked stops}. (2 x 3 x 2 = 12)
- Part A = **23 configurations.**

## Part B: ST2's skipped stocks (down >= X% from the open) -> rebound longs (parent ST2-slope20up-long-am-t05s1-FD)
Universe: adv20 >= $95M (ST2's min_adv). X in {3, 4, 5, 6}.
- **B1 same-day rebound long**, trigger bar close 10:30-15:00, first trigger per symbol-day, entry at its close:
  - H5 = close > the previous 5-min bar's high, with fromOpen <= -X at the previous bar;
  - VW = VWAP reclaim (close > VWAP, previous close <= its VWAP) on a stock whose lowest fromOpen so far today
    (09:50 bar onward) is <= -X;
  - MR = H5 plus VWAP stretch: the previous bar was >= 0.5 daily ATR below VWAP.
  - Geometries t05s1 / t1s1. 4 x 3 x 2 = **24.**
- **B2 next-day rebound long:** day d closes >= X% below its open (daily open/close), adv20 >= $95M; on the next
  session d+1 (must be the next market date and not in the locked block) buy at the open (cost x3.8) or at the 09:50
  bar close (x1.4); exit same day: EOD (no stop, flat 15:55) or t1s1 (R = 0.25 x ATR). 4 x 2 x 2 = **16.**
- **B3 gap-fade reference** (counted as configurations): long at the d+1 open on any universe name gapping down
  >= 2% at that open, regardless of day d; EOD and t1s1. **2.** B2 is also reported split by d+1 gap sign.
- Part B = **42 configurations.**

**Total N_study = 65.** Study bar sqrt(2 ln 65) = 2.89. No configuration is added after scoring; if one is, it is
counted and the plan says so.

## Controls (rule 6)
- **Same-minute random:** mean production R of every universe bar (A: adv20 >= $150M; B1: >= $95M) at the same date and
  bar time on the same side, frame geometry (t2s1 and eod-s1 use t1s1, as in bdi1014). Excess = trade R - control.
- **Same-universe base rate (B1):** mean R of every bar in the 10:30-15:00 window in the same conditioned universe
  (fromOpen <= -X at the previous bar), same geometry - i.e. a random entry on the same kind of stock.
- **B2/B3 base rate:** the same entry and exit on every adv20 >= $95M name on the same d+1 (excess per trade = R minus
  that day's universe mean).

## Bars (fixed now)
- **Testing bar:** exp > 0 with day-clustered t >= 2.0; train > 0 and valid > 0; up and down sessions > 0
  (`gates.regime_split`); walk-forward share >= 0.6; ex-best-day > 0; excess over the same-minute control > 0;
  plateau: every neighbour (same part and trigger, adjacent X or adjacent geometry) has exp > 0.
- **Research / Primary bar:** the Testing bar plus t >= max(1.5, sqrt(2 ln N)) with cumulative lineage N:
  Part A lineage = exhaustion/RW2 934,970 + 23 = 934,993 (t >= 5.24); Part B lineage = stack1009 120,500 + 42 =
  120,542 (t >= 4.84). The study-only bar (2.89) is reported for reference.
- A pass would make a Testing candidate only (no holdout scored here; the locked block is the lead's single look).
