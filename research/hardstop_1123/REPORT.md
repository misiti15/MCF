Educational only — not financial advice.

# hardstop_1123: hard stops for truly bad days, and the 11-23 pattern (research only, no config change)

## What the owner asked (2026-11-23)

- "I want hard stops in place on truly detrimental days based on hard numbers of what is likely to happen." Under the CLAUDE.md rule against a human in the loop on losing days, these must fire automatically.
- "6/7 trades +4.1R but the rest trending bad."

## How it was tested

- **Pre-registration:** PLAN.md, written before scoring.
- **Rules tried:** 17, plus one reproduction check.
- **Significance bar:** 2.38 for this study, or 2.86 if the rules_1122 and etfstop_1123 loss rules count as the same lineage (N = 59).
- The locked block was never read.

**Engine (build_paths.py, sim.py, score.py):**
- bench10 signals, 1-minute exits, LR8 costs plus borrow.
- One minute-by-minute book for the 4 current Primary setups:
  - cap 30 per setup, at most 3 lots per symbol;
  - −2R latch on closed R per setup;
  - burst brake;
  - −20R halt on closed + open R.
- **Point in time:** each entry sees the previous minute's state.
- **Reproduction:** with the halt and brake off, the book matches bench10 exactly.

**Periods:** FIT 170 sessions, T2 427, CHECK 276 (to 2026-11-04).

## Failures first

1. **The bench book itself loses.** The 4 current Primary setups make −1,701R over 873 sessions (−0.086R per lot), and 27% of sessions end at or below −6R.
   - Any rule that trades less therefore "gains" R.
   - To separate real tail protection from simply trading less, every rule is also scored with the book re-priced to zero expectancy (dR_neutral) and to +0.10R per lot (dR_book_p10).
2. **Part 2 (no new shorts on strong SPY up-days while the book is red): No, for all 6 configs.**
   - Best is S1_0: +25R in 3.5 years, t 0.73.
   - The worst day is unchanged, and the rule is −20R at zero expectancy.
3. **Per-setup open+closed latches and "no new entries" stops** (L2, L3, LF2, LF3, N4, N6, N8) only cut exposure; they do not pick out bad days.
   - Their gain disappears at zero expectancy.
   - On a +0.10R-per-lot book they lose −14 to −590R.
4. **Account stops cannot catch a one-minute shock.** On 2026-07-29 14:00 the book fell from −10R to −40.7R within a single minute.
5. **Small stops cut recovery days in the live window.**
   - A8 on 11-12: +39.9R became −8.2R.
   - A12 on 11-05: +2.4R became −12.8R.

## Part 1: results (pooled)

Base worst day by period: FIT −48.1R, T2 −36.0R, CHECK −45.7R.

| rule | days fired / yr | dR | saved / lost (R) | worst day FIT / T2 / CHECK | dR FIT / T2 / CHECK | t | dR_neutral | dR_book_p10 |
|---|---|---|---|---|---|---|---|---|
| A6 | 112.6 | +534 | 1647 / −1113 | −9.9 / −10.6 / −12.0 | +345 / +48 / +142 | 2.46 | +225 | −134 |
| A8 | 83.7 | +431 | 1246 / −815 | −10.6 / −12.3 / −13.4 | +303 / −11 / +138 | 2.25 | +246 | +32 |
| A10 | 60.0 | +452 | 944 / −492 | −12.7 / −13.5 / −40.7 | +252 / −6 / +207 | 2.94 | +339 | +207 |
| **A12** | **44.7** | **+351** | **727 / −377** | **−18.5 / −16.2 / −40.7** | **+208 / +28 / +115** | **2.63** | **+284** | **+205** |
| L2 | 194.6 | +404 | 983 / −578 | −39.4 / −22.7 / −34.9 | +203 / +68 / +133 | 2.86 | +15 | −438 |
| LF2 | 194.6 | +587 | 1962 / −1375 | −11.5 / −11.2 / −9.2 | +334 / +38 / +215 | 2.56 | +205 | −240 |
| N4 | 143.2 | +547 | 1254 / −707 | −39.4 / −15.8 / −25.1 | +306 / +107 / +134 | 3.30 | +22 | −590 |
| N8 | 83.7 | +231 | 442 / −210 | −39.4 / −23.8 / −34.8 | +131 / +16 / +85 | 2.45 | +47 | −167 |

