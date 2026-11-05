# REGX — do the setups' market-condition ratings hold? (owner 2026-11-05) — PRE-REGISTRATION

*Educational only — not financial advice.* Research only: no config, setup, exit or dashboard change. Written and
committed **before any cell is scored**. Locked block 2024-11-01..2025-02-28 is never read (trade lists and bars of
those dates are dropped on load; rolling medians simply skip those days).

## Question
The dashboard's "Best conditions" column (`docs/live/regimes.json`, regime1022) gives each setup a best / worst
condition (Bull / Bear / Choppy / Quiet) from its full 2-year backtest. Does a setup's best / worst condition, measured
in-sample, hold out-of-sample (VALID 2-year) and live — and does the answer depend on how "condition" is defined?

## Data
- **2-year**: `research/history2y/data/bt_lab1104/sig_*.parquet` (production R after costs, uncapped chains, stop first,
  15:55 flatten). **TRAIN** = 2024-10 + 2025-03-01..2025-12-31; **VALID** = 2026-01-01..2026-10-05. Days 2026-10-06..
  11-04 of the lists are not used (they overlap live).
- **Live (paper)**: journals run_id 1 of mcf-data, -testing, -testing2, -graveyard, -gen, -explore1, -livelab,
  2026-10-06..2026-11-05, closed trades, R = pnl_adj / (|entry − stop| × shares).
- **Market data**: SIP 1-minute bars in `data/cache_hist/1Min` (to 11-04) + a scratch fetch of 11-05 (`fetch1105.py`).
- **Setups in scope**: every live setup with ≥ 30 closed live trades across all accounts (incl. Graveyard). Those with
  a 2-year list get the full test; those without are reported live-only and can only be **weak** (in-sample only).

## Schemes (cells) — all point-in-time at the entry minute *m* unless marked hindsight
State at entry = last 1-minute SPY bar that started before *m* (fully closed).
| id | scheme | cells | known when |
|---|---|---|---|
| DASH | dashboard scheme (regime1022): SPY open-to-close ≥ +0.5% Bull, ≤ −0.5% Bear, else Choppy if day high-low ≥ prior-20-session median, else Quiet | Bull / Bear / Choppy / Quiet | **hindsight** (close) |
| OC25 | SPY open-to-close ≥ +0.25% up, ≤ −0.25% down, else quiet | up / down / quiet | **hindsight** (close) |
| VWAP | SPY last close vs its session VWAP at entry | above / below | entry |
| COMP | GATE1 compass reading at the latest 30-min checkpoint ≤ entry (10:00..14:00, gate1/compass.py votes; universe breadth_open as in gate1) collapsed to up (UP-confirmed + leaning up) / mixed / down | up / mixed / down; entries < 10:00 = no reading (not ranked) | entry (≥ 10:00) |
| DAYT | first-hour day type: a = SPY from open at 10:00, b = at 10:30. trend-up/-down: sign(a) = sign(b), \|b\| ≥ 0.25%, \|b\| ≥ 0.67\|a\|; reversal: \|a\| ≥ 0.15% and (sign(b) ≠ sign(a) or \|b\| < 0.33\|a\|); else range | trend-up / trend-down / reversal / range; entries < 10:30 = not ranked | 10:30 |
| VOL | SPY high-low since the open (to the last closed bar) / open, divided by the median of the same at the same minute over the prior 20 sessions | low < 0.75 / normal / high > 1.33 | entry |
| BRD | breadth: share of the day's top-500 lab names (by prior-day 20-day dollar ADV) whose last closed 1-min close is above its session VWAP, at the latest 5-min boundary ≤ entry | strong ≥ 0.60 / mixed / weak ≤ 0.40 | entry (≥ 09:35) |
| SECT | sector leadership: mean from-open of XLK, XLY, XLC minus mean of XLP, XLU, XLV at entry | offense ≥ +0.20% / neutral / defense ≤ −0.20% | entry |

(A per-symbol "own sector vs SPY" scheme was considered but the repo has no symbol→sector map; not run.)

## Rating and tests (fixed in advance)
- **Cell eligibility**: TRAIN cell ranked only with n ≥ 30 and ≥ 10 days; a setup × scheme is rated only with ≥ 2 ranked
  cells. VALID cell counts with n ≥ 30 and ≥ 5 days; live cell with n ≥ 10 and ≥ 3 days.
- **Rating** = TRAIN best cell (highest avg R) and worst cell (lowest).
- **Spread** = avg R(best) − avg R(worst). SE by day-cluster bootstrap (1,000 resamples of days, seed 1105); t = spread / SE.
- Per window: spread, t, Spearman rank correlation of cell averages vs TRAIN (schemes with ≥ 3 eligible cells), each
  cell's avg R without its best day and that day's share of the cell's total R.
- **Verdict per setup × scheme**
  - **trustworthy**: TRAIN t ≥ 2.0; VALID spread > 0 with t ≥ 1.0; VALID spread still > 0 with each cell's best day
    removed; and live not contradicting (if both live cells eligible, live spread > 0).
  - **false**: VALID spread ≤ 0 (rating flips out of sample), or live spread < 0 with live t ≤ −1.0 while VALID t < 1.0.
  - **weak**: everything else (TRAIN t < 2 but holds, not significant on VALID, carried by one day, cells too thin on
    VALID, live disagrees mildly, or no 2-year list = in-sample only).
- **Flip between schemes**: map directional cells to + (Bull, up, above, COMP up, trend-up, strong, offense) and −
  (Bear, down, below, COMP down, trend-down, weak, defense). A setup "flips" if its TRAIN best cell is + in at least one
  directional scheme and − in another (among its rated schemes).
- **Dashboard check**: the live dashboard labels (regimes.json, fit on the full 2-year incl. VALID) are scored on live
  only: does live avg R(best label) > live avg R(worst label)?
- **Stability per scheme** (overall and per family × side): share trustworthy / false, median VALID Spearman, share of
  VALID and live spreads > 0. Most stable = highest share of VALID spreads > 0, tie-break median Spearman.
- **Multiple testing**: every setup × scheme rating counts as one configuration (reported). At p ≈ 0.16 (t ≥ 1.0) about
  16% of null ratings would pass VALID by chance; the TRAIN t ≥ 2 filter plus VALID is the guard.
- **Special look**: MF4-h40-open-flowsell-FD and MF2-open-rsimidhi-flowsell-FD on 11-04 and 11-05 — their cell under
  each scheme on those days and what TRAIN / VALID said about that cell.

## Rule changes in the live window (owner rule 2026-11-02)
Listed in NOTES.md from `research/ledger.jsonl` effective dates 10-06..11-05.
