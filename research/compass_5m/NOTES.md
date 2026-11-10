Educational only — not financial advice.

# COMPASS-5M — do 5-/10-minute updates between the 15-minute marks help? (2026-11-10)

Owner, 11-10 ~13:55 and ~14:00 ET: "Is it worth adding rolling 5-minute stats to the 15-minute compass for a more
up-to-date direction? Also test 5- and 10-minute 'moveable glue' between the marks. Add a plain-English line to the
card. Build a continuous table of what happens after X time has passed and SPY is already moving one way, together
with the previous day's close."

Research and display only. This is not a trading signal and changes no trading config. Pre-registered in `PLAN.md`
(commit 8c60e5c03, before any score). It is a market-only study (SPY / QQQ / IWM / 200 Hunch names, no setup R), so no
`research/ledger.jsonl` rule change bears on these numbers. The locked block 2024-11-01..2025-02-28 was never read: it
is filtered inside the parquet read. Periods follow COMPASS-LEARN: TRAIN 234 days, VALID 190, FWD 22, and LIVE 3
(11-05 / 06 / 09, shown only). **Configurations: 10 state definitions × 7 horizons × 2 targets + 2 rest-of-day tests =
142 tests, so the bar is t ≥ 3.15.** The cap was raised from ~10 to 16 configs for the owner's 5- and 10-minute glue
states; 10 were used.

## Plain-English answer
- **Is it worth it? No, not for direction.** A 5- or 10-minute update between the 15-minute marks does not tell you
  better where SPY goes next. At every horizon from 5 to 90 minutes, all ten states (today's W60 compass, 5- and
  10-minute glue, momentum, VWAP, "fresh tilt", the 0.20% rule) are right 48.1–52.7% of the time in VALID, against a
  base rate of about 50%. FWD shows the same. No direction test comes near the bar: the largest |t| is 2.29, and it
  points the *wrong* way (contrarian).
- **What 5-minute data does tell you is *how much* SPY is about to move, not which way.** After SPY moved ≥ 0.10% in the
  last 15 minutes, a further ≥ 0.10% move in the next 10 minutes happens 16% of the time instead of 10%. A ≥ 0.10% move
  *against* the last move also happens 17% of the time. This technically passes the pre-registered "size" rule (13
  tests, t up to 6.0, TRAIN and FWD agree), but it is volatility clustering on both sides, not direction. That is
  useful for "expect movement / wider stops", not for "it's heading up".
- **Rest of the day (where SPY closes vs its open): 5- or 10-minute glue reads about 10 minutes earlier, but it is less
  accurate at that first reading.** It is the same as W60 on the 15-minute grid (VALID S 0.335 both; GLUE10 +0.001,
  t 0.14). The glue confirms by 10:00 on 75% of days instead of 56%. Its first confirmation is right 67% of the time
  instead of 74% (VALID; FWD 59 vs 68%), and it flips 0.36 times a day instead of 0.26. On a 5-minute grid it is
  slightly better in TRAIN / VALID (S +0.013, "stays" 89.6 vs 88.8%) but worse in FWD (−0.012). Earlier but noisier;
  no pass.
- **So the card's window is "the rest of today".** That is the one thing the compass reads well, and it gets better as
  the day goes on. A confirmed UP reading is right 79% of the time before 11:00, 84% from 11:00 to 13:00, and 92% after
  13:00 (TRAIN+VALID). The next hour stays a coin flip: a confirmed compass called SPY's next 60 minutes right 53.5% of
  the time (FWD 51.3%).

