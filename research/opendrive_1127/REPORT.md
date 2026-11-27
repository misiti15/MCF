Educational only — not financial advice.

# OPENDRIVE_1127: are 09:35-09:45 opening-drive entries worth their extra cost? (verdict: FAIL)

## Plain-language summary
- **No. 0 of 24 configurations pass, and no early entry beats the same rule at 09:50 on both test periods.** Three
  rules based on how the market works (R1 opening-range drive with volume, R2 gap-and-go, R3 gap-fill), each tried at
  09:35 / 09:40 / 09:45 / 09:50, long and short, on the top 20 names of a K6-style mover score that only uses bars
  available at that time. Every early config loses money after costs on CHECK or T2 (most on both).
- **Entering earlier does get a better price before costs, but costs eat all of it.** Pooling all rules: at 09:35 the
  average trade makes **+0.048 R before costs on CHECK** (T2 +0.031) against +0.004 (T2 +0.014) at 09:50. After costs it
  is **−0.057 R at 09:35 vs −0.059 R at 09:50 on CHECK** (a tie) and **−0.113 vs −0.063 on T2** (09:35 worse). Costs per
  trade rise from 0.063 R to 0.105 R (CHECK) because early stops are tighter (median risk 3.1% vs 4.1% of price) and
  early spreads are wider.
- **The early lists catch fewer of the day's big movers, not more.** Share of the day's top-2% movers (open-to-close)
  that a rule trades the right way: CHECK **14.5% at 09:35 → 15.9% → 17.2% → 17.5% at 09:50**; T2 24.0% → 30.4%. For
  the move still left after 09:35 the gap is wider (CHECK 6.6% at 09:35 vs 11.2% at 09:50). Five more minutes of tape
  make the mover score sharper faster than the price runs away. The BDI "48 of 50 movers were decidable 09:35-09:45" is
  hindsight: at 09:35 the score cannot yet tell them from the many names that pop and stall.
- **What we can salvage:** (1) the list still picks better trades than random names under the same rule (control diff
  positive in most cells, e.g. R1-long 09:35 CHECK +0.149 R/trade, paired t 4.2; R2-long 09:35 +0.291, t 4.6) — the K6
  selection lift from MOVEHUNT holds at earlier times too; (2) right-way trades on movers make +0.6 to +1.5 R each and
  wrong-way trades on movers are rare (57-170 per period vs 1,100-1,400 right-way); **the loss comes from non-movers on
  the list (−0.28 to −0.38 R each)**, i.e. the problem is still "which of the listed names will actually go", not
  direction once they go.
- **Early costs are an assumption, said plainly:** no MCF live trade has ever entered before 09:49 (all 10 journals,
  115,993 entries), so 09:35-09:45 slippage cannot be measured. We charged an extra 7.6 bp at 09:35 and 2.2 bp at
  09:40/09:45 (method below). Even with **no** surcharge, pooled 09:35 is −0.024 R (CHECK) / −0.061 R (T2): still a loss.

## Data, splits, rules
1-min RTH bars: data/cache_hist (1,226 symbols; FIT 170 sessions, CHECK 276) and data/cache_fresh (468 symbols; T2 427,
EARLY 63 = 2022-10..12, descriptive). Locked block 2024-11-01..2025-02-28 never read (pyarrow filter + asserts in build.py
and score.py). No premarket bars: gap = 09:30 open vs prior close. Eligible: price ≥ $5 at T, adv20 ≥ $20M, ATR14 known,
≥ 75% of bars before T present. Shorts need easy_to_borrow (data/universe.csv snapshot, not point-in-time; disclosed).
Ranker at T: MOVEHUNT K6 inputs recomputed on 09:30..T−1 bars, FIT standardisation per T, **frozen MOVEHUNT coefficients**
(no new fitting on any target). Entry at the open of the T bar; stop = opposite extreme of the 09:30..T−1 range ∓ 1c,
widened to ≥ 0.15 ATR; stop-first on 1-min bars; time exit 15:55. Pre-registration: PREREG.md (commit 531914ae5b, pushed
before any build or score). Backtest only: no live trades of these rules exist, so no live window and no ledger rule
change to note.

