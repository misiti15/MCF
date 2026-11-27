Educational only — not financial advice

# L3REFIRE-1127: an L3-only limit on repeat lots in the same name (Primary). Research only. **LEAD (FIRST1), no pass**

## Plain-language summary
- **The question.** Gap-Down Recovery Fade (`L3-gap-slope-fromopen-FD`, "L3") often shorts the same stock 2–3 times. On 11-27 it shorted PANW three times, and all three lots were stopped together. Would a limit on these repeat lots make Primary better?
- **The test.** 7 rules, pre-registered before any scoring. They were tested on two years of history (CHECK and T2) and on L3's 19 live Primary sessions, with costs in.
- **The answer.** No rule passes. The best rule, **FIRST1** (one L3 entry per name per day), is a **LEAD** by the pre-registered rule:
  - It improves the history book by **+0.44 R/day on CHECK** (t 1.83, needed 3.0) and **+0.21 R/day on T2** (t 2.06).
  - It does not pick better trades. Cutting every L3 lot to the same smaller total size gives more: +0.56 / +0.25 R/day.
  - On history, first lots are no better than repeat lots under today's rules: −0.111 vs −0.103 R per lot on CHECK, −0.118 vs −0.118 on T2.
  - Live, FIRST1 is +8.9R over 19 sessions (t 0.44). One day carries more than all of that gain; without it the change is −0.17 R/session.
- **No decision card.** Only a pass gets one. "Fewer L3 repeats" acts as a size cut on a setup that loses on the bench. The L3-OUT card already covers that more directly: removing L3 entirely gives +0.95 R/day on CHECK.
- **What could still be salvaged:** with LATCH-OPEN on, repeat lots are clearly worse than first lots on history (CHECK −0.126 vs −0.100; T2 −0.161 vs −0.097). That interaction is the next thing to test (see the end).

## Setup
- **Pre-registration:** PREREG.md (sha256 e775dc75…7054), committed in c9bdaab4c4 before any score.
- **Configs: 7** (OPEN1, OPEN2, GAP30, GAP60, GAP120, NOSTOP, FIRST1), all reported below.
  - Cumulative N ≈ 9,176 + tonight's wave 4 so far (DAYTYPE 24, GAPNEWS 18, PAIRS 28) + 7 ≈ **9,253**.
  - Lineage bar sqrt(2 ln N) ≈ 4.27, for reference.
  - Per-study bar: paired day t ≥ 3.0 on CHECK and ≥ 2.0 on T2, and above the random-skip 95th percentile.
- **Engine: E4-L3** (`e4l3.py`). It is cfprimary's `e4nb.py` copied line by line, with one added L3-only entry check.
  - With the rule off it matches e4nb exactly on all 861 sessions (max diff 0.000R, same lots), in BASE and in LO.
- **Bench:** bench10 P4 lots, rebuilt with the hedgeb_1126 build. `build_fast.py` is that build with a faster day index and the same output.
  - 52,544 candidates, the same count as cfprimary / rwout; 0 missing paths.
  - Costs: LIVE-L on shorts, LR8 on NM-ETF.
  - Keep CHECK −3.03 R/day (BASE) / −2.05 (LO), matching rwout and cfprimary.
  - Sessions: CHECK 276, T2 415, FIT 170.
  - **The locked block 2024-11-01..2025-02-28 is filtered and asserted absent in every script.**
- **Prior results flagged (rule 26, STOP2 item 1):**
  - W7 STACK1 (one open lot per symbol across all setups) cost L3 −15.0R.
  - sat1024 G1 (one lot per symbol, Primary-wide) failed.
  - This study is L3-only and within one setup, run at the consultant's request.

## Bench: dR/day vs keep (paired day t; percentile among 500 size-matched random L3 skips)
Each cell lists: dR (t, random pct). "cut" = constant cut: L3 lots scaled to the config's L3 lot count, which is the exposure-matched control.

