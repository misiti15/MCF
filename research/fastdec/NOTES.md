# FASTDEC — faster promote / keep / demote verdicts, 2026-11-11

*Educational only — not financial advice. Research only: **no config, setup, assignment, ledger or dashboard change** (written
during market hours). All records are live **paper** results (rule 7); R is after costs (`pnl_adj / (|entry − stop| × shares)`).
Backtest numbers are labelled as backtest.*

Owner (11-11): live reps come too slowly; we need verdicts on setups faster.

## Plain English first

1. **Demotion can be called sooner; promotion cannot, yet, with sound statistics.**
   - **Demote:** a Bayesian sequential test on the setup's own session-clustered record (M2a) called its demotions a median of
     **3 sessions before** the setup reached REPS-MIN 8/30. It was earlier than the REPS-MIN bar on 15 of its 21 setups (62
     sessions saved in all). Precision was **76%** (16 of 21 negative over the next 5 sessions; 95% CI 55-89%). The REPS-MIN bar
     scored 79% (62-89%).
   - **The combined engine (M4)** is M2a plus the REPS-MIN demote floor. It called 35 setups at **82% precision (CI 67-92%)**.
     43% of those calls came before 8/30, and next-5 avg R was **−0.184R** per trade (CI −0.239 to −0.141). M4 was built
     after seeing the results (post hoc), so treat it as a hypothesis to confirm on the next sessions.
   - **Promote:** every method made only 2-6 first promote calls in 16 checkpoints. Their precision runs from 50% to 100%,
     with 95% CIs as wide as 9-100%. **Nothing here shows that any method promotes soundly earlier than REPS-MIN.**
2. **Why promotion is slow: the data, not the method.**
   - Per-trade R has an SD of about 0.87R, and same-day trades move together (design effect **3.4** on the 11-10 data).
   - Using only its own record, a setup needs about **4.3 / (true avg R)² trades** before P(avg R > 0) reaches 0.90:

     | true avg R | trades needed |
     |---|---|
     | +0.30R | ~47 |
     | +0.20R | ~106 |
     | +0.10R | ~426 |
     | +0.05R | ~1,700 |

   - **A real +0.05-0.10R edge cannot be confirmed from a few weeks of live reps by any honest method.** Only big edges can.
3. **Borrowing strength did not help on this history.**
   - **Split-half test:** a setup's avg R on odd sessions has *negative* correlation with its avg R on even sessions (−0.24,
     p = 0.03). First half against second half: −0.05. Between-setup spread estimated from the covariance: **0**.
   - **Most of what separates records is a common day × side factor** (longs vs shorts on the day), not the setup. With that
     factor removed, there is a small persistent spread (τ ≈ 0.05-0.08R per trade), which is still not significant.
   - So shrinking toward the family mean (EB) or toward the backtest mostly pulls every setup toward the pool. The pool is
     about −0.13R per trade live (shorts −0.138 ± 0.048, longs −0.117 ± 0.037, equal weight per session).
   - The EB / backtest demotes then land at about the base rate: **60-67% precision, against a 69% base rate** of "negative
     next 5 sessions". They add no information, and they would demote setups whose own record is positive, which the owner's
     fair-chance rule forbids.
   - The backtest prior's lab-to-live gap is **−0.08R (longs) and −0.06R (shorts)** per trade: live is worse than the lab.
     The L3LEASH-2 E90 borrow restriction moves the shorts' gap by only 0.002R on these setups.
4. **Recommended engine: M4.** The posterior P(avg R > 0) comes from the setup's own record, with a weak prior N(0, 0.20²)
   and a session-clustered SE regularised toward the pool while k is small. The status rules:
   - **demote-ready:** P(avg R < −0.05) ≥ 0.90 with own avg R < 0, from 4 traded sessions and 10 trades; **or** REPS-MIN 8/30
     reached with the Graveyard-floor shape.
   - **promote-ready:** P(avg R > 0) ≥ 0.90 with own avg R > 0. It is a *review flag* only: promotion keeps the ROT/ONDECK bars,
     the one-big-day check and the owner's yes.
   - **on-track:** the projection reaches a verdict within 10 sessions.
   - **undecided:** everything else.
   Command: `python -m research.fastdec.engine` (§7).
