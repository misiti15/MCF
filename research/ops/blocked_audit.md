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
| **2026-10-29** | 10-27, 10-28, 10-29 (GX1 clock gate) | decision minutes of 77: 10-27 77 / 77 / 77 / 77 / 77 · 10-28 77 / 77 / **76** / 77 / **76** (handover 5.7 / 5.8 min, 14:35 bucket) · 10-29 77 ×5 (99.8% overall; polls < 90%: T2 70-82%, GY 72-82%, Gen 59-69%, non-lab only) | 67 of 209 enabled (P 0, T1 7, T2 10, GY 0, Gen 50); **broken 0** (load failures 0; rare by design / regime-gated / young; GEN-261020-09 low odds but fires in replay) | broker rejects 12 (8 bracket leg past base −8.4R, 4 buying power +2.5R), crosscheck 1 (−0.4R), no quote 1 (+0.9R), missed-triggered 0, crash 0; missed 14:35 bucket T2 / Gen 10-28 (≈ 1-5 signals); Gen 8 unbooked (HK-RECON-GEN) | unintended skips **−5.4R net** (14 signals, would have lost); place in line 212, −60.8R, no change; ETB +40.6R (T1 L3 2x ETFs), rest saved money; no fix, no decision |
| **2026-11-02** | 10-30, 11-02 (GX1; Testing cost filter from 10-30; R2A legs T2 from 11-02) | decision minutes of 77: 10-30 **75 ×5** (handover 11.2-13.8 min, 14:40 + 14:45 decisions; standby setup-python ~10 min) · 11-02 77 / 77 / 77 / **76** (GY 14:30, slow 16 s poll) / 77 (759 / 770 = 98.6%; polls < 90%: T2 79 / 77%, GY 80% on 10-30, Gen 76 / 66%, non-lab minutes only) | 67 of 209 enabled (P 1, T1 8, T2 18, GY 0, Gen 40); **broken 0** (load failures 0; R2A short leg idle by its regime: 11-02 was a long-leg day, spy_prng present) | broker rejects 50, all buying power (GY 38 on 11-02 −2.6R, Gen 12 on 10-30 +8.0R); crosscheck / no quote / missed-triggered / crash / data-stale 0; 11 missed decision minutes (≈ 31,000 symbol-minutes, not priceable); Gen 39 unbooked (HK-RECON-GEN); Primary −2R latch one lot late 11-02 (HK-LATCH, −1.0R) | unintended skips **+5.4R net** (50 signals); place in line 204, −70.1R, no change; Testing cost filter 91 skips −29.8R saved; ETB −282R saved overall (T2 +36.5R); no fix, no decision |
| **2026-11-05** | 11-03, 11-04, 11-05 (7 accounts from 11-05; UNI1 T2 from 11-04, ROLL1 from 11-05) | decision minutes of 77: 11-03 **76 / 76 / 76 / 76** / 77 (14:30 hand-over) · 11-04 **76** / 77 / 77 / **76** / 77 (14:30) · 11-05 **74 / 75 / 74 / 75 / 74**, Explore 1 **75**, Live Lab **75** (14:40 + 14:45 outage gap 12.7-14.8 min; 10:05 P / T2 130-s fetch; 10:10 Gen) (1,286 / 1,309 = 98.2%; polls < 90%: GY 78-85%, Gen 82 / 73 / **47%**, T2 85% 11-03, E1 77%, LL 81%) | 63 of 252 enabled (P 0, T1 6, T2 14, GY 0, Gen 20, E1 13, LL 10); **broken 0** (load failures 0; ROLL1 42: 19 fired day 1, 23 index / breadth gated on a crash day; IDX dip met, no 20% bounce, checked on SIP bars) | crosscheck 13 (+18.3R, Gen MU complex 11-05), buying power 83 (+15.9R: GY 59 11-03, Gen 20 at 14:50 halt-restart #152), bracket 36 (−8.1R), missed-triggered 1 (−1.1R); 23 missed decision minutes (14 outage #151, 6 at 14:30 hand-over, 3 slow fetch / poll); restart catch-up entries 61 (backlog); Gen 69 unbooked (#154) | unintended skips **+25.0R net** (133; +12.1R without the halt-restart 20); place in line 261, +0.3R, no change (Gen +11.1R, 1 day); costliest intended GY ETB +32.1R, T1 split-tape +14.9R; −2R stop −368R saved; no fix, no decision (14:30 hand-over alignment queued) |
| **2026-11-09** | 11-06, 11-09 (both bot-dispatched; 11-06 change-over 14:38, 11-09 08:50 start + self-hand-over 14:39; EXPO1109 GEN temp moves 11-09) | decision minutes of 77: 11-06 77 / 77 / **76** / **76** / **76**, Explore 1 77, Live Lab **76** (14:35 bucket at the 14:38 change-over) · 11-09 **76** (P, 14:30 bucket at the self-hand-over) / 77 ×6 (1,073 / 1,078 = 99.5%; 08:50 start polled from 09:30:01 = 0 lost; polls < 90%: GY 70 / 67%, Gen 53 / 63%, E1 78% 11-09, LL 82 / 82%, non-decision minutes only) | 71 of 211 enabled (P 0, T1 2, T2 2, GY 0, Gen 44, E1 11, LL 12); **broken 0** (load failures 0; two up days: breadth < 0.5 / SPY- / QQQ-down gated GEN, IDX no dip, LD breadth, CWT04 / CWT05 / CWT13-z075 crash-day setups; moved GEN-261019-03 / -261026-02 in T1 p0 0.40 / 0.87) | buying power 1,025 (Gen 785 −131.7R, GY 240 +3.9R; HK-GEN-BP), bracket 16 (+6.7R), crosscheck 8 (−0.1R), missed-triggered 4 (T1 orb20_a 11-09, −1.1R); 5 missed decision minutes (≈ 48 signals, not priceable); data-stale / outage / crash / failed flatten / unbooked 0 | unintended skips **−122.3R net** (1,053; −51.1R gross; would have lost — Gen BP rejects saved money); place in line 387, −22.1R, no change (GY +14.8R, mostly twin heat_fade, split days); costliest intended Primary ETB +34.2R (L3-fromopen-FD), max positions per setup +84.1R (Gen GEN-261021-02 / GY CWT12 coil); no fix, no decision |
| **2026-11-12** | 11-10, 11-11, 11-12 (10 accounts from 11-12; rename 11-11/12: T1 = On Deck, T2 = Testing A, E1 = Testing B, LL = Testing C; D / E / F new 11-12; TEAM-6 Primary from 11-11; from 11-12: LR3 / LR8 cost-in R latches + live cost model, LR5 position check, halts −300R in testing / Gen, Gen / GY sizing + caps REPV) | decision minutes of 77: 11-10 77 ×7 · 11-11 P **76** (14:30 bucket, hand-over) / OD 77 / A 77 / GY **76** (14:30) / Gen **74** (14:40-14:50 + 15:00, 5.8-min polls) / **Testing B 51 (66.2%, runner lost 12:18 → 14:30, 132.6 min, OPS-EX1-RUNNER)** / C 77 · 11-12 P 77 / OD 77 / A 77 / GY **76** (14:35, 4.2-min hand-over) / Gen **74** / B 77 / C 77 / D / E / F 77 (1,813 / 1,848 = 98.1%; polls < 90% of 384: OD 84-86%, A 84% 11-12, GY 68-83%, Gen 53-70%, B 49-85%, C 71-74%, P 88% 11-10) | 66 of 254 enabled (P 0, OD 1, A 4, GY 0, Gen 31, B 8, C 10, D 5, E 5, F 2); **broken 0** (load failures 0; Gen 31 = SPY- / QQQ-down-margin and breadth-gated: no "ltm" context setup fired on any of the 3 days; B / C / D / E / F = IDX / LD index-turn, CWT04 / LIQ-pdl crash-day, 2 GEN graduates 1 day) | buying power 762 (Gen 394 −163.5R, GY 368 −2.0R; **0 on 11-12 after the REPV sizing change**), bracket 9 (+1.6R), crosscheck 10 (+2.1R), missed-triggered 2 (OD orb20_a, +0.2R); LR5 position_mismatch 0 (no skips, health [] in all 10); data-stale / outage / failed flatten / unbooked / halt skips 0; 35 missed decision minutes (26 Testing B runner loss ≈ 2.5 signals; 9 hand-over / slow Gen poll) | unintended skips **−161.7R net** (783; −113.3R gross; would have lost — Gen BP rejects saved money); place in line (other setup) 307, +11.5R, no change; Primary L3-gap-slope-fromopen-FD 30-lot cap 648 skips +362.5R on 11-12 (intended); costliest other intended Primary ETB +139.3R, GY spread +120.8R; no fix, no decision |

Last audit: **2026-11-12**. Next: Mon 2026-11-16 (sessions 11-13, 11-16).

## 2026-11-12 — answer first (sessions 11-10 Tue, 11-11 Wed, 11-12 Thu; 7 accounts, 10 from 11-12)

Script `research/ops/blocked1112_audit.py` (= blocked1109_audit.py with the dates and the 10 accounts set; adds the LR5
"position mismatch" skip as unintended); output `blocked1112_results.json`. Reused, not redone: `research/bdi/nightly1110`,
`nightly1111`, `nightly1112`. No replay was run. Account names follow the owner rename of 11-11/12 (On Deck = old
Testing 1, Testing A = old Testing 2, Testing B = Explore 1, Testing C = Live Lab); Testing D / E / F ran their first
session on 11-12. **Rule changes inside the window** (research/ledger.jsonl): from 11-11 TEAM-6 in Primary (frozen to
11-13) and the EXPO1109 revert; from 11-12 LR3 / LR8 (Primary −20R halt and −2R latch count R after costs; pnl_adj uses
the live cost model), LR1 / LR4 / LR5 / LR7, Testing D / E / F wired and filled, account halt 120R → 300R in On Deck /
Testing A-F / Gen, Gen and Graveyard buying_power_multiple 3.8 → 1.8 / 1.6 with slots 300 and per-setup caps 150 / 75,
generic per-setup cap 10 → 30 in Testing B-F, Testing A back to the full universe, ODX-1 split-tape gate off in On Deck,
GEN-GRAD (5 Gen setups to D / E / F). The what-if R below uses the audit's fixed cost model on all three days (not the new
LR8 model), so the days stay comparable; run 2 what-if trades carry no $ (pnl 0), so values are in R only.

