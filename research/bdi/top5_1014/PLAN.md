# top5_1014 pre-declaration: small one-knob variations of the 5 most-traded live setups

*Educational only - not financial advice.*

Written 2026-10-14 after the live ranking (`live_top5.py`, live paper trades only) and **before any history
configuration below was scored**. The results go in `NOTES.md` and may not change this file. If anything is added
after scoring starts it is appended below a dated line and counted.

## 1. Which setups (step 1, live, rule 7: paper)
Ranked by real trades (run_id 1) on 2026-10-08, 09, 12, 13, 14 across Primary (`origin/mcf-data`), Testing 1
(`origin/mcf-data-testing`) and Testing 2 (`origin/mcf-data-testing2`) journals; S6 excluded; a "-FD" copy is its own
setup (`live_rank.csv`, 2,428 trades in all).

| rank | setup | account | live n | parent definition |
|---|---|---|---|---|
| 1 | CWT14-failbrk-orl-p05-long | T2 | 191 | `research/bdi/cwt/live/CWT14-failbrk-orl-p05-long.py`: `cwt_live_lib.b3(level=OR, p=0.05, lowvol=False, long)`, t05s1, window [950,1500], min_adv 95M (CWT package B id 154) |
| 2 | CWT14-failbrk-orl-p05-lowvol-long | T2 | 190 | same with lowvol=True (poke bar volumeRatio < 1) (id 166) |
| 3 | heat_fade_short-FD | T1 | 156 | `research/bdi/fullday/heat_fade_short-FD.py`: regime_9 heat score <= -11.3, gate fo-, k_cost 8, type heat, short, t1s1, window [950,1500], min_adv 125M |
| 4 | CWT14-failbrk-pdl-p05-long | T2 | 132 | `b3(level=PD, p=0.05, lowvol=False, long)`, t05s1, [950,1500], 95M (id 106) |
| 5 | RW7-gapdn-bounce-early-short-FD | T1 | 126 | `research/bdi/fullday/RW7-gapdn-bounce-early-short-FD.py`: heat <= -20, buyPressure < -0.15, 55 <= RSI14 <= 65, gap < 0; short t1s1, [950,1500], 95M |

## 2. Data, costs, splits
- research/history2y frames via `lib.load_month` (open months only). The rule-19 locked block 2024-11-01..2025-02-28
  is **never loaded** (the loader refuses it; `MCF_HIST_ALLOW_LOCKED` is never set).
- CWT14 runs on frames plus the 09:35-09:45 head rows (`refire1014/scan.head_rows`, as the parity-verified scans
  did). Heat and RW7 run on the plain frames.
- Live semantics: one trade per symbol-day = the FIRST bar inside the window where the (variant) mask is true; an
  added filter is part of the mask (the first bar passing the filter fires).
- Costs: production R with time-of-day entry costs (`gates.prod_r(..., tod=)`): 1c + 1 bps per side, exit free on
  targets, +2c on stops, entry side x1.4 for bars before 10:30 (`gates.TOD_COST`).
- **Splits (by date):** TRAIN = open sessions <= 2025-12-31 (2024-10, 2025-03..2025-12). VALID = 2026-01-01..2026-03-31
  and 2026-07-01..2026-09-15. **HOLD** = the rule-2 holdouts Apr-Jun 2026 and 2026-09-16..2026-10-07: not used for
  selection; scored once, only for variants that meet the Testing bar on TRAIN+VALID. The parent's full open-history
  numbers are reported only as the "backtest" reference against live.
- **Same-minute random control (rule 6):** mean production R of every universe bar with adv20 >= the variant's
  min_adv at the same date and tod, same side and geometry. Excess = R - control.
- Regimes: `lib.regimes()` (open-history terciles); walk-forward `gates.walk_forward` over TRAIN+VALID months.
- Re-entry/refire is **not** in this grid: `research/bdi/refire1014` scored refire cd1/cd3/cd6 for every live lab
  setup tonight (including these four lab setups), so repeating it would double-count.
- Already tested tonight and **not repeated**: CWT14 stop-and-reverse (bdi1014 B, B2), CWT14 skip-first-bar
  (nightly1014), CWT14 index confirm (nightly1012, 800 configs), LIQ index filters. No index/SPY filter is used here.

