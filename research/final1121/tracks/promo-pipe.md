Educational only — not financial advice.

# Promotion pipeline (track promo-pipe), 2026-11-21

## Bottom line
1. **No setup is ready for Primary in the 11-27 Friday window.** The promotion hold is still on as well.
2. **Ranked list:**
   1. L3-gap-slope-lowdist-FD
   2. L3-gap-slope-rsi5hi-FD
   3. RW7-gapdn-bounce-early-short-FD
   4. CWT09-gapdn-vwaploss-g10-short
   5. GEN-261029-06 (early watch only)
3. **RW1-FD is not a candidate.**
4. **The RW7-FD watch needs a stricter bar.**
   - Replayed under Primary's own book (30-lot cap per setup, at most 3 lots per symbol, -2R per-setup latch), its +60.1R falls to +18.1R, and avg R w/o best day is -0.027.
   - It does no better than random entries on the same stock-days (p 0.83).
   - Before 11-16 it was -14.0R in On Deck. All of its R comes from 5 Testing F sessions; 11-20 alone is +40.2R.
   - A best-day-share pass alone would promote something that loses under Primary's rules.
5. **Goal check (positive R daily in Primary):**
   - Every ranked candidate except CWT09 is a down-tape short that moves with the current five (daily corr +0.24 to +0.58). None of them adds R on the five's red days.
   - Promoting any of them adds R on good days and does not fix red days.
   - CWT09-g10 is the only uncorrelated record with positive R (corr -0.04, +2.8R on red days), but it has 24 trades.
6. **Recommended new bar item:** replay every candidate's trades under the Primary book before naming it. Call it PB-REPLAY: avg R w/o best day > 0 after the latch and cap.

## Data and method
- **Live trades:** rebuilt from the 10 journals (`origin/mcf-data*`, fetched 11-21) through **2026-11-20**.
  - Run-1 de-dup as in `footrace.live_trades()`, LR8 cost-R. 29,564 trades.
  - Saved to `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe/live.pkl`.
- **Records shown:** raw (pooled across accounts) and two non-overlap records.
  - **A:** drops symbol-days the Primary account traded. This is what the 11-20 brief used.
  - **B:** drops symbol-days any of the current five traded in any account. Stricter, and closer to "what it adds on top of today's Primary".
- **Columns:** day-clustered t, w/o best day, w/o top-2 days, best-day share, shrunk estimate n/(n+150)·avg + 150/(n+150)·(−0.10).
- **Primary-book replay:** Primary's lot cap, symbol cap and latch applied to the journal entry and exit times (`primbook.py`).
- **Null:** `research/whatworks_1120/null/null_results.csv` (±30-min random-entry null on the same stock-day, day-clustered p, through 11-19).
- **Lab:** `research/ultimate_1119/top10/bench10.py`, copied unchanged except the setup list and an extra Primary-rules book view.
  - Run for RW7-FD and RW1-FD, the two not already benchmarked. The others come from `top10/benchmark.json`.
  - FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..2026-11-04, scored once; T2 = 2023-01..2024-09.
  - **The locked block 2024-11-01..2025-02-28 was never read** (the lib asserts on every load).
- **Configs:** 2 frozen setups × 3 book views = **6 lab scorings, 0 fitted parameters.** The job's cumulative N stays about 1,882.
  - WB2 bar max(1.5, sqrt(2 ln 1882)) = **3.88**. No live day t reaches it; the highest is 3.51, rsi5hi on non-overlap B.
- **Scripts:** in `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe/`.
  - `load_live.py`, `live_stats.py`, `bar2.py`, `lineup.py`, `primbook.py`, `bench/benchpp.py`; output in `bench/benchmark.json`.

## Primary context (LR8)
- **Primary account, 10-06..11-20:** −76.6R in total. +16.0R since 11-11 (TEAM-6 / C3).
- **The current five, pooled across all accounts:** +148.8R, green on 19 of 34 sessions.
- **Leak:** NM-ETF −11.45R and ST7-FD −6.08R inside Primary.

