# Overnight Consultant: Final-Push Report (2026-11-21)

**Educational only — not financial advice.** All figures are R after costs (LR8). "CHECK" is the holdout, scored once. "T2" is 2023-01..2024-09.

## Owner summary (5 lines)
1. **Nothing new passed.** We tried 128 setup configs across 6 tracks, plus 12 robustness neighbour configs. No new setup goes to testing and nothing is ready for Primary.
2. **Primary's red days (SPY-up and quiet days) are still not covered.** Every new long only made about what the market rose, and lost on quiet days. Every gap-down short just adds to Primary's existing down-tape bet.
3. **April 2025 (tariff crash) carried most of the "strong" lab results.** Take that week out and the gap-down, open-drive and ETF-burst edges are about zero or negative.
4. **Promotion pipeline:** no promotion on 11-27. The best candidate, P1 (L3-lowdist), owes 69% of its R to one day (11-12). That day was the first session after the On Deck split-tape gate was switched off. The earliest realistic promotion is mid or late December.
5. **Only process and shadow decisions are on the table (FP-A to FP-F below).** None of them changes live setups or exits.

## All candidates

| Track | Name | Side | CHECK avg R | w/o best day (CHECK) | vs null | vs top-10 | Skeptic | Robust |
|---|---|---|---|---|---|---|---|---|
| cov-long | N1 narrow-range opening-range breakout | L | -0.057 (t -1.86) | -0.066 | loses less than random | NEAR (fails CHECK avg) | refuted | — |
| cov-long | E2 late-day ETF momentum | L | -0.039 | -0.057 | = random | Tier A in name only | refuted | — |
| cov-long | M7 trend-day VWAP pullback | L | -0.034 | -0.038 (FIT+CHECK) | ≈ random; worse on T2 | NEAR (fails R/session) | refuted | — |
| cov-long | M6 SPY gap-up stock new high of day | L | -0.077 | -0.042 (FIT+CHECK) | slightly above random | FAIL | — | — |
| cov-long | M2 prior-day-high break, green tape | L | -0.074 | -0.060 (FIT+CHECK) | below random | FAIL | — | — |
| cov-long | M3 relative-strength new high of day | L | -0.061 | -0.067 | ≤ random | FAIL | — | — |
| cov-long | M5 quiet-tape leader | L | -0.088 | -0.096 | = random | REALLY BAD | — | — |
| cov-long | M4 late-day stock momentum | L | -0.062 | -0.066 | = random | REALLY BAD | — | — |
| cov-long | M1 gap and go | L | -0.077 | -0.087 | = random | REALLY BAD | — | — |
| cap-etp | A-vwhold: buy inverse ETP, DN state | L (inverse) | +0.030 (t 0.44) | +0.012 (w/o top-2 -0.006; 60% one day) | timing +0.19 vs random DN bar | Tier A in name only | refuted (timing finding kept) | — |
| cap-etp | B-vwhold: short bull ETP | S | -0.019 | -0.034 | beats day null | borderline | — | — |
| cap-etp | A-brk / C-brk | L | not scored | — | beats day null | FIT fail | — | — |
| open-drive | OD2 failed down-push long | L | -0.037 (t -1.42) | -0.049 | only vs a null added after FIT | MEETS (median bar loses money) | refuted; breaks pre-reg | — |
| open-drive | OD7 gap-down ≥4% drive short at 09:50 | S | -0.018 | -0.051 | ≤ random | NEAR (T2 -0.129 fails) | refuted | — |
| open-drive | OD5 gap-down ≥4% gap and go | S | -0.023 | -0.071 | below matched null | NEAR (T2 -0.161 fails) | refuted (strongest) | — |
| open-drive | OD1 down-drive short, rvol ≥2 | S | -0.059 | -0.065 | = null | FAIL | — | — |
| open-drive | OD5 gap ≥2% short | S | -0.067 | -0.097 | below null | FAIL | — | — |
| open-drive | OD2 failed up-push short (BDI 11-20 pattern) | S | FIT only, -0.103 to -0.004 | — | below null | FAIL | — | — |
| trio | R2c L3 recovery in ATR units | S | -0.017 | -0.039 (combined -0.088; 144% one day) | = later-entry null | NEAR / Tier B | refuted | — |
| trio | R2b L3 small gap | S | -0.0485 | -0.060 | = later-entry null | FAIL Tier A | refuted | — |
| trio | R2a, S1-S7 (8 ideas) | S | -0.081 to -0.26 (FIT/CHECK) | — | — | FAIL / REALLY BAD | — | — |
| promo-pipe | P1 L3-gap-slope-lowdist-FD (live) | S | live +0.237 | +0.103 (69% one day) | p 0.004 (picks stock-day) | lab FAIL | upheld as watch only | not promotable; all 7 lab neighbours negative |
| promo-pipe | P2 L3-gap-slope-rsi5hi-FD (live) | S | live +0.096 | +0.022 (82% one day) | p 0.12 w/o best day | MEETS | refuted | — |
| promo-pipe | P3 RW7 gap-down bounce early short (live) | S | live +0.069 | +0.024; -0.027 under Primary book | worse than random (p 0.83) | FAIL/NEAR | refuted | — |
| promo-pipe | P4 CWT09-g10 VWAP-loss short (live) | S | live +0.228 (n 24) | +0.151 | none (p 0.82) | MEETS T1; T2 fails | upheld as low-rep watch | not promotable; flat plateau, about 0 w/o best day |
| promo-pipe | P5 GEN-261029-06 (live) | L/S | live +0.131 | +0.040 (75% one day) | p<0.001 | not scored | refuted (no mechanism, regime flip) | — |
| promo-pipe | X1 RW1 flow-sell short (live) | S | live +0.014 | -0.027 | worse than random | NEAR | — | — |
| etf-burst | V30A3: skip burst on SPY 15-min flush ≥0.30 ATR | L (remedy) | dR +8.87R (1 bar) | +0.066 | CHECK p 0.075 | NEAR | refuted (CHECK seen early; threshold set with hindsight) | — |
| etf-burst | V25A3 | L (remedy) | dR +5.91 (3 days worse) | +0.058 | p 0.197 | NEAR | refuted | — |
| etf-burst | C1A1 owner spec: one lot per group below VWAP | L (remedy) | dR +7.12 | +0.059 | — | FAIL (FIT -12.8R; net -8.2R) | — | — |
| etf-burst | C2/C3/C4 burst trims, C0 cap | L (remedy) | FIT dR -1.7 to -40.8 | — | — | FAIL | — | — |