| Config | BASE CHECK | BASE T2 | LO CHECK | LO T2 | L3 lots/session lost (BASE C / T2) | Best-day share (BASE C / T2) | Verdict |
|---|---|---|---|---|---|---|---|
| OPEN1 (≤ 1 open/name) | +0.21 (1.0, 66th; cut +0.37) | +0.11 (1.5, 95th; cut +0.17) | +0.24 (1.7, 71st; cut +0.23) | +0.12 (1.7, 96th; cut +0.13) | 4.8 / 1.7 | 18% / 22% | FAIL |
| OPEN2 (≤ 2 open/name) | +0.21 (2.0, 84th; cut +0.13) | +0.06 (1.5, 95th; cut +0.08) | +0.10 (1.4, 74th; cut +0.07) | +0.08 (2.4, 98th; cut +0.06) | 1.9 / 0.7 | 18% / 20% | FAIL |
| GAP30 | +0.11 (0.5, 40th; cut +0.21) | +0.01 (0.1, 69th; cut +0.10) | +0.04 (0.3, 12th; cut +0.17) | +0.03 (0.5, 44th; cut +0.09) | 5.5 / 1.9 | 62% / 164% | FAIL |
| GAP60 | +0.29 (1.2, 84th; cut +0.37) | +0.08 (0.8, 83rd; cut +0.17) | +0.24 (1.4, 53rd; cut +0.27) | +0.13 (1.8, 95th; cut +0.14) | 6.2 / 2.2 | 16% / 36% | FAIL |
| GAP120 | +0.39 (1.7, 97th; cut +0.49) | +0.15 (1.5, 95th; cut +0.22) | +0.28 (1.7, 61st; cut +0.34) | +0.16 (2.0, 98th; cut +0.19) | 6.5 / 2.3 | 12% / 18% | FAIL |
| NOSTOP (no re-entry after an L3 stop) | +0.30 (1.4, 93rd; cut +0.07) | +0.09 (1.2, 98th; cut +0.07) | +0.06 (0.4, 48th; cut +0.09) | +0.08 (1.1, 97th; cut +0.06) | 2.2 / 0.9 | 36% / 33% | FAIL |
| **FIRST1 (1 entry/name/day)** | **+0.44 (1.8, 99th; cut +0.56)** | **+0.21 (2.1, 99.6th; cut +0.25)** | +0.34 (2.1, 73rd; cut +0.40) | +0.21 (2.6, 100th; cut +0.22) | 6.7 / 2.4 | 10% / 13% | **LEAD** |

- **Why FIRST1 is a LEAD and not a PASS.** It meets every bar except bar 2 on CHECK: t 1.83 (BASE) and 2.13 (LO), against 3.0, and in LO it is only at the 73rd percentile of random skips. T2 meets bar 2 in both contexts (t 2.06 / 2.55, 99.6th / 100th percentile). FIT agrees: +0.25 / +0.29 R/day.
- **It is a size cut, and a slightly worse one than cutting evenly (the RWOUT lesson).**
  - The random skips refill freed caps with other L3 lots. Random draws kept 2,389 L3 lots on BASE CHECK, against FIRST1's 1,227, so beating the random control mostly reflects lower exposure.
  - Against the exposure-matched constant cut, FIRST1 is behind in every cell: BASE CHECK +0.44 vs +0.56, T2 +0.21 vs +0.25; LO CHECK +0.34 vs +0.40, T2 +0.21 vs +0.22.
  - GAP30, GAP60 and GAP120 trail their cut in every cell, and OPEN1 in 3 of 4. OPEN2 and NOSTOP beat their (small) cut in 3 of 4 cells, by at most +0.23 R/day (NOSTOP, BASE CHECK); both are far from the t bar (t ≤ 2.4).
  - L3's own avg R per lot does not improve: BASE CHECK −0.106 → −0.115, T2 −0.118 → −0.150. The lots that replace the skipped repeats (other names, later in the day) are no better.
- **Bench, first lot vs repeat lot** (keep run, `bench_first_vs_repeat.json`):

  | Context | Period | First lots (n, avg R) | Repeat lots (n, avg R) |
  |---|---|---|---|
  | BASE | CHECK | 868, −0.111 | 1,828, −0.103 |
  | BASE | T2 | 409, −0.118 | 987, −0.118 |
  | LO | CHECK | 690, −0.100 | 1,210, −0.126 |
  | LO | T2 | 351, −0.097 | 756, −0.161 |

  Under today's rules (BASE), repeats are not worse. Under LATCH-OPEN they are.
- **Rule-30 checks** (bespoke entry rules; CHECK + T2):
  - FIRST1 keeps 43% (BASE) / 47% (LO) of L3 lots and 33% / 40% of L3's top-decile winners. The rule needs ≥ 70% and ≥ 90%: **both fail**.
  - NOSTOP and OPEN2 come closest: 87–89% of lots, 84–89% of winners.
  - Plateau: the GAP30 → 60 → 120 → ∞ effect rises steadily with the gap (BASE CHECK +0.11 / +0.29 / +0.39 / +0.44), which is the signature of a size cut.