**Bootstrap, A12:** median +101R a year, 5th–95th percentile +38 to +164R, P(dR > 0) = 0.996.

**Per setup under A12 (dR FIT / T2 / CHECK):** all 3 gap-down shorts gain, and NM-ETF is roughly flat.
- L3: +61 / +9 / +111
- RW3: +81 / +4 / −8
- RW5: +68 / +8 / +16
- NM-ETF: −2 / +7 / −4

**Live replay** (Primary, 10-23..11-23, 22 sessions; base −87.3R, worst day −34.8R):

| rule | days fired | total | dR | worst day |
|---|---|---|---|---|
| A10 | 8 | −36.0R | +51.4R | −21.2R |
| A12 | 7 | −51.4R | +36.0R | −21.2R |

- A12's live gain came mostly from setups no longer in Primary (MF2/MF4, +30.8R); the 4 current setups net about +1.6R.
- None of these rules would have fired today: the day's low was −4.1R.
- This live window is what prompted the question, so it is a sanity check, not evidence.

### Recommendation

**A12: Yes, as tail insurance, not as edge.** When Primary's closed + open R after costs reaches −12R, flatten every lot and take no new entries for the rest of the day.

**Why A12:**
- It is the only rule that passes every pre-registered test: the worst day improves in FIT, T2 and CHECK, dR ≥ 0 in all three, and t is 2.63 against a bar of 2.38.
- It stays positive with the book re-priced to zero expectancy and to +0.10R per lot.

**Limits:**
- It misses the lineage bar of 2.86, and CHECK alone has t of only 1.21.
- It fires about 45 days a year on the bench.
- It cannot cap a one-minute shock.
- It cuts some recovery days.

**Process:** Primary changes go in at the Friday epoch, after a skeptic review, with a ledger entry.

**The bigger problem is the book:** −0.086R per lot on the bench and −0.105R per trade live. No stop fixes that.

## Part 2: 11-23

SPY was +4.4% by 09:59 and held between +4.4% and +5.1% all day. Primary took 24 trades and finished +0.49R after costs.

- **"6/7 for +4.1R" holds at 14:20.** At that point 15 lots were open at −6.7R. The book's low was −4.1R at 14:25, and it recovered to +0.49R by the close.
- **Win rate needed:**
  - Short targets sit around 0.84R against a 1R stop plus costs.
  - Today's average win was +0.61R and average loss −0.80R, so breaking even needs about 57% winners. Today had 58%.
  - Live since 10-23: 50.8% winners, +0.68R / −0.91R, for −0.105R per trade.
- **Holding time:** winners held a median 101 minutes, losers 184.
  - 10 of 18 shorts hit neither target nor stop and were flattened at 15:55, for −2.57R.
  - Shorts' median MFE was +0.24R and median MAE −0.69R.
  - 9 shorts never got to +0.25R in profit, and those 9 made −5.74R.
- **Timing:**
  - Shorts entered before 11:00 made +2.34R.
  - Shorts entered after 11:00 made −4.84R, almost all from 11:30–13:10 entries into a market holding +5%.
- **Not a pile-on:** only 4 shorts were entered while open R was below −2R, and they netted −0.04R.

## Rule-change context

- 10-29: Primary −2R latch.
- 11-11: TEAM-6 lineup with NM-ETF.
- 11-12: LR8 costs and LR3.
- 11-19: NS5 out.
- 11-20 / 11-23: burst brake.
- 11-23: ST7 out; PSHADOW.

The live replay pools whatever setups were in Primary on each day, so lineups are mixed.
