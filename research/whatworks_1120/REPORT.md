# What works in MCF: protected-list report

**Educational only — not financial advice.**

Window: live journals 10-06..11-19 (33 sessions). R is after costs on the LR8 basis. All figures are as re-checked by the skeptic pass; where the finder and the skeptic disagreed, the skeptic's number is used. Primary is the scoreboard. Results from testing, Graveyard and Gen are used only as evidence for or against a mechanism, never as a verdict on MCF.

**Rule changes inside the window (read every figure against these):** 10-09 full-day (FD) windows · 10-13 per-lot stacking · 10-14 refire / same-setup re-entry · 10-20 twin cap · 10-23 ST-A (no -2R stop in Testing/Gen) · 10-28 Primary ~$4k slots, per-setup cap 30 · 10-29 Primary -2R latch (ST-P) · 10-30 CF stop-cost filter in Testing · 11-11 TEAM-6 lineup · 11-12 LR1/LR3/LR5/LR7/LR8 (flatten, cost-R latch/halt, cost model) · 11-17 TSZ1 half-size testing lots, HK-FLAT · 11-18 live quote recording · 11-19 Epoch 1/BASE1, C3-BAR2, U9-TGT, U9-ETB · 11-20 stop-rounding fix (after the data ends).

---

## 1. Owner summary

1. **Primary:** only the three gap-down shorts make money: L3-gap-slope-fromopen-FD, RW3-FD and RW5-FD. Together: 530 trades, +73.4R. The other 24 setups lost -161R. The three's profit rests on two days (10-22 and 11-12); without those two days they are at -9.7R. Of the three, only L3-fromopen holds up across accounts and time periods. RW3/RW5 have been about flat since 11-03.
2. **The plumbing clearly works:** booking matches the broker exactly, broker-held stops fill as the model assumes, the 15:55 flatten has left Primary with 0 overnight positions, and the spread ≤ 25%-of-stop gate is the strongest filter (Primary trades it blocked: -0.41R vs -0.12R for trades taken).
3. **The research process that works:** strict, pre-declared, costs-in swarms (6 of 12 setups positive live), live testing before Primary, and a high promotion bar. Volume sources do not: the Generator, CWT, NS and MarcoFlow MF families went 0-3 positive out of 11-64 setups each.
4. **Brakes are insurance, not earners:** the -2R latch, the -20R halt, the caps and the twin block are about neutral on Primary R. Keep them, but do not judge them by R.
5. **Of 65 findings, 56 survived review, but only 7 are strong.** Most of this list is protected for consistency, not because it is proven. WW-PROTECT is therefore an evidence gate for changes, not a freeze.

---

## 2. Protected list

The table is ordered by strength, then by impact on Primary. "Guard" means the evidence needed before the item is changed. Every change also needs owner approval, the Friday epoch window for anything in Primary, and a per-setup report of how many setups improve and how many get worse.