### Per-setup effect (dR per month, 21 sessions; L3 / RW3 / RW5 / NM-ETF)
| Config | BASE CHECK | BASE T2 | LO CHECK | LO T2 |
|---|---|---|---|---|
| OPEN1 | +6.0 / −0.5 / −1.0 / −0.0 | +2.4 / 0 / 0 / 0 | +5.7 / −0.4 / −0.5 / +0.1 | +2.5 / 0 / 0 / 0 |
| OPEN2 | +4.2 / +0.2 / −0.0 / +0.0 | +1.2 / 0 / 0 / +0.1 | +2.3 / −0.2 / 0 / 0 | +1.7 / 0 / 0 / 0 |
| GAP30 | +2.8 / +0.1 / −0.6 / +0.1 | +0.1 / 0 / 0 / +0.1 | +1.6 / −0.4 / −0.5 / +0.1 | +0.7 / 0 / 0 / 0 |
| GAP60 | +7.8 / −0.6 / −1.1 / 0 | +1.6 / 0 / 0 / 0 | +5.9 / −0.4 / −0.5 / −0.1 | +2.7 / 0 / 0 / 0 |
| GAP120 | +10.0 / −0.8 / −1.0 / +0.1 | +3.2 / 0 / 0 / 0 | +6.9 / −0.4 / −0.5 / −0.2 | +3.3 / 0 / 0 / 0 |
| NOSTOP | +6.1 / +0.1 / +0.3 / −0.1 | +1.9 / 0 / 0 / 0 | +2.0 / −0.4 / −0.5 / 0 | +1.8 / 0 / 0 / 0 |
| FIRST1 | +11.0 / −0.8 / −1.0 / +0.1 | +4.4 / 0 / 0 / 0 | +7.9 / −0.4 / −0.5 / −0.0 | +4.4 / 0 / 0 / 0 |

- Only L3 changes materially.
- RW3 and RW5 lose up to −1.1 R/month on CHECK. The bar is −2: when L3 trades less, the account halt fires later, so the RW shorts keep trading on bad days.
- The worst-5 days improve with almost every rule. Red days per month barely move (13.1 → 12.6 for FIRST1 BASE CHECK).

### Interaction with LATCH-OPEN and L3-OUT (docs/live/decisions.json, both open)
- **LATCH-OPEN:** every rule gains less with LO on CHECK. FIRST1 goes from +0.44 to +0.34, and its random percentile drops from 99th to 73rd. So LO already does part of the same job (stopping L3 piling in on a bad day). The two overlap; they are not additive.
- **L3-OUT:** FIRST1 captures 47% (BASE CHECK) to 56% (LO T2) of L3-OUT's dR (L3-OUT: +0.95 / +0.40 BASE; +0.77 / +0.38 LO).
  - On the bench, L3-OUT dominates every cap. If L3-OUT is chosen, these rules are moot.
  - If L3 stays on probation, an even size cut does slightly better than FIRST1.

## Live replay (19 Primary L3 sessions 10-21..11-27; LR8; all Primary lots; current rules re-applied every day; drops only)
- **Journal:** 884 lots, −89.45R. L3: 238 lots, −11.0R LR8.
- **Keep under today's rules:** −78.3R (BASE), −24.9R (LO).
- **Consultant split reproduced:**
  - First L3 lots: 111, +0.010R each.
  - Repeat L3 lots: 127, −0.096R each (−12.1R; −22.6R without the best day).
  - Since 11-19: first lots −0.78 R/lot (31), repeats −0.73 R/lot (32).
  - The consultant's 131 / −0.113R differs slightly (cost basis / counting); the direction is the same.

| Config | BASE dR/session (t; random pct) | BASE: L3 lots removed (their R) | Best-day share / dR w/o best | 11-27 | LO dR/session (t; random pct) |
|---|---|---|---|---|---|
| OPEN1 | +0.45 (0.45; 84th) | 99 (−10.9R) | 139% / −0.19 | +3.23 | −0.22 (−0.28; 45th) |
| OPEN2 | +0.15 (0.40; 72nd) | 34 (−2.8R) | 93% / +0.01 | +1.64 | −0.14 (−0.43; 53rd) |
| GAP30 | +0.59 (0.74; 94th) | 85 (−16.6R) | 88% / +0.08 | +2.67 | +0.24 (0.36; 77th) |
| GAP60 | +0.40 (0.40; 80th) | 108 (−11.9R) | 145% / −0.19 | +3.23 | +0.56 (0.47; 84th) |
| GAP120 | +0.47 (0.44; 88th) | 115 (−12.3R) | 135% / −0.17 | +3.23 | +0.66 (0.58; 86th) |
| NOSTOP | +0.00 (0.00; 47th) | 17 (−0.0R) | n/a / −0.18 | 0.00 | +0.02 (0.06; 66th) |
| FIRST1 | +0.47 (0.44; 88th) | 115 (−12.3R) | 135% / −0.17 | +3.23 | +0.68 (0.60; 87th) |

