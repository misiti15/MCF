# REPS3 — frozen setup-days forecast for the 11-12 roster (descriptive; scored after >= 5 sessions)
Educational only — not financial advice. Research only. Frozen 2026-11-11 17:30 ET, before the 11-12 open.
Context: owner restructure c64d75df0 (effective 11-12): Testing D/E/F filled (10 each), 5 Gen graduates out of Gen, one home
per setup, Testing A full universe (top-500 pool removed), per-setup cap 10 -> 30 in Testing B-F, Gen x1.8 / 300 slots / cap 150,
Graveyard x1.6 / 300 slots / cap 75, account halt 120R -> 300R (On Deck, Testing A-F, Gen; Primary 20R). 9 ledger entries 2026-11-12-*.

## Forecast (`forecast.py` -> `forecast_out.txt`, `forecast_setups.csv`)
p_day per enabled setup = its live submitted-day share 10-20..11-10 (REPS2), else 1 - exp(-0.193 x lab trades/day), else unrated.
| Account | Setups (rated) | Forecast setup-days/week |
|---|---|---|
| Gen | 88 (66) | 152.4 |
| Graveyard | 33 (33) | 149.7 |
| On Deck | 14 (14) | 43.4 |
| Testing A | 11 (10) | 33.0 |
| Primary | 6 (6) | 22.1 |
| Testing F / E / C / B / D | 10-11 each | 21.7 / 17.1 / 16.0 / 13.9 / 13.8 |
| **Total** | 204 (165) | **482.8**, the same as the 10-20..11-10 baseline (~482) |

## Reading
Moving setups between homes adds no setup-days by itself: the total is unchanged because each setup keeps its own rate.
New setup-days must come from:
(a) the unlocks: Gen halt + buying power, at most ~12/week per REPS1b, whose halt part rests on 2 days;
(b) Testing A's full universe, not measured;
(c) the 39 unrated setups, mostly new Gen setups.
The per-setup cap rise (10 -> 30) should add ~0 setup-days, since max-positions skips were all same-day extras (REPS1b).
Expected: total ~482-500/week. Clearly more would mean the universe change or new setups carried it. Less would mean
lost split copies or quieter markets.

## Scoring rule (fixed now)
After >= 5 sessions from 11-12: realized setup-days/week per account = 5 x (setup, day) pairs with >= 1 submitted signal / sessions.
Report realized vs forecast per account and per setup source (live / lab / unrated). Also report the realized Gen halt /
buying-power skip counts vs REPS1b, and Testing A's signals per session before vs after the universe change. Market context:
SPY realized range, since quiet weeks lower every rate.
