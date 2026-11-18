# DIPTURN — the owner's 'dip in the first 20 min, then a turn' as a day-level condition on setup trades (FROZEN 2026-11-14 23:30 ET, not scored)
Educational only — not financial advice. Plan by Scout for Builder to score AFTER SIZESTOP (Lead lead-20261114-2300-1; owner anchor
rule 2026-11-14; Skeptic skeptic-20261115-0351-2). Research only; no setup or live change.
Why through setups: ANCHOR950 showed no LARGE index effect after 09:50 but cannot resolve small ones (SPY +6bps on dip-then-turn
days would need ~5,500 sessions). Setup trades give many trades per day. They are still day-clustered (~5 trade-equivalents per
session at ICC 0.19), so the day is the unit.

## Day condition (ANCHOR950's definitions, unchanged; known at 09:50:00 ET)
SPY 5-min bars: early range H20 / L20 = high / low of the 09:30..09:45 bars; P = open of the 09:50 bar; pos = (P - L20) / (H20 - L20).
- **DT (dip-then-turn):** L20 <= open_0930 - 0.25 x (H20 - L20) AND pos >= 0.6.
- **PF (pop-then-fade, mirror):** H20 >= open_0930 + 0.25 x (H20 - L20) AND pos <= 0.4.
## Trades (2-year lab lists, all entry times, as MOMSIDE Amendment 2: bt_lab1104 full-day, build_full.py)
Only trades whose entry bar starts AFTER 09:50 (the lab generator window already starts at 09:50; the assert stays).
- **C1:** LONG setups' trades on DT days.   **C2:** SHORT setups' trades on PF days.   (2 configs)
Locked block absent (asserted). TRAIN <= 2025-09-30 < VALID (VALID = the primary test; TRAIN is thin after the gap).

## Score (the guild standard for a day-level condition)
Unit = setup-day. For each config: the condition's trades vs a **shared-day random control**: draw the same NUMBER of days at random
from that period's sessions, ONE day permutation shared by all setups per draw (Skeptic's GAP-U fix; the condition is index-level),
500 draws. Statistic = mean ex-market GROSS R per trade on condition days minus the same on the random days, plus a day-clustered t of
the per-day summed excess over each setup's own mean (pooled ratio estimator, checklist #39).
Ex-market = gross - TRAIN beta per setup x side x SPY over each leg's own hold. Also print net, ATR beside R (checklist 15), per-setup /
per-family better / worse with the top-5 setups' share, w/o best day, the number of condition days per period, and SPY's
09:50 -> close on those days (ANCHOR950 row).
## Counting, bar, pass
Family market-state 2,605 + up-day track (LEAD20 1, ETFTIER 2, SHORTUP 1) + 2 = **2,611 -> BAR90 3.57**.
Pass (a lead for an arena field test only; any change is the owner's): ex-market excess > 0 with day-clustered t >= 3.57 in VALID, > 0 in
TRAIN, beats the shared-day null's 95th percentile, >= 60% of setups better, w/o best day > 0. Otherwise closed. No grid over the
0.25 / 0.6 / 0.4 thresholds or the 09:50 time.
Prior, stated: REGSW-2 / RCOMPASS v2 found trades AGAINST the morning state do no worse (SPY reverting to its open), so a dip-then-turn
morning is not obviously good for longs. The honest expectation is ~0.

## Amendment 1 (2026-11-15 01:20 ET, before any score; Skeptic skeptic-20261115-0550-1, Lead lead-20261115-0100-1; 0 configs)
1. Tie at 09:50 (checklist 2): lab tod is the bar END. A trade with tod 950 is entered at the close of the 09:45-09:50 bar, the same
   instant as the 09:50 reading. Only trades with lab tod >= 955 are scored; the number of trades this drops is printed per config.
2. The minimum detectable effect is printed beside the result (guild standard 2026-11-15): MDE80 = 2.8 x SE of the pooled day-clustered
   estimate, and MDE at the bar = (3.57 + 0.84) x SE. Expected size from Skeptic's scaling: ~65 DT days in VALID -> MDE ~0.08R per
   trade at the bar. A 'closed' result is worded 'nothing above X; smaller unknown'.

## Amendment 2 (2026-11-15 ~06:25 ET, BEFORE any score; checklist #42, Skeptic skeptic-20261115-0951-2, Lead lead-20261115-0500-1; 0 configs)
Early-close sessions dropped entirely: 2025-07-03, 2025-11-28, 2025-12-24 (the 2024 half days lie in the locked block). The 1-min
cache carries after-hours prints after the 13:00 close (SPY 164 bars on 11-28), so the lab window (entries to 15:00, flat 15:55)
placed fills after the close. Outcome-free count on the full-day lists: 4,843 trades on those days (0.41%), 2,023 with entry or
exit after 13:00. Dropping the whole sessions is simpler and stricter than dropping only the after-13:00 trades.

## Pre-registered reading of the result (author, 2026-11-15 13:20 ET, before any score; complements Skeptic's audits in roles/skeptic.md)
| Pattern | Reading | Next step |
|---|---|---|
| C1 excess ~0 (inside +-MDE) | The owner's dip-then-turn morning does not help long setups. Say 'nothing above X R'. | Close; give the owner the MDE line. |
| C1 excess > 0 but it equals beta x SPY 09:50->close on those days (ex-market ~0) | Index direction, not selection: the same as ANCHOR950's +6bps. | Close; the index part is already reported. |
| C1 ex-market excess > 0, t >= 3.57, VALID + TRAIN, >= 60% setups better | Long setups do better on dip-then-turn mornings beyond beta. | Arena field-test plan for a long-only 'DT-day' tag (owner decision). |
| C1 > 0 below the bar but positive in every split | Hint only. | Forward e-process shadow tagging DT days live; no new configs. |
| C2 (shorts on pop-then-fade) mirrors C1 | Symmetric early-swing effect. | Report both. Any plan must name both sides. |
| C1 < 0 (longs worse on DT days) | Consistent with REGSW-2 / RCOMPASS v2 (counter-state trades do no worse; SPY reverts toward its open). | Close; note the sign. |
| Top-5 setups carry > 50% of the excess | Not a book-wide condition. | Per-setup notes only. |