## Short horizons: every number (VALID; `horizons.csv` has every state / period / target)
Direction = SPY's sign over the next h minutes equals the state. The base rate is ~50.0–50.2% at every horizon.
| horizon | W60 hit TRAIN / VALID / FWD | W60 coverage (VALID) | W60 t (VALID) | best of 10 states in VALID (hit, t) |
|---|---|---|---|---|
| 5 min | 50.5 / 49.9 / 49.2% | 60% | −0.28 | MOM5 48.9% (t −1.37, contrarian) |
| 10 min | 51.2 / 50.6 / 49.2% | 60% | 0.78 | MOM30 51.3% (1.29) |
| 15 min | 51.7 / 51.0 / 49.6% | 59% | 1.00 | CHK15 51.6% (1.62) |
| 30 min | 52.9 / 51.4 / 49.2% | 59% | 1.06 | VWAP 51.9% (1.42) |
| 45 min | 53.5 / 51.8 / 48.2% | 59% | 1.03 | CHK15 52.7% (1.72) |
| 60 min | 54.5 / 51.9 / 50.3% | 59% | 0.97 | GLUE5 52.4% (1.27) |
| 90 min | 56.5 / 52.5 / 52.3% | 58% | 1.11 | GLUE10 52.7% (1.20) |
- Glue states (VALID / FWD): GLUE5 10 min 51.0 / 49.8%, 30 min 51.6 / 49.4%; GLUE10 10 min 50.8 / 49.3%, 30 min 51.5 /
  49.3%. They are no better than W60.
- Momentum (MOM5 / 15 / 30), "fresh tilt" (TILT5 / 10) and VWAP fire on 22–66% of 5-minute marks and sit at 48–52% in
  VALID. TILT5 / 10 look best in FWD (54–57%), but in VALID they score below 50% (48–49%). That is a sign flip, so it is
  noise.
- "Size" target (≥ 0.10% in the called direction): W60 and the glue states are at their base rate (e.g. W60 30 min 20.1
  vs 20.5%). MOM15 / MOM30 / MOM5 beat their base by 3–7 points, but the move *against* the call rises by the same
  amount (MOM15 10 min: with the call 16.2%, against 17.0%, base 10.2%). It is volatility, not direction.
- TRAIN looks a little better than VALID for W60 at the long horizons (54–57%). That is the known TRAIN drift; it does
  not hold in VALID or FWD.

## Plain-English card: the state table (`mcf/report/compass_plain.json`, from `plain_table.py`)
This is the share of 15-minute readings in that state after which SPY closed on the stated side of its open.
TRAIN+VALID is pooled (days = distinct days with that state); FWD is shown (22 sessions, small).
| state | 09:45–10:59 | 11:00–12:59 | 13:00–15:45 | FWD (early / mid / late) |
|---|---|---|---|---|
| UP-confirmed | 79% (171 d) | 84% (217 d) | 92% (207 d) | 75 / 99 / 100% |
| DOWN-confirmed | 82% (144 d) | 90% (186 d) | 94% (184 d) | 53 / 90 / 93% |
| leaning up | 65% (287 d) | 64% (184 d) | 71% (132 d) | 77 / 65 / 95% |
| leaning down | 67% (277 d) | 71% (188 d) | 82% (143 d) | 52 / 62 / 36% (11 readings) |
| mixed (share closing above) | 47% | 52% | 45% | 69 / 75 / 64% |
| flipped up after midday* | – | – | 60% (27 d, all after 12:15) | no FWD case |
| flipped down after midday* | – | – | 82% (28 d) | no FWD case |
\*SPY ≥ 0.20% from its open at 12:00, then on the other side of its open at a later 15-minute mark (the live card
version of COMPASS-LEARN's D1 flip detector).
- Sentences on the card:
  - confirmed: "SPY is likely to finish today ABOVE / BELOW its open."
  - leaning: "SPY is leaning ABOVE / BELOW its open — not confirmed yet."
  - flip: "SPY has flipped back ABOVE / BELOW its open since midday."
  - mixed: "No clear direction yet — so far today is a coin flip."
  - Each sentence is followed by "… closed above / below its open N% of the time (on D past days, 2024-26; latest N% in
    n recent days)".
  - Always shown: "Next hour: no reliable read — … right only 54% of the time (51% recently), about a coin flip."
- Honest limits: "leaning down" late in the day was 36% in FWD (11 readings, 5 days), and "flipped up" is only 60%
  (27 days). Treat those lines as weak.

## Conditional stats: a durable table to fall back on (`mcf/report/compass_cond.py`)
- Key: time of day (every 10 min, 10:00..15:50) × SPY from its open (< −0.4, −0.4..−0.2, −0.2..0, 0..0.2, 0.2..0.4,
  > 0.4%) × SPY vs yesterday's close (above / below). A second grouping uses the gap (gap up ≥ +0.20% / flat / gap down).
