Educational only — not financial advice

# U4 long-side program — results (2026-11-18, research only)

USAGE PLAN item 4. Pre-registration: PLAN.md (committed and pushed before any scoring, commit 9f7b8e106).
Run during market hours: no config, code, runtime or branch change; nothing deployed; no PR.

**Configurations tried: 10** (5 new long specs x 2 fixed exit packages). The same 10 were re-scored on the 2-year packs
(not new configs). Part A is descriptive (0 configs). Bar: day-clustered t >= max(1.5, sqrt(2 ln 10)) = 2.15; Testing bar
(BAR90) 1.93. Random controls: 5 seeds x 2 kinds per trade. Locked block 2024-11-01..2025-02-28 never read (1day rows
inside it dropped and asserted absent; 2-year sessions start 2025-05-01 so no prior window touches it).

## Verdict (failures first)

**0 of 10 new long configs pass. No new long setup is proposed as a Testing copy.** Every config is negative on the
2-year packs (223 sessions, -0.046 to -0.134 R/trade after costs, 1,745-2,724 trades each); 9 of 10 are negative on
the 31 live sessions. The one live-positive spec (U4-VWR, the VWAP reclaim on up-tape days) has t 0.77 / 1.00
(bar 1.93), a 52-56% best-day share, and is -0.116 R/trade over 2 years (positive in 3 of 13 months).

The existing live long book is worse still: **14,503 live long trades, -1,952R** (-0.135R/trade), across all accounts.
Only two long setups have a record that holds without the best day and in both halves, and both are already in
Primary: **NM-ETF-late-dip-di-long** (27 trades, +0.289R, +0.265 w/o best day, t 4.2) and **ST7-rsi50dn-long-pm-t1s1-FD**
(49 trades, +0.118R, +0.038 w/o best day, best day 70% of total).

What carries forward (the optimistic part, stated honestly): every long spec makes money on SPY **up** days, in both
datasets (2-year up-day R per session +0.7 to +3.4R for 4 of 5 specs), and loses on quiet and down days. The long edge
here is a day-type edge, and the day type is not known at entry — U4-VWR already requires SPY to be up >= +0.20% at
the bar and still loses -0.44R/trade on quiet days and -0.68R on down days over 2 years. Quiet days, the other target,
have no long answer in this round: all 10 configs are negative on quiet days in both datasets (U4-PMT, built for them,
is the worst).

## Primary by day type (why the program exists)

Primary journal as traded, 31 sessions 10-06..11-17 (SPY open-to-close: up > +0.25%, down < -0.25%, else quiet):

| Day type | Sessions | Primary R | R per session | Primary trades avg R |
|---|---|---|---|---|
| Up | 10 | -89.2R | -8.92R | -0.155 |
| Quiet | 12 | -56.4R | -4.70R | -0.145 |
| Down | 9 | +79.8R | +8.87R | +0.226 |

Primary has 241 long trades of 1,316 (18%). Rule changes inside this window (research/ledger.jsonl): 10-20 twin-symbol
block; 10-22/23 per-setup latch off in Testing 1/2; 10-27 slots 160 -> 77; 10-28 Primary sizing (~$4k cap); 10-29 -2R
per-setup latch + BAR90; 11-05 ROLL1 low-rep homes; 11-11 TEAM-6 lineup; 11-12 LR8 after-cost R, Testing D/E/F open;
11-16 ROT1; 11-17 TSZ1 half-size testing, 15 WB copies, promotion hold. The Primary series mixes lineups (TEAM-6 from
11-11); Part A live records span all of these. Part B (bar replays) uses one fixed engine and is not affected.

## Part B — the five pre-registered long specs (live packs, 31 sessions, full universe, costs in)