- **Coverage: 1,813 of 1,848 decision minutes polled (98.1%).** **Testing B 11-11: 51 of 77 (66.2%)** — the hosted
  runner lost communication (GitHub annotation, resource starvation, not code); last poll 12:18:13, resumed by the 14:29
  hand-over job at 14:30:49 (132.6 min, 26 decision minutes, ≈ 110,000 symbol-minutes, ≈ 2.5 signals at Testing B's
  rate); already logged as OPS-EX1-RUNNER. Hand-over misses: Primary 11-11 14:30 bucket (1.9-min gap), Graveyard 11-11
  14:30 and 11-12 14:35 (4.2-min gap), Gen 14:40 / 14:50 / 15:00 buckets on 11-11 and 11-12 (decision poll 5-6 min, max
  gap 5.9 / 6.3 min; those minutes held 2 / 0 / 0 Gen signals on other days) — 5 of 24 account-sessions (OPS-HANDOVER /
  OPS-POLL, both queued). Every other account-session 77 / 77, longest gap ≤ 4.2 min. data-stale polls 0, `data_outages`
  [], `flatten_failed` [], LR5 `position_mismatch` [] in all 10 on 11-12. Polls < 90% of 384 (non-decision minutes only):
  On Deck 321 / 329, Testing A 321 (11-12), GY 317 / 318 / 262, Gen 267 / 207 / 205, Testing B 188 (11-11), Testing C
  284 / 271, Primary 338 (11-10, 88%).
- **Never fired: 66 of 254 enabled, broken 0.** Load failures 0 in all 10 freeze files, every module exists. Gen 31 of 93,
  all context-gated: the SPY- / QQQ-down-margin ("ltm") setups and breadth < 0.3-0.5 windows — no "ltm" context setup
  fired in Gen on any of the 3 days while QQQgt / SPYgt / QQQup did (hundreds of signals), so the gate, not the code, held
  them; nearly all last fired 11-05 / 11-09. On Deck: GEN-261026-02 (late breadth_open, 1 day, p0 0.87). Testing A:
  CWT13-vwapstretch-z075-short (46 lifetime, last 11-06, crash-day pullback), GEN-261022-07 / -261026-03 (1 day, p0
  0.53 / 0.52), NS1-rsidip-rsi5pop-long (first day). Testing B / C / D / E / F 30: IDX (no index dip), LD (breadth-up /
  index-turn), NM-RWN4 / RWN5 (spy_fo), CWT04 / CWT05-m075-v5 / LIQ-pdl / NM-PM-gapdn (crash-day / rare), GEN-261026-03
  and GEN-261027-01 (graduates, 1 day, p0 0.52 / 0.38) — same rare-by-design list as 11-09.
- **Unintended blocks: 783 signals, −113.3R gross / −161.7R net (would have lost).** Buying power **762** (Gen 394
  −163.5R net — GEN-261029-03 165, GEN-261029-01 68, GEN-261026-10 37; GY 368 −2.0R — CWT12 coil k4 76, CWT14 orl p05 70
  / lowvol 58), all on 11-10 / 11-11 and **0 on 11-12**, the first session after the Gen / GY sizing change (REPV-1 /
  REPV-11) — HK-GEN-BP looks addressed; one more session to confirm. Bracket leg past base price 9 (+1.6R; GY 6, the same
  CWT05 flush signal in Testing C / D / F). Crosscheck 10 (+2.1R). "missed: triggered" 2 (On Deck orb20_a 11-11, +0.2R).
  LR5 "position mismatch" skips 0; account-halt / HALT-flag skips 0; no broker crash, failed flatten or unbooked order.
- **Place in line: 307 lost to a different setup, +11.5R net, no change.** Primary 9 (−0.2R; MF4 base to its -FD twin),
  On Deck 8 (−5.7R), Testing A 32 (−2.9R, opposite side: CWT14 pdl R2A short to its p10 long 21), **Graveyard 241
  +16.8R** — NS2-sma50break-overbought-short 69 +40.7R to its -FD twin / RW6 (twin by design), heat_fade_short-FD 46
  −22.9R, CWT14 orl p05 33 +6.8R; Gen 17 +3.5R. By reason (all, incl. own-setup stacking): lot cap 70 +3.2R, opposite
  side 137 −13.9R, GY max concurrent positions 296 −63.4R (11-12, new 300-slot sizing), max positions per setup GY 477
  +34.9R / Gen 147 −133.1R / Testing F 84 +6.4R. **Primary L3-gap-slope-fromopen-FD hit its 30-trade cap on 11-12: 648
  skips, +362.5R net what-if — intended** (the cap is the design; the day was its +31R driver, nightly1112).
- **Most costly intended blocks (no change):** Primary per-setup cap +362.5R (above); Primary not shortable/ETB +139.3R
  (864, L3-fromopen-FD, 557 on 11-12); GY spread filter +120.8R (761); On Deck spread +41.6R, Primary spread +38.9R; GY
  max per setup +34.9R; GY twin held +19.7R. Saved money: Gen max per setup −133.1R, On Deck ETB −123.7R (L3-rsi5hi-FD),
  GY −2R latch −91.4R (1,075), On Deck split-tape gate −81.8R (11-10 / 11-11; gate off from 11-12, ODX-1), GY max
  concurrent −63.4R, Gen ETB −51.6R, Testing cost filter −42.3R (On Deck −22.3R, Testing A −20.0R), Primary −2R latch
  −21.4R, Testing E ETB −18.3R / spread −12.2R (day 1).
- **No fix, no decision.** Every item has an owner (OPS-EX1-RUNNER, OPS-HANDOVER, OPS-POLL, HK-GEN-BP — watch 11-13 for
  BP rejects staying at 0).

Educational only — not financial advice.

## 2026-11-09 — answer first (sessions 11-06 Fri, 11-09 Mon; 7 accounts)

