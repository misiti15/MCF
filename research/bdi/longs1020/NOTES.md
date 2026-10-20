# longs1020: dip-timed longs (BDI, owner request 2026-10-20). Results

*Educational only. Not financial advice. These are backtests on the open two-year history, with costs in. Nothing here is paper or live.*
- The plan was declared in `PLAN.md` before scoring.
- The locked block (2024-11-01..2025-02-28) was never read. 1-minute files were read with pyarrow row filters that drop it. One early exploratory call loaded the whole SPY file to print its date range; no locked row was analysed or printed.
- No holdout was scored.
- TRAIN = sessions up to 2025-12. VALID = 2026-01 onward (frames end 2026-10-07; 1-minute bars end 2026-10-16, so 10-20 itself is not in the data).

## Failures first
- **0 candidates.** 200 pre-declared configurations were scored (`counts.json`):
  - Part A index: 96, plus 8 A2, plus 8 parents.
  - Part B stocks: 64, plus 16 live-setup variants, plus 8 parents.
  - 8 random controls are reported alongside.
- **Bars:**
  - study bar `max(1.5, sqrt(2 ln 200))` = **3.26**
  - live-long lineage (NS/ST rework 165,764 + top5 7,737 + 200) = **4.91**
  - index-dip lineage (266,882 + 200) = **5.00**
  - No configuration reaches either bar, and none clears the Testing bar (`gate_check.csv`).
- **Part A (index dip-bounce, 104 new rows): best VALID t 0.99.**
  - 13 of 104 rows are positive on both train and valid.
  - **0 of 104 are positive in down sessions.**
  - The confirmation triggers do **not** beat a random entry time on the same dip days. Only 2 of 104 beat C_same on both splits.
  - Mean VALID R by trigger, against the same-days random bar:

    | trigger | mean VALID R | same-days random bar |
    |---|---|---|
    | VWAP reclaim | −0.17 | +0.12 |
    | higher-low | −0.03 | +0.09 |
    | rec20 | −0.08 | +0.07 |
    | breadth turn | +0.05 | +0.12 |

  - Waiting for confirmation enters after most of a shallow bounce is done.
- **Part B (stock dip-timed longs, 64 rows): all 64 are negative on train and valid.**
  - Excess over a same-minute random long is −0.14..+0.03R.
  - The rows are pure beta: up sessions −0.04..+0.38R, down sessions −0.15..−0.44R.
  - "Index down but the stock holds above its open / VWAP / prior-day low" (B2) is also negative in down sessions: −0.16..−0.32R.
  - Buying relative strength on a bad tape did not work.
- **IDX parents:**
  - The IDX5 replica (SPY ≥ 0.5% by 09:45) traded 12 times in train (+0.36R t1s1) and 5 in valid (+0.58R).
  - The IDX1 replica traded 7 and 2 times and is negative.
  - The samples are too small to judge the live IDX setups.

## Part 0: how often does the index dip early and bounce? (`dip_buckets.csv`, `dipstats.json`, `predictors.csv`)
**Hindsight view.** In about 43% of sessions (SPY: train 42.9%, valid 42.7%; QQQ 45% / 37%), the 09:30–11:00 low prints at 09:35–10:15. Where that low was ≥ 0.10% below the open:
- SPY was back at its open by 12:00 in 88% (train) / 83% (valid) of cases.
- The median bounce was 2.0× the dip.
- SPY closed above its open in 52–53% of cases.

**Dip size matters, and shallow dips bounce best.**

| SPY dip size | back to open by noon | close above open |
|---|---|---|
| 0.10–0.25% | 91% | 65% train / 57% valid |
| 0.25–0.50% | 48–51% | 30–35% |
| 0.50–1% | 36% | 25–28% |
| > 1% | 0–17% | 0–17% |

The owner's 10-20 read (−0.21%, then a rally) is the typical shallow-dip case.

**At decision time (10:00), the edge mostly disappears.** We took the days where SPY was ≥ 0.10% below its open on a 5-minute close by 10:00: 126 train and 97 valid days.
- Only 30% / 31% of those days held the low and were higher at 12:00.
- The mean SPY return from 10:00 to 12:00 was −0.01% / +0.05%.
- Knowing that "the low was early" needs hindsight.

**What predicts that the low holds.** These features are stable on both splits, with AUC 0.66–0.80:
- recovery off the low
- close vs VWAP
- position in the opening range
- breadth (share above VWAP), and breadth's rise from its low

But they barely predict **how far** the index rallies afterwards: Spearman with the 10:00→12:00 return is ≤ 0.09. They mostly restate that price is already away from the low.

**Weak signals that hold on both splits:**
- a down prior day (AUC 0.44–0.47) slightly favours the bounce;
- gap, volume and dip/ATR carry nothing.
- QQQ−SPY strength helped SPY on train (0.65) but not on valid (0.51).

