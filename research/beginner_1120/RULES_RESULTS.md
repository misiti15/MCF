Educational only — not financial advice

# BEG-RULES: the beginner's session rules S1-S8, tested as overlays (2026-11-20)

Pre-registration: `BEG-RULES/PLAN.md` (written before scoring; one addendum for tweak T-S2ps, written before that
run). Code: `BEG-RULES/prep.py` (trade table + S7/S8 inputs), `sim.py` (event simulation + random control),
`report.py` (tables), `calendar.json` (S6 macro days), raw numbers `BEG-RULES/results.json`.
**Configurations: 29** (9 overlays x 3 books + the MCF-rules comparator on the BEG book + T-S2ps on Primary).
Random-removal controls (200 seeds per rule/window) are controls, not configurations. Costs are in everywhere
(BEG: LR8 + borrow from the bench10 booking; Primary: LR8 cost-R via `mcf.costs.cost_r_lr8`). The locked block
2024-11-01..2025-02-28 was never read (asserted on every load).

## What was tested
- **BEG book**: the 10 BEG setups in their **base** (pre-registered) form, booked the normal way (bench10 testing
  book: cap 100/setup, <= 3 lots/symbol, ETB, 0.15R cost filter), all in ONE account. FIT 170 sessions, CHECK 276
  (2025-10-01..2026-11-04, scored once), T2 427 (2023-01..2024-09, seen, reference).
- **BEG alone**: the same, each setup as its own account (per-setup view without book interaction).
- **Primary live**: Primary journal (origin/mcf-data, run 1), 2026-10-06..11-19, 33 sessions, 1,397 trades,
  -133.4R LR8. MCF's own rules are already inside these trades.
- Each rule only removes (or for S5 halves) trades; no rule value was tuned. "Beats random" = share of 200 random
  removals (same number of trades removed per day) that the rule beats. Because both baselines lose money, **any
  rule that removes trades shows a positive ΔR**. A rule only shows real skill if it beats random removal and
  raises R per trade.

## Data gaps closed (DESIGN listed them as missing)
- S6 macro calendar: built from the public BLS CPI / Employment Situation schedules (with the 2025 and Jan-2026
  shutdown shifts) and FOMC statement days. ISM = 1st and 3rd trading day of the month. bls.gov is not reachable from
  this session, so 2026 dates come from search-result copies of the BLS calendar. Small date errors are possible.
- S7 SPY tape: SPY session VWAP from 1-minute bars, sign taken at bar em-1. The rule is computed outside DayContext
  (the live engine would still need `ctx.peers`).
- ETB: already applied in the bench10 booking (>= 90% of universe snapshots). BEG-07's 15:24 cross-sectional rank is
  already in its booked trades.
- Coverage: 100% on BEG. On Primary, S8 volume covers 74% and S7 covers 79% of trades. 1-minute bars run only to
  2026-11-10, so for 11-11..11-19 those two legs pass by default.
- S3: 11 BEG trades exit after 15:55 (BEG-04 6, BEG-09 4, BEG-05 1). They are counted as booked, since they cannot be
  re-walked here.

## Rule-change context
- BEG rows are backtests on fixed rules. No rule change applies inside any window.
- Primary 10-06..11-19 had many setup moves: promotions and demotions on 10-12, 10-14, 10-15, 10-16, 10-20, 10-21 and
  10-22 (research/ledger.jsonl).
- Primary's -2R per-setup latch was effective from 10-29. LR3 (latch and -20R halt count cost-R, and the halt counts
  open marks) and LR8 live costs were effective from 11-12. This study re-costs every row on the LR8 basis.
- The owner declined a new Primary daily stop on 2026-10-22 (ledger 2026-10-22-owner-replies-r1-r2, R2). S1 is that
  kind of rule. It is research only here.

## Verdicts (pre-registered rule; BEG book FIT, confirmed on CHECK)

