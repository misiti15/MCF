# LATCH-OPEN on the Monday roster (critic gaps 1-2)

Educational only — not financial advice. 2026-11-28, about 02:45 ET.

## What was asked
- LATCH-OPEN's figures (11-25: −40 → −8R; bench days ≤ −20R: 33 → 8) all came from the 4-setup book that includes L3.
- If the owner takes L3 out, Monday's book is **roster A = RW3, RW5, NM-ETF**. If L3 stays, it is **roster B = A + L3**.
- This note replays both rosters, each with the −2R latch counting closed R only and with it counting closed + open R (LATCH-OPEN).
- It sets LATCH-OPEN's saving beside an exposure-matched random cut, which the critic said was missing (gap 2).

## Basis
- **Configs: 4** (roster A / B x closed-only / closed + open). The controls are not configs. The running count goes from about 9,656 to **about 9,660**.
- **Bench:**
  - bench10 lots for the 4 Primary setups were rebuilt tonight (research/squeeze_1125/gen.py, unchanged).
  - Filters and LIVE-L costs on the shorts are as in research/primshorts_1126/bench_build.py. NM-ETF keeps LR8 research costs.
  - The engine is research/primshorts_1126/booksim.py, unchanged. Its Primary book rules are: 77 open lots, 30 per setup, 3 per setup per symbol, the burst brake, the −2R per-setup latch and the −20R halt.
  - Windows: CHECK (2025-10-01..2026-11-04, 276 sessions) and T2 (2023-01-03..2024-09-13, about 410 sessions). FIT is not used.
  - The locked holdout 2024-11-01..2025-02-28 was never read; the build asserts on it.
  - **Parity:** roster B closed-only on CHECK is −3.03 R/day and roster A is −2.08. These equal primshorts_1126's "a keep" and "b L3 → On Deck" rows exactly.
- **Live:**
  - Primary journal, run 1, 10-23..11-27, 25 sessions, LR8 cost-R, as in roster_options.py.
  - Roster A's journal total is 361 lots and −27.0R. The closed-only replay keeps 352 lots for −25.7R.
  - Open marks come from Alpaca SIP 1-minute closes (GET only).
  - The replay can only drop lots that were taken live.
- **Controls:** 400 draws each, static removal, so freed slots are not refilled.
  - **ctrl-day (the pre-stated control):** on each day, remove as many lots as LATCH-OPEN removed that day, picked at random from that day's lots.
  - **ctrl-setup (sensitivity):** the same, but random within the same setup on the same day.
  - **ctrl-any (sensitivity):** the same total number of lots, removed at random across the whole window. This is a plain size cut.
  - "pct" is the share of draws that LATCH-OPEN beats. Higher is better for LATCH-OPEN.
- **Rule changes inside the live window** (research/ledger.jsonl; a selection):
  - 10-27 GX1.
  - 10-28 sizing.
  - 10-29 the closed −2R latch goes live.
  - 10-30 L3 back in Primary.
  - 11-12 LR8/LR3.
  - 11-17 TSZ1.
  - 11-19 Epoch 1 / U9-TGT / DQ-P4.
  - 11-23 burst brake.
  - The live closed-only replay therefore matches what Primary actually ran only from 10-29 on.
- **After the window:**
  - AV50 (NM-ETF burst tight stop) is effective 11-30. Neither the bench nor the replay models it.
  - It touches NM-ETF only, which is about 4% of roster A's lots.

## Results

