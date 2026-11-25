Educational only — not financial advice

# Project Pyramid — Team X: long vs short evidence + two-account design (2026-11-24)

Research only. Live: 32,069 deduped trades, all 10 accounts, 10-06..11-24, LR8 after costs. Lab: research/history2y/data/bt_lab1104 (1.17M trades; FIT 170 / CHECK 276 sessions; locked block never read). Path speed from 1-min bars (12,934 live trades, 10-06..11-04). Scripts/data: scratchpad/pyramid/X/.

## Owner beliefs — verdicts
| Belief | Verdict | Evidence |
|---|---|---|
| Shorts move sharper | Partly — only against us | Same favourable move in R (MFE +0.17/+0.30/+0.42R at 10/30/60 min both sides); P(+1R before −1R) 33% long vs 34% short; shorts hit −1R in 45 min vs 66 (squeezes); +10–16% raw bps offset by wider stops |
| Shorts pay quicker | Wrong | Same target size: ~0.5R targets 33 vs 32 min; ~1R targets longs faster (50 vs 90 min live; lab 35–45 vs 50–60) |
| Longs are a slow burn | Wrong | Long holds shorter (55 vs 85 min) because long targets are smaller (median 0.50R vs 0.86R) |
| Shorts earn more | Right live, not over 2 years | Live −0.08 vs −0.20R/trade (41 of 46 live-positive setups are shorts); lab and 2023-24 longs equal or better; live short edge is SPY-down-day dependent (+0.07 down vs −0.26 up) and the live window was mostly down/flat |
| More longs = more diverse | Right (strongest part) | Long vs short daily R correlation −0.32 Primary, −0.24..−0.68 live accounts, −0.55/−0.63 lab; shorts caused 9 of Primary's 10 worst days; 60% longs cuts avg worst-5 days ~35% (−19.3 → −12.5R) — but only raises total R if the longs are break-even or better (live longs today −0.18R/trade) |
| Less dependent on the same tickers | Wrong framing | Primary shorts: 1,198 trades in 589 names, top-10 7.7%, 16% repeat within 5 sessions — what repeats is the condition (gap-down, heavy selling, down tape), not the ticker; longs also unlock the ~25% of names that are not ETB |

## Two-account split
- Ticker selection: every enabled setup scans the same ~5,200-name universe on the same 5-min features; nothing assigns tickers between setups, so similar setups pick the same names (RW3/RW5 share ~25% of symbol-days). Account rules only act after a signal (3 lots/symbol, no opposite side, twin block, caps, −2R latch, burst brake, ETB).
- Overlap: Primary 12% of symbol-days with 2+ setups; stacked lots did not lose more (−0.003R vs −0.117R single). Testing 1/2: 22–30% of symbol-days, mostly copies of the same family; stacked lots worse (−0.18..−0.21R).
- Worst days are breadth, not stacking: stacking explains ~20–25% of Primary's 10 worst days (−211R); the rest is 26–71 different names all going against the same short idea (11-10: 71 names, −34.8R). Separate accounts cannot fix breadth — only longs with an edge or a pre-registered regime gate can.
- Options:
  - (a) Split by side: changes no trades or overlap; gains separate halts/slots (once: 11-06, 11 long signals blocked by the halt). Costs: on real funds each account generally needs its own $25k PDT floor, buying power not pooled (Primary peaks: long $43k, short $163k), opposite positions in the same ticker possible, double operations.
  - (b) Split by family: no benefit beyond (a).
  - (c) Per-symbol owner rule in one account — c2 "day owner" (first setup to enter a symbol owns it for the session): Primary 36 sessions total R −141.6 → −135.8, worst day −34.8 → −26.9; current roster +12.2 → +13.6R, worst −29.3 → −24.8 (RW3 +4.0, RW5 −2.7); Testing 1 −656 → −442, Testing 2 −961 → −659 (mostly removes family copies).
  - (d) Disjoint ticker pools: halves every setup's trades; worst days improve only as a size cut, R/trade unchanged.
- Recommendation: keep one account per book for now; forward-test OWNER-1 (c2) as a journal-only tag (20 Primary sessions, 1 config; pass: avg worst-5 improves ≥ 15%, total R not lower by > 2R or 0.1R/session, no setup loses > 25% of its R or > 3R, direction holds in ≥ 1 of Testing 1/2). Revisit a long-book / short-book two-account split only once a long sleeve passes on its own.

## Caveats
36-session live window mostly down/flat SPY; path test covers 10-06..11-04 only; lab is uncapped signal chains on a 1,226-name universe; replays only drop trades (freed slots/latch paths not modelled); broker rules described generally — not advice.
