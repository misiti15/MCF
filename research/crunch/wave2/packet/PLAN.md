Educational only — not financial advice

# Wave 2 "packet" — Friday review packet (W2 rerun) + Primary red-day account-R decomposition — pre-registered plan

Written 2026-11-19 after the close, **before any scoring**. Research and proposals only: no config, runtime, ledger,
assignments or setup change; no final decision without the owner. Locked block 2024-11-01..2025-02-28 never read (live
journals start 2026-10-06; 2-year bars not used here).

## Data
- Live journals, `run_id = 1`, all ten accounts (`origin/mcf-data*` at the 11-19 close: Primary, On Deck (`testing`),
  Testing A (`testing2`), B (`explore1`), C (`livelab`), D, E, F, Setup Generator, Graveyard), 2026-10-06..**2026-11-19** (11-20 is tomorrow; not in).
- **R on the LR8 basis**: `mcf.costs.cost_r_lr8` (DQ-P3, merged 11-19): pre-11-12 rows re-costed with LR8, rows from
  11-12 keep booked pnl_adj. **LR8 dollars** = R_lr8 × |entry − stop| × shares (booked pnl_adj where risk is 0).
- Identical signals across accounts (setup | symbol | date | entry minute) counted once in pooled setup records.
- **Account R (UNIT1)** = LR8 $ ÷ (0.25% × equity). Primary per day: prior-session equity close
  (`docs/live/equity_history.json` to 11-05; afterwards reconstructed back from Primary's 11-19 `last_equity` 84,883.40
  with booked journal $). Per setup in other accounts: the account's 11-19 `last_equity` (display only; TSZ1 halved
  testing lots from 11-17, so testing account R is not comparable with Primary's — stated next to the table).
- **Active days** = sessions on which the setup is `enabled` in that account's `setups/<date>.json` snapshot (benched /
  archived sessions excluded). Cross-checked against `docs/live/arena_reps.json` (to 11-18).
- Universe: every setup in `docs/live/assignments.json` (asof_session 2026-11-20, which already lists the 11-20 admissions;
  setups with 0 live trades are counted and listed by name only).
- Epoch 1 vs BASE1: Primary journal **run 3** (shadow), setups `BASE1:<name>` vs the same-run shadow of the live book
  (`of_live`); live run 1 shown beside it. Epoch 1 has one session (11-19).

## Columns per setup (every live setup)
n, traded sessions, active days, total trade R, avg R (LR8), avg R w/o best day, best-day share (`1 day` at ≥ 50%),
green-day %, last-5 R, day-clustered t (`mcf.report.footrace.day_t`), try-count bar max(1.5, √(2 ln N)), N = setups
scored (lineage counts are not recorded per setup, so the pool N is used and said so), shrunk estimate
n/(n+150)·avg + 150/(n+150)·(−0.10), non-overlap avg R w/o best day, account R (UNIT1), $ (LR8), verdict.

## Rule sets scored (configurations counted: 7; no tuning)
1. **C3-BAR2 promotion, plan view** (On Deck + arena; non-overlap vs Primary members' trades in Primary). W2 thresholds
   verbatim. A **CSCV PBO line** (S = 8, 70 splits, setups ≥ 20 trades) for the ranking BAR2 uses (shrunk estimate),
   with total R and raw avg R shown as reference — part of this rule set, not a separate selection.
2. **C3-BAR2 strict view** (`nx_`: non-overlap vs Primary members' trades in any account).
3. **Primary −10R demotion** since admission (C3-BAR2).
4. **FOOTRACE-EXIT** (effective 11-20, replaces EXIT100 in Testing A-F + Gen): `mcf.report.footrace.exit_review`
   logic (≥ 15 active days, ≥ 30 trades, avg ≤ 0, w/o best ≤ 0, day t ≤ −1.5; rare < 0.5 signals/active day,
   11-20 admissions and young WB copies exempt).
5. **GY-LIFE graduation** (W2 definition: ≥ 15 Graveyard traded days, ≥ 30 Graveyard trades, whole record w/o best day
   > 0, best-day share < 50%).
6. **Epoch 1 vs BASE1** (descriptive): per-session paired difference (live-book shadow − BASE1 shadow), also with the
   live run; no verdict (1 session; the C3-EPOCH verdict needs a paired difference beyond ~2 SE).
7. **UNIT1 red-day decomposition of Primary** (descriptive): for every Primary session 10-06..11-19 — trade R vs account
   R (LR8), sign agreement; on red days (trade R < 0 or account R < 0): R and account R per setup, and per lot-size
   bucket (risk $ per lot: < $25, $25-75, $75-150, ≥ $150); "decider" = the smallest set of setups (largest |account
   R| first) whose sum carries the day's account-R sign; count of trade-R red days that were account-R green and the
   reverse; which lot buckets drive the disagreement. Primary sizing changed 10-28 (≈$5k → ≈$4k), so pre/post 10-28
   are shown separately.

## Honesty
- Every setup scored lands in `scores.csv` (gzip-free, small). Fit/check halves on each candidate. Rule changes inside
  the window listed from `research/ledger.jsonl`, including 11-19 (Epoch 1, NS5 out, EXIT100 20 moves, GY-ARCHIVE-20,
  DQ-P3/P4, UNIT1, U9-TGT, U9-ETB, ROT2, RT-UNCAL) and the 11-20 items (FOOTRACE-EXIT, GY-FOOTRACE, 9 admissions).
- L3-gap-slope-fromopen-FD protected: scored, no proposal touches it.
- No 11-19 market-hours change is proposed; any Primary item is for the Friday-after-close epoch window only.
