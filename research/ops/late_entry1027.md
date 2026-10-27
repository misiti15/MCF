# LATE-CUT - late entries per setup, do-no-harm (owner 2026-10-27)

*Educational only - not financial advice. Backtests (two-year history) and live paper results are labelled
separately. NOTHING here is implemented: no config, window or engine change.*

Owner: Primary live entries after 14:00 ET mostly end at the 15:55 flatten. "Not too drastic, don't handicap setups;
only find edge or limit bad opportunities where a setup needs time to work but wouldn't get it." Per setup only -
never a blanket cutoff.

## 0. Pre-declaration (written 2026-10-27 before any late bucket was scored)

### 0.1 Data
- Setups: every setup of Primary, Testing 1 and Testing 2 (docs/live/assignments.json, 2026-10-27 evening, i.e. with
  tonight's three Primary -> Testing 2 moves) that the two-year lab harness covers: **51 setup ids** (8 Primary,
  43 Testing 1 / 2; the uncovered ones - CWT, IDX, LD, LIQ, RW6G1, orb20_a, intraday_momentum, NM-ETF - have no
  live-shaped two-year list and stay unchanged).
- Trades: `research/ops/late_entry1027/build_cache.py` - the gates1021 scan code (live mask, window capped 09:50..15:00
  as live, min_adv point-in-time, refire chain), costs in (production costs + time-of-day entry costs, 3x extended
  tier), plus the 5-minute exit bar of every trade (stop first inside a bar). Open history 2024-10..2026-10-07; the
  locked block 2024-11-01..2025-02-28 is never read. Train <= 2025-12-31, valid 2026-01-01..2026-10-07.
- Exit kind: target (win = 1), stop (gross R at the stop), else held to the 15:55 flatten. Time to exit = exit bar -
  entry bar; a bracket hit after 15:00 is "15:05-15:55" (frames end at 15:00, the outcome itself walks to 15:55).

### 0.2 Configurations
Per setup: cutoff C in {13:30, 14:00, 14:30} (late = entry bar close after C) x action {skip late entries, half size
late} = 6 per setup, **N = 51 x 6 = 306**. Bar = max(1.5, sqrt(2 ln 306)) = **3.38** (day-clustered t).

### 0.3 Pass rule (all must hold; anything else = setup unchanged)
1. Late n >= 30 on the open history.
2. Late avg R < the same setup's earlier (<= C) avg R in train AND in valid.
3. Late sum R < 0 in train AND in valid (cutting raises the setup's total R in each split: it removes losing / flat
   trades, not winners).
4. Day-clustered t of the improvement (per-session sum of -late R) >= 3.38.
5. Plateau: the neighbouring cutoff(s) also have late sum R < 0 on the full history.
Skip and half size share conditions 1-5 (half size gives half the improvement at the same t); if a setup passes,
the gentler half-size form is what would be proposed unless late avg R is <= -0.10R.

### 0.4 Also reported (information)
Per setup: time-to-exit distribution (median minutes to target / stop, share held to 15:55) by entry hour; avg R by
entry hour (train / valid); live paper late entries (>= 14:00) by setup across all accounts.

## Results (scored 2026-10-27, after section 0 was written)

**Configurations: N = 306 as declared** (51 ids x 3 cutoffs x 2 actions; 50 ids have two-year trades, 31 have any
entry after 13:30 - the other 19 already stop earlier, e.g. NS1 / NS5 / MF4 window versions). Bar 3.38. 244,874
backtest trades, 426 open sessions. Code: `late_entry1027/build_cache.py` (trade lists, scratch), `late.py` ->
`late_out.txt`, `results.csv` (every setup x cutoff), `by_hour.csv`, `exit_time.csv`; `robust.py` -> `robust_out.txt`.

### Verdict first: no per-setup cutoff to propose (no decision)
- **One row meets the pre-declared rule, at the margin, and it is not a late-entry effect.** Big Gainer Dip-and-Pop
  (all day) `NS1-rsidip-rsi5pop-long-FD` (Testing 1), cutoff 13:30: late 891 trades -0.086R vs earlier -0.068R
  (train) / -0.057R (valid), late sum -34.2R train / -42.1R valid, improvement t **3.385 vs bar 3.38**, neighbour 14:00
  late sum also < 0. But:
  - late is NOT clearly worse than its own earlier entries: late - early -0.025R, session-clustered **t -0.74**
    (train -0.42, valid -0.59), and at 14:00 / 14:30 the late entries are BETTER than earlier ones (+0.033R / +0.046R).
    The bad stretch is 12:00-14:00 (13:00-13:30 -0.127 / -0.159R; 13:30-14:00 -0.175 / -0.140R), not "too late to work".
  - the whole setup loses on two years (2,490 trades, -0.070R, -173.6R; win 63% early vs 56% late). Rule 4 tests
    "late R < 0", which any losing setup meets when the sample is large; the cutoff would trim a losing setup, not fix
    a late-entry problem. Its live late entries: 5 trades -0.106R vs 26 earlier -0.104R (the same).
  - So it fails the owner's own criterion ("clearly worse than that setup's own earlier entries"). **Reported, not
    proposed.** This is a flaw in the pre-declared rule (rule 4 needed a late-vs-early test); fixed for any re-run:
    require the late - early t <= -bar as well.
