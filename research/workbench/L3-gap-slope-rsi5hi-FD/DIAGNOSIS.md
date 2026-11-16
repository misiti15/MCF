# Diagnosis — Gap-Down Rebound Overbought Short (all day) `L3-gap-slope-rsi5hi-FD` (On Deck)
Educational only — not financial advice. Mechanic, 2026-11-16 (built during market hours: research files only, no config change).

Engine: `L3-gap-slope-rsi5hi-FD_engine.png` (P1..P25, blueprint `L3-gap-slope-rsi5hi-FD.md`). Live evidence = all 139 closed
live trades (On Deck 72, Testing A 45, Primary 22; 2026-10-13..11-16, 21 sessions; the brief's 138 / 20 excludes today's one
trade) and 1,214 live signals (753 = 62% blocked as not shortable/ETB). Live numbers are used to DIAGNOSE only; the pass decision
uses the identical backtests (RESULTS.md), never the live record (owner 2026-11-16).

**Rule changes inside the live window** (they mix into the live numbers, not into the backtests, which apply today's rules to
every day): Primary −2R per-setup latch (10-29), Testing cost filter 0.15R (CF, from 10-30), move Testing A → Primary (10-30),
Primary → On Deck/Testing 1 (TEAM-6, 11-11), LR1/LR3/LR5/LR7 + LR8 cost model (11-12), On Deck build (11-12). Live R also carries
fill drift: R = |fill − stop|, so a favourable fill shrinks the denominator (OKLO's +2.38R is a 0.5R target on a 1R that the
−108 bps fill cut from $0.54 to $0.24).

**The record leans on one day:** 11-12 = 38 trades +13.2R = 84% of total R (`1 day` tag); w/o it the live avg is +0.025R.