| Config | Trades | Days | Avg R | Total | t (day) | Avg w/o best day | Best-day share | Fit avg | Check avg | Random same-time | Random bar | Corr w/ Primary daily R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| U4-PMT E1 | 361 | 30 | -0.207 | -74.7 | -2.52 | -0.252 | — | -0.070 | -0.365 | -0.119 | +0.172 | 0.07 |
| U4-PMT E2 | 361 | 30 | -0.226 | -81.5 | -2.81 | -0.268 | — | -0.128 | -0.339 | -0.153 | +0.192 | 0.00 |
| U4-MPB E1 | 381 | 31 | -0.115 | -43.7 | -1.17 | -0.156 | — | -0.067 | -0.159 | -0.108 | -0.129 | 0.13 |
| U4-MPB E2 | 381 | 31 | -0.126 | -48.0 | -1.31 | -0.168 | — | -0.094 | -0.156 | -0.080 | -0.130 | 0.07 |
| U4-RSB E1 | 235 | 25 | -0.133 | -31.4 | -1.28 | -0.172 | — | -0.049 | -0.251 | -0.133 | +0.045 | 0.22 |
| U4-RSB E2 | 235 | 25 | -0.031 | -7.3 | -0.19 | -0.147 | — | +0.099 | -0.213 | -0.053 | +0.056 | 0.41 |
| U4-ODC E1 | 381 | 31 | -0.060 | -23.0 | -0.61 | -0.110 | — | -0.195 | +0.078 | -0.092 | +0.152 | 0.15 |
| U4-ODC E2 | 381 | 31 | -0.036 | -13.8 | -0.27 | -0.137 | — | -0.225 | +0.158 | -0.121 | +0.125 | 0.19 |
| U4-VWR E1 | 274 | 19 | +0.062 | +17.0 | 0.77 | +0.029 | 56% (1 day) | -0.032 | +0.188 | -0.057 | -0.011 | **-0.49** |
| U4-VWR E2 | 274 | 19 | +0.106 | +29.0 | 1.00 | +0.054 | 52% (1 day) | +0.031 | +0.206 | -0.066 | -0.020 | **-0.51** |

Specs: ODC opening-drive continuation on +2..+15% gap-ups with RS and rvol >= 2; VWR VWAP reclaim in daily up-trend
names while SPY is up >= +0.20%; RSB RS-leader 20-day-high breakout (no sector map in the packs, so "leader" = top 10%
20-day return of the universe); MPB morning pullback to VWAP in early-strong names; PMT 13:30 trend-day continuation.
E1 = +1.5R target, E2 = hold to 15:55; stop 0.30 x ATR14 for all. Full definitions in PLAN.md.

## Part B — 2-year packs (223 sessions: 2024-09-16..10-31, 2025-05-01..2026-01-30)

| Config | Trades | Avg R | t (day) | Avg w/o best day | H1 avg | H2 avg | Random same-time | Random bar | Up-day avg | Quiet avg | Down avg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| U4-RSB E2 | 2,233 | -0.134 | -2.69 | -0.144 | -0.194 | -0.059 | -0.131 | -0.056 | +0.055 | -0.138 | -0.587 |
| U4-VWR E1 | 1,745 | -0.118 | -2.37 | -0.128 | -0.124 | -0.111 | -0.142 | -0.096 | +0.145 | -0.443 | -0.676 |
| U4-VWR E2 | 1,745 | -0.116 | -1.84 | -0.144 | -0.106 | -0.125 | -0.125 | -0.103 | +0.180 | -0.448 | -0.808 |
| U4-RSB E1 | 2,233 | -0.101 | -2.68 | -0.110 | -0.127 | -0.069 | -0.150 | -0.086 | +0.062 | -0.159 | -0.368 |
| U4-PMT E2 | 2,455 | -0.097 | -3.18 | -0.103 | -0.116 | -0.079 | -0.140 | +0.400 | -0.039 | -0.095 | -0.195 |
| U4-MPB E2 | 2,424 | -0.084 | -1.93 | -0.094 | -0.075 | -0.092 | -0.127 | -0.035 | +0.125 | -0.062 | -0.400 |
| U4-MPB E1 | 2,424 | -0.079 | -2.26 | -0.085 | -0.113 | -0.049 | -0.124 | -0.029 | +0.084 | -0.084 | -0.292 |
| U4-PMT E1 | 2,455 | -0.078 | -2.64 | -0.084 | -0.100 | -0.057 | -0.126 | +0.293 | -0.005 | -0.095 | -0.169 |
| U4-ODC E1 | 2,724 | -0.071 | -2.13 | -0.078 | -0.014 | -0.131 | -0.157 | +0.097 | +0.125 | -0.083 | -0.284 |
| U4-ODC E2 | 2,724 | -0.046 | -0.87 | -0.059 | +0.040 | -0.135 | -0.152 | +0.161 | +0.281 | -0.018 | -0.461 |