### Roster A (RW3, RW5, NM-ETF): the Monday roster if L3 goes out
| | CHECK closed | CHECK +open | T2 closed | T2 +open | Live closed | Live +open |
|---|---|---|---|---|---|---|
| R/day | −2.08 | **−1.28** | −1.42 | **−1.22** | −1.03 | **−0.31** |
| Red days | 169/276 | 172/276 | 251/408 | 254/408 | 14/25 | 14/25 |
| Days ≤ −20R | 9 | **2** | 1 | **0** | 2 | **0** |
| Days ≤ −10R | 39 | 15 | 18 | 9 | 2 | 1 |
| Worst-5 days | −148.1 | −97.2 | −104.8 | −63.0 | −66.6 | −41.4 |
| Worst day | −34.6 | −24.2 | −35.1 | −14.7 | −25.4 | −13.8 |
| R/day without best day | −2.26 | −1.40 | −1.46 | −1.26 | −1.86 | −0.73 |
| Lots | 6,119 | 4,719 (−23%) | 3,793 | 3,314 (−13%) | 352 | 283 (−20%) |
| Saving, R/day (day t) | | +0.80 (3.0) | | +0.20 (2.3) | | +0.72 (0.9) |
| Saving without the best saving day | | +0.72 (best day = 11%) | | +0.14 (28%) | | +0.23 (**70%, `1 day`**: 11-10) |

### Roster B (A + L3): if L3 stays
| | CHECK closed | CHECK +open | T2 closed | T2 +open | Live closed | Live +open |
|---|---|---|---|---|---|---|
| R/day | −3.03 | −2.04 | −1.80 | −1.58 | −0.97 | −0.26 |
| Red days | 172 | 167 | 249/415 | 253/415 | 14 | 14 |
| Days ≤ −20R | 19 | 7 | 4 | 0 | 2 | 0 |
| Days ≤ −10R | 62 | 39 | 31 | 22 | 3 | 1 |
| Worst-5 | −178.1 | −128.4 | −122.0 | −72.4 | −102.3 | −50.9 |
| Saving R/day | | +0.99 (t 2.8) | | +0.22 (t 2.1) | | +0.71 (t 0.4; 11-25 = 180% of it) |

### Per setup (the remedies rule)
**Bench, roster A, LATCH-OPEN vs closed-only:**
- RW3: +82R on CHECK, +24R on T2.
- RW5: +138R on CHECK, +58R on T2.
- NM-ETF: +0.9R on CHECK, 0 on T2.
- No setup gets worse in either window. Roster B is the same picture: L3 +63 / +10R.

**Lots skipped by LATCH-OPEN:**
- CHECK: −0.158R per lot, against a book average of −0.094.
- T2: −0.169R per lot, against −0.153.

### Against the exposure-matched control (roster A)
| | CHECK | T2 | Live |
|---|---|---|---|
| **ctrl-day** R/day (median) vs LATCH-OPEN | −1.20 vs −1.28 → **pct 16** | −1.07 vs −1.22 → **pct 0** | −0.17 vs −0.31 → **pct 20** |
| ctrl-day worst-5 | −109 vs −97 → **pct 100** | −70 vs −63 → **pct 100** | −38 vs −41 → pct 9 |
| ctrl-day days ≤ −20R | 4 vs 2 → pct 98 | 0 vs 0 → tie | 0 vs 0 → tie |
| ctrl-day days ≤ −10R | 18 vs 15 → pct 93 | 9 vs 9 → pct 63 | 1 vs 1 → tie |
| ctrl-day red days | 167 vs 172 → pct 6 | 247 vs 254 → pct 0 | 14 vs 14 → tie |
| ctrl-setup R/day | pct 1 | pct 0 | pct 0 |
| ctrl-any (plain size cut) R/day | −1.61 → **pct 100** | −1.24 → pct 65 | −0.85 → pct 97 |
| ctrl-any worst-5 / ≤ −20R | pct 100 / 99 | pct 100 / 100 | pct 100 / 82 |

**What the control says, in plain words:**
1. **LATCH-OPEN beats a plain size cut.** Trading 20% smaller every day saves less R and cuts the bad days less, in all three samples. So LATCH-OPEN is better than "just trade smaller", and the gain comes from **which days** it acts on.
2. **Within a bad day, its choice of lots is no better than random. It is slightly worse for total R.**
   - Removing the same number of lots at random on the same days saves as much or more R. LATCH-OPEN sits at the 0-20th percentile on R/day and adds about 3-7 red days.
   - The reason: the lots it skips are the late ones, after −2R. Some of those late lots recover. A random cut also removes the early lots that caused the loss.
   - This matches the shorts_autopsy reviewer and rules_1122: the latch works as a day-level cut.
   - A random same-day cut is **not a rule anyone could trade**: it needs to know in the morning that the day will be bad. LATCH-OPEN is the real-time way to find that out.
