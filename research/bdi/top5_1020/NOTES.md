# Top-5 setup execution tune, 2026-10-20 (fifth run): FAILED the Testing bar, 0 of 80; 13 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-14..10-20 (rule 7). They are a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history, production and time-of-day costs in,
  TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15) unless a row says otherwise.
- The rule-19 locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was scored, because nothing
  reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored. Nothing was appended afterwards.
- **Configurations scored: 80** (5 setups x 16), plus 5 parent reference runs. Study bar max(1.5, sqrt(2 ln 80)) =
  **2.96**; setup bar (N 16) 2.35; CWT14 b3 lineage bar (N 121,364) 4.84.
- **Results:**
  - 0 variants meet the Testing bar.
  - 0 variants have exp > 0. Every parent and every variant loses after costs.
  - 13 beat their parent at the pre-declared bar: E04 / E05 (wider stop at the same $ risk) on all 5 setups, plus
    E06 (scale at 0.15R) and E08 (wait one bar) on orl-p05, and E08 on orl-p05-lowvol. The 10 E04/E05 rows also clear
    the lineage bar.
- **No Testing candidate. No DECISION line.**
- config/, mcf/, workflows, research/backlog.jsonl and owner_inbox are untouched. Nothing is committed.

Files:
- `live_rank.py`: live ranking plus the detail of the chosen 5 (`live_rank.csv`, `live_top5.csv`,
  `live_top5_detail.txt`).
- `scan_1020.py`: the top5_1019 harness, unchanged, with this run's BASE table. The parent includes the live
  scale-out.
- `report_1020.py`: writes `results.csv`, `summary.json` and `hist_parent_detail.txt`.
- `make_proposals.py`: writes `backlog_proposals.jsonl`, 18 lines with tag `top5-tune`. The lead appends them.

**Parity on 2025-06** (`scan_1020.py parity`):
- All 5 kernels equal `cwt_live_lib.b3`.
- R0 (the parent without scale-out) equals `gates.lab_trades` trade for trade: 4,413 / 2,882 / 2,767 / 1,988 / 1,626
  matched, mean |diff| 3-4e-5 R, 100% within 0.01R.

The scan took about 7 minutes. The 120 MB scratch trades file was deleted afterwards.

## Selection
Live paper trades on 10-14, 15, 16, 19, 20 (run_id 1; S6 and GEN-* out).

**Out:**
- the MF3 family;
- the 5 setups tuned in top5_1019;
- the 10-21 Graveyard moves: heat_fade_short-FD (212), L3-gap-slope-fromopen-FD (112), heat_fade_long-FD (98) and
  the rest of the list.

**In:** the next five, all CWT14 failed-breakout in Testing 2:

| setup | live trades |
|---|---|
| orl-p05-long | 235 |
| orl-p05-lowvol-long | 217 |
| pdl-p05-long | 187 |
| pdh-p05-lowvol-short | 122 |
| orl-p10-long | 121 |

**Caveat:** this is a homogeneous set. All five were tuned on 10-14..10-16, and all five got a live scale-out
(0.25R or 0.35R) afterwards. That scale-out only began to execute after the 10-19 runner fix: the first 2
`scaled+target` exits are on 10-20. So the live sample below is almost entirely **without** scale-out.

## Failures first

| setup | variants | exp > 0 | beat parent | parent exp (t) | best (d R; t_improve) | best variant exp (VALID t) |
|---|---|---|---|---|---|---|
| orl-p05-long | 16 | 0 | 4 | -0.0763 (-10.3) | E05 1.5x stop: +0.0285 (13.1) | -0.0478 (-5.14) |
| orl-p05-lowvol-long | 16 | 0 | 3 | -0.0752 (-9.9) | E05: +0.0287 (11.9) | -0.0465 (-4.79) |
| pdl-p05-long | 16 | 0 | 2 | -0.0648 (-9.1) | E05: +0.0240 (11.2) | -0.0409 (-4.16) |
| pdh-p05-lowvol-short | 16 | 0 | 2 | -0.0761 (-9.9) | E05: +0.0318 (13.2) | -0.0443 (-3.15) |
| orl-p10-long | 16 | 0 | 2 | -0.0695 (-5.7) | E05: +0.0239 (6.0) | -0.0456 (-2.09) |

**Regime split of the parents (up / down sessions):**
- longs: +0.012..+0.019 / -0.141..-0.146
- pdh short: -0.169 / -0.006