| # | Area | What to protect | Evidence (verified) | Strength | Change guard |
|---|---|---|---|---|---|
| 1 | Protective rule | `max_spread_risk_frac 0.25` on the live SIP quote (G1, LW4, EX7) | Primary: 132 blocked at -0.409R vs -0.117R taken, same basis (t -4.16); -0.345R without the worst day; median day -0.93R. After the spread adjustment, 15 of 19 Primary setups' blocked trades lose, including RW3 and RW5. All accounts: 3,274 blocked at -0.280R. Across all accounts R falls steadily as spread/stop rises; 40 of 64... 50 of 66 setups are worse at a high share | strong | Blocked-signal replay over ≥ 20 Primary sessions, spread in, at or above the taken average without the best day, with most setups improving. Tightening it goes to the backlog |
| 2 | Execution | Order identity and booking: deterministic coid, lot-aware reconcile, newest-first paging (EX4) | 28,115 submitted and 28,115 booked; 0 duplicate ids; 0 short fills; 0 Primary rejects | strong | Reconcile and paging tests pass, plus one replayed session per account with submitted = booked, 0 duplicates and journal P/L = Alpaca |
| 3 | Execution / ops | Flatten at min(15:55, close - 5m), LR7 retries, HK-FLAT adoption, session guard (EX5, OPS-7) | Primary: 0 overnight positions in 1,397 trades. Since 10-08, 364 of 389 flattens at 15:55-15:56. Flatten exits average -0.010R (no R leak). All 24 overnight lots in the arenas came from 2 plumbing bugs, both fixed | strong | Fire drill on every account plus one clean live session. Half days (11-27) checked at 12:55 the first time |
| 4 | Research pipeline | Costs-in scoring at every stage; volume sources stay in the arenas (PIPE-7) | Generator 3 of 64 positive (5,271 trades, -0.175R); CWT 1 of 27 (12,308 trades); NS 0 of 11; ST 0 of 8; heat 0 of 4. Random baselines are negative once costs are in | strong | Measure later-live yield (n ≥ 15, avg > 0, w/o best day > 0) of at least ~10% before expanding a volume source. Never drop the cost haircut |
| 5 | Protective rules | Earnings blackout ±4d, no entry before 09:50, inverse guard, universe cap (G9) | These act upstream and leave no blocked rows, so they cannot be scored from the journals. 09:50 has only indirect support from the cost model | strong (that they are unmeasured) | A same-signal lab backtest with the guard on and off, costs in, held-out sessions and the configuration count |
| 6 | Primary setup | L3-fromopen's layers as they are: gap ≤ -2.657, sma20 slope > 0.3724, fromOpen > 3.46, t1s1, min_adv 0, no spread/ADV floor (P4, F1, PIPE-1) | Pooled n=403, +0.202R, w/o best day +0.148, +16.8R without its best 2 days, positive in both halves (+0.155 / +0.278). Slice gap > -5 with ATR ≥ 5: Primary +0.314 (w/o best day +0.198), Testing 1 +0.389, on non-overlapping dates. Primary alone: 181 trades, +31.7R, but w/o best day about 0 (`1 day`, 11-12) | moderate | No filter or gap widening unless the excluded slice is positive w/o best day in both Primary and Testing. The gap > -5 / ATR ≥ 5 gates go to the backlog as Workbench copies |
| 7 | Primary book | The three core seats, judged on full tenure under the epoch rule (P1, PD5, PIPE-8) | Trio +0.139R, +73.4R vs the rest -0.186R, -161R. Fragile: day-clustered t 0.97; -9.7R without the top 2 days; RW3 since 11-12 has a `1 day` tag | moderate (core) / weak (robustness) | Demote or tune only if full-tenure avg ≤ 0 and w/o best day ≤ 0 over ≥ 15 active days, or on the -10R-since-admission trigger. Paired against BASE1, and showing the effect on the three-setup book |
| 8 | Primary timing | Keep the FD window rather than narrowing back to backtest windows. The money is earned before 13:00 (P5, PIPE-3) | Core before 13:00: n=428, +0.207 (w/o best day +0.121); from 13:00: -0.148. Testing 1: +0.318 vs -0.246. FD trades outside the original window beat trades inside it (16 of 24 setups, Wilcoxon p 0.014); L3 inside its source window -0.547 | moderate | No narrowing to a backtest window. A 13:00 cut-off is a backlog remedy (see WW-REMEDY-Q) and is re-checked after LR1 |
| 9 | Families | The "extension" entry conditions: RSI(5) > 80 in RW3/RW5, fromOpen recovery in L3 (F1, PIPE-2) | RW3S (RW3 without RSI5 > 80): -0.148 on n=488, vs RW3 +0.016 on the same 13 sessions (a ~0.16R gap). RW3 on those days was itself only flat. Other "bounce" gap-down shorts are flat to losing | moderate / weak | Paired comparison on the same sessions, ≥ 40 trades and ≥ 10 sessions, with both avg R and w/o-best-day R not worse, reporting every family member |
| 10 | Families / stops | Do not narrow short stops. Keep CF and U9-TGT where they run (F5) | Short stop terciles: tight -0.187 / mid -0.074 / wide -0.045 net, and the same order gross. 40 of 64 setups better wide; day-paired t 2.60. Gap-down family: tight +0.055 vs wide +0.246 | moderate | Net and gross R by stop tercile, per setup, on later sessions only |
| 11 | Execution | Broker-held stop legs, plus the 11-20 rounding direction (EX2) | Primary 487 stops: median 0.031R beyond the stop, p99 0.27R, 0 beyond 0.5R, worst -1.44R; stable week to week | moderate | Recorded-quote evidence, per setup, with tail figures (p99, count beyond 0.5R). No soft or polled stops |
| 12 | Execution | Market order with bracket on the deciding poll, SIP feed (EX1) | Primary slippage 3.9 bps / +0.037R, stable by week; fills at the touch. Paper fills only; no alternative entry was ever tested | moderate | Forward test on recorded quotes, net of missed fills. Re-measure on the first real-funds sessions |
| 13 | Ops | Restore halt and latch state at restart; successor-job hand-over (EX6) | Halt held through 11-06; the one failure (Gen 11-05) gave 32 extra entries, then fixed. 77/77 decision minutes polled from 11-17 | moderate | Restart drill showing restored state = pre-restart state, plus ≥ 98% of decision minutes polled |
| 14 | Promotion | C3-BAR2 (15 active days, shrunk > 0, best-day share < 50%), the promotion hold, live testing before Primary (PIPE-5, F6, PIPE-4) | 4 of 12 promotions positive in Primary, and those are fragile. MF4-FD went from +0.290 before promotion to -45.3R in Primary. 3 of 3 Generator graduates collapsed. Split-half persistence is low | moderate | Back-test the proposed bar on the 12 promotions and 5 Generator graduates: hit rate > 1 in 3 and w/o best day > 0 in Primary |
| 15 | Research pipeline | Strict swarm design: pre-declared grids, train/valid split, cost haircut, random baseline, plateau and both-halves gates, finalist cap (PIPE-1) | Swarms 6 of 12 positive live (really about 2 mechanisms) vs ~5 of 140 from everything else | moderate | A new route must show yield ≥ the swarms' on later live trades before it replaces them |
| 16 | Research pipeline | Off-live sources get 0 ranking weight; holdouts scored once and reported, not a hard gate (PIPE-4) | src_value: Spearman ≈ 0 across 12 pre-declared configurations; the 2-year screen is optimistic by +0.16R; replay rated L3-fromopen -0.198 vs live +0.202 | moderate | src_value rule passes: Spearman CI low > 0 and sign-hit CI low > naive, on ≥ 8 setups |
| 17 | Families | Failed families (CWT14, MF open flowsell, Generator ORB-fail, heat-fade, NS2/NS3) return only through a mechanism change (F6) | CWT14 0 of 15, MF 0 of 11 (Primary -64.4R), Generator 2 of 53; base rate 7 of 142 | moderate | A mechanism change (not a parameter tweak) plus a split check on later sessions only |
| 18 | Promotion | Demotion is a move; a setup returns only on live evidence (LW1, PD1, PD2) | No demoted setup has earned its way back. Their later record (-0.148) is about the arena base rate (-0.132), so this shows the demotions cost nothing, not that they were skilful | moderate / weak | Return requires n ≥ 50, w/o best day > 0, best-day share < 50%, judged against the same-day arena base, not zero |
| 19 | Protective rule | `max_spread_bps 30` (G3, LW10, SPREAD-5) | All accounts: blocked -0.250 vs taken -0.156. Primary: neutral at half-spread; -0.37 when the full spread is charged; the bps gate does most of the blocking in Primary | moderate | Replay charging at least the recorded spread, ≥ 20 sessions, w/o best day above Primary's taken average |
| 20 | Protective rule | ETB-only shorts (G5) | All accounts: -0.133R (t -9.2). Primary neutral (+0.030). Borrow is a real-world constraint | moderate | Locate and borrow-fee modelling plus a ≥ 30-session Primary replay |
| 21 | Brakes | Primary -2R latch (cost R) and -20R halt (G6, LW7, LATCH-3, HALT-4) | Latch: 168 blocked at -0.018 (blocked trades +0.083 *better* than kept ones); saved ~20R on 11-10. Halt replay: at -20R it costs ~2R; a -10R halt would have cost ~22R | moderate | Judge on worst-day protection over ≥ 30 sessions. No halt tighter than 20R without saves on ≥ 2 separate days. No latch in Testing |
| 22 | Brakes | Testing CF 0.15R filter on, and off in Primary (LW8, G7) | With real costs: blocked -0.371, paired against kept -0.217 (t -5.39). Primary replay separates weakly and would cut RW3/L3 | moderate | Arena removal needs ≥ 500 blocked trades at ≥ 0. A Primary extension needs a per-setup test showing it does not cut RW3/L3 |
| 23 | Capacity | Per-setup cap 30, lot cap 3, quote crosscheck. No burst caps (G8, STACK-6, P8 guard) | The cap bound only once (11-12, L3, +98.8R forgone, one day). Lot cap neutral. Burst-cap remedies cut every winner | moderate | Replay on cluster days (10-22, 11-03, 11-05, 11-12, 11-16) next to the bad days (11-10/11). A cap raise needs ≥ 3 mass-signal days in both directions |
| 24 | Sizing | Equal-notional slots; R (after costs) as the only verdict unit (SIZE-1) | -87.5R = -$1,636 (-1.7% of equity); the risk cap binds on 2 of 1,397 trades; max drawdown -4.6% | moderate | State the effect on per-trade R, cost per R and worst-day $. No size-up while Primary R is negative |
| 25 | Concentration | Twin block, kept as a concentration cap and not as an edge (LW3, TWIN-2; G2 rejected) | Arenas: blocked trades -0.204 worse than the same setup's kept trades (t -2.95). Primary: 74 blocks ≈ the held twin's own R, carried by 11-09 and 11-06 | moderate (arenas) / weak (Primary) | Per-pair replay ≥ 10 sessions, best-day share < 50%. The guard notes that the effect follows the held twin's quality |
| 26 | Primary setup | RW3/RW5 gap-down layer, heat / buyPressure / RSI thresholds; no gap widening (P2, P3, F3) | RW3 gap ≤ -1%: +0.430 vs -0.141 (-1.5R without its top 2 days). Not a rule across families. Thresholds were never compared with alternatives | weak | No loosening without a 2-year cost-in backtest plus a live Testing copy. Gap ≤ -1% tightening → backlog |
| 27 | Exits | t1s1 default (1R = 0.25 × ATR, symmetric, no scale-out) (P7) | Descriptive only (L3 target +0.94 / stop -1.13). Holding to 15:55 helps only L3, in Primary only | weak | Beat t1s1 on the same signals, per setup, costs in, ≥ 15 Testing sessions |
| 28 | Book | No whole-side market-direction gate (P6) | RW is better on SPY-down entries, L3 on SPY-up in Primary only. The hedge claim does not hold (11-11 lost on both sides) | weak | Per-setup and whole-book w/o best day improve over ≥ 20 sessions in Testing |
| 29 | Primary setup | NM-ETF-late-dip unchanged; tweaks only as WB copies (F4) | n=33, w/o best day +0.185, day t 2.91, but the best of ~142 screened setups. Primary n=15, +0.075 | weak | ≥ 15 more active days of the unchanged version |
| 30 | Primary setup | L3 refire (cooldown 1) and stacking left as configured (LW6, PIPE-6) | Primary re-entries +0.080 (w/o best day -0.031); Testing 1 +0.287. Neutral in Primary, not harmful | weak | ≥ 150 re-entry trades, ≥ 15 days, w/o best day, before switching it off |
| 31 | Governance | Small book, Friday-only epoch, BASE1 shadow (PD6, LW2, EPOCH-8, PIPE-8) | Protects a process. TEAM-6 "gain" is -27R without 11-12; no counterfactual | weak (as evidence) | Paired Primary vs BASE1 difference (> ~2 SE) at a Friday review. Mid-epoch changes only for BROKEN bugs |
| 32 | Protective rules | $5 minimum price; split-tape gate and CF where they run (G4, G7) | The $5 result comes entirely from the 3x cost tier assumption (gross -0.010). Split-tape has no edge over the shorts taken | weak | Dedicated low-price study with real spreads. ≥ 20 sessions of blocked replay for the others |

