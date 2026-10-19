# Top-5 setup execution tune, 2026-10-19 (fourth run): FAILED the Testing bar, 0 of 93; 7 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-13..10-19 (rule 7). They are a diagnosis, not evidence.
  **Testing 1's 10-19 report is missing about 132 trades**, so the two T1 setups (LIQ, RW2) are under-counted for 10-19.
- History numbers are **backtests** on the open two-year history (2024-10, 2025-03..2026-10-07), production and
  time-of-day costs in, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15) unless a row says otherwise.
- The rule-19 locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was scored, because nothing
  reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored. Nothing was appended afterwards.
- **Configurations scored: 93** (3 CWT14 x 18, LIQ 19, RW2 20), plus 5 parent reference runs.
  Study bar max(1.5, sqrt(2 ln 93)) = **3.01**.
- **Results:** 0 variants meet the Testing bar, 0 meet the research bar, and 3 have exp > 0 (all LIQ index-filter rows,
  t <= 1.15). **7 beat their parent** at the pre-declared bar, and 6 of those 7 also clear the lineage bar.
- **No Testing candidate.** config/, mcf/ and workflows are untouched. research/backlog.jsonl and owner_inbox are
  untouched. Nothing is committed.

Files:
- `live_rank.py`: ranks the setups from `reports/<date>.csv` on the 3 data branches. Writes `live_rank.csv`,
  `live_top5.csv` and `live_top5_detail.txt`.
- `scan_1019.py`: the history scan. It is `top5_1016/scan_1016.sim`, extended with a per-trade risk unit and a fixed
  stop price (LIQ), the SPY-direction filters and re-entry after a cooldown.
- `report_1019.py`: writes `results.csv`, `summary.json` and `hist_parent_detail.txt`.
- `make_proposals.py`: writes `backlog_proposals.jsonl`, 12 lines in backlog.jsonl format with tag `top5-tune`. The lead
  appends them; this script does not touch research/backlog.jsonl.

**Parity on 2025-06** (`scan_1019.py parity`):
- The 3 CWT14 kernels equal `cwt_live_lib.b3`.
- The LIQ mask equals the live module's `mask()`.
- The CWT14 and RW2 parents equal `gates.lab_trades` trade for trade: 1,558 / 1,722 / 1,376 / 681 matched, mean |diff|
  3-5e-5 R.

The scan takes about 5 minutes. The 54 MB scratch trades file was deleted afterwards.

## Rotation and selection
**Rotated out:** every setup tuned in the last 3 runs (10-14, 10-15, 10-16).

| setup(s) | live trades | why out |
|---|---|---|
| CWT14 orl-p05 / orl-p05-lowvol / pdl-p05 | 314 / 293 / 215 | They got `scale_out_r 0.25` + `live_scale_out` from 10-19. **Flag:** live partial exits do not work at Alpaca (the bracket leg qty cannot be changed), so these three are effectively unchanged. A third grid would only repeat 10-14/10-15. The real gap is a runner fix, or E05 below as a supported alternative. |
| heat_fade_short-FD | 269 | tuned 10-14 and 10-15, no change |
| orl-p10, pdh-p05-lowvol-short, orl-p10-lowvol, RW7-FD, coil-k4 | | tuned 10-16 (coil also 10-15), no change |

**Chosen:** the next five by live count. None of them was tuned before.

## Failures first

| setup (acct) | variants | exp > 0 | beat parent | best (d R; t_improve / setup bar / lineage bar) |
|---|---|---|---|---|
| CWT14-failbrk-pdl-p10-long (T2) | 18 | 0 | 2 | E05 1.25x stop, same target: -0.0683 vs -0.0854, **d +0.0171R, t 8.01** / 2.40 / 4.84 (met) |
| CWT14-failbrk-pdl-p05-lowvol-long (T2) | 18 | 0 | 2 | E05: -0.0734 vs -0.0930, **d +0.0195R, t 8.83** (met) |
| CWT14-failbrk-pdh-p10-short (T2) | 18 | 0 | 2 | E05: -0.0634 vs -0.0881, **d +0.0247R, t 8.90** (met) |
| LIQ-orl-sweep-open15-s25-long (T1) | 19 | 3 | 0 | E12 skip longs while SPY < open: +0.0520R (t 1.15; TRAIN +0.072 / VALID +0.023, VALID t 0.29) vs -0.0099; d +0.0619R, t 1.60 / 2.43 / 4.23 |
| RW2-exhaustion-noon-adv150-short-FD (T1) | 20 | 0 | 1 | E05: -0.0482 vs -0.0633, d +0.0151R (TRAIN +0.023 / VALID +0.004), t 3.92 / 2.45 / 5.24 (not met) |

d = the paired TRAIN+VALID difference in exp per unit of $ risk. LIQ note: every LIQ signal comes after 10:30, so E10
equals the parent and E12 equals E14 (they still count in N).

**Every parent is negative after costs** (TRAIN+VALID):