**Costs.** LIVE-L (primshorts_1126 cells_live.json) plus an early surcharge = E × (m_T − 1) bp of price on the entry side.
E = 4.43 bp = live mean signed entry slip 09:49-09:59 (n 2,588, 3.43 bp, se 0.58) + 1 bp fees (slip_tod_out.txt). m_T =
max(measured median 1-min entry-bar range vs 09:50 — 24.9 / 20.0 / 19.4 / 16.2 bp → 1.54 / 1.23 / 1.20; gates ratio
2.71 / 1.5 / 1.5) → surcharge 7.59 / 2.22 / 2.22 / 0 bp. Harsh = double surcharge; LR8 alongside (gates tod multiplier).
Side note from the journals: live entry slip at 09:50-09:59 (3.4 bp) is **not** higher than later in the day (4.5-5.2 bp),
so the gates 2.1× / 1.4× early multipliers look conservative for 09:50 itself.
Stress: +1 minute entry (same stop) and +2 bp per side. **Bug fix (disclosed):** the first scoring run let a +1 minute
entry land a hair from the fixed stop (float risk ≈ 0 → R of −1e11 in two cells); the stressed trade now has to meet
MOVEHUNT's minimum risk (≥ 0.10% of price). This touches only the stress column; it changes no verdict.

## Configurations
24 (3 rules × 4 times × long/short; the 09:50 cells are the comparator). Cumulative ≈ 9,300 → ≈ 9,324. Bar: CHECK
day-clustered t ≥ 3.1 (Bonferroni for 24), T2 ≥ 2.0, plus costs, one-big-day, control, stress and beats-09:50 gates.

