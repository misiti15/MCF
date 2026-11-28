# Track 5: regime and filters (book risk budget, first hour, vol regime, SPY open, day carry-over)

Educational only — not financial advice.

**Data:** run-1 closed lots from 9 journals (the Graveyard is excluded), LR8 net R after costs (`cost_r_lr8`). Identical arena signals are counted once. No backtest data was used, and the locked holdout was not read.
- **DISC** = 10-23..11-27, 25 sessions. Primary has 943 lots; the arena (8 accounts, each scored as its own book) has 16,789.
- **HOLD** = every earlier session in the journals, 10-06..10-22. Primary has 12 sessions / 548 lots; the arena has testing, testing2 and gen, 9 sessions / 5,109 lots. HOLD was scored once, after DISC, with the same configs.
- **SPY:** 1-minute bars from Alpaca (GET only), 08-03..11-27.
- **Rules were fixed in advance** in `exploration/sandbox/regime_filters/PREREG.md` (00:16 ET), before any rule was scored. Q2b, Q3b and Q4 were added afterwards and are labelled as such.

**Configs tried on this track: 22.**
- Q1: 3. Q2: 8. Q2b: 4 rules on top of a latch. Q3: 3. Q3b: 2 post-hoc looks. Q4: 2.
- Cumulative: about 9,363 before tonight, plus the other tracks' counts, plus 22.

**Rule changes inside the windows (ledger).** Read every number below with these in mind.
- **10-23:** per-setup daily stop OFF in the arena (ST-A). The arena has **no per-setup latch** in either window.
- **10-28:** Primary size about $4k.
- **10-29:** Primary −2R per-setup latch on closed R. Primary HOLD and 10-23..10-28 are therefore pre-latch.
- **11-12:** LR8 costs. Primary −20R halt on cost R. Half-day flatten at 12:55.
- **11-17:** TSZ1, testing at half lots with 2x slots, so arena lots per day roughly doubled.
- **11-19:** Epoch 1. **11-20:** stop rounding. **11-21:** cost-basis fix.
- **11-23:** ST7 out of Primary and BRAKE-BURST.
- **Next, 11-30:** AV50 for NM-ETF and the Friday-review moves.

**Two definitions used throughout:**
- **L** is a point-in-time scale: the account's median lots per day over its previous (up to) 5 sessions.
- **A rule blocks new entries** for the rest of that day in that account. Lots already open run as they did. A flatten is not modelled, because the journal has no open marks.

---

## Top findings (numbers first)

### 1. A bad first hour does NOT predict a worse rest of day for MCF's own book (Q1, 3 configs)
- **What was measured:** closed R by T, scaled by L, against the average R of lots entered after T. Note that first entries are at 09:50, so "first hour" really means 09:50 to T.

| T | Book | Account-days | Spearman rho | Late R/lot after a bottom-quintile negative start | Late R/lot, rest | pct vs within-account shuffle |
|---|---|---|---|---|---|---|
| 10:30 | Primary DISC | 25 | +0.09 (p 0.66) | **−0.018** (5 days) | −0.186 | 75 |
| 10:30 | Arena DISC | 133 | +0.05 (p 0.55) | **−0.133** (27 days) | −0.206 | 64 |
| 11:00 | Primary DISC | 24 | −0.08 | −0.262 (5 days) | −0.121 | 36 |
| 11:00 | Arena DISC | 131 | +0.04 | −0.096 (27 days) | −0.200 | 72 |
| 11:00 | Arena HOLD | 17 | +0.58 (p 0.01) | −0.280 (4 days) | −0.045 | 1 |

- **DISC:** if anything, the lots after a bad start do *better* than other days' lots. HOLD hints the other way, but on 4 days only.
- **By side at 10:30:** no side shows that its own bad start predicts its later lots (rho −0.21 to +0.07 in DISC).
- **Verdict:** "stop after a bad first hour" (FH05 / FH10) has no basis. On Primary, FH05 *loses* 8.0R in DISC and 2.3R in HOLD.

### 2. A book-level daily risk budget does nothing for Primary. In the arena it beats both a random cut and a time-matched cut, but only partly beyond its size (Q2 / Q2b, 12 configs)
- **What was measured:** each budget rule blocks new entries once the book's closed R (BR), its stop count (BS) or one side's closed R (SIDE) crosses a threshold scaled by L.
- **Controls:**
  - **U:** the same number of random lots in the same account.
  - **TT:** the trigger time moved to a random non-trigger day.
  - **neutral:** the saving after re-pricing each account to zero mean R per lot. This is the part that is *not* just a size cut.

