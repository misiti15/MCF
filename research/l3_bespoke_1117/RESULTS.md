# L3 bespoke review 2026-11-17: results

*Educational only — not financial advice.* Research only: no config, setup, exit or latch change. The −2R latch stays
as it is (owner: "leave the −2R latch for now").

Setup: `L3-gap-slope-fromopen-FD` ("Gap-Down Recovery Fade (all day)", Primary). Plan fixed before any scoring:
PLAN.md (committed first). **43 configurations tried** (14 latch levels, 8 time/day-type latch rules, 21 Workbench
one-knob variants). Bar: max(1.5, sqrt(2 ln 43)) = **2.74**. Lineage bar, counting the earlier L3 runs (13 + 46 + 42 +
latch review 10), N = 154: **3.17**. Locked block 2024-11-01..2025-02-28 not read (asserted). Costs: LR8 in the engine;
R after costs (cost_r) in the live journals.

Evidence: **live** = Primary journal 10-21..11-17 plus On Deck 10-13..10-29 (378 paper fills + 42 post-latch what-ifs).
**Replay** = the Workbench engine on the live sessions, extended here to 11-17 (25 sessions). **2-year** = the same
engine on 2024-10..2026-11-04 (436 sessions; TRAIN ≤ 2025-12-31, VALID ..10-05, FWD ..11-04). The engine applies the
latch the way the runner does (latched on the day's running low). The earlier Workbench book re-armed, so the parent
baseline here is 354 / +0.136R in the replay and 4,242 / −0.052R over 2 years, not 350 / +0.059R and 4,885 / −0.048R
(NOTES.md).

## Verdict
- **No config passes.** No decision codes were added. The −2R latch stands.
- **Latch level:** −2 sits inside a flat region. **Do not loosen it.** Below −2 the 2-year VALID loses 16-64R. Above
  −2 (−1.0 / −1.25) the 11-12 day is lost: +31R live. Details in Test A.
- **Morning vs afternoon:** the edge is in the **morning**. AM entries make +0.31R/trade live and PM entries +0.04R.
  In the replay, AM is +0.19R and PM is −0.17R. Lifting the latch in the afternoon (B1) is the worst rule tried. Only
  one rule is promising: **B6**, latch −3 instead of −2 when SPY at 10:00 is below its open. It improves the 2-year
  (TRAIN, VALID, FWD) and the replay, with t 2.46. That is below the 2.74 bar, and it is neutral to slightly negative
  live.
- **Workbench:** no variant clears validation. The closest is C05, stop 1.25R. It is better in TRAIN, VALID and the
  replay, but its t is 1.17, its worst 2-year day is −40R against −29R, and each loss is bigger: the opposite of the
  ask. The best "bigger gains" shape is C02, target 1.5R: avg win +1.12R vs +0.90R, replay +0.189R vs +0.136R. It is
  worse in TRAIN, so it is not stable.

## Rule changes inside the windows (ledger)
- Primary sizing ~$4-5k: 10-28.
- Primary −2R per-setup latch (ST-P): 10-29.
- LL-LATCH (latched, not re-armed): 10-23.
- L3 re-promoted Testing 1 → Primary: 10-30.
- TEAM-6: 11-11.
- LR3 (latch and halt count R after costs) and the LR8 cost model: 11-12.
- WB4 copy in Testing A: 11-17 (8 fills, −2.4R raw on its first day; description only).

The live record mixes the two latch regimes. Primary had no latch before 10-29, and On Deck had one only on 10-20..10-22.
Live R uses R after costs throughout. Engine tests apply today's rules to every session.

## Test A: latch level grid (−1.00..−4.00 step 0.25, plus none)
**Mechanics: the latch moves in steps.** A full stop costs about −1.04R in the 2-year test (median; p10 −1.12) and
−1.11R live (p10 −1.25). So a level does not set a precise loss amount. It sets **how many full stops the setup may take
before the latch**:

| band | levels | effectively | live Primary trades / R | 2-year trades |
|---|---|---|---|---|
| 1st stop | −1.00 | latched after one loss | 92 / +9.1 | 3,277 |
| 2nd stop | −1.25 · **−1.50 · −1.75 · −2.00** | today's rule (−1.75 = −2.00 in every live day) | 148 / +38.6 at −1.5..−2 (−1.25: 101 / +7.6) | 4,153-4,242 |
| 3rd stop | −2.25 · −2.50 · −2.75 · −3.00 | | 150-151 / +40.4-42.7 | 4,894-5,194 |
| 4th stop | −3.25 · −3.50 · −3.75 · −4.00 | | 157-177 / +36.2-41.4 | 5,801-6,157 |
| none | — | | 198 / +32.8 | 10,909 |

Distinct thresholds: in the live record, −1.50, −1.75 and −2.00 are identical. So are −2.50, −2.75 and −3.00, and so
are −3.75 and −4.00. Over 2 years, −1.25 → −1.50 → −1.75 → −2.00 change only 15, 7 and 3 of 436 days. The real
choices are "after 1, 2, 3 or 4 stops" (A_engine.csv `days_differ_vs_next_tighter`, A_live.csv).

R without the best day, minus the −2 figure (A_plateau_vs_m2.csv; chart `latch_curve.png`):

| level | 2y TRAIN | 2y VALID | 2y FWD | replay | live Primary | live Primary + On Deck | 2y t vs −2 |
|---|---|---|---|---|---|---|---|
| −1.00 | +8.9 | +28.6 | +16.4 | −1.7 | **−14.9** | **−43.8** | 0.60 |
| −1.25 | +8.1 | +20.3 | 0.0 | +0.1 | **−16.4** | **−28.8** | 1.77 |
| −1.50 | +2.7 | +6.4 | 0.0 | −2.6 | 0.0 | +2.1 | 1.65 |
| −1.75 | +1.2 | +2.9 | 0.0 | 0.0 | 0.0 | 0.0 | 1.17 |
| **−2.00** | 0 | 0 | 0 | 0 | 0 | 0 | — |
| −2.25 | −4.6 | −16.0 | +2.7 | −3.3 | +1.9 | +1.9 | −0.04 |
| −2.50 | +0.4 | **−34.8** | +0.3 | −1.5 | +4.1 | +4.1 | −0.32 |
| −3.00 | +0.7 | **−43.0** | +4.5 | +0.8 | +4.1 | −0.1 | −0.38 |
| −3.50 | −8.3 | **−42.4** | −0.1 | +30.6* | −2.4 | −6.6 | −0.45 |
| −4.00 | +23.8 | **−64.0** | −9.3 | +30.1* | +2.8 | −2.5 | −0.39 |
| none | −68.9 | −102.5 | −21.4 | −21.8 | −5.8 | −12.2 | −0.76 |

\* The replay gain at −3.25..−4.00 is one session. On 11-12 the replay latched at −2 and would have made +36R with 4
stops allowed. Live never latched that day (+31R). Without 11-12 the gain is +7R over 24 sessions.

**Plateau check (PLAN rule: beat −2 in TRAIN, VALID and live; both neighbours too; t ≥ 2.74): no level passes.**
- Looser levels (−2.25..−4): live is +2 to +4R from 2 days (10-22 and 11-09), but the 2-year VALID loses 16-64R. This
  matches the board-wide latch review.
- Tighter levels (−1.0 / −1.25) are slightly better over 2 years (t 0.6 / 1.8). They would have cut the setup's best
  live day (11-12: −0.01R instead of +31R), because one stop plus a small loss latches it. That is exactly the "flex"
  the owner wants kept.
- −1.50..−2.00 is a **flat plateau** (it is the same rule: latch after the 2nd full stop), and −2 sits inside it.
  **Precise per-setup level: keep −2.** Writing it as −1.75 or −1.85 would change nothing live and almost nothing over
  2 years.

## Test B: morning vs afternoon, day type (B_time_daytype.csv, B_latch_rules.csv)
**Entry time.** Cap on, no latch, so every signal the book can hold:

| entries | live Primary + On Deck | live Primary | replay | 2y TRAIN | 2y VALID | 2y FWD |
|---|---|---|---|---|---|---|
| AM 09:50-11:59 | 283 tr **+0.306R** (20 days) | 121 tr +0.257 | 449 tr **+0.194** | −0.022 | −0.046 | +0.031 |
| PM 12:00-15:00 | 95 tr **+0.039R** (15 days) | 35 tr +0.270 | 270 tr **−0.173** | −0.060 | −0.023 | −0.045 |

Live, the 11:00-11:59 half-hours carry the setup (204 trades, +68R). 13:00-14:59 lost: 35 trades, −12.8R. The 2-year
AM/PM gap is small and flips between TRAIN and VALID. The afternoon weakness is real in the recent sample, and the
existing WB4 copy (window ends 13:00) is already testing it in Testing A.

**Day type** (SPY open→close ±0.25%; reporting only). Over 2 years: up days −0.171R (5,199 trades), down days +0.096R,
quiet days +0.080R. All of the 2-year loss is on up days, as UPDAY found. Live is the reverse so far: up days +0.28R
(9 days). Point-in-time, SPY at 10:00 vs its open: in the 2-year test a **strong start** (≥ +0.25%) is the worst bucket
(−0.082R; TRAIN −0.114, VALID −0.072). Live, the strong-start days were the best ones (+0.44R, 6 days; 10-20 On Deck
+33.6R and 11-12 +31.0R carry it).

**Latch rules** (configs; Δ total R vs the −2 parent):

| rule | replay | 2y TRAIN | 2y VALID | 2y FWD | 2y t | live Primary | live P + OD | call |
|---|---|---|---|---|---|---|---|---|
| B1 AM −2 / PM none | −30.5 | −117.7 | −66.5 | +0.2 | −1.01 | −6.9 | −6.9 | fail (worst) |
| B2 AM −2 / PM −3 | −1.3 | −29.9 | +0.5 | +15.8 | −0.25 | 0 | 0 | fail |
| B3 AM −2 / PM −4 | −1.9 | −53.3 | +3.8 | +26.9 | −0.33 | −2.3 | −2.3 | fail |
| B4 AM none / PM −2 | +32.1 | +48.3 | **−67.5** | −11.5 | −0.23 | +1.1 | −5.3 | fail (VALID) |
| B5 AM −3 / PM −2 | +4.8 | −2.8 | −39.5 | +4.5 | −0.76 | +4.1 | −0.1 | fail |
| **B6 −3 if SPY 10:00 < open** | **+2.8** | **+10.4** | **+34.0** | **+12.8** | **2.46** | 0.0 | −4.2 | **promising, below the bar** |
| B7 −1 if SPY 10:00 ≥ +0.25% | −9.3 | +12.6 | −11.0 | 0 | 0.05 | −31.7 | −64.2 | fail |
| B8 none if SPY 10:00 < open | −57.4 | +44.8 | −8.0 | −12.5 | 0.20 | +1.5 | −4.8 | fail |

B6 allows a 3rd stop only on mornings when the market is already weak, which is a tailwind for a short. It is the one
time or day-state rule with a consistent sign in the engine. Over 2 years it adds +57R, and R without the best day
improves from −255.7 to −198.4. It still misses the bar (2.46 < 2.74). Live it has not mattered: there was no
weak-start Primary day where the latch was the binding limit. **Not proposed.** It can be re-scored when more live
sessions accrue, or folded into the bespoke-rules evidence pack.

## Test C: Workbench Mechanic pass (21 one-knob variants; −2 latch; C_workbench.csv, C_verdicts.csv)
Guards (2-year): ≥ 70% of trades kept and ≥ 90% of the parent's top-decile winners kept. Selection on TRAIN, then
VALID, the replay and the t bar.

| variant | replay avg R | 2y avg R | TRAIN / VALID / FWD | avg win / avg loss (2y) | worst day 2y | 2y t | verdict |
|---|---|---|---|---|---|---|---|
| **PARENT** | +0.136 (w/o best +0.085) | −0.052 (w/o best −0.062) | −0.079 / −0.043 / +0.078 | +0.89 / −0.96 (0.93) | −28.8 | — | — |
| C01 target 1.25R | +0.167 | −0.042 | −0.065 / −0.047 / +0.151 | 1.10 | −26.8 | 0.80 | fails VALID |
| C02 target 1.5R | **+0.189** | −0.049 | −0.107 / −0.017 / +0.136 | **+1.16 / −0.95 (1.23)** | −25.0 | 0.75 | not selected (TRAIN worse) |
| C03 target 2.0R | +0.160 | −0.049 | −0.115 / −0.020 / +0.189 | 1.38 | −23.8 | 0.82 | guard (85% of top decile) |
| C04 stop 0.8R | +0.115 | −0.043 | −0.070 / −0.028 / +0.032 | 1.11 | −21.9 | 0.57 | fails replay |
| **C05 stop 1.25R** | **+0.146** (w/o best +0.100) | **−0.027** (−0.038) | −0.058 / −0.014 / +0.101 | +0.89 / **−1.11** (0.81) | **−40.3** | 1.17 | **promising, below the bar**; bigger losses |
| C06 BE after +0.5R | +0.132 | −0.037 | −0.060 / −0.025 / +0.054 | 1.69 | −27.7 | 0.79 | fails replay |
| C07 BE after +0.75R | +0.135 | −0.037 | −0.050 / −0.039 / +0.075 | +0.90 / −0.76 (1.19) | −28.3 | 1.28 | fails replay (meets it) |
| C08 stop −0.5R after +0.5R | +0.129 | −0.042 | −0.067 / −0.031 / +0.062 | 1.11 | −27.0 | 0.84 | fails replay |
| C09 60-min stop if MFE < 0.25R | +0.098 | −0.045 | −0.072 / −0.038 / +0.085 | 1.01 | −23.4 | 1.01 | fails replay |
| C10 max hold 75 min | +0.055 | −0.039 | −0.058 / −0.033 / +0.060 | 0.94 | −23.4 | 0.67 | fails replay |
| C11 30-min stop if MFE < 0.25R | +0.070 | −0.043 | −0.068 / −0.033 / +0.067 | 1.10 | −23.3 | 0.50 | fails replay |
| C12 half 1R / half 2R, BE | +0.149 | −0.048 | −0.086 / −0.036 / +0.143 | 0.92 | −27.8 | 0.94 | not selected |
| C13 half 0.5R / half 1.5R, BE | +0.120 | −0.022 | −0.037 / −0.013 / +0.040 | 0.49 | −25.1 | **1.77** | fails replay |
| C14 trail 0.75R after 1R, cap 3R | +0.117 | −0.059 | −0.097 / −0.049 / +0.161 | 0.89 | −26.8 | −0.07 | not selected |
| C15 fromOpen ≤ 9.75 | +0.143 | −0.046 | | | −31.6 | 0.73 | guard (83%) |
| C16 vwapDist ≤ 4.0% | +0.179 | −0.042 | | | −26.1 | 1.03 | guard (73%) |
| C17 volumeRatio ≤ 1.24 | +0.114 | −0.044 | | | −26.5 | 0.64 | guard (66%) |
| C18 rsi5 ≥ 38.8 | +0.106 | −0.046 | | | −25.2 | 0.89 | guard (83%) |
| C19 1R ≥ 0.5% of price | +0.136 | −0.046 | −0.062 / −0.049 / +0.088 | 0.94 | −28.8 | 1.11 | fails VALID |
| C20 no re-entry after a stop (BEZ case) | +0.137 | −0.051 | | | −26.9 | 0.42 | guard (86%) |
| C21 ≤ 2 lots per symbol | +0.156 | −0.052 | | | −29.1 | 0.83 | guard (77%) |

Reading it for the owner's aim (fewer losses, bigger gains):
- **Bigger gains:** a wider target (C02, 1.5R) is the cleanest shape change. The avg win rises from +0.90 to +1.12-1.16R
  with the same size of loss, the replay improves, and VALID and FWD improve. TRAIN (2025) gets worse by −26R, so the
  gain is not stable across years.
- **Fewer losses:** a breakeven move at +0.75R (C07) cuts the avg loss from −0.96 to −0.76R and helps TRAIN (t 1.75 in
  TRAIN), but it is flat in VALID and only matches the replay.
- **Neither clears validation.** The entry-quality filters all drop too many top winners (guard).
- **C20 "no re-entry after a stop"** would have stopped today's BEZ run. Over 2 years it is roughly neutral (+28.6R, t
  0.42), but it fails the top-decile guard because winning re-entries go too.
- **Random entries** (C_random_entries.csv): the same names entered at random 5-min bars with the same exits make
  −0.22R (2-year) and −0.13R (replay). The signal timing adds about +0.17R and +0.27R per trade. The timing is real; the
  2-year problem is the up-day drift of gap-down names, not the entry.

## Files
`PLAN.md`; `NOTES.md` (method, deviations); `BESPOKE_RULES.md` (draft design note, nothing implemented);
`latch_curve.png`; `A_engine.csv`, `A_live.csv`, `A_live_days.csv`, `A_plateau_vs_m2.csv`; `B_latch_rules.csv`,
`B_time_daytype.csv`; `C_workbench.csv`, `C_verdicts.csv`, `C_random_entries.csv`, `C_quantiles.json`; `code/`.
