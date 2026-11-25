Educational only — not financial advice

# Project Pyramid round 2 — Team G: gate the tape, grow from live (2026-11-25)

Research only. Pre-registered and hashed (scratchpad/pyramid/G/PREREG.md, 00:15 UTC): 10 configs (5 candidates × gates TT1/TT0) + 1 flagged post-hoc diagnostic; cumulative N ≈ 1,917 (t bar ≈ 3.89). bench10 splits, LR8 research basis, testing book, entries ≥ 09:50. Locked block never read.

TT1 gate (point-in-time on SPY 1-min bars): SPY above session VWAP now, it traded ≥ 0.05% below VWAP earlier (since 09:35), and SPY's 30-min return > 0. TT0 = without the "was below" part.

## Part 1 — does the tape-turn gate make an ultimate long?
No. Only B3 TREND-CLOSE-DRIFT + TT1 passes the pre-registered test, and only by the letter:
| Config | Fit | Check (w/o best day) | 2023-24 | Verdict |
|---|---|---|---|---|
| B3 + TT1 | +0.013 (best day 516%) | +0.112 (+0.077), t 1.55, 23 traded sessions | +0.014 (best day 494%) | TIER A by the letter → treated as TIER B: 23-day basket, one-day fit/T2, TT0 erases it (+0.005), misses the top-10 2023-24 bar (+0.034) |
| NM-ETF-late-dip + TT1 | +0.290 | +0.087 (+0.040) | −0.031 | TIER B; live gated 20 tr +0.355 vs blocked 79 tr −0.289 |
| GEN-261027-01 + TT1 | +0.052 | +0.016 (−0.020) | +0.020 | TIER B / fails pass test |
| C3 OR20-RECLAIM + TT1 | +0.153 | −0.028 | +0.026 | FAIL |
| GEN-261019-02 + TT1 | −0.012 (12 tr) | +0.120 (59 tr) | −0.427 | FAIL |
The gate's lift beyond random long bars is real on check (+0.01..+0.14) but ≈ 0 on 2023-24 — mostly a bet on the tape.

## Part 2 — why live beats the backtest (diagnostic)
- GEN-261027-01 (Late Pullback Buy): no engine bias. 22 of its 39 live trades are inverse/volatility ETPs (UVXY, VXX, SQQQ, SOXS, …) at +0.493R; its 17 stock trades make +0.033R (close to the engine's −0.026). 11-23/11-24 carry 73% of its R. The engine on the ETP subset shows no stable edge (check −0.085). Live is a 9-session, two-down-day ETP record → do not treat it as an ultimate; its On Deck case (ODP2) is weaker than it looked.
- L3-gap-slope-fromopen-FD: same symbols and bars (99.4% same-bar match). The ~0.07R/trade gap is mainly the research cost model (0.087R vs live LR8 0.043R; worst on sub-$20 names) and a live window the engine itself ranks in its best 3%. Primary rules (−2R latch, cap 30) turn raw −0.245R into +0.122R in-window; non-ETB signals replay at −0.516R and halted ones at −0.763R.
- Systematic bias found: the research cost model is ~0.04–0.09R/trade too harsh on sub-$20, small-stop names (mainly the gap-down short family). L3-fromopen's check would be ≈ −0.025 — still not positive. None of the round-1 or ultimate_1119 long candidates flips.
- Round-1 bug: L3 team's walk function is long-only, so its Primary reference-book short rows are wrong (book-correlation / worst-day figures in L3_REPORT are invalid; its long-candidate rows are fine).

## Next (backlog)
Re-score the gap-down short family with live-LR8 costs (housekeeping); forward-test NM-ETF + TT1 as a journal-only tag (20 sessions); do not pursue GEN-261027-01 as an ultimate; flag the L3 walk bug.
