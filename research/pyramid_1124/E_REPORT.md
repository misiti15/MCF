Educational only — not financial advice

# Project Pyramid round 2 — Team E: catch the 09:35 bid (early-session longs) (2026-11-25)

Research only; entries 09:35–09:50 under a research exception (deploying anything would need the owner to lift the ≥ 09:50 entry rule). Pre-registered and hashed (scratchpad/pyramid/E/PLAN.md, 00:14 UTC; selection frozen 00:28 UTC). 12 configs (3 candidates × 2 rule values × 2 exits), LR8 with the 2.1× early-entry cost multiplier, testing book, 1-min bars. FIT 170 / CHECK 276 / 2023-24 427 sessions. Locked block never read. Caches hold regular-session bars only — no pre-market data, so no pre-open predictor could be scored.

Result: 0 of 3 pass; all 12 configs negative on check (−0.055 to −0.149R) and on 2023-24.

| Candidate | Rule | Check avg R (gross) | 2023-24 | vs same-universe random | Corr with book proxy |
|---|---|---|---|---|---|
| E1 OPEN-DRIVE-SECTOR | 09:35 entry; first-5-min volume ≥ 3× its average, strong green first bar, sector ETF leads SPY by ≥ 0.10% | −0.128 (−0.041) | −0.080 | −0.075 | −0.06 |
| E2 DEFENSIVE-GAPDOWN-RECLAIM | gap ≤ −1%, beta60 ≤ 0.8, ADV ≥ $100M, red first bar, reclaim of the 09:30–09:35 high by 09:50 | −0.118 (−0.043) | −0.129 | −0.036 | −0.03 |
| E3 ROTATION-BID | 09:40 entry; stock's sector ETF strongest of 11 and ≥ 0.3% over SPY, stock up, 10-min rel. volume ≥ 1.5, top 5 per day | −0.055 (+0.032) | −0.196 | −0.001 | −0.04 |

## Why
- Costs and noise: with a 0.25 ATR stop at 09:35, E1's median hold is 8 min and 57% are stopped; the early-entry costs take ~0.07–0.10R per trade.
- The 09:35/09:40 bid is a bet on the day's tape, not a stock edge: random entries in the same window show the same up-day/down-day shape, and no candidate adds anything reliable over them.
- No hedge value: correlation with the book ≈ 0; on the book's 10 worst days they add −18 to +5R against ~−360R.

## Next (backlog only)
(a) Early longs only with a wider early stop (below the opening-range low) plus a pre-registered "tape up at 09:45" gate — a new idea, not a re-tune. (b) A real pre-open predictor needs extended-hours bars (GET-only Alpaca pull; disk-limited). (c) Do not pursue 09:35 entries as a book hedge.