5. **Today (data to 11-10, 26 sessions):**
   - **1 promote-ready, 28 demote-ready, 4 on-track, 127 undecided** (160 setups with ≥ 5 trades).
   - **Promote-ready:** Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` (Primary, so the action is **keep**).
     285 trades over 19 traded sessions, avg R **+0.170**, P(> 0) = 0.93. **`1 day` record:** its best session (10-20) is 69% of
     total R, and avg R without that day is +0.072.
   - **Demote-ready in the testing accounts (7, review only):** see §5. They include MF4-FD (rule-20 protected to about
     11-25) and RW3S-FD (its Graveyard proposal is already pending).
   - **The other 21 demote-ready setups** are 18 already in the Graveyard and 3 GEN setups (owner's consent needed).

**Failures first:** no method beat the base rate with a CI that excludes it, for either direction. Promote calls are too few to
score. The walk-forward has 16 overlapping checkpoints on one month of one regime. Every number below is a hypothesis to re-check
at about 40 sessions.

## Rule / config changes inside the stats window (owner rule 2026-11-02)
The records run 10-06 → 11-10 (26 live sessions, run_id=1, all 7 accounts merged by setup id). Changes in force inside that
window, from `research/ledger.jsonl` (see research/ondeck_build/PLAN.md for the full list):
- **All accounts:** per-lot stacking (3 lots per symbol) from 10-13; same-setup re-entry from 10-14; twin cap from 10-20/21.
- **Testing 1:** split-tape short gate (from about 10-14); per-setup −2R stop on 10-19/20, off from 10-23.
- **Testing 1 / 2:** CF cost filter 0.15R from 10-30.
- **Testing 2:** UNI1 top-500 universe from 11-04.
- **Explore 1 / Live Lab:** live from 11-05 (ROLL1, about $1,000 lots).
- **Primary:** about $4,000 lots from 10-28; −2R per-setup latch from 10-29; promotions and demotions on 10-20/21, 10-26/27,
  10-28 and 10-30.
- **After the window:** TEAM-6 from 11-11; the account renames (`testing` = On Deck, `testing2` = Testing A, `explore1` =
  Testing B, `livelab` = Testing C) change the labels only.
- So one setup's record mixes sizing, caps, universes and stop rules. The walk-forward's forward windows cross these dates too.

## 1. Data and unit
- **Trades:** closed run_id=1 trades from the 7 journals on the data branches (`git show origin/mcf-data*:journal.db` at
  11-11 09:41 ET), restricted to sessions up to 11-10. That is 18,878 trades and 194 setups, of which **160 have ≥ 5 trades**.
  No broker calls were made.
- **Unit = session:**
  - avg R uses the ratio estimator over session sums;
  - its variance is session-clustered;
  - it is mixed with a pooled value, `(k·V_cl + 4·c/N)/(k+4)`, where c = median(V_cl·N) over setups with k ≥ 8 and N ≥ 30,
    which equals 2.59, or 0.762 per trade × design effect 3.40.
- **Families** (from the id prefix): RW, L3, MF, NS, CWT, ST, NM, LD, LIQ, GEN, CLS (the classic named setups); **side** from the
  trades.

## 2. Methods compared (11 configurations, all reported)
| # | config | what it is |
|---|---|---|
| B1 | REPS-MIN 8/30 balanced bar | ROT balanced Candidate bar for promote (shrunk ≥ +0.03, w/o best > 0, share ≤ 60%, day-t ≥ 0.73, last-5 > −0.15, 2y ≥ −0.10; ex-market R omitted, it is not in the journals); demote = Graveyard-floor shape (shrunk ≤ −0.10, w/o best < 0, last-5 < 0) at 8/30 instead of 40 trades |
| B2 | REPS-MIN 8/30 sign rule | at 8/30: promote if avg R > 0, demote if < −0.05 |
| M1a | EB family × side | prior = leave-one-out family × side mean shrunk to the side mean; τ² by DerSimonian-Laird on the day (floor 0.02²) |
| M1b | M1a + own-sign guard | a call also needs the setup's own avg R on the same side of 0 |
| M1c | EB on day-factor excess + guard | the same-side pool's R that day removed; μ = side pool long-run mean + shrunk excess |
| M1d | M1b + no `1 day` promote | promote blocked when the best day is ≥ 50% of total R |
| M2a | Bayes sequential, weak prior | own record, prior N(0, 0.20²), clustered SE |
| M2b | SPRT | H0 μ = −0.05 vs H1 μ = +0.05, α = β = 0.10, clustered SE |
| M3a | 2y backtest prior | prior = 2y lab mean (bt_lab1104; locked block out; to 10-05, pre-live) + lab-to-live gap per side (DL), spread τ_bt² + SE²; no backtest → M1b |
| M3b | M3a with E90 borrow | shorts' lab restricted to names that were shortable + ETB on ≥ 90% of 23 snapshots (L3LEASH-2 proxy) |
| M4 | M2a + REPS-MIN demote floor | **post hoc** union of M2a and B1's demote rule |

**Shared rules for M1-M4, pre-set and not tuned:**
- the call floor is ≥ 4 traded sessions and ≥ 10 trades;
- promote when P(μ > 0) ≥ 0.90;
- demote when P(μ < −0.05) ≥ 0.90;
- every config except M1a carries the own-sign guard.

## 3. Walk-forward (`study.py` → `out/wf_calls.csv`, `out/wf_summary.csv`, `out/wf_summary.json`)
**Method:**
- 16 checkpoints, after live sessions 6 to 21 (10-13 → 11-03). At each one, a method sees only the trades up to that
  session.
- A call is scored on the setup's next 5 live sessions when it has ≥ 3 forward trades. Promote is correct if forward avg R > 0;
  demote is correct if forward avg R < 0.
- Each setup's **first** call per direction is one unit. CIs are Wilson intervals for precision and a setup bootstrap for
  forward avg R.

**Base rate** over 1,158 scorable setup-checkpoints:
- forward avg R < 0: **68.6%**;
- forward avg R > 0: 31.4%;
- forward avg R < −0.05: 62.2%.

A method is useful only if it beats these rates.

### Demote calls
| config | setups called | precision (95% CI) | false calls | next-5 avg R (CI) | median sessions before 8/30 reached | share called before 8/30 | vs B1's own call (median, n) |
|---|---|---|---|---|---|---|---|
| B1 REPS-MIN balanced | 35 | 0.79 (0.62-0.89) | 7 / 33 | −0.147 (−0.220, −0.089) | 0 | 0% | – |
| B2 REPS-MIN sign | 45 | 0.77 (0.62-0.87) | 10 / 43 | −0.145 (−0.210, −0.093) | 0 | 0% | 0 (35) |
| M1a EB | 64 | 0.63 (0.50-0.74) | 22 / 59 | −0.084 (−0.153, −0.015) | 4 | 88% | 4 (33) |
| M1b EB + guard | 54 | 0.66 (0.52-0.78) | 17 / 50 | −0.105 (−0.160, −0.048) | 4 | 89% | 4 (33) |
| M1c EB excess + guard | 52 | 0.60 (0.46-0.73) | 19 / 48 | −0.099 (−0.162, −0.032) | 2 | 73% | 2 (34) |
| M1d | 54 | 0.66 (0.52-0.78) | 17 / 50 | −0.105 | 4 | 89% | 4 (33) |
| **M2a Bayes sequential** | 21 | **0.76 (0.55-0.89)** | 5 / 21 | **−0.162 (−0.214, −0.112)** | **3** | 71% | **3 (21)** |
| M2b SPRT | 17 | 0.76 (0.53-0.90) | 4 / 17 | −0.155 (−0.210, −0.088) | 3 | 53% | 3 (17) |
| M3a backtest prior | 46 | 0.67 (0.52-0.79) | 15 / 45 | −0.103 (−0.164, −0.041) | 4 | 85% | 4 (33) |
| M3b backtest E90 | 46 | 0.67 (0.52-0.79) | 15 / 45 | −0.103 (−0.164, −0.039) | 4 | 85% | 4 (33) |
| **M4 (post hoc)** | **35** | **0.82 (0.67-0.92)** | 6 / 34 | **−0.184 (−0.239, −0.141)** | 0 | 43% | 0 (35); 15 earlier |

### Promote calls
| config | setups called | precision (95% CI) | false calls | next-5 avg R (CI) | median sessions before 8/30 |
|---|---|---|---|---|---|
| B1 | 4 | 0.50 (0.15-0.85) | 2 | +0.193 (−0.363, +0.657) | 0 |
| B2 | 14 | 0.50 (0.27-0.73) | 7 | +0.045 (−0.131, +0.191) | 0 |
| M1a / M1b | 3 | 0.67 (0.21-0.94) | 1 | +0.164 | 4 |
| M1c | 0 | – | – | – | – |
| M1d | 2 | 0.50 (0.09-0.91) | 1 | +0.155 | −2.5 |
| M2a / M4 | 6 | 0.50 (0.19-0.81) | 3 | +0.134 (−0.172, +0.430) | 2 |
| M2b SPRT | 2 | 1.00 (0.34-1.00) | 0 | +0.392 (+0.198, +0.507) | −0.5 |
| M3a / M3b | 4 | 0.75 (0.30-0.95) | 1 | +0.171 (−0.171, +0.501) | 4 |

- The promote calls are mostly the same few mid-October short-side records: RW3-FD, RW5-FD, MF2-FD, MF3-FD, MF4-FD and
  L3-fromopen.
- RW3-FD was right everywhere. MF3-FD was wrong everywhere: called at k = 4 on 10-15, next-5 −0.243.
- **Counted over the rest of the record, every method's early promotes were below zero, except SPRT (+0.151, 2 setups) and M1d
  (+0.133, 2 setups).**

**Reading:**
- Early demote calls are real: M2a, SPRT and M4 run 0-3 sessions ahead of REPS-MIN at similar precision.
- No method's demote precision has a CI lower bound above the 69% base rate. M4's (0.665) comes closest.
- Pooling methods (EB, backtest) call many more setups early, but at the base rate (60-67%), so they add no information on
  this history.
- Repeated calls (every checkpoint, not just the first) agree:
  - demote 0.69-0.85 (SPRT highest at 0.85, n = 118);
  - promote 0.47-0.67.
- **Multiple testing:** 11 configs × 2 directions. The ranking between M2a, SPRT, B1 and M4 is inside noise. M4 is a post-hoc
  union, so its edge over B1 (+3 points) is not evidence.

## 4. Why borrowing strength failed here (`out/wf_summary.json` → reliability)
| split | setups | Pearson (p) | Spearman | between-setup τ from covariance |
|---|---|---|---|---|
| raw avg R, odd vs even sessions | 81 | **−0.24 (0.03)** | −0.32 | 0 |
| raw avg R, first vs second half | 89 | −0.05 (0.65) | −0.12 | 0 |
| excess R (day × side pool removed), odd vs even | 81 | +0.05 (0.68) | −0.04 | 0.053 |
| excess R, first vs second half | 89 | +0.10 (0.37) | +0.02 | 0.079 |

- Over 26 sessions, raw records do not carry a detectable, persistent "this setup is better" signal. The negative odd/even
  correlation is the long/short market factor: a setup that won on the up days lost on the down days.
- So a family or backtest prior (both centred near the pool, −0.06 to −0.18R) shrinks almost everyone below −0.05, and then
  "demotes the pool".
- **The engine therefore keeps M1/M3 as diagnostic columns** (`--method eb|ebx|bt`), not as the decision rule. Revisit at about
  40 sessions, when τ can be estimated with some precision. If the excess-R spread holds at ~0.08R, M1c becomes the faster
  ranking tool.
- **Backtest prior details:**
  - 83 of the 160 setups have a 2y lab list (own, or the base setup's for an -FD setup without its own).
  - Lab-to-live gap: longs **−0.080R** (τ 0.096, 44 setups); shorts **−0.060R** (τ 0.084, 39 setups); E90 shorts −0.063R.
  - The ETB snapshots run 10-07 → 11-10, so the E90 restriction uses borrow lists from after some checkpoints. That leak is
    small, because E90 moved nothing material.

## 5. Today's verdicts (`out/decisions.json`, method flat + REPS-MIN floor = M4, data to 11-10)
Homes come from `docs/live/assignments.json` on this branch.

**Promote-ready / keep:**
- `L3-gap-slope-fromopen-FD` (Primary → **keep**): 285 trades, 19 traded sessions, avg R +0.170, posterior +0.134,
  P(> 0) = 0.93. Avg R without its best day is +0.072; the best day's share is 69% (**`1 day`**). Primary −2R latch from 10-29.

**Demote-ready in the testing accounts (review only, all owner decisions):**

| setup | home | trades / traded sessions | avg R | P(> 0) | P(< −0.05) | w/o best day | why |
|---|---|---|---|---|---|---|---|
| `RW3S-gapdn-flowsell-short-FD` | Testing A | 204 / 6 | −0.281 | 0.005 | 0.98 | −0.291 | posterior (RW3S-GY already pending) |
| `intraday_momentum` | On Deck | 52 / 20 | −0.352 | 0.008 | 0.97 | −0.381 | posterior |
| `NM-AR-AM-gapdown-capitulation-long` | Testing A | 58 / 9 | −0.460 | 0.024 | 0.94 | −0.598 | posterior |
| `CWT13-vwapstretch-z05-long` | Testing A | 275 / 20 | −0.147 | 0.023 | 0.89 | −0.189 | REPS-MIN floor |
| `MF4-h40-open-flowsell-FD` | On Deck | 158 / 22 | −0.231 | 0.059 | 0.86 | −0.278 | floor; **rule 20: protected to about 11-25** (demoted from Primary 11-11) |
| `MF1-945-flowsell-vwapup` | On Deck | 30 / 13 | −0.360 | 0.154 | 0.76 | −0.438 | floor |
| `NS3-failed-vwap-reclaim-short` | On Deck | 67 / 10 | −0.229 | 0.175 | 0.71 | −0.403 | floor |

- Also demote-ready: 18 setups already in the Graveyard (`stay-graveyard`) and 3 GEN setups (`propose-owner`; no GEN demotion
  without the owner's consent).
- **On-track:** 4 GEN setups, all leaning demote.
- No testing-account setup is on track to promote within 10 sessions at its current rate.

## 6. Forward replay (research/fwdrep) — interface, not yet available
`research/fwdrep` was not on the branch at 11-11 09:45 ET. **Rule 21:** replays never count toward a record or a decision, so
the engine reads forward replay only as a *filter column*, never in the posterior.

**Contract:** `research/fwdrep/out/setup_fwd.csv` with columns:
- `setup`;
- `sessions`, `trades`;
- `avgR` (after costs);
- `se` (session-clustered);
- `audit_pass` (bool, the rule-21 audit: ≥ 95% trade match, |ΔR| ≤ 0.03, never optimistic).

When the file exists, `decisions.json` carries `fwdrep_avgR` for setups whose audit passed. A later step may use it to *order*
which undecided setups get rotation priority. Any use beyond a filter needs the owner's yes.

## 7. Nightly use (designed for the nightly loop and the dashboard; not wired yet)
```
python -m research.fastdec.engine                        # after the close; reads origin/mcf-data* journals via git show
python -m research.fastdec.engine --journals DIR --asof 2026-11-10 --method flat --out DIR
python -m research.fastdec.engine --build-priors         # offline: rebuild priors.csv from the 2y lab cache + ETB snapshots
python -m research.fastdec.study DIR                     # re-run the walk-forward (about 45 s)
```
- **Output:** `research/fastdec/out/decisions.{json,csv}`. The JSON contract is
  `{version, asof, generated, method, params, sessions, pooled, counts, setups: [...]}`.
- **Per setup:** trades, traded_sessions, avgR, se_clustered, post_mean, post_sd, p_avgR_gt_0, p_avgR_lt_m005,
  exp_sessions_to_verdict, lean, status, action, last5_avgR, avgR_wo_best_day, best_day_share, one_day, bt_prior,
  fwdrep_avgR.
- **`exp_sessions_to_verdict`** holds the posterior mean fixed and shrinks the variance at the setup's own traded-session rate.
  It is a projection, not a promise.
- **`action`:**
  - keep / promote-review / demote-review / stay-graveyard / propose-owner / collect;
  - every move stays an owner decision;
  - promotion = move;
  - rule-20 protection and the GEN / Graveyard rules apply.
- **Default `asof`:** the last closed session (today after 16:15 ET, else yesterday). The engine makes no broker calls.

## Configurations tried
**11 decision configs** (B1, B2, M1a-d, M2a-b, M3a-b, M4), every one reported above. The 11 configs × 2 directions are scored
at 16 checkpoints.

**Diagnostics** (not decision configs):
- the split-half reliability (4 splits);
- the arithmetic for trades needed.

**Pre-set parameters, not tuned:** min 4 / 10, thresholds 0.90, demote line −0.05, k0 = 4, prior SD 0.20. M4 was chosen after
seeing the results.

## Files
| file | what |
|---|---|
| `engine.py` | decision engine and nightly CLI |
| `study.py` | walk-forward and reliability |
| `priors.csv` | 2y lab prior per setup: raw and E90, day-clustered SE |
| `out/decisions.{json,csv}` | today's verdicts |
| `out/wf_calls.csv` | every call at every checkpoint |
| `out/wf_summary.{csv,json}` | tables above, base rates, reliability |
| `tests/test_fastdec.py` | synthetic smoke test |

*Paper results. Educational only — not financial advice.*
