# GAPNEWS_1127: can we tell which way the 09:50 big movers will go? (verdict: FAIL)

**Educational only — not financial advice.**

## In plain words
- **No. We still can't call direction inside the K6 high-mover list.** 13 pre-registered direction rules were tested on
  the frozen K6 top-50 list: gap direction, gap x first-20-minute continuation/reversal, opening-range position, strength
  vs a sector ETF, prior-day close location, VWAP side, first-bar volume imbalance, 5- and 20-day trend, a vote, and a
  FIT-frozen logistic model. **None has direction skill on CHECK or T2.** All |t| < 1.5, hit rates 48.3-50.8%
  (CHECK 48.3-49.8%, T2 48.5-50.8%). The rules that looked best on FIT (VWAP side t 2.4, prior-day close fade t 2.4,
  logit t 2.6) shrink to about 0 out of sample. Direction is a coin flip.
- **The 3 directional setups lose money after costs** (CHECK -0.061 to -0.124 R/trade, T2 -0.071 to -0.086, all day
  t <= -2.7). Before costs they make about 0 (-0.035 to +0.032 R/trade).
- **The direction-neutral structure fails too.** An OCO bracket (buy-stop above / sell-stop below the 09:30-09:49 range,
  first trigger wins, 09:50-11:29, stop at the range midpoint (N1) or the opposite extreme (N2), exit 15:55) is a real
  stock-only order structure. It made about 0 before costs and **-0.049 to -0.085 R/trade after LIVE-L** (N2 CHECK -0.049,
  T2 -0.055, t -4.8 / -5.0). 0 of 5 setups pass.
- **What we can still use:** the K6 list "beats random names" by +0.04 to +0.08 R/trade after costs here too. But the
  before-costs check shows **this is cost arithmetic, not stock picking.** Before costs the gap is 0 (t -0.5 to +0.3). K6
  names have about 3x wider stops (SA median risk 367 bp vs 112 bp for the pool on CHECK), so fixed costs weigh less per R.
  That is the same result the MOVEHUNT skeptics found. The useful lesson matches STOPFLOOR: **wide-stop trades on
  high-range names keep cost per R low.** That helps any setup that already has a direction signal. It is not a setup
  on its own.

## Setup and rules
Pre-registration: `PREREG.md`, committed and pushed (9584917ed0) before anything was built or scored.
- **List:** K6 = MOVEHUNT logistic ranker. It was refit on FIT with the identical code, and the code asserts that it
  reproduces MOVEHUNT's coefficients to 3 dp (it does).
- **Data:** 1-min RTH bars. data/cache_hist covers FIT (141 sessions) and CHECK (276). data/cache_fresh covers T2 (427)
  and EARLY 2022-11/12 (43 sessions after warm-up; extra out-of-sample).
- **Locked block:** 2024-11-01..2025-02-28 was never read (pyarrow filter + asserts in build.py and score.py).
- **Sector ETF:** point-in-time, chosen as the highest 60-session return correlation among 14 sector ETFs. It covers
  95.8% of top-50 names.
- **Shorts:** need easy_to_borrow. This uses the current universe.csv snapshot, which is not point-in-time (disclosed).
- **Bracket:** runs on ETB names only, so that both orders can be placed.
- **Costs:** LIVE-L (primshorts_1126 cells_live.json) is the scored basis; LR8 is shown alongside.
- **Code check:** the score code was smoke-tested on a 58-symbol subset before the full run. That subset is not the
  study universe and nothing was tuned on it.
- **Live window:** no live trades of these rules exist, so there is no live window and no ledger rule change to note.

## Configurations
18 this study: 13 direction rules + 3 directional setups + 2 neutral brackets. Cumulative N goes from about 9,176 to
about 9,194. Pass bar: day t >= 3.0 on CHECK and >= 2.0 on T2 (Bonferroni 0.05/18 one-sided, z = 2.77, rounded up).
A lineage claim would need t >= 4.3. `ctrl_gross.py` is a descriptive before-costs check of the control, not a new
configuration.