- **Per setup, live BASE:** L3 +8.5R under FIRST1 / GAP120. Through the latch and halt, RW3 +0.9 and RW5 −0.5. No other setup changed. In LO only L3 changes.
- **L3's own live record under FIRST1 (BASE):** 109 lots, +0.014 R/lot. Without its best day it is −0.294 R/lot, and the best day carries more than 100% of L3's total.
- **Reading:** every live effect is noise (|t| ≤ 0.74). Each positive one is carried by one day (best-day share 88–145%). Without that day, most are ≤ 0.
  - 11-27 (PANW) is the day the rules were designed for: +2.7 to +3.2R.
  - The replay cannot refill skipped signals, and it cannot let in signals that the latch blocked in reality.

## Verdict
- **LEAD** (FIRST1), by the pre-registered rule: bars 1, 3, 4 and 5 hold everywhere; bar 2 holds on T2 in both contexts but not on CHECK; the live replay is not dR < 0 with t ≤ −2.
- All other configs **FAIL**.
- FIRST1 carries three caveats:
  - It is a size cut that trails an even constant cut in every cell (−0.01 to −0.12 R/day).
  - It fails rule 30: it keeps 43–47% of L3 lots.
  - Live, it is a `1 day` record.
- **No decision-card proposal for the 12-04 epoch** (a card is written only on a PASS). For the open cards:
  - **L3-OUT card:** a one-entry-per-name rule recovers only about half of L3-OUT's bench gain, and does it by cutting size. It is not a selective fix that would let L3 stay at full strength.
  - **LATCH-OPEN card:** LO overlaps with these rules (FIRST1's CHECK gain falls from +0.44 to +0.34 with LO on).

## Next step (optimistic salvage, not counted here)
- With LATCH-OPEN on, repeat L3 lots are worse than first lots on both splits: −0.126 vs −0.100 (CHECK), −0.161 vs −0.097 (T2). With today's realised latch they are not.
- If LATCH-OPEN is adopted, a single pre-registered config could test it: "L3 repeat lot only while the name's open L3 lot is in profit". It would be scored against the exposure-matched constant cut, not only the refill random control.
- Alternatively, add a journal-only `l3_repeat` tag (TAGS1 path, rule 30) to collect clean forward data.
- This is a note for backlog `nightly-1015-l3-fromopen-refire-cap`; the backlog was not edited here.

## Rule-change context (research/ledger.jsonl, effective dates inside the live window 10-21..11-27)
- **L3 membership:** 10-20/21 L3 promoted to Primary; 10-22 demoted; 10-30 re-promoted.
- **Size and loss limits:**
  - 10-28 Primary size ~$4k: 77 slots, 30 lots per setup.
  - 10-29 −2R per-setup latch (ST-P).
  - 11-12 LR3 (latch and halt count after-cost R, the halt counts open marks) and LR8 costs.
- **Lineup:**
  - 11-11 TEAM-6 (NM-ETF in; MF2/MF4-FD and others out over 11-11..16).
  - 11-16 TEAM-6 open-ended, with L3's cap staying at 30.
  - 11-19 C3-NS5 / Epoch 1, DQ-P4 fill marks, TAGS1 (including a journal-only STACK1+L3x tag).
  - 11-23 ST7 out of Primary, BRAKE-BURST, PSHADOW.
- **Other:** 11-20 stop rounding; 11-27 changes affect testing / Graveyard only.
- **Next:** 11-30 AV50 (NM-ETF only).
- The live replay applies today's latch and halt on every day, so the early-window lots (before 10-29, with no latch) are re-ruled. Bench rules are fixed.

## Files
- **Scripts:** `e4l3.py` (engine), `l3run.py` (bench), `l3live.py` (live replay), `l3desc.py` (first vs repeat), `build_fast.py` (bench build).
- **Outputs:** `results.csv` (every config × context × period: dR, t, random p95 / percentile, selection value, constant cut `cut_dR`, L3-OUT dR, per-setup dR / month, lots, worst-5, red days); `summary.json` (parity, rule-30 checks, verdicts); `live_replay.csv` / `.json`; `bench_first_vs_repeat.json`; `run_out.txt`.
- **Scratch:** the journal copy was used in a scratch directory and deleted.

Educational only — not financial advice
