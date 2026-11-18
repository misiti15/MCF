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

## Journal refresh with the timing guard (2026-11-14 21:30 ET)
`refresh.py <MCF repo> <out dir> <session>` pulls every account's journal.db and REFUSES unless each one's last commit is from
that session (ET) and >= 10 minutes old (Skeptic's FWDCAL guard: Gen pushed its last 11-13 trades at 16:06). It prints per-account
commit time and session trade counts. Tested: 11-13 passes (Gen 16:06, Graveyard 16:05, others 15:56-15:57); 11-14 (no session)
is refused. 11-18 order: refresh.py (after 16:30 ET) -> score.py -> ICCSET LR8 commands.

## Guard hardened (2026-11-15 17:20 ET; Skeptic's FWDCAL hole skeptic-20261115-2150-1, applied to my own scoring)
refresh.py now: refuses a session date after today (ET); accepts a journal whose last commit is ON OR AFTER the session
(a later commit means the session is closed), still requiring >= 10 min age when the last commit is the session itself.
score.py takes --end <session>, so a later, possibly partial session is never counted. Selftests plant each case
(future / stale / too fresh / later commit / --end). Live check: 11-12 passes (later commits), 11-20 refused, --end 11-12 -> 1 session.
11-18 commands: refresh.py <MCF> <out> 2026-11-18 ; score.py <out> forecast_setups.csv --end 2026-11-18

Added 2026-11-15 19:20 ET (Skeptic's past-window hardening): a last commit ON the session day must be at or after 15:55 ET
(a midday push or a dead EOD job is refused as 'pre-close commit'); selftest plants both. Live: 11-13 passes (commits 15:56-16:06).

## 11-18 reporting fixes (code only, before the run; forecast unchanged)
Skeptic -1550-1/-1551-2, Observer -1152-1, Skeptic -1750-1, Lead -1100-1/-1300-1. score.py prints:
(1) forecast setups matched by setup id, any account; (2) non-forecast setups apart; (3) setups whose realized accounts != {home},
which catches split setups such as the GY-BENCH guests; (4) 11-12..11-16 vs 11-17..end (TSZ1); (5) every ledger entry in the window;
(6) eligibility-adjusted: realized only over sessions a setup was eligible, and its forecast scaled to those sessions. The excluded
(setup, day) pairs are printed.
Eligibility source: research/ledger.jsonl patches `strategies.<id>.benched` {from, until}, and `strategies.<id>.enabled`
[true, false] from the effective date, unless the setup signals somewhere later (then it is enabled somewhere). Known limit: a
setup disabled and re-enabled elsewhere that never signals afterwards counts as off. On the current ledger: 38 (setup, day) pairs
are off, all on 11-18 (GY-BENCH). Selftests: a GY-BENCH guest pattern is flagged, and a benched case gives exactly 10/3 vs 10/3/wk.
