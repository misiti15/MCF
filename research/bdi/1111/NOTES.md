# BDI 2026-11-11 (Wednesday), LEAN run: Move Hunt (capture 2 %), Primary swing autopsy, LATCH-CLOSE pre-registered and passed on 2 years → DECISION

*Educational only — not financial advice.* Live **paper** results from one session, plus one 2-year **backtest** (labelled).
**Configurations tried tonight: 1** (LATCH-CLOSE). Builds on research/bdi/nightly1111/NOTES.md (not redone).

**Lean run (usage tight).** Done: Move Hunt, Primary swing autopsy, one pre-registered lead (LATCH-CLOSE), owner-inbox FYIs.
**Skipped:** full per-trade analysis, swarms / new setup tests, other accounts' autopsies, precursor scan, other forward
shadows (the nightly ran those), research/queue items.

**Rule changes in the window.** TEAM-6 on Primary from 11-11 (ledger 2026-11-10-team6-primary, frozen to 11-13); EXPO1109
revert effective 11-11; the account restructure (PRs #182/#183) and the LR fixes take effect 11-12, so they do not touch
today's data. The 2-year lab run uses the lab lists and is not affected by any of these.

**Today's win.** LATCH-CLOSE, a targeted remedy for the loss on open lots after the latch, went from a nightly pattern to a
pre-registered 2-year test and **passed** (VALID day-t 3.89 vs 2.89; 7 of 9 families better). It is now in forward shadow,
and there is a DECISION for the owner.

## 0a. Move Hunt (v1 definition unchanged; moves.csv +100 rows for 11-11; research/bdi/moves/moves_1111_out.txt)
Inputs rebuilt in scratch `mh1111/`: build.sh = coverage1029/fetch.py + fetch5.py + frames_today.py. That is 1,697 priors,
1,299 liquid names, 85,476 decision rows, 761 live trades (449 symbols) across 7 accounts.

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | 1 / 50 (2 %) | −1.01 | 10, −7.28R | earnings blackout 17, no setup 10, outside the move 9 |
| **tradable (blackout removed)** | **1 / 50 (2 %)**: long 0 / 25, short 1 / 25 | **−1.01** | 12, −9.83R | no setup 20, traded outside the move 13, wrong side only 9, skipped 7 |

**Capture rate 2 % vs 16 % on 11-10 (R −1.01 vs +6.51).** The only catch was COST short by Gen `GEN-261023-03` (−1.01R).
Hunt so far: 10-29 26 %, 10-30 6 %, 11-02 22 %, 11-03 12 %, 11-04 20 %, 11-05 2 %, 11-06 26 %, 11-09 22 %, 11-10 16 %, 11-11 2 %.

**Main miss reason.** 41 of the 50 tradable moves were decided at 09:35-09:50 (long 18, short 23), before most setups'
09:50 window opens. So "no setup" (20) and "traded outside the move" (13) dominate. This is the third day running that the
big moves started in the first 20 minutes.
- Longs were semis / tech into 11:00: MU, AMD, MPWR, AMKR, ARM, SWKS, plus ZM and CASY.
- Shorts were staples / retail at the open: COST, WMT, CLX, CPB, ELF, FIVE, ULTA, AMZN.
- Skips: three are not-ETB shorts (CORD, SNDQ, NVD) and three hit the setup daily loss limit (DUOL, CASY, TPG).

The open-window catalogue (09:30-09:50 decisions) is still the next Move Hunt step. It is not run tonight.

## 0b. Swing autopsy, Primary only (swings_p.py → swings_p_out.txt, timeline_p_1111.csv)
Method: 1110/swings.py unchanged. It marks every lot in R on 1-min bars. The parts are market (beta × SPY), setup-day
mismatch (sector-ETF residual), bad entries (fill + first 5 min) and stock-specific (the rest, incl. exits and costs).
The parts sum exactly (asserted). The top 5 names are a cross-cut of the same leg. Betas are 5-min, 09-22..11-10.

The 1-min curve peaks at **+3.00R at 12:36**; the nightly's +2.37R at 12:30 was on 5-min marks. It closes at
**−26.63R**, which matches the journal. SPY was +0.54 % at 12:36 and +0.36 % at the close.

**Split of the 12:36 → close swing, −29.63R (−$854):**

| part | R |
|---|---|
| (a) market beta | **+2.00** (the net-short book gained as SPY slipped 0.18 %) |
| (b) bad entries | **−0.61** |
| (c) setup-day mismatch | **−13.82** |
| stock-specific rest | **−17.20** |
| check (sum) | −29.63 |

**(d) Top 5 names** (a cross-cut, inside (c) + rest), together −10.48R:
1. HGTY, Gap-Down Recovery Fade (all day) (`L3-gap-slope-fromopen-FD`), 3 lots: −4.78R
2. WEC, Gap-Down Pop Fade, Heavy Selling (all day) (`RW3-gapdn-rsi5pop-flowsell-short-FD`): −1.51R
3. WEC, Gap-Down Pop Fade (all day) (`RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`): −1.50R
4. PGR, Gap-Down Pop Fade, Heavy Selling (all day) (`RW3-gapdn-rsi5pop-flowsell-short-FD`): −1.41R
5. HNGE, Big Loser Flush Buy (`NS5-sma50-flush-oversold-long`): −1.29R

By setup: RW5-FD −14.4R, RW3-FD −10.3R, L3 ≈ −4.8R, NS5 −0.7R.

Context for the leg:
- 18 shorts were entered inside it; their final average was −0.678R.
- The short book grew from 20 lots at 12:36 to 33 at 13:54, with net beta about −9..−13R per +1 % SPY.
- The morning leg (09:50 → 12:36, +3.00R) split as market −1.58, mismatch +2.26, entries −0.94, stock +3.26.

**What turned it.** A tech-out / defensives-in rotation from about 12:36. From 12:36 to the close, XLK fell 1.12 % and QQQ
0.63 %, while XLP rose 1.04 %, XLV 0.75 %, XLF 0.51 % and XLU 0.46 %. SPY barely moved (−0.18 %).
- Primary's gap-down fade shorts sit in exactly those groups: staples, health, insurance and utilities (WEC, DEO, PFE,
  PGR, MCD, AEP, CNP). Those names rose with their sectors (mismatch −13.8R), plus name-level bounces (−17.2R).