| rule | BEG book verdict | FIT d R/session (t, beats random) | CHECK d R/session (t, beats random) | T2 d (beats random) | BEG alone FIT / CHECK d | Primary live d R/session (t, beats random) |
|---|---|---|---|---|---|---|
| S1 | THINNING ONLY (no better than random removal) | +5.29 (+1.89, 0%) | +4.08 (+2.68, 0%) | +1.07 (0%) | +2.19 / +1.20 | -0.99 (-0.48, 0%) |
| S2 | THINNING ONLY (no better than random removal) | +6.49 (+1.76, 12%) | +9.72 (+4.03, 2%) | +2.48 (0%) | +3.83 / +7.19 | +3.31 (+1.03, 72%) |
| S3 | NEUTRAL | +0.00 (+1.00, 58%) | +0.01 (+1.39, 60%) | +0.00 (36%) | +0.00 / +0.01 | +0.00 (+0.00, 0%) |
| S4 | THINNING ONLY (no better than random removal) | +5.77 (+1.56, 4%) | +9.12 (+3.82, 6%) | +2.24 (32%) | +3.56 / +7.15 | +2.87 (+0.92, 76%) |
| S5 | HELPS on FIT, not confirmed | +5.43 (+2.23, 100%) | +4.80 (+3.07, 2%) | +1.01 (38%) | +2.03 / +2.05 | +0.48 (+0.36, 20%) |
| S6 | NEUTRAL | +0.66 (+0.93, 69%) | +0.72 (+1.27, 80%) | +0.49 (60%) | +0.66 / +0.72 | -0.03 (-0.20, 8%) |
| S7 | THINNING ONLY (no better than random removal) | +2.40 (+2.03, 51%) | +3.26 (+3.68, 32%) | +0.97 (80%) | +2.40 / +3.26 | +0.72 (+0.29, 0%) |
| S8 | HELPS, CONFIRMED | +2.08 (+2.46, 98%) | +2.00 (+4.17, 87%) | +0.36 (75%) | +2.08 / +2.00 | +0.86 (+0.89, 49%) |
| ALL | THINNING ONLY (no better than random removal) | +6.58 (+1.79, 15%) | +10.08 (+4.19, 42%) | +2.67 (28%) | +5.53 / +8.62 | +3.20 (+1.01, 32%) |
| MCF | NEUTRAL | +2.11 (+0.85, 0%) | +2.23 (+1.57, 0%) | +0.70 (0%) | n/a | n/a (already live) |

Verdict rule (PLAN): HELPS needs, on FIT, ΔR/session > 0, paired t >= 1.5, beating >= 80% of random removals,
and setups improved >= setups worsened. It is CONFIRMED if CHECK Δ > 0 and it beats >= 60% of random. "Thinning
only" = a positive Δ that comes only from taking fewer trades in a losing book. Random removal of the same number of
trades does as well or better.

## Reading it (honest, costs in, looking for what works)

1. **S8 sanity filter is the one rule that holds up.** It skips trades whose stop is < 0.25% or > 3% of price, or
   whose last 5 bars average < $150k traded. It removes 15-18% of BEG trades, and those removed trades are worse than
   average. R per trade improves in every BEG window: FIT -0.0567 -> -0.0490, CHECK -0.0716 -> -0.0676, T2 -0.0564 ->
   -0.0548. It beats random removal 98% on FIT, 87% on CHECK and 75% on T2. Per setup it improves 8 and worsens 2 on
   FIT (worst: BEG-04 -41R) and improves 10 of 10 on CHECK (BEG alone). On Primary it is about neutral: +0.86R/session
   (t 0.89), 49% vs random, R/trade -0.0955 -> -0.0942, 17 setups better and 8 worse, worst day -34.8 -> -30.4.
   It is small. It does not turn any setup positive.
2. **S5 streak control** passes FIT (beats 100% of random) but fails CHECK (2%) and T2 (38%). In BEG-alone CHECK it
   worsens 5 setups and improves 3. Not confirmed.
3. **S1 daily -3R stop** is worse than random removal in every BEG window (0%), so the trades it removes are better
   than average. On Primary it **hurts**: -32.7R, -0.99R/session. It costs two of Primary's three positive setups (RW3 -35.4R,
   RW5 -31.0R) and MF2-FD -26.8R. This agrees with the owner's R2 decision.
4. **S2 trade caps and S4 exposure caps** cut about 95% of BEG trades and about 75-85% of Primary trades. They shrink
   the worst day a lot: BEG FIT -234.7R -> -7.2R, Primary -34.8R -> -6.5R. Their ΔR is no better than random removal
   on BEG (0-32%). On Primary they reach 72-76% vs random, which is not significant (t about 1.0). They admit trades
   in arrival order, so they starve late or refiring positive setups: BEG-04 FIT -265R; on Primary L3-fromopen
   -26.8R, RW3 -25.9R, RW5 -11.9R. This conflicts with the owner's playing-time rule.
5. **S7 trade with the tape** gives a large Δ on momentum setups (BEG-01 +181R on CHECK alone) but only matches
   random removal on the book (51% / 32% / 80%). On Primary it is 0% vs random and costs RW5 -28.5R and RW3 -16.8R.
   Shorts fade up-tapes on purpose there.
6. **S6 event blackout**: neutral (t < 1.5 everywhere, Primary -1.0R). **S3 time window**: a no-op, because the
   setups already respect their windows.
7. **ALL rules together** is dominated by S2/S4: 95% fewer trades, worst day about -7R, R/trade worse than baseline
   (BEG FIT -0.112 vs -0.057), no better than random.
8. **Compared with MCF's existing rules** (-2R per-setup latch + -20R halt, run on the BEG book): Δ +2.1R/session
   on FIT and +2.2R on CHECK, beating random removal 0% of the time. So MCF's latch, like S1, removes better-than-
   average trades on this book. The 0.15R cost filter is already in the BEG baseline. On S8's stop-distance leg,
   MCF's cost filter already removes very tight stops, which explains why S8 adds little on Primary.

