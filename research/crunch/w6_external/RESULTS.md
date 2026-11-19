Educational only — not financial advice

# W6-external — outside ideas tested on MCF's live journals (2026-11-18, crunch)

This is research only. No config, code, setup or branch was changed outside this folder, and nothing needs a decision until the owner replies to a code. Data: live run (run_id 1) from all ten `mcf-data*` journals, 10-06..11-17 (31 sessions, 25,921 trades), with R after LR8 costs. Pre-open features come from the release asset `bars-2026-11/1day-2026-11-17.parquet`, and SPY 1-minute bars come from Alpaca market data (GET only). The locked block was not read, and no 2-year data was used. Fit half: 10-06..10-27 (16 sessions). Check half: 10-28..11-17 (15 sessions). The plan was pre-registered in PLAN.md before any scoring.

**Configurations tried: 35.** That is 26 pre-registered plus 9 post-hoc descriptive cuts, labelled as such below. The bar is day-clustered t ≥ sqrt(2 ln 35) = **2.67**, with the right sign in both halves.

**Rule changes inside the window (research/ledger.jsonl):**
- 10-20: twin-symbol block.
- 10-22/23: per-setup latch off in Testing 1/2.
- 10-27: slots 160 → 77.
- 10-28: Primary sizing (~$4k).
- 10-29: -2R latch and BAR90.
- 11-05: ROLL1 low-rep homes.
- 11-11: TEAM-6.
- 11-12: LR8 after-cost R; Testing D/E/F opened.
- 11-16: ROT1.
- 11-17: TSZ1 half-size testing, 15 WB copies, promotion hold.

The fit/check boundary (10-27/28) falls on the slots and sizing changes. R per unit of risk is not distorted by sizing, but the latch and LR8 change which trades count.