---

## 3. Per-area detail

**Primary setups.** What survived: the gap-down trio is the only positive part of Primary, both before and after TEAM-6 (about +0.10 and +0.09 per trade). L3-fromopen is the one robust member: positive in both halves, in both accounts, and without its top 2 days in its best slice. RW3/RW5 were strong through October (+0.35 / +0.32 per trade) and about flat to negative since 11-03 (Primary since 11-03: RW3 +3.7R, RW5 -6.8R). They are a protected bet, not a proven edge. With day-clustered t of 0.77 and 0.53, the data cannot yet tell them from zero in either direction, which is why the guard asks for ≥ 15 more sessions rather than acting now. ST7-FD is the one current member whose evidence is failing: 42 trades, -0.158R, w/o best day -0.296, and it failed the one-day check before promotion.

**Promotion.** Both routes into Primary fail about 75-80% of the time. Testing surfaced the trio but did not raise the average quality of what entered Primary (promoted setups without the trio averaged -0.180, about the same as direct adds at -0.193). Expect about 0.2R of shrinkage from the testing record to Primary. Demotions cost nothing, because almost every setup loses; they did not show skill. What to keep is a high bar and demotion as a move.

**Protective rules.** The spread gates are the real filters. The spread/stop gate is strong in Primary; the 30 bps cap and ETB are system-wide helpful and neutral to slightly protective in Primary. For the twin block, latch, halt and caps, the blocked trades in Primary average about zero. Their value is tail and concentration protection (11-10 latch save; halt placement). "Without the worst day" is the right check for a blocking guard; finders often reported "without the best day", which flatters a guard.

