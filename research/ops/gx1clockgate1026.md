# GX1: 5-minute clock gate for lab setups, and GX5: realistic GEN expectations (2026-10-26)

*Educational only — not financial advice. Owner decision 2026-10-26 07:10 ET (GX1 all accounts, GX5). Replays are
replays, not live results (rules 7–8). Effective session 2026-10-27; merge only after 16:00 ET (setup-freeze).*

## Failures and limits first

- **Added trades are not better trades.** Priced with production costs, the trades the clock gate adds average
  −0.002 R (Primary, n 180), +0.065 (Testing 1, 490), +0.016 (Testing 2, 1,155), **−0.184 (Graveyard, 366)**,
  −0.018 (Gen, 51) over 5 sessions (Graveyard 3). These are the same setups on the same rules, so their R is the
  setups' R; the change is about reps, not edge. Without each account's best day: −0.036 / +0.041 / +0.006 / −0.233 /
  −0.058 R. Testing 1's and Testing 2's added R lean on one day (47% / 67% of the added R on 10-20 / 10-23).
- **More trades also displace some.** Caps and held symbols fill sooner: trades the old gate took and the new one
  does not: Primary 1, Testing 1 24 (−0.31 R avg), Testing 2 123 (+0.11), Graveyard 188 (−0.10), Gen 16 (−0.32).
- **Primary trades ~57% more** (64 → 100 submitted/day in the replay). Same setups, same rules; this is the
  exposure their backtests already assumed, but it is a large step in live risk count.
- Graveyard has only 3 sessions (it started 10-21). Gen is replayed with the caps of those days (80 / 16), not GX2's.
- HeatStrategy (`type: heat`, e.g. heat_fade_* in Testing / Graveyard) keeps the old bar-count gate: not in GX1's scope.
- The replay universe is the lab universe ∩ the live universe; live names outside it are not replayed.

## What changed (GX1)

`LabStrategy.eligible` used `len(bars) % 5 == 0`. A symbol that missed one minute earlier in the day was out of phase
for the rest of it, and with the first-signal-per-symbol-day rule a skipped first hit lost the day.
Now (`mcf/strategies/setups.lab_decision_buckets`) the latest 1-minute bar is checked against the 5-minute clock
buckets of `resample(bars, '5min')` (the screen's and the backtests'): it decides its own bucket when it is the
bucket's 4th minute, and the previous bar's bucket when that bucket had no 4th-minute bar (the bucket completes with the
next bar that arrives; this is the bar `_signal` already uses as `end`). Only completed buckets, only the latest bar's
(no catch-up of older buckets: GX6, not approved). For a name trading every minute nothing changes (test: identical to
the old count test on every prefix). The runner evaluates each bucket once per setup and symbol
(`PaperRunner.lab_bucket`); after a restart the journal dedupe (seen / moments) keeps a fired bucket from firing again.
The replay fast path (`mcf/replay/fast.py`) calls the same function, so replay and live agree.

## Replay validation (VALIDATION.md method: 10-21..23, as live, paper fills, touch limits)

Live ran the old gate, so the old-gate replay is the like-for-like check; the new-gate replay must keep every live
signal it matched and only add.

| account | live signals in universe | matched old gate | matched new gate | replay signals old → new | live trades | matched trades old → new |
|---|---|---|---|---|---|---|
| Primary | 284 | 284 (100%) | 284 (100%) | 285 → 418 | 204 | 174 → 174 |
| Testing 1 | 837 | 836 (99.9%) | 836 (99.9%) | 856 → 1,335 | 443 | 400 → 395 |
| Testing 2 | 534 | 534 (100%) | 534 (100%) | 861 → 1,388 | 376 | 289 → 288 |
| Graveyard | 1,909 | 1,907 (99.9%) | 1,907 (99.9%) | 1,918 → 2,844 | 902 | 705 → 567 |
| Gen | 57 | 28 | 28 | 210 → 292 | 68 | 20 → 19 |

Fast-path fidelity checks: 0 frame / 0 mask differences in every session of every run. No live signal is lost under
the new gate; the added signals are the decision bars the old gate could not act on. Matched trades drop where the
added signals fill caps first (Graveyard). Gen's low match is the pre-existing breadth-context / poll difference
(genexposure1025 §2, §4d), the same under both gates. Testing 2's replay-only signals under the old gate (327) are the
known poll-gap losses (VALIDATION.md).