## Screen: every setup with ≥ 15 traded sessions, avg R > 0 and w/o best day > 0
- **Primary members:** L3-fromopen, RW3-FD, RW5-FD.
- **Others:** only RW7-FD, L3-lowdist-FD and L3-rsi5hi-FD.
- **Nothing from the Graveyard, the GEN account or the WB copies qualifies.**
- **Near misses with fewer sessions:**
  - CWT09-g10: 13 sessions, 24 trades.
  - GEN-261029-06: 10 sessions, `1 day`.
  - GEN-261026-07: 8 sessions, 93% best day.

## Candidate table (live LR8 through 11-20)

| # | setup | n / sess | avg | w/o best | w/o top-2 | day t | best day share | shrunk | non-overlap A: n, shrunk, share | non-overlap B: n, shrunk, share | Primary-book replay: R, w/o best | null edge (p) | corr with the five | R on the five's red days (green) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | L3-lowdist-FD | 111/20 | +0.237 | +0.103 | −0.017 | 1.70 | 69% (11-12) | +0.043 | 84, +0.016, 0.498 | 52, −0.016, 0.80 | +26.3, +0.103 | +0.163 (0.004) | +0.58 | −6.3R (3/11) |
| 2 | L3-rsi5hi-FD | 167/25 | +0.096 | +0.022 | −0.046 | 1.03 | 82% (11-12) | +0.003 | 108, +0.022, 0.33 | 69, −0.003, 0.44 | +15.8, +0.021 | +0.083 (0.025) | +0.53 | −14.1R (2/11) |
| 3 | RW7-FD | 872/28 | +0.069 | +0.024 | +0.005 | 0.95 | 67% (11-20) | +0.044 | 773, +0.045, 0.65 | 757, +0.042, 0.69 | **+18.1, −0.027** | −0.022 (0.83) | +0.24 | −35.7R (5/11) |
| 4 | CWT09-g10 | 24/13 | +0.228 | +0.151 | +0.087 | 1.64 | 48% | −0.055 | 20, −0.052, 0.42 | 19, −0.052, 0.42 | +5.5, +0.151 | −0.036 (0.82) | −0.04 | +2.8R (5/11) |
| 5 | GEN-261029-06 | 222/10 | +0.131 | +0.040 | −0.016 | 1.29 | 75% | +0.038 | – | – | – | +0.097 (<0.001) | +0.12 | 0.0R (3/8) |
| x | RW1-FD | 243/29 | +0.014 | −0.027 | −0.052 | 0.18 | 277% | −0.029 | 177, −0.041 | 172, −0.041 | −5.8, −0.079 | −0.069 (0.96) | +0.34 | −30.9R (3/11) |

## 2-year lab (bench10 engine, home book, LR8 + borrow)
- **The standard:** T1 comb ≥ −0.038, check ≥ −0.046, T2 ≥ −0.105. The standard's medians are negative, so "meets" means "backtests no worse than our live winners", not "profitable in backtest".

| setup | T1 fit | T1 check (t) | T1 comb (t) | T2 (t) | R/session comb | SPY up / down days | top-10 standard |
|---|---|---|---|---|---|---|---|
| RW7-FD (new run) | −0.105 | −0.018 (−0.75) | −0.047 (−2.37) | −0.112 (−4.68) | −2.11 | −0.29 / +0.14 | FAIL (3 legs) |
| RW7-FD, Primary rules | −0.135 | −0.032 | −0.067 (−3.6) | −0.143 | −2.17 | | REALLY BAD (leg 1) |
| RW1-FD (new run) | −0.112 | −0.008 (−0.28) | −0.041 (−1.90) | −0.104 (−3.29) | −0.55 | −0.28 / +0.14 | NEAR |
| L3-lowdist-FD (benchmark.json) | −0.112 | −0.104 (−2.37) | −0.107 | −0.086 | −0.73 | −0.30 / +0.15 | FAIL (L3-fromopen −0.085 too) |
| L3-rsi5hi-FD | +0.010 | −0.020 | −0.010 | −0.084 | −0.14 | | MEETS |
| CWT09-g10 | +0.053 | +0.054 | +0.054 | −0.181 | +0.08 | −0.23 / +0.17 | T1 meets, T2 fails |

