# L3-AM: results (plan: L3AM_PLAN.md, committed before scoring)

*Educational only — not financial advice.* Research only: no config, setup, exit or latch change.

`L3-gap-slope-fromopen-FD` ("Gap-Down Recovery Fade (all day)", Primary) with no new entries after 13:00 (window
09:50-13:00) vs the parent (09:50-15:00). Same engine, book, −2R latch, LR8 costs. **Configurations: 1** (lineage 44,
bar 2.75; longer lineage 155, bar 3.18). Locked block 2024-11-01..2025-02-28 not read (asserted). Script
`code/testAM.py`, table `L3AM.csv`.

## Verdict: **FAIL** — no decision code (no "L3AM-COPY"), the parent stays as it is
| gate (2-year VALID, 2026-01-02..10-05) | parent | AM | result |
|---|---|---|---|
| 1 avg R per trade ≥ parent | −0.0434 (1,970 tr) | −0.0474 (1,627 tr) | **fail** |
| 2 total R ≥ parent | −85.5 | −77.2 | pass (+8.3R) |
| 3 avg R w/o best day > parent | −0.0639 | −0.0727 | **fail** |
| 4 day-paired t ≥ 2.75 | — | 0.36 | **fail** |
| live avg R ≥ parent (Primary + On Deck, −2R latch replay) | +0.266 (356 tr) | +0.338 (319 tr) | pass |
| live total R w/o best day ≥ parent | +61.0 | +74.2 | pass |

The 13:00-15:00 entries are a small loss in VALID (343 trades, −8.3R ≈ −0.024R each), so cutting them saves R in
total, but the morning trades left are no better per trade than the whole day.

## Reported, not gates
| test | parent trades / avg R / total | AM trades / avg R / total | AM avg R w/o best day (parent) | t vs parent |
|---|---|---|---|---|
| 2-year ALL | 4,242 / −0.052 / −221.4 | 3,597 / −0.051 / −181.6 | −0.062 (−0.062) | 1.30 |
| 2-year TRAIN | 1,995 / −0.079 / −157.5 | 1,721 / −0.079 / −135.6 | −0.096 (−0.094) | 1.20 |
| 2-year FWD (10-06..11-04) | 277 / +0.078 / +21.6 | 249 / +0.125 / +31.2 | −0.002 (−0.048) | 1.26 |
| Session replay (10-12..11-17) | 354 / +0.136 / +48.0 | 292 / +0.206 / +60.1 | +0.125 (+0.085) | 1.07 |
| live Primary | 148 / +0.261 / +38.6 | 139 / +0.271 / +37.6 | +0.076 (+0.079) | — |
| live Primary + On Deck | 356 / +0.266 / +94.6 | 319 / +0.338 / +107.8 | +0.310 (+0.221) | — |

Read: the afternoon weakness is a **recent** effect (FWD, replay, live all favour AM), while the two older years show
nothing (TRAIN equal per trade, VALID slightly worse). Live best-day shares are high in Primary (80-82%): the Primary
record rests on one day either way. What can be salvaged: the existing Testing A (key `testing2`) copy `-WB4` (window to 13:00 plus gap
≤ −3.2%) keeps collecting live evidence on the same idea; re-check AM vs PM there and in Primary's journal as reps grow.

## Rule changes inside the windows (research/ledger.jsonl)
Primary sizing ~$4-5k 10-28; LL-LATCH (latched, not re-armed) 10-23; Primary −2R per-setup latch 10-29; L3
re-promoted Testing 1 → Primary 10-30; TEAM-6 11-11; LR3 + LR8 cost model 11-12; WB4 copy in Testing A 11-17;
promotion hold 11-17. The engine applies today's rules to every session; the live record mixes latch regimes (no
Primary latch before 10-29).