| Book / period | Rule | Lots cut | Saved | pct U / TT | neutral | day t | Blocked R/lot vs book | Worst-5 |
|---|---|---|---|---|---|---|---|---|
| **Primary DISC** | BR30 | 10% | **−20.5R** | 0 / 27 | −34.8 | −1.16 | **+0.223** vs −0.156 | unchanged |
| Primary DISC | BS30 | 13% | +5.0 | 10 / 79 | −13.4 | 0.22 | −0.04 vs −0.16 | −151.5 → −149.3 |
| Primary DISC | BS15 | 24% | +17.3 | 12 / 100 | −18.3 | 0.57 | −0.08 vs −0.16 | → −129.4; red days 17 → 20 |
| Primary DISC | SIDE20 | 16% | −9.7 | 0 / 15 | −33.4 | −0.43 | +0.06 vs −0.16 | unchanged |
| Primary HOLD (pre-latch) | BR10 / BS30 | 31% / 24% | +17.0 / +8.7 | 73 / 50 vs U | +5.8 / −0.1 | 1.22 / 0.83 | | |
| Arena DISC (no latch) | BS30 | 23% | +1,313 | 100 / 100 | +552 | 1.46 | −0.35 vs −0.18 | −1,986 → −918 |
| Arena DISC (no latch), ex-11-25 | BS30 | | +403 | | +71 | | −0.16 vs −0.13 | |
| **Arena DISC, on top of a simulated −2R per-setup latch** | **BS30** | 12% | **+301 (+60/wk across 8 accounts)** | **100 / 100** | **+82** | **3.15** | −0.199 vs −0.125 | −859 → −695 |
| same | BR30 | 9% | +225 | 99.7 / 100 | +67 | 2.90 | −0.198 vs −0.125 | → −732 |
| same | SIDE20 | 11% | +277 | 99.7 / 84 | +89 | 1.64 | −0.186 vs −0.125 | → −843 |
| same, ex-11-25 | BS30 / SIDE20 | | +290 / +355 | | +98 / +208 | | | |
| **Arena HOLD, on top of the latch** | BS30 | 7% | +28 | **50** / 100 | −0.4 | 1.42 | −0.111 vs −0.128 | |
| same | SIDE20 | 7% | +53 | 95 / 87 | +24 | 2.60 | −0.204 vs −0.128 | → −395 from −441 |

- **Primary:** the lots that come after a Primary drawdown are *better* than the average Primary lot. Primary is a 4-6 setup book and already has the −2R per-setup latch and the −20R halt. Its drawdowns are one setup's basket, which the latch already handles. A book budget then cuts the other, healthier setups. **Not one Primary rule beats a random size cut** (all at the 0-12th percentile vs U, except FH10, which fired on 1 day).
- **Arena (dozens of setups per account):** a book drawdown here is a broad adverse move. Blocked lots are 0.06-0.18R worse than the book average, and that holds even after the per-setup latch has taken its share. Best-day share is 24-28%, and 6-7 of 8 accounts do better.
- **But HOLD replicates only for SIDE20:** 95th percentile vs U, day t 2.60, 9 days. BS30 / BR30 fall to the size-cut line.
- **Most of every arena saving is a size cut.** The "neutral" part is about +2 to +3R a week per account.
- **Pre-registered bar** (DISC Primary AND arena at t ≥ 2, ≥ 90th percentile vs U and TT, HOLD with the same sign): **0 of 12 pass.**

### 3. Vol regime, SPY gap and the first 30 minutes do not split the book (Q3, Q3b, 5 configs)
- **Vol regime:**
  - SPY 20-day realised volatility went from about 10% to **31%** inside the window (11-02 onward is "high vol" on cut points fixed on 08-03..10-22).
  - Book R per lot did not change: longs −0.163 at mid vol vs −0.162 at high vol; shorts −0.189 vs −0.191.
  - The book loses the same in calm and in violent tape. So the vol regime is **not** the cause, and a vol switch would not have helped.
- **Regime by family:** the best-minus-worst regime cell keeps its sign from H1 (10-23..11-09) to H2 (11-10..11-27) in:
  - **1 of 9** family × side cells for the SPY gap (11%: it reverses);
  - **3 of 7** for the SPY open→10:00 move;
  - **0 comparable** for vol (H2 is all high vol).

  This repeats REGX / REGSTEER: regime ratings per family flip.