## Effect per account (10-19..23 as live, live universe, production costs)

Signals / submitted per day, old gate → new gate (Graveyard 10-21..23):

| account | sessions | signals/day | submitted/day | added trades: n, avg R (se) | w/o best day | displaced trades |
|---|---|---|---|---|---|---|
| Primary | 5 | 81.6 → 125.8 (+54%) | 63.8 → 100.4 (+57%) | 180, −0.002 (0.065) | −0.036 | 1 |
| Testing 1 | 5 | 424.8 → 594.8 (+40%) | 242.0 → 336.8 (+39%) | 490, +0.065 (0.039) | +0.041 | 24, −0.31 |
| Testing 2 | 5 | 553.0 → 895.0 (+62%) | 402.4 → 608.2 (+51%) | 1,155, +0.016 (0.022) | +0.006 | 123, +0.11 |
| Graveyard | 3 | 639.3 → 948.0 (+48%) | 291.3 → 350.7 (+20%) | 366, −0.184 (0.043) | −0.233 | 188, −0.10 |
| Gen | 5 | 57.6 → 79.4 (+38%) | 27.0 → 34.0 (+26%) | 51, −0.018 (0.115) | −0.058 | 16, −0.32 |

Per day (signals old → new, submitted old → new):

| day | Primary | Testing 1 | Testing 2 | Graveyard | Gen |
|---|---|---|---|---|---|
| 10-19 | 46→66, 32→51 | 695→844, 401→509 | 1025→1679, 813→1241 | – | 10→17, 7→13 |
| 10-20 | 77→145, 72→125 | 573→795, 271→357 | 879→1408, 624→925 | – | 68→88, 22→25 |
| 10-21 | 83→125, 57→88 | 339→552, 240→375 | 242→405, 201→299 | 693→1052, 344→430 | 37→47, 21→24 |
| 10-22 | 162→233, 126→186 | 352→525, 159→223 | 437→696, 211→316 | 676→982, 280→299 | 153→221, 66→86 |
| 10-23 | 40→60, 32→52 | 165→258, 139→220 | 182→287, 163→260 | 549→810, 250→323 | 20→24, 19→22 |

Gen's 288 → 397 signals reproduces genexposure1025's in-process what-if (288 → 397) with the shipped code.
Every replay signal / trade, both gates: `gx1clockgate1026_results.json`.

## GX5: expected live trades/day per GEN setup (display only)

`mcf/research/generator/expect.py`: median-day screen per_day over the last 60 sessions of the screen history
× 0.97 (live-gate share with GX1, genexposure1025 §3: 1,288 of 1,324) × 1.40 (names outside the lab universe, §4a / §5)
× 0.81 (spread / ETB / opposite-side skips, §4f). Stored per setup in `docs/live/generator_lab.json` → `expected_live`,
in every generator run report (`expected_live`, refreshed for all GEN setups), in `config/account_gen.yaml`
`gen.screen` for new setups, and shown as **Expected live /day** in the Generated setups table.
Backfill for the setups generated before today: `python -m mcf.research.generator expected` (last 4 open months;
window 2026-07-15..2026-10-07) → `research/generator/expected_live.json`.

**Limit of the per-setup median:** 47 of the 60 generated GEN setups fire on fewer than half of the last 60 sessions, so their
median day is 0 and their per-setup expectation shows 0.0 although they do trade some days (the tooltip gives the
same factors on the last-60 mean). For the account the summary uses the median of the live setups' daily *total*:
60 live setups, screen mean 273/day over 2 years, last-60 mean 166.5, median day 136 → **~150 expected live
signals/day before caps** (the sum of per-setup medians would say 42; on the means 183).

## Files

- `mcf/strategies/setups.py`, `mcf/execution/runner.py`, `mcf/replay/fast.py` — GX1.
- `tests/test_lab_clock_gate.py` — missing minute still evaluated; missing 4th minute; two buckets on one bar;
  no lookahead; each bucket once; no double fire after a restart; replay uses the same gate.
- `mcf/research/generator/expect.py`, `screen.py`, `apply.py`, `summary.py`, `__main__.py`, `docs/live/index.html`,
  `tests/test_gen_expected.py` — GX5.
- `gx1clockgate1026_oldgate.py` (replay with the pre-GX1 gate, in-process), `gx1clockgate1026_compare.py`,
  `gx1clockgate1026_results.json`.
