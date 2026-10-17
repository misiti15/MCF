# swarm1017 / rework-cwt — results (2026-10-17)

*Educational only — not financial advice. Lab backtests on the open two-year history (train 2024-10 + 2025-03..2025-12,
valid 2026-01-01..2026-10-07; the locked block 2024-11..2025-02 was never loaded). Costs in (production haircut plus
time-of-day entry costs). Live numbers are Testing 2 paper fills and are labelled as such (rule 7).*

## Failures first

- **No variant of CWT04 / CWT05 / CWT09 / CWT12 / CWT13 passes. Candidates: 0.** I scored 115,204 configurations, plus
  38 parent re-scores.
- Every gate except the try-count bar was passed by **30 configurations** (`finalists.csv`, labelled near-miss). Their
  best day-clustered t is **2.58**, and the family bars are 4.43-5.07. With 115k tries, pure noise is expected to reach
  t ≈ 4.8. So the near-misses are what noise looks like, not evidence of an edge.
- The raw scan shows high t values: B1 up to t 110, A7 up to t 4.46, and 739 configurations with t ≥ 3 at n ≥ 200.
  These are **concentration artifacts**. They come from configurations whose trades sit mostly on 2025-04-07 and the
  other tariff-crash sessions; one example has 427 of 504 trades on 2025-04-07. One configuration first passed the
  pre-declared screen this way (B1 a1.5-d0.3-T1, long, tr1, gap<-2). The concentration gate (rule 5) was added
  after that first look: expectancy without the best day must be > 0, and no single day may hold more than 20% of the
  trades. Of the 290 configurations checked, 181 fail it.
- **Parents re-scored** (`parents.json`): all 19 parents reproduce their published n exactly with the earnings
  blackout off (for example lh-a15 n 1,212, coil-k4 44,505, z05-short 16,165). With the live earnings blackout on:
  - B2 / B4 / B5 stay negative: -0.04 to -0.15R, with t from -1.2 to -5.7.
  - CWT04-lh-a25 rises to +0.486R, t 3.33, but on only 93 trades (n < 200), and its valid expectancy is +0.009.
  - CWT04-lh-a15 is +0.282R, t 1.36, but **valid is -0.129**.
  - CWT09-g10 pair: +0.10 / +0.16R, t 0.93 / 0.70, with **train negative** for the T2 version.
- **Live week, Testing 2 paper, 10-12..10-16** (research/swarm1017/week/setups_live.csv): this family took **387 trades,
  -$1,523.33, -0.232R a trade**.
  - CWT09: 76 trades, -0.618R, -$984 (history about 0).
  - CWT12: 213 trades, -0.086R.
  - CWT13: 72 trades, -0.254R.
  - CWT05: 23 trades, -0.209R.
  - CWT04: 3 trades.
  - Live is worse than the backtest for CWT09 and CWT13-z05-short. The other families are in line with their
    negative history.

## What was run (PLAN.md, pre-declared)

- **Kernels.** The `kern.py` numba ports of `cwt_live_lib` match the live signal code exactly at every parent
  parameter (`parity.json`: 38 of 38 checks over 2 months, ref = mine = both). The exit simulator matches the frame
  geometries on 99.998% of rows (`build_meta`, build_meta.json).
- **Grids:**
  - **A:** 99 kernel variants × parent / opposite side × 7 exits (+S for A7) × 5-6 windows × first / refire.
  - **B:** every variant × 40 context filters × 2 sides × 6 exits × parent / full window.
  - **C:** 19 parent variants × 780 filter pairs × parent side × 2-3 exits.
- **Configurations per family:** B1 33,240 | B2 17,744 | B4a 20,820 | B4b 11,480 | B5 16,160 | A7 15,760 =
  **115,204**.
- **Bars,** max(1.5, sqrt(2 ln N_lineage)), with the prior lineage from research/bdi:
  - B1: 356,381 + 33,240 → **5.07**
  - B2: 272 + 17,744 → **4.43**
  - B4 (coil + flag): 354 + 32,300 → **4.56**
  - B5: 31,290 + 16,160 → **4.64**
  - A7: ~83,300 + 15,760 → **4.80**
