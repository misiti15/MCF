Educational only — not financial advice

# Variants vs the TOP-10 benchmark: normal filter way, pre-registered rule (ultimate_1119, 2026-11-19)

Research only. Nothing is committed, and no setup, YAML, account, assignments or ledger entry was changed. The locked
block 2024-11-01..2025-02-28 was never read: bench10's guards ran on every load, and the earnings builders drop it.
**0 fitted configurations.** Every variant ran with its frozen rule; the two dispersion-gated books use round 6's frozen
cut-offs. The job's cumulative N stays at about 1,882. This stage made 35 frozen scorings.

## In plain words
- Every variant that has a frozen rule went through the same engine as the top-10 benchmark (bench10.py): the same
  frames, 1-minute exits, LR8 costs plus borrow, and live book (lot caps, at most 3 lots per symbol, price at least
  $5, easy-to-borrow shorts, the 0.15R cost filter). Each was booked under testing-account rules and judged against
  the PLAN.md rule.
- **The bar is low.** The top 10 lose money in this engine, so every threshold is negative. **20 of 35 scored rows
  "meet" it.** Several meet it only by losing less than the live leaders do here. **13 of the 20 are positive on both
  T1 combined and T1 check**, and only 4 of those are also positive on T2 (the two dispersion-gated books, H-V2 at
  +0.005 and leg M at +0.026).
- **The only rows that are clearly positive are the late-afternoon ETF dip family** (leg E, BOOK-EM, their dispersion
  gates, ULT-32) **and H-V2**. **All the ETF-dip rows mostly repeat a live setup.** Leg E trades the same
  symbol-sessions as NM-ETF-late-dip-di-long-WB4 (Testing E, live since 11-17) 100% of the time. BOOK-EM's overlap is
  73%, and its two gated versions' overlap is 76% and 100%.
- The owner's new setup (leg E gated to high-dispersion days) is scored too, but the rule does not judge it. It meets
  Tier A: +0.192R on T1 combined, +0.125R on check, +0.214R on T2 (34 trades). **Note: it trades only on WB4's
  symbol-sessions.** In practice it is WB4 restricted to the days after high dispersion, so on those days it runs WB4's
  trades a second time.
- After the no-duplicates rule, **the admissible list is 13 Tier A rows plus the owner's setup, and 4 Tier B rows**
  (§5). Several Tier A rows are near zero or negative after costs (§6).

## 1. Engine: identical to the benchmark, with the gaps stated
- **bench_var.py** reuses bench10.py's frames, `book()`, `add_r()` (LR8 basis, 1.2 bp borrow), `stats()`, sessions and
  ETB list. Each variant is booked with `TESTING_RULES` (cap 100, cost filter 0.15R, no latch, at most 3 lots per
  symbol). A variant's long and short sides, or its legs, are separate live YAML entries, so each is booked on its own
  and then pooled.
- **What a variant's YAML would carry instead of a home-account block:**
  - the module's own WINDOW, MIN_ADV (ADV20 at that point in time) and SYMBOLS (`symbols: module`);
  - its time stop: 45 min, or 30 / 20 where the frozen pick says TX30 / X20. This exits at the open of the first
    1-minute bar at or after entry + hold. bench10 models no time stop for the top 10.
  - geom "hold" (ULT-02 / ULT-06): a 2u catastrophic stop;
  - refire: modules thin themselves; ULT-02 / ULT-06 use the YAML cooldown of 14 / 11 bars from their RESULTS.md.
