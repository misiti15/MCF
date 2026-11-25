Educational only — not financial advice

# Project Pyramid (owner "national project", 2026-11-24/25): rounds 1-2 summary

Goal (owner): the "ultimate 5" — about 3 longs + 2 shorts, clear-cut better than the current top 10, working in most conditions.

Result after 2 rounds, 7 teams, ~70 pre-registered configs (cumulative job N ≈ 1,917; 82 candidates including ultimate_1119's 35): **0 setups reach the ultimate bar. Nothing deployed; no config change.**

| Report | Lane | Outcome |
|---|---|---|
| X_REPORT.md | evidence: long vs short; two-account design | Longs/shorts move at the same speed in R; shorts are sharper only against us; long/short daily R correlation −0.3..−0.7 → 60% longs cut worst-5 days ~35% if longs ≥ break-even. Two accounts don't change ticker overlap (worst days are breadth, not stacking); test a "day-owner" tag first. |
| S_REPORT.md | the 2 best shorts | TIER B: L3-gap-slope-fromopen-FD (best live short, fails lab check) and GEN-261029-06 Late Quiet-Day Short (only short meeting the lab standard in both halves; live `1 day`). |
| L1_REPORT.md | rotation / relative-strength / opening-drive longs | 0/3; bets on the tape turning up; confirmation entries come too late. |
| L2_REPORT.md | buy-the-flush longs | 0 TIER A; NM-ETF + "SPY ≥ open" gate TIER B (low volume); capitulation seed is a loser overall. |
| L3_REPORT.md | live-mined + momentum longs | 0 TIER A; breakout longs fail; its book-correlation figures are invalid (long-only walk bug, see G). |
| E_REPORT.md | 09:35–09:50 early-entry longs (research exception) | 0/3; costs and noise; no edge over random. |
| G_REPORT.md | tape-turn gate; live-vs-backtest gap | Gate adds lift on check, ~0 on 2023-24; B3+TT1 TIER B only. Late Pullback Buy's live edge is mostly inverse/vol ETPs on 2 days. Research cost model ~0.04–0.09R too harsh on sub-$20 names. |

## Standing TIER B list (forward-test only)
Shorts: L3-gap-slope-fromopen-FD; GEN-261029-06. Longs: NM-ETF-late-dip-di-long with a SPY-tape gate ("SPY ≥ open" or TT1); B3 TREND-CLOSE-DRIFT + TT1; GEN-261019-02 (low-rep).

## Honest read
On the data we have, no rule-based intraday long beats our top 10 after costs in both halves of the backtest. Every long candidate's R is driven by whether the market turns up, so the most promising path is a well-tested long-side *market gate* plus the few longs already working live, grown by forward testing — not a new backtest-built "ultimate". Next steps (backlog): re-score the gap-down short family with live-LR8 costs; journal-only forward tags for NM-ETF + gate and the day-owner rule; extended-hours data only if a pre-open predictor is wanted.

## Round 3 (2026-11-25) — R3B_REPORT.md, R3N_REPORT.md, R3C_REPORT.md
- B (best 5-setup book vs the top 10): no book clearly beats the top 10 out of sample (best book one-day carried; worse worst-5 days; paired t 1.18–1.33). The long/short hedge exists only against the gap-down shorts.
- N (300-draw generator search with honest fitness): 0 of 300 pass; "SPY ≥ open at entry" does not stop gated longs losing on down-closing days; non-gap-down shorts show no edge.
- C (live-calibrated costs): corrects round 2 G — overall the research cost model is ~0.042R per trade too LENIENT (too harsh only on $5–20 names). No verdict improves; 5 drop to FAIL. Survivor: NM-ETF + "SPY ≥ open" gate (check +0.117, 2023-24 −0.056, 0.33 trades/session).
- Running tally: ~400 pre-registered candidates across rounds 1-3 (+35 in ultimate_1119); 0 reach the ultimate bar. Missing piece: a market gate that predicts the CLOSE (needs breadth data for 2023-24), or Primary's shorts + 2 gated longs as a hedge test.
