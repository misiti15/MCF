Educational only — not financial advice

# ARENASTARS-1127: audit of the three strongest arena records, and do they belong in Primary? Research only. **FAIL**

Pre-registered: PREREG.md (commit 24e8d70654, before any score). **Configs: 15** (3 history replays + 12 Primary-book
configs). Cumulative N ≈ 8,952 → **≈ 8,967** (family bar ≈ 4.27, reference only). Locked block 2024-11-01..2025-02-28
never read (asserted in every script). No config / setup / exit / assignments / decisions.json / ledger / backlog change.

## Plain-language summary
- **All three records are one-day records.** The quoted "t 6.6" counts every trade as independent, but trades on the
  same day move together. Counted by day, none of the three can be told apart from zero.
  - **G05** (GEN-261022-05 PM Upper-Wick Short, Testing B): 223 trades, +0.49R LIVE-L. One day (11-20) made **+131.7R,
    more than the whole total** (best-day share 121%). Without that day: −0.19R per trade. Day t 0.0.
  - **G07** (GEN-261026-07 PM Upper-Band Fade, Testing A): 238 trades, +0.42R. **11-20 made +96.1R of +99.1R (97%).**
    Without it: +0.02R; without the best two days: −0.01R. Day t 0.9.
  - **G37** (GEN-261023-07 Lunch Choppy RSI Turn Buy, Testing A): 139 trades, +0.45R. **11-25 made +92.0R of +62.4R
    (147%).** Without it: −0.33R. Day t −0.4.
- **Costs are not the story.** These setups trade liquid names around $100 (median entry $101-111; only 1-5% under $20).
  LIVE-L and LR8 agree within about 0.04R. The setups are not cheap names that LR8 over-charges, and they are not names
  that LIVE-L penalises.
- **History does not agree.** Replayed over 2½ years with LIVE-L costs and the live rules, all three are flat to negative
  on CHECK. All three are negative on T2, the only window the generator never saw: G05 −0.07R, G07 −0.20R, G37 −0.15R per
  trade. Their rare big days are big market days (G37: +695R on 2025-04-09, the tariff-pause rally).
- **What they really are:** a bet on the market's direction for the rest of the afternoon, spread across 30-100 stocks at
  once. In history, day R tracks SPY's move after the entry window opens (correlation 0.37-0.46). They win big when SPY
  moves 0.5% or more their way and lose steadily on every other day.
- **Primary:** none of the 12 book configs passes.
  - Added to Primary, each one lowers the book: −0.09 to −1.03 R/day on CHECK and T2, BASE and LO alike.
  - Used as a replacement for L3 / RW3 / RW5, the only gain comes from removing the short. The candidate's own lots lose
    money in every one of the 36 replacement rows: replacement minus plain removal is −0.06 to −1.04 R/day.
- **Salvage (optimism):** the live signal is a day-type signal, not a stock-picking edge.
  - The idea worth keeping is "extreme breadth plus an afternoon trend", traded as **one** index position instead of
    30-100 single-name lots.
  - That carries the same market bet at a small fraction of the cost and without the burst risk.
  - Backlog idea only: it was not tested here, and nothing in this study passes.

