# Top-5 setup execution tune, 2026-10-15 (second run of the owner's daily task): FAILED the Testing bar, 0 of 89; 4 beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions (rule 7): a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history (2024-10, 2025-03..2026-10-07), with production
  and time-of-day costs in. The rule-19 locked block (2024-11-01..2025-02-28) was **never loaded**.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 89** (CWT14 3 x 16, heat_fade_short-FD 19, CWT12-coil-k4-long 22), plus 5 parent runs.
- **Passes:** 0 variants have exp > 0. **4 beat their parent** at the pre-declared bar. 0 meet the Testing bar.
  0 meet the research bar. No holdout was scored.
- **No Testing addition is proposed.** No config entry is written. config/ and mcf/ are untouched. Nothing is committed.

Files:
- `live_top5.py`: the ranking and the live stats (`live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`).
- `scan_1015.py`: the history scan.
  - It holds a new 5-minute path simulator that mirrors `mcf/backtest/engine.simulate`, plus a numba coil kernel.
  - `python scan_1015.py parity` checks the simulator against `gates.lab_trades` on 2025-06. All 5 parents matched
    trade for trade (mean |diff| 3-5e-5 R). The coil kernel equals `cwt_live_lib.b4a`.
- `report_1015.py`: writes `results.csv`, `summary.json` and `hist_parent_detail.txt`.
- `add_backlog.py`.

Runtime is about 7 minutes. The scratch trades file was deleted afterwards.

## Failures first

| setup (acct) | variants | exp > 0 | beat parent at bar | improve on TRAIN and VALID | best (d R, t_improve / setup bar / lineage bar) |
|---|---|---|---|---|---|
| CWT14-failbrk-orl-p05-long (T2) | 16 | 0 | 1 | 6 | X06 scale-out: -0.0763 vs -0.0933, **+0.0170R, t 4.30** / 2.35 / 4.84 |
| CWT14-failbrk-orl-p05-lowvol-long (T2) | 16 | 0 | 2 | 6 | X06 scale-out: +0.0157R, **t 3.78**; X12 wait one bar: +0.0096R, **t 2.53** |
| CWT14-failbrk-pdl-p05-long (T2) | 16 | 0 | 1 | 4 | X06 scale-out: -0.0648 vs -0.0865, **+0.0216R, t 5.43** / 2.35 / 4.84 (lineage bar met) |
| heat_fade_short-FD (T1) | 19 | 0 | 0 | 1 | X03 time stop 60 min: +0.0047R, t 1.38 / 2.43 / 4.45 |
| CWT12-coil-k4-long (T2) | 22 | 0 | 0 | 5 | X06 scale-out: +0.0099R, t 1.65 / 2.49 / 3.23 |

**Why nothing reaches Testing.** Every parent is still negative after costs:
- CWT14 runs -0.087 to -0.093R (t -8 to -9), and coil runs -0.073R (t -4.9).
- heat_fade_short-FD runs -0.030R (t -1.8).

The sign is set by the session regime:
- CWT14 and coil longs: up sessions +0.04..+0.07R, down sessions -0.20..-0.23R.
- heat short: up sessions -0.26R, down sessions +0.14R.

The best execution change (X06) narrows that split: CWT14 down sessions move from -0.20 to -0.14R, but up
sessions also fall, from +0.04 to +0.01R. Every variant stays below zero.

**The X06 gain is mostly generic.** The same scale-out also lifts the random same-minute longs. So X06's excess over
the matched random control is slightly *worse* than the parent's (ORL -0.0145 vs -0.0111). It is an exit effect,
not extra information in the setup.

## 1. The five setups, live (5 sessions 10-09, 12, 13, 14, 15; real trades, run 1)
- Ranking (`live_rank.csv`): the CWT14 ORL / ORL-lowvol / PDL setups and heat_fade_short-FD stay in the top 5.
  RW7-gapdn-bounce-early-short-FD drops to 7th (134 trades) and CWT12-coil-k4-long comes in 5th.
- All four repeats were tuned only once (top5_1014), so none of them is due for rotation. Today's grid uses
  **none** of yesterday's knobs.
- Testing 1 and Testing 2 have 4 sessions in this window.

| # | setup | acct | n | win | avg win / avg loss (R) | **break-even win** | avg R | P/L | losers that never reached +0.2R | stop / target / flat |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CWT14-failbrk-orl-p05-long | T2 | 241 | 58.9% | +0.432 / -0.895 | **67.5%** | -0.113 | -$257.18 | 39 of 99 | 80 / 140 / 21 |
| 2 | CWT14-failbrk-orl-p05-lowvol-long | T2 | 230 | 55.7% | +0.405 / -0.989 | **70.9%** | -0.213 | -$312.37 | 29 of 102 | 89 / 127 / 14 |
| 3 | heat_fade_short-FD | T1 | 205 | 38.5% | +0.767 / -0.863 | **53.0%** | -0.235 | -$492.38 | 49 of 126 | 79 / 49 / 77 |
| 4 | CWT14-failbrk-pdl-p05-long | T2 | 176 | 58.0% | +0.505 / -0.955 | **65.4%** | -0.109 | -$185.85 | 29 of 74 | 63 / 100 / 13 |
| 5 | CWT12-coil-k4-long | T2 | 143 | 68.5% | +0.466 / -1.001 | **68.2%** | +0.004 | +$72.05 | 14 of 45 | 38 / 95 / 10 |