- Per cell:
  - % closing on the same side of the open;
  - % closing on the same side of yesterday's close;
  - median and quartiles of the move to the close;
  - next 5 / 10 / 30 / 60-minute direction hit (in the from-open direction);
  - n.
- Baseline: 460 sessions, 2024-09-16..2026-11-09, with the locked block and half days excluded (16,560 rows, 1,090
  cells): `conditional_obs.csv.gz` and `conditional_stats.csv`. The cells are pooled over all periods (descriptive; no
  test).
- Examples (vs-previous-close grouping):
  - 13:00, SPY > +0.4% and above yesterday's close: closed above its open 95% (n 87), median move to the close +0.03%
    (IQR −0.15..+0.15%).
  - 11:00, SPY −0.4..−0.2% and below yesterday's close: 95% (n 39).
  - 10:00, SPY 0..+0.2% and above yesterday's close: 57% (n 94).
  - Being on the same side of yesterday's close as of the open adds a few points in most cells. Being on the
    *opposite* side lowers the hold rate early in the day (e.g. 10:00, +0.2..0.4% but below yesterday's close: 60%,
    n 10).
- **Caution:** the "next 5 / 10 / 30 / 60-minute" hits per cell spread from 27% to 74% across cells with n ≥ 30.
  Weighted, they are 50.8 / 50.8 / 51.8 / 52.8%, which is what ~240 noisy cells of ~50 days look like around a coin
  flip. Do not read a single cell's next-x hit as an edge. The close-side columns are the robust ones.
- **Continuous.** The table lives on the mcf-data-compass branch: `compass/cond_obs.csv` (seeded from the baseline on
  its first run), `compass/cond_stats.csv` and `compass/cond_stats.json`. Nightly, after 16:00 ET:
  `python -m mcf.report.compass_cond --date $(TZ=America/New_York date +%F) --push`
  It is idempotent: a rerun replaces that day, and a holiday appends nothing. It needs the Alpaca data keys (read-only
  SPY 1-minute GET). The live card shows the current cell's line ("At 13:40 with SPY +0.89% from its open and above
  yesterday's close, it finished on the same side of its open in 96% of 105 past days") only when
  `cond_stats.json`'s last session is the previous business day and the cell has n ≥ 15.

## For the Research Guild: next steps worth trying (count the new configs)
- Short-horizon direction from index-level state looks like a dead end: 10 states × 7 horizons, all coin flips. Do not
  spend more configs on SPY-only momentum / VWAP / breadth-tilt variants.
- The 5-minute volatility signal is real: next-10-minute ≥ 0.10% moves are 1.6× the base after a ≥ 0.10% 15-minute
  move, in both directions. Candidate uses: stop width / entry timing in setups (test per setup, Remedies rule), or a
  "movement expected" line on the card.
- The close-side read gets more accurate through the day (79 → 92% for UP-confirmed). A probability-of-close-side
  number from a calibrated model (COMPASS-LEARN's logistic) by time of day could replace the 3-block table.
- Being on the same side of yesterday's close helps the close-side hold rate. Test it as a vote in a pre-registered
  round. In COMPASS-LEARN, the gap as a must-agree filter hurt (it cut coverage), so try it as a weight, not a filter.
- Re-score the plain-English table every ~20 sessions from the nightly conditional stats and the live compass rows.

## Files
- `PLAN.md` (pre-registration)
- `study.py` → `horizons.csv` (10 states × 7 h × 2 targets × 4 periods; hit, base, coverage, excess, t clustered by
  day, against / against_base) and `side.csv` (rest-of-day side)
- `plain_table.py` → `mcf/report/compass_plain.json`
- `build_cond.py` → `conditional_obs.csv.gz`, `conditional_stats.csv`
- Panel: `research/compass_learn/panel.py` (scratch, deleted)
- Caveats: breadth = the 200 Hunch names over the whole history (survivorship); the 5-minute-grid side check
  (S +0.013 VALID) is a diagnostic, not a counted test.