- **These are all down-tape shorts.** They lose on SPY up days and win on down days, like Primary's three shorts. That is why they cannot fill Primary's red days.

## Per-candidate evidence bar for the next window(s)
1. **L3-lowdist-FD.** Strongest live edge per trade, unchanged under Primary's book, and improving (halves +0.076 → +0.364).
   - Still needs best-day share < 50%: about +10R without a new best day. PRIME's ≤ 40% needs about +19R.
   - Strict non-overlap shrunk > 0: about 15 more unique trades.
   - A compatibility gate vs L3-fromopen: about 50% of its trades are on L3-fromopen symbol-days.
   - Plus the owner's yes, the hold lifted, and the skeptic review.
   - Earliest realistic: mid/late December.
2. **L3-rsi5hi-FD.** Passes C3-BAR2 on record A as written.
   - Fails PRIME's best-day share (82% raw).
   - The 2nd half is flat (+2.1R on 90 trades), and its 10-30..11-10 Primary stint lost −9.5R.
   - Needs 10 more sessions ≥ 0 with w/o best day > 0.
   - Needs an owner ruling on whether the non-overlap record can be the PRIME basis.
3. **RW7-FD.** Keep in Testing F under FOOTRACE-EXIT.
   - Change the pre-registered pass to also require: PB-REPLAY w/o best day > 0, and a null edge > 0.
   - Best-day share < 50% needs +20R without a new best day.
4. **CWT09-g10.** Needs 30 trades and 20 traded sessions; shrunk > 0 needs about 66 trades.
   - Watch it because it is the only diversifier.
5. **GEN-261029-06.** Early watch.
   - Needs 20 traded sessions, a best-day share < 50%, an On Deck stage and a mechanism note.
6. **Not eligible before about 2026-12-18 (20 traded sessions):** the 9 ULT admissions (1 session each, 11-20) and BEG-ORB (starts 11-23).
   - Lab leaders among the admissions: ETFDISP (+0.192 / +0.125 / +0.214) and ULT-HV2 (+0.171 / +0.196 / +0.005).
   - BEG-ORB CHECK is −0.026 (meets the standard, but is not profitable).

## Remedy note (per-setup effect)
- **PB-REPLAY is a gate on the promotion bar, not a live change.**
- **Applied to the 9 setups replayed:**
  - Unchanged: L3-lowdist-FD, RW3-FD and CWT09-g10.
  - Slightly lower: L3-rsi5hi-FD (−0.2R), RW5-FD (−1.5R) and L3-fromopen (−6.3R; its avg R per trade rises from +0.223 to +0.246).
  - Turned negative: RW1-FD (+3.5 → −5.8R) and RW6-FD (+18.8 → −5.5R).
  - Cut by 70%: RW7-FD (+60.1 → +18.1R).
- So it flags only high-frequency setups whose R depends on running past the −2R latch. This matches the live Primary evidence for the current three shorts.

## Rule-change context inside 10-06..11-20 (ledger)
- 10-23: Testing per-setup stop off.
- 10-28: Primary ~$4k sizing.
- **10-29: −2R per-setup latch.** This is why PB-REPLAY matters.
- 10-30: L3-rsi5hi-FD promoted to Primary. 11-10: it was moved out (TEAM-6).
- 11-11: TEAM-6.
- 11-12: LR8 cost basis (all figures here are re-costed on LR8).
- 11-12: ODX-1, the split-tape short gate switched off in On Deck. This affects the On Deck records of RW1, RW7, CWT09, L3-lowdist and L3-rsi5hi.
- 11-13: RW7-FD moved On Deck → Testing F, from 11-16. Its lot cap went from 150 to 100.
- 11-17: TSZ1, WB copies, promotion hold.
- 11-19: C3 Epoch 1 (NS5 out, BAR2).
- 11-20: stop-rounding fix and the 9 ULT admissions.
- From 11-23: BEG-ORB and the Friday-review moves. No Primary change.