- **The book-level cell that looked strong in Q3** (shorts entered from 10:00 on "flat-open" days: **−0.374R/lot**, against −0.01 on days with a moving open, arena DISC) **is 11-25.**
  - Excluding 11-25 it is −0.133 vs −0.03 / +0.02.
  - Day-weighted it is −0.18 vs −0.10 (Welch t −0.60).
- **Longs entered after an up first 30 minutes** were negative in every DISC slice (arena −0.19 H1, −0.34 H2, −0.30 ex-11-25; Primary −0.57 in H2). But this rests on 7 days with an up open (day-weighted t not significant), and HOLD has 1 such day. It is a watch item only.

### Also checked (Q4, 2 configs, added after Q1-Q3)
- **Day-to-day carry-over at account level:** none. rho(yesterday R/lot, today R/lot) is +0.08 in the arena and −0.07 on Primary.
- **"Cool-off" (sit a setup out for its next session after a ≤ −2R session):**
  - It saves R: Primary DISC +96R, arena DISC +1,146R, with 7/4 and 88/45 setups helped/hurt.
  - But the excess over a lot-matched size cut is +36R on Primary DISC (t 0.48, **97% from one day**), +256R in the arena (t 0.83, 73% from one day) and −55R in arena HOLD.
  - It is a size cut carried by 11-25. Not a lead.

---

## Confidence

| Claim | Level | Reason |
|---|---|---|
| A bad first hour does not predict a worse rest of the day | **Medium-high** | 3 cut-offs, 2 books and 2 periods all fail to show it. DISC points the *other* way. HOLD is only 4-5 bad days. |
| A book budget does not help Primary | **High** for the current Primary design | All 8 rules are at the 0-12th percentile vs U, and blocked lots beat the book average. The mechanism is clear: the latch already handles single-setup baskets. |
| A book budget on top of a per-setup latch adds a little in multi-setup books | **Low-medium** | DISC t 2.9-3.2 with best day < 30%, but HOLD replicates only for SIDE20 (9 days, 3 accounts). The non-size part is about +2-3R per account a week. |
| Vol / gap / open regime does not separate setups usefully | **Medium-high** | The R/lot split across vol regimes is flat. Family cells flip (1/9 and 3/7), as in ~4,100 earlier regime configs. |

---

## Proposal candidates

### P1. BUDGET-SHADOW: score book-budget rules nightly as a shadow (reporting only; START Monday 11-30)
- **What:**
  - Each night, replay every non-Graveyard account's journal with **SIDE20** and **BS30**, applied on top of each account's actual per-setup handling. Primary already has its latch; for the arena, a simulated −2R latch is applied first.
  - Report saved R, the U and TT percentiles, the neutral (non-size) part, best-day share, accounts better/worse and setups better/worse (remedy rule).
  - Code: `exploration/sandbox/regime_filters/q2_budget.py` + `q2b_on_latch.py`. These are read-only replays.
- **Accounts:** all 9, no runtime change. Primary rules stay untouched.
- **Baseline:** actual live LR8 R on the same sessions.
- **Duration:** 20 sessions (to about 12-28). Report the 12-24 half day separately.
- **Success:** on the arena, the neutral part > 0 with day t ≥ 2, ≥ 90th percentile vs U **and** TT, best day < 50%, and at least 6 of 8 accounts better. For Primary, the expectation is a *fail* (it confirms the latch is enough). A Primary pass would need the same bars.
- **Expected effect on weekly R:**
  - **Primary: 0** (range −4 to +3R/wk).
  - **Arena: +30 to +60R/wk in total across 8 accounts** if it holds, but only about **+15R/wk** of that is better than a plain size cut (1 SE about ±10). Per account that is about +2R/wk beyond size.
- **Risk:**
  - None while it is a shadow.
  - **A live version would conflict with the owner's playing-time rule:** no in-session throttling in Primary/Testing, and the arena deliberately has no per-setup stop. Any adoption needs an explicit owner decision and should go to an exploratory account first.

### P2. Close the first-hour and regime-switch lines for Primary (decision support; START Monday, no experiment)
- **What:** record in the backlog that, on live data, these add nothing beyond a size cut and should not be re-proposed without new data:
  - "stop the book after a bad first hour" (FH05 / FH10);
  - a book-level daily budget in Primary (BR / BS / SIDE);
  - vol-regime switches;
  - "cool-off day" benching.