- **Primary (8 setups): nothing to change.** After 14:00 (two-year, late vs earlier avg R):
  | Setup | late n | late avg R | earlier avg R | train late / early | valid late / early | 15:55 share late | verdict |
  |---|---|---|---|---|---|---|---|
  | Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` | 891 | -0.063 | -0.039 | +0.008 / -0.036 | -0.127 / -0.042 | 39% | train late better - unchanged |
  | Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` | 635 | -0.107 | -0.083 | -0.102 / -0.121 | -0.114 / -0.045 | 43% | train late better (diff t -0.76) - unchanged |
  | Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` | 719 | -0.080 | -0.070 | -0.088 / -0.096 | -0.071 / -0.041 | 68% | train late better - unchanged |
  | Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` | 783 | -0.069 | -0.058 | -0.109 / -0.045 | -0.030 / -0.072 | 66% | valid late better - unchanged |
  | RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` | 114 | **+0.149** | +0.008 | -0.064 / -0.061 | +0.303 / +0.046 | 63% | late is its best part - unchanged |
  | Early Sellers, Strong Heat `MF4-h40-open-flowsell`, Big Gainer Dip-and-Pop `NS1-rsidip-rsi5pop-long`, Big Loser Flush Buy `NS5-sma50-flush-oversold-long` | 0 | - | - | - | - | - | windows already end before 13:30 |
  The four Primary shorts lose or are flat on two years at every entry hour (late is about as bad as early); a cutoff would not make
  them work and is not a do-no-harm late fix. ST7-FD's late entries are where its edge is - a blanket cutoff would
  have cut it.
- **Near misses (watch, not proposed):**
  - `ST4-emadn-long-am-t1s05-FD` (Testing 1; no display name in setup_names) 13:30: late 629 trades -0.069R vs earlier
    +0.002 (train) / +0.143 (valid); skipping late would take the setup from +22.2R to +65.6R; late - early t -3.44
    (valid -3.29, but train only -1.08); improvement t 2.11 < 3.38. The closest thing to a real late effect. Re-check
    on forward sessions.
  - Sellers into Strength (all day) `MF5-flowsell-vwapup-rsi5hi(-FD)` 14:00: late 482 -0.115R vs -0.053R, t 3.02 < 3.38,
    late - early t -1.51; the whole setup is -0.057R.
  - Pre-declared conditions met: c1 (n >= 30) 93 / 150 rows, c2 (late worse in train AND valid) 17, c3 (late sum < 0
    in both) 36, c4 (t >= 3.38) 4, c5 (plateau) 53; all five: 1 (above).

### Time to work (two-year, all 51 setups pooled; information)
| Entry hour | n | target | stop | held to 15:55 | avg R |
|---|---|---|---|---|---|
| 09:50-11 | 69,429 | 48.6% | 40.9% | 10.5% | -0.047 |
| 11-12 | 45,945 | 43.0% | 38.8% | 18.2% | -0.065 |
| 12-13 | 37,552 | 37.8% | 34.2% | 28.0% | -0.053 |
| 13-14 | 42,908 | 33.1% | 28.7% | 38.2% | -0.036 |
| 14-15 | 49,040 | 28.5% | 20.9% | 50.6% | **+0.012** |
- Late entries do run out of time (half end at the flatten), but those flatten exits are not worse on average: the
  14:00-15:00 bucket is the best hour pooled (train +0.033 / valid -0.007). Median minutes to target per setup run
  5-65 (80th percentile 25-125; `late_out.txt`): the slow ones (RW1 / RW3 / RW5 / RW7 / MF3 / MF5, 55-65 min median,
  120+ min p80) are the ones whose late entries mostly flatten, but they lose overall (-0.05..-0.08R/trade), late or not.
- Live paper (owner's figure reproduced): Primary entries >= 14:00 through 10-26: 56, 37 at the 15:55 flatten,
  journal R -0.007 (after costs -0.026R) vs earlier entries -0.038R; with 10-27: 66 entries, +0.012R after costs.
  Late entries are not worse than Primary's earlier entries live either.

### Caveats
- Lab frames stop at 15:00 (no entries after 15:00 exist live either: windows are capped at 15:00); a bracket hit
  after 15:00 has no exact minute. Late-session spreads were never measured (cutoff/NOTES.md); 1.0x entry cost after
  10:30. Survivorship as RESCORE.md. The rule-19 locked block was not read; no holdout was scored (nothing passed).