Script `research/ops/blocked1109_audit.py` (= blocked1105_audit.py with the dates set; empty place-in-line frames
guarded); output `blocked1109_results.json`. Reused, not redone: `research/bdi/nightly1106`, `nightly1109` (closes,
rejects, latches, hand-overs). No replay was run. **Both sessions were bot-dispatched** (GitHub's scheduler missed):
11-06 changed over at 14:38 to a scheduled run; 11-09 started 08:50, polled from 09:30:01 and self-handed-over at
14:39. Primary hit the −20R account halt ~10:55 on 11-06; the −2R latches fired on both days. **Rule changes inside the
window** (research/ledger.jsonl): from 11-09 EXPO1109 (5 GEN setups temporarily Gen → Testing 1 / 2, revert after the
11-10 close); ops fixes in effect from 11-06: #151 self-hand-over, #152 halt restore, #154 Gen booking. Both were up
days (SPY ≈ +1.0% / +1.4%), so the never-fired list leans on one regime (the mirror of 11-05).

- **Coverage: 1,073 of 1,078 decision minutes polled (99.5%).** The 5 misses are all at the hand-over: **11-06 14:35
  bucket (minute 14:39) in Testing 2 / Graveyard / Gen / Live Lab** at the 14:38 change-over (gaps 1.9-4.5 min), and
  **11-09 14:30 bucket (minute 14:34) in Primary** at the self-hand-over (14:34:13 → 14:36:01, 1.8 min; GX1 does not
  catch up an older bucket). Size ≈ 3,500 symbol-minutes each, ~48 signals at those accounts' signal rate (GY 24, Gen 16,
  P / T2 ~4), not priceable. Running tally of the hand-over miss since 11-02 (outage day excluded): **12 of 29
  account-sessions** (OPS-HANDOVER alignment idea still queued; Gen's 3.5-4.2-min decision poll makes a fixed slot end
  hard). **Late 08:50 start on 11-09: 0 coverage lost** — the run was polling at 09:30:01 in all 7, same as a normal
  start; its only cost is the earlier slot end (14:30) that put the hand-over next to the 14:30 decision. Longest gap
  per account ≤ 5.3 min (Gen 10:30 on 11-06, 4 gaps > 5 min that day, none on a lost decision); data-stale polls 0,
  `data_outages` [], `flatten_failed` [], phase `closed` in all 7. **Polls < 90% of 384:** GY 268 / 257 (70 / 67%), Gen
  203 / 243 (53 / 63%), Explore 1 300 (78%, 11-09), Live Lab 314 / 315 (82%) — non-decision minutes only. Decision poll
  → next poll (median): P 1.3-1.4, T1 1.7-1.8, T2 1.4-1.6, **GY 3.0-3.2 (was 1.9-2.7)**, **Gen 4.2 / 3.5** (11-05 4.3),
  E1 1.8-2.7, LL 2.5-2.6 min (watch, OPS-POLL: a decision is lost past ~6 min).