## Caveats
- All live records are short: 30 active sessions at most.
- The ±30 null runs through 11-19, so it misses RW7's +40R on 11-20.
- The Primary-book replay uses each setup's own journal fills. It cannot model the slots, buying power or setup-order effects of sharing Primary with the five.
- The non-overlap records skip the twin-symbol (leveraged ETF) adjustment. Its effect is negligible for these single-stock shorts.

## Robustness

# promo-pipe survivors: robustness checks and deployment spec (P1, P4)

Educational only, not financial advice. All figures are LR8 cost-R.

## Bottom line
- **No new testing deployment for either one.** Both already run live, unchanged, in Testing 1 / On Deck (`config/account_testing.yaml`). Both also have Workbench WB4 copies in Testing F, added 11-17. P4 has a near-twin in Explore 1 (`NM1-cwt09-g10-vwaploss-short`: 9 trades, +4.1R, 6 of its symbol-days shared with P4). Adding another testing home would make a copy, which "Promotion = move / no copies" rules out. So there is no module to port, no new tests and no ledger entry.
- **Admission (CLAUDE.md testing rule):**
  - P4 meets it: on T1 it is one of the top 10.
  - P1 meets it as "debatable + derived from a promising parent". Its parent L3-fromopen is Primary's #1, and P1's own live record is positive.
  - Both are therefore correctly in Testing. **Neither is promotable.**
- **Action:** keep both On Deck unchanged and keep watching the promotion gates. Treat P1 and P2 as one L3 slot.
- **New finding, P1:**
  - Its best day, 11-12 (+18.2R over 32 trades on 32 symbols, 84% winners), was the first session after ODX-1 turned the split-tape short gate off in On Deck (ledger 2026-11-12-ondeck-split-tape-off). That same day L3-fromopen made +31.0R in Primary.
  - Since 11-12 P1 has only 6 other trades (+1.5R).
  - Under the earlier gate regime (before 11-12) it made 73 trades at +0.091 avg, and **-0.042 without its best day**.
  - Rule-change context: the gate change on 11-12 splits P1's record.

## Configurations tried
- 12 lab neighbour configurations: 7 for P1, 5 for P4, all pre-declared.
- Engine: bench10 normal way (`nb.py`, a copy of the promo-pipe benchpp). Testing-1 book: cap 150, 3 lots per symbol, cost filter 0.15, easy-to-borrow shorts. T1 only, no T2. The locked block was never read.
- The base rows reproduce `benchmark.json` exactly.
- No variant was selected or proposed, so the WB2 bar (max(1.5, sqrt(2 ln 12)) = 2.23) is only for reference.
- **Disclosure:** I also read the neighbours on CHECK. That was a stability check only, and no variant is being put forward.

## P1: L3-gap-slope-lowdist-FD (short)

**1. Robustness, live (111 trades, 20 traded sessions)**