## Results (train / valid exp R after costs, day-clustered t, trades/day, down-session R)
| config | train | valid | /day | down | note |
|---|---|---|---|---|---|
| A-QQQ-abs015-brd-t05s1 (QQQ ≥ 0.15% dip, breadth turns, TQQQ) | +0.030 (92, t0.42) | +0.079 (67, t0.96) | 0.4 | −0.06 | best Part A; beats C_all and C_same; misses t |
| P-IDX5-SPY-t1s1 (parent replica, SPXL) | +0.36 (12) | +0.58 (5, t1.61) | 0.04 | +0.15 (9) | n too small |
| B5-NS1-BRDUP-t05s1 (NS1 + breadth rising) | +0.081 (61, t0.71) | +0.108 (73, t1.52) | 0.35 | +0.02 | beats NS1 (−0.008 / +0.054) and random; n_train < 150 |
| B5-ST2-IDXTURN-t05s1 (ST2 after SPY dip-turn) | +0.035 (23) | +0.268 (50, t3.44) | 0.26 | −0.04 | train = parent; n tiny; valid concentrated in 2026Q2 |
| B5-ST2 / ST4 parents (live) | +0.03 / +0.08 (57–59) | +0.17 / +0.19 (t2.6 / 2.2) | 0.6 | +0.07 / +0.05 | the live AM longs are positive in 2026 but weak on train |
| best B1–B4 (B2-d060-am-time60) | −0.28 | −0.03 | 25 | −0.23 | all 64 negative |

Random 3x-ETF long at 09:50–10:30 on all days: SPXL −0.03..−0.08R, TQQQ −0.03..−0.13R.

## Near-misses (observation only, if the owner wants; NOT candidates)
- `modules/LD1-ns1-breadthup-t05s1-long.py`, "Oversold Pop with Breadth Turning Up".
  - It is NS1, taken only when market breadth is ≥ 5 points higher than two bars earlier.
  - Overall: n 134, +0.095R, t 1.50. Positive in 7 of 9 quarters. Best day 2025-04-07 (15% of P/L). Without the best day: +0.059R.
  - Every trade is also an NS1 trade: it is a filtered copy.
  - Parity with the scan is exact (`verify_modules.json`, 26/26).
- `modules/LD2-qqq-dip015-breadthturn-tqqq-t05s1-long.py`, "Shallow Nasdaq Dip, Breadth Turn → TQQQ".
  - The valid t is 0.96.
  - Offline parity is 137 of 159: the frames lack QQQ's 09:35–09:45 bars, and the live frame has them.

```yaml
# config/account_testing.yaml (strategies:), ONLY if the owner asks for observation. Near-misses, research bar not met.
  LD1-ns1-breadthup-t05s1-long:
    enabled: true
    type: lab
    module: research/bdi/longs1020/modules/LD1-ns1-breadthup-t05s1-long.py
    min_adv: 95000000
    window: [950, 1130]
    context: [breadth]
    scale_out_r: null
    tags: [near-miss, longs1020, forward-observation]
  LD2-qqq-dip015-breadthturn-tqqq-t05s1-long:
    enabled: true
    type: lab
    module: research/bdi/longs1020/modules/LD2-qqq-dip015-breadthturn-tqqq-t05s1-long.py
    symbols: [TQQQ]
    window: [950, 1030]
    context: [qqq_fo, breadth]
    scale_out_r: null
    tags: [near-miss, longs1020, forward-observation]
# config/setup_names.yaml
LD1-ns1-breadthup-t05s1-long: {name: "Oversold Pop with Breadth Turning Up", side: long}
LD2-qqq-dip015-breadthturn-tqqq-t05s1-long: {name: "Shallow Nasdaq Dip, Breadth Turn (TQQQ)", side: long}
```

## Method notes
- **Costs:** production R (`gates.prod_r`, time-of-day entry multiplier, +2c on stop fills), ×3 on the extended tier.
- **R:** 0.25 × daily ATR.
- **Exit sources:**
  - Part B t1s1 / t05s1 come from lab outcomes (entry at the bar close).
  - holdtr / time60 and all Part A exits come from a 1-minute simulator: entry at the next minute's open, stop checked first.
  - Simulator vs lab parity on 48,756 rows: mean −0.087 vs −0.087R (t1s1), correlation 0.96 (`parity.json`).
- **Controls:**
  - Part B holdtr / time60: a deterministic 1/20 sample of universe rows at the same minute.
  - Part A: C_all is a random bar 09:50–10:30 on every day. C_same is a random bar after the dip, on the same days.
- **A2 filter:** the A2 feature (recovery, chosen by the largest train AUC, from QQQ) duplicates the rec20 trigger in most rows. Those rows are identical to their parents but are still counted.
- **Regimes:** up / flat / down by the universe median open-to-close (open-history terciles).
- **Files:**
  - `scripts/`: common, build_index, build_frames, build_ctrl, sim, dipstats, part_a, part_b, select_cands, nearmiss, verify_*
  - `results_A.csv`, `results_B.csv`, `gate_check.csv`, `trades_A.csv.gz`, `dipdays.csv`, `predictors_rows_*.csv`, `nearmiss.json`, `backlog_proposals.jsonl`
  - The scratch data is outside the repo (about 100 MB, well under 1.5 GB).

Educational only — not financial advice.
