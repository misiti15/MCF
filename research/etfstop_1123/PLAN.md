Educational only — not financial advice.

# etfstop_1123: thorough study of ETF-STOP50 before the owner decides (pre-registration)

Written 2026-11-23 before any configuration in this study was scored. Research only: no config, setup or exit change.
Owner: "I don't want to restrict any one setup from potential gains long term ... not if it's at the risk of harming
potential gains too."

## Rule under study
**ETF-STOP50 (= Q50 of rules_1122 part D):** a booked `NM-ETF-late-dip-di-long` lot that is a *burst lot* (entered
when >= 4 NM-ETF lots — itself and same-minute candidates included — were booked in the last 10 minutes) uses half the
normal stop distance (stop = entry − 0.5 × risk), same shares, R counted in original risk units. Nothing else changes.

## Engine and data (E4-normal-way, reused unchanged)
- `partS.py` = rules_1122 `partD.py` (bench10 NM-ETF signals, 1-minute re-walk, LR8 costs, Primary book: cap 30,
  <= 3 lots per symbol, −2R latch on realized cost-R) with the burst definition parameterised (k, window), a stop
  fraction, and the variant switches below. Base must reproduce bench10 again: FIT +57.78R, T2 −9.16R, CHECK +10.71R.
- FIT = 2024-10 + 2025-03..09; T2 = 2023-01..2024-09-13; CHECK = 2025-10-01..2026-11-04.
  2024-11-01..2025-02-28 is never read (pyarrow filter + assert, also for SPY bars).
- SPY 1-minute bars (same caches, same filter) for the point-in-time index state at each entry: SPY close of the
  minute before entry vs. SPY's session open and session VWAP up to that minute (no look-ahead).
- Live: run-1 closed trades of every mcf-data* journal (`load_live.py`, LR8 cost-R). NM-ETF family = NM-ETF (Primary,
  Live Lab, Testing 2), WB1 (Explore 1), WB4 (Testing E), ULT-22 (Live Lab): 16 live sessions 10-19..11-20.
  Real SIP 1-minute bars for those 16 days fetched read-only (`fetch_live_bars.py`) so the live replay re-walks the
  half stop on actual minute lows (not the interpolated marks of rules_1122).

## Configurations (21 new scorings; N = 21)
| group | ids | rule |
|---|---|---|
| stop-fraction plateau (k=4, 10 min) | Q30 Q40 Q50 Q60 Q70 Q80 | burst lots stop at f × normal distance, f = 0.3..0.8 |
| burst-definition plateau (f = 0.5) | K3W5 K3W10 K3W15 K4W5 K4W15 K5W5 K5W10 K5W15 K6W5 K6W10 K6W15 | burst lot = >= k lots in the last w minutes (K4W10 = Q50) |
| variants (f = 0.5) | AV50 | half stop only on burst lots entered while SPY is below its session VWAP (point-in-time) |
| | AO50 | half stop only while SPY is below its session open (point-in-time) |
| | F5_50 | half stop only from the 5th lot of the burst onward |
| | Q50G2 | Q50 plus G2: once 2 lots of a burst have stopped out, flatten the burst's remaining open lots |

Q40 and Q50 were already scored in rules_1122; they are re-run here for the plateau and counted again.

**Bars.** Study N = 21 → max(1.5, sqrt(2 ln 21)) = 2.47. Lineage (ETF-burst 21 + giveback 2 + rules_1122 part D 21
+ 19 new here) N = 63 → 2.88. Applied to the day-clustered t of per-day dR (FIT+T2, and ALL). Tail insurance is not an
edge: a worst-day cut is reported as insurance with its price, never as an R improvement.

## Walk-forward (fixed now)
Choose the stop fraction on FIT only among {0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0 (= no rule)} by
J = FIT total R + FIT sum of the 5 worst FIT days (tail counted twice). Score the chosen fraction once on T2 and on
CHECK. Secondary (reported, not used): the fraction that maximises FIT total R alone.

## Metrics (Q50 in full; every config in the summary table)
1. **Harm to gains** (lot-matched by signal id vs base, all periods): burst lots that won under the normal stop and are
   stopped early (count, lost R); burst losers that lose less (count, saved R); lots whose outcome changes for other
   reasons (latch knock-on); MAE / MFE of base burst lots in R (buckets 0–0.25, 0.25–0.5, 0.5–0.75, 0.75–1, stopped)
   split winners / losers; effect on the 10 best base days and on the top-decile base winners (charter: keep >= 90%
   of top-decile winners: a top-decile lot is "kept" if its R under the rule is >= 90% of its base R).
2. **Stability:** dR and worst day per calendar year (2023 / 2024 / 2025 / 2026), per period, per hindsight day regime
   (SPY open-to-close > +0.3% up, < −0.3% down, else quiet — HINDSIGHT label), per point-in-time lot state (SPY
   above / below VWAP at entry); plateau tables over f and over (k, w); walk-forward as above.
3. **Tail robustness:** day bootstrap (5,000 resamples of all FIT+T2+CHECK days, seed 1123) of dR total, worst-day
   improvement and worst-5-days-sum improvement for Q50 (and the best variant): median and 5–95% bands, P(dR < 0),
   P(worst-day improvement > 0). Days per year on which the rule changed anything; R cost per year and $ at $105 risk
   per lot (Primary's typical live NM-ETF $ risk).
4. **Variants** AV50 / AO50 / F5_50 / Q50G2 scored like Q50.
5. **Generalisation / live:** the same rule (and the best variant) on every live NM-ETF-family lot with real minute
   bars: burst lot = >= 4 lots of the same setup and account with entry in the last 10 minutes (same 5-minute decision
   bar peers included, as rules_1122 live); a burst lot whose minute low reaches entry − 0.5 × risk between entry and
   its journal exit exits at min(bar open, half stop) with the lot's own journal cost; the Primary −2R latch is
   re-applied (lots it would now block are removed; lots the live latch blocked cannot be added back — stated).
6. **Live replay:** every one of the 16 live NM-ETF-family days, per account/setup, with and without the rule.

**Proposal bar (fixed now):** Q50 (or a variant) is recommended as a plain Yes only if it (a) gives up <= 2R per year in
expectation on the 2-year bench, (b) keeps >= 90% of top-decile winners, (c) improves the worst day in FIT, T2 and
CHECK, and (d) sits on a plateau (neighbouring f and k/w also cut the tail at a similar price). Clearing the t-bar is
NOT required for an insurance rule, but any claim of R improvement must clear it. Otherwise Optional (price stated) or No.