| setup | exp | t | regime split (up / down) |
|---|---|---|---|
| pdl-p10-long | -0.085R | -7.5 | +0.036 / -0.203 |
| pdl-p05-lowvol-long | -0.093R | -8.4 | +0.043 / -0.215 |
| pdh-p10-short | -0.088R | -8.3 | -0.196 / +0.007 |
| LIQ | -0.010R | -0.25 | +0.359 / -0.288 |
| RW2-FD | -0.063R | -3.2 | -0.196 / +0.123 |

The best execution change narrows the loss by about 0.02R and does not change the sign. Every setup is a regime bet.

## 1. Live (paper, 5 sessions) vs backtest

| setup | live n | live win / BE win | live avg win / loss | backtest win / BE win / exp | bt med MFE / MAE | bt loser give-back |
|---|---|---|---|---|---|---|
| pdl-p10-long | 164 | 62.2 / 72.5% | +0.39 / -1.02 | 64.6 / 70.3% / -0.085 | 0.54 / -0.51 | 1.25R |
| pdl-p05-lowvol-long | 142 | 61.3 / 67.7% | +0.45 / -0.93 | 63.5 / 69.8% / -0.093 | 0.53 / -0.51 | 1.23R |
| pdh-p10-short | 136 | 66.9 / 69.5% | +0.44 / -0.99 | 65.3 / 71.0% / -0.088 | 0.55 / -0.52 | 1.29R |
| LIQ-orl | 126 | 43.7 / 48.4% | +0.88 / -0.83 | 48.1 / 48.8% / -0.010 | 0.39 / -0.57 | 1.10R |
| RW2-FD | 125 | 45.6 / 51.3% | +0.92 / -0.97 | 49.5 / 53.0% / -0.063 | 0.36 / -0.76 | 1.30R |

- **Conversion problem (CWT14):** the 0.5R target against a 1R stop needs a 70% win rate. Live and backtest both sit
  at 62-67%.
- **Never-worked losers** (MFE < 0.2R): live 30/62, 26/55, 16/45, 42/71, 36/68; backtest 54-56% of CWT14 losers.
- **LIQ:** 68 of 126 live trades ride to 15:55, at +0.52R, and only 4 hit the 2.5R target. In the backtest, 70% end
  flat at 15:55.

**Where the losers cluster.** Live is from `live_top5_detail.txt`, history from `hist_parent_detail.txt`.

*pdl-p10-long*
- Live: the 09:50-10:00 entries are 48 trades at -0.58R. 10-14 alone lost -25.6R.
- History: the 09:50 bar is not worse (-0.069R), and starting at 10:00 (E09) does not help.

*pdl-p05-lowvol-long*
- Live: 09:50-10:30 is 81 trades at -0.26R, and 10:30-13:00 is +0.15R.
- History: from 10:30 (E10) gives d +0.008R, t 0.86.

*pdh-p10-short*
- Live: 10-15 (up day) lost -13.2R.
- History: up sessions run -0.196R and down sessions +0.007R.

*LIQ*
- Live: 10-14 lost -19.6R and 10-19 lost -6.1R.
- History: it depends on the index. Entries with SPY below its open run -0.061R (5,956 trades); entries with SPY above
  run +0.052R (4,868).

*RW2-FD*
- Live: 10-15 (up day) was 60 trades at -0.34R.
- History: 09:50-10:30 runs -0.08 to -0.11R and 13:00-15:00 runs about 0.