3. **Tails:** on the bench, LATCH-OPEN cuts the worst days **harder** than the random same-day cut (worst-5 at the 100th percentile on CHECK and T2; ≤ −20R days at the 98th percentile on CHECK). In the 25 live sessions it does not (worst-5 at the 9th percentile).
4. **Bottom line:** the saving is real against a plain size cut and against doing nothing. It is not a lot-picking skill. Forward, the right bar is "beats a same-size constant cut on fire days and does not lose to a random same-day cut by more than X". The plain "skipped lots ≤ 0R" bar would pass almost automatically (critic gap 2).

## Honest numbers for D1 and MONDAY_PLAN (roster A)
- **Weekly R from LATCH-OPEN (5 sessions):**
  - CHECK +4.0 R/wk (+3.6 without the best saving day).
  - T2 +1.0 (+0.7).
  - Live +3.6, but **+1.1** without 11-10.
  - **An honest range is about +1 to +4 R/wk**, all from trading about 13-23% fewer lots in a losing book.
  - The old "+1 to +6 R/wk" was for both changes on the 4-setup book. With L3 out, the remaining L3-OUT gain is the CHECK +0.95 / T2 +0.39 R/day of primshorts_1126 (+2.0 to +4.8 R/wk before LATCH-OPEN). L3-OUT plus LATCH-OPEN together, against today's book: CHECK −3.03 → −1.28 R/day (+8.8 R/wk) and T2 −1.80 → −1.22 (+2.9 R/wk). Live: −0.97 → −0.31 (+3.3 R/wk; noise, t < 1).
- **The book is still negative:** roster A with LATCH-OPEN is about **−6 R/wk** on the bench (−1.28 / −1.22 R/day) and −1.6 R/wk on the live window.
- **Days at −20R or worse** (scaled at 252 sessions a year):

  | Book | Closed-only latch | With LATCH-OPEN |
  |---|---|---|
  | Roster A, CHECK | 9 in 276 sessions, about 8 a year | 2, about **1.8 a year** |
  | Roster A, T2 | 1 in 408 | 0 |
  | Roster A, CHECK + T2 pooled | about 3.7 a year | about **0.7 a year** |
  | Roster B, pooled | about 8.4 a year | about **2.6 a year** |

  - The 2.6 a year for roster B matches the old "about 3 a year" claim.
  - So "about 3 a year" was the 4-setup figure. **With L3 out it is about 1-2 a year** (CHECK alone, the recent and harsher window: 1.8).
- **Days at −10R or worse, roster A:** CHECK 39 → 15 (about 36 → 14 a year); T2 18 → 9.
- **Red days:** unchanged or slightly more (+3 on each bench window; live 14 → 14). LATCH-OPEN does not make more days green.

## Caveats
- Live: 25 sessions. The saving is t 0.9 and carries the `1 day` tag (11-10 = 70%).
- The live replay cannot add back lots that live rules blocked.
- The bench uses bar-close marks and models neither AV50 nor live fills beyond the LIVE-L cost model.
- T2 roster A has 408 scored sessions against roster B's 415: 7 days with no roster A lot were left out (0R days, so R/day barely changes).
- All controls are static removals, so freed slots are not refilled.

**Files** (exploration/sandbox/latchopen_monday/):
- Scripts: bench.py, live_replay.py, score.py.
- Outputs: score_bench.txt, score_live.txt, live_days.csv.
- Inputs not in git (rebuildable): bench10 WORK, cand.parquet / paths.npy, the journal copy, the minute grid.

Educational only — not financial advice.