## Part A: live audit (journals of all 10 accounts, identical signals counted once; as_live.py, as_brake.py)
LIVE-L R = from the decision-bar close (signal ref_price) to the engine exit, minus the LIVE-L cost (primshorts_1126).
The engine exit is the stop price for untrailed stops, the target, or the exit fill.
| | G05 | G07 | G37 |
|---|---|---|---|
| Accounts (trades) | Testing B 163, Gen 60 | Testing A 163, Gen 75 | Testing A 119, Gen 20 |
| Live window | 10-30..11-20 | 10-30..11-20 | 10-23..11-27 |
| Active / traded days | 25 / 7 | 23 / 8 | 24 / 11 |
| Avg R: LR8 / fill / **LIVE-L** | +0.445 / +0.472 / **+0.488** | +0.416 / +0.453 / **+0.417** | +0.460 / +0.501 / **+0.449** |
| Day t (per-day mean) / trade-clustered t | 0.01 / 1.18 | 0.87 / 1.44 | −0.36 / 0.77 |
| Green days | 57% | 63% | 45% |
| Best day (R) / share of total | 11-20 +131.7 / **121%** | 11-20 +96.1 / **97%** | 11-25 +92.0 / **147%** |
| Avg w/o best 1 / 2 days | **−0.187 / −0.362** | +0.019 / **−0.013** | **−0.326 / −0.363** |
| Shrunk estimate (C3-BAR2) | +0.25 | +0.22 | +0.16 |
| Non-overlap with Primary (n, avg, w/o best) | 216, +0.49, −0.20 | 232, +0.42, +0.02 | 138, +0.45, −0.34 |
| Share under $20; median price | 5%; $101 | 3%; $107 | 1%; $111 |
| Spread at signal median / p90 (bp) | 10.9 / 24.3 | 7.1 / 17.9 | 7.5 / 17.3 |
| Entry slip vs decision bar (R) | 0.064 | 0.074 | 0.042 |
| LR8 cost / LIVE-L cost (R) | 0.026 / 0.088 | 0.037 / 0.111 | 0.042 / 0.118 |
| Median lot notional | $498 | $762 | $439 |
| Top skips | halted 114, opposite side held 48, max positions 41, spread 27, **not ETB 26** | halted 77, cost filter 47, **not ETB 32**, max positions 26 | cost filter 55, **burst brake 37**, spread 22, buying power 22 |
- **Exits:** the profit sits in 15:55 flattens on the big day (G05: 175 flattens averaging +0.84R vs 48 stops at −0.78R).
- **Bursts:** G05 opened **69 lots in 10 minutes** on 11-20 (Testing B).
  - Under BRAKE-BURST (ledger, from 11-23: at most 30 entries per setup per rolling 10 minutes), G05's record would be
    184 trades at +0.30R. It is still a `1 day` record (141%), day t −0.02.
  - G37's 11-25 was already braked (37 burst-brake skips). G07 is unchanged.
- **Fill realism:** spreads and slippage are normal for $100 names. Lots are small (~$500 notional against
  ADV20 ≥ $95-150M), so size is no concern at testing size. Shorts lost 26-32 signals to ETB; the history replay
  applies the ETB ≥ 90% screen.
- **PRIME-RULES entry / C3-BAR2, per candidate (LIVE-L):**
  | Bar | G05 | G07 | G37 |
  |---|---|---|---|
  | ≥ 30 trades / ≥ 8 traded sessions | pass / **fail (7)** | pass / pass (8) | pass / pass (11) |
  | ≥ 15 active days | pass (25) | pass (23) | pass (24) |
  | ≥ 20 sessions (PRIME-RULES) | **fail (7 traded)** | **fail (8)** | **fail (11)** |
  | avg w/o best day > 0 | **fail** | pass (+0.019) | **fail** |
  | best-day share < 40% (PRIME) / < 50% (C3) | **fail (121%)** | **fail (97%)** | **fail (147%)** |
  | green days ≥ 50% | pass | pass | **fail (45%)** |
  | shrunk estimate > 0 | pass | pass | pass |
  | non-overlap avg w/o best day > 0 | **fail** | pass | **fail** |
  | Primary-book replay (FP-C) | **fail** (Part C) | **fail** | **fail** |
- **Rule changes inside the live window (10-23..11-27, ledger):**
  - 10-27 GX1 5-minute clock gate; 10-28 sizing; 10-29 −2R latch (Primary) and the Testing cost filter 0.15.
  - 11-12 LR8 / LR3 cost basis.
  - **11-15/16 ROT1 moved them Gen → Testing A / B**, so each record spans two accounts. Their Gen part was negative
    (G05 −0.58R, G07 −0.01R, G37 −0.14R); the Testing part holds the big day.
  - 11-17 TSZ1 (testing risk 0.25% → 0.125%; R comparable, $ not).
  - 11-19 U9-TGT, U9-ETB, C3-ROT / ROT2 family caps, Epoch 1.
  - 11-20 stop rounding and FOOTRACE-EXIT.
  - **11-23 BRAKE-BURST.**
  - 11-27 ROT3 rotation block 3.
  - G05 and G07 have had no trades since 11-20: their condition (weak breadth in the afternoon) has not come up on a
    session they played since.