Each parent is a regime bet. The best execution change narrows the loss by about 0.03R and does not change the
sign. Walk-forward positive months: 0-20%.

## 1. Live (paper, 5 sessions) vs backtest

Live columns are win / BE win, then avg win / loss. Backtest columns are win / BE win / exp; P includes the scale-out
and R0 does not.

| setup | live n | live win / BE win | live avg win / loss | bt P | bt R0 | bt loser give-back | live never-worked losers |
|---|---|---|---|---|---|---|---|
| orl-p05 | 235 | 59.1 / 70.5% | +0.42 / -0.99 | 70.1 / 77.0% / -0.076 | 63.3 / 69.6% / -0.093 | 1.00R | 50 of 96 |
| orl-p05-lowvol | 217 | 53.9 / 71.8% | +0.41 / -1.04 | 70.6 / 77.4% / -0.075 | 63.6 / 69.7% / -0.091 | 1.01R | 51 of 100 |
| pdl-p05 | 187 | 61.0 / 67.0% | +0.49 / -1.00 | 70.6 / 76.4% / -0.065 | 63.9 / 69.8% / -0.087 | 1.00R | 36 of 73 |
| pdh-p05-lowvol-s | 122 | 60.7 / 68.8% | +0.45 / -0.98 | 68.7 / 74.4% / -0.076 | 63.1 / 69.6% / -0.097 | 1.14R | 31 of 48 |
| orl-p10 | 121 | 58.7 / 69.9% | +0.46 / -1.06 | 70.1 / 75.2% / -0.070 | 65.0 / 70.7% / -0.089 | 1.19R | 25 of 50 |

**Live trails the backtest (R0) by 2-10 points of win rate.** orl-p05-lowvol is the worst at 53.9% vs 63.6%.

**The conversion problem is unchanged.**
- The 0.5R target against a 1R stop needs about 70% wins without scale-out. With the scale-out, it needs 75-77%.
- The scale-out raises the backtest win rate by about 7 points and lifts exp by 0.016-0.022R (R0 vs P: t -3.7 to
  -8.2). The live change was right, but it does not reach break-even.

**Live MFE / MAE:**
- median MFE is 0.29-0.38R and median MAE 0.38-0.64R;
- about half of the live losers never reached +0.2R;
- 5-15 losers per setup reached +0.5R and still lost.

**Live split by session** (10-14 and 10-16 down; 10-15 and 10-20 up; 10-19 flat):

| setup | down | flat | up |
|---|---|---|---|
| orl-p05 | -0.20 (127) | -0.03 (58) | -0.21 (50) |
| orl-p05-lowvol | -0.30 (122) | -0.06 (53) | -0.37 (42) |
| pdl-p05 | **-0.68 (66)** | -0.06 (39) | **+0.37 (82)** |
| pdh-p05-lowvol-short | +0.02 (64) | -0.12 (9) | **-0.29 (49)** |
| orl-p10 | -0.16 (71) | -0.18 (27) | -0.18 (23) |

pdl-p05 and pdh-p05-lowvol-short follow the day exactly as the history says. The three ORL longs lost in every class.

**Where the losers cluster:**

*ORL longs*
- Live: 10:00-10:30 holds most of the trades: 176 / 162 / 92 at -0.15 / -0.26 / -0.21R. 10:30-13:00 is no better.
- History: 10:00-10:25 is the worst bucket (-0.082 / -0.086 / -0.073R), but starting at 10:30 (E10) gives only
  d +0.000..+0.007R, with t <= 1.21.

*pdl-p05*
- Live: the 09:50-10:00 entries are 85 trades at -0.29R, carried by 10-14 (-40.5R on 50 trades).
- History: 09:50 is the *best* bucket (-0.051R). So the live cluster is the 10-14 down day, not the time of day.

*pdh-p05-lowvol-short*
- Live: 10:00-10:30 is 59 trades at -0.21R.
- History: 13:00-15:00 is the worst bucket (-0.096 / -0.109R). E11 (until 11:00) gives d +0.005R, t 0.96.

*Index direction:*
- Entries after 10:30 against SPY are not worse than those with SPY, for the ORL longs and pdl.
- E12 (SPY filter) has d -0.006..+0.004R. It is not a lever here.

## 2. Grid readout (all 80 rows in `results.csv`)

d = paired TRAIN+VALID change in exp vs the live parent, in R per unit of $ risk. t = day-block t_improve.