## Every config (LIVE-L incl. surcharge, avg R/trade; n; day t) — all FAIL
| Config | CHECK n, avg, t | T2 n, avg, t | LR8 CHECK / T2 | gross CHECK / T2 | ctrl diff CHECK (t) | vs 09:50 R/session CHECK / T2 (t) |
|---|---|---|---|---|---|---|
| R1 long 09:35 | 1337, −0.047, −1.5 | 1943, −0.106, −3.4 | +0.010 / −0.039 | +0.045 / +0.023 | +0.149 (4.2) | +0.09 (0.6) / −0.23 (−1.7) |
| R1 short 09:35 | 1130, −0.020, −0.6 | 1525, −0.129, −3.9 | +0.033 / −0.074 | +0.069 / −0.005 | +0.122 (3.0) | +0.13 (1.1) / −0.10 (−0.9) |
| R2 long 09:35 | 1028, −0.023, −0.4 | 1301, −0.122, −2.6 | +0.041 / −0.054 | +0.090 / +0.036 | +0.291 (4.6) | +0.13 (0.8) / −0.18 (−1.4) |
| R2 short 09:35 | 763, −0.125, −2.3 | 1044, −0.130, −2.3 | −0.066 / −0.069 | −0.009 / +0.031 | +0.231 (3.4) | −0.23 (−1.8) / −0.07 (−0.6) |
| R3 long 09:35 | 606, −0.008, −0.1 | 877, −0.125, −2.4 | +0.047 / −0.044 | +0.107 / +0.032 | +0.223 (3.1) | +0.18 (1.5) / −0.26 (−2.5) |
| R3 short 09:35 | 697, −0.152, −3.2 | 867, −0.060, −1.0 | −0.101 / −0.003 | −0.029 / +0.101 | +0.138 (2.3) | −0.29 (−2.3) / −0.13 (−1.1) |
| R1 long 09:40 | 1340, −0.034, −1.3 | 1893, −0.097, −3.6 | +0.003 / −0.062 | +0.033 / −0.010 | +0.094 (3.0) | +0.15 (1.2) / −0.18 (−1.7) |
| R1 short 09:40 | 1125, −0.031, −1.2 | 1544, −0.080, −2.9 | +0.006 / −0.050 | +0.036 / +0.004 | +0.053 (1.6) | +0.08 (0.8) / +0.07 (0.8) |
| R2 long 09:40 | 1026, −0.098, −2.6 | 1292, −0.079, −2.1 | −0.061 / −0.048 | −0.018 / +0.024 | +0.080 (1.6) | −0.15 (−1.3) / −0.05 (−0.5) |
| R2 short 09:40 | 717, −0.042, −0.9 | 1055, −0.093, −2.0 | −0.009 / −0.067 | +0.043 / +0.012 | +0.130 (1.7) | +0.00 (0.0) / +0.02 (0.2) |
| R3 long 09:40 | 589, −0.070, −1.5 | 775, −0.015, −0.3 | −0.038 / +0.025 | +0.011 / +0.091 | +0.095 (1.4) | +0.05 (0.5) / −0.03 (−0.4) |
| R3 short 09:40 | 644, −0.095, −1.9 | 801, −0.021, −0.4 | −0.067 / −0.002 | −0.011 / +0.083 | +0.114 (2.0) | −0.12 (−1.3) / −0.04 (−0.6) |
| R1 long 09:45 | 1376, −0.061, −2.7 | 1841, −0.078, −3.1 | −0.023 / −0.041 | +0.003 / +0.004 | +0.078 (2.9) | +0.01 (0.1) / −0.09 (−1.0) |
| R1 short 09:45 | 1141, −0.062, −2.6 | 1571, −0.108, −3.9 | −0.025 / −0.076 | +0.001 / −0.028 | +0.038 (1.4) | −0.05 (−0.6) / −0.04 (−0.5) |
| R2 long 09:45 | 1037, −0.014, −0.3 | 1266, −0.044, −1.1 | +0.023 / −0.011 | +0.064 / +0.056 | +0.134 (2.9) | +0.16 (1.6) / +0.06 (0.7) |
| R2 short 09:45 | 665, −0.072, −1.6 | 1047, −0.122, −3.1 | −0.038 / −0.095 | +0.008 / −0.022 | +0.068 (1.0) | −0.06 (−0.8) / −0.05 (−0.8) |
| R3 long 09:45 | 588, −0.160, −4.1 | 759, −0.001, −0.0 | −0.132 / +0.036 | −0.083 / +0.101 | +0.045 (0.8) | −0.14 (−2.3) / −0.01 (−0.1) |
| R3 short 09:45 | 641, −0.060, −1.3 | 790, −0.011, −0.2 | −0.031 / +0.010 | +0.021 / +0.087 | +0.161 (2.8) | −0.04 (−0.5) / −0.02 (−0.4) |
| R1 long 09:50 | 1337, −0.065, −2.9 | 1802, −0.060, −2.4 | −0.026 / −0.025 | −0.008 / +0.009 | +0.022 (0.9) | — |
| R1 short 09:50 | 1158, −0.050, −2.4 | 1547, −0.099, −4.1 | −0.014 / −0.068 | +0.007 / −0.032 | +0.029 (1.1) | — |
| R2 long 09:50 | 1018, −0.058, −1.6 | 1275, −0.064, −1.8 | −0.021 / −0.032 | +0.011 / +0.019 | +0.091 (2.2) | — |
| R2 short 09:50 | 667, −0.047, −1.1 | 1059, −0.099, −2.3 | −0.014 / −0.073 | +0.022 / −0.014 | +0.055 (0.9) | — |
| R3 long 09:50 | 572, −0.096, −2.3 | 692, +0.002, +0.0 | −0.065 / +0.040 | −0.027 / +0.087 | +0.063 (1.0) | — |
| R3 short 09:50 | 618, −0.044, −1.1 | 728, +0.002, +0.0 | −0.014 / +0.021 | +0.025 / +0.083 | +0.154 (2.7) | — |
One-big-day: every CHECK total is negative (best-day share undefined; avg without the best day is lower still). The only
positive cells are T2 R3 at 09:50 (+0.002, 1-day carried: best-day share 776% / 1,982%) and EARLY (63 sessions, n 54-82,
e.g. R3-long 09:50 +0.37, t 2.0): too small to count. Stress (+1 min, +2 bp): negative on CHECK and T2 for every config
except R1-short 09:35 CHECK (+0.05, T2 −0.16). Family split (CHECK+T2, LIVE-L): of 18 early configs × 5 cells, the only
positive cells are R3 price < $20 (long 09:35 +0.29, 09:40 +0.11; short 09:40 +0.06) and R3-long 09:40 gap < 1 ATR (+0.008) — small subsets, one rule family,
not pre-registered as a filter. Gap ≥ 1 ATR is less negative than gap < 1 ATR in 12 of 18 early configs.

