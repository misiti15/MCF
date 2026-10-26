# Blocked-signal audit (owner 2026-10-22: "We don't want setups sitting unused because of hiccups")

*Educational only — not financial advice. Read-only audit of the five intraday accounts, run Mon/Thu after the close.
Intended blocks are reported, never changed here. Replays are replays, not live results.*

Method: `research/ops/pollspeed1022.md` (decision bars a poll never saw). Scripts: `research/ops/blocked1026_audit.py`
(poll logs `polls/<date>/*.jsonl.gz` via `mcf.execution.runner.read_poll_log`, journals `run_id=1` signals and
`run_id=2` what-if trades, frozen `setups/<date>.json`; output `blocked1026_results.json`) and
`research/ops/blocked1026_replay.py` (full-coverage replay of the same sessions with `python -m mcf.replay run
--as-live --universe live --fills costs`, current code = GX1 clock gate; output `blocked1026_replay.json`).
"Net" = what-if R after the production cost model ($0.01/sh + 1 bps per side, no slippage on target exits, +$0.02/sh
on stops). Coverage = share of the account's lab decision bars (5-minute bars 09:50–15:00 × symbols with bars) that a
poll evaluated, *including* bars before a late start; "own" = from the account's first poll.

## Running table

| audit | sessions | coverage % Primary / T1 / T2 / Graveyard / Gen (own window) | never fired (broken) | unintended blocks (count, what-if net R) | value |
|---|---|---|---|---|---|
| **2026-10-26** (first) | 10-22, 10-23, 10-26 | 10-22: 99.3 / 95.3 / **63.7** / 92.1 / **52.6** · 10-23: 99.3 / 99.8 / 91.9 / 93.2 / 93.0 · 10-26: **84.1 / 84.1 / 77.4 / 83.9 / 57.1** (own 99.9 / 99.9 / 91.9 / 99.7 / 99.9) | 83 of 182 enabled (P 2, T1 13, T2 19, GY 0, Gen 49); **broken 0**: 55 rare on these days (replay 0 too), 28 lost to coverage / old gate | broker rejects 12 (+2.4R), "missed: triggered" 6 (+3.1R), crosscheck 1 (+0.3R), job crash 1 (Primary 10-23, 4.1 min, **fixed PR #117**), late start 10-26 (all accounts 10 of 63 decision bars, Gen 27) | unintended skips +5.8R net (19 signals); 10-26 late-start replay **−105R / −$1,495** over 593 trades (would have lost; Primary −12.6R / −$140, missed1026 old gate −1.5R / −$26) |

Last audit: **2026-10-26**. Next: Thu 2026-10-29 (sessions 10-27..10-29; first sessions with the GX1 clock gate).

## 2026-10-26 — answer first

- **Coverage.** Outside the 10-26 late start (no scheduled trade.yml run; all accounts from ~10:39, Gen 12:02 — known)
  every account evaluated ≥ 99.7% of its decision bars on 10-26, except **Testing 2 at 91.9%** (266 polls vs 316;
  8.1% of symbol decisions skipped on 10-23 and 10-26 alike) — OPS-POLL stays open, no gap > 2.5 min. 10-22 is the
  pre-fix phase lock (T2 63.7%, Gen 52.6%, fixed 10-23). Below ~90%: T2 / Gen on 10-22, everyone on 10-26 (outage).
- **One crash, fixed.** 2026-10-23 10:47 ET Primary's job ended in `AlpacaBroker.can_short` (alpaca-py rejects asset
  exchange "TXSE", pydantic ValidationError); the next scheduled job took over after a 4.1-minute gap. Housekeeping
  fix merged before the 10-27 session (PR #117): raw `/assets/<symbol>` fallback, else "not shortable".
- **Never fired: none broken.** No module load errors (`build_strategies` LOAD_FAILURES empty in all accounts), every
  context column (breadth, breadth_open, spy_fo, qqq_fo, qqq_vwap) drives at least one firing setup, all modules exist,
  pinned ETFs (TQQQ, SPXL) are in the universe. The replay fires 28 of the 83 never-fired setups: Gen 18 (10-22 phase
  lock 178 signals, 10-26 before 12:02 75), T2 6 / T1 3 (1–5 each, 10-22..10-26 — the old bar-count gate; GX1 from
  10-27). The other 55 do not fire in the replay either: rare on these days (index-dip / breadth-turn / regime-gated
  designs, e.g. IDX1-5, LD1-8, NM-RW*, 31 GEN).
- **Unintended blocks are small:** 19 signals in 3 sessions, +5.8R net if taken. Broker rejects (12): a market bracket
  whose 0.5R target (once the stop) the price had already passed at submit — Alpaca refuses the order. Not a code bug;
  re-anchoring the bracket would be an exit change (not proposed: +2.4R over 10 priced).
- **Place in line:** 130 signals lost to another setup holding the symbol, −29.7R net (Graveyard 85, −30.4R). The
  lost trades were worse than average in every account except a handful (Primary 13, +2.9R; T2 13, +2.4R) — **no
  setup_order or cap change suggested.**
- **Most costly intended blocks (no change):** not shortable/ETB +92.5R (312; T1's L3 refire on non-borrowable 2x
  ETFs, 82 on 10-26, repeat symbols), lot cap +27.5R (96; T1 L3 self-stacking on 10-26), max positions per setup
  +12.2R (39, Graveyard). The spread filters saved −63.3R, twin cap −13.1R, opposite side −10.6R.

## 1. Poll coverage per account and session

| account | session | polls | first poll | longest gap (at) | gaps > 3 min | data-stale polls | decision bars missed (own window) | late-start bars | coverage % |
|---|---|---|---|---|---|---|---|---|---|
| Primary | 10-22 | 379 | 09:30 | 1.9 min (09:50) | 0 | 0 | 0.7% | 0 | 99.3 |
| Primary | 10-23 | 382 | 09:30 | **4.1 min (10:44, job crash)** | 1 | 0 | 0.7% | 0 | 99.3 |
| Primary | 10-26 | 316 | 10:39 | 1.5 (11:00) | 0 | 0 | 0.1% | 10 | 84.1 |
| Testing 1 | 10-22 | 351 | 09:30 | 2.4 (09:50) | 0 | 0 | 4.7% | 0 | 95.3 |
| Testing 1 | 10-23 | 383 | 09:30 | 1.8 | 0 | 0 | 0.2% | 0 | 99.8 |
| Testing 1 | 10-26 | 316 | 10:39 | 1.5 | 0 | 0 | 0.1% | 10 | 84.1 |
| **Testing 2** | 10-22 | 157 | 09:30 | **17.5 (09:50)** | 40 | 0 | **36.3%** | 0 | **63.7** |
| **Testing 2** | 10-23 | 321 | 09:30 | 2.4 | 0 | 0 | 8.1% | 0 | 91.9 |
| **Testing 2** | 10-26 | 266 | 10:39 | 2.1 | 0 | 0 | 8.1% | 10 | 77.4 |
| Graveyard | 10-22 | 329 | 09:30 | 2.3 | 0 | 0 | 7.9% | 0 | 92.1 |
| Graveyard | 10-23 | 331 | 09:30 | 2.3 | 0 | 0 | 6.8% | 0 | 93.2 |
| Graveyard | 10-26 | 316 | 10:38 | 1.6 | 0 | 0 | 0.3% | 10 | 83.9 |
| **Generated** | 10-22 | 126 | 09:30 | **32.6 (09:50)** | 53 | 0 | **47.4%** | 0 | **52.6** |
| Generated | 10-23 | 330 | 09:30 | 2.5 | 0 | 0 | 7.0% | 0 | 93.0 |
| Generated | 10-26 | 233 | **12:02** | 1.7 | 0 | 0 | 0.1% | **27** | 57.1 |

status.json health at each close: `data_outages` [], `outage_actions` [], `data_stale` none, `flatten_failed` [] in all
accounts and sessions. Missed decision bars of the poll gaps cannot be priced from the journal (no signal was
computed); the replay below gives their size, and earlier evidence (pollspeed1022, gx1clockgate1026) puts the trades
they add at about 0 R after costs.

## 2. Setups that never fired (enabled, zero journaled signals over the sessions they were live)

| account | enabled | never fired | replay fires (lost to coverage / gate) | replay 0 too (rare on these days) | broken |
|---|---|---|---|---|---|
| Primary | 14 | 2 | 0 | NS1-rsidip-rsi5pop-long, ST7-rsi50dn-long-pm-t1s1-FD (new 10-26) | 0 |
| Testing 1 | 35 | 13 | MF1-945-flowsell-vwapup 6 (10-26 before 10:39, window 09:50–10:30), NS3-failed-vwap-reclaim-short 1, ST8-volspikedn-long-pm-t1s1-FD 1 (10-23) | IDX1 ×2, IDX2, IDX3, IDX5 (index dip by 09:45/09:55 — none on these days; 10-26 window closed before the start), RW6G1-ns2-up3-vwap2sd-short, ST5, ST7, ST7Q (qqq_vwap), LIQ-pdl-sweep | 0 |
| Testing 2 | 48 | 19 | CWT05-flush-m05-v5-long 5, CWT05-flush-m075-v5-long 4, CWT04-backside-vwaptest-a15 2, CWT04-backside-lh-a15 1, NM-RWR3 1, NS3V1-am-widestop-short 1 | LD1–LD8 (breadth / index turn; none on these days), NM-RWN3, NM-RWN5, NM-RWR1, CWT04-backside-lh-a25, CWT04-backside-vwaptest-a25 | 0 |
| Graveyard | 22 | 0 | — | — | 0 |
| Generated | 63 | 49 | 18 setups, 286 replay signals: 10-22 phase lock 178 (e.g. GEN-261021-04 71, GEN-261020-09 56), 10-26 before 12:02 75 (GEN-261021-07 29, GEN-261026-04 12), 10-23 3 (GEN-261022-07) | 31 (incl. GEN-POD1022-01/02/03, live since 10-26 only, from 12:02) | 0 |

Checks for "broken": module files exist for every lab setup; `build_strategies` on each account config loads all
(LOAD_FAILURES empty); a firing setup exists for each context column in T2/Gen; TQQQ / SPXL / QQQ are in every
universe (SPY is added through the context symbols); `min_adv` of the never-fired setups is $0–500M (POD1022-01
$500M by design); the replay (same frozen setups, same code) also fires 0 for the 55 "rare" ones, so their masks are
not failing silently in live only. The replay universe is the lab universe ∩ live (~1,220 names), so the "rare" list
is an upper bound for names outside it.

## 3. System errors and unintended blocks

| what | account / when | count | what-if gross / net R | note |
|---|---|---|---|---|
| Broker reject: bracket target/stop already passed at submit | T1 1 (10-22), T2 6 (10-22 5, 10-23 1), GY 5 (10-22 1, 10-23 4) | 12 (10 priced) | +3.02 / **+2.39** | CWT14 failbrk 0.5R-target setups 10, ST1 1, CWT13 1 (stop side). Quote moved past the target between bar close and submit (7–25 cents). Journaled, not fatal |
| "missed: triggered at" (orb20_a stop entries) | T1: 10-22 ×2 (09:50 poll ran 2.4 min), 10-26 ×4 (late start) | 6 | +3.26 / **+3.08** | |
| Price crosscheck | T2 TSLL 10-22 09:50 (2.13% > 2%) | 1 | +0.40 / +0.34 | working as designed (stale bar vs quote) |
| **Job crash** (exception) | Primary 10-23 10:47 ET, `can_short` → alpaca-py ValidationError on exchange "TXSE" | 1 | — | 4.1-min handover gap (next scheduled job). **Fixed: PR #117** (merged 2026-10-26 evening, tests/test_can_short_txse.py) |
| Outage: no scheduled run 10-26 (known) | all accounts to ~10:39, Gen to 12:02 (numba crash, PRs #114/#116) | 10 / 27 decision bars | replay: **−105.0R, −$1,495** (593 trades: P 27 −12.6R −$140 · T1 101 −25.8R −$119 · T2 108 −33.4R −$467 · GY 263 −29.2R −$352 · Gen 94 −4.0R −$417) | GX1-gate replay, research cost model; Primary in missed1026.md (old gate) −1.5R / −$26. Avoided losses, not money left behind |
| Data-stale pauses / data outages | — | 0 | — | none in any account |
| Handover gaps between CI jobs | 10-22 15:07, 10-23 15:05, 10-26 none | 0 > 3 min | — | max 2.5 min (normal) |

## 4. Place in line (lost to another setup already holding the symbol: twin held / lot cap / opposite side / max positions, held by a different setup)

| account | lost | net R (avg) | biggest losers of the queue | verdict |
|---|---|---|---|---|
| Primary | 13 | +2.91 (+0.22) | MF4-h40-open-flowsell 7 (−0.6R, to its -FD twin), MF2-open-rsimidhi-flowsell 3 (+2.2R, to its -FD twin), MF4-FD 3 (+1.3R, to RW3/RW5) | twins by design; n tiny |
| Testing 1 | 18 | −4.81 | exhaustion_short-FD 5 (+0.25R), MF3-open-flowsell-rsi5hi 4 (−2.5R) | worse than average |
| Testing 2 | 13 | +2.44 | NM-MF3-qqqdn-gapdn-FD 3 (+2.7R, +0.90 avg vs its live +0.61; lost to NM-AR-AM-gapdown-capitulation-long), MF5 non-FD 3 (+1.6R, to its -FD twin) | n = 3; no change |
| Graveyard | 85 | −30.42 (−0.36) | heat_fade_short-FD 25 (−5.9R), CWT14-failbrk-orl-p05-long 22 (−8.9R), NS2-sma50break-overbought-short 16 (−3.3R) | worse than average |
| Generated | 1 | −0.61 | — | — |

No setup_order or cap change suggested: the queue's lost trades were not better than average anywhere with a sample
worth acting on.

## 5. Intended blocks that cost the most this period (one line each, no change)

1. **not shortable/ETB** — 312 skips, +92.5R net (T1 +82.2R: L3-gap-slope-fromopen-FD refiring on non-borrowable 2x
   single-stock ETFs CRWG / CWVX / NCLD / NBIG / NBIL, 82 on 10-26; repeated symbols, not tradable short anyway).
2. **lot cap** — 96 skips, +27.5R (T1 49 on 10-26, mostly L3 stacking on its own lots; Primary 15 on 10-22 +5.5R).
3. **max positions per setup** — 39 skips (Graveyard), +12.2R.
4. **setup daily loss limit (−2R)** — 694 skips, +3.7R net (T1 10-22 +50.5R before it was switched off that
   evening; Graveyard −24.4R and T2 −22.4R saved).
5. Saved money: spread filters −63.3R (387), twin held −13.1R (53), opposite side −10.6R (53), split-tape gate −4.5R (22).

Educational only — not financial advice.