**Approved changes (ledger).** Helped: spread/stop gate (strong), twin block in the arenas, CF in the arenas (once real costs are charged), keeping CF out of Primary. Neutral: the -2R latch in Primary, refire, stacking and the lot cap. Not shown: split-tape (rejected), TEAM-6 "earning" money (one day).

**Execution.** Booking, stop legs, flatten and restart hand-over are well evidenced and cheap to protect. The caveat is that entry and target-limit fills are paper fills at the touch, so slippage must be re-measured on real funds before these numbers are trusted.

**Families / features.** Solid: the extension condition, the gap-down context for these shorts, and not tightening short stops. Families that do not work are confirmed across thousands of trades. Not shown: a general short-over-long edge (rejected; it is market direction in one window); Monday, afternoon and other leads (F7, logged as backlog ideas only).

**Research pipeline.** Strict swarms beat volume sources by a margin far too wide for noise. Off-live sources (2-year screen, replay, holdout) have no setup-ranking skill. Full-day-first worked against the backtest windows, but the late tail (13:00 and after) loses and should not be frozen.

**Sizing / ops.** Tiny real risk per trade (median about 0.03% of equity) keeps survival and R comparability. Costs are about 40% of Primary's net R loss and are worst on tight stops. The ops layer is reliable. One correction: the start-time record needs a run-log check for 10-29 and 10-30. Those days show late first signals, against the finding's claim that only 11-13 started late.

