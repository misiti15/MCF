# arena-mid-short (swarm 2026-10-17) - NOTES

*Educational only - not financial advice. History backtests only; nothing here is paper or live.*

## Failures first
- **No candidate passes. modules/ is empty.**
- I scored **30,595 configurations**, all SHORT with bar close 11:00-14:00:
  - 21,168 pairs (30 triggers x 80 live filters x 3 windows x 3 geometries, minus pairs on the same indicator)
  - 7,404 live triples and 2,000 research-only context triples (the top 100 pairs by train t, n >= 150, >= 60 sessions, x a third condition)
  - 23 plateau points around 3 near-misses
- **Lineage and bar**
  - Arena family N = 20,282 (screen) + 23,032 (am-long) + 30,773 (mid-long) + 22,932 (am-short) + 30,595 (this study) = **127,614**.
  - Bar = max(1.5, sqrt(2 ln N)) = **4.85**. Without am-short, which ran in parallel, N is 104,682 and the bar is 4.81.
- **Funnel**
  - 272 configurations passed the TRAIN screen gate (228 live).
  - 28 were positive on VALID with excess > 0 (19 live).
  - **0 pass quality_pass**. 5 fail only the t-bar (3 live), and their best TRAIN t is 1.71.
- **The up-session regime kills midday shorts.** This mirrors mid-long, where down sessions killed the longs.
  - Among live configurations with n_train >= 200, 17.4% have exp > 0 after costs on TRAIN, and 83.8% are positive in down sessions.
  - Only **2.5%** are positive in up sessions.
  - Only 10.3% of the train-gate survivors stayed positive on VALID.
- **TRAIN clears the bar only on down-session cells.** The configurations with t >= 4.85 on TRAIN (n >= 200, >= 60 sessions) are all trend-continuation shorts:
  - Examples: fromOpen <= -2.78% & dist_pdl_atr >= 1.02 & day_vs_prev_range <= 0.54, 11:00-12:30 t1s1 (+0.47R, n 655, t 5.06), and emaDiff <= -0.41 & dist_pdl_atr >= 1.02 & gap_atr <= -0.22.
  - All of them are **negative in up sessions** (-0.02..-0.15R) and carried by down sessions (+0.5..+0.7R).
  - They fail the regime gate, so per the plan they were never scored on VALID.
  - They would need a live market-state (day-class) gate, which the live runner lacks for lab setups. See the backlog idea below.

## Near-misses (NOT candidates; near_miss/ modules are labelled; VALID was used for the plateau, so it is no longer clean)
1. **AR-MIDS-abvwap-belowOR**: vwap_atr >= 0.336 & or_high_dist_atr <= -0.540 & emaDiff >= 0.142, 11:00-12:30, t1s1. The stock is above VWAP but more than 0.54 ATR under its opening-range high, on a short-term up-EMA bounce.
   - Train +0.133R (n 271, t 1.71). Valid +0.080R (n 251, t 1.29).
   - Excess over random: +0.23R on train, +0.15R on valid.
   - Regime: up **+0.026R**, down +0.233R. Walk-forward 0.71. 1.2 trades/day. 14 of 21 months positive.
   - Without the best day it is +0.09R.
   - Plateau: 5 of 7 neighbours fail the regime gate. The other geometries go negative in up sessions, and or_high_dist -0.40 is valid-negative. Tightening or_high_dist_atr to -0.77 improves up-session exp to +0.19R, but n is 148 and walk-forward 0.56.
   - Verdict: weak, regime-fragile. It is a spike, not a plateau.
2. **AR-MIDS-macdneg-abvwap-widerange**: macdPct < -0.297 & vwap_atr >= 0.163 & day_range_atr >= 0.983, 12:30-14:00, t1s05.
   - Train +0.070R (n 199), valid +0.034R (n 156). Up +0.018R, down +0.160R. Walk-forward 0.62.
   - Without the best day (2025-04-03, 82% of P/L) it is **+0.011R**.
   - Verdict: a spike.
3. The prev_range_atr >= 0.83 sibling of (2):
   - Train +0.154R (n 170), but valid only +0.008R. 2025-04-03 carries 64% of P/L.
   - Neighbours are valid-negative.
- Parity: the near-miss 1 module (mask + gates.lab_trades on a raw 2026-03 history frame, adv20 >= $95M) gives the same 23 symbol-days as the arena trades. R is +0.392 versus +0.388 for the arena; the difference is the arena's x3 extended-tier cost.
- Live support:
  - All indicators can be computed from the live LabStrategy frame (write_module accepts them as live).
  - The exits are standard lab geometries with a 15:55 timed exit. **No exit feature is missing.**
  - The live runner must apply the adv20 >= $95M universe, which is not inside mask().

## Backlog idea (NOT scored; for the lead)
- Midday trend-continuation shorts gated by a live day-class or market-down filter (for example the K3 day-class gate in the ledger, applied as "block unless trend_down").
- Every train t >= 4.85 cell here lives in down sessions. Only a gate that is known at decision time can make them tradable.
- Needs its own pre-declared study. VALID is clean for these configurations because none was scored on VALID.

## Split, costs, data
- Split: TRAIN = 2024-10 + 2025-03..2025-12 (234 sessions). VALID = 2026-01-01..2026-10 (192 sessions). The locked block 2024-11..2025-02 was never loaded.
- Costs: arena.data.outcomes, i.e. gates.prod_r with tod entry costs plus x3 on the extended tier.
- Random baseline: the same-minute universe mean (adv20 >= $95M, full universe).
- Trades: first bar per symbol-day. Statistics are day-clustered.
- Duplicates are counted as scored, which keeps N conservative. For example, the window 11:00-14:00 shares its first bars with 11:00-12:30, and triples repeat pairs in a different order.
- Resources: search.py took about 4 minutes, with RSS about 5.2 GB at load. Scratch (2.0 GB) was deleted.

## Files
- PLAN.md, common.py (the pre-declared space), build.py, search.py, plateau.py
- results.csv (every configuration: train stats, plus valid stats for gate survivors), stage3.json (evaluate_combo of the 28)
- plateau.json, counts.json, near_miss/*.py
