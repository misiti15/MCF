# flow1_1104: the book as a sensor (owner FLOW1, 2026-11-04)

*Educational only — not financial advice.* Live **paper** results (rule 7); no backtest was run (see failures).
Research only: nothing in config/, mcf/, setups, exits, docs/live or the ledger changed. Pre-registered in `PLAN.md`
(commit e8d9d5b5a, pushed before any result was computed). Code `flow1.py`; tables `results_live.csv`,
`regress_live.csv`, `picture_live.csv`, `out_live.txt`.

**Configurations: 64 live FLOW1 configs (4 T × 2 k × 2 measures × 2 rules × 2 books) + 16 SPY/VWAP control rules.
Pre-registered N = 96 (incl. 32 lab) → bar t ≥ 3.02; on the 64 actually scored, bar 2.88. Nothing reaches either.**

## Failures first
- **The 2-year lab half was NOT run.** This container has no lab frames (`research/history2y/data/` absent, no
  `headtail.parquet`, no latch_1103 `bt/sig_*.parquet`). Rebuilding them means a 2-year 1-min download of ~3,000 names,
  which would compete with the live data budget during market hours. TRAIN / VALID are therefore **untested**; the
  locked block was not touched. `flow1.py` takes a trade table, so the lab run is: latch_1103 `bt_all.py` → caps →
  same scoring (TODO for an off-hours session with the frames).
- **Live: no rule reaches the bar.** Best by day-clustered t:
  - Merged (5 accounts, 21 days, 13,032 trades): 10:15, win share, filter: **+762R, t 2.42**; w/o best day +530R
    (best day 30%).
  - Primary (21 days, 804 trades): 10:15, sumR, filter: **+2.8R, t 1.41**; w/o best day +1.1R (best day 61%).
    Primary has ≥ 3 early closes on a side on only 5-14 of 21 days.
- **The raw gains are mostly "trade less in a losing book".** Merged later trades average −0.10R, so dropping almost
  anything adds R. The excess delta (dropped trades scored against the book's own mean) shrinks the best merged filter
  to +444R, t 1.78. 10:30 sumR filter: +425R raw, excess +18R (t 0.07).
- **It mostly restates SPY.** Merged at 10:15, the plain SPY-vs-open rule makes +763R (t 2.32). FLOW1's kept trades
  and dropped trades have the same avg R as the SPY rule's (−0.09 / −0.14 vs −0.09 / −0.14). Added on top of the SPY
  rule, the best FLOW1 filter makes **+80R, t 0.76**; every merged on-top-of-SPY t is ≤ 1.09 (Primary ≤ 1.45). The side's early-close sign
  correlates with side × SPY-from-open at T: r = 0.16 at 10:15, 0.39 at 10:30, 0.49-0.51 at 11:00 (merged).
- **Regression (trade R on the book signal, clustered by day, merged).**
  - With the SPY and VWAP terms in, the book-sign coefficient has |t| ≤ 0.92 at every T and k.
  - The book avg-R term at 11:00 is **negative**: t −2.03 with SPY in, i.e. contrarian, not confirming.
  - Primary: 5-14 days per cell, with signs that flip between T and k. No usable signal.

## The simple picture (T = 10:30; later = trades entered after 10:30, same side)
| book | side | first k closes | days | later trades | win | avg R |
|---|---|---|---|---|---|---|
| merged | short | k=3 green | 9 | 2,017 | 54.8% | +0.044 |
| merged | short | k=3 red | 10 | 1,685 | 43.0% | −0.174 |
| merged | long | k=3 green | 9 | 2,671 | 50.4% | −0.171 |
| merged | long | k=3 red | 7 | 1,680 | 57.3% | −0.097 |
| merged | short | k=5 green / red | 7 / 12 | 1,271 / 2,431 | 46.5% / 51.0% | −0.104 / −0.030 |
| merged | long | k=5 green / red | 9 / 7 | 2,812 / 1,539 | 53.5% / 52.4% | −0.135 / −0.157 |
| primary | short | k=3 green / red | 3 / 5 | 70 / 173 | 67.1% / 67.1% | +0.164 / +0.370 (w/o best day +0.080 / −0.093) |
| primary | long | k=3 | 0 green / 1 red | — | — | too few |

- Only merged shorts with k=3 look the way the owner expects. Merged longs with k=3, k=5 shorts and Primary shorts all
  go the other way. On 7-12 days per cell, that is noise.

## Day type (SPY open→close ±0.25%; diagnostic)
- For the best merged filter (10:15, win share), the gain is positive on up, down and quiet days (+238 / +295 / +228R).
  The SPY rule shows the same pattern.

## Rule changes inside the live window (research/ledger.jsonl)
- **Accounts opened mid-window:**
  - Testing 1 data from 10-09; Testing 2 opened 10-12.
  - Setup Generator opened 10-19 and was paused after 10-28; its caps went 80 → 200 on 10-26.
  - Graveyard opened 10-21.
  - So the merged book changes shape over the window.
- **Primary sizing:** ~$5k then ~$4k per position (10-28).
- **Stops and latches:** per-setup −2R latched daily stop in Primary (10-29), latch semantics (10-23), per-setup stop
  off in Testing (10-23).
- **Entry timing and costs:** GX1 5-minute clock gate (10-27), Testing cost filter CF (10-30).
- **Setup moves:** promotions on 10-20 and 10-26, demotions on 10-20, 10-26 and 10-27, rotations on 10-28, Graveyard
  moves throughout.

## Verdict
**FYI, parked.**
- No lab TRAIN / VALID evidence: not run here.
- Live best t is 2.42, below the 3.02 bar.
- The edge over SPY is nil (on-top t 0.76).
- The simple picture is inconsistent.
- A nightly forward-shadow tally was added to `research/bdi/swings/hypotheses.jsonl` (`flow1-book-sensor`). No
  DECISION card.