| view | n | avg | w/o best day | w/o top-2 | best-day share | t (G/(G-1)) | green |
|---|---|---|---|---|---|---|---|
| all | 111 | +0.237 | +0.103 | -0.017 | 0.69 | 1.66 | 50% |
| cost +50% | 111 | +0.231 | +0.098 | -0.022 | 0.70 | 1.62 | |
| cost +100% | 111 | +0.225 | +0.092 | -0.028 | 0.71 | 1.58 | |
| 1st half / Oct (before 11-02) | 57 | +0.043 | -0.148 | -0.274 | 3.75 | 0.22 | 27% |
| 2nd half / Nov | 54 | +0.442 | +0.257 | +0.191 | 0.76 | 3.92 | 78% |
| entry before 11:00 | 14 | +0.697 | +0.368 | | | 2.47 | |
| entry 11:00-13:00 | 85 | +0.170 | -0.072 | | | 0.96 | |
| entry 13:00 or later | 12 | +0.181 | +0.031 | | | 0.97 | |
| without top symbol (PENG) | 109 | +0.215 | +0.081 | -0.044 | 0.73 | 1.43 | |

- The t on daily R sums is 1.22.
- Costs are not the risk: they average only 0.013R per trade because stops are wide.
- Long/short split does not apply (short only).
- Correlation of daily R:
  - With the Primary account: +0.34. On the account's 20 red days P1 made +8.0R, green on 7 of them, and turned 1 red day green.
  - With the current five pooled: +0.57. On their 11 red days P1 made -4.8R.

**1b. Parameter neighbourhood ±1 step, lab, testing book**

| config | FIT n / avg / w/o best day | CHECK n / avg / t |
|---|---|---|
| base | 1261 / -0.112 / -0.178 | 1774 / -0.104 / -2.36 |
| gap ≤ -2.0 | 1738 / -0.111 / -0.190 | 2700 / -0.118 / -2.73 |
| gap ≤ -3.5 | 837 / -0.089 / -0.188 | 1101 / -0.085 / -1.86 |
| slope > 0.25 | 1580 / -0.111 / -0.151 | 2204 / -0.089 / -2.14 |
| slope > 0.50 | 944 / -0.117 / -0.196 | 1353 / -0.092 / -1.93 |
| dist band -0.1 | 1363 / -0.096 / -0.170 | 2062 / -0.121 / -2.61 |
| dist band +0.1 | 1153 / -0.125 / -0.194 | 1475 / -0.043 / -0.93 |

- All 7 configurations are negative in both FIT and CHECK. The base is not a lucky outlier; the whole neighbourhood is negative in the lab.
- Halves of CHECK: -0.118 / -0.089.
- Positive months are rare: 6 of 26.

**Lab vs live parity, 10-13..11-04 (an important caveat on the lab verdict)**
- Lab: 132 trades, -0.177. Live: 59 trades, +0.039.
- Only 28 symbol-days are shared. On those, the two engines agree (lab +0.010, live -0.012).
- Lab-only trades average -0.227; 59 of them fall on 10-15, when live took 2.
- So the lab's negative partly comes from symbol-days live never trades. The cause (universe, features or timing) is not resolved. A parity audit is needed before the lab result is treated as decisive in either direction.

**Random-entry null** (from the survivor file, not recomputed): an edge of +0.163R for picking the stock-day, p 0.004. A random later entry does as well, so the entry minute adds nothing.

**2. Verdict:** admitted to testing (already there). Not promotable. It fails:
- best-day share < 50% (69%);
- strict non-overlap shrunk > 0 (-0.016);
- the lab, across the whole neighbourhood;
- regime stability: Oct -0.148 w/o best day, and only 6 trades since its gate-off best day.

**3. Deployment:** none. Keep it On Deck with no setup changes.
- Optional, owner decision, outside 09:30-16:00 ET only: once the On Deck stage is judged complete, add it to Primary `shadow_setups` (PSHADOW, rule 34a: no orders) to build the Primary-overlap record that C3-BAR2 needs.
- Ledger text if adopted: "PSHADOW: L3-gap-slope-lowdist-FD added to Primary shadow_setups (no orders, slots, latch or halt); separate record, SRCV1 weight 0; On Deck home unchanged. Evidence: research promo-pipe robustness 2026-11-21."
- Watch gates:
  - best-day share < 50%: needs about +10R without a new best day;
  - strict non-overlap shrunk > 0;
  - October-type weeks w/o best day > 0 now that the gate is off;
  - P1 and P2 as one slot.