## What passed: owner decisions
None of the decisions below is a new testing setup.

- **FP-A: put P1 in Primary shadow (PSHADOW, no orders) once its On Deck stage ends.** This builds the Primary-overlap record the promotion bar needs. **Optional.**
  - Numbers: live 111 trades, +0.237, w/o best day +0.103, best-day share 69%, strict non-overlap shrunk -0.016. All 7 lab neighbours are negative, though lab and live disagree on which symbol-days to trade.
  - Must be done outside 09:30-16:00 ET, with a ledger entry and regenerated assignments.

- **FP-B: count P1 and P2 as one L3 slot in all promotion rankings.** **Yes.**
  - Numbers: daily correlation 0.75, and both are carried by 11-12.

- **FP-C: add a "Primary-book replay" gate to the promotion bar.** The candidate must stay positive w/o best day under cap 30 and the -2R latch, and must beat the random-entry null. **Yes.**
  - Numbers: RW7 falls from +60.1R to +18.1R (w/o best day -0.027), yet it would pass the current 11-20 pre-registration on beta alone.

- **FP-D: run V30A3 (ETF-burst index-flush skip) as a shadow tally only, no live change.** **Optional (lean No).**
  - Numbers: it improved 5 of 5 burst events (dev +18.1R, CHECK +8.9R from 1 bar). It fires about twice a year, does not fire on 11-20, its CHECK was seen early, and its threshold was set with hindsight.

- **FP-E: backlog the "VWAP-hold timing inside an index-down state" finding as an entry-quality idea for existing index-short setups.** **Optional.**
  - Numbers: it beats random DN-state entries by +0.19R (t 4.5) on CHECK, but it only lifts a losing base to about zero.
  - A further test needs a fresh holdout.

- **FP-F: do not deploy the owner's C1A1 burst rule.** **No (do not deploy).**
  - Numbers: CHECK +7.1R and live replay +21.6R (all on 11-20), but FIT -12.8R and net -8.2R. The effect flips sign between periods.

## What failed: do not re-run
- **cov-long (24 configs):** all 9 long mechanisms (N1, E2, M1-M7).
  - Long-side lesson: the gain on SPY-up days is about the market move, and they lose on quiet and flat days. They roughly match random entries.
  - M1, M4 and M5 meet the REALLY BAD definition.