**Outside sources:** see SOURCES.md. WebFetch could not reach any host (they are not on the session's network allowlist), so all ten citations rest on search abstracts and summaries, not full papers.

## Failures first

| ID | Hypothesis (pre-registered) | Result | Verdict |
|---|---|---|---|
| X6 | Scaling daily risk by 1/SPY variance (Moreira-Muir) raises daily Sharpe in both halves | Primary journal: Sharpe fell in both halves at L=10 (-0.056 → -0.113, -0.167 → -0.224). Lookbacks 5 and 20 did not form a plateau. The check-half "gain" on pooled books (-2,164R → -639R) only reflects weights falling to 0.08-0.11 from 11-06, when SPY variance rose. R per trade was **not** worse in high-variance terciles (-0.110 vs -0.139 in the low tercile; P3). The weights cut exposure on a losing stretch and do not identify bad days. | **FAIL**. Back on the stop list with P8's sizing tilts. |
| X5 | Late trades (≥ 15:00) aligned with SPY's first half-hour do better (Gao et al.) | The reverse held: aligned trades averaged -0.219 (n 181) and trades against it +0.096 (n 100), with the same sign in both halves. The pre-registered filter F5 cost -9.6R. | **FAIL** as registered. The reversed version (post hoc, no look-ahead) saves +26.7R, t 2.33, n 126, 0 Primary trades. It is below the bar and too small to matter. |
| X3 | Gap-fade trades do better in low-liquidity names and on high-uncertainty days (Branch-Ma) | Wrong direction: the low-ADV tercile was worst (-0.229) and the top tercile least bad (-0.124). The check half had no low-variance days, so the uncertainty split cannot be identified. F3 (skip gap fades in the top ADV tercile): +199.6R, t 1.56, 75 setups improve / 43 worsen. It only "works" because all 3,500 gap-fade trades lose (-0.179R/trade). | **FAIL** (mechanism). See P1 for what does hold. |
| X4 | Short tail losses are squeeze-type, concentrated after run-ups or gap-ups and in names under $10 | Tail losses (R ≤ -1.5) are rare: 0.6% of shorts and 3% of short losing R. Stops hold, and no short traded under $5. F4 (skip shorts after a ≥ +25% 5-session run-up): +34.0R, but fit +0.6 / check +33.4, t 1.32, best-day share 0.67. It costs L3-gap-slope-fromopen-FD +3.1R over 8 trades. | **FAIL** at the bar. Watch only; it would touch the protected L3. |
| X2 | Few live setups pass a try-count bar | **0 of 114** setups with ≥ 30 trades reach t ≥ 3.27 (N = 210 distinct setups). Only 2 reach t ≥ 1.5, against ~7.6 expected by chance with no edge at all. Best: L3-gap-slope-fromopen-FD t 1.70 (+90.3R, 378 trades, w/o best day +0.190, best-day share 37%). Next: GEN-261027-08 t 1.61 (5 days only). | Confirmed. No live record is yet statistically distinguishable from luck. |

## What held up

| ID | Result | n / t | Notes |
|---|---|---|---|
| **X1 PBO (CSCV, 8 blocks, 70 splits, 135 setups ≥ 20 trades)** | Picking the best **avg R per trade**: PBO **0.74**. The in-sample winner's median out-of-sample rank is the 13th percentile, at -0.32R/trade vs -0.12 for the median setup. Picking the best **total R**: PBO **0.24**, median OOS rank the 87th percentile, OOS +10.1R vs -4.2R for the median. An in-sample top-decile basket beat the all-setup mean out of sample in 71% of splits (+3.5R). | 2 configs | The leader by avg R is mostly noise from small samples. Total R (which rewards a large n) persists. This supports C3-BAR2's shrunk estimate n/(n+150)·avg + ... over raw avg R. It conflicts with nothing. |
| **X7 implied breadth** | Primary's current 10 setups (pooled across accounts, daily R): average pairwise correlation 0.091, implied breadth **5.5**. Strong pairs: **L3-fromopen ↔ RW3 0.74**, L3-rsi5hi ↔ NS1 0.76, L3-rsi5hi ↔ MF2-FD / MF4-FD 0.55. | 0 | This conflicts with Part 3's "L3 corr 0-0.03 with RW3". Part 3 used Primary-only series; this uses series pooled across accounts. Both should be checked before L3 and RW3 are called diversifiers. |
| **P1 (post hoc) trade R by relation to the open gap** | Trading **with** a ≥ 2% gap: -0.058 fit / **+0.008** check (4,362 trades). No gap: -0.123 / -0.149. **Fading** the gap: -0.157 / -0.187. In Primary: with-gap +0.065 / +0.120, fade **-0.376 / -0.596**. | 1 | This matches the literature (the reversal has decayed in liquid names) and P3's "gap mechanisms -0.008 vs -0.140R". Across 62 setups with ≥ 10 trades on both sides, fades are worse in 36 and better in 26 (median -0.045R). So it is not a system-wide rule. |
| **MF (post hoc) open-flowsell family shorts that fade a ≥ 2% gap-up** | 127 trades at **-0.558R** (fit -0.450, n 26; check -0.586, n 101), vs -0.137 for the rest of the family. Skipping them: **+70.9R**, day-t **2.14**, 15 days, worst-day share 0.40, **9 setups improve / 1 worsens**. Negative in every gap-size bucket (2-4%, 4-8%, >8%). In Primary, MF2-open-rsimidhi-flowsell-FD's 28 fades made **-21.7R**, while its 83 other trades made +20.7R. MF4-FD fades: -9.2R. | 1 | **Below the bar** (2.14 < 2.67), and the fit half has only 26 trades. It is a family-level, targeted remedy (one failure mode, one family), so it fits the owner's remedy rule. It is independent support for C3-WB5 item 3 (NM-MF3's gap-down gate on MF2-FD / MF4-FD). |
| **Q1/Q4 (post hoc) early (< 10:00) trades against SPY's move since the prior close, measured at entry with no look-ahead** | n 1,395, -0.321 check / -0.189 fit, vs aligned +0.009 / -0.272. Skipping: +376.5R, t 2.51, 32 setups improve / 13 worsen, best-day share 0.20. **Most of it is CWT14** (failbrk-pdl longs -97.6R, -46.3R, -26.5R). Without CWT12/CWT14 the fit half flips (against -0.120 vs aligned -0.552), t 1.47. | 2 | It is not a general rule. It adds weight to C3-EXIT100 for the CWT14 failbrk longs, which lose mainly when they buy against a down-opening market. |

Per-setup improve/worsen counts are in out/tests.txt and out/posthoc*.txt. Avg R w/o best day and best-day share are given for every filter above.

## Proposals (reply codes; nothing changes without the owner)

| Code | Proposal | Evidence | Honest expected effect |
|---|---|---|---|
| **W6-MFGAP** | Pre-register now, score forward: open-flowsell (MF1-MF5) shorts skip a stock whose open gapped up ≥ 2% (one part). Run it as a shadow tag on the existing MF setups (report-only column: "would have skipped"). Once C3-WB5 item 3 is approved, use it as one of that copy's ≤ 2 parts. No Primary change while it is below the bar. | +70.9R over 31 sessions, t 2.14, 9 setups improve / 1 worsens. Primary MF2-FD fades -21.7R. | If it holds: about +2R/session across the arena and ~+0.8R/session in Primary (MF2-FD + MF4-FD fades ≈ -31R / 31 sessions). It could be zero: fit n is only 26. |
| **W6-PBO** | In promotion and leaderboard ranking, never rank by raw avg R per trade. Rank by total R or by C3-BAR2's shrunk estimate, and add a CSCV PBO line (this script) to each Friday review. | PBO 0.74 (avg R) vs 0.24 (total R) over 70 splits. | Fewer promotions of small lucky records. No direct R. |
| **W6-DSR** | Leaderboard and brief column: day-clustered t of the live record next to the try-count bar sqrt(2 ln N) for N live setups (now 3.27), reporting only. | 0 of 114 pass. Best t is 1.70. | Stops "proven" labels on records that are still noise. No R. |
| **W6-BREADTH** | Before C3-NS5 / C3-BAR2 decisions that rely on diversification, recheck L3-fromopen ↔ RW3 correlation on both series (Primary-only 0-0.03 vs pooled 0.74). | X7 | Avoids counting two correlated gap shorts as two bets. No R. |
| **W6-HKS / W6-SIP** | Next studies (not run, need 1-min packs ~4,700 names/day; disk too tight tonight): (a) the stock's return in the same 30-minute slot on the prior 1-5 days as a condition (Heston-Korajczyk-Sadka); (b) opening-range relative volume ≥ 100% of its 14-day average as a quality gate on opening setups (Zarattini-Barbon-Aziz). Each pre-registered with ≤ 3 configs, fit/check split. | Literature only. | Unknown. Both aim at quality reps, not more trades. |

**Not proposed:** volatility-managed sizing (X6 FAIL), the late-day SPY filter (X5 FAIL, tiny), the squeeze filter F4 (FAIL at the bar, touches protected L3), the liquidity-tercile gap filter F3 (wrong mechanism), and daily loss limits (no outside evidence; P8 already failed them).

## Caveats

- 31 sessions; the check half is 15 sessions inside a single SPY volatility rise.
- The pooled series counts copies in several accounts (twin symbols overlap).
- Gap and ADV come from Alpaca SIP daily bars; 0.5% of trades lack a gap and are excluded.
- Post-hoc cuts (P1-P3, Q1-Q5, MF) were chosen after seeing X3/X5. They count in N, but they are not confirmations and need forward sessions.
- Outside sources were read only as search abstracts (network allowlist).
- Scratch data were deleted after the run.