**Live against backtest** (parent, TRAIN+VALID, production costs, one trade per symbol-day; `hist_parent_detail.txt`):

| setup | live win / BE win | backtest win / BE win / exp (n, t) | backtest median MFE / MAE (R) | backtest loser give-back (MFE - R) |
|---|---|---|---|---|
| CWT14 ORL | 58.9 / 67.5% | 63.3 / 69.6% / -0.093 (84,333, t -8.8) | 0.53 / -0.50 | 1.22R |
| CWT14 ORL lowvol | 55.7 / 70.9% | 63.6 / 69.7% / -0.091 (59,625, t -8.3) | 0.53 / -0.51 | 1.23R |
| heat_fade_short-FD | 38.5 / 53.0% | 49.3 / 51.2% / -0.030 (58,329, t -1.8) | 0.63 / -0.62 | 1.13R |
| CWT14 PDL | 58.0 / 65.4% | 63.9 / 69.8% / -0.087 (53,326, t -8.5) | 0.54 / -0.50 | 1.23R |
| CWT12 coil | 68.5 / 68.2% | 63.5 / 68.5% / -0.073 (34,840, t -4.9) | 0.53 / -0.48 | 1.20R |

The full-open-history parent n match the earlier studies exactly: 105,023 / 74,014 / 66,875 / 75,136, and coil
44,505 = verify.json.

**Where the losers cluster** (`live_top5_detail.txt`, `hist_parent_detail.txt`)

*CWT14 ORL, both versions*
- Live, 154 of 241 trades (ORL) and 148 of 230 (lowvol) come at 10:00-10:30, at -0.16 and -0.22R.
- Live, every day was negative. Lowvol's worst day was 10-12 at -0.47R.
- 52-54% of history losers never reach +0.2R.

*CWT14 PDL*
- The 09:50 bar is the cluster: 56 live trades at -0.56R.
- 10-14 alone made -40R live. 10-13 and 10-15 were positive.

*heat_fade_short-FD*
- 09:50-11:30 entries: 69 live trades, 7-29% wins, -0.47 to -1.16R.
- 10-15 (gap-down reversal up day): 44 trades, 11% wins, -41R.
- 11:30-13:00 is about flat (+0.035R, n 84).

*CWT12 coil*
- Live is near break-even. 10-12 lost (-3.7R) and 10-15 gained (+4.8R).

**Live winners rarely went far against the trade**, but history does not support a tighter stop:
- Live, winners rarely went below -0.75R (CWT14 6-8 of 102-142 winners, heat 4, coil 6). Losers took the full
  -0.9 to -1.0R.
- On history, 7.9-8.8% of winners pass -0.75R. That is enough that a 0.75R stop cuts as much from the winners as
  it saves on the losers (see X08 below).

## 2. Grid results (all 89 in `results.csv`, with win, avg win/loss, break-even win, margin, never-worked share)

| knob | CWT14 x3 (d exp, R) | coil | heat | what happens to the win/loss shape |
|---|---|---|---|---|
| X01-X03 time stop 15/30/60 min, best < 0.2-0.25R | +0.000..+0.003 | +0.002..+0.006 | +0.004..+0.005 | Avg loss -1.02 -> -0.61R. Win rate also falls, 63 -> 50% (15 min). Roughly a wash; best t 1.38 |
| X04-X05 breakeven at 0.25/0.35R (heat 0.5/0.75R) | -0.007..-0.013 | -0.008..-0.011 | -0.004..-0.009 | Cuts winners: win 63 -> 42% |
| **X06 scale-out half at +0.25R, rest to BE** (heat: half at +0.5R) | **+0.016..+0.022** | +0.010 | +0.000 | Win 63 -> 70%, avg loss -1.02 -> -0.85R. The only consistent gain |
| X07 scale-out half at +0.5R, rest to 1R (heat: half at +0.3R) | -0.002..-0.005 | -0.008 | +0.000 | Bigger winners do not pay for the extra stop-outs |
| X08-X09 stop 0.75 / 0.6R | -0.002..-0.006 | 0.000..+0.001 | -0.005 | Loss -1.02 -> -0.84R, win 63 -> 58% |
| X10-X11 limit entry 0.1 / 0.2R better | **-0.026..-0.038** | -0.020..-0.023 | -0.022..-0.025 | Fills 51-79%; it fills on the trades that keep going against it (as in bdi1013) |
| X12 wait one bar | +0.002..+0.010 | +0.001 | -0.008 | Only lowvol beats its bar (t 2.53) |
| X13 wait one bar + confirm | -0.002..+0.006 | -0.002 | -0.006 | Halves the trade count, no gain |
| X14 flow3 agrees | -0.001..-0.002 | +0.003 | -0.006 | |
| X15-X16 heat exit 15:00 / 14:00 | | | -0.004 / +0.003 | |
| T01-T06 coil thresholds +-20-25% | | -0.016..+0.001 | | Flat plateau |
| O1 opposite for signals before 10:30 (own exp, not a difference) | -0.085..-0.100 | -0.087 | -0.100 | All negative: the early losers are not a reversal signal |
| O2 next-day rebound long after a stop-out (own exp) | -0.083..-0.084 | -0.093 | -0.031 (t -1.1) | |
| O3 heat: reverse long after the stop (own exp) | | | -0.056 | |