## Direction screen (K6 top-50; y = remaining move after 09:50 in ATR, signed by the rule's call; orientation fixed on FIT)
| Rule | orient | FIT y (t) | CHECK y (t), hit | T2 y (t), hit | EARLY y (t) |
|---|---|---|---|---|---|
| R1 gap sign | fade | +0.003 (0.1) | -0.009 (-0.9), 49.8% | +0.001 (0.1), 50.8% | +0.007 (0.2) |
| R2 first-20 continuation | follow | +0.016 (1.0) | +0.000 (0.0), 48.6% | +0.000 (0.0), 49.1% | +0.006 (0.3) |
| R3 gap-and-go (gap = first move) | follow | +0.012 (0.4) | +0.010 (0.7), 49.0% | -0.001 (-0.1), 48.5% | +0.001 (0.0) |
| R4 gap being reversed | follow reversal | +0.020 (0.8) | -0.010 (-0.8), 48.3% | +0.000 (0.0), 49.7% | +0.013 (0.3) |
| R5 opening-range position | follow | +0.024 (1.6) | +0.000 (0.0), 48.9% | -0.004 (-0.6), 48.9% | -0.013 (-0.6) |
| R6 RS vs sector ETF | follow | +0.007 (0.5) | +0.003 (0.3), 48.9% | +0.003 (0.4), 49.2% | +0.025 (1.1) |
| R7 prior-day close location | fade | +0.050 (2.4) | -0.014 (-1.5), 49.4% | -0.009 (-1.1), 49.8% | +0.010 (0.3) |
| R8 VWAP side at 09:50 | follow | +0.035 (2.4) | -0.002 (-0.2), 48.9% | -0.010 (-1.2), 48.6% | -0.015 (-0.7) |
| R9 first-20 volume imbalance | follow | +0.007 (0.5) | +0.007 (0.8), 49.8% | +0.003 (0.5), 49.3% | +0.008 (0.4) |
| R10 5-day trend | fade | +0.016 (0.8) | -0.006 (-0.6), 49.8% | +0.004 (0.5), 50.5% | +0.030 (1.5) |
| R11 20-day trend | fade | +0.007 (0.3) | -0.012 (-1.3), 49.1% | -0.005 (-0.5), 49.6% | -0.010 (-0.4) |
| R12 vote | follow | +0.006 (0.3) | +0.002 (0.2), 49.2% | -0.003 (-0.4), 48.8% | -0.006 (-0.3) |
| R13 direction logit (FIT-frozen) | follow | +0.062 (2.6) | +0.003 (0.3), 49.7% | +0.007 (0.8), 50.8% | -0.003 (-0.1) |

Each period has about 7,000 (FIT), 13,800 (CHECK), 21,300 (T2) and 2,100 (EARLY) names; R3/R4 cover about half of
them and R13 covers 1,100 in EARLY. 0 of 13 rules meet the skill bar. On the top-20 list the largest out-of-sample value
is +0.035 ATR (R3 CHECK), which reverses on T2 (+0.000).

**Gap x first-20 cells** (y = remaining move signed by the first-20-minute direction, CHECK / T2):

| Cell | CHECK y (t) | T2 y (t) |
|---|---|---|
| Gap up, still going up | +0.019 (0.9) | +0.015 (0.8) |
| Gap up, reversing down | +0.001 (0.1) | -0.012 (-0.6) |
| Gap down, still going down | -0.003 (-0.1) | -0.021 (-1.1) |
| Gap down, reversing up | -0.023 (-1.0) | +0.013 (0.7) |

There is no stable cell.

## Setups (K6 top-20, entry 09:50 open, exit 15:55; LIVE-L avg R/trade, LR8 in brackets; day-clustered t)
| Setup | FIT | CHECK n, avg, t | T2 n, avg, t | EARLY n, avg | Gross CHECK / T2 | +1 min / +2bp CHECK, T2 | Random-direction diff (paired t) CHECK / T2 |
|---|---|---|---|---|---|---|---|
| SA = R8 VWAP side, range stop | -0.022 | 5,456, -0.061 (-0.026), -5.1 | 8,490, -0.071 (-0.041), -5.6 | 845, -0.114 | +0.004 / +0.009 | -0.060, -0.073 / -0.075, -0.093 | +0.026 (1.1) / +0.025 (1.3) |
| SB = R13 logit, range stop | +0.019 | 5,445, -0.064 (-0.045), -2.7 | 8,489, -0.086 (-0.080), -4.2 | 430, -0.101 | +0.029 / +0.032 | -0.094, -0.102 / -0.095, -0.132 | +0.025 (1.2) / +0.012 (0.6) |
| SC = R13 high-confidence, 0.5 ATR stop | +0.060 | 1,807, -0.124 (-0.090), -3.6 | 3,013, -0.083 (-0.057), -2.9 | 170, -0.092 | -0.035 / +0.016 | -0.118, -0.092 / -0.149, -0.115 | -0.000 (0.0) / +0.022 (0.8) |
| N1 OCO bracket, midpoint stop | +0.030 | 3,681, -0.076 (-0.040), -4.2 | 6,277, -0.085 (-0.060), -4.3 | 639, -0.021 | +0.002 / +0.014 | -0.075, -0.099 / -0.095, -0.117 | n/a (size-matched +0.066 / +0.061) |
| N2 OCO bracket, opposite-extreme stop | +0.001 | 3,682, -0.049 (-0.011), -4.8 | 6,277, -0.055 (-0.021), -5.0 | 639, -0.028 | +0.008 / +0.012 | -0.051, -0.063 / -0.058, -0.071 | n/a (size-matched +0.041 / +0.038) |

