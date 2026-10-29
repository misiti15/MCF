Educational only — not financial advice.

# P2 2026-10-29: cold start / trade frequency (Testing 1 and Testing 2)

Owner Prompt 2. This is research only. No config, engine, setup, exit, ledger or backlog file was changed, and nothing was committed. Live = paper journals from the
`mcf-data-testing` / `mcf-data-testing2` state branches, sessions through 2026-10-28. Two-year = the open history
2024-10..2026-10-07 (426 sessions) from the `research/history2y` frames. **The locked block 2024-11..2025-02 was never loaded**
(asserted in `bt2y.py`). **No holdout was scored. Replays were not used** (rule 21: they are not audited yet). Costs are in everywhere, using the production model
in `mcf/research/gates.py`: entry 1c + 1 bp × the time-of-day multiplier, exit 1c + 1 bp (free on a target limit fill), +2c on stops.

**Configurations tried: N = 265** (36 parent / parent+time-stop, 49 count-only diagnosis configs (20% relaxations and
leave-one-out), 180 grid configs). Bar: t ≥ max(1.5, √(2 ln 265)) = **3.34**; near-miss ≥ 3.04. That is this study's own N. The
lineage bars are higher still (ST lineage N 120,500 → 4.84; the CWT batches are similar).

## Failures first

1. **No variant qualifies, and none is a near-miss.** 0 of 198 non-parent configs pass. 37 configs raise trades/month by 25%+
   without lowering avg R, but every one of them has t between −9.6 and +0.23, against a bar of 3.34. On the two-year data the
   loosened versions are the parent's edge (≈ 0, or negative), spread over more trades.
2. **The failure time-stop (exit at the 3rd bar unless +0.5R) does not help.** It lowers avg R in 14 of 18 parents. It helps only
   CWT04 lh-a25 (+0.265 → +0.294R, but only 6.8 trades/month), CWT04 vwaptest-a25 / vwaptest-a15 and CWT12 (+0.009 / +0.005 / +0.013R,
   all still negative). It never makes a negative setup positive.
3. **The only positive parents fail the one-big-day check.** CWT04-backside-lh-a25-short is +0.265R (t 1.29) and CWT04-backside-lh-a15-short is +0.186R (t 0.96).
   Without their best day both are **−0.11R**. The April 2025 crash carries both: lh-a25 fired 3.24 times/day that month against 0.32 overall.
   Loosening `a` toward 1.25 ATR dilutes them toward 0, so lh-a15 is in effect lh-a25 at x0.6 (the same numbers).
4. **The 2-year trade counts are 2-30× the live counts for all 18 setups** (live/backtest 0.00–0.50, Poisson p(≤ live) < 0.03 for
   every setup). See "Live vs backtest gap" below. Part of this is the regime: the last 3 open months run below the 2-year average
   (e.g. CWT13-long 5.1/day against 9.4). But even the recent rates are well above live. The gap is **not** explained by the universe:
   live has 1,175 names with ADV ≥ $95M against ~972/day in the lab frames.
5. **The path simulator is cruder than the frames.** My 5-minute path sim (stop first inside a bar, entry at the signal-bar close, which is needed for
   the time-stop) runs on average 0.00–0.05R below the frames' 1-minute outcome (`avgR_frame` column; per-trade correlation 0.86–0.99). The parent and its variants are compared
   in the same sim, so the deltas are fair. The levels are slightly pessimistic. Gaps through a stop are filled at the stop (the frames have no open price).

## 1. Tiers (rule 21; sessions = freeze-file sessions since the setup's current continuous enabled run began)

Source: the daily `setups/<date>.json` freeze files on each account's state branch (`tiers.py` → `tiers.csv`). The T1 setups
started on 10-12 (the 10-09 file has them disabled). Testing 2 started on 10-12.