## Tweaks
- **T-S2ps** counts the S2 caps per setup instead of per account. On BEG this is exactly the BEG-alone S2 row: FIT
  +3.83R/session, 0% vs random, so it fails. On Primary (one config, seen data) it gives +1.91R/session (t 0.75),
  beats 99.5% of random removals, improves 17 setups and worsens 3. It still cuts L3-fromopen from +30.0R to -5.0R
  (56 of 181 trades kept): that setup's edge is in its later or refire trades. **Not adopted.** It is a backlog
  candidate only if it exempts setups with a positive record.
- **Recommended for the beginner book:** keep S8 and drop S1 and S7 (and S5 until it confirms). Use S2/S4 only as
  a disaster cap (they cut worst-day risk), not as an edge, and set them per setup with headroom so positive
  setups are not starved.
- **For MCF Primary:** no rule here clears the bar on the live window. S8 is about neutral, and S1, S7 and S2/S4
  hurt the three positive setups. Nothing should go live. A Primary version of S8 (the $150k/5-bar liquidity leg)
  could go to research/backlog.jsonl for a proper test on the lab history.

## Full tables

**BEG_book / fit** (170 sessions; baseline 21651 trades, total -1228.4R, -7.23R/session, -0.0567R/trade, worst day -234.7R, green 32%, avg R/trade w/o best day -0.0671)

| rule | trades kept | total R | R/session | R/trade | R/trade w/o best day | worst day | green % | d R/session | paired t | days helped/hurt | beats random | setups better/worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 10216 | -329.5 | -1.94 | -0.0323 | -0.0477 | -101.1 | 28% | +5.29 | +1.89 | 113/49 | 0% | 9/1 |
| S2 | 1020 | -125.8 | -0.74 | -0.1234 | -0.1358 | -7.2 | 37% | +6.49 | +1.76 | 118/52 | 12% | 9/1 |
| S3 | 21649 | -1228.2 | -7.22 | -0.0567 | -0.0671 | -234.7 | 32% | +0.00 | +1.00 | 1/0 | 58% | 1/0 |
| S4 | 2327 | -247.7 | -1.46 | -0.1064 | -0.1129 | -15.4 | 41% | +5.77 | +1.56 | 114/56 | 4% | 9/1 |
| S5 | 11982 | -304.5 | -1.79 | -0.0254 | -0.0359 | -68.8 | 36% | +5.43 | +2.23 | 120/49 | 100% | 9/1 |
| S6 | 20284 | -1116.9 | -6.57 | -0.0551 | -0.0661 | -234.7 | 32% | +0.66 | +0.93 | 18/13 | 69% | 4/4 |
| S7 | 16511 | -820.0 | -4.82 | -0.0497 | -0.0619 | -233.6 | 36% | +2.40 | +2.03 | 106/63 | 51% | 5/1 |
| S8 | 17841 | -874.6 | -5.14 | -0.0490 | -0.0593 | -220.8 | 34% | +2.08 | +2.46 | 109/61 | 98% | 8/2 |
| ALL | 991 | -110.6 | -0.65 | -0.1116 | -0.1222 | -6.8 | 42% | +6.58 | +1.79 | 115/55 | 15% | 9/1 |
| MCF | 13546 | -869.0 | -5.11 | -0.0641 | -0.0761 | -101.1 | 30% | +2.11 | +0.85 | 105/59 | 0% | 8/2 |

**BEG_book / check** (276 sessions; baseline 40784 trades, total -2919.3R, -10.58R/session, -0.0716R/trade, worst day -143.7R, green 31%, avg R/trade w/o best day -0.0793)

| rule | trades kept | total R | R/session | R/trade | R/trade w/o best day | worst day | green % | d R/session | paired t | days helped/hurt | beats random | setups better/worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 17106 | -1794.0 | -6.50 | -0.1049 | -0.1219 | -112.6 | 20% | +4.08 | +2.68 | 173/98 | 0% | 8/2 |
| S2 | 1656 | -236.1 | -0.86 | -0.1426 | -0.1493 | -7.2 | 34% | +9.72 | +4.03 | 193/83 | 2% | 9/1 |
| S3 | 40778 | -2917.2 | -10.57 | -0.0715 | -0.0793 | -143.7 | 31% | +0.01 | +1.39 | 3/0 | 60% | 1/0 |
| S4 | 4062 | -402.8 | -1.46 | -0.0992 | -0.1031 | -15.2 | 37% | +9.12 | +3.82 | 192/84 | 6% | 8/2 |
| S5 | 19918 | -1595.2 | -5.78 | -0.0801 | -0.0938 | -106.4 | 30% | +4.80 | +3.07 | 182/94 | 2% | 9/1 |
| S6 | 37791 | -2721.0 | -9.86 | -0.0720 | -0.0804 | -143.7 | 32% | +0.72 | +1.27 | 38/22 | 80% | 8/0 |
| S7 | 30165 | -2019.0 | -7.32 | -0.0669 | -0.0776 | -123.9 | 32% | +3.26 | +3.68 | 184/92 | 32% | 6/0 |
| S8 | 35018 | -2365.9 | -8.57 | -0.0676 | -0.0757 | -122.3 | 32% | +2.00 | +4.17 | 185/91 | 87% | 10/0 |
| ALL | 1626 | -137.3 | -0.50 | -0.0845 | -0.0913 | -6.7 | 43% | +10.08 | +4.19 | 194/82 | 42% | 8/2 |
| MCF | 24547 | -2304.5 | -8.35 | -0.0939 | -0.1054 | -119.4 | 28% | +2.23 | +1.57 | 165/109 | 0% | 7/3 |