- **Never fired: 71 of 211 enabled, broken 0.** Load failures 0 in all 7 freeze files, every module exists. Gen 44 of
  93: all context-gated (breadth / breadth_open < 0.5, SPY- / QQQ-down, late windows) and nearly all fired through 11-05
  (bursty on down days: e.g. GEN-261019-04 0 / 20 / 0 / 41 / 53 on 10-29 .. 11-05); context setups did fire on both days
  at the 11-05 rate (Gen breadth 11 / 15 of 28, spy_fo 15 / 14 of 31), so nothing is stuck. T1: moved GEN-261019-03 /
  -261026-02 (1 day, screen odds of 0 0.40 / 0.87). T2: NM-MF3-qqqdn (QQQ-down gate) and NM-HL-T75-pm-long (57 lifetime,
  weak-day fires). Explore 1 / Live Lab 23: IDX (no dip), LD (breadth-up / index-turn), NM-RWN4 / RWR1, RW6G1, CWT04 /
  CWT05 / CWT13-z075 / LIQ-pdl (crash-day pullback setups; CWT04's last signals were ETB skips) — same as the 11-09
  low-rep review.
- **Unintended blocks: 1,053 signals, −51.1R gross / −122.3R net (would have lost).** Buying power **1,025** (Gen 785,
  −131.7R net — GEN-261026-10 172, GEN-261029-01 69; GY 240, +3.9R, 10:20-10:50 on 11-09) = HK-GEN-BP, queued; the
  rejects acted as a capacity cap that saved money. Bracket leg past base price 16 (+6.7R; GY 15 on 11-06, CWT14 legs on
  inverse / index ETFs). Crosscheck 8 (−0.1R; Gen OMH 7-11% on 11-09). "missed: triggered" 4 (T1 orb20_a NVDA / NVDL /
  NVDX / ST at 09:50-09:51 on 11-09, −1.1R). No broker crash, exception, failed flatten or unbooked order.
- **Place in line: 387 lost to a different setup, −22.1R net.** Primary 33 (MF4 non-FD 31 to its -FD twin, −27.7R),
  T1 7 (+1.2R), T2 12 (−0.3R), **Graveyard 216 +14.8R (+0.07 vs live −0.10)** — twin heat_fade_short-FD 63 +6.5R, CWT12
  coil k4 / k6 22 +11.7R; days split (11-06 twin held +16.6R, 11-09 −17.1R); Gen 121 −11.3R (−0.09 vs −0.17), Explore 1
  1 (+0.2R). **No setup_order or cap change suggested** (GY lead is a twin by design plus one big coil day).
- **Most costly intended blocks (no change):** max positions per setup +84.1R (495; Gen +59.6R GEN-261021-02 158 on 11-06,
  GY +46.6R CWT12 coil k4 167; Explore 1 −22.2R); Primary not shortable/ETB +34.2R (442; L3-fromopen-FD 349 on L3 ETFs);
  spread filter +16.4R overall (GY +23.8R, Primary −19.0R); opposite side held GY +12.2R; Primary account halt 11-06
  +3.9R (92). Saved money: split-tape short gate T1 −83.4R (121, 113 on 11-09), setup −2R stop −82.0R (722; GY −78.1R,
  Primary −3.9R), ETB −78.3R overall (GY −66.6R), twin held −27.0R (Primary MF4 −27.7R), Testing cost filter −22.9R,
  spread vs stop −16.3R, lot cap −6.1R.
- **No fix, no decision.** Every item already has an owner (HK-GEN-BP, OPS-HANDOVER, OPS-POLL).

Educational only — not financial advice.

## 2026-11-05 — answer first (sessions 11-03 Tue, 11-04 Wed, 11-05 Thu; 7 accounts from 11-05)

Script `research/ops/blocked1105_audit.py` (= blocked1102_audit.py with the dates set and Explore 1 / Live Lab added);
output `blocked1105_results.json`. Reused, not redone: `research/bdi/nightly1103`, `nightly1104`, `nightly1105` (polls,
handovers, closes, rejects, the 14:50 restart). SIP 1-min SPY / QQQ for 11-03..11-05 09:30-10:06 fetched read-only to
check the IDX triggers. No replay was run. **Rule changes inside the window** (research/ledger.jsonl): from 11-03 MF3-FD /
MF5-FD to the Graveyard, SO-1A (R2A legs outside T2's scale-out cap), RW3S added to Testing 2; from 11-04 DM-N3
(NS5-FD / ST4-FD / RW6G1-FD to the Graveyard) and **UNI1 (Testing 2 top-500 pool)**; from 11-05 **ROLL1 (42 setups to
Explore 1 / Live Lab)**. Ops fixes merged after the 11-05 close (in effect from 11-06): PR #151 self-handover, #152
HK-HALT-RESTART, #154 HK-GEN-BOOK (branch `claude/gen-reconcile-1105`, the Gen booking gap; not duplicated here). 11-05
was a crash day (SPY −4.1%, QQQ −5.2%), so the never-fired list and the block values lean on one regime.

- **Coverage: 1,286 of 1,309 decision minutes polled (98.2%).** The 23 misses: **14:40 + 14:45 in all 7 accounts on 11-05
  (14)** — the GitHub scheduler outage left no standby behind the 08:5x run (limit 14:35-14:40), replacement polled from
  14:49:59-14:50:07, gap 12.7-14.8 min (PR #151 now dispatches a successor); **14:30 at the regular hand-over (6)**: 11-03
  P / T1 / T2 / GY (gaps 3.8-4.8 min straddling 14:30), 11-04 P (14:29:10 → 14:31:03) / GY — with 11-02's GY one, **7
  account-minutes in 3 sessions, all at 14:30** (the slot ends ~14:28-14:30 and GX1 does not catch up an older bucket);
  **10:05 Primary / Testing 2 (2)** — two 130-s data fetches at 10:01-10:06 on 11-05 (crash open; all accounts saw them,
  the others still polled a 10:05 minute); **10:10 Gen (1)** — a 3.8-min poll. Size ≈ 23 × ~3,000-3,400 symbol-minutes,
  not priceable (≈ 5 signals at 14:30 in Primary on other days). Data-stale polls 2 (GY / Live Lab 10:08, non-decision);
  `data_outages` [], `flatten_failed` [], phase `closed` in all 7 at the 11-05 close. **Polls < 90% of 384:** 11-03 T2
  85.2 / GY 78.4 / Gen 81.5%; 11-04 GY 85.4 / Gen 73.2%; 11-05 GY 80.7 / **Gen 47.4%** / Explore 1 76.8 / Live Lab
  80.7% (P / T1 / T2 95-96%, the outage only). **Watch: Gen's decision poll is getting slower** — median time from a
  decision poll to the next poll 2.4 → 2.8 → **4.3 min** (p90 5.1; 9 gaps > 5 min on 11-05); a decision is lost once a
  poll runs past ~6 min (OPS-POLL).
- **Never fired: 63 of 252 enabled (setup-account pairs), broken 0.** Load failures 0 in all 7 freeze files, every module
  exists. **ROLL1's 42 on day 1: 19 fired, 23 not** — all index-direction or breadth gated, a crash day cannot open them:
  SPY-up / QQQ-up shorts (NM-RWN3 / RWN4 / RWN5 / RWR1 / RWR3 / RWR4), breadth-up longs (LD1 / LD4 / LD5), index dip +
  breadth turn (LD2 / LD6 / LD8, LD3 / LD7); **IDX1 / IDX2 / IDX3 / IDX5: the dip was met (QQQ −1.78% by 09:45, −2.27% by
  09:55; SPY −1.12% by 09:45) but no bar 09:50-10:05 closed 20% off the low (`find_trigger` on SIP bars: None for all
  four)** — rare by design, not broken; plus MF2-open-rsimidhi-flowsell (non-FD twin), RW6G1, NM-AMS-N1,
  NM-PM-gapdn-above-pdh (0-2 lifetime in T1 / T2). Testing 1 6 (IDX ×5 on 11-03/04: no dip, QQQ low −0.18 / −0.08%;
  LIQ-pdl-sweep 1 in 17), Testing 2 14 (LD ×8, NM-RWN5 / RWR4, NM-AMS-N1, CWT04 a25 ×2 dormant; NS5-FD 1 session before
  DM-N3), Gen 20 (breadth / breadth_open / qqq_fo gated or 14:00-15:00 windows; 3-session screen odds of 0 ≥ 0.13 for
  all), Primary / Graveyard 0.
- **Unintended blocks: 133 signals, +34.5R gross / +25.0R net** (+12.1R net without the 20 halt-restart rejects).
  Crosscheck 13 (+18.3R; **Gen 10 on 11-05 +19.9R**, the MU / MULL / MUU / RAM / WDCX bounce at 11:10, quote 2-5% above
  the bar — working as designed, and the what-if enters at the stale ref price, so it overstates); buying power 83
  (+15.9R: **GY 59 on 11-03** 10:50-11:20 +2.8R (GY-BP); Gen 24 on 11-05 +13.1R, **20 of them at 14:50 after the halt was
  not restored** (+12.9R; they would have been halted; fixed #152)); bracket leg past base price 36 (−8.1R; Gen 28
  −16.9R, GY 7 +8.4R, Live Lab 1); "missed: triggered" 1 (T1 orb20_a 11-03, −1.1R). **Unintended non-blocks:** the 14:50
  restart poll entered signals on the gap's bars (P 1, T1 5, T2 3, GY 15 (+11 at 14:55), Gen 32, Explore 1 4, Live Lab 1;
  backlog `nightly-1105-restart-catchup-entries`); Gen 69 lots unbooked on 11-05 (fixed #154, `claude/gen-reconcile-1105`).
  No broker crash, exception or failed flatten.
- **Place in line: 261 signals lost to a different setup, +0.3R net.** Primary 15 (−0.04 vs live −0.04; MF4 non-FD to
  its -FD twin), T1 4 (+1.2R), T2 27 (−0.12 vs −0.25; R2A short leg 12 +2.0R to its long leg, by design), Graveyard 157
  (−0.06 vs −0.18; CWT14 orl p05 24 −20.7R), **Gen 57, +11.1R (+0.19 vs live −0.51)** — but 4 trades on 11-04 carry 70%
  of it (+7.8R; without that day +3.3R over 53, +0.06) and n ≤ 6 per setup ("1 day"). **No setup_order or cap change
  suggested.**
- **Most costly intended blocks (no change):** split-tape short gate T1 +14.9R (151, all 11-04; RW7-FD 50); "size < 1
  share after liquidity cap" +13.8R (21; T2 15 +14.8R); Graveyard not shortable/ETB +32.1R (371; CWT09 g5 shorts on the
  crash) though ETB overall saved −62.0R (1,227); opposite side held +11.5R (150; Gen +11.1R); Primary −2R stop +5.4R
  (100, 80 on 11-05). Saved money: setup −2R stop −368.3R (2,305; Graveyard −373.7R), max positions per setup −145.2R
  (375; Gen −96.8R), spread vs stop −133.6R, spread filter −99.9R, **Testing cost filter −81.1R** (212; T1 −56.3R), Gen
  account halt −78.9R (1,061 skips on 11-04 / 11-05), lot cap −21.3R. UNI1 removes names before any signal, so it has
  no skip rows to price (nightly1105 tracks it as an owner flag).
- **No fix, no decision.** Every problem found already has an owner or a merged fix (#151 / #152 / #154, backlog
  restart catch-up, GY-BP). **Queued (housekeeping, OPS-HANDOVER):** the regular hand-over now loses the 14:30 decision
  minute in ~45% of account-sessions (7 of 15, 11-02..11-04); fix idea: end the slot ~20 s after a 5-minute decision poll
  (`job_deadline` aligned to a bucket boundary) so the 2-5-min gap falls between decisions — no decision rule changes;
  check against Gen's slow decision polls first.

### 1. Coverage per account and session (decision minutes of 77; longest gap; polls of 384)

| account | 11-03 | 11-04 | 11-05 | polls 11-03 / 04 / 05 |
|---|---|---|---|---|
| Primary | **76** (14:30) · 3.9 min (14:27:16 → 14:31:08) | **76** (14:30) · 1.9 (14:29:10) | **74** (10:05, 14:40, 14:45) · **14.8** (14:35:14 → 14:49:59) | 382 / 384 / 367 |
| Testing 1 | **76** (14:30) · 4.8 (14:29:12 → 14:34:02) | 77 · 2.5 | **75** (14:40, 14:45) · **14.8** | 381 / 384 / 364 |
| Testing 2 | **76** (14:30) · 3.8 | 77 · 2.6 | **74** (10:05, 14:40, 14:45) · **12.7** (14:37:16 → 14:49:59) | **327** / 354 / 368 |
| Graveyard | **76** (14:30) · 3.9 | **76** (14:30) · 2.4 | **75** · **14.8** | **301 / 328 / 310** |
| Generated | 77 · 3.2 (14:55; handover 14:35 3.2) | 77 · 3.9 (handover) | **74** (10:10, 14:40, 14:45) · **14.8**; 9 gaps > 5 min | **313 / 281 / 182** |
| Explore 1 | — | — | **75** · **14.8** | **295** |
| Live Lab | — | — | **75** · **14.8** | **310** |

First poll 09:30:00-02 everywhere. Decision-poll → next poll (median, min): Primary 1.2 / 1.4 / 1.5, T1 1.6, T2 2.3 / 1.8
/ 1.6, GY 2.7 / 2.1 / 1.9, **Gen 2.4 / 2.8 / 4.3**, Explore 1 2.6, Live Lab 2.5. Fetch median 5-10 s; 11-05 max 131-134 s
(10:01-10:06, every account).

### 2. Never fired (enabled, 0 journaled signals in the sessions they were enabled)

| account | enabled | never | which / why | broken |
|---|---|---|---|---|
| Primary | 10 | 0 | — | 0 |
| Testing 1 | 28 | 6 | IDX1 hold / trail, IDX2, IDX3, IDX5 (11-03 / 11-04, no dip: QQQ low −0.18 / −0.08%, SPY −0.04 / −0.05% by 09:55; moved to Explore 1 / Live Lab 11-05); LIQ-pdl-sweep (1 in 17) | 0 |
| Testing 2 | 46 | 14 | LD1-LD8 (breadth / index-turn gated; 0-4 in 11); NM-RWN5 / RWR4 (spy_fo / qqq_fo up; 19 / 6 before, last 11-02 / 10-26), NM-AMS-N1 (2); CWT04 lh-a25 / vwaptest-a25 (0 in 18, dormant); NS5-sma50-flush-FD (1 session, then DM-N3) | 0 |
| Graveyard | 33 | 0 | — | 0 |
| Generated | 93 | 20 | breadth / breadth_open / qqq_fo gated, 14:00-15:00 and 13:00-15:00 windows, $150M min ADV; 3-session screen odds of 0 ≥ 0.13 (lowest GEN-261020-06 0.13, -261029-09 0.15, -261023-03 0.25); GEN-POD1022-01 / -02 observation (0.85 / 0.73) | 0 |
| Explore 1 (day 1) | 21 | 13 | IDX1 hold, IDX2, IDX5 (dip met, no 20% bounce by 10:05); LD1 / LD3 / LD4 / LD8; NM-RWN3 / RWN5 / RWR4 (index-up shorts); MF2 non-FD, RW6G1, NM-AMS-N1 | 0 |
| Live Lab (day 1) | 21 | 10 | IDX1 trail, IDX3 (same); LD2 / LD5 / LD6 / LD7; NM-RWN4 / RWR1 / RWR3 (index-up shorts); NM-PM-gapdn-above-pdh | 0 |

### 3. System errors and unintended blocks

| what | account / when | count | what-if gross / net R | note |
|---|---|---|---|---|
| Crosscheck (bar vs quote > 2%) | Gen 11-05 10 (+19.9R; MU / MULL / MUU / RAM / WDCX ×7 at the 11:10 poll), 11-04 1; P 11-03 1; T2 11-05 1 | 13 | +18.83 / **+18.33** | as designed; what-if at the stale ref price overstates |
| Broker reject: insufficient buying power | GY 11-03 10:50-11:20 (CWT12 coil k4 15, MF5-FD 8) | 59 | +6.37 / **+2.80** | GY-BP (Graveyard capital in open lots) |
| Broker reject: insufficient buying power | Gen 11-05 14:02-14:03 4, **14:50 20** | 24 | +14.14 / **+13.14** (14:50: +12.9) | 14:50 = halt not restored (fixed #152) |
| Broker reject: bracket leg past base price | Gen 28 (11-05 26: inverse ETFs at the 11:10 bounce), GY 7 (11-05 CWT14 orl twins), LL 1 | 36 | −3.77 / **−8.13** | price past the 0.5R target / stop at submit; not a code bug |
| "missed: triggered" | T1 11-03 VCIG orb20_a | 1 | −1.05 / −1.11 | |
| Missed decision minutes | 14:40 + 14:45 all 7 (11-05 outage); 14:30 ×6 (hand-over); 10:05 P / T2 (130-s fetch); 10:10 Gen (slow poll) | 23 account-min (≈ 70,000 symbol-min) | not priceable | OPS-HANDOVER / #151 / OPS-POLL |
| Restart catch-up entries | 11-05 14:50 first poll, all 7 | 61 entries | (Gen 32: +30.65R real, nightly1105) | backlog nightly-1105-restart-catchup-entries |
| Submitted, not booked | Gen 11-05 | 69 | — | fixed #154 (claude/gen-reconcile-1105) |
| Data-stale polls / outages / crashes / failed flatten | GY, LL 10:08 (stale, non-decision) | 2 | — | |

### 4. Place in line (lost to a different setup holding the symbol)

| account | lost | net R (avg) | live avg net R | biggest | verdict |
|---|---|---|---|---|---|
| Primary | 15 | −0.55 (−0.04) | −0.04 | MF4-h40-open-flowsell 15 (to its -FD twin) | twins by design |
| Testing 1 | 4 | +1.22 (+0.31) | +0.01 | exhaustion_short-FD 3, RW6G1-FD 1 | n tiny |
| Testing 2 | 27 | −3.34 (−0.12) | −0.25 | R2A short 12 (+2.0R, to the long leg), RW3S-FD 5 (−5.4R) | negative; R2A by design |
| Graveyard | 157 | −8.65 (−0.06) | −0.18 | CWT14 orl p05 24 (−20.7R), NS2 non-FD 10 (+5.6R, to its -FD twin), CWT12 coil k4 13 (+2.7R) | negative after costs |
| Generated | 57 | +11.10 (+0.19) | −0.51 | GEN-261019-04 6 (+8.7R), GEN-261021-07 3 (+6.8R); 11-04 4 trades = 70% of R | 1 day; n ≤ 6 per setup |
| Explore 1 / Live Lab | 0 / 1 | — / +0.50 | | | — |

### 5. Intended blocks, cost this period (all accounts, what-if net R; no change)

1. **not shortable/ETB, Graveyard** — 371 skips, +32.1R (CWT09 g5 vwaploss 164 / bounce 116 on the crash); overall ETB saved −62.0R (1,227; Gen −59.9R, T2 −17.3R, Primary −10.5R).
2. **split-tape short gate, Testing 1** — 151 (11-04 only), +14.9R (RW7-FD 50, exhaustion_short-FD 22).
3. **size < 1 share after liquidity cap** — 21, +13.8R (T2 15 +14.8R, 11 on 11-05).
4. **opposite side held** — 150, +11.5R (Gen 57 +11.1R; T2 −4.7R).
5. **Primary setup −2R stop** — 100, +5.4R (80 on 11-05); Graveyard's −373.7R saved.
6. Saved money: setup −2R stop −368.3R (2,305), max positions per setup −145.2R (375), spread vs stop −133.6R (482), spread filter −99.9R (985), Testing cost filter −81.1R (212), Gen account halt −78.9R (1,061), lot cap −21.3R (39), price below minimum −8.8R (12). UNI1 pool: no skip rows (filtered before signals).

Educational only — not financial advice.

## 2026-11-02 — answer first (sessions 10-30 Fri, 11-02 Mon)

Script `research/ops/blocked1102_audit.py` (= blocked1029_audit.py with the dates set, the Testing cost filter as an
intended reason, and missed decision minutes sized in symbol-minutes and in the signals that minute carried on the other
session); output `blocked1102_results.json`. Reused, not redone: `research/bdi/nightly1030`, `nightly1102` (polls,
handovers, closes, rejects). No replay was run. **Rule changes inside the window** (research/ledger.jsonl): Testing 1/2
cost filter `max_stop_cost_r` 0.15 from 10-30; L3 pair promoted to Primary 10-30; NS3-FD / RW4-FD to the Graveyard and
PDL-1a R2A legs into Testing 2 from 11-02 (SO-1A scale-out exemption and MF3-FD / MF5-FD moves only from 11-03); earlier
and still in effect: GX1 lab clock 10-27, Primary ~$4,000 size 10-28 and −2R per-setup stop 10-29, BAR90 10-29.

- **Coverage: 759 of 770 decision minutes polled (98.6%).** 10-30: **every account missed the 14:40 and 14:45 decisions
  (75/77)** — run 41058369921 hit the 6-hour limit at 14:36-14:38 ET and the standby's `actions/setup-python` took
  ~10 min (cache not reserved), so polls stopped 11.2 (P) / 12.3 (T1) / 13.5 (T2) / 13.4 (GY) / 13.8 (Gen) min
  (OPS-HANDOVER regressed; 11-02 fine at 2.0-4.7 min). 11-02: Graveyard missed the **14:30** decision only: its 14:29:14
  poll saw minute 14:28, the next poll took 16.2 s and ended 14:31:07 with minute 14:30, and GX1 does not catch up an
  older bucket. Size: 11 account-minutes ≈ 31,000 symbol-minutes (≈ 2,800-2,950 symbols with bars each), **not priceable**
  (no signal computed); on the other session the same poll minutes carried P 16, T1 2, T2 5, GY 6 (+5 at 14:30), Gen 22
  signals, so roughly 50 signals were never evaluated, about two-thirds in Primary and Gen. No data-stale poll, no data
  outage, no flatten failure, no job crash or exception in any account. **Polls under 90%** (of 384): T2 303 / 297
  (79 / 77%), GY 309 / 348 (80 / 91%), Gen 292 / 253 (76 / 66%): the misses are bucket minutes 1-2 (only orb20_a /
  exhaustion_short / heat_fade use them) plus the handover; OPS-POLL residual, no lab decision lost to them.
- **Never fired: 67 of 209 enabled, broken 0.** Load failures 0 in all 5 freeze files (11-02), every module exists. All
  are rare by design, regime-gated or young (table 2). **PDL-1a R2A legs (Testing 2, day 1 11-02):** context `spy_prng`
  (SPY prior-day range / ATR, `mcf/strategies/lab_context.py` DAILY_COLS) was present — the long leg fired 31 (19
  trades, −2.97R; 12 spread-filter skips), so 10-30's SPY range was above the 0.7956 cut and the short leg was idle *by
  its regime*, not broken (pdl1a_lib: NaN would have given neither leg).
- **Unintended blocks: 50 signals, +9.4R gross / +5.4R net, all "insufficient buying power".** Graveyard 38 on 11-02
  (−2.6R; CWT14 orl p05 9, CWT12 coil k6 6; 10:40-10:50 ET) — its cash is in open lots (395 trades that day); Gen 12 on 10-30 (+8.0R; GEN-261026-02 / -06 ×4,
  14:35-15:00 ET) — plausibly lots of the 31 unbooked 10-30 entries holding buying power (HK-RECON-GEN; those 31 were booked
  11-02, 39 new ones are still `submitted`). Crosscheck 0, no quote 0, "missed: triggered" 0, bracket base-price rejects
  0 (10-29: 8). **One unintended non-block:** Primary's −2R latch was one lot late on 11-02 (4th SOXS short of
  L3-gap-slope-fromopen-FD at 12:45:39, 25 s after two stop fills that the 12:46:44 reconcile booked; −1.02R, −$87) —
  HK-LATCH (queued by nightly1102, a runner change; not done here). One Testing 2 intraday push failed 11:27 ET (GitHub
  `commit_refs`), later pushes landed.
- **Place in line: 204 signals lost to a different setup holding the symbol, −70.1R net.** Worse than the account's
  live average in Primary (4, −1.17 vs −0.37; L3-rsi5hi to L3-fromopen, MF4 to its -FD twin), Testing 1 (8, −0.68 vs
  −0.22; MF3 to its -FD twin) and Graveyard (153, −0.33 vs −0.24; heat_fade_long-FD 22 −19.4R to its non-FD twin).
  Slightly better but still negative: Testing 2 (8, −0.05 vs −0.22) and Gen (31, −0.28 vs −0.39); the one positive
  setup, GEN-261026-06 (5 lost, +2.9R, live −0.02R), has n = 5. **No setup_order or cap change suggested.**
- **Most costly intended blocks (no change):** not shortable/ETB in Testing 2 +36.5R net (185; CWT09 g10 vwaploss /
  bounce 113 on 10-30, a down day that suited shorts); spread vs stop +22.9R in the Graveyard; Testing 1 spread filter
  +8.1R; split-tape gate +2.6R (2). Everything else saved money: ETB overall −282.0R (1,039; **Primary −188.8R**, 324:
  L3-fromopen-FD 215), setup −2R stop −180.3R (615; Graveyard −162.6R, Primary −17.6R), spread filter −64.2R, max
  positions per setup −44.0R, twin held −39.2R, **Testing cost filter (first sessions) −29.8R over 91** (T2 CWT13 z05 25),
  opposite side −23.6R, lot cap −12.5R. Testing 2's scale-out cap (2/day) let 11 R2A trades run without the half-off on
  11-02 (exemption SO-1A from 11-03). No account daily stop, max-trades or max-concurrent skip.
- **No fix, no decision.** Buying power is the Graveyard's capital and Gen's booking lag (HK-RECON-GEN); the missed
  decisions are OPS-HANDOVER (10-30) and the GX1 no-catch-up rule (GY 14:30; changing it is a timing rule for the owner,
  one minute in 11 sessions, not worth a decision yet); HK-LATCH is queued.

### 1. Coverage per account and session (decision minutes of 77; longest gap; polls of 384)

| account | 10-30 | 11-02 | polls 10-30 / 11-02 |
|---|---|---|---|
| Primary | **75** (14:40, 14:45) · **11.2 min** (14:36:51 → 14:48:00) | 77 · 2.3 (14:30, handover) | 373 / 384 |
| Testing 1 | **75** · **12.3** (14:35:14 → 14:47:34) | 77 · 2.5 (handover) | 374 / 384 |
| Testing 2 | **75** · **13.5** (14:35:15 → 14:48:45) | 77 · 3.8 (handover) | **303 / 297** |
| Graveyard | **75** · **13.4** (14:35:18 → 14:48:40) | **76** (14:30) · 2.2 (handover 14:45, 2.1) | **309** / 348 |
| Generated | **75** · **13.8** (14:35:13 → 14:49:03) | 77 · 4.7 (handover) | **292 / 253** |

First poll 09:30:00-02 in every account and session; data-stale polls 0; status.json `data_outages` [], `flatten_failed`
[], phase `closed` at both closes (nightly1030 / nightly1102). Symbols with a bar at the decision poll ≈ 55-56% fresh in
every account (the rest are decided by their next bar).

### 2. Never fired (enabled, 0 journaled signals 10-30, 11-02)

| account | enabled | never | which / why | broken |
|---|---|---|---|---|
| Primary | 10 | 1 | NS1-rsidip-rsi5pop-long (09:50-11:30; 15 signals since start, last 10-29) | 0 |
| Testing 1 | 30 | 8 | IDX1 hold / trail, IDX2, IDX3, IDX5 (index dip by 09:45-09:55; 0 in 12 sessions, rare by design); RW6G1 (0 in 8, very rare by design; its -FD twin is in DM-N3); ST6-volspikeup-short-mid-FD (23 since start, last 10-28); LIQ-pdl-sweep (1 in 15) | 0 |
| Testing 2 | 48 | 18 | **CWT14-pdl-p05-R2A-short** (day 1; regime picked the long leg); LD1 / LD3-LD8 (breadth / index-turn gated; 0-2 in 9); NM-RWN4 / RWR1 / RWR4 (spy_fo / qqq_fo index-up gated; 9 / 0 / 6 before); NM-AMS-N1, NM-PM-gapdn-above-pdh (2 each, last 10-29); MF2-open-rsimidhi-flowsell (non-FD twin, 2); CWT04 lh-a25 / vwaptest-a25 (0 in 16, dormant); CWT05 flush m05 / m075 v5 (11 / 7 before, last 10-29) | 0 |
| Graveyard | 28 | 0 | — | 0 |
| Generated | 93 | 40 | all regime / window gated (breadth > 0.6-0.7 or < 0.3-0.35, SPY / QQQ from open beyond ±0.25-0.6%, 13:00-15:00 windows, $150M min ADV) or young (GEN-261028/29, 3-4 sessions). Screen odds of 0 signals in these 2 sessions ≥ 0.14 for all 40; the four with low lifetime odds (GEN-261019-02, -261020-01, -261020-05, -261027-01: 0.007-0.010) fired 3-48 times before, last 10-27..10-29 | 0 |

### 3. System errors and unintended blocks

| what | account / when | count | what-if gross / net R | note |
|---|---|---|---|---|
| Broker reject: insufficient buying power | GY 11-02 10:40-10:50 (CWT14 orl p05 9, CWT12 coil k6 6, ...) | 38 | +0.90 / **−2.60** | Graveyard capital in use |
| Broker reject: insufficient buying power | Gen 10-30 14:35-15:00 (GEN-261026-02 ×4, -06 ×4, -07 ×2) | 12 | +8.46 / **+7.99** | likely the 31 unbooked lots (HK-RECON-GEN) |
| Bracket leg past base price / crosscheck / no quote / missed-triggered | — | 0 | — | (10-29: 8 / 1 / 1 / 0) |
| Missed decision minutes (handover) | all 5 accounts 10-30, 14:40 + 14:45 | 10 account-min (≈ 28,000 symbol-min) | not priceable (≈ 45 signals) | OPS-HANDOVER: standby setup-python ~10 min |
| Missed decision minute (slow poll, no catch-up) | GY 11-02 14:30 | 1 (2,954 symbol-min) | not priceable (≈ 5 signals) | 16.2 s poll straddled the minute |
| −2R latch one lot late | Primary 11-02 SOXS (L3-fromopen-FD) | 1 entry that should have been blocked | −1.02R, −$87 (real) | HK-LATCH (queued) |
| Submitted, not booked | Gen 11-02: 39 entries | 39 | — | HK-RECON-GEN; 10-30's 31 booked 11-02 |
| Intraday push failed | T2 11-02 11:27 ET (`commit_refs`) | 1 | — | later pushes landed |
| Data-stale pauses / outages / job crashes / exceptions | — | 0 | — | |

### 4. Place in line (lost to a different setup holding the symbol)

| account | lost | net R (avg) | live avg net R | biggest | verdict |
|---|---|---|---|---|---|
| Primary | 4 | −4.66 (−1.17) | −0.37 | L3-gap-slope-rsi5hi-FD 2 (−2.1R, to L3-fromopen-FD), MF4-h40 2 (−2.5R, to its -FD twin) | worse; twins by design |
| Testing 1 | 8 | −5.44 (−0.68) | −0.22 | MF3-open-flowsell-rsi5hi 8 (to its -FD twin) | worse |
| Testing 2 | 8 | −0.38 (−0.05) | −0.22 | MF5 non-FD 4 (−2.7R, to its -FD twin); NM-HL-T75-pm-long 2 (+1.0R), CWT13 z05 1, NM-RWN3 1 (+0.9R) | n tiny |
| Graveyard | 153 | −50.85 (−0.33) | −0.24 | heat_fade_short-FD 38 (−9.2R), CWT14 orl p05 25 (−3.3R), heat_fade_long-FD 22 (−19.4R) | worse |
| Generated | 31 | −8.72 (−0.28) | −0.39 | GEN-261021-06 6 (−5.4R), GEN-261022-05 6 (−5.0R), GEN-261026-06 5 (+2.9R) | negative; n ≤ 6 per setup |

### 5. Intended blocks, cost this period (all accounts, what-if net R; no change)

1. **not shortable/ETB, Testing 2** — 185 skips, +36.5R (CWT09 g10 vwaploss / bounce on 10-30); overall ETB saved −282.0R.
2. **spread vs stop, Graveyard** — 151, +22.9R (overall +2.6R: Gen −21.3R).
3. **spread filter, Testing 1** — 22, +8.1R (overall −64.2R saved).
4. **split-tape short gate, Testing 1** — 2, +2.6R.
5. **Testing 2 scale-out cap (2/day)** — 11 R2A trades ran without the half-off on 11-02 (not a skip; SO-1A exempts R2A from 11-03).
6. Saved money: setup −2R stop −180.3R (615), max positions per setup −44.0R (219), twin held −39.2R (67), **cost filter
   −29.8R (91, first period)**, opposite side −23.6R (98), lot cap −12.5R (44), price below minimum −7.8R (8).

Educational only — not financial advice.

## 2026-10-29 — answer first (sessions 10-27, 10-28, 10-29; first three with the GX1 clock gate)

Script `research/ops/blocked1029_audit.py` (output `blocked1029_results.json`). Under GX1 a lab decision is taken only by
the poll whose latest completed minute is the bucket's 4th minute (poll record `exp % 5 == 0`, no catch-up of an older
bucket), so coverage is now **decision minutes polled of 77**, not the old bar-count % 5 measure. Reused, not redone:
`coverage1029.md` (Primary live = offline recompute 35/35 on 10-29, 92/92 since 10-27; earnings blackout removes 1,490
names), `research/bdi/nightly1027/1028/1029` (polls, handovers, rejects), `research/bdi/p2_1029` (low-rate tiers).
No replay was run (rule 21; another session is auditing the replay).

- **Coverage: 1,153 of 1,155 decision minutes polled (99.8%).** Every account polled 77/77 in every session except
  **Testing 2 and Gen on 10-28 (76/77)**: the handover #159 → #165 left a 5.7 / 5.8-minute gap and the 14:35 bucket
  (decided at the 14:40 poll) was never evaluated there. Size: 0-3 signals in T2 and 0-10 in Gen at that minute on the
  other days, so about 1-5 signals, value unknown (no signal was computed). OPS-HANDOVER has it; 10-29 was clean (checkout
  ~5 s). No data-stale poll, no data outage, no flatten failure, no job crash, no visible exception in any account.
  **Poll counts under 90%** (of 384 one-minute polls): Testing 2 82 / 70 / 82%, Graveyard 72 / 82 / 81%, Gen 65 / 59 / 69%.
  They skip bucket minutes 1-2, which only the non-lab setups (orb20_a, exhaustion_short, heat_fade_*) use; OPS-POLL.
- **Never fired: 67 of 209 enabled, broken 0.** Primary 0 of 11, Graveyard 0 of 24. All modules exist and
  `build_strategies` on each 10-29 freeze file loads every setup (LOAD_FAILURES empty in all 5). The 67 are rare by design
  or young (table 2); the one low-odds case, GEN-261020-09 (QQQ < −0.3% midday long, 0 in 8 sessions, screen odds of 0
  = 0.007, 0.04 without the 10-22 phase-lock and 10-26 late-start days), fired 56 times in the 10-26 replay of 10-22,
  so its code works; watch, not broken.
- **Unintended blocks are small and would have lost: 14 signals, −2.3R gross / −5.4R net.** Broker rejects 12: 8 bracket
  legs already past the broker's base price at submit (−8.4R net; Graveyard 5 of them are CWT14 orl twins on RWM / SDS at
  10:10 on 10-29) and 4 Graveyard "insufficient buying power" (+2.5R); crosscheck 1 (GY, quote 386 s old, −0.4R); no
  quote 1 (Gen, ConnectionError, +0.9R). "missed: triggered" 0 (10-26: 6). Primary: none. Plus the 10-28 missed bucket
  above and Gen's 8 entries of 10-29 still `submitted` with no trade row (booking, not a block: HK-RECON-GEN, due 10-30).
- **Place in line: 212 signals lost to another setup holding the symbol, −60.8R net.** Worse than the account's live
  average in Primary (4, −1.30 avg; MF4 to its -FD twin), Testing 1 (38, −0.50 vs −0.25) and Testing 2 (46, −0.70 vs
  −0.17; NS3-FD 22 to NS3V1). Graveyard's 120 were a little better than its average (−0.05 vs −0.19R) but still negative
  after costs, the better setups have n ≤ 9 each, and it is the Graveyard. Gen 4 (+1.8R). **No setup_order or cap change
  suggested.**
- **Most costly intended blocks (no change):** not shortable/ETB +40.6R net over 1,012 (T1 +101.2R: L3-gap-slope-fromopen-FD
  refiring on non-borrowable 2x single-stock ETFs MRNX / STXL / STXU / STXX ..., 380 skips on 10-29; Graveyard −47.2R and
  Gen −13.4R saved); opposite side held +9.3R (78). Everything else saved money: spread vs stop −101.7R (425), setup −2R
  stop −101.3R (477; Graveyard −98.6R; **Primary day 1 (10-29): 4 skips, −2.7R saved**), twin held −58.6R (94), max
  positions per setup −42.2R (258), spread filter −36.4R (560), lot cap −20.9R (72). No split-tape or account daily stop
  skips this period.
- **No fix, no decision.** Nothing here is a clear bug: the bracket rejects are price moving past a 0.5R target / stop
  between bar close and submit (re-anchoring = an exit change, and they were losers), buying power is the Graveyard's
  capital limit, the handover gap is OPS-HANDOVER's.

### 1. Coverage per account and session (decision minutes of 77; longest gap; handover gap)

| account | 10-27 | 10-28 | 10-29 | polls 10-27 / 28 / 29 (of 384) |
|---|---|---|---|---|
| Primary | 77 · 1.8 min (14:27, handover) | 77 · 3.0 (14:36, handover) | 77 · 1.8 (14:37, handover) | 384 / 383 / 384 |
| Testing 1 | 77 · 2.1 (handover) | 77 · 2.1 (handover) | 77 · 2.4 (handover) | 383 / 382 / 384 |
| Testing 2 | 77 · 3.3 (handover) | **76** (14:35 bucket) · **5.7 (14:36:19 → 14:42:00)** | 77 · 3.5 (handover) | **316 / 268 / 316** |
| Graveyard | 77 · 3.5 (handover) | 77 · 3.1 (14:55; handover 3.1 at 14:41) | 77 · 3.5 (handover) | **277 / 315 / 310** |
| Generated | 77 · 4.5 (handover) | **76** (14:35 bucket) · **5.8 (14:36:20 → 14:42:11)** | 77 · 4.3 (handover) | **248 / 227 / 264** |

First poll 09:30:01 in every account and session (no late start); data-stale polls 0; status.json at each close
`data_outages` [], `flatten_failed` [], phase `closed`. The longest gap is the 6-hour-limit handover every day. Primary's
signals match the offline recompute 92/92 over these sessions (coverage1029.md), the symbol-level check that the decision
minutes were really used.

### 2. Never fired (enabled, 0 journaled signals 10-27..10-29)

| account | enabled | never | which / why | broken |
|---|---|---|---|---|
| Primary | 11 | 0 | — | 0 |
| Testing 1 | 32 | 7 | IDX1 hold / trail, IDX2, IDX3, IDX5 (QQQ −1.0% / SPY −0.75% / −0.5% by 09:45-09:55: QQQ's lows were −0.21 / −0.53 / −0.69%, SPY −0.28%; 0 in 10 sessions, rare by design); RW6G1 (RW6 with a VWAP 2-SD band guard, very rare by design: 0 in 6, replay 0 on 10-22..10-26); LIQ-pdl-sweep (1 in 13, low tier p2_1029) | 0 |
| Testing 2 | 49 | 10 | CWT04 lh-a25 / vwaptest-a25 (0 in 14, dormant in p2_1029; the 2-year rate is carried by April 2025); LD1 / LD4 / LD8 (breadth thrust / SPY −0.30% dip + breadth turn: none on these days); NM-RWR1 (spy_fo-gated, 0 in 9); NM-RWN4 / RWN5 / RWR3 / RWR4 (fired 9 / 6 / 3 / 6 before, last 10-19..10-26; index-direction gated) | 0 |
| Graveyard | 24 | 0 | — | 0 |
| Generated | 93 | 50 | 18 young (added 10-27..10-29, 1-3 sessions); the rest regime- or late-window-gated (breadth > 0.7 / < 0.3, SPY / QQQ from open beyond ±0.25-0.6%, 14:00-15:00 windows, $150M min ADV). Screen odds of 0 signals over the sessions they were enabled ≥ 0.1 for 49 of 50; GEN-261020-09 0.007 (see above; replay fires it); GEN-POD1022-01 / -02 (observation, breadth thrust) 0.80 / 0.66 | 0 |

Screen odds = share of zero-signal days in the setup's last 60 screen sessions (`research/generator/expected_live.json`
counts60), else 1 − signal days / screen sessions; earnings blackout and universe differences ignored, so a guide only.

### 3. System errors and unintended blocks

| what | account / when | count | what-if gross / net R | note |
|---|---|---|---|---|
| Broker reject: bracket leg past base price | GY 6 (10-28 SCHA; 10-29 RWM ×3, SDS ×2 CWT14 orl twins at 10:10), T2 1 (10-29 PURR stop leg), Gen 1 (10-28 ORCL stop leg) | 8 | −5.69 / **−8.39** | price passed the 0.5R target (or the stop) between bar close and submit; H-1 / HK-1. Not a code bug |
| Broker reject: insufficient buying power | GY 10-28 SOXQ, XOP; 10-29 VTRS ×2 (twins) | 4 | +2.72 / **+2.47** | the Graveyard's cash is used up by its open lots at 11:00-11:30 |
| Crosscheck | GY 10-28 SLN (quote 386 s old > 300 s) | 1 | −0.28 / −0.44 | working as designed |
| No quote (ConnectionError) | Gen 10-28 HIMS | 1 | +0.95 / +0.92 | one transient |
| "missed: triggered" | — | 0 | — | (10-26: 6, late start) |
| Missed decision minute (handover) | T2, Gen 10-28 14:35 bucket | 1 bucket each | not priceable (≈ 1-5 signals) | OPS-HANDOVER; 10-29 clean |
| Submitted, not booked | Gen 10-29: 8 entries (TRV ×2, LITE, EVRG, TMF, USFD, AKAM, EQX) | 8 | — | HK-RECON-GEN (reconcile 10-30); T2's 2 of 10-27 were booked 10-28 |
| Data-stale pauses / outages / job crashes | — | 0 | — | |

### 4. Place in line (lost to a different setup holding the symbol: twin / lot cap / opposite side / max positions)

| account | lost | net R (avg) | live avg net R | biggest | verdict |
|---|---|---|---|---|---|
| Primary | 4 | −5.20 (−1.30) | −0.06 | MF4-h40-open-flowsell 3 (−4.3R, to its -FD twin) | worse; twins by design |
| Testing 1 | 38 | −18.89 (−0.50) | −0.25 | MF3-open-flowsell-rsi5hi 13 (−15.6R, to its -FD twin), exhaustion_short-FD 6 (−3.4R) | worse |
| Testing 2 | 46 | −32.08 (−0.70) | −0.17 | NS3-failed-vwap-reclaim-short-FD 22 (−20.7R, to NS3V1), MF5 non-FD 13 (−8.5R, to its -FD twin) | worse |
| Graveyard | 120 | −6.43 (−0.05) | −0.19 | heat_fade_short-FD 37 (−14.2R, to its non-FD twin), CWT14 orl p05 34 (−6.8R, to its p10 twins); better: CWT12-coil-k6 8 (+6.4R), heat_fade_long-FD 9 (+4.9R) | slightly better, still negative, n ≤ 9 per setup: no change |
| Generated | 4 | +1.78 (+0.45) | −0.40 | GEN-261022-07 2 (+1.8R) | n tiny |

### 5. Intended blocks, cost this period (all accounts, what-if net R; no change)

1. **not shortable/ETB** — 1,012 skips, +40.6R (T1 +101.2R, L3-gap-slope-fromopen-FD 482 refires on non-borrowable 2x
   single-stock ETFs; 65 symbols on 10-29; Graveyard −47.2R, Gen −13.4R saved).
2. **opposite side held** — 78, +9.3R (Graveyard +8.7R).
3. Saved money: spread vs stop −101.7R (425), setup −2R stop −101.3R (477; Primary's first day 4 skips −2.7R), twin held
   −58.6R (94), max positions per setup −42.2R (258, Graveyard), spread filter −36.4R (560), lot cap −20.9R (72),
   price below minimum −4.3R (6). Split-tape gate and account daily stop: 0 skips.

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