- **One-big-day:** every CHECK/T2 total is negative, so the best-day share is undefined. Avg R without the best day is
  lower still (SA -0.064 / -0.073, N2 -0.051 / -0.058). The positive FIT totals are carried by single days: SB best-day
  share 146%, SC 175%, N2 3,535%, all `1 day`.
- **Gates:** 0 of 5 setups pass. All 5 fail costs, t, one-big-day and stress. The directional setups also fail the
  random-direction control; N1 and N2 pass only the size-matched control, which is explained below.
- **Bracket:** it triggers on 71.7% of top-20 names. Both sides triggering in one bar happened 0% of the time.

**Size-matched control before costs** (`ctrl_gross.py` -> `ctrl_gross.json`):

| Setup | Split | Gap after costs (paired t) | Gap before costs (paired t) |
|---|---|---|---|
| SA | CHECK | +0.053 (3.0) | -0.002 (-0.1) |
| SA | T2 | +0.064 (3.7) | +0.005 (0.3) |
| N2 | CHECK | +0.041 (2.6) | -0.002 (-0.1) |
| N2 | T2 | +0.038 (2.5) | -0.008 (-0.5) |

Median stop width is 367 / 220 bp for SA list names vs 112 / 79 bp for pool names (CHECK / T2). The bracket shows the
same pattern: 485 / 288 bp vs 147 / 103 bp. **So the gap is the stop width (lower cost per R), not stock selection.**

**Effect split** (CHECK+T2 pooled, LIVE-L). Each setup has 7 cells: long, short, gap >= 1 ATR%, gap < 1 ATR%,
price < $20, $20-100, $100+. All 35 cells are negative.

| Setup | Range of cell averages (R/trade) | Best cell |
|---|---|---|
| SA | -0.049 to -0.080 | — |
| SB | -0.046 to -0.125 | — |
| SC | -0.071 to -0.124 | — |
| N1 | -0.048 to -0.102 | — |
| N2 | -0.024 to -0.066 | price < $20, -0.024 |

The earnings-like gap >= 1 ATR% cell is not better: SA -0.049 vs -0.076, N2 -0.048 vs -0.055.

## Finalists (all reported)
| Finalist | Result |
|---|---|
| R1..R13 | no direction skill (0/13) |
| SA, SB, SC | FAIL |
| N1, N2 | FAIL |

## Verdict: FAIL
Direction inside the 09:50 high-mover list is about a coin flip with all six requested feature families, alone, combined
and in a fitted model. The straddle-like OCO bracket is break-even before costs and loses about 0.05-0.09 R/trade after
LIVE-L. With optimism, what is left:
1. K6 is still a good **size** finder.
2. High-range names carry wide stops and so lower cost per R. That matters only for setups that already have a direction
   edge.

The next direction source has to come from outside 09:50 price/volume. Examples: news or earnings catalyst type, or
options flow. None of these is in the repo's history.

## Backlog proposal
None. No passed idea. A data idea, not tested: collect a point-in-time catalyst tag (earnings/news) to test direction in
the K6 list forward.

## Files
| File | What it does |
|---|---|
| `build.py` | Features, target and candidate trades per symbol-day. Work files went to the scratchpad and were deleted. |
| `score.py` | Direction screen, setups, controls, stress. |
| `ctrl_gross.py` | Before-costs control check. |
| `results.json`, `score_out.txt`, `ctrl_gross.json` | Outputs. |
| `PREREG.md` (+ `.sha256`) | Pre-registration. |

Educational only — not financial advice.