## Pooled by entry time (all three rules, both sides; LIVE-L)
| Time | CHECK avg / gross / cost / no-surcharge / LR8 | T2 avg / gross / cost | CHECK capture right-way (on list) | T2 capture right-way |
|---|---|---|---|---|
| 09:35 | −0.057 / +0.048 / 0.105 / −0.024 / +0.000 | −0.113 / +0.031 / 0.144 | 14.5% (18.6%) | 24.0% (34.0%) |
| 09:40 | −0.058 / +0.018 / 0.076 / −0.050 / −0.023 | −0.073 / +0.023 / 0.096 | 15.9% (20.3%) | 27.6% (37.4%) |
| 09:45 | −0.064 / +0.008 / 0.072 / −0.057 / −0.029 | −0.070 / +0.021 / 0.091 | 17.2% (21.3%) | 29.3% (39.3%) |
| 09:50 | −0.059 / +0.004 / 0.063 / −0.059 / −0.024 | −0.063 / +0.014 / 0.076 | 17.5% (22.0%) | 30.4% (40.7%) |
Right-way trades on movers: 09:35 CHECK n 1,215, +1.09 R each; 09:50 n 1,416, +0.60 R (earlier = bigger slice of the
same move, fewer of them). Non-movers on the list: −0.36 R (09:35) vs −0.28 R (09:50) each, and they are ~75% of trades.

## Finalists (all reported)
All 24 configs above; none passes. Gates failed by every early config: costs, t, one-big-day, stress, beats-09:50.
Control passes for 10 of 18 early configs (the list selects better than random) — selection, not edge.

## Verdict: FAIL
The early window adds gross R (about +0.04 R/trade at 09:35 on CHECK) but costs about +0.04 R more and catches fewer
movers. Not worth its extra cost under these rules. Reason for optimism: the gap is small and is entirely about
non-movers on the list; anything that cuts that 75% share (a better "will it really go" filter) would help the 09:50
and the 09:35 versions alike.

## Backlog proposal (for the synthesis step; not written to research/backlog.jsonl here)
`{"id": "OD-EARLYQUOTE", "title": "Log-only: record NBBO spread for K6-listed names at 09:35/09:40/09:45",
"idea": "Extend the SPREADFLOOR shadow recorder to snapshot quotes for the K6-at-T top-20 at 09:35-09:45 (no orders), so
early-entry cost is measured instead of assumed (OPENDRIVE charged 7.6 bp at 09:35 with no live data).",
"evidence": "research/opendrive_1127/REPORT.md: pooled 09:35 gross +0.048 R CHECK; net −0.057 with surcharge, −0.024
without; no live entry before 09:49 in 115,993", "kind": "housekeeping-logging", "status": "proposed"}` — only worth
doing if a later study finds an early rule that is positive before the surcharge.

## Files
build.py (per symbol-day window features and both-direction trades at each T; work files in scratch, deleted),
score.py, results.json, score_out.txt, slip_tod.py + slip_tod_out.txt (journal slippage by minute), PREREG.md (+ sha256).