## 3. Grid (one knob per variant; every row counts)
**CWT14 (each of the 3 parents; 14 + 16 + 14 = 44)**
| id | knob | value |
|---|---|---|
| V01 / V02 | poke depth p | 0.04 / 0.06 ATR (-20% / +20%) |
| V03 / V04 | reclaim within | 2 / 4 bars (parent 3) |
| V05 | window | [1030, 1500] |
| V06 | window | [950, 1300] |
| V07 / V08 | exit geometry | t1s1 / t1s05 (parent t05s1) |
| V09 / V10 | VWAP | signal bar close above / below session VWAP |
| V11 / V12 | RSI(14) at the signal bar | < 40 / >= 40 |
| V13 | extra filter | fromOpen > -1.0% |
| V14 | extra filter | gap > 0 |
| V15 / V16 (lowvol parent only) | poke-bar volumeRatio | < 0.8 / < 1.2 (parent < 1.0) |

**heat_fade_short-FD (15)**
| id | knob | value |
|---|---|---|
| H01 / H02 / H03 | SHORT_AT | -10.2 / -12.4 / -13.6 (-10% looser, +10%, +20% stricter) |
| H04 / H05 / H06 | window | [1030,1500] / [1130,1500] / [950,1400] |
| H07 / H08 | geometry | t05s1 / t1s05 (parent t1s1) |
| H09 / H10 | VWAP | above / below session VWAP |
| H11 | RSI(14) | >= 50 |
| H12 | RSI(5) | >= 70 |
| H13 | fromOpen | <= -0.5% |
| H14 / H15 | min_adv | 100M / 150M (-20% / +20%) |

**RW7-gapdn-bounce-early-short-FD (16)**
| id | knob | value |
|---|---|---|
| R01 / R02 | heat | <= -16 / <= -24 |
| R03 / R04 | buyPressure | < -0.12 / < -0.18 |
| R05 / R06 | RSI band | 53-67 / 57-63 |
| R07 | gap | < -1% |
| R08 / R09 / R10 | window | [1030,1500] / [1130,1500] / [950,1400] |
| R11 / R12 | geometry | t05s1 / t1s05 |
| R13 / R14 | VWAP | above / below |
| R15 / R16 | min_adv | 114M / 76M (+-20%) |

**N (this study) = 44 + 15 + 16 = 75.** Study bar sqrt(2 ln 75) = 2.94. Parents are re-scored too (5 reference
runs, not configurations).

## 4. Bars (fixed now)
- **Beats parent:** exp(variant) - exp(parent) > 0 on TRAIN and on VALID, and the improvement's t on TRAIN+VALID
  (day-block bootstrap, 1,000 resamples of sessions, seed 20261014) >= max(1.5, sqrt(2 ln N_setup)) with N_setup the
  setup's grid size (14 -> 2.30, 15 -> 2.33, 16 -> 2.35). Every beater goes to the backlog (tag `top5-tune`), with its
  status set by the bars below (exp <= 0 -> `failed` with "beats parent" in the notes).
- **Testing bar** (experimental, Testing 1 or 2 by origin), on TRAIN+VALID: beats parent; exp > 0 on TRAIN and on
  VALID; day-clustered t >= max(2.0, study bar 2.94) = 2.94; up and down sessions each exp > 0 (n >= 30); walk-forward
  share >= 0.6; ex-best-day > 0; excess over the same-minute control > 0; plateau: another value of the same knob also
  has exp > 0 on TRAIN+VALID (for one-value knobs V13, V14, H11, H12, H13, R07 the cut-offs at +-50% are scored as the
  plateau check, counted in N, only if needed). A variant meeting it is then scored once on HOLD (exp > 0 required,
  t reported); passing both makes it a proposed Testing addition (named `<parent>-<knob tag>`), never a Primary change.
- **Research / Primary bar:** gates.verdict == keep at the cumulative lineage N: CWT14 cwt-b-b3 121,089 + 44 =
  121,133 (t >= 4.84); heat_fade_short 19,706 + 15 = 19,721 (t >= 4.45); RW7 / bdi-rw-gapdn-bounce-early 82,964 + 16 =
  82,980 (t >= 4.76); plus everything in the Testing bar. A pass there would only make a finalist for the lead's
  single locked-block score.
- Every variant is reported (`results.csv`), failures first.