R per session by day type (2-year; sessions with no trade count as 0): ODC E2 up +3.41 / quiet -0.21 / down -5.82;
VWR E2 +2.49 / -2.47 / -2.91; MPB E2 +1.42 / -0.69 / -4.03; RSB E1 +0.78 / -1.69 / -2.26; PMT E1 -0.06 / -1.04 / -1.59
(u4_daytype.csv). Day types over 2 years: 76 up, 84 quiet, 63 down.

**Against random entries.** Every spec beats a random liquid name entered at the same bar (same-time control) by
+0.01 to +0.09 R/trade over 2 years — there is some selection edge — but none beats the same name entered at a random
bar in its window except VWR, RSB and MPB by 0.02-0.08R, and all sit below zero. A random long entry after costs with a
0.30 ATR stop averages -0.12 to -0.16R: that is the hurdle a long setup of this shape has to clear.

**Gross vs costs.** Gross R (before costs) is about zero for every spec on 2 years (-0.06 to +0.03); costs take
0.05-0.10R per trade with a 0.30 ATR stop. U4-ODC E2 is the only config with positive gross R in both datasets
(+0.029 2-year, +0.035 live) — costs turn it negative.

## Correlation with Primary and Primary's red days (live, 31 sessions, 22 Primary red days)

| Config | Corr with Primary daily R | R on Primary's red days | R on Primary's green days | Primary red days the spec was green |
|---|---|---|---|---|
| U4-VWR E2 | -0.51 | +44.3 | -15.3 | 10 / 22 |
| U4-VWR E1 | -0.49 | +28.6 | -11.7 | 12 / 22 |
| U4-PMT E2 | 0.00 | -63.7 | -17.8 | 8 / 22 |
| U4-MPB E2 | 0.07 | -41.0 | -6.9 | 8 / 22 |
| U4-ODC E2 | 0.19 | -53.5 | +39.7 | 7 / 22 |
| U4-RSB E2 | 0.41 | -27.6 | +20.2 | 7 / 22 |

VWR is the only real hedge to Primary (corr -0.5), because its SPY-up gate puts it on Primary's losing days. Its
2-year record (-0.116R, 3 of 13 months positive) says that hedge costs R on average. P2/P3 already found that hedges
and day-type switches do not keep their sign; this repeats it from the long side.

## Part A — existing live long setups (10-06..11-17, all accounts, run 1)

101 long setups, 14,503 trades, -1,952R. By SPY day type: up -37.7R (-0.008/trade, 4,627 trades), quiet -409R
(-0.089), down -1,505R (-0.285). Pooled long daily R vs Primary daily R: corr -0.30 — the longs do offset Primary, but at
a loss of ~63R per session. Of 53 long setups with >= 30 trades, **1** is positive w/o its best day (and in both halves)
(ST7). Full list: u4_live_longs_all.csv.

| Setup (account) | Trades | Avg R | W/o best day | Best-day share | Fit / check avg | Up / quiet / down avg | Corr w/ Primary |
|---|---|---|---|---|---|---|---|
| NM-ETF-late-dip-di-long (Primary, Testing A/C) | 27 | +0.289 | +0.265 | 19% | +0.407 / +0.263 | +0.173 / +0.343 / +0.317 | 0.36 |
| ST7-rsi50dn-long-pm-t1s1-FD (Primary, On Deck) | 49 | +0.118 | +0.038 | 70% (1 day) | +0.199 / +0.078 | +0.329 / +0.020 / +0.074 | 0.02 |
| GEN-261027-01 MACDh LATE BRvw>0.5 t05s1 (Gen, Testing E) | 16 | +0.187 | +0.139 | 39% | +0.082 / +0.235 | +0.201 / +0.246 / -0.021 | -0.16 |
| GEN-261021-02 BarRng OPEN SPY>0.5 t1s1 (Gen, On Deck) | 305 | +0.088 | -0.041 | 133% (1 day) | — / +0.088 | -0.092 / +0.422 / +0.341 | 0.18 |
| GEN-261020-09 EMAdChg MID QQQ<-0.3 holdtr (Gen) | 174 | +0.385 | -0.056 | 108% (1 day, all on down days) | — / +0.385 | — / — / +0.385 | -0.01 |
| GEN-261019-04 EMAdChg RSI14<=22 MID t1s1 (Gen) | 112 | +0.071 | -0.040 | 148% (1 day) | +0.096 / +0.070 | +0.286 / -0.155 / +0.025 | -0.20 |
| NM-HL-T75-pm-long (On Deck, Testing A) | 61 | -0.013 | -0.071 | — | +0.352 / -0.068 | +0.491 / -0.066 / -0.068 | 0.09 |
| NS5-sma50-flush-oversold-long (Primary) | 41 | -0.023 | -0.076 | — | +0.084 / -0.106 | +0.021 / +0.346 / -0.355 | 0.07 |

