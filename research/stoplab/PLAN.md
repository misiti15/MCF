# stoplab: is -2R the right per-setup daily stop, and the right stop width per setup? (pre-registration)

*Educational only — not financial advice.* Written 2026-11-10 after `trades.csv.gz` was built (counts only) and
**before any stop level or width was scored**. Results go in `NOTES.md`; this file is not changed afterwards (an
amendment, if any, is appended below with its time and the reason, before the affected result is read).
Research only: nothing in config/, mcf/, setups, exits, docs/live or the ledger is changed here.

## Question (owner 2026-11-09)
"Is -2R the perfect daily stop? Maybe -1.6 / -1.75 / -1.8 / -2.01 / -2.25 is better, and maybe some setups need a
tighter or looser stop." Run on ALL setups, all live sessions. Two separate stops are in scope:
1. the **per-setup daily stop** (Primary `account.max_setup_daily_loss_r: 2.0`, latched, from 2026-10-29; off in
   Testing 1/2, Gen, Explore 1, Live Lab; on at -2R in the Graveyard since it opened 10-21; on in T1/T2/Gen 10-19..10-22);
2. the **per-trade stop width** (each setup's own stop distance).

## Data
- **Live (paper, rule 7):** `trades.csv.gz`, built by `build_trades.py` from `origin/<b>:journal.db` of all 7 accounts
  (mcf-data, -testing, -testing2, -gen, -graveyard, -explore1, -livelab), 2026-10-06..2026-11-09.
  - `whatif == False`: run 1 live trades, R = pnl_adj / (|entry - stop| x shares) (costs + stop-slippage allowance in).
  - `whatif == True`: run 2 what-if trades of signals skipped ONLY because of a daily stop: `blocked_latch`
    (why = "setup daily loss limit") or `blocked_halt` (why = "halted" / "daily loss limit", the account stop).
    R = runner what-if r_multiple (backtest costs). Other skip reasons (ETB, spread, lot cap, ...) are not included:
    they would be skipped at any stop level.
  - `setups.csv`: per (account, setup) live counts, what-if counts, config entry, lab module. `lab_modules.csv`.
- **Bars for re-walks:** 1-min `/home/user/MCF/data/cache_hist/1Min` (to 2026-11-04, 1,226 symbols; covers ~69% of
  the rows incl. what-ifs) and 5-min lab frames `/home/user/MCF/research/history2y/data/frames` (to 2026-11-04).
  These live in the main checkout, not in this worktree: scripts use `ROOT = /home/user/MCF` for data.
- **2-year lab history (setups with lab modules):** the gates1021 signal cache (as `research/bdi/top5_1109/build_cache.py`)
  + the top5_1028 exit simulator (stop x k, same $ risk, target price unchanged, R divided by k), with the top5 parity
  gate (parent simulated R = cached production R, mean |d| < 0.002R). For grid A on 2 years, the latch_1103 trade
  lists with exit times (`/home/user/MCF/research/history2y/data/bt_lab1104/sig_*.parquet`, 92 traded setups covered)
  are reused. **Locked block 2024-11-01..2025-02-28 never read** (`MCF_HIST_ALLOW_LOCKED` unset and asserted).

## Units and the replay
- Unit = (account, setup, date). The daily stop is per account; levels are simulated per setup-day independently.
- "Off" sequence per setup-day = live trades + `blocked_latch` what-ifs (the trades the latch prevented). Account-halt
  what-ifs (`blocked_halt`) are **excluded in the primary run** (a per-setup level does not lift an account halt) and
  included in a sensitivity run.
- A trade is blocked under level L if the setup's realised R from trades that EXITED at or before its entry minute
  ever reached <= -L that day (latched, as the live runner since 10-23). Blocked trades contribute nothing.
- Baseline per account = the rule that was live: Primary -2.0R from 10-29 (off before), Graveyard -2.0R, others off.
  Every level is also compared with "off".
- **Excess-delta control (from latch_1103):** delta minus (blocked trades x the setup's own average R on the choose
  split). A level only counts as a timing edge if the excess delta is also positive; otherwise it is reported as
  "saves because the setup loses", which is a setup-expectancy question, not a stop-level answer.

## Splits
- Per setup (pooled across accounts by setup name): its live session dates sorted; first ceil(60%) = CHOOSE, rest =
  VALIDATE. Setups with < 5 live sessions take the global choice and are reported as "too few sessions to choose".
- Global levels are scored on the union of the per-setup splits (each setup-day keeps its setup's label).
- 2-year lab: TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD (2026-04..06, 2026-09-16 onward) not read
  unless a candidate passes everything else (then scored once).

## Grids (every row counts toward N)
**(A) Per-setup daily stop level**, L in {off, -1.0, -1.25, -1.5, -1.6, -1.75, -1.8, -2.0, -2.01, -2.25, -2.5,
-3.0, -4.0} (12 levels vs off):
- A1 realised R (live rule) — global level: 12.
- A2 realised + open (marked) R at the entry minute, marked on 1-min closes (only setup-days whose open trades all
  have bars, i.e. dates <= 11-04 and covered symbols; reported with its own coverage) — global level: 12.
- A3 per-setup choice: each setup's best A1 level on CHOOSE, applied on VALIDATE (1 rule; per-setup N = 12).
- A4 per-setup choice by family (MF, RW, NS, ST, CWT, L3, GEN, other; latch_1103 classifier) on CHOOSE (1 rule).
- A5 day give-back stop: no new entries once realised R falls G below the day's peak realised R (peak floored at 0),
  G in {1.5, 2.0, 2.5, 3.0}: 4.
- A6 sensitivity (not counted as candidates): A1 with halt what-ifs included; A1 on 2-year lab lists (TRAIN/VALID).
- Note: -2.0 vs -2.01 differ only when realised R lands in (-2.01, -2.0]; both are kept because the owner named them.

**(B) Per-trade stop width**, k in {0.75, 0.9, 1.0, 1.1, 1.25, 1.5} x the setup's own stop distance (5 vs 1.0),
same dollar risk (shares / k), target price unchanged:
- B1 live re-walk on 1-min bars (entry = live fill, stop/target from the journal, flatten 15:55; scale-out lots
  excluded). Parity gate first: k = 1.0 must reproduce the live exit reason for >= 90% of rows and mean |dR| < 0.05R;
  rows that fail parity are dropped and counted. 5.
- B2 live approximation from mfe_r / mae_r only, k < 1 (stopped if mae_r <= -k, else R / k; ordering unknown so a
  bound, not a score) — diagnostic, not counted.
- B3 2-year lab re-walk (top5 harness), setups with lab modules and a t/s geometry (not hold / holdtr / S, which the
  harness does not cover): 5.

**(C) Stop variants** (per trade; live re-walk B1 rows, then 2-year lab where covered):
- C1 time-in-trade stop: exit at T in {15, 30, 60, 90} min if best R so far < b, b in {0, +0.25}: 8.
- C2 give-back stop: once MFE >= m (m in {0.5, 1.0} R), exit if price gives back to {break-even, 50% of MFE}: 4.

**N (study-wide):** A 24 + 2 + 4 = 30; B 10; C 12 x 2 sources = 24 → **N = 64**, bar = max(1.5, sqrt(2 ln 64)) =
**2.88**. Per-setup choice (A3) bar = max(1.5, sqrt(2 ln 12)) = 2.23 per setup, study-wide 2.88 reported too.

## Pass bars (all required for a candidate; everything is reported either way)
1. VALIDATE delta R vs the live baseline > 0, and CHOOSE delta > 0 (same sign).
2. Day-clustered t of the VALIDATE delta (sum of delta per date, t over dates) >= 2.88 (A3: >= 2.23 per setup).
3. Plateau: both grid neighbours also have VALIDATE delta > 0 (and the level is not the only positive one).
4. Excess delta > 0 (A grids): the gain is from timing, not from trading a losing setup less.
5. One-big-day: delta without its best day still > 0; best day's share of delta reported, flagged at >= 50%.
6. Remedies table: per affected setup / family, how many improve, how many worsen and by how much (sum and worst).
7. Costs in everywhere (live pnl_adj; what-if and lab: production costs incl. time-of-day entry multiplier, +2c stops).
8. Rule-change context printed with every figure (below).

## Rule changes inside the live window (research/ledger.jsonl)
Per-setup daily stop on in T1/T2/Gen 10-19/20 (non-latching), LL-LATCH (latched) 10-23, ST-A off in T1/T2/Gen 10-23,
Graveyard -2R since 10-21, ST-P Primary -2R latched 10-29; live scale-out fixes 10-16 / 10-20 (SO1); Primary size
~$5k 10-28 then ~$4k; BAR90 10-29; CF cost filter T1/T2 10-30; R2A cap exemption 11-03; ROLL1 Explore 1 / Live Lab
11-05; EXPO1109 temporary GEN moves 11-09; many setup moves 10-20..11-09. The what-if replay gives every level the same
trade sequence, so these changes move the sample, not the comparison.

## Known caveats (fixed before scoring)
- Short live window (25 sessions max; most setups far fewer) — the 2-year lab is the main evidence for B/C.
- What-if R uses backtest costs, live R uses pnl_adj; the live runner latches on journal r_multiple, not pnl_adj.
- What-ifs of latch-blocked signals ignore whether the trade would have been skipped for another reason (already in
  symbol, lot cap) had earlier trades been taken — second order.
- Graveyard has had the latch on since day 1: its "off" sequence relies heavily on what-ifs (4,466 rows).
- 1,240 live rows have null mfe_r / mae_r (reconciled fills); B2 skips them.
- Days after 2026-11-04 have no bars yet: A2 / B1 / C cover 10-06..11-04 only.
