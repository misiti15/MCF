# arena-pm-both (swarm 2026-10-17) - NOTES

*Educational only - not financial advice. These are history backtests only. Nothing here is paper or live.*

## Failures first
- **No candidate passes. modules/ is empty.**
- **Configurations scored here: 61,479.** All entries are LONG or SHORT, with bar close 14:00-15:00. The frames end at the 15:00 close, so the declared 14:00-15:30 window is 13 decision bars.
  - Stage 1 pairs: 42,552
  - Stage 2 live triples: 14,888
  - Stage 2c research-only context triples: 4,000
  - Stage 4 plateau points: 39 (some of them are duplicates of the base, because of a float rounding in the edge lookup; they are counted anyway)
- **Lineage N.** The arena family totals 20,282 (screen) + 23,032 (am-long) + 22,932 (am-short) + 30,773 (mid-long) + 30,595 (mid-short, which ran at the same time) + 61,479 (this study) = **189,093**. The bar is max(1.5, sqrt(2 ln N)) = **4.93**. Without mid-short, N is 158,498 and the bar is 4.894; that is the N stage3.json used.
- **Funnel.**
  - 3,107 configurations passed the TRAIN screen gate (1,727 short, 1,380 long).
  - 454 of those were positive on VALID with excess > 0 (381 live).
  - 3 had combine.quality_pass = True (2 live, 1 context). **All 3 are artifacts of one or a few sessions, or of the period around the April 2025 tariff shock.**
    1. from_pc <= -2.32% & dist_pdl_atr >= 1.05 & sma50_dist_pct >= 0.02, short t1s1 14:00-15:00. Train +0.274R, t 9.0, n 553. **But 464 of its 677 trades are on 2025-04-10**, and that day carries 83% of the P/L. With that day removed, train is n 89, +0.113R, t 1.11, which fails. The day-clustered t breaks down when one session dominates both the mean and the sample. (Its VALID result, +0.147R on n 124 with day-weighted t 2.80, is interesting but thin.)
    2. gap <= -2.13% & dist_pdl_atr >= 0.46 & fromOpen_atr <= 0.016, short t05s1 14:00-14:30. 375 of its 766 trades are on 2025-04-10 (83% of P/L). With that day removed, train t is 1.65 and day-weighted train t is -0.39, so it fails.
    3. gap_atr <= -0.61 & dist_pdh_atr <= -0.15 & spy_ret3 <= -0.06 (**context, research-only**), short t05s1. VALID is +0.003R, which is zero, and the top 5 days carry 77% of P/L.
- **Rule-5 concentration re-check (robust.py).** It was added after the passes above were seen. It is a diagnostic only: no new configurations, so nothing is added to N.
  - 12 of the 454 stay positive with the best day removed on train AND valid, with the best-day share under 25%, a per-day cap of 10 trades positive on train and valid, up and down regimes > 0 with the best day removed, and walk-forward >= 0.6. 8 of the 12 are live.
  - Their best ex-best-day train t is 4.06, below the bar.
- **Stage 4 plateau, 3 bases (plateau.csv).** These are clearly NOT candidates; VALID was used for them, so it is no longer clean.
  - **NM-PM-S-gapdn-reclaim-pdh-fade** (near_miss/): gap_atr <= -0.614 & dist_pdh_atr <= -0.453 & rvol_day >= 0.839, short t1s1 14:00-15:00.
    - It is the one combine.quality_pass among the plateau points:
      - train +0.419R (n 125, 46 sessions, t 4.92)
      - VALID +0.186R (n 77, t 1.55)
      - excess over the same-minute random baseline +0.336 / +0.285R
      - up +0.29R, down +0.49R
      - walk-forward 1.0
    - **It fails, for three reasons:**
      - Its t of 4.92 is below the full-family bar of 4.93.
      - It was picked after VALID was seen.
      - It has n 202, 0.47 trades/day, and the top 5 days (2025-10-14, 2025-11-20, 2025-04-07, 2026-01-05, 2025-04-09) carry 65% of P/L. Without those days it is +0.17R.
    - Economic story: the stock gapped down more than 0.6 daily ATR, then by 14:00 rallied back above the prior-day high on heavy volume. The short is a fade of an exhausted reversal into the close.
  - **NM-PM-S-gapdn-above-pdh-rvol** (base, dist_pdh_atr <= -0.149):
    - train +0.320R (n 274, t 3.46), VALID +0.112R (n 173, t 1.36)
    - 1.05 trades/day, walk-forward 0.70, up +0.26R / down +0.33R
    - top 5 days hold 74% of P/L
    - The neighbourhood mostly holds. 9 of 11 neighbours are positive on train AND valid: looser gap, looser rvol, dropping rvol, other geometries, and 14:00-14:30. 14:30-15:00 is train-negative, and dropping either the gap or the pdh condition kills it.
    - This is the most plateau-like family found here, but it is driven by event days.
  - **NM-PM-L-belowvwap-orh-retest**: vwapDistPct <= -1.33 & or_high_dist_atr >= -0.19 & day_pos <= 0.196, long t1s1 14:00-15:00.
    - train +0.213R (n 168, t 4.56), VALID +0.046R (n 127, t 0.78), 0.69 trades/day
    - A spike, not a plateau: dropping any condition or moving day_pos is valid-negative, and the top symbols are leveraged/vol ETFs (BOIL, ETHU, SOXS, UVXY).
- **Regime asymmetry is the main obstacle, as it was for the siblings.** Among configurations with n_train >= 200:
  - long: 31.6% have exp > 0 on TRAIN, only 13.3% are positive in down sessions, and 73.3% in up sessions
  - short: 35.7% have exp > 0 on TRAIN, 71.2% are positive in down sessions, and only 20.9% in up sessions
- **Methodology warning for the lead: the day-clustered t (gates.summary) is unreliable when one session holds most of a configuration's trades.**
  - Raw train t reached 38 on configurations with 3-10 sessions, all in the April 2025 tariff week. The days >= 60 screen gate removes those.
  - Inside quality_pass, however, the 2025-04-10 cases still reached t 5-9.
  - Recommendation (housekeeping/gates, not done here): add a best-day-removed t, or a per-session trade cap, to combine.evaluate_combo gates.

## Split, costs, data
- TRAIN = 2024-10 + 2025-03..2025-12 (234 sessions). VALID = 2026-01-01..2026-10-07. The locked block 2024-11..2025-02 was never loaded.
- Costs: arena.data.outcomes, which is gates.prod_r with time-of-day entry costs plus x3 on the extended tier. The random baseline is the same-minute universe mean over adv20 >= $95M.
- One trade per symbol-day (the first qualifying bar). Statistics are day-clustered. Regimes come from history2y lib.regimes().
- Live: every near-miss uses only live-computable indicators and standard lab exits (t/s geometry on R = 0.25 x daily ATR, time exit 15:55), so **no exit feature is missing**.
- Module round trip: mask(df) + gates.lab_trades on raw frames for 2025-04 and 2026-03 reproduces the arena trades exactly (emit.json).
  - The long module's 2026-03 exp differs (+0.009 vs +0.034R) only because the arena applies x3 extended-tier costs.
- Resources: search.py peak RSS was about 2.6 GB; the whole run took about 5 minutes after a 5-minute build. Scratch was deleted.

## Files
- PLAN.md, common.py, build.py, search.py, robust.py, plateau.py, check_passes.py, emit.py
- results.csv (every stage 1-2 configuration), stage3.json, counts.json, robust.csv, check_passes.json + trades_1..3.csv (the 3 artifact passes), plateau.csv, plateau_counts.json, emit.json, near_miss/*.py