**BEG_book / t2** (427 sessions; baseline 22974 trades, total -1295.5R, -3.03R/session, -0.0564R/trade, worst day -62.8R, green 39%, avg R/trade w/o best day -0.0600)

| rule | trades kept | total R | R/session | R/trade | R/trade w/o best day | worst day | green % | d R/session | paired t | days helped/hurt | beats random | setups better/worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 13650 | -837.5 | -1.96 | -0.0614 | -0.0675 | -43.8 | 32% | +1.07 | +2.50 | 210/153 | 0% | 6/4 |
| S2 | 2562 | -235.9 | -0.55 | -0.0921 | -0.0973 | -6.8 | 42% | +2.48 | +3.25 | 249/178 | 0% | 8/2 |
| S3 | 22967 | -1294.9 | -3.03 | -0.0564 | -0.0600 | -62.8 | 39% | +0.00 | +1.41 | 2/0 | 36% | 1/0 |
| S4 | 5231 | -341.0 | -0.80 | -0.0652 | -0.0681 | -14.2 | 39% | +2.24 | +3.06 | 251/176 | 32% | 9/1 |
| S5 | 16705 | -862.3 | -2.02 | -0.0516 | -0.0564 | -47.4 | 39% | +1.01 | +2.57 | 231/176 | 38% | 8/2 |
| S6 | 21188 | -1088.0 | -2.55 | -0.0513 | -0.0553 | -62.8 | 39% | +0.49 | +1.84 | 49/36 | 60% | 6/2 |
| S7 | 17655 | -883.1 | -2.07 | -0.0500 | -0.0548 | -72.4 | 41% | +0.97 | +3.15 | 251/171 | 80% | 5/1 |
| S8 | 20810 | -1141.2 | -2.67 | -0.0548 | -0.0581 | -58.2 | 39% | +0.36 | +2.46 | 246/171 | 75% | 7/3 |
| ALL | 2484 | -153.4 | -0.36 | -0.0618 | -0.0655 | -6.7 | 43% | +2.67 | +3.51 | 252/175 | 28% | 9/1 |
| MCF | 18059 | -997.7 | -2.34 | -0.0552 | -0.0598 | -48.2 | 38% | +0.70 | +2.09 | 210/153 | 0% | 7/3 |

**BEG_alone / fit** (170 sessions; baseline 21651 trades, total -1228.4R, -7.23R/session, -0.0567R/trade, worst day -234.7R, green 32%, avg R/trade w/o best day -0.0671)

| rule | trades kept | total R | R/session | R/trade | R/trade w/o best day | worst day | green % | d R/session | paired t | days helped/hurt | beats random | setups better/worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 15785 | -856.2 | -5.04 | -0.0542 | -0.0644 | -94.5 | 30% | +2.19 | +1.09 | 96/61 | 0% | 7/0 |
| S2 | 5147 | -578.0 | -3.40 | -0.1123 | -0.1165 | -20.1 | 29% | +3.83 | +1.05 | 109/61 | 0% | 6/3 |
| S3 | 21649 | -1228.2 | -7.22 | -0.0567 | -0.0671 | -234.7 | 32% | +0.00 | +1.00 | 1/0 | 54% | 1/0 |
| S4 | 5234 | -622.8 | -3.66 | -0.1190 | -0.1235 | -24.3 | 31% | +3.56 | +0.98 | 113/57 | 0% | 7/2 |
| S5 | 15960 | -882.5 | -5.19 | -0.0553 | -0.0653 | -91.2 | 32% | +2.03 | +1.04 | 108/57 | 4% | 7/0 |
| S6 | 20284 | -1116.9 | -6.57 | -0.0551 | -0.0661 | -234.7 | 32% | +0.66 | +0.93 | 18/13 | 73% | 4/4 |
| S7 | 16511 | -820.0 | -4.82 | -0.0497 | -0.0619 | -233.6 | 36% | +2.40 | +2.03 | 106/63 | 50% | 5/1 |
| S8 | 17841 | -874.6 | -5.14 | -0.0490 | -0.0593 | -220.8 | 34% | +2.08 | +2.46 | 109/61 | 96% | 8/2 |
| ALL | 3389 | -288.8 | -1.70 | -0.0852 | -0.0908 | -15.0 | 37% | +5.53 | +1.52 | 114/56 | 13% | 9/1 |