- **Parity:** leg E reproduces its earlier figures closely, for example T1 fit +0.218 vs round 6's +0.213, check +0.107
  vs +0.110, and T2 −0.042 vs round 5's −0.040. BOOK-EM, H-V1 and the BOOK-EM dispersion gate also reproduce, H-V2
  less exactly. All pairs are in the table below.

  | row | test | this engine | earlier figure | trades here / there |
  |---|---|---|---|---|
  | leg E | T1 fit | +0.218 | +0.213 (round 6) | — |
  | leg E | check | +0.107 | +0.110 | — |
  | leg E | T2 | −0.042 | −0.040 (round 5) | 251 / 249 |
  | BOOK-EM | T1 fit | +0.187 | +0.188 | — |
  | BOOK-EM | T2 | −0.035 | −0.040 | — |
  | BOOK-EM + disp | T2 | +0.173 | +0.186 | 36 / 36 |
  | H-V1 | T2 | −0.130 | −0.141 | 87 / 88 |
  | H-V2 | T2 | +0.005 | +0.042 | 197 / 192 |

- **R-unit caveat (it favours variants, so read Tier A conservatively):** R = |entry − stop|, which is the live
  definition. The time-exit variants (geom S / hold: ULT-01, 02, 03, 05, 06, 08, 10, 11, 13, 16, 19, 20, 21, 25, 28,
  30, 33, 34, 35) carry a far catastrophic stop: 2u, or 4u for ULT-25. Their R is therefore 2-4 times larger than the
  rounds' u-unit, which pulls avg R toward zero. Against a negative bar that makes passing easier. Re-checked in u
  units:
  - ULT-02 would fail Tier A (check w/o best day −0.082, T2 −0.119);
  - ULT-06 would be REALLY BAD (combined −0.062, t −3.36);
  - no other verdict changes.
