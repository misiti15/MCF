Educational only — not financial advice

# U5 — Day-type specialists (USAGE PLAN item 5) — PRE-REGISTRATION

Written 2026-11-18 (market hours) BEFORE any outcome was scored. Research only: no config, code, runtime, merge or PR.
Locked block 2024-11-01..2025-02-28 is never read (fit sessions start 2025-06-02 so even the 80-day daily lookback in
the 1day packs stays after 2025-03-13; every daily row <= 2025-02-28 is dropped at read time and asserted absent).

## Why (P2 / BDI day-type findings)

- Primary loses on quiet and up days, wins on down days (research/bdi/1109/daytype_out.txt: Primary avgR down +0.224,
  quiet -0.145, up -0.199; consultant P3: current six -29.8R on 10 SPY gap-up days; no arena setup turns Primary's
  losing days green). The book is short-heavy (gap-down fades) and has nothing built for range or up tapes.
- These are NEW setups whose own entry conditions encode the day type. They are not on/off switches of existing setups,
  not lineups, not hedges, not sizing tilts, not CWT12/14 variants. Each has a mechanism (C3-MECH tag).

## Data sources (docs/GLOSSARY.md terms)

- FIT  = 2-year backtest bars (release bars2y-2025-06 .. bars2y-2026-01, point-in-time universe), 2025-06-02..2026-01-30.
- CHECK = Session replay bars of the live sessions (release bars-2026-10 / bars-2026-11, full live universe),
  2026-10-06..2026-11-17 (11-18 still open: left out). Unseen when the rules below were written.
- Both are non-live sources (weight 0 toward On Deck / Primary minimums, SRCV1). A pass here = a Testing-copy proposal
  only; the live record must be built in testing. Promotion hold is on.

## Common mechanics (fixed)

- 5-minute decision bars built from 1-minute RTH bars (bar labelled by its end; decision at the bar close; entry price =
  that close). Exits walked on 1-minute bars from the entry minute: stop checked first, target fills only when traded
  through by >= $0.01, flat at 15:55 (open of the 15:55 minute).
- Costs (LR8 engine model, research/workbench/.../sim.py): e*(1e-4 + SEC) + TAF + 2*CAT + exit slip (stop: max($0.02,
  4 bp); time: max($0.01, 1 bp); target: 0), per share, both sides. R = net P&L per share / |entry - stop|.
- Point-in-time daily features from the 1day pack rows strictly before the session: prior close, ATR14 (true range),
  ADV20 in dollars. Gap = session open / prior close - 1.
- Universe (all setups): prior close >= $10, ADV20 >= $20M, 1% <= ATR14/price <= 8%. Range setups (S1-S3) also need
  |gap| <= 3% (no news gaps); S4 needs |gap| <= 8%.
- One trade per symbol per day per setup (first signal); at most 15 open positions per setup (later signals skipped).
- Stop distance R must be 0.08..0.40 x ATR14 (else no trade).

## Day-type cues (point-in-time, anchored after the first 20-30 minutes, owner 2026-11-14)

- ATRs = SPY ATR14 (daily). OR30s = SPY high-low 09:30-09:59. OR20s = SPY 09:30-09:49 range. P950s = SPY close of the
  09:50 minute bar (the 09:46-09:50 five-minute bar close).
- QUIET(T): OR30s/ATRs <= q40 AND SPY high-low from 09:30 to T <= 1.25 x OR30s (the tape is still inside an only
  slightly widened opening range). q40 = the 40th percentile of OR30s/ATRs over the FIT sessions — a frequency rule set
  outcome-blind (no R looked at).
- UP(T): SPY close(T) > OR20s high AND SPY close(T) >= P950s + 0.10 x ATRs AND breadth(T) >= 0.55, where breadth(T) =
  share of universe names whose close(T) is above their own 09:50 close.

## The four setups (one pre-registered config each)

| # | id | day type | side | entry (5-min bar close T) | stop | target | window |
|---|---|---|---|---|---|---|---|
| S1 | DT-QD-FBD-long | QUIET(T) | long | own OR30 (09:30-09:59) width 0.25-0.90 ATR; a bar after 10:00 broke below OR30 low by >= 0.05 ATR; bar T closes back above OR30 low within 6 bars of the first break | break low - 0.03 ATR | OR30 mid; skip if < 1.0R away | 10:30-14:30 |
| S2 | DT-QD-FBO-short | QUIET(T) | short | mirror of S1 (failed breakout above OR30 high) | break high + 0.03 ATR | OR30 mid; skip if < 1.0R away | 10:30-14:30 |
| S3 | DT-QD-VWAPSTRETCH-long | QUIET(T) | long | close <= VWAP - 0.40 ATR; bar T green and close > prior bar close (turn) | day low so far - 0.03 ATR | VWAP at T; skip if < 1.0R away | 10:30-14:30 |
| S4 | DT-UP-VWAPPB-long | UP(T) | long | leader: at the 10:00 bar close, close >= own 09:50 close + 0.25 ATR and > VWAP; bar T low <= VWAP + 0.05 ATR, close > VWAP, close > open | min(bar low, VWAP) - 0.05 ATR | 2.0R | 10:15-13:30 |

Mechanisms (falsifiable): S1/S2 — on a quiet index tape single-name breaks of the opening range lack follow-through
and revert to the range middle; S3 — an over-stretch below VWAP on a quiet tape snaps back toward VWAP; S4 — on a
broad up tape, names that led after 09:50 get bought on their first VWAP test.

## Controls and diagnostics (counted as configs)

- D1-D4: the same four setups WITHOUT the day-type cue (all days) — shows whether the day type carries the edge.
- R1-R4: random entries — for every setup trade, 3 random universe names (same day, same filters, same minute, same
  side), R = the same multiple of their ATR, same target R-multiple, same exit rules and costs.
- Configurations counted: 4 setups + 4 no-cue + 4 random = **12**. Bar: t >= max(1.5, sqrt(2 ln 12)) = **2.23**.

## Pass rule (per setup, fixed now)

1. FIT (2-year): >= 100 trades, avg R > 0 after costs, day-clustered t >= 2.23.
2. CHECK (live-session replay, unseen): >= 25 trades, avg R > 0, avg R w/o best day > 0, best-day share < 50%,
   avg R > its random-entry control.
3. Reported for each: trades, win %, avg R, total R, avg R w/o best day + share, worst day, green days, t, random
   control, no-cue version, and its R on Primary's losing (quiet / up) live days vs Primary's own R those days.
- PASS -> Testing-copy proposal (decision code), never deployed here. Pass on fit only = WATCH (no proposal).
- No parameter is changed after scoring. If something is broken (a bug, not a result), the fix is logged in NOTES.md.