**BEG_alone / check** (276 sessions; baseline 40784 trades, total -2919.3R, -10.58R/session, -0.0716R/trade, worst day -143.7R, green 31%, avg R/trade w/o best day -0.0793)

| rule | trades kept | total R | R/session | R/trade | R/trade w/o best day | worst day | green % | d R/session | paired t | days helped/hurt | beats random | setups better/worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 29470 | -2588.2 | -9.38 | -0.0878 | -0.0977 | -128.6 | 28% | +1.20 | +0.94 | 162/106 | 0% | 3/5 |
| S2 | 9909 | -935.6 | -3.39 | -0.0944 | -0.0970 | -25.3 | 33% | +7.19 | +3.14 | 185/91 | 5% | 7/2 |
| S3 | 40778 | -2917.2 | -10.57 | -0.0715 | -0.0793 | -143.7 | 31% | +0.01 | +1.39 | 3/0 | 63% | 1/0 |
| S4 | 10278 | -947.2 | -3.43 | -0.0922 | -0.0947 | -31.9 | 29% | +7.15 | +3.08 | 188/88 | 3% | 7/2 |
| S5 | 29878 | -2353.5 | -8.53 | -0.0788 | -0.0884 | -128.1 | 29% | +2.05 | +1.73 | 176/100 | 0% | 3/5 |
| S6 | 37791 | -2721.0 | -9.86 | -0.0720 | -0.0804 | -143.7 | 32% | +0.72 | +1.27 | 38/22 | 81% | 8/0 |
| S7 | 30165 | -2019.0 | -7.32 | -0.0669 | -0.0776 | -123.9 | 32% | +3.26 | +3.68 | 184/92 | 32% | 6/0 |
| S8 | 35018 | -2365.9 | -8.57 | -0.0676 | -0.0757 | -122.3 | 32% | +2.00 | +4.17 | 185/91 | 84% | 10/0 |
| ALL | 6440 | -539.8 | -1.96 | -0.0838 | -0.0871 | -17.6 | 37% | +8.62 | +3.71 | 191/85 | 30% | 9/1 |

**Primary / live** (33 sessions; baseline 1397 trades, total -133.4R, -4.04R/session, -0.0955R/trade, worst day -34.8R, green 27%, avg R/trade w/o best day -0.1531)

| rule | trades kept | total R | R/session | R/trade | R/trade w/o best day | worst day | green % | d R/session | paired t | days helped/hurt | beats random | setups better/worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 969 | -166.1 | -5.03 | -0.1714 | -0.2304 | -32.8 | 18% | -0.99 | -0.48 | 17/7 | 0% | 19/7 |
| S2 | 198 | -24.1 | -0.73 | -0.1217 | -0.1470 | -6.5 | 39% | +3.31 | +1.03 | 23/10 | 72% | 21/6 |
| S3 | 1397 | -133.4 | -4.04 | -0.0955 | -0.1531 | -34.8 | 27% | +0.00 | +0.00 | 0/0 | 0% | 0/0 |
| S4 | 378 | -38.6 | -1.17 | -0.1022 | -0.1218 | -6.7 | 42% | +2.87 | +0.92 | 22/11 | 76% | 21/6 |
| S5 | 1154 | -117.4 | -3.56 | -0.1018 | -0.1510 | -26.6 | 24% | +0.48 | +0.36 | 19/8 | 20% | 18/8 |
| S6 | 1379 | -134.4 | -4.07 | -0.0975 | -0.1561 | -38.4 | 27% | -0.03 | -0.20 | 3/3 | 8% | 4/6 |
| S7 | 805 | -109.7 | -3.32 | -0.1363 | -0.2049 | -40.1 | 30% | +0.72 | +0.29 | 16/9 | 0% | 19/7 |
| S8 | 1113 | -104.9 | -3.18 | -0.0942 | -0.1434 | -30.4 | 36% | +0.86 | +0.89 | 21/11 | 49% | 17/8 |
| ALL | 167 | -27.7 | -0.84 | -0.1658 | -0.1930 | -5.5 | 31% | +3.20 | +1.01 | 24/9 | 32% | 23/4 |

### Per-setup effect: delta total R (trades kept) vs no rules

