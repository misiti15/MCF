Educational only — not financial advice.

# L3LEASH — can a leash cut the bad (up-market) days of the Gap-Down Recovery Fade without costing its good days? (owner 2026-11-10)

Owner, 11-10 ~12:30 ET: Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` (short; Primary + Claude's Team) is
doing very well today. Cut its bad days (up-market days, when shorts get run over) without giving up good days — "no
risking positive R, just negative". Hypothesis: if the market is going up it won't go much higher after ~10:30-11:15, so
early entries are the risk; maybe keep it on a leash with the Market Compass or scale in through the morning.

**Research only. No config, setup, exit, ledger or workflow change (market hours, setups frozen).**

## Plain-English summary
- **Verdict: 0 of 12 leashes pass. Recommendation: keep the setup as is (no leash).** Every leash that removes a real
  share of the bad-day losses also gives up a similar or bigger share of the good-day R. None meets the owner's
  criterion (≤ ~10% of green-day R given up while removing ≥ 20% of red-day losses) in both VALID and FWD.
- **The hypothesis is only half true.** When SPY is up from its open at 10:30 / 11:00 / 11:15, the rest of the day is a
  coin flip, the same as on any day: the median further move to the close is +0.06 / +0.01 / +0.02%. 57 / 51 / 54% go
  higher. About 1 in 4 adds another +0.25% or more, and about 1 in 10 adds +0.5% or more. 25% fall back 0.25% or more, and
  28 / 28 / 24% close below the open. Down mornings mirror this exactly. So it is right that an up morning does not keep
  running, but it does not reverse either. The morning gives no edge on where SPY goes next. That matches COMPASS-LEARN:
  the compass reads the closing side ~89% of the time, but the next 30-120 minutes only ~51%.
- **The bad days are real.** In the 2-year lab, the setup's day R on SPY-up-close days (open→close > +0.25%) is −242R
  (TRAIN, 86 days) and −177R (VALID, 62 days), with 64-65% of those days red. On VALID down days it is +68R. But the
  morning signals that point to an up day (compass UP-confirmed, SPY ≥ +0.20%) also fire on the mornings that turn and
  pay. **Today (11-10) is the example:** all 9 Primary entries (10:00-10:26, +7.82R so far) came while the compass read
  UP-confirmed and SPY was +0.37..+0.43% from its open. The day then turned down by 10:45. The compass block, compass
  scale (0x) and SPY ≥ +0.20% skip would each have taken today to 0R. Half-size rules would have taken it to +3.9R. Only
  the −1R latch (K12) keeps the full +7.82R.
- **Early entries are not where the setup loses.** Halving entries before 10:30 / 10:45 / 11:15 (K04-K06) *loses* R on
  TRAIN and VALID (VALID −92 / −130 / −49R). In VALID, entries before 10:30 with the compass unconfirmed average +0.09R,
  among the setup's best.
- **The best lab-only scores mostly mean "trade a losing lab setup less".** With live caps and the −2R latch, the lab
  version of `L3-gap-slope-fromopen-FD` loses money in every split (TRAIN −355R, VALID −167R, FWD −39R). So any rule
  that removes trades looks good on TRAIN/VALID: the compass block and the SPY ≥ +0.20% skip gain about +95R in VALID
  and +63..93R in TRAIN. Both turn negative in FWD (−6.4 / −6.6R, giving up 74 / 81% of green-day R). Both are also
  worse in both live checks (Primary −2.6 / −2.4R; Testing 1 −34 / −51R). Live, the setup earns: Testing 1 had +55.1R
  over 206 trades (10-13..10-29). The lab misses that, most likely because live only shorts easy-to-borrow names: 913 of
  Primary's L3 signals were skipped as not shortable/ETB.
- **Sister setups:** in the lab, every leash "helps" most sisters in TRAIN/VALID, again because every sister's lab base
  is negative there. In FWD, where the sisters earn (RW3-FD +32R, RW5-FD +28R, MF2-FD +14R), most leashes hurt them.
  The compass block makes 0 of 7 better and 7 worse (−62R). The SPY ≥ +0.20% skip makes 1 better and 6 worse (−60R).
- **Closest calls, for the record:**
  - K11 (half size when SPY ≥ +0.40%) is the gentlest. In VALID it removed 8% of red-day losses for 11% of green-day R.
    In FWD it removed 19% for 25%. Net ≈ 0 in VALID.
  - K12 (−1R per-setup daily stop once the compass has read UP-confirmed) gave up only 10% of green-day R in FWD,
    removed 21% of red-day losses (+12.7R) and keeps today. But it is −24.9R in VALID and −5.6R in TRAIN, and it removes
    only 4-7% of red-day losses there.
  - K06 (half size before 11:15) is the only one positive in FWD on both counts (+26R, green R *gained*). It is −49R in
    VALID and −69R in TRAIN.
  - All three fail.
- **Configurations tried: 12 (K01-K12) + the base**, pre-declared in the module docstring of `study.py` before any
  score was read. Bar for a paired VALID day-t at N 12: 2.23. Best paired VALID t is 1.64 (K01). Expected false
  positives at p 0.05: ~0.6.

## 1. Hypothesis check — SPY after an up morning (1-min cache, 2024-10 + 2025-03..2026-11-09, locked block excluded)

Further move = SPY close vs SPY at the mark (%); for 'down <0 (mirror)' the sign is flipped (further move in the morning's direction). 'crosses open' = closes on the other side of its open. 'max further / max against' = mean best excursion after the mark each way.

| mark | SPY at the mark | split | days | mean | p10 | p25 | median | p75 | p90 | goes further | +0.25% more | +0.5% more | gives back ≥0.25% | closes across open | max further | max against |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10:30 | up >0 | ALL | 245 | +0.01 | -0.59 | -0.25 | +0.06 | +0.31 | +0.52 | 57% | 31% | 11% | 25% | 28% | +0.40 | +0.46 |
| 10:30 | up >0 | TRAIN | 132 | +0.02 | -0.63 | -0.26 | +0.07 | +0.33 | +0.54 | 58% | 35% | 13% | 26% | 29% | +0.44 | +0.52 |
| 10:30 | up >0 | VALID | 99 | +0.00 | -0.53 | -0.24 | +0.06 | +0.27 | +0.50 | 57% | 26% | 10% | 24% | 28% | +0.35 | +0.40 |
| 10:30 | up >0 | FWD+LIVE | 14 | -0.10 | -0.45 | -0.31 | +0.02 | +0.07 | +0.40 | 57% | 21% | 7% | 29% | 21% | +0.32 | +0.36 |
| 10:30 | up >=+0.20% | ALL | 128 | +0.02 | -0.67 | -0.33 | +0.11 | +0.36 | +0.52 | 59% | 34% | 11% | 27% | 20% | +0.47 | +0.52 |
| 10:30 | up >=+0.20% | TRAIN | 65 | +0.01 | -0.67 | -0.36 | +0.11 | +0.36 | +0.52 | 57% | 34% | 11% | 32% | 23% | +0.55 | +0.64 |
| 10:30 | up >=+0.20% | VALID | 55 | +0.07 | -0.56 | -0.16 | +0.12 | +0.39 | +0.56 | 66% | 36% | 13% | 18% | 14% | +0.40 | +0.37 |
| 10:30 | up >=+0.20% | FWD+LIVE | 8 | -0.27 | -0.80 | -0.38 | -0.17 | +0.04 | +0.19 | 38% | 12% | 0% | 50% | 25% | +0.30 | +0.50 |
| 10:30 | up >=+0.40% | ALL | 56 | +0.14 | -0.78 | -0.46 | +0.13 | +0.43 | +0.77 | 57% | 38% | 16% | 32% | 20% | +0.62 | +0.55 |
| 10:30 | down <0 (mirror) | ALL | 215 | +0.01 | -0.60 | -0.26 | -0.01 | +0.31 | +0.62 | 48% | 32% | 17% | 26% | 27% | +0.48 | +0.43 |
| 10:30 | all days | ALL | 460 | +0.00 | -0.60 | -0.29 | +0.03 | +0.29 | +0.57 | 54% | 28% | 13% | 28% |  | +0.41 | +0.47 |
| 11:00 | up >0 | ALL | 255 | -0.00 | -0.56 | -0.25 | +0.01 | +0.28 | +0.48 | 51% | 27% | 9% | 25% | 28% | +0.34 | +0.39 |
| 11:00 | up >0 | TRAIN | 130 | +0.04 | -0.55 | -0.21 | +0.05 | +0.33 | +0.51 | 55% | 30% | 11% | 24% | 28% | +0.37 | +0.41 |
| 11:00 | up >0 | VALID | 111 | -0.02 | -0.48 | -0.27 | -0.04 | +0.28 | +0.41 | 48% | 26% | 8% | 26% | 30% | +0.31 | +0.38 |
| 11:00 | up >0 | FWD+LIVE | 14 | -0.20 | -0.56 | -0.32 | -0.20 | +0.12 | +0.15 | 36% | 7% | 0% | 29% | 21% | +0.22 | +0.40 |
| 11:00 | up >=+0.20% | ALL | 142 | -0.02 | -0.62 | -0.24 | +0.04 | +0.26 | +0.45 | 54% | 25% | 7% | 25% | 18% | +0.33 | +0.41 |
| 11:00 | up >=+0.20% | TRAIN | 71 | +0.03 | -0.59 | -0.20 | +0.15 | +0.30 | +0.48 | 63% | 31% | 8% | 24% | 17% | +0.37 | +0.42 |
| 11:00 | up >=+0.20% | VALID | 61 | -0.04 | -0.60 | -0.23 | -0.04 | +0.21 | +0.40 | 48% | 21% | 7% | 23% | 20% | +0.30 | +0.38 |
| 11:00 | up >=+0.20% | FWD+LIVE | 10 | -0.27 | -0.68 | -0.38 | -0.23 | +0.03 | +0.14 | 30% | 10% | 0% | 40% | 10% | +0.20 | +0.45 |
| 11:00 | up >=+0.40% | ALL | 65 | -0.03 | -0.64 | -0.26 | -0.03 | +0.27 | +0.44 | 49% | 28% | 6% | 26% | 14% | +0.36 | +0.43 |
| 11:00 | down <0 (mirror) | ALL | 205 | -0.01 | -0.55 | -0.25 | -0.01 | +0.27 | +0.62 | 49% | 28% | 13% | 25% | 25% | +0.47 | +0.45 |
| 11:00 | all days | ALL | 460 | +0.00 | -0.59 | -0.27 | +0.01 | +0.28 | +0.50 | 51% | 26% | 10% | 26% |  | +0.38 | +0.43 |
| 11:15 | up >0 | ALL | 242 | +0.04 | -0.51 | -0.23 | +0.02 | +0.26 | +0.46 | 54% | 26% | 8% | 24% | 24% | +0.37 | +0.37 |
| 11:15 | up >0 | TRAIN | 125 | +0.10 | -0.59 | -0.16 | +0.07 | +0.29 | +0.51 | 58% | 32% | 10% | 22% | 25% | +0.43 | +0.38 |
| 11:15 | up >0 | VALID | 102 | -0.01 | -0.48 | -0.25 | +0.01 | +0.20 | +0.45 | 51% | 22% | 6% | 26% | 24% | +0.31 | +0.35 |
| 11:15 | up >0 | FWD+LIVE | 15 | -0.12 | -0.40 | -0.27 | -0.07 | +0.13 | +0.20 | 47% | 7% | 0% | 33% | 13% | +0.24 | +0.32 |
| 11:15 | up >=+0.20% | ALL | 155 | +0.08 | -0.50 | -0.21 | +0.06 | +0.27 | +0.46 | 58% | 28% | 7% | 23% | 16% | +0.41 | +0.38 |
| 11:15 | up >=+0.20% | TRAIN | 78 | +0.15 | -0.69 | -0.14 | +0.11 | +0.30 | +0.47 | 62% | 37% | 9% | 23% | 19% | +0.50 | +0.41 |
| 11:15 | up >=+0.20% | VALID | 67 | +0.01 | -0.42 | -0.20 | +0.03 | +0.19 | +0.41 | 55% | 19% | 6% | 22% | 15% | +0.33 | +0.35 |
| 11:15 | up >=+0.20% | FWD+LIVE | 10 | -0.08 | -0.32 | -0.25 | -0.11 | +0.10 | +0.16 | 50% | 10% | 0% | 30% | 0% | +0.26 | +0.27 |
| 11:15 | up >=+0.40% | ALL | 69 | +0.17 | -0.51 | -0.16 | +0.10 | +0.32 | +0.48 | 62% | 30% | 9% | 20% | 9% | +0.54 | +0.39 |
| 11:15 | down <0 (mirror) | ALL | 218 | +0.03 | -0.52 | -0.24 | -0.02 | +0.24 | +0.58 | 47% | 24% | 12% | 24% | 22% | +0.46 | +0.37 |
| 11:15 | all days | ALL | 460 | +0.00 | -0.56 | -0.24 | +0.02 | +0.25 | +0.49 | 54% | 25% | 10% | 24% |  | +0.37 | +0.41 |

Reading: up mornings behave like every other morning after 10:30 (all-days row: 54 / 51 / 53% further, median ≈ 0). FWD+LIVE (14-15 up mornings) leaned to giving back (mean −0.10..−0.27%), too few days to lean on.

## Method
- **Trades:** `research/history2y/data/bt_lab1104` lab trade lists. These are the setups' refire chains with
  production costs: entry 1c+1bps × time-of-day multiplier, non-target exits 1c+1bps, +2c on stops, ×3 for the
  extended tier. They run 2024-10 + 2025-03..2026-11-04, and the locked block 2024-11-01..2025-02-28 is filtered at
  load and asserted.
  - Each setup-day is re-simulated in time order with the live caps the lab can model: ≤ 3 lots per symbol and ≤ 30
    open positions per setup.
  - The −2R per-setup daily stop (realised R, latched) is kept in the base and in every variant.
  - A 0.5x entry counts ½ R and ½ costs. A 0x entry is not placed and takes no cap room.
- **Compass:** the W60 15-min compass backfill from ECG1 / `research/bdi/hc1/state15.py` (SPY/QQQ/IWM 1-min cache +
  lab `breadth_open`). The reading used is the one at the latest 15-min mark ≤ the entry.
  - LIVE days use the production `mcf.report.compass_live.compute` on 1-min SIP bars from the read-only market-data GET
    (`live_compass.py`). It matches the recorded compass rows of 11-06 / 11-09 / 11-10 on 100% of marks.
- **SPY from open:** the 1-min bar closed by the entry minute.
- **Splits (as COMPASS-LEARN / GATE1):** TRAIN 2024-10 + 2025-03..12 (214 L3 days), VALID 2026-01-01..10-05 (179),
  FWD 10-06..11-04 (21).
  - LIVE: Primary journal `run_id=1` 10-21..11-09 (34 trades incl. the latch what-ifs that the latch blocked), and
    Testing 1 `run_id=1` 10-13..10-29 (206 trades; the −2R latch is applied in the sim).
  - 11-10 is partial (in progress) and in-sample, so it is shown separately.
- **Red / green days** = the base's day R < 0 / > 0, per setup and split.
  - "Red-day R removed" = variant R − base R on base-red days (+ = loss cut).
  - "Green-day R given up" = base R − variant R on base-green days (+ = R lost).
- **Pass rule (pre-declared in `study.py`):**
  - In VALID and in FWD: red-day losses cut ≥ 20%, green-day R given up ≤ 10%, total dR ≥ 0.
  - TRAIN dR ≥ 0.
  - No sister worse by > 5% of its base |R| in VALID.
  - The paired VALID day-t vs the N-12 bar (2.23) is reported.

## 2. The 12 leashes (pre-declared)
| id | leash |
|---|---|
| K01 | BLOCK: no new entry while the compass reads UP-confirmed (resumes when it flips) |
| K02 | SCALE: 0.5x until the day's first confirmation; 1x DOWN-confirmed or unconfirmed after it; **0x** UP-confirmed |
| K03 | SCALE: as K02 but **0.5x** while UP-confirmed |
| K04 / K05 / K06 | RAMP: 0.5x for entries before 10:30 / 10:45 / 11:15 |
| K07 | RAMP 10:30 + BLOCK |
| K08 / K09 | skip the entry when SPY ≥ +0.20% / +0.40% from its open |
| K10 / K11 | 0.5x when SPY ≥ +0.20% / +0.40% |
| K12 | per-setup daily stop −1R (not −2R) once the compass has read UP-confirmed at any mark today |

## 3. Verdict per leash (`verdict.csv`)
| cfg | TRAIN dR | VALID dR | FWD dR | VALID red cut / green given | FWD red cut / green given | VALID paired t | sisters VALID better/worse | sisters FWD better/worse (dR) | live Primary dR | live Testing 1 dR | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| K01 BLOCK on UP-conf | +63.4 | +94.3 | -6.4 | 30% / 20% | 31% / 74% | +1.64 | 7/0 | 0/7 (-62) | -2.56 | -34.23 | fail |
| K02 SCALE 0.5 pre-conf / 0 UP | +33.6 | +39.9 | -13.4 | 32% / 34% | 35% / 99% | +0.55 | 6/1 | 3/4 (-43) | -2.85 | -42.67 | fail |
| K03 SCALE 0.5 pre-conf / 0.5 UP | +19.8 | -8.1 | -4.9 | 20% / 28% | 29% / 68% | -0.14 | 6/1 | 3/4 (-28) | -2.78 | -26.33 | fail |
| K04 RAMP 0.5x < 10:30 | -48.7 | -92.1 | +7.2 | -4% / 13% | 2% / -12% | -1.41 | 4/3 | 5/2 (+14) | -1.58 | +0.63 | fail |
| K05 RAMP 0.5x < 10:45 | -55.2 | -130.0 | +0.4 | -4% / 22% | -6% / -13% | -2.20 | 5/2 | 6/1 (+17) | -1.69 | -2.88 | fail |
| K06 RAMP 0.5x < 11:15 | -68.5 | -48.9 | +26.4 | 10% / 23% | 27% / -10% | -0.74 | 5/2 | 3/4 (-53) | -2.35 | -5.06 | fail |
| K07 RAMP<10:30 + BLOCK | +37.7 | -7.4 | -15.1 | 24% / 34% | 14% / 62% | -0.10 | 5/2 | 2/5 (-40) | -3.03 | -33.60 | fail |
| K08 SPY>=+0.20% skip | +92.9 | +99.4 | -6.6 | 40% / 34% | 34% / 81% | +1.39 | 7/0 | 1/6 (-60) | -2.36 | -50.52 | fail |
| K09 SPY>=+0.40% skip | +21.3 | -1.0 | -7.3 | 15% / 21% | 14% / 45% | -0.02 | 7/0 | 2/5 (-31) | -2.60 | -43.88 | fail |
| K10 SPY>=+0.20% half | +30.4 | +17.8 | +8.5 | 15% / 17% | 34% / 46% | +0.42 | 7/0 | 2/5 (-50) | -2.39 | -25.52 | fail |
| K11 SPY>=+0.40% half | +18.1 | -0.1 | +5.2 | 8% / 11% | 19% / 25% | -0.00 | 7/0 | 2/5 (-30) | -2.51 | -21.94 | fail |
| K12 -1R latch after UP-conf | -5.6 | -24.9 | +12.7 | 4% / 11% | 21% / 10% | -0.64 | 5/2 | 1/6 (-76) | -1.42 | -12.91 | fail |

Sister dR detail per split: `study_out.txt` ("Sisters" section) and `configs.csv`.

## 4. L3-gap-slope-fromopen-FD per split and live (full metrics)

**L3-gap-slope-fromopen-FD - TRAIN (lab, costs in)**

| cfg | leash | trades | total R | R/trade | day-t | dR vs base (paired t) | red-day R removed | green-day R given up | green days | worst day | worst 5 | avg R w/o best day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | base (-2R latch) | 2902 | -355.3 | -0.122 | -2.50 | +0.0 () | +0.0 of -805.3 (0%) | +0.0 of 450.0 (0%) | 88/214 | -57.5 | -199.4 | -0.141 |
| K01 | BLOCK on UP-conf | 2147 | -291.9 | -0.136 | -2.78 | +63.4 (+0.74) | +246.5 of -805.3 (31%) | +183.1 of 450.0 (41%) | 84/214 | -47.1 | -166.8 | -0.149 |
| K02 | SCALE 0.5 pre-conf / 0 UP | 2350 | -321.7 | -0.137 | -3.11 | +33.6 (+0.35) | +270.0 of -805.3 (34%) | +236.4 of 450.0 (53%) | 85/214 | -47.5 | -159.3 | -0.148 |
| K03 | SCALE 0.5 pre-conf / 0.5 UP | 3525 | -335.5 | -0.095 | -3.04 | +19.8 (+0.28) | +166.5 of -805.3 (21%) | +146.7 of 450.0 (33%) | 101/214 | -33.9 | -144.4 | -0.104 |
| K04 | RAMP 0.5x < 10:30 | 3281 | -404.0 | -0.123 | -2.92 | -48.7 (-0.89) | +21.1 of -805.3 (3%) | +69.9 of 450.0 (16%) | 93/214 | -48.8 | -188.6 | -0.139 |
| K05 | RAMP 0.5x < 10:45 | 3324 | -410.5 | -0.123 | -2.99 | -55.2 (-0.98) | +22.9 of -805.3 (3%) | +78.1 of 450.0 (17%) | 96/214 | -57.4 | -187.2 | -0.138 |
| K06 | RAMP 0.5x < 11:15 | 3452 | -423.8 | -0.123 | -3.13 | -68.5 (-1.12) | +23.0 of -805.3 (3%) | +91.5 of 450.0 (20%) | 97/214 | -56.9 | -186.1 | -0.135 |
| K07 | RAMP<10:30 + BLOCK | 2349 | -317.7 | -0.135 | -3.07 | +37.7 (+0.39) | +260.4 of -805.3 (32%) | +222.7 of 450.0 (49%) | 86/214 | -34.3 | -153.9 | -0.147 |
| K08 | SPY>=+0.20% skip | 1855 | -262.4 | -0.141 | -2.72 | +92.9 (+0.97) | +301.9 of -805.3 (37%) | +209.0 of 450.0 (46%) | 73/214 | -39.7 | -154.0 | -0.156 |
| K09 | SPY>=+0.40% skip | 2269 | -334.0 | -0.147 | -2.95 | +21.3 (+0.30) | +163.5 of -805.3 (20%) | +142.2 of 450.0 (32%) | 82/214 | -48.2 | -173.3 | -0.167 |
| K10 | SPY>=+0.20% half | 3245 | -324.9 | -0.100 | -3.12 | +30.4 (+0.54) | +139.4 of -805.3 (17%) | +109.0 of 450.0 (24%) | 91/214 | -33.7 | -142.9 | -0.111 |
| K11 | SPY>=+0.40% half | 2987 | -337.2 | -0.113 | -2.92 | +18.1 (+0.37) | +93.6 of -805.3 (12%) | +75.5 of 450.0 (17%) | 90/214 | -36.6 | -158.2 | -0.128 |
| K12 | -1R latch after UP-conf | 2633 | -360.9 | -0.137 | -2.82 | -5.6 (-0.12) | +57.4 of -805.3 (7%) | +63.0 of 450.0 (14%) | 83/214 | -47.9 | -187.0 | -0.151 |

**L3-gap-slope-fromopen-FD - VALID (lab, costs in)**

| cfg | leash | trades | total R | R/trade | day-t | dR vs base (paired t) | red-day R removed | green-day R given up | green days | worst day | worst 5 | avg R w/o best day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | base (-2R latch) | 3021 | -166.5 | -0.055 | -1.38 | +0.0 () | +0.0 of -646.1 (0%) | +0.0 of 479.5 (0%) | 61/179 | -31.7 | -121.7 | -0.070 |
| K01 | BLOCK on UP-conf | 2229 | -72.2 | -0.032 | -0.65 | +94.3 (+1.64) | +192.6 of -646.1 (30%) | +98.2 of 479.5 (20%) | 65/179 | -29.7 | -117.3 | -0.056 |
| K02 | SCALE 0.5 pre-conf / 0 UP | 2795 | -126.6 | -0.045 | -1.16 | +39.9 (+0.55) | +205.1 of -646.1 (32%) | +165.3 of 479.5 (34%) | 71/179 | -29.7 | -127.1 | -0.063 |
| K03 | SCALE 0.5 pre-conf / 0.5 UP | 3925 | -174.7 | -0.044 | -1.66 | -8.1 (-0.14) | +128.2 of -646.1 (20%) | +136.3 of 479.5 (28%) | 72/179 | -29.1 | -126.2 | -0.053 |
| K04 | RAMP 0.5x < 10:30 | 3674 | -258.6 | -0.070 | -1.99 | -92.1 (-1.41) | -27.9 of -646.1 (-4%) | +64.2 of 479.5 (13%) | 65/179 | -34.2 | -147.5 | -0.082 |
| K05 | RAMP 0.5x < 10:45 | 3576 | -296.5 | -0.083 | -2.49 | -130.0 (-2.20) | -24.3 of -646.1 (-4%) | +105.7 of 479.5 (22%) | 63/179 | -29.9 | -132.4 | -0.094 |
| K06 | RAMP 0.5x < 11:15 | 3808 | -215.4 | -0.057 | -1.85 | -48.9 (-0.74) | +62.6 of -646.1 (10%) | +111.5 of 479.5 (23%) | 68/179 | -28.3 | -125.8 | -0.066 |
| K07 | RAMP<10:30 + BLOCK | 2702 | -173.9 | -0.064 | -1.53 | -7.4 (-0.10) | +153.8 of -646.1 (24%) | +161.3 of 479.5 (34%) | 68/179 | -29.2 | -128.4 | -0.083 |
| K08 | SPY>=+0.20% skip | 2036 | -67.2 | -0.033 | -0.69 | +99.4 (+1.39) | +260.0 of -646.1 (40%) | +160.7 of 479.5 (34%) | 58/179 | -28.3 | -96.8 | -0.048 |
| K09 | SPY>=+0.40% skip | 2388 | -167.5 | -0.070 | -1.54 | -1.0 (-0.02) | +99.1 of -646.1 (15%) | +100.1 of 479.5 (21%) | 57/179 | -29.6 | -119.5 | -0.090 |
| K10 | SPY>=+0.20% half | 3472 | -148.7 | -0.043 | -1.38 | +17.8 (+0.42) | +97.6 of -646.1 (15%) | +79.7 of 479.5 (17%) | 63/179 | -28.3 | -105.8 | -0.054 |
| K11 | SPY>=+0.40% half | 3227 | -166.7 | -0.052 | -1.48 | -0.1 (-0.00) | +54.9 of -646.1 (8%) | +55.0 of 479.5 (11%) | 64/179 | -28.3 | -114.5 | -0.065 |
| K12 | -1R latch after UP-conf | 2727 | -191.5 | -0.070 | -1.61 | -24.9 (-0.64) | +28.8 of -646.1 (4%) | +53.8 of 479.5 (11%) | 55/179 | -30.7 | -131.3 | -0.087 |

**L3-gap-slope-fromopen-FD - FWD (lab, costs in)**

| cfg | leash | trades | total R | R/trade | day-t | dR vs base (paired t) | red-day R removed | green-day R given up | green days | worst day | worst 5 | avg R w/o best day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | base (-2R latch) | 408 | -39.2 | -0.096 | -1.10 | +0.0 () | +0.0 of -81.4 (0%) | +0.0 of 42.1 (0%) | 9/21 | -17.0 | -56.1 | -0.159 |
| K01 | BLOCK on UP-conf | 272 | -45.7 | -0.168 | -2.21 | -6.4 (-0.25) | +24.9 of -81.4 (31%) | +31.3 of 42.1 (74%) | 5/21 | -13.1 | -39.4 | -0.220 |
| K02 | SCALE 0.5 pre-conf / 0 UP | 346 | -52.6 | -0.152 | -2.03 | -13.4 (-0.42) | +28.1 of -81.4 (35%) | +41.5 of 42.1 (99%) | 4/21 | -13.1 | -52.0 | -0.204 |
| K03 | SCALE 0.5 pre-conf / 0.5 UP | 534 | -44.1 | -0.083 | -1.46 | -4.9 (-0.19) | +23.7 of -81.4 (29%) | +28.6 of 42.1 (68%) | 8/21 | -13.1 | -52.9 | -0.110 |
| K04 | RAMP 0.5x < 10:30 | 556 | -32.1 | -0.058 | -0.66 | +7.2 (+0.23) | +2.0 of -81.4 (2%) | -5.2 of 42.1 (-12%) | 10/21 | -17.4 | -78.5 | -0.098 |
| K05 | RAMP 0.5x < 10:45 | 544 | -38.8 | -0.071 | -0.89 | +0.4 (+0.02) | -4.9 of -81.4 (-6%) | -5.3 of 42.1 (-13%) | 9/21 | -17.4 | -71.1 | -0.114 |
| K06 | RAMP 0.5x < 11:15 | 555 | -12.8 | -0.023 | -0.32 | +26.4 (+1.01) | +22.3 of -81.4 (27%) | -4.1 of 42.1 (-10%) | 9/21 | -16.9 | -56.5 | -0.057 |
| K07 | RAMP<10:30 + BLOCK | 378 | -54.4 | -0.144 | -1.50 | -15.1 (-0.42) | +11.0 of -81.4 (14%) | +26.1 of 42.1 (62%) | 5/21 | -17.1 | -66.4 | -0.199 |
| K08 | SPY>=+0.20% skip | 240 | -45.9 | -0.191 | -2.21 | -6.6 (-0.23) | +27.4 of -81.4 (34%) | +34.0 of 42.1 (81%) | 5/21 | -13.1 | -41.1 | -0.254 |
| K09 | SPY>=+0.40% skip | 328 | -46.6 | -0.142 | -1.85 | -7.3 (-0.35) | +11.8 of -81.4 (14%) | +19.1 of 42.1 (45%) | 8/21 | -13.1 | -45.2 | -0.187 |
| K10 | SPY>=+0.20% half | 494 | -30.7 | -0.062 | -1.16 | +8.5 (+0.43) | +28.0 of -81.4 (34%) | +19.4 of 42.1 (46%) | 10/21 | -13.1 | -45.6 | -0.083 |
| K11 | SPY>=+0.40% half | 444 | -34.0 | -0.077 | -1.15 | +5.2 (+0.38) | +15.7 of -81.4 (19%) | +10.4 of 42.1 (25%) | 9/21 | -13.1 | -50.2 | -0.108 |
| K12 | -1R latch after UP-conf | 373 | -26.5 | -0.071 | -0.89 | +12.7 (+1.18) | +16.8 of -81.4 (21%) | +4.1 of 42.1 (10%) | 9/21 | -13.1 | -45.1 | -0.121 |

**LIVE Primary 10-21..11-09 (run 1 + latch what-ifs)**

| cfg | trades | total R | dR | red-day R removed | green-day R given up | worst day | best-day share |
|---|---|---|---|---|---|---|---|
| B0 | 34 | -7.18 | +0.00 | +0.00 of -12.10 | +0.00 of 4.92 | -5.75 |  |
| K01 | 18 | -9.74 | -2.56 | +1.30 of -12.10 | +3.86 of 4.92 | -5.75 |  |
| K02 | 18 | -10.03 | -2.85 | +1.30 of -12.10 | +4.15 of 4.92 | -5.75 |  |
| K03 | 49 | -9.97 | -2.78 | -0.56 of -12.10 | +2.22 of 4.92 | -5.75 |  |
| K04 | 49 | -8.76 | -1.58 | -0.77 of -12.10 | +0.81 of 4.92 | -5.75 |  |
| K05 | 49 | -8.87 | -1.69 | -0.34 of -12.10 | +1.35 of 4.92 | -5.17 |  |
| K06 | 52 | -9.53 | -2.35 | -0.40 of -12.10 | +1.95 of 4.92 | -5.17 |  |
| K07 | 18 | -10.22 | -3.03 | +1.12 of -12.10 | +4.15 of 4.92 | -5.75 |  |
| K08 | 15 | -9.54 | -2.36 | +2.56 of -12.10 | +4.92 of 4.92 | -4.49 |  |
| K09 | 18 | -9.78 | -2.60 | +1.30 of -12.10 | +3.89 of 4.92 | -5.75 |  |
| K10 | 49 | -9.58 | -2.39 | +0.07 of -12.10 | +2.46 of 4.92 | -5.12 |  |
| K11 | 49 | -9.69 | -2.51 | -0.56 of -12.10 | +1.95 of 4.92 | -5.75 |  |
| K12 | 32 | -8.61 | -1.42 | -1.42 of -12.10 | +0.00 of 4.92 | -5.75 |  |

**LIVE Testing 1 10-13..10-29 (run 1; -2R latch applied in sim)**

| cfg | trades | total R | dR | red-day R removed | green-day R given up | worst day | best-day share |
|---|---|---|---|---|---|---|---|
| B0 | 206 | +55.09 | +0.00 | +0.00 of -8.97 | +0.00 of 64.06 | -3.81 | 61% |
| K01 | 108 | +20.86 | -34.23 | +2.04 of -8.97 | +36.27 of 64.06 | -3.81 | 79% |
| K02 | 114 | +12.42 | -42.67 | +5.66 of -8.97 | +48.33 of 64.06 | -3.51 | 96% |
| K03 | 214 | +28.76 | -26.33 | +3.87 of -8.97 | +30.20 of 64.06 | -4.03 | 71% |
| K04 | 209 | +55.72 | +0.63 | +1.60 of -8.97 | +0.97 of 64.06 | -3.81 | 59% |
| K05 | 216 | +52.21 | -2.88 | +2.12 of -8.97 | +5.00 of 64.06 | -7.20 | 56% |
| K06 | 216 | +50.03 | -5.06 | +4.77 of -8.97 | +9.83 of 64.06 | -4.03 | 50% |
| K07 | 111 | +21.49 | -33.60 | +3.64 of -8.97 | +37.24 of 64.06 | -3.81 | 74% |
| K08 | 66 | +4.57 | -50.52 | +4.14 of -8.97 | +54.67 of 64.06 | -2.44 | 162% |
| K09 | 93 | +11.21 | -43.88 | +0.00 of -8.97 | +43.88 of 64.06 | -3.81 | 132% |
| K10 | 207 | +29.57 | -25.52 | +1.81 of -8.97 | +27.33 of 64.06 | -2.76 | 57% |
| K11 | 206 | +33.15 | -21.94 | +0.00 of -8.97 | +21.94 of 64.06 | -3.81 | 54% |
| K12 | 178 | +42.18 | -12.91 | +0.00 of -8.97 | +12.91 of 64.06 | -3.81 | 60% |

**Primary 11-10 so far (9 trades, partial, in-sample - the day that prompted the question)**: B0 +7.82R; K01 +0.00R; K02 +0.00R; K03 +3.91R; K04 +3.91R; K05 +3.91R; K06 +3.91R; K07 +0.00R; K08 +0.00R; K09 +3.05R; K10 +3.91R; K11 +5.44R; K12 +7.82R


## 5. Sister setups (Remedies rule)
**Sisters (lab): setups better / worse vs their own base, sum of dR**

| cfg | TRAIN better/worse, dR | VALID better/worse, dR | FWD better/worse, dR | worst sister VALID | worst sister FWD |
|---|---|---|---|---|---|
| K01 BLOCK on UP-conf | 6/1, +398 | 7/0, +250 | 0/7, -62 | MF2-open-rsimidhi-flowsell-FD +3 | MF2-open-rsimidhi-flowsell-FD -18 |
| K02 SCALE 0.5 pre-conf / 0 UP | 6/1, +574 | 6/1, +361 | 3/4, -43 | MF2-open-rsimidhi-flowsell-FD -13 | RW3-gapdn-rsi5pop-flowsell-short-FD -17 |
| K03 SCALE 0.5 pre-conf / 0.5 UP | 7/0, +344 | 6/1, +247 | 3/4, -28 | MF2-open-rsimidhi-flowsell-FD -2 | L3-gap-slope-lowdist-FD -15 |
| K04 RAMP 0.5x < 10:30 | 6/1, +62 | 4/3, +41 | 5/2, +14 | RW3-gapdn-rsi5pop-flowsell-short-FD -33 | MF2-open-rsimidhi-flowsell-FD -7 |
| K05 RAMP 0.5x < 10:45 | 5/2, +105 | 5/2, +84 | 6/1, +17 | RW3-gapdn-rsi5pop-flowsell-short-FD -23 | MF2-open-rsimidhi-flowsell-FD -16 |
| K06 RAMP 0.5x < 11:15 | 6/1, +235 | 5/2, +81 | 3/4, -53 | RW3-gapdn-rsi5pop-flowsell-short-FD -44 | MF2-open-rsimidhi-flowsell-FD -26 |
| K07 RAMP<10:30 + BLOCK | 6/1, +463 | 5/2, +280 | 2/5, -40 | RW3-gapdn-rsi5pop-flowsell-short-FD -16 | RW3-gapdn-rsi5pop-flowsell-short-FD -16 |
| K08 SPY>=+0.20% skip | 7/0, +589 | 7/0, +414 | 1/6, -60 | MF2-open-rsimidhi-flowsell-FD +32 | MF2-open-rsimidhi-flowsell-FD -21 |
| K09 SPY>=+0.40% skip | 6/1, +299 | 7/0, +199 | 2/5, -31 | MF4-h40-open-flowsell +6 | L3-gap-slope-lowdist-FD -14 |
| K10 SPY>=+0.20% half | 7/0, +259 | 7/0, +213 | 2/5, -50 | MF2-open-rsimidhi-flowsell-FD +14 | MF2-open-rsimidhi-flowsell-FD -21 |
| K11 SPY>=+0.40% half | 6/1, +124 | 7/0, +111 | 2/5, -30 | MF4-h40-open-flowsell +4 | L3-gap-slope-lowdist-FD -13 |
| K12 -1R latch after UP-conf | 6/1, +132 | 5/2, +157 | 1/6, -76 | L3-gap-slope-rsi5hi-FD -7 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD -30 |

**Sister base R (lab, -2R latch, caps)**: L3-gap-slope-lowdist-FD T -125 / V -195 / F +3; L3-gap-slope-rsi5hi-FD T -290 / V -117 / F -7; MF2-open-rsimidhi-flowsell-FD T -85 / V -221 / F +14; MF4-h40-open-flowsell T -164 / V -74 / F -7; MF4-h40-open-flowsell-FD T -274 / V -169 / F +5; RW3-gapdn-rsi5pop-flowsell-short-FD T -295 / V -44 / F +32; RW5-heat30-flowsell-rsi5pop-gapdn-short-FD T -166 / V -107 / F +28


## 6. Where the base loses (diagnostic, not a config; `study_out.txt`)
Base L3 avg R by entry window × compass, VALID (n):

| entry | DOWN-confirmed | UP-confirmed | unconfirmed |
|---|---|---|---|
| < 10:30 | −0.214 (90) | −0.189 (255) | **+0.090 (455)** |
| 10:30-11 | +0.140 (51) | +0.263 (87) | −0.098 (197) |
| 11-12 | −0.293 (173) | −0.051 (283) | −0.089 (497) |
| 12-14 | −0.003 (167) | −0.233 (184) | +0.018 (327) |
| ≥ 14 | −0.084 (54) | +0.156 (87) | −0.112 (114) |

TRAIN shows a different pattern: UP-confirmed is worst early (−0.142 before 10:30), and 11-12 unconfirmed is −0.270.
No cell keeps its sign across TRAIN / VALID / FWD consistently enough to build a cleaner leash. The losses are spread
over the whole day, not concentrated in early, up-market entries.

Base day R by SPY day type (close vs open ±0.25%):

| split | SPY up | flat | SPY down |
|---|---|---|---|
| TRAIN | −242R (86 d, 64% red) | −99R (64 d) | −14R (64 d) |
| VALID | −177R (62 d, 65% red) | −57R (60 d) | +68R (57 d) |
| FWD | −17R (6 d) | −20R (10 d) | −2R (5 d) |

## One-big-day check
- **Lab base:** negative in every split, so a best-day share does not apply. Avg R without the best day: TRAIN −0.141,
  VALID −0.070, FWD −0.159.
- **Live Testing 1 base:** +55.1R / 206 trades. The best day is 61% of total R (**`1 day` tag**; 10-20, 80 trades).
  Without it, +0.17R/trade. Under the leashes the share rises to 0.54-1.62, i.e. they lean even more on the one day.
- **Live Primary base:** −7.18R / 34 trades (3 green days of 7). 11-10 so far is +7.82R on 9 trades and would be its
  best day.

## Rule-change context (research/ledger.jsonl) inside the windows
- 10-14 lab refire option B (cooldown per setup).
- 10-20 per-setup −2R daily loss limit (net).
- 10-20/21 L3-fromopen-FD Testing 1 → Primary, then 10-22 demoted back to Testing 1.
- 10-23 the setup stop latches. Testing 1/2 + Gen setup stop off.
- 10-28 Primary ~$5k then ~$4k position size (per-setup cap 30).
- 10-29 Primary −2R latch (ST-P).
- 10-30 L3-fromopen-FD re-promoted Testing 1 → Primary.
- 11-05 ROLL1.

The lab is rule-fixed: it applies the −2R latch and the caps to all days. The live Primary window mixes pre- and
post-latch sessions (10-21 / 10-22 had no latch), and the sim applies the latch to all of them. Testing 1 ran with the
setup stop off from 10-23, and the sim applies −2R.

## Caveats
- **The lab and live disagree about the setup.** In the lab the base loses in every split. Live it is +55.1R (Testing 1)
  and −7.18R (Primary, before 11-10). The lab has no ETB/shortable filter (913 Primary signals skipped live as
  not-ETB), no spread or participation checks, and no account-level halts. Survivorship: today's symbol list is applied
  to the past.
- **Two compass sources:**
  - History uses lab `breadth_open` (the ECG1 / state15 convention).
  - LIVE uses the production compass (200 Hunch names).
  - The live compass rows are written a few minutes after each mark; the sim reads a mark's value at the mark itself.
- **Small live samples:** 34 Primary trades on 7 days and 206 Testing 1 trades on 11 days. 11-10 is partial and is
  the day that raised the question (in-sample).
- **Relation to ECG1 (11-09).** K01 is ECG1's gate restricted to L3. ECG1 on the uncapped, unlatched lab lists had L3
  at −110R. Here, with caps and the latch, it is +63 / +94 / −6R (TRAIN / VALID / FWD). The ECG1 lineage stays where it
  was: swing1109-L11 forward shadow.

## Recommendation (for the owner after the close)
**Keep `L3-gap-slope-fromopen-FD` as is: fully unlocked, −2R latch, no leash.** Nothing tested cuts bad days without
cutting good days by a similar amount, and the up-day damage is not concentrated in early entries. The morning does not
tell which up-mornings keep running, which is exactly the setup's risk. The two rules that look best in the 2-year lab
(K01 compass block, K08 SPY ≥ +0.20% skip) do so because the lab version of the setup loses. They are negative in FWD,
in both live checks, and on today.

Next steps worth a pre-registered run (each counts new configs in this lineage, N = 12 so far):
- **L3LEASH-2:** re-run on an ETB-proxy lab universe (e.g. names that were ETB in the live journals), so the base
  resembles live before any leash is judged.
- Watch K12 (−1R latch after UP-confirmed) and K11 (half size at SPY ≥ +0.40%) in a nightly forward shadow only. They
  are the gentlest: green-day give-up 10-25%, and K12 keeps 11-10. Re-score at 20 sessions.

Backlog: `l3leash-1110-up-market-leash` (status parked, 12 configs) in `research/backlog.jsonl`.

## Files
- `study.py`: everything → `study_out.txt`, `configs.csv` (every setup × config × split, incl. live),
  `verdict.csv`, `hypothesis.csv`, `hypothesis_days.csv`, `l3_base_days.csv`.
- `live_compass.py`: production compass + SPY bars for the live days (scratch parquet, not committed).
- `tables.py` → `tables.md`.
- Run: `python research/l3leash/live_compass.py <scratch> && python research/l3leash/study.py <scratch>`, with
  `<scratch>/j/{primary,testing}.db` = `git show origin/mcf-data:journal.db` / `origin/mcf-data-testing:journal.db`.
  Single process, nice'd, ~5 min.

Educational only — not financial advice.