## The 10 trades (5 worst, 5 best) — what happened → part → what a small tweak would have done
| Trade | What happened | Part that caused it | Catalogue part | Tweak → this trade |
|---|---|---|---|---|
| TTMI 10-13 −1.30R (`_worst1_`) | 14:30 bar, short 14:31 @ 113.53, MFE +0.58R 15:05 (target 0.5R missed by cents after −20.7 bps fill drift), stop 15:38 | P6 late window + P23 target vs fill drift | Timer; Target | window 13:00 / max hold 60-75: skipped / cut ≈ flat. **WB4 still takes it** (cost/R 0.03, RSI 89, slope 0.64) |
| USAR 10-15 −1.20R (`_worst2_`) | 11:00 bar, RSI(5) = 100 (flat-top), 1R = $0.15 on $10.58 (stop-exit cost 0.26R), never better than +0.20R, stop in 9 min | P9 RSI at the extreme + P19 thin 1R | Sensors; Intake/cost | RSI ≤ 90 (WB3) or cost/R ≤ 0.05 (WB1): **not taken** (+1.20R) |
| NG 10-29 −1.18R (`_worst3_`) | 11:35 bar, RSI 92.6, 1R = $0.09 on $6.18 (cost 0.50R of R), MFE +0.11R, stop 13:08 | P19 thin 1R + P9 near-extreme | Intake/cost; Sensors | WB1 or WB3: **not taken** (+1.18R) |
| FMC 10-16 −1.18R (`_worst4_`) | 10:00 bar, RSI 57.8 → 100 in one bar, 1R $0.18 on $5.73 (cost 0.26R), +32.9 bps fill drift, stop in 10 min | P9 flat-top pop + P19 thin 1R | Sensors; Intake/cost | WB1 or WB3: **not taken** (+1.18R) |
| ARVN 11-10 −1.17R (`_worst5_`) | 12:55 bar, 1R $0.13 on $6.74 (cost 0.35R), MFE +0.16R, ground up to the stop at 15:43 | P19 thin 1R + P25 long hold | Intake/cost; Time exit | WB1: **not taken** (+1.17R); max hold 75: ≈ −0.4R |
| OKLO 10-20 +2.38R (`_best1_`) | 10:40 bar, −108 bps fill drift shrank 1R to $0.24, target in 55 min | works; R inflated by fill drift | — | WB1 (cost/R 0.085) and WB3 (RSI 90.9) **skip it** — the copy gives this one up |
| EWZ 10-26 +0.89R (`_best2_`) | RSI 100, slope 1.00, target in 22 min | works | — | WB1/WB3 skip it (cost/R 0.21 on the bench ATR) |
| ARM 10-13 +0.85R (`_best3_`) | RSI 80, cost/R 0.02, target in 54 min | works as designed | — | **WB4 keeps it** |
| RIOT 10-13 +0.84R (`_best4_`) | RSI 89, cost/R 0.14, target in 36 min | works | — | WB1 skips it |
| EMBJ 10-26 +0.79R (`_best5_`) | RSI 82, target in 25 min | works | — | WB1 skips it (bench ATR for EMBJ is far below live's — data outlier) |

Four of the five worst trades are thin-R (stop-exit cost 0.26-0.50 of R) and/or flat-top RSI bars; WB4 removes 4 of 5. It also
removes 4 of the 5 best — the honest cost of the copy (see the live check below).

## Across all trades (live 139, replay 327, 2-year 6,313) — which part is behind the losses
- **Intake / cost per R (P16/P19) — the clearest backtest pattern.** Stop-exit cost / 1R ≤ 0.05: replay +0.061 (210), TRAIN +0.032,
  VALID +0.032, FWD −0.009; 0.05-0.15: replay −0.08, TRAIN −0.014, VALID +0.006, FWD −0.10. Not only cost: gross R also rises
  (2y +0.028 → +0.046) — thin-R names are noisier, not just dearer. Live disagrees (kept 63 +0.071R vs dropped 75 +0.144R), but live
  R on thin names is the most distorted by fill drift (denominator), and pre-10-30 trades ran without the 0.15R filter.
- **Sensors — RSI(5) (P9).** RSI 70-80: replay +0.072, TRAIN +0.050; 90-100: replay −0.07, TRAIN −0.03/−0.05, FWD −0.08/−0.19.
  Live agrees: RSI > 90 entries 36 trades +0.019R vs ≤ 90 102 trades +0.144R. A cap (not a higher floor: RSI > 80 failed) helps.
- **Sensors — SMA20 slope (P11).** Slope > 1.0 (near-vertical rebound): replay −0.13/−0.26, VALID −0.01/−0.06, FWD −0.19/−0.13 —
  shorting a vertical run gets run over. Live neutral (15 trades +0.11R). → slope cap 1.0.
- **Timer / window (P6).** Live: entries 13:00-15:00 22 trades −9.9R (−0.45R/trade); replay 13:00-14:00 −0.51R/trade. But the 2-year
  says the afternoon is fine (13:00-15:00 TRAIN −0.04/+0.11, VALID +0.15/+0.09). The sibling's 13:00 cut does NOT transfer: V01 fails
  the 2-year (−0.013 vs +0.011). 09:50-10:30 is weak everywhere (−0.10 TRAIN, −0.16 FWD) but small.
- **Time exit / max hold (P25).** Trades still open after 30 min lose in every test (2y 30-45 min −0.08, 45-90 −0.2, > 90 −0.1 to −0.4).
  But a clock exit only converts those into smaller losses AND cuts the late targets: max hold 30/45/60/75/90 all lift the replay
  (+0.04..+0.06) and all lose 0.01-0.02R on the 2-year (VALID worst). The sibling's 75-min max hold does NOT transfer.
- **Stop (P22) / Target (P23).** 2y stops avg −1.04R, 24% had MFE ≥ 0.3R first, 12% ≥ 0.4R (target 0.5R). Stop 0.5R (t05s05) fixes the
  replay (+0.063) and fails the 2-year (−0.004); target 1R (t1s1) lifts the 2-year (+0.042) but the replay worst day goes −21 → −52R.
- **Refire / lots (P8/P13).** Cooldown 12 or 1 lot per symbol help a little in both (lots per symbol is account-wide, tool only).
- **Gates (SPY after 09:50).** Skip SPY > +0.30% or < −0.30% since 09:50: both fail (2y −0.019 / −0.004). No market-state part helps.
- **Day type (2y, SPY open→close):** up −0.043, flat +0.075, down +0.063 — losses are on up days, not fixed by a gate visible at entry.
- **Tail:** 2y worst day 2025-03-04 −122R (246 trades), 2025-11-07 −77R; best 2025-04-07 +164R. The parent's 2-year record is carried by
  04-07 (best-day share > 100%).

## Candidates chosen (each ONE part) and why
1. **WB1 — P16/P19 cost/R ≤ 0.05** (module clause): strongest in both tests; 4 of the 5 worst live trades.
2. **WB2 — P11 slope cap 1.0**: near-vertical rebounds lose in replay, VALID and FWD.
3. **WB3 — P9 RSI(5) cap 90**: flat-top / parabolic bars; the one cap live also confirms.
4. **WB4 — WB1 + WB2 + WB3** (config X10): best of the combos in both tests and every 2-year split; neighbours (cost 0.075, slope 0.85,
   RSI 85, + start 10:30, + price ≥ $20, + volume ≤ 2.5×) score within ±0.02R — a plateau, not a spike.
Not kept: the sibling's two parts (13:00 cut, 75-min max hold) — replay-only gains, 2-year losses; stop 0.5R, target 1R, SPY gates,
RSI > 80, gap ≤ −3.2, slope > 0.70, cooldown 3, 1R × 1.2 (RESULTS.md).