| setup (BEG_alone / fit) | base n | base R | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | ALL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BEG-01 | 556 | -213.2 | +9.6 (536) | +22.5 (529) | +0.0 (556) | +4.7 (542) | +20.3 (527) | +24.1 (503) | +90.0 (336) | +27.3 (487) | +123.0 (246) |
| BEG-02 | 505 | -73.5 | +4.8 (464) | +14.3 (469) | +0.0 (505) | -6.6 (489) | +8.6 (475) | -8.8 (467) | +51.0 (247) | +2.7 (482) | +40.8 (206) |
| BEG-03 | 321 | -18.8 | +0.9 (317) | +10.8 (299) | +0.0 (321) | +15.1 (263) | +1.1 (316) | -3.0 (294) | +3.0 (191) | +5.9 (276) | +8.9 (137) |
| BEG-04 | 1860 | +197.6 | +5.3 (1651) | -265.0 (583) | +0.0 (1860) | -250.5 (498) | +12.1 (1706) | +98.0 (1576) | +0.0 (1860) | -41.0 (1603) | -250.0 (427) |
| BEG-05 | 137 | -42.1 | +0.0 (137) | +0.0 (137) | +0.0 (137) | +5.9 (122) | +0.0 (137) | +0.0 (137) | +0.0 (137) | +8.3 (107) | +12.9 (97) |
| BEG-06 | 265 | -25.2 | +7.3 (258) | -4.1 (220) | +0.0 (265) | +0.0 (265) | +0.7 (262) | -3.0 (254) | -3.5 (259) | +24.7 (160) | +4.7 (126) |
| BEG-07 | 2223 | -195.5 | +0.0 (2223) | +106.8 (1020) | +0.2 (2221) | +144.4 (678) | +0.0 (2223) | +0.0 (2223) | +0.0 (2223) | +14.7 (2000) | +159.3 (675) |
| BEG-08 | 1570 | -118.5 | +5.1 (693) | +117.5 (433) | +0.0 (1570) | +51.5 (790) | +62.4 (824) | -27.3 (1535) | +0.0 (1570) | +5.4 (1492) | +113.7 (382) |
| BEG-09 | 481 | -11.6 | +0.0 (481) | -1.0 (466) | +0.0 (481) | +8.0 (433) | +0.0 (481) | +1.0 (480) | +18.0 (324) | -0.7 (431) | +24.4 (258) |
| BEG-10 | 13733 | -727.6 | +339.2 (9025) | +648.8 (991) | +0.0 (13733) | +633.1 (1154) | +240.7 (9009) | +30.5 (12815) | +249.9 (9364) | +306.6 (10803) | +701.8 (835) |

| setup (BEG_alone / check) | base n | base R | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | ALL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BEG-01 | 1315 | -330.8 | +41.8 (1220) | +46.8 (1216) | +0.0 (1315) | -8.4 (1289) | +60.6 (1216) | +22.2 (1180) | +181.2 (755) | +51.4 (1185) | +208.8 (581) |
| BEG-02 | 1149 | -102.7 | -4.5 (1054) | +11.7 (1042) | +0.0 (1149) | +6.5 (1126) | -24.6 (1075) | +8.7 (1056) | +22.8 (538) | +7.7 (1105) | +35.8 (468) |
| BEG-03 | 595 | +3.3 | -1.3 (587) | -2.9 (542) | +0.0 (595) | -0.2 (483) | -3.3 (586) | +4.6 (540) | +14.1 (367) | +6.5 (523) | +18.7 (243) |
| BEG-04 | 4465 | -180.6 | -158.9 (3893) | +63.2 (1350) | +0.0 (4465) | +112.6 (1138) | -35.7 (4052) | +22.0 (4043) | +0.0 (4465) | +0.3 (4025) | +85.8 (1006) |
| BEG-05 | 226 | -30.2 | +0.0 (226) | +0.0 (226) | +0.0 (226) | +1.2 (218) | +0.0 (226) | +0.0 (226) | +0.0 (226) | +18.9 (104) | +18.9 (104) |
| BEG-06 | 471 | -14.4 | -1.4 (469) | -22.4 (387) | +0.0 (471) | +0.0 (471) | -1.7 (470) | +6.9 (438) | +3.4 (457) | +0.0 (338) | -10.5 (255) |
| BEG-07 | 4326 | -159.7 | +0.0 (4326) | +96.8 (1654) | +2.1 (4320) | +129.2 (1106) | +0.0 (4326) | +0.0 (4326) | +0.0 (4326) | +14.3 (4001) | +116.6 (1096) |
| BEG-08 | 2424 | -144.1 | +67.6 (1305) | +77.9 (884) | +0.0 (2424) | +57.7 (1653) | -3.4 (1539) | +6.7 (2383) | +0.0 (2424) | +38.9 (2314) | +115.7 (793) |
| BEG-09 | 1034 | -79.8 | -2.1 (1008) | +3.2 (956) | +0.0 (1034) | +13.6 (890) | +3.5 (1019) | +3.3 (1027) | +47.7 (639) | +3.0 (922) | +34.6 (510) |
| BEG-10 | 24779 | -1880.3 | +390.0 (15382) | +1709.3 (1652) | +0.0 (24779) | +1659.9 (1904) | +570.4 (15369) | +123.8 (22572) | +631.1 (15968) | +412.4 (20501) | +1755.0 (1384) |

