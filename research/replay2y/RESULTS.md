# 2-year live-code replay — results (first sample)

*Educational only — not financial advice. Research only: no trading, setup, exit or config change. Method and
deviations: [NOTES.md](NOTES.md); plan: [PLAN.md](PLAN.md); every setup: [per_setup.csv](per_setup.csv); overlap:
[overlap_account.csv](overlap_account.csv), [overlap_setup.csv](overlap_setup.csv); totals: [summary.json](summary.json).
R = per entry lot after LR8 costs on its own fills, replay and live alike. Configurations tried: 1.*

## Answer first

- **The engine does NOT yet reproduce live**, so the 2-year numbers below are screening only (weight 0). Overlap
  (3 live sessions × 10 accounts, as-live setups, no poll logs / recorded quotes, as the 2-year sessions run):
  **79.4% match, 34.8% extra trades, matched-pair bias +0.031R (95% CI +0.019..+0.043, optimistic)**, against the
  pre-registered bar of ≥ 98% / ≤ 2% / ±0.01R. Replay_cal with poll logs got 87.1% / 26.2% / +0.005R.
- **Coverage is a sample:** 60 account-sessions, 7 sessions (2024-10-11, 10-23, 2025-04-30, 05-21, 06-02, 07-15,
  09-16), 5-7 per account, 5,327 replay trades, 185 of 206 setup slots traded. Pooled avg R **−0.096**.
- **SRCV1 caveat stands:** no non-live source has predicted live so far; this one must earn trust via a passing
  overlap check and a later SRC-VALUE re-score.

## 1. Per account (2-year sample, today's config)

| account | setup slots | sessions | trades | avg R (LR8) | setups > 0 |
|---|---|---|---|---|---|
| Primary | 6 | 7 | 292 | −0.237 | 2 |
| Testing 1 | 13 | 5 | 309 | −0.222 | 5 |
| Testing 2 | 25 | 7 | 1,318 | −0.136 | 6 |
| Explore 1 | 25 | 6 | 328 | +0.053 | 12 |
| Live Lab | 25 | 6 | 403 | −0.060 | 10 |
| Testing D | 19 | 6 | 537 | −0.097 | 3 |
| Testing E | 17 | 6 | 294 | +0.515 (one setup, one day: see 4) | 9 |
| Testing F | 24 | 6 | 676 | −0.141 | 9 |
| Gen | 18 | 6 | 491 | −0.173 | 7 |
| Graveyard | 34 | 5 | 679 | −0.155 | 10 |

Testing 1 lacks 2025-05-21 (crash, NOTES) and 2025-09-16 (not run: container restart); Graveyard lacks 05-21 (same
crash). Per-setup trades, sessions, avg R, avg R w/o best day + best-day share, green-day %, per-period avg R and the
live record are in per_setup.csv. **71 of 185 trading setup records carry the `1 day` tag** (best session ≥ 50% of a
positive total): with ≤ 7 sessions most records are one or two big days.

## 2. Overlap check (engine vs live; 2026-11-12, 11-13, 11-17)

| account | live trades | replay trades | match % | extra % | bias R (pairs) | live avg R | replay avg R |
|---|---|---|---|---|---|---|---|
| Primary | 110 | 76 | **54.5** | 14.5 | −0.030 | +0.327 | +0.067 |
| Testing 1 | 330 | 417 | 92.4 | 33.9 | +0.028 | −0.090 | −0.044 |
| Testing 2 | 571 | 743 | 90.7 | 39.4 | +0.036 | −0.082 | −0.062 |
| Explore 1 (1 session) | 7 | 9 | 100 | 28.6 | +0.056 | +0.848 | +0.820 |
| Live Lab | 77 | 103 | 88.3 | 45.5 | +0.028 | −0.037 | +0.014 |
| Testing D | 198 | 255 | 91.9 | 36.9 | +0.043 | −0.078 | −0.039 |
| Testing E | 193 | 231 | 86.5 | 33.2 | +0.059 | −0.241 | −0.156 |
| Testing F | 302 | 327 | 87.7 | 20.5 | +0.029 | −0.102 | −0.087 |
| Gen | 839 | 1,026 | 87.6 | 34.7 | +0.025 | −0.078 | −0.076 |
| Graveyard | 2,031 | 2,132 | **68.6** | 36.4 | +0.031 | −0.155 | −0.176 |
| **pooled** | 4,658 | 5,319 | **79.4** | **34.8** | **+0.031** | −0.110 | −0.109 |

Daily R correlation 0.967, sign agreement 89%. Totals look close (−577R replay vs −511R live) only because two errors
offset: matched trades are rosier (+0.031R), the 35% extra trades are worse (−0.136R avg) than the live trades the
replay missed (−0.042R). Per setup (85 with ≥ 10 live trades): median match 88%, median extra 29%; 6 reach ≥ 98%
match, none also ≤ 2% extra. Worst: L3-gap-slope-fromopen-FD (Primary) 15%, CWT14-failbrk-orl-p10-long 31%,
MF1-945-flowsell-vwapup-FD 33%. Largest known cause (replay_cal): no recorded quotes (spread skips) and, here, no poll
logs. **Verdict: fails; 2-year replay numbers stay screening only.**

## 3. Versus the old 2-year screen and 2-year backtest (setups with ≥ 20 replay trades)

| source | setups | sign agrees with replay | source mean | replay mean | Spearman |
|---|---|---|---|---|---|
| 2-year screen (docs/live/sim_inputs.json) | 30 | 47% | +0.054 | −0.017 | −0.09 |
| 2-year backtest (research/history2y/rescore.csv; 14 exact + base-setup matches) | 17 | 82% | −0.030 | −0.284 | +0.26 |
| live record (≥ 20 live trades) | 61 | 61% | −0.163 | −0.152 | −0.15 |