- **Re-check:** at 50 Primary sessions (about mid-January), with one re-run of `q1_firsthour.py` and `q2_budget.py`.
- **Expected effect:** 0R/wk directly. It saves research time and keeps the owner from adopting a rule that, on DISC, *loses* (BR30 −20.5R, SIDE20 −9.7R on Primary).
- **Risk:** low. The HOLD arena hint (at 11:00, rho +0.58 on 4 bad days) is the only contrary sign, so the re-check keeps it in view.

### P3. Fold the vol-regime and "up-open longs" checks into the existing GAP-U / IDX3-P regime-switch shadow scoring (reporting only; START Monday)
- **What:** when the running regime-switch shadow is scored (about 12-10), add two columns:
  - RV20 tercile (fixed cut points: 8.9 / 10.4% annualised, from 08-03..10-22, or re-fixed on a pre-window block);
  - SPY open→10:00 > +0.2% for longs entered after 10:00.

  Score them against a random skip of the same exposure.
- **Success:** ≥ 90th percentile vs random, day t ≥ 2, at least 10 qualifying days, best day < 50%.
- **Expected effect:** about 0 to +5R/wk on Primary longs (very uncertain, n = 7 up-open days). **Risk:** none, reporting only.

**Plain bottom line:** filtering *when* to trade does not rescue a book with no edge after costs. On Primary, the −2R per-setup latch already captures what a book budget would. Green weeks still need the exposure cut, the tail insurance (LATCH-OPEN) and a positive-edge sleeve named in PRIOR_RESEARCH, not a regime gate.

## Sources
- Journals: origin/mcf-data, mcf-data-testing, -testing2, -gen, -livelab, -explore1, -testingd, -testinge, -testingf. Read through git show and deleted after use.
- research/ledger.jsonl. SPY 1-minute bars from Alpaca (IEX, GET).
- Prior work: exploration/PRIOR_RESEARCH.md; exploration/findings/loss_anatomy.md (basket cap, gap-up shorts); research/hardstop_1123 (A12 account stop on the bench, which gained mainly through trading less); research/bdi/regx (ratings flip); research/bdi/latch_1103.
- Scripts and outputs: `exploration/sandbox/regime_filters/`. Files: `PREREG.md`, `extract.py`, `common.py`, `q1_firsthour.py`, `q2_budget.py`, `q2b_on_latch.py`, `q3_regime_family.py`, `q3b_o30_check.py`, `q4_daycarry.py`, with `*_out.txt`, `q2_budget.csv` and `q3_cells.csv`.

Educational only — not financial advice.

---

## Reviewer notes (review_regime_filters, 2026-11-28 ~00:50 ET)

Educational only — not financial advice. Reviewer configs: 3 diagnostic re-cuts (no new rules); script and output in `exploration/sandbox/regime_filters/review/`.

**What I re-ran:** I re-extracted the run-1 lots from the 9 journals (read-only `git show`, LR8 costs; SPY not re-fetched).
- `q2b_on_latch.py` reproduces **exactly**: arena DISC latch alone +1,352.8R; BS30+latch +300.9R, U 218.2, neutral +82.2, day t 3.15, best share 0.243, 7/1 accounts.
- Primary DISC reproduces exactly: BR30 −20.5R (92 lots blocked, +0.223 vs −0.156), SIDE20 −9.7R, FH05 −8.0R. All BR30 firings fall in the post-latch window (10-29 on, 21 sessions).

**Hygiene checks, all pass:**
- **Scope:** nothing outside `exploration/` differs between origin/explore/2026-11-27 and its merge-base with the default branch (be8e648c04). Commit a47a791c23 touches only `exploration/` and is contained only in origin/explore/2026-11-27.
- **Costs:** LR8 costs are in. No backtest data was used, and the locked holdout was not read.
- **Duplicates:** the arena dedup on key `k` removes 0 lots, so the per-account books are intact.
- **Timing:** there is no minute-level lookahead in the book rules. A trigger at exit minute τ blocks only entries after τ.

### Per finding

**F1. A bad first hour does not predict the rest of the day: HOLDS (confidence medium).**
- There is no lookahead: X uses exits ≤ T and Y uses entries > T, and L is point-in-time.
- The weak spot is sample size. The Primary contrast rests on 5 bad days per cut-off. The only out-of-sample contrary sign (arena HOLD 11:00, rho +0.58) is on 4 days.
- The finding is "no evidence for a first-hour stop", not "evidence against first-hour effects". FH05 losing on Primary (−8.0R DISC, −2.3R HOLD) confirms this.

**F2a. A book budget is useless for the current Primary: HOLDS (confidence medium-high, down from high).**
- The mechanism (the latch already takes single-setup baskets, and the lots blocked after a drawdown are better than average) reproduces.
- I lowered the confidence because it rests on 21 post-latch sessions and about 50-150 blocked lots per rule.