---

## 4. Proposed protection mechanism and decisions

**WW-PROTECT (owner decision): an evidence gate, not a freeze.** This follows your Epoch answer: no freezes, but heavy consideration and giving rules a chance.
- Add `docs/PROTECTED.md` listing items PROT-01..PROT-32 from the table above. Each item has an owner area, the config keys or setup names it covers, its strength, and its change guard.
- Add `tests/test_protected.py`, run from `python -m mcf.research.ledger check`. Any `research/ledger.jsonl` entry whose `touches` field, setup names or config keys hit a protected item must carry three fields:
  1. `protected_ids`
  2. `guard_evidence`: a path to a report with n, sessions, avg R, w/o best day, w/o top 2 days, day-clustered t, per-setup improve/worsen counts, configurations tried, and rule-change context
  3. `owner_approval`: date and quote

  Primary items also need an effective date inside a Friday epoch window.
- Add a CI diff check. If a protected key in `config/default.yaml` or a protected setup YAML changes without a matching ledger entry in the same commit, the test fails.
- Strong items need the full guard. Weak items need only `guard_evidence` plus approval, so consistency is protected without blocking learning.
- This is housekeeping-sized (one doc and one test) and touches no setup or exit.

**WW-CLUSTER (owner decision): statistics standard for reviews.** Every promotion, demotion and review would report day-clustered t and "avg R without top 2 days" alongside the existing "w/o best day". For guards, it would report "without the worst day". Trade-level t overstated the trio (3.2-3.8 trade-level vs 0.97 day-level).