| knob | d range over 5 setups (best t) | effect on the shape |
|---|---|---|
| R0 no scale-out | -0.016..-0.022 (t -3.7..-8.2) | Confirms the live scale-out change |
| E01 / E02 time stop 30 / 60 min | -0.000..+0.003 (1.56) | Smaller avg loss (-0.60..-0.88R), lower win rate; a wash |
| E03 stop 0.85R (same $) | -0.015..-0.017 (t -7..-13) | Clearly worse |
| **E04 stop 1.25R, same target and scale price (same $)** | **+0.014..+0.022 (6.1-12.5)** | win 69-71 -> 72-74%, avg loss -0.84..-1.03 -> -0.75..-0.96R |
| **E05 stop 1.5R (same $)** | **+0.024..+0.032 (6.0-13.2)** | win -> 74-76%, avg loss -0.66..-0.89R. Monotone in the stop: 0.85 < 1.0 < 1.25 < 1.5 |
| E06 scale trigger -0.1R | +0.000..+0.006 (2.62, orl-p05 only) | Win falls, avg loss -0.52R |
| E07 scale trigger +0.1R | -0.001..-0.009 | |
| E08 wait one bar | +0.006..+0.011 (3.19) | Beats the parent on orl-p05 / orl-p05-lowvol only. Excess vs random moves to -0.002..+0.003 (parents -0.005..-0.014); the only knob that moves the excess |
| E09 from 10:00 | 0 (ORL: = P) / -0.000..-0.004 | |
| E10 from 10:30 | -0.005..+0.007 (1.21) | Fewer trades (-23..-35%) |
| E11 until 11:00 | -0.006..+0.005 (0.96) | |
| E12 SPY-against filter after 10:30 | -0.006..+0.004 (0.89) | |
| E13 re-entry, 30-min cooldown | -0.001..+0.001 (0.97) | +4-19% trades at the same quality |
| T1 / T2 poke threshold +-20% | -0.003..+0.002 | Flat plateau |

**Excess over the same-minute random control** (TRAIN+VALID):
- Every row is negative except E08 (wait one bar) on pdl-p05 (+0.0025) and orl-p10 (+0.0017). Neither of those beats
  its parent (t_improve 1.31 / 1.58).
- E05 is at -0.005..-0.009, against the parents' -0.005..-0.014.
- As on 10-15, 10-16 and 10-19, the wide-stop gain is mostly generic exit geometry: random entries gain about as much.

## 3. Bars (PLAN section 4)

**Beats parent:** 13 variants.
- E04 and E05 on all 5 setups. t_improve is 6.0-13.2, above the lineage bar of 4.84.
- orl-p05: E06 (t 2.62) and E08 (t 2.93).
- orl-p05-lowvol: E08 (t 3.19).
- All 13 are still negative, with VALID t between -2.1 and -7.7.

**Testing bar:** VALID t >= 2.96 with exp > 0, both regimes > 0, and excess > 0. **0 met it.** No holdout was scored.

**Live support:**

| knob | how it could go live |
|---|---|
| E04 / E05 wider stop | A module only, no mcf/ change: GEOM "S" with `stop_price = close -/+ k x 0.25 x atr_d` and `target_price` = the parent's target price. The setup's `scale_out_r` is divided by k so that the scale price stays put. LabStrategy sizes by stop distance, so $ risk is unchanged. |
| E06 | config `scale_out_r` (scale-out executes since 10-19) |
| E08 | needs `entry_delay_bars` code |

**1.5x is the edge of the grid and the curve is still rising.** It is not a plateau proof. Every pair or extension is
a new lineage look.

## Backlog proposals (`backlog_proposals.jsonl`, 18 lines, tag `top5-tune`; not appended)
- `top5-1020-<setup>-exec` x 5: status **failed**.
- 13 beats-parent entries: status **rework**, each with `live_support`.

## Next run (queued, not scored)
- **E05 extension and pair round (rule 18):** stop 1.75x / 2.0x at the same $, and E05 + E08 on the ORL p05 pair.
- **Regime gate:** the CWT14 longs lose only on down sessions (-0.14R) and the pdh short only on up sessions (-0.17R).
  An intraday day-direction gate for this family failed on 10-16 (bdi1016). Any retry needs a new, pre-declared
  feature.
- **Rotation:** these 5 have now been tuned twice or three times. All five remain negative after costs under every
  execution change scored. A Graveyard or retire review, which is the owner's call, may fit better than a sixth grid.

Educational only — not financial advice.