## P4: CWT09-gapdn-vwaploss-g10-short (short)

**1. Robustness, live (24 trades, 13 sessions)**

| view | n | avg | w/o best day | w/o top-2 | best-day share | t | green |
|---|---|---|---|---|---|---|---|
| all | 24 | +0.228 | +0.151 | +0.087 | 0.48 | 1.58 | 77% |
| cost +50% / +100% | 24 | +0.224 / +0.220 | +0.147 / +0.143 | | | | |
| 1st half / Oct | 11 | +0.349 | +0.205 | -0.015 | | 1.43 | |
| 2nd half / Nov | 13 | +0.127 | +0.040 | -0.047 | | 0.78 | |
| since 11-12 (On Deck move) | 8 | +0.027 | | | | | |
| account testing2 / testing / livelab | 12 / 8 / 4 | +0.395 / +0.027 / +0.129 | | | | | |
| without top symbol (SOXL) | 21 | +0.196 | +0.121 | | | 1.28 | |

- Daily-sum t is 1.49.
- Correlation: -0.02 with the Primary account (+4.6R on its 20 red days, green on 8) and -0.04 with the five (+2.8R on their 11 red days).
- Long/short split does not apply (short only).

**1b. Neighbourhood, lab**

| config | FIT avg / w/o best day | CHECK avg / w/o best day / t |
|---|---|---|
| base | +0.053 / +0.009 | +0.054 / -0.056 / 0.45 |
| gap 8 | +0.050 / -0.007 | +0.076 / -0.012 / 0.77 |
| gap 12 | +0.060 / +0.015 | +0.077 / -0.014 / 0.71 |
| min ADV 5M | +0.054 / +0.010 | +0.054 / -0.056 / 0.45 |
| window end 14:00 | +0.053 / +0.009 | +0.055 / -0.058 / 0.45 |

- A flat, stable plateau, but about zero once the best day is removed, and every t is below 1.
- Halves of CHECK: +0.054 (w/o best day -0.177, share 4.1) and +0.055 (w/o best day +0.029).
- Jan-2026 is one big-day month (+1.44 avg, but -0.12 w/o best day).
- T2 -0.181 (t -2.68), unchanged.

**Parity, 10-13..11-04:** lab 41 trades / live 12 trades, 8 symbol-days shared. They agree in sign: lab +0.29, live +0.37.

**Random-entry null** (from the survivor file): no timing edge (p 0.82).

**2. Verdict:** admitted (meets the top-10 standard on T1; already in Testing). Not promotable. It needs ≥ 30 trades, ≥ 20 traded sessions and shrunk > 0 (about 66 trades): January at the earliest. The 2nd half and the time since 11-12 are fading. It is diversifying, but at 0.8 trades per session it cannot move Primary's daily R.

**3. Deployment:** none. Keep it On Deck unchanged. A pooled view of P4 + WB4 + NM1 (de-duplicated by symbol-day) could speed up the rep count. Report it only, with no config change.

## Rule-change context inside the window (10-13..11-20)
- **11-12:** ODX-1 split-tape short gate off in On Deck; LR8 cost basis (pre-11-12 rows re-costed); halt 300R; P4 moved into On Deck from Testing C.
- **11-17:** TSZ1 testing sizing (R comparable); WB4 copies added in Testing F.

## Files (scratch only; repo untouched)
- `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe-rob/nb.py`: neighbourhood bench, a bench10 copy with a variant inventory.
- `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe-rob/mods/p1var.py` and `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe-rob/mods/p4var.py`: research-only wrappers, not for porting.
- `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe-rob/score_nb.py`: FIT/CHECK/month scoring.
- `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe-rob/live_rob.py`: live halves, months, cost stress, correlation.
- `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe-rob/overlap.py`: lab/live parity.
- `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe-rob/w/`: lab signals and trades.