- **Screen:** optimistic as SRCV1 found; the replay disagrees on sign for half. Biggest gaps: GEN-261029-08 (screen
  +0.02 / replay −0.70), GEN-261029-01 (+0.24 / −0.32, 132 trades), GEN-261019-04 (+0.07 / −0.45); the other way
  GEN-261020-07 (+0.03 / +1.19, one day), GEN-261019-05 (+0.10 / +0.60, one day).
- **Backtest:** agrees on sign (mostly negative) but the replay is far more negative (−0.28 vs −0.03): the backtest
  had first-qualifying-bar entries, R = 0.25 × ATR and a 1,226-name survivor universe; the replay has the live
  sizing, stops, caps and full point-in-time universe. Largest: RW5-…-FD (Primary) −0.47 vs −0.01, MF5 −0.49 vs −0.05,
  NS2 −0.41 vs +0.01, exhaustion_short-FD −0.39 vs −0.01.

## 4. Replay vs live record — supports / contradicts (≥ 30 replay and ≥ 20 live trades: 49 setups)

- **Supports (same sign, 31 of 49) — almost all on the negative side (30):** GEN-261029-08 (replay −0.70 / live
  −0.40, 169 live), NS2-sma50break-overbought-short (−0.41 / −0.35), MF4-h40-open-flowsell-FD (−0.44 / −0.30),
  CWT05-flush-m075-v3-long (−0.75 / −0.25), MF5-…-FD (−0.44 / −0.24), RW3S-gapdn-flowsell-short-FD (−0.39 / −0.23),
  MF3-open-flowsell-rsi5hi-FD (−0.32 / −0.20). Only positive pair: RW7-gapdn-bounce-early-short-FD (Testing F;
  +0.04 / +0.00, but w/o best day −0.24).
- **Contradicts (18):** replay positive, live negative — GEN-261020-07 (+1.19 / −0.34; 90% one day),
  GEN-261019-05 (+0.60 / −0.58; one day), GEN-261019-07 (+0.20 / −0.44; one day), GEN-261026-10 (+0.33 / −0.26;
  w/o best day −0.20): every one is a `1 day` record. Replay negative, live positive — **RW5-heat30-…-FD (Primary)
  −0.47 / +0.12 over 7 sessions**, L3-gap-slope-lowdist-FD (−0.27 / +0.22), GEN-261019-04 (−0.45 / +0.05).
- **Fast lane (REPS2): no setup meets the pre-set rule** (live < 20, replay ≥ 30 trades, avg R > +0.027, w/o best day
  > 0, best day < 50%, green days ≥ 50%, positive in ≥ 2 periods). Closest low-rep records, both failing the one-day
  test: GEN-261027-01-MACDhge0p12 (Testing E; +0.11 on 31 trades, w/o best day −0.06) and
  GEN-POD1022-01-thrasher (Graveyard; +1.11 on 75 trades, all on one day). Nothing to fast-lane from this sample.

## 5. Remaining storage and the nightly plan

- **Storage:** 296 of 435 2-year sessions stored (through 2026-01; the 14:19 UTC run of 11-18 paused for market hours).
  The 16:40 ET nightly run of 11-18 did **not** appear in the run list, so the chain has stalled; it needs one ops
  dispatch (`store-bars`, start=2026-02, end=2026-02, chain_to=2026-10). Then ~9 chunks × ~45 min off-hours ≈ 7 h:
  **ETA ≈ one night after the dispatch** (139 sessions, ~2.3 GB more).
- **Replay compute:** ~375 replayable sessions (all stored minus 2025-03-03..04-29 and the 2024-09 warm-up) × 10
  accounts × ~800 s ≈ 830 core-hours. Not feasible on one box; feasible on Actions.
- **Nightly job plan (ops/owner step; nothing shipped here):**
  1. Workflow `replay2y`, after `store-bars`, outside 09:30-16:00 ET; matrix of 10 jobs (one per account), each a
     4-core runner with a 5.5 h budget running `python -m mcf.replay run --account A --universe live --live-cal
     research/replay2y/params_2y.json --jobs 4 --dates <next unreplayed sessions>` with `MCF_REPLAY_HIST_PACKS=1`
     (≈ 100 sessions per account per night → full history in ~4 nights, then only new months).
  2. Per session it keeps only trades/signals/stats (≈ 50 KB) in a `replay2y-runs` release asset; packs are pulled
     per session and deleted after use (`check_dates` keeps the locked block and its look-back out).
  3. Then `research/replay2y/analyze.py` refreshes per_setup.csv; the overlap check re-runs on the newest live
     sessions with the same params; a dashboard column stays labelled "2-year replay (screening, weight 0)".
  4. Fix first (owner/backlog): the CWT09 `a7_stop` empty-slice crash (kills whole sessions), the Explore 1 as-live
     crash, and record quotes / use poll logs so the overlap gap can close; re-score SRC-VALUE once ≥ 10 fresh live
     sessions exist after the replay snapshot.

## Rule-change context

The replay applies one fixed config (commit 8a9a0cb6c) to every 2-year session, so no rule change falls inside it.
The live records it is compared with (10-06..11-17) span LR8 costs from 11-12 (neutralised: LR8 on every trade), the
Primary −2R latch in cost R from 11-12, Testing A full universe from 11-12, new accounts (Explore 1 / Live Lab from
11-05, Testing D/E/F from 11-12) and the setup moves in research/ledger.jsonl.