## Part B: history replay at the live config (as_gen.py, as_hist.py; home testing book, LIVE-L)
Avg R per trade [LR8]; t = day-clustered; control = 500 size-matched random entries (same side / window / ADV / geometry).
| Setup | FIT | CHECK | T2 (unseen by GEN) | Control CHECK / T2 (mean, p95) | Pre-reg bars |
|---|---|---|---|---|---|
| G05 | +0.003 [+0.043], 953 tr, t 0.02 | +0.013 [+0.058], 1,590 tr, t 0.15, w/o best −0.036, best share 355% | **−0.072** [−0.033], 911 tr, t −1.16 | −0.072, −0.043 / −0.043, −0.002 | fail (CHECK t, w/o best, share; T2 all) |
| G07 | −0.097 [−0.046], 1,379 tr, t −1.34 | **−0.025** [+0.026], 2,133 tr, t −0.37 | **−0.198** [−0.144], 1,808 tr, t −3.70 | +0.003, +0.028 / −0.193, −0.168 | fail (all) |
| G37 | +0.347 [+0.413], 1,683 tr, t 0.86, best share 119% (2025-04-09 +695R) | **−0.110** [−0.047], 2,384 tr, t −1.07 | **−0.152** [−0.078], 1,996 tr, t −2.39 | +0.041, +0.072 / +0.033, +0.067 | fail (all) |
- **G05 on CHECK beats its random control** (100th percentile; random PM shorts lose −0.07R), so its filter does pick
  better shorts than random. That is the one salvageable signal. But the edge rests on a few days (2025-04-08 +118R,
  2025-10-10 +75R, 2025-12-12 +48R; worst day 2025-04-10 −119R) and does not carry to T2 (10th percentile there).
- **Regime (SPY open→close ±0.3%, T1):**
  - G05 and G07 make money only on down sessions (CHECK +0.11 / +0.04R) and lose on flat ones (−0.30 / −0.23R).
  - G37 makes money only on up sessions (+0.14R) and loses on flat (−0.54R) and down (−0.92R) ones.
- **Post-hoc descriptive (as_mech.py, not a config):** day R correlates with SPY's signed move from the window open to
  15:55 at 0.37 / 0.46 / 0.42. On days SPY moved ≥ 0.5% their way: +155R / +185R / +547R. On all other days: −199R /
  −597R / −1,111R (CHECK + T2).
- **T2 breadth** was computed here from the T2 1-minute cache (t2ctx.py; 469 names, a different universe from live).
  Checked against the lab context on 2025-10 with a 150-name sample (t2ctx_check.py): correlation 0.98, and the two
  agree on which side of the thresholds a bar falls 95-97% of the time.

## Part C: Primary book (E5 = E4 with a 5th slot; P4 lineup; LIVE-L; as_build.py, as_book.py)
- **Parity:** the bench lots match rwout_1127 exactly (52,544 P4 lots). Keep R/day is BASE −3.03 / −1.75 and LO −2.05 /
  −1.53 (CHECK / T2), the same as rwout and primshorts.
- **Lots and rules:** the candidates' lots enter at the lowest priority on same-minute ties, under Primary's caps
  (30 per setup, 77 slots, −2R latch, burst brake).

dR/day vs keep (paired t). ADD control = 100 random adds of the same lot count per day.
| Config | BASE CHECK | BASE T2 | LO CHECK | LO T2 | Control (BASE CHECK / T2 mean) | Bar |
|---|---|---|---|---|---|---|
| ADD-G05 | −0.09 (−0.3) | −0.27 (−1.8) | −0.14 (−0.6) | −0.20 (−1.8) | −0.19 / −0.10 | fail |
| ADD-G07 | −0.39 (−1.4) | −1.03 (−3.9) | −0.18 (−0.9) | −0.64 (−3.9) | −0.11 / −0.32 | fail |
| ADD-G37 | −0.70 (−1.7) | −0.52 (−1.8) | −0.43 (−1.2) | −0.55 (−2.3) | −0.16 / +0.08 | fail |