- **No earnings blackout,** because bench10 applies none to the top 10 either. Survivorship (today's symbol list) and
  today's ETB flag favour every row.
- **T1** = lab frames, fit 170 / check 276 / combined 446 sessions. **T2** = 2023-01-03..2024-09-13, 427 sessions, from
  cache_fresh (468 of 469 symbols built; per-variant symbol coverage in the table). **T3:** no variant runs in any
  account, so none is in the 2026-11-18 recorded-quote replay. T3 is not available for any row; it is never a pass
  condition.
- **Seen data:**
  - T1 check shaped the rounds 1-4 designs. ULT-32 (and so leg E / leg M / BOOK-EM) is check-informed, and H-V1 / H-V2
    were hunted with check in view.
  - T2 was scored once in round 5 (BOOK-EM, leg E, leg M, H-V1, H-V2) and then used to train round 6's gates.
  - The dispersion gate's cut-offs are leave-one-window-out: T2 used 3.1274%, fit 2.579% and check 2.6438%, so no
    window's cut-off saw that window. But the gate itself was picked after all three windows had been seen.
  - Nothing here is out of sample in the strict sense.

## 2. The rule (PLAN.md, fixed before any variant was scored)
- **Tier A** requires all of: T1 combined avg R ≥ −0.0383 and check ≥ −0.0464; w/o best day ≥ −0.0674 / −0.0781;
  R/session ≥ −0.4862 / −0.5218; T2 avg R ≥ −0.1048; at least 20 trades on check and at least 20 on T2.
- **REALLY BAD** if either holds:
  - leg 1 (L1): combined ≤ −0.05 with day-clustered t ≤ −2.0;
  - leg 2 (L2): fit, check and T2 all < −0.03. When T2 has fewer than 20 trades, fit and check both < −0.03.
- **Tier B** requires debatable (not REALLY BAD) and derived from a promising parent.
- **No duplicates:** if 70% or more of a row's T1 symbol-sessions are traded by a live setup or an admitted variant,
  keep the better T1 combined avg R. Rows are processed in this order: the owner's setup first, then Tier A, then Tier
  B, each by T1 combined avg R from high to low. A Tier B row never displaces a Tier A row.

## 3. Every scored row (testing-account book, costs in)
Columns:
- fit / chk / comb / T2 = avg R per trade; n = trades.
- wo = avg R without the best day; R/s = total R per session.
- t = day-clustered t on combined; share = best-day share of total R on combined (— when the total is negative).
- T2 sym = symbols traded on T2.

**Bold** marks a value that fails its Tier A threshold.

| row | n fit / chk / T2 | fit | chk | chk wo | chk R/s | comb | comb wo | comb R/s | t | share | T2 | T2 sym | MEETS | REALLY BAD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| leg-E + disp (owner) | 205 / 181 / 34 | +0.251 | +0.125 | +0.108 | +0.082 | +0.192 | +0.145 | +0.166 | 4.07 | 0.39 | +0.214 | 14 | yes | no |
| BOOK-EM + disp | 217 / 278 / 36 | +0.228 | +0.106 | +0.087 | +0.106 | +0.159 | +0.119 | +0.177 | 3.55 | 0.37 | +0.173 | 16 | yes | no |
| H-V2 | 138 / 290 / 197 | +0.119 | +0.196 | +0.112 | +0.206 | +0.171 | +0.115 | +0.164 | 1.63 | 0.37 | +0.005 (T2 share 5.8, 1 day) | 22 | yes | no |
| leg-E | 289 / 235 / 251 | +0.218 | +0.107 | +0.093 | +0.091 | +0.168 | +0.132 | +0.198 | 4.20 | 0.33 | −0.042 | 20 | yes | no |
| BOOK-EM | 325 / 382 / 282 | +0.187 | +0.096 | +0.082 | +0.132 | +0.138 | +0.108 | +0.218 | 3.85 | 0.30 | −0.035 | 47 | yes | no |
| ULT-32 (E+M+D) | 568 / 568 / 391 | +0.123 | +0.060 | +0.045 | +0.123 | +0.091 | +0.063 | +0.232 | 2.54 | 0.36 | −0.092 | 86 | yes | no |
| H-V1 | 67 / 159 / 87 | +0.031 | +0.103 | +0.073 | +0.059 | +0.081 | +0.060 | +0.041 | 1.61 | 0.31 | **−0.130** | 9 | no | no |
| ULT-22 | 531 / 669 / 599 | +0.140 | +0.002 | −0.006 | +0.004 | +0.063 | +0.037 | +0.169 | 1.90 | 0.48 | −0.050 | 25 | yes | no |
| ULT-02 | 869 / 952 / 253 | +0.086 | +0.035 | −0.041 | +0.120 | +0.059 | −0.000 | +0.241 | 0.80 | 1.01 (1 day) | −0.059 | 147 | yes (fails in u units) | no |
| leg-M | 36 / 147 / 31 | −0.060 | +0.078 | +0.046 | +0.041 | +0.051 | +0.024 | +0.021 | 0.81 | 0.53 | +0.026 (T2 share 1.7) | 27 | yes | no |
| ULT-14 | 812 / 919 / 207 | +0.074 | +0.017 | −0.011 | +0.057 | +0.044 | +0.010 | +0.170 | 0.96 | 0.79 | −0.069 | 118 | yes | no |
| ULT-12 | 662 / 1,210 / 263 | +0.113 | +0.001 | −0.008 | +0.003 | +0.040 | +0.025 | +0.170 | 1.79 | 0.41 | −0.054 | 20 | yes | no |
| ULT-20 | 1,559 / 3,127 / 724 | +0.012 | +0.013 | +0.010 | +0.147 | +0.013 | +0.001 | +0.133 | 0.69 | 0.92 | −0.012 | 114 | yes | no |
| ULT-21 | 1,919 / 4,394 / 1,579 | +0.073 | −0.016 | −0.020 | −0.254 | +0.011 | −0.010 | +0.155 | 0.47 | 1.88 | +0.021 (T2 share 0.91) | 41 | yes | no |
| ULT-13 | 583 / 1,797 / 371 | −0.024 | +0.021 | +0.016 | +0.138 | +0.010 | +0.006 | +0.055 | 0.66 | 0.40 | −0.023 | 191 | yes | no |
| ULT-10 | 4,064 / 8,605 / 2,527 | +0.048 | −0.023 | −0.031 | **−0.709** | −0.000 | −0.008 | −0.000 | −0.00 | — | −0.042 | 282 | no | no |
| ULT-25 | 1,415 / 5,305 / 663 | +0.009 | −0.004 | −0.005 | −0.078 | −0.001 | −0.003 | −0.019 | −0.27 | — | +0.003 | 49 | yes | no |
| ULT-16 | 1,470 / 3,773 / 937 | −0.003 | −0.002 | −0.003 | −0.021 | −0.002 | −0.004 | −0.023 | −0.39 | — | −0.002 | 195 | yes | no |
| ULT-11 | 5,928 / 18,211 / 4,781 | +0.023 | −0.014 | −0.018 | **−0.934** | −0.005 | −0.014 | −0.269 | −0.42 | — | −0.043 | 266 | no | no |
| ULT-01 | 908 / 1,509 / 235 | +0.007 | −0.014 | −0.020 | −0.078 | −0.006 | −0.016 | −0.034 | −0.29 | — | −0.008 | 91 | yes | no |
| ULT-03 | 1,741 / 4,394 / 1,214 | −0.020 | −0.008 | −0.009 | −0.121 | −0.011 | −0.017 | −0.152 | −1.04 | — | −0.010 | 260 | yes | no |
| ULT-19 | 1,518 / 5,410 / 620 | −0.010 | −0.012 | −0.015 | −0.233 | −0.012 | −0.014 | −0.178 | −1.89 | — | −0.015 | 18 | yes | no |
| ULT-26 | 2,353 / 4,019 / 696 | −0.006 | −0.018 | −0.036 | −0.266 | −0.014 | −0.025 | −0.197 | −0.43 | — | −0.016 | 153 | yes | no |
| ULT-30 (T1 only) | 480 / 1,097 / — | +0.002 | −0.026 | −0.032 | −0.102 | −0.017 | −0.021 | −0.061 | −1.34 | — | not computed | — | no (T2 n/a) | no |
| ULT-33 (T1 only) | 858 / 1,709 / — | −0.011 | −0.023 | −0.026 | −0.141 | −0.019 | −0.022 | −0.108 | −1.99 | — | not computed | — | no (T2 n/a) | no |
| ULT-08 | 59 / 118 / 25 | +0.068 | **−0.066** | −0.075 | −0.028 | −0.021 | −0.035 | −0.009 | −0.77 | — | −0.025 | 25 | no | no |
| ULT-05 | 3,527 / 8,662 / 1,866 | −0.053 | −0.009 | −0.013 | −0.281 | −0.022 | −0.024 | **−0.591** | −1.87 | — | −0.024 | 252 | no | no |
| ULT-06 | 9,697 / 21,386 / 8,552 | −0.016 | −0.038 | −0.040 | **−2.904** | −0.031 | −0.034 | **−2.154** | −3.36 | — | −0.033 | 305 | no | no (yes in u units) |
| ULT-09 | 224 / 290 / 82 | +0.174 | **−0.198** | **−0.230** | −0.208 | −0.036 | **−0.131** | −0.042 | −0.31 | — | **−0.234** | 60 | no | no |
| ULT-28 (T1 only) | 339 / 667 / — | +0.015 | **−0.078** | **−0.095** | −0.187 | **−0.046** | −0.057 | −0.104 | −1.56 | — | not computed | — | no | no |
| ULT-07 | 524 / 1,505 / 335 | −0.230 | −0.030 | −0.040 | −0.163 | **−0.082** | **−0.090** | −0.371 | −1.68 | — | −0.063 | 138 | no | no, by 0.0001 (check −0.0299) |
| ULT-04 | 63 / 101 / 22 | −0.035 | **−0.125** | **−0.185** | −0.046 | **−0.090** | **−0.125** | −0.033 | −0.90 | — | **−0.109** | 22 | no | **yes (L2)** |
| ULT-34 (T1 only) | 991 / 817 / — | −0.068 | **−0.060** | −0.066 | −0.178 | **−0.065** | **−0.100** | −0.262 | −1.32 | — | not computed | — | no | **yes (L2)** |
| ULT-35 (T1 only) | 287 / 645 / — | −0.081 | **−0.064** | −0.074 | −0.149 | **−0.069** | **−0.076** | −0.144 | −2.34 | — | not computed | — | no | **yes (L1 + L2)** |
| ULT-23 | 15 / 76 / 10 | +0.336 | +0.144 | +0.109 | +0.040 | +0.176 | +0.148 | +0.036 | 2.44 | 0.19 | +0.073 (10 trades) | 10 | not scorable (n) | no |

Sides and legs worth knowing (T1 combined):
- **ULT-32:** E +0.168, M +0.051, D +0.014 (w/o best day −0.006).
- **ULT-14:** long +0.107, short −0.045.
- **ULT-20:** long +0.018, short −0.277 (81 trades).
- **ULT-25:** long +0.070, short −0.006.
- **ULT-26:** long +0.004, short −0.033.
- **ULT-05:** long −0.011, short −0.040.
- **ULT-10:** leg 02 +0.122; every other leg is between −0.09 and +0.02.

Full figures, including per-side / per-leg stats, SPY up/flat/down splits, worst days and hold times, are in
variants.json.

## 4. Not scored (no frozen rule, or the live runner cannot express it)
| id | why |
|---|---|
| ULT-15 | No fit pick: the base gate was closed, so there is no frozen rule. |
| ULT-24 | No fit pick (gates closed). |
| ULT-29 | No fit pick (gates closed). |
| ULT-17 | Needs sector columns (sec_fo / sec_atrp / sec_beta) that the live runner does not build. The module fires nothing live (its own LIVE GAP note). |
| ULT-18 | Needs a cross-section runner hook (`set_book`) that is not in the runner, so it fires nothing live. |
| ULT-27 | Its per-date profile file (ULT-27_profile.json) does not exist, so the module fires nothing. |
| ULT-31 | The earnings ranker's frame needs ULT-11's extra feature build plus a per-half state table. It was not wired into this engine in this pass. |
| Round-6 gates other than dispersion | No single frozen rule: the cut-off and direction flip between rotations. |
| ST7-FD gates | Gates on a live setup, not variants. |

- **Round-4 earnings rows (ULT-28 / 30 / 33 / 34 / 35):** these ran on T1 only. Each candidate's own frozen event
  builder (round4/ULT-*/bt.py) was used, and these builders start in 2024-08, so T2 cannot be computed. **They can
  never be Tier A** (T2 has fewer than 20 trades) and none has a promising parent, so none can be Tier B.
- **ULT-16 and ULT-33:** their frozen picks used limit (LMT) entries, which the live runner cannot express. The engine
  ran their market-order (MKT) twin, as live would.

## 5. Classification and admission (pre-registered rule; testing-account book)
Live overlap is the share of the row's T1 symbol-sessions that are also traded by:
- the live top 10 + ST7-FD (home books);
- NM-ETF-late-dip-di-long-WB4 (Testing E), NM-ETF-late-dip-di-long-WB1 (Explore 1) and NS3-failed-vwap-reclaim-short
  (Testing E), at signal level.

The other ~115 live setups were not replayed, so live overlap is a lower bound.

**Tier A: admissible, ranked** (owner's setup first, then T1 combined avg R from high to low):
| # | row | parent | max live overlap | verdict |
|---|---|---|---|---|
| 0 | **leg-E + disp** (owner decision; not judged by the rule) | NM-ETF-late-dip / WB4 | **WB4 100%**, NM-ETF 73% | Goes in by owner decision. It meets Tier A anyway, but it is WB4 on the days after high dispersion. |
| 1 | **H-V2** | ST7-FD (one-bar collapse on ETFs; loose) | 10% | **A.** Positive on fit, check and combined. T2 is +0.005 and rests on one day (share 5.8; round 5 found one correlated six-ETF day). |
| 2 | **ULT-22** | WB4 / NM-ETF (12:30-15:00) | WB4 50% | **A.** Check is flat (+0.002). |
| 3 | **ULT-02** | none | 10% | **A by the letter.** Its check record is one day (share 2.04, w/o best day −0.041), and it fails Tier A in u units. |
| 4 | **ULT-14** | WB4 / NM-ETF (loose) | 7% | **A.** The long side carries it (+0.107); the short side is negative. |
| 5 | **ULT-12** | WB4 (205 ETFs) | WB4 27% | **A.** Check is flat (+0.001, share 11.7). |
| 6 | **ULT-20** | none | 10% | **A.** Near zero (t 0.69). The short side is −0.28 on 81 trades. |
| 7 | **ULT-21** | none | 5% | **A by the letter.** Check is −0.016. |
| 8 | **ULT-13** | ST7-FD | ST7 27% | **A.** Near zero (t 0.66). |
| 9 | **ULT-25** | none | 5% | **A by the letter.** Zero edge (−0.001). |
| 10 | **ULT-16** | ST7-FD (MKT twin of an LMT pick) | 13% | **A by the letter.** Zero edge (−0.002). |
| 11 | **ULT-01** | RW3 / RW5 | L3-rsi5hi 41% | **A by the letter.** Negative (−0.006). |
| 12 | **ULT-19** | none | 9% | **A by the letter.** Negative (−0.012, t −1.89). |
| 13 | **ULT-26** | L3 family (loose) | 10% | **A by the letter.** Negative (−0.014). |

**Tier A rows that are duplicates (not admitted):**
- **leg-E:** 100% of its sessions are WB4's (live), and 72% are inside the owner's leg-E + disp, which is better
  (+0.192 vs +0.168).
- **BOOK-EM + disp:** 76% inside leg-E + disp, which is better.
- **BOOK-EM:** 73% WB4. WB4's own T1 combined, measured in this engine, is +0.140 on 706 trades, a hair above
  BOOK-EM's +0.138.
- **ULT-32:** passes as a book, but its live entries are three separate setups. Entry E is 100% WB4, and entry M is
  87% ST7-FD (a tie: +0.051 vs +0.050). Only leg D is new, and leg D alone is +0.014 with w/o best day −0.006.
- **leg-M:** 87% ST7-FD and no better (+0.0506 vs +0.0502, within noise). It would run ST7-FD's large-cap trades
  twice.
- **ULT-03:** 70.4% of ULT-16's sessions are inside ULT-03, and ULT-16 has the better T1 combined avg R (−0.002 vs
  −0.011).

**Tier B: debatable and derived** (admitted only if slots allow after Tier A), ranked:
| # | row | labelled | why it is not REALLY BAD, and the caveats |
|---|---|---|---|
| B1 | **H-V1** | "debatable / derived from NM-ETF-late-dip / WB4 (mirror, short)" | T1 combined +0.081, check +0.103. Fails Tier A on T2 (−0.130, 9 symbols). Concentrated in leveraged ETFs (round 5). |
| B2 | **ULT-05** | "debatable / derived from L3-gap-slope family (loose)" | Combined −0.022 (t −1.87). Fails on R/session (27 trades/session). Fit −0.053, check −0.009, T2 −0.024 (not all < −0.03). |
| B3 | **ULT-09** | "debatable / derived from CWT09-g10 (loose)" | Fit +0.174 but check −0.198 and T2 −0.234: a sign flip. Not REALLY BAD only because fit is positive. Weakest case. |
| B4 | **ULT-07** | "debatable / derived from NM-ETF-late-dip (loose)" | Check −0.0299 against a −0.03 line, so it escapes REALLY BAD by 0.0001R. Fit −0.230, T2 −0.063. Recommend last or skip. |

**Debatable rows that are not admitted:**
- **ULT-23** (mega-cap ST7, 91 trades): Tier B by the letter, with T1 combined +0.176. But 86% of its sessions are live
  ST7-FD's, and 81-90% are inside admitted ULT-16 (and inside ULT-03 / 13). Tier B never displaces Tier A, and
  admitting it would add no new exposure.
- **ULT-10:** contains admitted ULT-01 (79.5%) and ULT-02 (97.5%).

**No tier (debatable but no promising parent):** ULT-06 (REALLY BAD in u units), ULT-08, ULT-11, ULT-28, ULT-30,
ULT-33.

**REALLY BAD (never admitted):** ULT-04 (L2), ULT-34 (L2, T1 only), ULT-35 (L1 + L2, T1 only).

## 6. Honest read
- **"Meets" here is a low bar.**
  - Of the 13 Tier A admissions, 6 (ULT-21, 25, 16, 01, 19, 26) have a negative T1 check, combined or w/o-best-day
    figure, with t between −1.9 and +0.5. They clear the bar by losing less than L3-fromopen / RW3 / RW5 do in this
    engine.
  - The rule allows them in, and the owner's policy is that backtests have not predicted live failure for the current
    leaders (BENCHMARK.md §5).
  - Still, these are not evidence of an edge. If slots are tight, the ones with a positive record (H-V2, ULT-22, 14,
    12, 20, 13) come first.
- **What is clearly positive is one family:** the 14:00-15:00 ETF dip and its gates. **It is already live as WB4**
  (Testing E) and NM-ETF-late-dip (Primary).
  - The dispersion gate lifts it on all three tests:
    - on T2, from −0.042 to +0.214 (34 of 251 trades kept);
    - on fit, from +0.218 to +0.251;
    - on check, from +0.107 to +0.125.
  - It keeps few trades on T2 (0.08 per session), because 2023-24 dispersion ran lower. Round 6's 13% keep-rate
    warning still applies.
  - **Per-leg effect (remedy rule):** in BOOK-EM + disp, leg E improves on all three tests. Leg M is too thin on T2
    to judge (round 6: it got worse there on 2 trades).
- **H-V2 is the only new mechanism that is positive on T1 fit, check and combined.** Its T2 record is flat and carried
  by one day, so it is a debatable A.
- **High-volume broad rows fail on R/session, not on avg R:** ULT-06 at 70 trades per session, ULT-11 at 54, ULT-10
  and ULT-05 at 27-28. At these volumes a −0.01..−0.03R edge costs 0.3-2.9R per session.

## Rule-change context
- **The variants:** every figure is a backtest on 1-minute history with one fixed rule set (LR8 costs, live book,
  testing-account rules, module time stops). No live-account window is quoted for them, so no `research/ledger.jsonl`
  change applies.
- **The parents' live figures** come from BENCHMARK.md (10-06..11-18). They carry that window's rule changes:
  - L3-fromopen moves on 10-20, 10-22 and 10-30;
  - the Primary −2R latch from 10-29, the 0.15R cost filter from 10-30, and Primary sizing / cap 30 from 10-28;
  - LR3 / LR8 on 11-12;
  - RW6 in the Graveyard 10-21..11-13;
  - half-size testing lots from 11-17;
  - WB4 live from 11-17; CWT14-WB5 since 11-17.
- **Any admission** takes effect 2026-11-20 at the earliest, merged after the 16:00 ET close, with its ledger entry and
  regenerated assignments in the same commit. This stage made no such change.

## Files (research/ultimate_1119/top10/)
- `bench_var.py`: the engine for the variants (bench10 plus time stops / hold geometry / module window, ADV and
  symbols).
- `bench_var_earn.py`: the round-4 earnings rows, T1 only.
- `score_var.py`: books the trades, computes stats and applies the PLAN.md rule; writes `variants.json`.
- `overlap_var.py`: symbol-session overlaps; writes `overlap.json`.
- Trade rows are in the scratch work dir `varw/` (trades_t1.parquet, trades_t2.parquet; not in the repo).

Educational only — not financial advice.