**WW-REMEDY-Q (owner decision): send three slice ideas to the backlog.** Each would run as a pre-registered Workbench copy in Testing, never edited into Primary:
- (a) a 13:00 entry cut-off for the trio
- (b) gap > -5% and ATR ≥ 5% gates on L3-fromopen
- (c) gap ≤ -1% on RW3/RW5

Each needs a per-setup improve/worsen report. The cut points were chosen from the data in hand, so they must be scored on later sessions only.

**WW-ST7 (owner decision): review ST7-FD at the next Friday epoch.** It is the only current Primary member with failing evidence and no compensating source record. Under "promotion = move" and the trimmed-setups rule, it would go to a testing account and would not be switched off.

---

## 5. Rejected or downgraded findings, and counts

**Rejected (9):**
- **P8**, cluster days drive R: confounded, because the latch ends losing days early, so losing days have fewer trades. The replay guard is kept.
- **PD3**, testing first is "far better": once the trio is removed, promoted setups equal direct adds (-0.180 vs -0.193).
- **PD4**, source t ≥ 2 predicts: it only tags the trio; it breaks on day-t; Fisher p ≈ 0.06 before correcting for the ~6 splitters tried.
- **PD7**, a fast demotion needs two signals: the rule would have endorsed the one wrong demotion (L3).
- **G2**, the twin block picks worse trades: blocked twins equal the held twin's own trade (corr 0.97). Kept as a concentration cap only.
- **LW5**, the 3-lot cap helped: paired against same-setup trades it is -0.022 (t -0.96), so neutral.
- **LW9**, split-tape "helped": blocked shorts were better than the shorts taken; 9 days.
- **EX8**, move toward the stop before the fill is a leak: mostly an artefact of the R denominator; about a coin flip per setup and per day.
- **F2**, shorts beat longs: a 0.04R gap that tracks market direction (correlation -0.58); in Primary, longs lost less.

**Claims downgraded inside upheld findings:**
- The "hedge" between L3 and RW (P6)
- "Patience paid off" on RW3/RW5 (PD5)
- TEAM-6 or the freeze "earned" R (PD6, LW2, EPOCH-8, PIPE-8: -27R without 11-12)
- "Target exits are the main source of R" (EX3: selection on outcome)
- The twin cap "every blocked entry a loser" (TWIN-2)
- "Hold to 15:55" for RW (P7)
- The spread-bucket gradient in Primary (SPREAD-5: not monotonic)
- Re-entries "clearly work" in Primary (PIPE-6)
- "Protect the full 09:50-15:00 window" (PIPE-3: the late tail loses)

**Counts:** 65 findings proposed across 8 areas. 56 upheld: 7 strong, 25 moderate, 24 weak. 9 rejected. Configurations tried, as reported by the finders: ~80 lens tests in the families pass (54 sign tests), ~6 splitters in promotion, 12 in src_value, 3 CF limits. The swarm rounds behind the core setups tried 74,056 configurations (rework) and 11,178 (layering). The finders did not report a single total for this investigation.

**Educational only — not financial advice.**