- **cap-etp (19 configs):** inverse/vol ETP buys, bull-ETP shorts, bull-ETP breakouts, onset entries, SPY ≤ -0.30% filters, t05s1 geometry.
  - The whole family is one bet that the index keeps falling.
- **open-drive (38 configs):**
  - OD1-OD8, both sides.
  - The BDI 11-20 failed-up-push short loses over 2 years (p0.3 FIT -0.103, t -3.0).
  - Gap-down ≥4% shorts are April-2025 artifacts and fail T2.
- **trio-family (20 configs):** tier-2 liquidity, no-flow, pop-fail, ETF, PDL reject, delayed trio entry, slope inversion, mid-recovery, small-gap, ATR-recovery.
- **etf-burst (21 configs):**
  - Every index-state burst trim: below VWAP, all three indexes down, trend since 13:00, near the day's low.
  - The unconditional cap, which cuts the setup's best pocket.
  - On these measures the 11-20 burst looks like the profitable April-2025 bursts.
- **promo-pipe (6 reviewed):**
  - X1 RW1 has no promotion path.
  - P5 stays out of On Deck talk until it has a mechanism note and 20+ sessions.

## Promotion pipeline: next Friday window (11-27)
**Nothing is ready, and the promotion hold is on anyway.**

| Rank | Setup | Gap to the bar | Realistic date |
|---|---|---|---|
| 1 | P1 L3-lowdist-FD (with P2 as one slot) | Best-day share under 50% (about +10R with no new best day); strict non-overlap shrunk > 0; positive in an October-type week now that the gate is off | mid/late Dec |
| 2 | P4 CWT09-g10 | 30 or more trades and 20 or more sessions; shrunk > 0 needs about 66 trades. The only setup uncorrelated with Primary, but at about 0.8 trades/session it cannot move daily R | Jan+ |
| 3 | P2 L3-rsi5hi-FD | Second half is fading; it already lost -9.5R in its own Primary stint | not before raw best-day share ≤ 40% |
| Watch | P3 RW7, P5 GEN | Fail FC-C; both rest on the 11-20 short-beta day; correlation 0.72 with each other | — |
| Not eligible | BEG-ORB, 9 ULT admissions | Need 20 traded sessions | about mid-Dec |

Rule-change context inside the window (10-13..11-20):
- **11-12:** ODX-1 split-tape short gate off in On Deck; rows before 11-12 re-costed to LR8; halt 300R; P4 moved into On Deck.
- **11-17:** TSZ1 testing sizing; WB4 copies added in Testing F.

P1's best day (11-12) is the first session after the gate change. Before 11-12, P1 was -0.042 w/o best day.

## Conflicts with owner rules
1. **OD2 was labelled "candidate" against its own pre-registration.** The pre-reg needed CHECK > 0 or t ≥ 2.70. It reached the finalists only through a null added after FIT.
2. **Trio round 2 (R2a-c) was designed after seeing round-1 FIT.** It was not pre-registered, but it is counted in N.
3. **ETF-burst CHECK was contaminated.** A diagnostic printed CHECK burst rows before the grid was declared, so V30A3 and V25A3 are shadow material at most.
4. **Several "Primary red-day hedge" claims rest on a 22-session live overlap, and some use end-of-day SPY direction (hindsight).** These are N1, M7, R2b, R2c and A-vwhold. The guardrails exclude pure hedges.
5. **"Promotion = move / no copies":** P4 has WB4 copies (Testing F) and a near-twin in Explore 1 (NM1). Adding any new testing home would be a copy, so none is proposed.
6. **P5 is GEN with no stated mechanism**, which the guardrails rule out.
7. **Remedy rule:** V25A3 makes 3 CHECK days worse and C1A1 flips sign between periods, so both fail the "targeted, without hurting other cases" standard.
8. **One-big-day rule:** every live candidate (P1, P2, P3, P5) carries the `1 day` tag. P4 sits at 48%.

## Configurations tried
- **128 build configs:** cov-long 24, cap-etp 19, open-drive 38, trio 20, etf-burst 21, plus 6 promo-pipe live records reviewed.
- **12 lab neighbour configs** in the P1/P4 robustness check.
- **Total: 140.**
- No config reached its WB2 bar (2.18-2.70). No test read the locked block (2024-11..2025-02). Live overlap is 22 sessions, because the 1-min data cache ends 2026-11-04.

**Educational only — not financial advice.**