| setup (BEG_book / check) | base n | base R | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | ALL | MCF |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BEG-01 | 1315 | -330.8 | +93.7 (1051) | +189.5 (754) | +0.0 (1315) | +141.5 (817) | +108.4 (1040) | +22.2 (1180) | +181.2 (755) | +51.4 (1185) | +272.5 (380) | +77.0 (1105) |
| BEG-02 | 1149 | -102.7 | +54.2 (583) | +86.6 (184) | +0.0 (1149) | +60.3 (343) | +52.0 (582) | +8.7 (1056) | +22.8 (538) | +7.7 (1105) | +98.8 (127) | +18.0 (872) |
| BEG-03 | 595 | +3.3 | -8.9 (399) | -13.7 (184) | +0.0 (595) | -5.6 (210) | -5.7 (383) | +4.6 (540) | +14.1 (367) | +6.5 (523) | -1.4 (97) | -7.4 (566) |
| BEG-04 | 4465 | -180.6 | +92.5 (2262) | +149.4 (401) | +0.0 (4465) | +132.2 (588) | +118.4 (2187) | +22.0 (4043) | +0.0 (4465) | +0.3 (4025) | +131.3 (513) | -138.4 (3403) |
| BEG-05 | 226 | -30.2 | +20.6 (34) | +30.2 (0) | +0.0 (226) | +30.2 (5) | +12.7 (179) | +0.0 (226) | +0.0 (226) | +18.9 (104) | +30.2 (0) | +7.0 (127) |
| BEG-06 | 471 | -14.4 | -22.1 (167) | +7.4 (28) | +0.0 (471) | -14.7 (139) | +14.3 (264) | +6.9 (438) | +3.4 (457) | +0.0 (338) | -3.1 (36) | -20.5 (347) |
| BEG-07 | 4326 | -159.7 | +116.6 (805) | +159.7 (0) | +2.1 (4320) | +150.6 (303) | +29.1 (3468) | +0.0 (4326) | +0.0 (4326) | +14.3 (4001) | +156.4 (11) | +129.4 (2657) |
| BEG-08 | 2424 | -144.1 | +130.9 (484) | +143.0 (1) | +0.0 (2424) | +140.0 (396) | +177.9 (1045) | +6.7 (2383) | +0.0 (2424) | +38.9 (2314) | +145.7 (54) | +121.4 (774) |
| BEG-09 | 1034 | -79.8 | +72.3 (133) | +79.8 (0) | +0.0 (1034) | +62.6 (235) | +15.2 (711) | +3.3 (1027) | +47.7 (639) | +3.0 (922) | +86.7 (11) | +40.5 (631) |
| BEG-10 | 24779 | -1880.3 | +575.6 (11188) | +1851.3 (104) | +0.0 (24779) | +1819.3 (1026) | +801.8 (10059) | +123.8 (22572) | +631.1 (15968) | +412.4 (20501) | +1864.8 (397) | +387.7 (14065) |

