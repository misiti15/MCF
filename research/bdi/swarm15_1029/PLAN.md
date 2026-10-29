# swarm15_1029 pre-declaration: variant swarm on the 15 most-traded live setups

*Educational only - not financial advice.*

Written 2026-10-29 (during market hours: research only, nothing in config/, mcf/, setups, exits or the ledger changes;
nothing is committed) after the live ranking (`live_rank.py`) and **before any history configuration was scored**.

## 1. Selection (live paper, rule 7)
All run_id-1 trades 2026-10-06..10-28 in the five intraday accounts (Primary, Testing 1, Testing 2, Setup Generator,
Graveyard; `reports/<date>.csv` on the mcf-data* branches), S6 out, copies of one setup id across accounts merged.
GEN setups were eligible (largest: 44 trades, not in the top 15). Top 15 by trade count (`live_rank.csv`):
orl-p05 (666), pdl-p05 (616), orl-p05-lowvol (590), heat_fade_short-FD (479), coil-k4 (421), pdl-p05-lowvol (377),
orl-p10 (361), pdl-p10 (349), orl-p10-lowvol (329), pdh-p05-lowvol-short (320), pdh-p10-short (317), RW7-FD (275),
RW2-FD (260), LIQ-orl-sweep (206), L3-gap-slope-fromopen-FD (206; tie with LIQ at 206, both kept -> 15).
MF2-FD / RW5-FD / RW3-FD (another agent's stop/scale-out sweep) are not in the top 15, so the exclusion does not bind.

## 2. Harness, data, costs, splits
- Entries computed per month on the open two-year frames: CWT14 / coil kernels (top5_1016 `b3_any`, top5_1015 `_b4a`),
  LIQ and RW2 masks (top5_1019), heat_fade_short-FD score (top5_1015 / regime_9 formula), RW7-FD and L3-fromopen-FD live
  modules (`load_mod`, as gates1021). First signal per symbol-day except L3-fromopen-FD (LabStrategy refire chain,
  cooldown 1 bar, prefilter gap <= -2.657). Window / ADV / scale-out from each setup's *current* account config.
- Exits: the top5_1028 5-minute simulator (stop-first, x3 cost on the extended tier, target limits free, stops +2c,
  market exits 1c + 1 bp, entry 1c + 1 bp x time-of-day multiplier). Stop rows at the same $ risk (target price kept).
- Random control: same date and bar, adv20 >= 95M, same side and exit mechanics, 3 draws.
- **Locked block 2024-11-01..2025-02-28 never loaded.** TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15. HOLD
  (2026-04..06 + 2026-09-16..10-07) is simulated but not read unless a finalist beats its parent on TRAIN and VALID
  (shrunk avg R = m n/(n+20), and day-clustered t), then read once (one look per lineage).
- Parity: each parent's TRAIN+VALID expectancy is compared with the parent number of its last top5 run.

## 3. Grid (one knob per row, same rows for every setup; a row already scored on that setup in a previous
top5 / hf run is dropped before the run and listed in NOTES)
| id | family | knob |
|---|---|---|
| S1 S2 S3 | stop | stop x2.0 / x2.5 / x3.0 ATR-multiple at the same $ risk |
| T1 | target | target x2 of the parent target |
| T2 | scale-out | half off at the parent target, stop to break-even, runner to 2x the parent target |
| X1 | time stop | exit at 45 min if the trade never reached +0.05R |
| X2 | time stop | exit at 180 min if the trade never reached +0.25R |
| W1 | window | until 14:00 (setups with a 12:00 end: until 10:30) |
| W2 | window | from 11:00 |
| C1 | context | only when QQQ is on the trade's side of its VWAP |
| C2 | context | only when QQQ is against the trade's side of its VWAP |
| C3 | context | only when breadth agrees (long: breadth > 0.5; short: < 0.5) |
| C4 | context | only when SPY's open gap agrees with the side (long: SPY gap >= 0; short: <= 0) |
| C5 | context | skip after a big prior SPY day (abs prior close-to-close > 1.0%, known pre-open) |
| C6 | context | skip after a quiet prior SPY day (abs prior close-to-close < 0.3%) |
| R1 | re-entry | allow a second trade per symbol-day after a 60-min cooldown from the first exit (cap 2); L3: refire cooldown 12 bars |
| R2 | per-symbol / day cap | L3: cap 2 trades per symbol-day; others: first 10 signals per session |
| R3 | day cap | first 5 signals per session |
| K1 | cost floor | skip if entry-side cost > 5% of R (hf1027) |
| K2 | cost floor | skip if round-trip cost estimate > 10% of R |

Up to 21 rows per setup. N per setup and the full lineage N (backlog configs_tried for the lineage + earlier top5 grids
+ tonight) are reported. Bar for a pass: exp > 0 in TRAIN and VALID, beats the parent on TRAIN and VALID, the
TRAIN+VALID day-clustered t >= max(1.5, sqrt(2 ln N_lineage)), up and down sessions > 0, avg R without its best day > 0,
beats the random control; then one HOLD look. **Near-miss**: exp > 0 and beats the parent in TRAIN and VALID, t >= 1.5
but under the bar.

## 4. Live vs backtest
Live avg R (paper) vs the parent's TRAIN+VALID avg R; z = (live - backtest) / live day-clustered SE. z > +2: live far
better (likely luck); z < -2: live far worse (possible execution issue).