- **Gate funnel** (`counts.json`, `verify.csv`):

  | stage | configurations left |
  |---|---|
  | n ≥ 200 | 65,594 |
  | + train and valid > 0 | 1,764 |
  | + regime (up and down > 0) | 332 |
  | + beats same-minute random | 290 |
  | exact re-check with mcf.research.gates (290 checked): | |
  | fail concentration | 181 |
  | fail walk-forward ≥ 0.6 | 171 |
  | fail plateau | 129 |
  | fail t bar | 269 |
  | pass all but t | **30** |
  | **pass all** | **0** |

- **Where the families sit** (n ≥ 200, median expectancy after costs): every family and side is between -0.05 and
  -0.11R.
  - Share of configurations with exp > 0: B1 26%, A7 23%, B4b 6%, B2 4%, B5 4%, B4a 2%. B1 and A7 are mostly the
    April-2025 concentration.
  - The opposite side does not rescue any family: the medians are about the same on both sides. Costs eat the
    entire move, the same finding as research/swarm1010.

## Best near-misses (all FAIL the bar; `finalists.csv`)

| # | family / variant | side | exit | window | filters | n | exp R (train / valid) | t (bar) | up / down | WF | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | A7 g5-T1 | short | t05s1 | 10:30-15:00 | fo<0 & sma50>0 | 708 | +0.125 (0.188 / 0.031) | 2.58 (4.80) | +0.024 / +0.167 | 0.73 | valid weak |
| 2 | A7 g10-T1 → module NM1 | short | t1s1 | 10:30-15:00 | fo<0 & slope>0 | 241 | +0.191 (0.177 / 0.204) | 2.49 (4.80) | +0.168 / +0.263 | 1.00 | live-implementable |
| 3 | B5 m1.25-v3 → module NM2 | **short (opposite)** | t05s1 + scale-out 0.25 | 11:30-13:00 | none | 226 | +0.088 (0.107 / 0.052) | 2.43 (4.64) | +0.147 / +0.140 | 0.71 | continuation of a deep flush |
| 4 | B2 above-z0.75 | short | t1s1 | 11:00-15:00 | atr_hi & Fri | 224 | +0.169 (0.217 / 0.014) | 2.36 (4.43) | +0.220 / +0.186 | 0.60 | day-of-week pair: likely noise |
| 5 | B2 above-z0.5 | short | t1s1 | 11:00-15:00 | SPY fromOpen>0.3 & Fri | 1,609 | +0.151 (0.160 / 0.128) | 2.22 (4.43) | +0.137 / +0.553 | 0.64 | needs SPY code + Friday; likely noise |

Modules (lab format, near-miss hypotheses only, NOT candidates):
- `modules/NM1-cwt09-g10-vwaploss-fodn-slopeup-short.py`: type lab, min_adv $1M, window [1030, 1500], t1s1.
- `modules/NM2-cwt05-flush-m125-v3-continuation-short.py`: type lab, min_adv $95M, window [1130, 1300], t05s1,
  scale_out_r 0.25, live_scale_out true.
- Parity is in `verify_modules.json`: every scan trade is reproduced by the module on 4 months. The module's extra
  hits are earnings-blackout days, which the live runner blocks.
- Both use only frame features the LabStrategy frame carries.

## Live-runner notes

- **t05s05:** not in LabStrategy.GEOMS, so it needs code. It was in grid A only and produced no near-miss.
- **Scale-out (so1 / so05):** live supported with `live_scale_out: true` and the setup's own `scale_out_r`.
- **Trail (tr1):** the Signal trail_r / trail_after_r. The simulator manages on 5-minute bars, while the runner
  manages each minute.
- **Structural S (A7):** supported through GEOM "S" and stop_price.
- **SPY / breadth / SPY-gap filters:** these 12 filters need live code, because the lab frame has no index or
  universe context. Day-of-week can be read from the frame index.

## Files

- `PLAN.md`
- `kern.py`, `sim.py` (copy of rework-cwt14/sim.py), `build.py`
- `parity.py` → `parity.json`
- `parents.py` → `parents.json`
- `scan.py` → `scan_all.csv.gz`: every configuration
- `gate.py` → `results.csv` (290 screened) and `counts.json`
- `verify.py` → `verify.csv` and `finalists.csv` (30 near-misses)
- `verify_modules.py` → `verify_modules.json`
- `modules/`

The scratch event tables (390 MB) were deleted after the run. Rebuild them with `python build.py <dir>` (about 1 minute
on 3 CPUs).