- **Testing 1: dormant 0, low 8, normal 11**, young (< 10 sessions) 13. Low: LIQ-pdl-sweep-open15-vwap-long (0.08/session),
  ST3 (0.15), ST5 (0.15), ST6 (0.46), ST8 (0.62), ST4 (1.00), NS4-FD (1.46), intraday_momentum (1.46).
- **Testing 2: dormant 2, low 10, normal 2**, young 34. Dormant: CWT04-backside-lh-a25-short, CWT04-backside-vwaptest-a25-short
  (0 signals in 13 sessions). Low: CWT04 lh-a15 (0.08), CWT05 m075-v5 (0.23), CWT05 m05-v5 (0.31), CWT09 vwaploss-g10 (0.31),
  CWT04 vwaptest-a15 (0.46), CWT13 z075-long (0.69), CWT05 m075-v3 (0.77), CWT09 bounce-g10 (0.85), CWT12-flag-s1 (1.00),
  CWT13 z075-short (1.08).
- **Will reach 10 sessions soon with ~0 trades:** IDX1 hold / IDX1 trail / IDX2 / IDX3 / IDX5 (T1, 9 sessions, 0 signals:
  these become dormant after today's session), NM-AMS-N1 and NM-RWR1 (T2, 8 sessions, 0 trades), and the LD1/3/4/5/8 breadth longs (T2, 6 sessions, 0 trades).
- **Caps confirmed as not binding:** over 10-20..10-28, the slot / per-setup / trades-per-day caps blocked 0 signals in Primary (77 slots since
  10-27), Testing 1 and Gen. Testing 2 had 1 (one "max positions for this setup"), and the Graveyard 350, which is set low on purpose. Lot cap, opposite side and the −2R stop are
  counted separately. This matches `research/ops/exposure1026.md`.

## 2. Table per setup

Live = paper, since entry. "sig-days" = unique symbol-day signals per session, before the skips. bt = two-year trades per session
(first per symbol-day). Binding = the threshold whose 20% relaxation adds the most signals (`diag_out.txt`). The best variant is the
grid config with the highest t among those with ≥ +25% trades/month. t = day-clustered.

| setup | acct | tier | sess | live trades (/sess) | live sig-days/sess | bt /day | live/bt | binding | best variant | trades/month parent → variant | avg R parent → variant | t (bar 3.34) | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ST3-rsi5up-short-pm-t1s1-FD | T1 | low | 13 | 2 (0.15) | 1.23 | 1.542 | 0.1 | fo_with 3.0 | flt0x0.9 | 32.4 → 41.3 (+28%) | -0.021 → -0.013 | -0.39 | t |
| ST5-pdbrkup-short-mid-t05s1-FD | T1 | low | 13 | 2 (0.15) | 0.54 | 1.0 | 0.15 | fo_with 3.0 | flt0x0.8 | 21.0 → 35.4 (+69%) | -0.040 → -0.051 | -1.39 | avgR,t |
| ST6-volspikeup-short-mid-t1s1-FD | T1 | low | 13 | 6 (0.46) | 1.23 | 1.425 | 0.32 | fo_with 3.0 | flt0x0.9 | 29.9 → 38.7 (+29%) | -0.000 → +0.005 | 0.18 | t |
| ST8-volspikedn-long-pm-t1s1-FD | T1 | low | 13 | 8 (0.62) | 0.77 | 1.239 | 0.5 | fo_against 3.0 | flt0x0.9 | 26.0 → 32.8 (+26%) | +0.003 → -0.003 | -0.07 | avgR,t |
| ST4-emadn-long-am-t1s05-FD | T1 | low | 13 | 13 (1.0) | 1.69 | 3.052 | 0.33 | rsi5_ext 80 | flt2x0.7 | 64.1 → 135.9 (+112%) | +0.002 → -0.008 | -0.37 | avgR,t |
| NS4-pm-vwap-reclaim-oversold-short-FD | T1 | low | 13 | 19 (1.46) | 2.77 | 3.972 | 0.37 | rsi 30.0 | rsix1.1 | 83.4 → 137.6 (+65%) | -0.040 → -0.045 | -2.22 | avgR,t |
| CWT04-backside-lh-a25-short | T2 | dormant | 13 | 0 (0.0) | 0.0 | 0.324 | 0.0 | a 2.5 | ax0.9+TS | 6.8 → 12.3 (+81%) | +0.265 → +0.252 | 1.36 | avgR,t |
| CWT04-backside-vwaptest-a25-short | T2 | dormant | 13 | 0 (0.0) | 0.0 | 0.502 | 0.0 | a 2.5 | ax0.7+TS | 10.5 → 53.0 (+405%) | -0.185 → -0.228 | -2.50 | avgR,t |
| CWT04-backside-lh-a15-short | T2 | low | 13 | 1 (0.08) | 0.31 | 2.594 | 0.03 | a 1.5 | ax0.9 | 54.5 → 78.7 (+44%) | +0.185 → +0.126 | 0.76 | avgR,t |
| CWT04-backside-vwaptest-a15-short | T2 | low | 13 | 6 (0.46) | 0.85 | 4.242 | 0.11 | a 1.5 | ax0.9+TS | 89.1 → 131.8 (+48%) | -0.175 → -0.150 | -3.79 | t |
| CWT05-flush-m075-v5-long | T2 | low | 13 | 3 (0.23) | 0.46 | 1.312 | 0.18 | m 0.75 | mx0.8 | 27.6 → 42.8 (+55%) | -0.081 → -0.093 | -2.36 | avgR,t |
| CWT05-flush-m05-v5-long | T2 | low | 13 | 4 (0.31) | 0.69 | 2.847 | 0.11 | v 5.0 | vx0.9 | 59.8 → 76.4 (+28%) | -0.098 → -0.095 | -3.05 | t |
| CWT05-flush-m075-v3-long | T2 | low | 13 | 10 (0.77) | 1.15 | 2.8 | 0.28 | m 0.75 | mx0.9 | 58.8 → 79.1 (+34%) | -0.149 → -0.146 | -3.70 | t |
| CWT09-gapdn-vwaploss-g10-short | T2 | low | 13 | 4 (0.31) | 3.38 | 1.995 | 0.16 | gap 10.0 | gapx0.9 | 41.9 → 54.7 (+30%) | +0.008 → +0.014 | 0.23 | t |
| CWT09-gapdn-bounce-g10-lowerhalf-short | T2 | low | 13 | 11 (0.85) | 5.38 | 2.343 | 0.36 | gap 10.0 | gapx0.9 | 49.2 → 64.0 (+30%) | -0.012 → -0.045 | -0.37 | avgR,t |
| CWT13-vwapstretch-z075-long | T2 | low | 13 | 9 (0.69) | 3.08 | 9.411 | 0.07 | z 0.75 | zx0.9 | 197.6 → 310.3 (+57%) | -0.041 → -0.052 | -2.17 | avgR,t |
| CWT13-vwapstretch-z075-short | T2 | low | 13 | 14 (1.08) | 2.08 | 6.362 | 0.17 | z 0.75 | zx0.8 | 133.6 → 383.9 (+187%) | -0.097 → -0.089 | -2.97 | t |
| CWT12-flag-s1-long | T2 | low | 13 | 13 (1.0) | 1.31 | 3.293 | 0.3 | s 1.0 | sx0.9 | 69.2 → 106.4 (+54%) | -0.082 → -0.083 | -3.91 | avgR,t |

Not in the grid:
- `LIQ-pdl-sweep-open15-vwap-long`: it has a structural VWAP target with BE + a 15-minute time stop, which my sim does not model. Its scored open history was 0.38/day (reddit1012liq), and live shows 1 trade in 12 sessions (expected ≈ 4.6, p ≈ 0.06).
- `intraday_momentum`: a 1-minute production-backtester setup. Its two-year rate is 2.70/session (`rescore.csv`, 1,151 / 426), and live is 1.46 (expected ≈ 35 in 13 sessions, observed 19, p ≈ 0.002).

**Stack setups (leave-one-out, two years):** "stock ±3% from the open" is the binding filter in ST3 / ST5 / ST6 / ST8. Removing it gives 54× / 247× / 56× / 33× more
signals; removing any other filter gives 1-15×. In ST4 the 20% relaxation of RSI(5) ≤ 20 adds the most (x1.8), but leave-one-out
says from-open is the bigger block (20×). In NS4, RSI ≤ 30 (x2.5 at −20%) and the from-open filter (> 2%) block about equally.

## 3. Live vs backtest gap (housekeeping, not a strategy change)

Every one of the 18 setups trades far below its two-year rate. The funnel has two separate losses:
- **Signal level (live sig-days / bt).** This ranges from 0.0 (CWT04 a25 ×2, expected 4.2 and 6.5 in 13 sessions: p 0.015 / 0.0015) through 0.07-0.33
  (CWT04 a15, CWT05, CWT13, CWT12, ST*) up to ≈ 0.6-1.7 for the CWT09 / NS4 shorts. Even against the last 3 open months, CWT13 z075-long fires 3.1 sig-days against 5.0,
  CWT12 1.3 against 2.1, and CWT05 m05-v5 0.7 against 2.1. **HK row proposed: LAB-RATE-PARITY.** Run each module's mask on the live 10-12..10-28 SIP
  bars for every name with ADV ≥ $95M (≥ $1M for CWT09) and compare signal counts with the journal's signals table. This is a parity check of the live
  frame / prefilter / poll path (T2 polls 70% of minutes), not a replay used as evidence. CWT13 z075-long also lost 28 signals to the
  account `halted` state on 10-14 / 10-16 (843 T2 signals that day).
- **Skip level (trades / sig-days).** Shorts lose most of their signals to borrow: CWT09 vwaploss 35 of 44 signals ETB, CWT09 bounce 53 of 70,
  NS4-FD 10 of 36, and ST3 / ST5 / ST6 to the split-tape short gate + ETB + opposite side held. The two-year backtest has no borrow model, so
  **it overstates the tradeable rate of the gap-down shorts by roughly 5×**. A borrow-aware rate (HK) is needed before any rate gap
  for CWT09 is read as a bug.

## 4. Recommended owner decisions

1. **Do not loosen any of the 18.** No variant clears the bar or comes within 0.3 of it. Loosening is supported only where the parent has an
   edge, and none does once the one-big-day check is applied.
2. **Run LAB-RATE-PARITY (housekeeping) before judging the dormant / low setups on their trade count.** The 2-30× gap is too large
   and too uniform to be only the quiet October tape.
3. **The two dormant CWT04 a25 setups:** their positive two-year record is one crash month (ex-best −0.11R). After LAB-RATE-PARITY,
   the owner can decide whether they stay in Testing 2 or move to the Graveyard (rule 20: the owner decides; nothing is proposed here).
4. Prompt 2's time-stop idea is not proposed for any setup: it lowered avg R in 14 of 18 parents.
5. `backlog_proposed.jsonl`: **no lines.** No setup or exit idea reached the bar.

## Files and how to rerun
- `tiers.py <scratch>` → `tiers.csv` (rule-21 tiers); `live_signals.py <scratch>` → `live_signals.csv` (funnel + skip reasons).
  `<scratch>` = `t1|t2/journal.db` and `frz/testing|testing2/*.json` copied read-only from the state branches.
- `bt2y.py [workers] diag` then `report.py diag` → `diag_out.txt`, `diag_table.csv`, `binding.json`. Then `bt2y.py [workers] grid` and
  `report.py grid` → `grid_out.txt`, `results.csv` (all 216 scored rows, failures included). `table.py` → `table_out.md`.
  The trades parquets are in the session scratchpad (`p2/`), not in git.
- Costs are in. Survivorship caveat (rule 19): today's lab list applied to the past.