- The book kept adding shorts into the rotation. The latches (13:57 / 14:25 / 15:20) stopped new lots, but left the open
  ones on the bet.
- It was not market beta (+2.0R). It is the same rotation as 11-10's first leg (XLK −1.12 % / XLP +0.71 %); 2 instances so
  far. Not added as a new lead tonight (lean run).

## 3. Lead: LATCH-CLOSE (`swing1111-L13`). Pre-registered, 2-year backtest PASSED, forward shadow from 11-12
- **Pre-registration first:** LATCH_CLOSE_PLAN.md and the hypotheses.jsonl line were committed and pushed as `df979d85d`
  before the read.
- **Rule:** when a setup's −2R per-setup latch fires, close that setup's still-open lots at the close of the next 5-min bar,
  minus the exit-side 1c + 1 bp. Both sides, every setup, no filter.
- **Backtest:** latch_close.py → latch_close_out.txt (+ latch_close_lots.csv.gz). One config. It runs on the bt_lab1104 lab
  lists plus burst1 5-min marks, with live caps (3 / symbol, 30 open / setup) and the stoplab lab2y latch rule.
- **Costs and holdouts:** production costs are in. The locked block 2024-11-01..2025-02-28 is excluded (asserted).
- **Pass bar:** lineage N 65 (stoplab grid-A 64 + 1), so t ≥ 2.89.

**Backtest results:**

| split | lots / days | delta (rule − actual) | day-t | days better |
|---|---|---|---|---|
| TRAIN | 54,380 / 234 | **+3,241.0R** (+0.060 / lot) | 6.33 | 70 % |
| VALID | 53,783 / 190 | **+1,684.1R** (+0.031 / lot); w/o best day (07-30, +127R) +1,557R | **3.89** | 63 % |
| LATE (10-06..11-04) | 6,295 / 22 | +169.5R | 0.98 | 64 % |