**Giveback check** (entries after 10:30 against SPY's move):
- For the 3 CWT14 setups it is a small effect: after 10:30, against SPY -0.088 to -0.108R vs with SPY -0.079 to -0.099R.
  E12, E13 and E14 give d -0.009 to +0.010R, all below the bar.
- It is large only for LIQ, where every signal comes after 10:30. But its valid t is 0.29 and down sessions are
  -0.49R, so it fails.

## 2. Grid readout (all 93 in `results.csv`)

d = paired TRAIN+VALID change in exp vs the parent (R per unit of $ risk); t = best day-block t_improve.

| knob | CWT14 x3: d (best t) | LIQ: d (t) | RW2: d (t) | effect on the win/loss shape |
|---|---|---|---|---|
| E01-E02 time stop 30/60 min | -0.001..+0.003 (1.57) | +0.000 / +0.004 (0.56) | -0.002 / +0.002 | Smaller avg loss (-1.06 -> -0.78..-0.98R) and lower win rate; a wash |
| E03-E04 tighter stop 0.85/0.75R (same $) | **-0.017..-0.038** (t -7 to -13) | +0.003 / -0.010 | -0.018 / -0.032 | Clearly worse |
| **E05 1.25x stop, target price unchanged (same $)** | **+0.017..+0.025 (8.0-8.9)** | +0.001 (0.2) | +0.015 (3.92) | CWT14 win 63-65 -> 67-70%, avg loss -1.03..-1.10 -> -0.94..-1.03R; up and down sessions both improve |
| E06 breakeven | -0.008..-0.009 | -0.002 | -0.005 | Cuts winners (win 64 -> 51-53%) |
| E07 scale-out (Alpaca caveat) | **+0.023..+0.027 (4.9-6.0)** | -0.001 | +0.013 (1.6) | Win -> 71%, avg win falls to +0.26R |
| E08 wait one bar | -0.001..+0.009 (2.14) | -0.005 | +0.004 | |
| E09-E11 entry window (from 10:00 / 10:30, until 11:00) | -0.012..+0.006 (1.54) | 0 / -0.014 | 0 / +0.011 / -0.016 | Live 09:50 clusters do not repeat in history |
| E12-E14 SPY-direction filter | +0.000..+0.008 (1.28) | **+0.062** (1.60) / +0.021 / +0.062 | -0.007 / -0.011 / +0.013 | LIQ: positive exp but VALID t 0.29, down -0.49R |
| E15 flow3 agrees | -0.004..+0.006 (1.48) | +0.006 | +0.008 (3 trades/day) | |
| E16 re-entry, 30-min cooldown | +0.001..+0.002 (1.25) | +0.000 | +0.004 (2.07) | Few extra trades (+4-10%) |
| T1-T4 thresholds +-20% / LIQ target 1.5R/2.0R / RW2 rsi5 88/92 | -0.005..+0.001 | -0.032..+0.003 | -0.003..+0.003 | Flat plateau |

**Excess over the same-minute random control:**
- E05: pdh +0.0004 (parent -0.0036), pdl-p05 -0.0097 (parent -0.0130), pdl-p10 -0.0098 (parent -0.0040), RW2 +0.0107
  (parent +0.0095).
- E07: -0.0014 / -0.0083 / -0.0049.
- So, as on 10-15 and 10-16, the exit gains are mostly generic: a random same-minute entry gains about as much.

## 3. Bars (PLAN section 4)
**Beats parent:** TRAIN d > 0, VALID d > 0, and the day-block t of the improvement >= the setup bar. 7 variants pass.

| variant | d TRAIN / VALID | t_improve | lineage bar | variant exp (VALID t) | up / down |
|---|---|---|---|---|---|
| pdh-p10-short E05 | +0.024 / +0.025 | 8.90 | 4.84 met | -0.063 (-3.05) | -0.176 / +0.037 |
| pdl-p05-lowvol E05 | +0.019 / +0.020 | 8.83 | 4.84 met | -0.073 (-4.58) | +0.053 / -0.188 |
| pdl-p10 E05 | +0.015 / +0.021 | 8.01 | 4.84 met | -0.068 (-4.45) | +0.045 / -0.178 |
| pdh-p10-short E07 (Alpaca caveat) | +0.025 / +0.029 | 6.00 | met | -0.061 (-3.57) | -0.127 / -0.000 |
| pdl-p10 E07 (caveat) | +0.024 / +0.025 | 5.21 | met | -0.061 (-5.28) | +0.018 / -0.136 |
| pdl-p05-lowvol E07 (caveat) | +0.017 / +0.033 | 4.91 | met | -0.070 (-5.02) | +0.013 / -0.149 |
| RW2-FD E05 | +0.023 / +0.004 | 3.92 | 5.24 not met | -0.048 (-0.49) | -0.175 / +0.129 |

**Testing bar** (VALID t >= 3.01 with exp > 0, both regimes > 0, excess > 0): **0 met it.** Every variant is negative.
No DECISION line is warranted.

**Live support:**

| knob | live support |
|---|---|
| E05 1.25x stop, same target | Supported **without an mcf/ change**. It needs a new research module with GEOM "S", `stop_price = close -/+ 1.25 x 0.25 x atr_d` and `target_price` = the parent's target price. LabStrategy sizes by the stop distance, so the $ risk stays the same. Plus a new config entry. Only one value (1.25) was scored; 0.85 and 0.75 are worse, so the trend is monotone, but 1.5x is untested on these modules. |
| E07 scale-out | **Not executable at Alpaca today**: the bracket leg qty cannot be changed. It needs a runner change first. The same caveat applies to the CWT14 p05 trio's live `scale_out_r 0.25`. |
| E08 wait one bar | Needs code (`entry_delay_bars`). |
| Window / SPY / flow filters | Config or a new module. |
| E16 re-entry | Roughly `refire: true` + `refire_cooldown: 6`, but that cooldown counts from the signal, not from the exit. |

## Backlog proposals (`backlog_proposals.jsonl`, 12 lines, tag `top5-tune`; not appended)
- `top5-1019-<setup>-exec` x 5: status **failed**.
- 7 beats-parent entries: status **rework**, each with a `live_support` field.

## Next run (queued, not scored)
- E05 at 1.25x / 1.5x on the CWT14 p05 trio, as the Alpaca-executable replacement for their non-working scale-out.
  Also a pair round (rule 18): E05 + E08 (wait one bar).
- LIQ + E12 as a regime-aware version (rule 18 rework). It needs positive down-session evidence before any Testing look.
- Rotation: these 5 are tuned once. pdl-p10, pdl-p05-lowvol and pdh-p10 got no live change.

Educational only — not financial advice.