| setup (Primary / live) | base n | base R | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | ALL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CWT13-vwapstretch-z05-long | 11 | -4.7 | +1.8 (8) | +4.7 (0) | +0.0 (11) | +3.5 (3) | +2.2 (9) | +0.0 (11) | +1.8 (8) | +0.7 (9) | +3.1 (2) |
| CWT14-failbrk-pdl-p10-lowvol-long | 78 | -3.4 | +1.8 (74) | +6.1 (19) | +0.0 (78) | +9.9 (39) | +1.9 (74) | +0.0 (78) | -0.7 (33) | +0.1 (71) | +0.2 (17) |
| L3-gap-slope-fromopen-FD | 181 | +30.0 | +6.0 (170) | -26.8 (24) | +0.0 (181) | -34.2 (36) | -5.2 (165) | -3.0 (175) | -6.9 (145) | -6.0 (142) | -26.3 (15) |
| L3-gap-slope-rsi5hi-FD | 22 | -10.3 | +7.8 (10) | +10.7 (1) | +0.0 (22) | +1.7 (8) | +2.2 (15) | -0.4 (21) | +3.0 (15) | +0.9 (13) | +10.3 (0) |
| MF1-945-flowsell-vwapup | 25 | -6.9 | +1.3 (24) | +8.5 (11) | +0.0 (25) | +8.0 (16) | +4.5 (19) | -1.9 (24) | +4.0 (8) | +5.5 (14) | +10.1 (4) |
| MF2-open-rsimidhi-flowsell | 4 | -5.0 | +0.0 (4) | +5.0 (0) | +0.0 (4) | +3.7 (1) | +1.2 (3) | +0.0 (4) | +1.2 (3) | +0.0 (4) | +3.7 (1) |
| MF2-open-rsimidhi-flowsell-FD | 111 | -7.5 | -26.8 (71) | +9.3 (8) | +0.0 (111) | +8.0 (21) | +11.4 (95) | +0.0 (111) | -24.4 (61) | -6.6 (83) | +5.2 (5) |
| MF3-open-flowsell-rsi5hi | 29 | -4.4 | +1.2 (24) | +5.4 (7) | +0.0 (29) | +5.5 (6) | +3.6 (19) | +1.1 (28) | +3.7 (18) | +1.9 (23) | +4.7 (2) |
| MF3-open-flowsell-rsi5hi-FD | 45 | -10.0 | -1.9 (21) | +6.9 (8) | +0.0 (45) | +10.6 (11) | +4.8 (36) | +0.0 (45) | +6.5 (19) | +3.8 (35) | +10.2 (6) |
| MF4-h40-open-flowsell | 21 | +0.5 | +2.1 (17) | +0.9 (8) | +0.0 (21) | +2.0 (11) | +0.7 (14) | -0.3 (20) | +2.2 (13) | -2.7 (15) | +0.7 (6) |
| MF4-h40-open-flowsell-FD | 126 | -51.2 | -0.1 (108) | +42.6 (19) | +0.0 (126) | +44.1 (30) | +5.6 (112) | +2.2 (123) | +25.8 (63) | +19.6 (87) | +46.7 (18) |
| MF5-flowsell-vwapup-rsi5hi | 31 | -4.5 | +5.4 (18) | +4.5 (1) | +0.0 (31) | +4.5 (8) | +2.6 (24) | +0.0 (31) | +4.0 (14) | +3.7 (24) | +3.7 (3) |
| NM-ETF-late-dip-di-long | 15 | +1.1 | +0.1 (8) | -1.1 (0) | +0.0 (15) | -1.1 (4) | -0.8 (13) | +0.0 (15) | +0.0 (15) | -0.5 (7) | -1.1 (0) |
| NS1-rsidip-rsi5pop-long | 23 | -0.8 | -0.7 (18) | -0.7 (5) | +0.0 (23) | -1.4 (11) | -0.3 (18) | +1.0 (21) | +2.6 (13) | +1.0 (18) | +1.1 (5) |
| NS2-sma50break-overbought-short | 54 | -27.5 | +11.7 (35) | +25.4 (10) | +0.0 (54) | +22.9 (13) | +11.7 (35) | +0.0 (54) | +26.4 (11) | -0.3 (53) | +26.8 (5) |
| NS3-failed-vwap-reclaim-short | 9 | -3.3 | +2.2 (1) | +3.3 (0) | +0.0 (9) | +3.4 (1) | +0.0 (4) | +0.0 (9) | +2.2 (1) | +1.2 (6) | +3.3 (0) |
| NS3-failed-vwap-reclaim-short-FD | 32 | -13.2 | +1.3 (21) | +11.5 (4) | +0.0 (32) | +11.6 (4) | +1.0 (29) | +0.0 (32) | +8.5 (9) | +1.2 (26) | +10.6 (4) |
| NS4-pm-vwap-reclaim-oversold-short | 20 | -0.6 | -3.1 (6) | +0.6 (0) | +0.0 (20) | +0.3 (5) | -0.1 (19) | +0.0 (20) | +1.8 (10) | +1.5 (17) | +0.4 (4) |
| NS5-sma50-flush-oversold-long | 41 | -0.8 | +4.5 (24) | -2.4 (11) | +0.0 (41) | -0.9 (23) | +4.0 (29) | +0.0 (41) | +3.9 (23) | +0.9 (35) | +0.3 (10) |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 169 | +21.1 | -35.4 (108) | -25.9 (17) | +0.0 (169) | -29.5 (44) | -35.0 (131) | -0.7 (168) | -16.8 (109) | +2.6 (140) | -26.1 (16) |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 180 | +10.7 | -31.0 (108) | -11.9 (8) | +0.0 (180) | -6.2 (28) | -11.1 (146) | -0.1 (179) | -28.5 (100) | +0.2 (139) | -9.5 (11) |
| RW6G1-ns2-up3-vwap2sd-short | 3 | -3.3 | +2.2 (1) | +3.3 (0) | +0.0 (3) | +2.2 (1) | +2.2 (1) | +0.0 (3) | +3.3 (0) | +0.0 (3) | +3.3 (0) |
| ST7-rsi50dn-long-pm-t1s1-FD | 42 | -7.3 | +1.4 (39) | +2.0 (18) | +0.0 (42) | +1.4 (18) | +2.2 (39) | +1.2 (41) | -3.4 (28) | -0.5 (39) | +0.4 (13) |
| exhaustion_short | 23 | -7.5 | +5.3 (2) | +7.5 (0) | +0.0 (23) | +4.9 (7) | +5.6 (13) | +0.0 (23) | -1.5 (16) | +0.3 (20) | +5.1 (4) |
| heat_fade_long | 43 | -6.4 | +3.4 (8) | +6.4 (0) | +0.0 (43) | +3.9 (11) | +3.0 (37) | +0.0 (43) | +2.5 (33) | -0.7 (41) | +5.7 (6) |
| heat_fade_short | 50 | -16.5 | +6.0 (34) | +11.0 (14) | +0.0 (50) | +14.7 (12) | -1.9 (48) | +0.0 (50) | +2.4 (31) | -0.3 (45) | +12.6 (9) |
| orb20_a | 9 | -1.6 | +0.9 (7) | +2.5 (5) | +0.0 (9) | +1.5 (6) | -0.2 (7) | +0.0 (9) | +0.1 (6) | +1.1 (4) | +0.6 (1) |

