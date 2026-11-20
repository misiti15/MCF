Educational only — not financial advice

# Beginner experiment 2026-11-20: 10 textbook setups and 8 session rules, built from scratch and tested the normal way

**Owner summary (5 lines)**
1. We built 10 textbook intraday setups and 8 session rules from public sources as if we had never tested anything, then ran them through MCF's normal backtest with costs in. That came to 69 configurations, and the locked block was never read. None of the 10 makes money after costs on the scored CHECK window.
2. Two meet the top-10 live standard, and the Skeptic upheld both: **BEG-01 ORB-15 on stocks in play, with the stop at the far side of the opening range** (CHECK −0.026R, about 11 trades a session) and **BEG-03 gap-and-go** as written (CHECK +0.006R, but that rests on one day). BEG-04 and BEG-06 are NEAR. The other six FAIL, most of them badly.
3. What the fresh eyes taught us: the published edges are before costs, and textbook tight stops get eaten by costs. The entry triggers rarely beat random entries on the same days. Tweaks picked on FIT mostly faded on CHECK. The one tweak that held was a structural one: BEG-01's wider stop.
4. Session rules: only S8, a sanity filter on stop size and liquidity, helps; it is confirmed on CHECK but the effect is small. A daily −3R stop and trade/exposure caps remove better-than-average trades and hurt Primary's winners. That agrees with your R2 decision of 10-22.
5. Your call: **BEG-ORB** (admit BEG-01 to a testing arena; recommend Yes, after a duplicate check against MCF's own ORB) and **BEG-GNG** (admit BEG-03; Optional, because its record leans on one day). Reply "BEG-ORB yes/no" and "BEG-GNG yes/no".

Research only. No setup, exit, config, account or ledger change. Nothing goes live without your reply. Any deployment happens outside 09:30-16:00 ET and regenerates the assignments.

## 1. What was done
- **Design.** `DESIGN.md` was written as a beginner. It used only README and the strategy interface, never MCF research, the backlog or the setup modules. All 10 setups and 8 session rules come from public sources (Zarattini/Barbon/Aziz, Gao et al., Lou/Polk/Skouras, Soebhag/Baltussen/Da, Aziz and others).
- **Testing.** Each setup was tested by its own workbench session, using the "normal way" from research/ultimate_1119/top10/bench10.py:
  - LR8 costs, plus 1.2 bp borrow on shorts;
  - the testing-arena book: cap 100, at most 3 lots per symbol, easy to borrow (ETB) >= 0.9, 0.15R stop-cost filter;
  - day-clustered t.
- **Windows.**
  - FIT = 2024-10 + 2025-03..09 (170 sessions).
  - CHECK = 2025-10-01..2026-11-04 (276 sessions), scored once for the base and once for the version picked on FIT.
  - T2 = 2023-01..2024-09 (427 sessions, already seen, reference only).
  - The locked block 2024-11-01..2025-02-28 was never read.
- **Process per setup.** PLAN.md was pre-registered before any scoring. Three one-part tweaks were added after a FIT-only diagnosis and before any of them was scored, and the best on FIT was picked mechanically. Every setup was also compared with random entries.
- **Configurations: 69.** That is 10 setups × 4 (base + 3 tweaks) = 40, plus 29 session-rule configurations. Random controls fit nothing and are not counted.
- **Rule-change context.** Every figure is a backtest that applies one fixed rule set to every session, so no live rule change from research/ledger.jsonl falls inside these windows. The Primary live window used in the session-rule study (10-06..11-19) did contain changes:
  - setup moves on 10-12..10-22;
  - the −2R per-setup latch, 10-29;
  - LR3 and LR8 costs, 11-12;
  - TSZ1 and SPYEXIT, 11-17;
  - C3 Epoch 1, 11-19.

  The study re-costed every Primary trade on the LR8 basis.

## 2. All 10 setups: base vs tweak (testing-arena book, R after costs)

Top-10 standard (top10/PLAN.md Tier A). Every one of these medians is negative, so "MEETS" means "backtests no worse than the setups now winning live". It does not mean profitable.

| Leg | Median | Tier A threshold |
|---|---|---|
| T1 combined avg R | −0.0283 | >= −0.0383 |
| T1 CHECK avg R | −0.0364 | >= −0.0464 |
| Avg R w/o best day (combined / CHECK) | — | >= −0.0674 / −0.0781 |
| R per session (combined / CHECK) | — | >= −0.486 / −0.522 |
| T2 avg R | −0.0848 | >= −0.1048 |

How to read the table below:
- **Trades/session** is for T1 combined.
- **FIT → CHECK** shows avg R on FIT, then on CHECK.
- **RB** = REALLY BAD under the binding top10/PLAN.md rule (combined avg R <= −0.05 with t <= −2, or below −0.03 on all of FIT, CHECK and T2). A REALLY BAD setup is never admitted.

| Setup | Version | Trades/session | T1 combined avg R | W/o best day (combined) | FIT → CHECK | T2 | vs top-10 | Skeptic |
|---|---|---|---|---|---|---|---|---|
| BEG-01 ORB-15 stocks in play | base (0.10 ATR stop) | 4.2 | −0.291 | −0.296 | −0.384 → −0.252 | −0.204 | FAIL (far worse than random) | UPHELD |
| | **stopOR** (stop at far side of OR15) | 10.9 | **−0.009** | −0.011 | +0.020 → −0.026 | −0.029 | **MEETS** | **UPHELD** |
| BEG-02 VWAP first pullback | base | 3.7 | −0.107 | −0.114 | −0.146 → −0.089 | −0.097 | FAIL, RB | UPHELD |
| | win1000 | 3.7 | −0.084 | −0.093 | −0.131 → −0.064 | −0.121 | FAIL, RB | UPHELD |
| BEG-03 Gap-and-go (long) | **base** | 2.1 | **−0.017** | −0.024 | −0.058 → +0.006 | −0.084 | **MEETS** | **UPHELD** (CHECK leans on one day: share 1.77) |
| | win1015 | 1.5 | −0.043 | −0.051 | −0.008 → −0.062 | −0.137 | FAIL | UPHELD |
| BEG-04 Quiet gap fade | base | 14.2 | +0.003 | −0.029 | +0.106 → −0.040 | −0.050 | FAIL (two CHECK legs miss) | UPHELD |
| | gap25 | 7.9 | +0.056 | −0.001 | +0.256 → −0.030 | −0.062 | NEAR (CHECK w/o best day misses by 0.018) | UPHELD, only just |
| BEG-05 Market intraday momentum | base | 0.8 | −0.199 | −0.213 | −0.308 → −0.134 | −0.167 | FAIL, RB | UPHELD |
| | longonly | 0.45 | −0.101 | −0.124 | −0.055 → −0.127 | −0.218 | FAIL, RB | UPHELD |
| BEG-06 Noise-area breakout (SPY/QQQ) | base | 1.65 | −0.054 | −0.088 | −0.095 → −0.031 | +0.078 | FAIL (misses by 0.0206) | UPHELD |
| | notrail | 1.36 | −0.038 | −0.080 | −0.083 → −0.013 | +0.087 | NEAR (combined w/o best day misses by 0.012) | UPHELD |
| BEG-07 End-of-day reversal | base | 14.7 | −0.054 | −0.056 | −0.088 → −0.037 | −0.034 | FAIL, RB | not received* |
| | atr4 | 14.1 | −0.037 | −0.038 | −0.040 → −0.035 | −0.048 | NEAR by the 0.02R reading (FAIL under its own PLAN wording), RB on leg 2 | not received* |
| BEG-08 VWAP stretch snap-back | base | 9.0 | −0.066 | −0.104 | −0.076 → −0.059 | −0.094 | FAIL, RB | not received* |
| | stop125 | 9.6 | −0.038 | −0.072 | −0.009 → −0.057 | −0.134 | FAIL | not received* |
| BEG-09 Midday range → HOD/LOD break | base | 3.4 | −0.060 | −0.066 | −0.024 → −0.077 | −0.037 | FAIL, RB | not received* |
| | stopx15 | 3.7 | −0.047 | −0.052 | −0.005 → −0.069 | −0.017 | FAIL (misses NEAR by 0.002) | not received* |
| BEG-10 NR-day ORB-30 (OCO) | base | 86.4 | −0.068 | −0.072 | −0.053 → −0.076 | −0.052 | FAIL, RB | not received* |
| | win1015 | 51.3 | −0.068 | −0.074 | −0.034 → −0.087 | −0.056 | FAIL, RB | not received* |

\* The Skeptic text for BEG-07..10 did not reach the Report stage (the relay was cut off). The tiers shown for those four are the workbench's own and should be read as **not independently reviewed**. None of them is proposed for anything, so this changes no decision.

**One-big-day check.**
- BEG-01 stopOR: best-day share on FIT is 0.23. Without the best day: combined −0.011, CHECK −0.029.
- BEG-03 base: the CHECK record is **`1 day`**. 2026-04-23 is +5.8R against a +3.3R total. Without it, CHECK is −0.004, and without the top two days −0.014.
- BEG-04: FIT is entirely 2025-04-08, the tariff crash, so it is tagged `1 day` too.
- Everywhere else total R is negative, so the best-day share is undefined. The avg R without the best day is reported in the table instead.

**Random entries.**
- BEG-01 stopOR scores −0.026 on CHECK against −0.032 for random entries on the same symbol-days and sides, so it is barely better than random.
- BEG-03, BEG-04, BEG-09 and BEG-10 are level with or worse than fair random controls on CHECK.
- BEG-02's tweak beats random by about 0.06R, but its gross edge is about zero.
- Several of the pre-registered "same filled days" controls turned out to be biased upward, because they sample only days on which the stop order later fills. The workbenches noticed this, and added fair controls before scoring any tweak.

Files: each `BEG-*/RESULTS.md`, `PLAN.md`, the module with its live Strategy class, `smoke_test.py` (all pass) and `results.json`. Trade lists are in the session scratchpad and are not in the repo.

## 3. What a fresh pair of eyes got right and wrong, compared with MCF's existing families
**Right:**
- **Stocks in play plus a structural stop.** The one big out-of-sample improvement came from replacing a tight 0.10 × ATR stop with the classic far-side-of-the-range stop. BEG-01 CHECK went from −0.252 to −0.026. In the base, 78% of stops hit within 5 minutes, and 67% of stopped trades later reached the target. This is the same lesson MCF learned with its 0.15R cost filter and "room to breathe": tight R is mostly cost and noise.
- **It found MCF's known failure modes on its own:**
  - per-name reversal setups blow up on market-wide trend days (BEG-08 lost −238.6R on 2025-04-09, at the 100-lot cap);
  - breakouts lose on SPY-flat days (BEG-06, BEG-09 and BEG-10, about −0.17R a trade);
  - shorts in breakout setups are the weak side (BEG-09, BEG-10).
- **Day selection beats trigger.** BEG-04's edge sits in which days it picks (quiet, no-news gaps) rather than in its late trigger. This echoes MCF's best live families, which are condition-specific (L3 gap-slope, RW gap-down short, NM-ETF late dip) rather than textbook triggers.
- **Daily stops hurt.** The beginner's daily −3R stop and MCF's own −2R latch both remove better-than-average trades on this book, which matches your 10-22 R2 decision.

**Wrong:**
- **Published edges are before costs.** Gao et al.'s market intraday momentum (BEG-05) and the end-of-day reversal (BEG-07) are both REALLY BAD after LR8 costs. Costs ran about 0.05-0.10R a trade on every setup, and on most of them that decides the sign.
- **Textbook stops are too tight.** A 0.10-0.15 × ATR stop, or a stop set from the pullback bar, sits inside normal noise. 86% of BEG-02's trades sat on the stop floor.
- **Rules fire too often.** BEG-10 booked 86 trades a session and hit the cap. BEG-04 and BEG-07 booked about 14 a session. Volume is not edge.
- **Tweaks picked on FIT mostly faded.** The FIT gains were 0.01-0.15R. On CHECK, 7 of 9 improvements shrank to 0.002-0.025R, and two reversed (BEG-03 win1015, BEG-10 win1015). BEG-03's "late fills are bad" pattern flipped to the best part of the setup out of sample.
- **Overlap with MCF modules.** Five ideas share a name or source with existing MCF modules (orb, gap_and_go, gap_fade, intraday_momentum, noise_band_momentum). The 70% duplicate test against those modules was **not run**, so the conflict checks under the decisions below include it.

## 4. Session rules: S1-S8 as overlays (BEG-RULES/, RULES_RESULTS.md, 29 configurations)
Read this first: both baselines lose money, so any rule that removes trades shows a positive ΔR. A rule only shows skill if it beats random removal of the same number of trades per day.

| Rule | Verdict | Beats random removal (FIT / CHECK / T2) | Primary live, 10-06..11-19 |
|---|---|---|---|
| S8 sanity filter (stop 0.25-3% of price; last 5 bars >= $150k traded) | **HELPS, CONFIRMED.** R/trade improves in every window (FIT −0.057 → −0.049). It improves 10 of 10 setups on CHECK. | 98% / 87% / 75% | About neutral: +0.86R/session, t 0.89; 17 setups better / 8 worse |
| S5 streak control | Passes FIT, fails CHECK | 100% / 2% / 38% | +0.48R/session |
| S1 daily −3R stop | Worse than random | 0% / 0% / 0% | **−32.7R** (RW3 −35.4R, RW5 −31.0R) |
| S2 / S4 trade and exposure caps | Thinning only. Worst day falls from −235R to −7R. Starves positive setups (BEG-04 FIT −265R). | 0-32% | L3-fromopen, RW3 and RW5 lose |
| S7 trade with the SPY tape | Thinning only | 51% / 32% / 80% | 0% vs random; RW5 −28.5R |
| S6 event blackout, S3 time window | Neutral, and a no-op respectively | — | About 0 |
| MCF's −2R latch + −20R halt, on the BEG book | Removes better-than-average trades | 0% | Already live |
| T-S2ps (caps counted per setup), tweak | Fails on BEG. On Primary it beats 99.5% of random removals, but L3-fromopen drops from +30R to −5R. | — | Not adopted |

**What follows from it.**
- S8 goes to the backlog for a proper test on the 2-year lab book of the arena setups. There is no Primary change: it is neutral there, and MCF's 0.15R cost filter already covers its stop leg.
- S1, S7 and S5 are dropped.
- S2 and S4 are useful only as a disaster cap, set per setup with headroom. Not proposed.
- Nothing goes live.

Gaps:
- The macro calendar was rebuilt from search-result copies of the BLS schedules, because bls.gov is blocked in this session.
- On Primary, S8's volume leg covers 74% of trades and S7 covers 79%.

## 5. Proposals
Admission path: CLAUDE.md "Testing admission (owner 2026-11-19)". These setups have no MCF parent, so only the "meets the top-10 standard" path applies. Both candidates are MEETS, upheld by the Skeptic, and not REALLY BAD.

Conflict check (owner 2026-11-19), named for both:
- **(a)** They overlap in name and theme with MCF's `orb` and `gap_and_go` modules. Run the 70% symbol-day duplicate test before deployment. If the overlap is 70% or more, do not admit.
- **(b)** Slots and crowding. BEG-01 adds about 11 trades a session. Admit only where the arena has room, with no crowding of existing setups.
- **(c)** Deploy only outside market hours (setup-freeze). The same commit regenerates assignments.json and adds a ledger line.
- **(d)** Each one is judged as a brand-new setup under FOOTRACE-EXIT. It is **not** covered by the 11-20 admissions exemption.
- **(e)** The promotion hold still applies. Admission does not open a route to Primary.

- **DECISION BEG-ORB:** admit BEG-01 stopOR to a testing arena, labelled "meets top-10 standard (beginner_1120)". **Recommendation: Yes**, subject to (a)-(e).
  - CHECK: 3,101 trades, −0.026R, −0.029 without the best day, t −1.89.
  - T1 combined −0.009, best-day share 0.23 on FIT. T2 −0.029.
  - The caveat: random entries score −0.032, and the gross edge on CHECK is about zero.
  - Reply "BEG-ORB yes" / "BEG-ORB no".
- **DECISION BEG-GNG:** admit BEG-03 gap-and-go (base) to a testing arena, labelled "meets top-10 standard (beginner_1120)". **Recommendation: Optional.**
  - It passes every Tier A leg: CHECK +0.006, combined −0.017, T2 −0.084 (threshold −0.1048).
  - The CHECK record is a `1 day` record (share 1.77; −0.004 without that day). It is level with fair random entries.
  - It trades only about 2 a session, so it would crowd nothing. The SPY-down-day leg loses in every test (−0.19).
  - Reply "BEG-GNG yes" / "BEG-GNG no".
- **Backlog (research/backlog.jsonl, status idea or parked; no owner action needed):**
  - `beg-1120-s8-sanity-filter`: S8 on the arena lab book;
  - `beg-1120-gapgo-spydown-block`: BEG-03 with no new longs while SPY is below its open;
  - `beg-1120-quietgap-early-entry`: BEG-04's quiet-gap days with an earlier entry, or a gate for volatile tapes;
  - `beg-1120-orb15-trigger-edge`: a BEG-01 trigger refinement judged against the random baseline;
  - `beg-1120-mim-volday-gate`: BEG-05 with |r1| > 1% and a wider stop;
  - `beg-1120-batch-finding`: a parked record of the 69 configurations.
- **FYI:** BEG-04 gap25, BEG-06 notrail and BEG-07 atr4 are NEAR, but none is proposed:
  - they have no promising MCF parent, so the debatable path does not apply;
  - BEG-07 is REALLY BAD on leg 2;
  - BEG-04's FIT gain reversed on CHECK.

Educational only — not financial advice.