- **By side:** VALID shorts +722.7R and longs +961.4R. LATE shorts −7.1R and longs +176.6R.
- **Families, VALID (≥ 30 affected lots), 7 better / 2 worse:**
  - Better: CWT +1,188.2R, RW +237.3R, exhaustion +117.0R, NS +97.3R, L +73.0R, MF +38.5R, ST +25.4R.
  - Worse: **GEN −62.6R** and **NM −30.0R**.
- **Setups, VALID (≥ 20 affected lots): 54 better (+2,208.3R) / 32 worse (−498.4R) of 86.**
  - Worst: MF1-945-flowsell-vwapup-FD −76.8R, GEN-261019-10 −61.9R, NS3-failed-vwap-reclaim-short-FD −32.6R,
    GEN-261021-02 −29.4R, CWT12-coil-k6-long −28.7R, NS5-FD −26.5R.
  - TEAM-6 setups: RW5-FD +48.1R, L3-fromopen-FD +28.3R, RW3-FD +25.6R, ST7 −3.6R, NS5 −0.3R.
  - The full list is in latch_close_out.txt.
- **Verdict: PASS.** VALID t 3.89 ≥ 2.89; TRAIN delta > 0; VALID without its best day > 0; families 7 / 9 (≥ 60 %).

**Honest caveats.**
- Lab books are larger than live: 49 % of lab setup-days latch.
- The per-lot gain is small (+0.03..0.06R). The rule trims a negative-expectancy open book: affected lots average −0.26R
  either way. It does not create edge.
- LATE is positive but not significant.
- The live split "fade shorts better, dip-buy longs worse" is **not** confirmed on 2 years: CWT14 pdl / orl longs are
  among the biggest gainers. CWT12-coil-k6-long (live-worse on 11-11) is also worse in the lab. GEN is worse in both.
- The latch trigger in the lab uses cost-in r. Live uses gross r_multiple.

**Live record** (latch_close_live.py, exact rule, both days in-sample):

| day | Primary | On Deck | Testing A | Graveyard | Gen | total | setup-days better / worse |
|---|---|---|---|---|---|---|---|
| 11-10 | +11.43R (5 / 0) | +11.67R | +0.78R | +0.04R | −0.43R | **+23.49R** | 16 / 12 |
| 11-11 | +5.50R (2 / 0) | +3.64R | +8.32R | +37.81R | −4.90R | **+50.37R** | 25 / 3 |

- On 11-11 the next-bar close gives Primary +5.50R vs +11.02R at the latch minute: the lots bled further in the 5-10 min
  wait.
- The nightly's latch-minute check, across the other accounts: 24 better / 3 worse (11-11), 19 / 4 (11-10). Both days
  point the same way.

**Forward shadow.** Added: `swing1111-L13` in hypotheses.jsonl; rows in research/bdi/swings/forward.csv; run
`latch_close_live.py <scratch> <day>` nightly. Bar: ≥ 15 latch sessions, pooled delta > 0 and > 0 on ≥ 60 % of them.
Backlog `nightly-1110-latch-closes-open-lots` → forward_wait, configs_tried 1.

## 5. Decision
**LATCH-CLOSE** (owner_inbox 2026-11-11). Reply codes:
- "LATCH-CLOSE testing": On Deck and the Testing accounts first. Recommended.
- "LATCH-CLOSE all": incl. Primary. Primary is mid-TEAM-6 trial (frozen to 11-13), so this is the owner's call.

Implementation (runner + ledger + tests) is the main session's job, outside 09:30-16:00 ET. No live config changed here.

Files: LATCH_CLOSE_PLAN.md, latch_close.py (+ _out.txt, _lots.csv.gz), latch_close_live.py (+ _1110 / _1111 outputs),
swings_p.py (+ swings_p_out.txt, timeline_p_1111.csv); research/bdi/moves/moves_1111_out.txt.
Scratch (session scratchpad, deleted after): `mh1111/` (build.sh), `lc1111/enr` (burst1/enrich.py). Educational only — not financial advice.