Both proven long legs (NM-ETF, ST7) are already in Primary and are positive on up and quiet days; they are small
(27 and 49 trades in six weeks). They are the long side Primary has, and the result here is to keep them and not
dilute them. NS5 is C3-NS5's drop candidate; nothing here argues against that.

## Decision codes (promotion hold on — nothing here is deployed by this study)

| Code | Proposal | Evidence | Expected effect |
|---|---|---|---|
| U4-NOCOPY | No new long Testing copy from this round: all 5 specs x 2 exits fail (2-year -0.05..-0.13R, t <= -0.87; live 9/10 negative) | Tables above | Avoids arena time on configs that made -7R to -82R each over the 31 live sessions (235-381 trades each) |
| U4-KEEP-LONGS | Keep NM-ETF-late-dip and ST7 as Primary's long legs as they run now (no gates, sizing or exit overlays); judge with the rest of the book | NM-ETF +0.265 w/o best day, t 4.2, positive on all three day types; ST7 positive on all three, but a 1-day record (70%) | Keeps Primary's only proven up/quiet-day long R (+13.6R across accounts in six weeks). No new R claimed |
| U4-GEN2701-REPS (optional, routine) | Give GEN-261027-01 (late-day long, 16 trades) its fair share of low-rep rotation in Explore 1 / Live Lab under C3-ROT; no copy, no promotion talk before 15 active days and 30 trades | +0.187R, +0.139 w/o best day, both halves positive, 6 active days; GEN setup, so its mechanism tag is "late-day momentum on a broad-breadth tape" — to be confirmed | Low-rep data only; R effect unknown (n 16) |

No code proposes U4-VWR: its live anti-correlation (-0.5) is real but its 2-year record is negative in both halves and
on quiet and down days, and a day-type gate on it would be a day-type switch (guardrail).

## Next step (not tested here; a backlog idea for a new pre-registered round, not a live change)

The shape of the failure is specific: gross R about zero, costs 0.05-0.10R, and a clean up-day edge (2-year up-day avg
+0.06 to +0.28R for 4 of 5 specs). Two salvage routes, one change each: (1) a cost-aware long design — stop and target
scaled so that costs are <= 0.03R (e.g. stop 0.5-0.6 ATR, fewer trades in tighter-spread names) for U4-ODC, the only
spec with positive gross R in both datasets; (2) U4-ODC/U4-MPB restricted to the C3-EARN earnings-reaction names (the
gap-and-go on earnings already has +0.346R/trade), i.e. a long-only reading of EARN-GO rather than a new family.
Either goes through the backlog and BAR90 before any arena time.

## Caveats

31 live sessions (fit 16 / check 15; one green day ≈ 3-6% of a total). Day types are classed with the SPY close
(hindsight) for reporting only; no config used them. rvol uses a linear volume clock, so early-session rvol is
overstated (thresholds were set knowing that, before scoring). The "sector leader" spec uses universe relative
strength because the packs carry no sector map. The 2-year packs are a point-in-time universe but stop at 2026-01 and
skip 2024-11..2025-04 (locked block and its priors). Fills are simulated (next 1-minute open + costs, stop first);
replays are a filter only (rule 21), never a record. Up to 15 entries per spec per day; no account-level slot or
buying-power limits. Pack data were streamed and deleted.