**F2b. A book budget on top of a latch adds a little in the arena: WEAKENED (confidence low).**

The +301R is real but almost entirely a size cut. The "beyond size" evidence does not reach significance:
1. **Post-hoc.** Q2b (4 configs) was designed after Q2 had been scored. Its headline rule is the best of 4 on DISC.
2. **The TT control is biased toward the rule.** TT moves the trigger time to a *non-trigger* day, and non-trigger days are good days by construction. Late lots (after the median τ ≈ 13:12) are **+0.026 R/lot on non-trigger days vs −0.103 on trigger days** (BS30+latch, DISC; HOLD +0.044 vs −0.099). So "100th percentile vs TT" says little. It should be dropped from the success bar.
3. **The U control is lot-level, not day-clustered.** Lots on the same day move together, so its percentiles overstate how significant the result is.
4. **The non-size part has day t 1.07, not 3.15.** The neutral +82.2R has a 61% best-day share and is positive on 8 of 20 days. The 3.15 and the 24% belong to the gross saving, which is mostly size. SIDE20+latch neutral: +89R, t 0.55, **95% from one day**.
5. **Within the same day the blocked lots are no worse.** Re-priced against each account's mean *for that day*, the neutral part is **−94.9R (t −1.43)** for BS30 and −74R for SIDE20. Post-TSZ1 (11-17..11-27) it is −69R.
   - So the rule works only by flagging bad days, after which the rest of the day stays about as bad as the morning. That is a day-level exposure cut, and it overlaps with the existing account halts.
6. **HOLD:**
   - BS30 is at the 50th percentile vs U.
   - SIDE20 is at 95th vs U but **87th vs TT**, so it fails the pre-registered bar even with the biased TT. It rests on 9 days, and only 2 accounts change.
   - SIDE20 HOLD same-day neutral is +34.8R (t 2.17), but DISC is −74R. The sign flips, so this is not a replication.
7. **Rule-change context missed:**
   - The arena already has a **book-level daily halt**: 120R, raised to 300R on 11-12 (ledger 2026-11-12-account-halt-300). Account-days at or beyond −120R occur in DISC: gen 10-29 and 11-04, and five accounts on 11-25 (testing −390.8, overshooting the 300R halt).
   - Not listed either: **BRAKE-BURST** (11-23, a per-setup entry cap), many composition moves (ROT3, GYH 11-27), and the **owner's 11-22 approval of a "per-setup −2R latch for every setup" study**. Of the arena gain, the simulated latch carries +1,353R. The book rule on top is the small part, and it is that latch study, not this one, that should own the question.
8. **Remedy rule:** setups helped/hurt are not reported for the Q2/Q2b rules, only accounts.

**F3. Vol / gap / first-30-minute regimes do not split the book: HOLDS (confidence medium).**
- Vol terciles were fixed on 08-03..10-22, before the window, and the gap and open→10:00 features are point-in-time. I found no leakage.
- I did not re-run this (SPY was not re-fetched).
- The persistence test is a single H1/H2 split on few cells (9 and 7). That is weak in both directions, but it agrees with about 4,100 earlier REGX configs.
- The "up-open longs" item rests on 7 days. Correctly labelled a watch item.

**Q4 cool-off is a size cut: HOLDS.** It is correctly called out as one-day carried (97% of the Primary excess comes from one day).

### Proposals
- **P1 BUDGET-SHADOW: keep as a shadow only, and fix its bar.**
  - Drop TT, or replace it with a trigger time moved to *any* random day of the account.
  - Require the **day-clustered neutral** (account-mean re-pricing) at t ≥ 2 **and** a non-negative same-day neutral.
  - Lower the expected beyond-size effect to **0 to +15R/wk across the arena (DISC point estimate ~+16R/wk, t 1.07)**.
  - Better: fold it into the owner-approved latch-per-setup study rather than run it as a separate line.
  - A live version still conflicts with the playing-time rule.
- **P2: holds.** Closing these lines for Primary is supported, and a re-check at 50 Primary sessions is reasonable.
- **P3: holds as reporting-only.** The expected value is near 0 and n is tiny.

### Final confidence
- Track conclusion ("timing filters do not rescue a no-edge book; Primary needs no book budget"): **medium-high**.
- Arena "beyond size" benefit: **low, not established** (day t 1.07, same-day neutral negative).
- Numbers: reproduced exactly where re-run.

Educational only — not financial advice.