## 3. Bars applied (PLAN section 4)

**Beats parent** (TRAIN and VALID both improve, and t_improve >= the setup bar of 2.35-2.49): 4 variants.

| variant | d TRAIN / VALID | t_improve | setup bar | lineage bar | variant exp (t) | up / down |
|---|---|---|---|---|---|---|
| CWT14-failbrk-pdl-p05-long X06 | +0.018 / +0.027 | 5.43 | 2.35 | **4.84 met** | -0.0648 (-9.1) | +0.017 / -0.143 |
| CWT14-failbrk-orl-p05-long X06 | +0.017 / +0.016 | 4.30 | 2.35 | 4.84 not met | -0.0763 (-10.3) | +0.012 / -0.146 |
| CWT14-failbrk-orl-p05-lowvol-long X06 | +0.015 / +0.017 | 3.78 | 2.35 | 4.84 not met | -0.0752 (-9.9) | +0.018 / -0.144 |
| CWT14-failbrk-orl-p05-lowvol-long X12 | +0.010 / +0.009 | 2.53 | 2.35 | 4.84 not met | -0.0813 (-7.4) | +0.052 / -0.180 |

- **Testing bar** (t >= 3.00 and exp > 0, plus every other gate): 0 met it. Every variant is negative, the
  walk-forward share is 0.0-0.3, and the excess over random is <= 0 for CWT14.
- **Research bar** at lineage N: 0 met it.
  - CWT14: N 121,181, t >= 4.84.
  - heat: N 19,740, t >= 4.45.
  - coil: N 184, t >= 3.23.
- The plateau checks were not needed, so N stays 89.

## Backlog (tag `top5-tune`; `research/BACKLOG.md` regenerated, 417 entries)

| id | status |
|---|---|
| `top5-1015-<setup>-exec` x 5 (one per grid) | failed |
| `top5-1015-CWT14-failbrk-pdl-p05-long-X06-scaleout` | rework (beats parent, negative) |
| `top5-1015-CWT14-failbrk-orl-p05-long-X06-scaleout` | rework |
| `top5-1015-CWT14-failbrk-orl-p05-lowvol-long-X06-scaleout` | rework |
| `top5-1015-CWT14-failbrk-orl-p05-lowvol-long-X12-wait1` | rework |

## Proposed Testing additions
**None.** No variant met the Testing bar. No Primary setup is affected.

For reference only, **not proposed**: X06 maps to an existing config key, `scale_out_r: 0.25` with the default
`scale_out_frac: 0.5`. Production then moves the stop to breakeven after the partial. All three CWT14 entries in
`config/account_testing2.yaml` currently carry `scale_out_r: null`. Changing that would be an exit change and needs
the owner, an after-hours merge and a ledger entry (rules 9, 11). On this evidence it would make each CWT14 trade
lose about 0.02R less. It would not make the setups profitable.

## vs yesterday (top5_1014)
- Yesterday: 75 configurations, 0 beat their parent, best t_improve 1.74.
- Today: 89 configurations with different knobs (execution mechanics instead of thresholds and filters). 4 beat
  their parent (t 2.5-5.4), all through exit management on the CWT14 t05s1 setups. All are still negative.
- The two runs agree on the diagnosis: these setups' sign comes from the session regime, and no single knob changes
  that.

## Next run (queued, not scored)
- **Pair round (rule 18, pre-declared, counted against the same lineage N):**
  - CWT14 ORL: X06 scale-out + yesterday's V05 window from 10:30.
  - CWT14 PDL: X06 + V04 reclaim within 4 bars.
  - heat_fade_short-FD: X03 time stop + yesterday's H09 above VWAP.
- **Rotation:** if the same 4 setups lead the ranking again tomorrow, they will have been tuned twice. One more run
  without a change rotates them out (3-run rule). RW7-FD and CWT14-failbrk-pdl-p10-long are next in line.