REP-X-G: dR vs keep (t) / **dR vs X-out (t)**, i.e. what the candidate adds beyond removing X.
| Config | BASE CHECK | BASE T2 | LO CHECK | LO T2 |
|---|---|---|---|---|
| REP-L3-G05 | +0.89 (2.0) / **−0.06 (−0.2)** | +0.12 (0.6) / **−0.27 (−1.8)** | +0.63 (2.0) / **−0.13** | +0.17 (1.1) / **−0.20** |
| REP-RW3-G05 | +0.86 (2.3) / **−0.09** | +0.27 (1.6) / **−0.30 (−1.9)** | +0.61 (2.1) / **−0.14** | +0.31 (2.3) / **−0.20** |
| REP-RW5-G05 | +0.83 (2.1) / **−0.08** | +0.48 (2.7) / **−0.30 (−1.9)** | +0.34 (1.2) / **−0.15** | +0.44 (3.1) / **−0.20** |
| REP-L3-G07 | +0.59 (1.4) / **−0.37** | −0.65 (−2.2) / **−1.04 (−3.9)** | +0.58 (1.9) / **−0.18** | −0.27 / **−0.64 (−3.9)** |
| REP-RW3-G07 | +0.55 (1.6) / **−0.40** | −0.47 / **−1.03** | +0.57 (2.0) / **−0.18** | −0.13 / **−0.64** |
| REP-RW5-G07 | +0.51 (1.4) / **−0.40** | −0.27 / **−1.04** | +0.31 (1.1) / **−0.18** | −0.00 / **−0.64** |
| REP-L3-G37 | +0.25 (0.5) / **−0.70** | −0.14 / **−0.53** | +0.28 (0.7) / **−0.48** | −0.18 / **−0.55 (−2.3)** |
| REP-RW3-G37 | +0.16 (0.3) / **−0.78** | +0.02 / **−0.54** | +0.25 (0.5) / **−0.50** | −0.04 / **−0.55** |
| REP-RW5-G37 | +0.12 (0.2) / **−0.79** | +0.23 (0.7) / **−0.54** | −0.02 / **−0.51** | +0.08 / **−0.55** |
- **Per-setup effect (remedy view):** adding a candidate barely moves the other four Primary setups (spill
  −0.02 to +0.01 R/day). Every loss is the candidate's own: its in-book R/day is negative in all 24 CHECK/T2 × context
  rows (G05 −0.07 to −0.30, G07 −0.18 to −1.05, G37 −0.43 to −0.79).
- **What the replacements show:** each replacement's positive "dR vs keep" is the removal effect rwout_1127 already
  measured (X-out +0.36 to +0.95 R/day). The candidate subtracts from that in every row. Removing a short and adding
  nothing is always better than putting one of these three in its place.
- **FIT agrees:** ADD-G07 −0.86 / −0.74; ADD-G05 +0.04 / +0.03; ADD-G37 +0.54 / +0.60. The G37 FIT result is the
  2025-04-09 day (t 0.4).

## Verdict and finalists
**FAIL.**
- All three candidates fail Part A (one-day records; day t ≤ 0.9), Part B (negative on T2 after costs, t −1.2 / −3.7 /
  −2.4) and Part C (0 of 12 configs; every candidate loses R in Primary's book).
- **Finalists (all reported): G05, G07, G37. None passes.**
- They do not serve PRIM-ADD2 or the diversification goal.
- Under the agreed arena rules they stay where they are. Their reps are met (≥ 15 active days and ≥ 30 trades), but
  FOOTRACE-EXIT does not fire because their avg R is positive.
- The leaderboard avg R for each reflects 1-2 days and should carry the `1 day` tag in every review: best-day share
  121% / 97% / 147%; avg w/o best day −0.19 / +0.02 / −0.33.

## Backlog proposal (idea only; nothing passed here)
`{"id": "arenastars-1127-breadth-index", "title": "Day-type index bet: extreme breadth + afternoon trend traded as ONE index position (SPY/QQQ) instead of 30-100 single-name lots", "mechanism": "G05/G07/G37 live and history P/L is the market's afternoon move (corr 0.37-0.46 with SPY's move from the window open; +887R on days SPY moved >= 0.5% their way, -1,907R on the rest); one index lot carries the same bet at a fraction of the cost and without burst risk", "source": "research/arenastars_1127/REPORT.md", "test": "pre-register: breadth_open < 0.35 / breadth < 0.3 at 13:00 (short) and breadth > 0.7 at 11:30 (long), one SPY position to 15:55, LIVE-L costs, CHECK + T2, random-time control, one-big-day check; expect it to fail unless a further afternoon-trend condition adds direction", "status": "idea"}`

Scripts: t2ctx.py, t2ctx_check.py, as_gen.py, as_live.py, as_brake.py, as_hist.py, as_mech.py, as_build.py, e5nb.py,
as_book.py. Outputs: live_audit.json, live_trades.csv, live_brake.json, hist_results.json / .csv, book_results.csv,
book_summary.json, *_out.txt logs. Big lot files stay in scratch (not committed).

Educational only — not financial advice.
